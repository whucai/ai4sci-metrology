#!/usr/bin/env python3
"""M1 Full Benchmark — 10-paper framework validation with real LLM extraction + dimension scoring.

Extends m1_framework_validation.py to support both:
  A) SciSciPaper annotations (pilot papers) — annotation summary as prompt
  B) Raw papers (.md files + gold_values.json) — full text as prompt

Pipeline per paper:
  1. Load gold dict (from SciSciPaper or gold_values.json)
  2. Build LLM prompt (from annotation or .md full text)
  3. LLM extracts 6 components as JSON → agent dict
  4. Build ReproductionProfile (gold + agent → 6×5 matrix)
  5. Cross-paper M1 analysis

Usage:
    python scripts/m1_full_benchmark.py --model gemma           # all 10 papers
    python scripts/m1_full_benchmark.py --papers 1-3 --model gemma  # pilot only
    python scripts/m1_full_benchmark.py --papers 4-6 --model qwen3-32b
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import math
import hashlib
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscibench.annotation import (
    SciSciPaper, create_wu2019, create_ke2023, create_arts2025,
)
from src.sciscibench.eval.dimensions import (
    build_reproduction_profile,
    detect_spurious_reproduction,
    compute_maturity_level,
    format_maturity,
    TaskType,
    ReproductionProfile,
    COMPONENT_DIMENSION_MAP,
)
from src.sciscigpt_local.llm_backends import LLMConfig, load_llm_from_config

BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "bench-mark"
REFINE_DIR = Path(__file__).resolve().parent.parent / "refine-logs"


# ── Paper Spec ────────────────────────────────────────────────────────────────

@dataclass
class PaperSpec:
    """Defines a paper for the M1 benchmark."""
    paper_id: str
    task_type: TaskType
    title: str = ""
    venue: str = ""
    year: int = 0

    # Mode A: SciSciPaper (pilot papers)
    sci_paper: SciSciPaper | None = None

    # Mode B: Raw paper (.md + gold_values.json)
    md_path: str = ""
    gold_json_path: str = ""


# ── 10-Paper Registry ─────────────────────────────────────────────────────────

def _infer_task_type(title: str, venue: str) -> TaskType:
    """Infer task type from title/venue keywords."""
    t = title.lower()
    method_keywords = ["review", "survey", "overview", "bibliometric", "scientometric",
                       "measurement", "taxonomy", "framework", "conceptual", "perspective",
                       "roadmap", "agenda", "theory", "theoretical", "methodology",
                       "a review", "literature review", "systematic review"]
    title_is_method = any(kw in t for kw in method_keywords)
    if title_is_method:
        return TaskType.METHOD
    return TaskType.STRICT


def _slug_from_metadata(item: dict) -> str:
    """Generate a clean paper_id from metadata."""
    title = item.get("title", "")
    arxiv_id = item.get("arxiv_id", "")
    # Use arxiv ID as base for uniqueness
    if arxiv_id:
        return arxiv_id.replace(".", "_").replace("v1", "").replace("v2", "").replace("v3", "").replace("v4", "")
    # Fallback: hash the title into a short slug
    h = hashlib.md5(title.encode()).hexdigest()[:8] if title else "unknown"
    words = title.lower().split()[:3] if title else ["paper"]
    return "_".join(w[:6] for w in words) + "_" + h


def _build_paper_specs_from_metadata(max_papers: int | None = None) -> list[PaperSpec]:
    """Auto-generate PaperSpecs from paper_metadata.json.

    Includes:
      - All papers with real titles (not just arxiv IDs) and existing .md files
      - SciSciPaper annotations for the 3 pilot papers
      - gold_values.json lookup from refine-logs/r*/

    Args:
        max_papers: Cap on total papers (None = all available).
    """
    meta_path = BENCHMARK_DIR / "paper_metadata.json"
    if not meta_path.exists():
        print("WARNING: paper_metadata.json not found, falling back to hardcoded list")
        return _build_paper_specs_hardcoded()

    with open(meta_path) as f:
        metadata = json.load(f)

    specs = []

    # ── SciSciPaper pilots (always first) ──
    pilot_specs = _build_pilot_specs()
    specs.extend(pilot_specs)
    pilot_ids = {s.paper_id for s in pilot_specs}
    pilot_md_paths = {str(Path(p).resolve()) for s in pilot_specs if s.md_path for p in [s.md_path]}

    # ── Gold values map (refine-logs/r*/gold_values.json) ──
    gold_map = {}  # paper_id, arxiv_id, md_path → gold_json_path
    for rdir in sorted(REFINE_DIR.glob("r*")):
        gv = rdir / "gold_values.json"
        if gv.exists():
            try:
                with open(gv) as f:
                    gdata = json.load(f)
                pid = gdata.get("paper_id", "")
                # Map by paper_id, arxiv_id, and md_path
                if pid:
                    gold_map[pid] = str(gv)
                aid = gdata.get("arxiv_id", "")
                if aid:
                    gold_map[aid] = str(gv)
                    gold_map[aid.replace(".", "_")] = str(gv)
                md = gdata.get("md_path", "")
                if md:
                    gold_map[md] = str(gv)
            except (json.JSONDecodeError, KeyError):
                pass

    # ── Build specs from metadata ──
    seen_md_paths = set(pilot_md_paths)
    seen_ids = set(pilot_ids)

    for item in metadata:
        if max_papers and len(specs) >= max_papers:
            break

        title = item.get("title", "").strip()
        md_rel = item.get("md_path", "")
        subdir = item.get("subdir", "")
        arxiv_id = item.get("arxiv_id", "")

        # Skip: no title, title is bare arxiv ID, or in "others"
        if not title:
            continue
        if title[0].isdigit() and not any(c.isalpha() for c in title[:20]):
            continue  # bare arxiv-like title
        if subdir == "others":
            continue

        # Resolve .md path
        if md_rel:
            md_path = str(BENCHMARK_DIR / md_rel)
            if not Path(md_path).exists():
                continue
        else:
            continue

        # Dedup: same .md file
        md_resolved = str(Path(md_path).resolve())
        if md_resolved in seen_md_paths:
            continue
        seen_md_paths.add(md_resolved)

        # Generate paper_id
        paper_id = _slug_from_metadata(item)
        # Ensure unique
        orig_id = paper_id
        counter = 1
        while paper_id in seen_ids:
            paper_id = f"{orig_id}_{counter}"
            counter += 1
        seen_ids.add(paper_id)

        # Task type
        venue = subdir
        task_type = _infer_task_type(title, venue)

        # Year
        year = item.get("year", 0)
        if not year:
            # Try to extract from arxiv ID
            m = re.match(r"(\d{2})(\d{2})", arxiv_id or "")
            if m:
                year = 2000 + int(m.group(1))

        # Gold lookup
        gold_path = ""
        # Try paper_id, then arxiv_id variants
        clean_aid = arxiv_id.replace(".", "_") if arxiv_id else ""
        for key in [paper_id, arxiv_id, clean_aid, md_rel]:
            if key and key in gold_map:
                gold_path = gold_map[key]
                break

        specs.append(PaperSpec(
            paper_id=paper_id,
            task_type=task_type,
            title=title[:200],
            venue=venue,
            year=year,
            md_path=md_path,
            gold_json_path=gold_path,
        ))

    return specs


def _build_pilot_specs() -> list[PaperSpec]:
    """Build the 3 SciSciPaper pilot paper specs."""
    return [
        PaperSpec(
            paper_id="wu2019_disruption", task_type=TaskType.DATA_SUB,
            title="Large teams develop and small teams disrupt science and technology",
            venue="Nature", year=2019, sci_paper=create_wu2019(),
        ),
        PaperSpec(
            paper_id="ke2023_normalized_impact", task_type=TaskType.STRICT,
            title="A network-based normalized impact measure reveals successful periods of scientific discovery across disciplines",
            venue="PNAS", year=2023, sci_paper=create_ke2023(),
            md_path=str(BENCHMARK_DIR / "PNAS/ke-et-al-2023-a-network-based-normalized-impact-measure-reveals-successful-periods-of-scientific-discovery-across.md"),
        ),
        PaperSpec(
            paper_id="arts2025_frontier_scientists", task_type=TaskType.METHOD,
            title="Not like the others: Frontier scientists for inventive performance",
            venue="Research Policy", year=2025, sci_paper=create_arts2025(),
            md_path=str(BENCHMARK_DIR / "Research Policy/1-s2.0-S0048733325001684-main.md"),
        ),
    ]


def _build_paper_specs_hardcoded() -> list[PaperSpec]:
    """Fallback: the original 10-paper hardcoded list."""
    specs = list(_build_pilot_specs())

    specs.append(PaperSpec(
        paper_id="petersen2024_disruption_index", task_type=TaskType.STRICT,
        title="The disruption index suffers from citation inflation and is confounded by shifts in scholarly citation practice",
        venue="arXiv", year=2024,
        md_path=str(BENCHMARK_DIR / "arXiv/2406.15311v1.md"),
        gold_json_path=str(REFINE_DIR / "r002/gold_values.json"),
    ))
    specs.append(PaperSpec(
        paper_id="park2023_disruptive", task_type=TaskType.STRICT,
        title="Papers and patents are becoming less disruptive over time",
        venue="Nature", year=2023,
        md_path=str(BENCHMARK_DIR / "Nature/s41586-022-05543-x.md"),
        gold_json_path=str(REFINE_DIR / "r004/gold_values.json"),
    ))
    specs.append(PaperSpec(
        paper_id="zhao2025_novelty_review", task_type=TaskType.METHOD,
        title="A Review on the Novelty Measurements of Academic Papers",
        venue="Scientometrics", year=2025,
        md_path=str(BENCHMARK_DIR / "Scientometrics/2501.17456v1.md"),
    ))
    specs.append(PaperSpec(
        paper_id="bentley2023_disruption", task_type=TaskType.STRICT,
        title="Is disruption decreasing, or is it accelerating?",
        venue="Advances in Complex Systems", year=2023,
        md_path=str(BENCHMARK_DIR / "Advances in Complex Systems/2306.14364.md"),
        gold_json_path=str(REFINE_DIR / "r007/gold_values.json"),
    ))
    specs.append(PaperSpec(
        paper_id="deng2023_robust_disruption", task_type=TaskType.STRICT,
        title="Enhancing the robustness of the disruption metric against noise",
        venue="Scientometrics", year=2023,
        md_path=str(BENCHMARK_DIR / "Scientometrics/s11192-023-04644-2.md"),
        gold_json_path=str(REFINE_DIR / "r008/gold_values.json"),
    ))
    specs.append(PaperSpec(
        paper_id="arts2021_nlp_patent", task_type=TaskType.METHOD,
        title="Natural language processing to identify the creation and impact of new technologies in patent text",
        venue="Research Policy", year=2021,
        gold_json_path=str(REFINE_DIR / "r003/gold_values.json"),
    ))
    specs.append(PaperSpec(
        paper_id="funk2021_science_disruption", task_type=TaskType.STRICT,
        title="The slowing of science",
        venue="Science", year=2021,
        md_path=str(BENCHMARK_DIR / "Science/2207.14260v2.md"),
    ))
    return specs


def _build_paper_specs() -> list[PaperSpec]:
    """Build the paper specification list from metadata (preferred) or hardcoded fallback."""
    return _build_paper_specs_from_metadata()


# ── Gold dict builders ────────────────────────────────────────────────────────

def sci_paper_to_gold(paper: SciSciPaper) -> dict:
    """Convert SciSciPaper annotation to gold component dict."""
    sm = paper.experiment_design_gold.get("statistical_method", {})
    spec_elements = []
    if sm.get("family"):
        spec_elements.append(sm["family"])
    if sm.get("estimation"):
        spec_elements.append(sm["estimation"])
    gs = paper.experiment_design_gold.get("grouping_strategy", {})
    if gs.get("groups"):
        spec_elements.extend(gs["groups"])

    coefficients = {}
    for rc in paper.result_claims:
        name = rc.get("metric", "unknown")
        val_str = rc.get("value", "")
        try:
            coefficients[name] = float(val_str.replace("%", "").split("+")[0].strip())
        except (ValueError, AttributeError):
            coefficients[name] = 0.0

    dv = paper.dependent_variables[0] if paper.dependent_variables else {}
    formula = dv.get("formula", "")

    target_values = []
    for rc in paper.result_claims:
        val_str = rc.get("value", "")
        try:
            val = float(val_str.replace("%", "").replace("+", "").replace("−", "-").split()[0])
        except (ValueError, AttributeError):
            val = 0.0
        target_values.append({"label": rc.get("metric", ""), "value": val})

    directions = [rc.get("direction", "") for rc in paper.result_claims]
    expected_direction = directions[0] if directions else ""

    return {
        "data_source": {
            "data_source": paper.data_source,
            "filter_rules": [paper.data_source],
        },
        "sample": {
            "N": 0,
            "time_window": paper.sample_scope.get("time_window", ""),
            "filter_rules": paper.sample_scope.get("filters", []),
        },
        "indicator": {
            "formula": formula,
            "indicator_stats": {"mean": 0, "std": 0},
        },
        "model": {
            "spec_elements": list(set(spec_elements)),
            "coefficients": coefficients,
        },
        "result_table": {
            "target_tables": [f"Main result: {rc.get('metric', '')}" for rc in paper.result_claims],
            "target_values": target_values,
            "expected_direction": expected_direction,
        },
        "claim": {
            "conclusion_claims": paper.conclusion_claims,
        },
    }


def gold_values_to_gold(gold_data: dict) -> dict:
    """Convert M0 gold_values.json to gold component dict for dimension scoring."""
    filters = gold_data.get("filters", {})
    gold_results = gold_data.get("gold_results", {})
    methodology = gold_data.get("methodology", gold_data.get("model_specification", ""))

    # Build filter rules
    filter_rules = []
    yr = filters.get("year_range", [])
    if yr:
        filter_rules.append(f"year_range: {yr[0]}-{yr[1]}")
    for k in ["reference_count", "author_count", "citation_count_5y", "require_cd_score",
              "require_citations", "drop_na"]:
        if k in filters:
            v = filters[k]
            filter_rules.append(f"{k}: {v}")

    # Build spec elements from methodology
    spec_elements = []
    method_lower = methodology.lower()
    for term in ["ols", "logit", "fixed_effects", "year_fe", "firm_fe",
                 "descriptive", "groupby", "mean", "median",
                 "citation-weighted", "weighted", "unweighted",
                 "cd index", "cd5", "disruption"]:
        if term in method_lower:
            spec_elements.append(term.replace("_", " "))

    # Build coefficients from gold_results
    coefficients = {}
    if "coefficients" in gold_results:
        for var, vals in gold_results["coefficients"].items():
            coefficients[var] = vals.get("coef", 0)

    # Build target values
    target_values = []
    for k, v in gold_results.items():
        if k in ("sample_N", "r_squared", "r_squared_adj", "years_count",
                 "decline_pct", "overall_mean_cd", "overall_std_cd"):
            if isinstance(v, (int, float)):
                target_values.append({"label": k, "value": v})
        elif isinstance(v, dict) and "mean" in v:
            target_values.append({"label": k, "value": v["mean"]})
        elif isinstance(v, dict) and "coef" in v:
            target_values.append({"label": k, "value": v["coef"]})

    # Direction from methodology
    direction = ""
    if "decreas" in method_lower or "declin" in method_lower:
        direction = "negative"
    elif "increas" in method_lower:
        direction = "positive"

    return {
        "data_source": {
            "data_source": gold_data.get("data_source", ""),
            "filter_rules": [gold_data.get("data_source", "")],
        },
        "sample": {
            "N": gold_results.get("sample_N", 0),
            "time_window": f"{yr[0]}-{yr[1]}" if yr else "",
            "filter_rules": filter_rules,
        },
        "indicator": {
            "formula": methodology,
            "indicator_stats": {
                "mean": gold_results.get("overall_mean_cd", 0),
                "std": gold_results.get("overall_std_cd", 0),
            },
        },
        "model": {
            "spec_elements": list(set(spec_elements)),
            "coefficients": coefficients,
        },
        "result_table": {
            "target_tables": [f"Main results for {gold_data.get('paper_id', '')}"],
            "target_values": target_values,
            "expected_direction": direction,
        },
        "claim": {
            "conclusion_claims": gold_data.get("claims", gold_data.get("conclusion_claims", [])),
        },
    }


def build_gold_dict(spec: PaperSpec) -> dict:
    """Build gold dict from whatever source is available."""
    if spec.sci_paper:
        return sci_paper_to_gold(spec.sci_paper)
    if spec.gold_json_path and Path(spec.gold_json_path).exists():
        with open(spec.gold_json_path) as f:
            gold_data = json.load(f)
        return gold_values_to_gold(gold_data)
    # Fallback: minimal gold from spec metadata
    return {
        "data_source": {"data_source": "", "filter_rules": []},
        "sample": {"N": 0, "time_window": "", "filter_rules": []},
        "indicator": {"formula": "", "indicator_stats": {"mean": 0, "std": 0}},
        "model": {"spec_elements": [], "coefficients": {}},
        "result_table": {"target_tables": [], "target_values": [], "expected_direction": ""},
        "claim": {"conclusion_claims": []},
    }


# ── LLM Prompt Builders ───────────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are an expert in computational scientometrics and research methodology.
Your task is to decompose a research paper into its 6 methodological components.

For each component, extract the relevant information as structured JSON.
Be precise and faithful to the paper — do not invent or assume details not present.

CRITICAL: Output ONLY valid JSON. No markdown, no explanation outside the JSON.
Start with '{' and end with '}'."""


def build_prompt_from_sci_paper(paper: SciSciPaper) -> str:
    """Build prompt from SciSciPaper annotation summary."""
    parts = []
    parts.append(f"Title: {paper.title}")
    parts.append(f"Authors: {', '.join(paper.authors)}")
    parts.append(f"Venue: {paper.venue} ({paper.year})")
    parts.append("")
    parts.append(f"Research Idea: {paper.research_idea}")
    parts.append(f"Research Question: {paper.research_question}")
    parts.append("")
    parts.append(f"Data Source: {paper.data_source}")
    parts.append(f"Data Description: {paper.data_description}")
    parts.append(f"Available Fields: {', '.join(paper.available_fields)}")
    parts.append("")
    for label, var_list in [
        ("Independent", paper.independent_variables),
        ("Dependent", paper.dependent_variables),
        ("Control", paper.control_variables),
    ]:
        for v in var_list:
            parts.append(f"  [{label}] {v.get('name', '')}: {v.get('definition', v.get('formula', ''))}")
    parts.append("")
    parts.append(f"Sample Scope: {json.dumps(paper.sample_scope)}")
    sm = paper.experiment_design_gold.get("statistical_method", {})
    parts.append(f"Statistical Method: {sm.get('family', '')} — {sm.get('specification', '')}")
    parts.append("")
    parts.append(f"Result Claims: {json.dumps(paper.result_claims)}")
    parts.append(f"Conclusion Claims: {json.dumps(paper.conclusion_claims)}")
    return "\n".join(parts)


def build_prompt_from_md(md_path: str) -> str:
    """Build prompt from paper .md full text."""
    text = Path(md_path).read_text(encoding="utf-8", errors="replace")
    # Truncate to ~10K chars for Gemma's 8192 token context window
    if len(text) > 10000:
        text = text[:10000] + "\n\n[... paper truncated ...]"
    return text


def build_prompt(spec: PaperSpec) -> str:
    """Build LLM prompt from best available source."""
    if spec.sci_paper:
        return build_prompt_from_sci_paper(spec.sci_paper)
    if spec.md_path and Path(spec.md_path).exists():
        return build_prompt_from_md(spec.md_path)
    return f"Title: {spec.title}\nVenue: {spec.venue} ({spec.year})"


def build_extraction_user_prompt(paper_text: str) -> str:
    """Wrap paper text in the extraction task prompt."""
    return f"""Decompose the following research paper into 6 methodological components.
Return a single JSON object with these exact keys:

{{
  "data_source": {{
    "data_source": "Name of the dataset used",
    "data_description": "Brief description"
  }},
  "sample": {{
    "N": <sample size or null>,
    "time_window": "Time period",
    "filter_rules": ["list", "of", "criteria"]
  }},
  "indicator": {{
    "formula": "The key bibliometric indicator formula",
    "parameters": "Key parameters"
  }},
  "model": {{
    "spec_elements": ["list", "of", "model", "spec", "elements"],
    "model_type": "OLS, logit, fixed_effects, descriptive, etc.",
    "dependent_variable": "Name",
    "independent_variables": ["list"],
    "control_variables": ["list"],
    "fixed_effects": ["any", "FE"],
    "standard_errors": "Type or null"
  }},
  "result_table": {{
    "main_findings": [
      {{"metric": "name", "value": "reported value", "direction": "positive/negative/null", "significance": "p-value or statement"}}
    ],
    "key_coefficients": {{"var_name": "coefficient value"}}
  }},
  "claim": {{
    "conclusion_claims": ["claim 1", "claim 2", ...],
    "limitations": ["limitation 1", ...]
  }}
}}

Paper text:
---
{paper_text}
---"""


# ── Response Parser ───────────────────────────────────────────────────────────

def parse_llm_extraction(response: Any, paper_id: str = "") -> dict:
    """Parse LLM response into agent dict compatible with dimension scorers."""
    text = ""
    if isinstance(response, str):
        text = response
    elif isinstance(response, list):
        texts = [b.get("text", "") if isinstance(b, dict) else str(b) for b in response]
        text = "\n".join(texts)
    elif hasattr(response, "content"):
        content = response.content
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            texts = [b.get("text", "") if isinstance(b, dict) else str(b) for b in content]
            text = "\n".join(texts)
    else:
        text = str(response)

    # Extract JSON
    extracted = None
    try:
        extracted = json.loads(text)
    except json.JSONDecodeError:
        depth = 0
        start = -1
        for i, ch in enumerate(text):
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        extracted = json.loads(text[start:i+1])
                        break
                    except json.JSONDecodeError:
                        continue
                    start = -1

    if not extracted or not isinstance(extracted, dict):
        print(f"  WARNING [{paper_id}]: Could not parse LLM extraction")
        return _empty_agent_dict()

    return _convert_extraction_to_agent(extracted)


def _convert_extraction_to_agent(extracted: dict) -> dict:
    ds = extracted.get("data_source", {})
    sample = extracted.get("sample", {})
    indicator = extracted.get("indicator", {})
    model = extracted.get("model", {})
    result = extracted.get("result_table", {})
    claim = extracted.get("claim", {})

    coefficients = {}
    raw_coefs = result.get("key_coefficients", {})
    if isinstance(raw_coefs, dict):
        for k, v in raw_coefs.items():
            try:
                coefficients[k] = float(v) if isinstance(v, str) else v
            except (ValueError, TypeError):
                coefficients[k] = 0.0

    main_findings = result.get("main_findings", [])
    if not isinstance(main_findings, list):
        main_findings = []

    reproduced_values = []
    for mf in main_findings:
        if isinstance(mf, dict):
            val_str = mf.get("value", "0")
            try:
                val = float(str(val_str).replace("%", "").replace("+", "").split()[0])
            except (ValueError, AttributeError):
                val = 0.0
            reproduced_values.append({"label": mf.get("metric", ""), "value": val})

    observed_direction = ""
    if main_findings and isinstance(main_findings[0], dict):
        observed_direction = main_findings[0].get("direction", "")

    has_substance = {
        "data_source": bool(ds.get("data_source")),
        "sample": bool(sample.get("filter_rules") or sample.get("N")),
        "indicator": bool(indicator.get("formula")),
        "model": bool(model.get("spec_elements") or model.get("model_type")),
        "result_table": bool(main_findings or coefficients),
    }

    def make_component(comp_name, extra=None):
        base = {
            "code_executed": {comp_name: has_substance.get(comp_name, False)},
            "traceable": {comp_name: bool(extra.get(f"{comp_name}_traceable", False)) if extra else has_substance.get(comp_name, False)},
            "hard_coded": {comp_name: False},
            "hallucinated": {comp_name: False},
        }
        if extra:
            base.update(extra)
        return base

    return {
        "data_source": {
            **make_component("data_source"),
            "data_source": ds.get("data_source", ""),
            "data_description": ds.get("data_description", ""),
        },
        "sample": {
            **make_component("sample"),
            "N": sample.get("N") or 0,
            "time_window": sample.get("time_window", ""),
            "filter_rules": sample.get("filter_rules", []) if isinstance(sample.get("filter_rules"), list) else [],
        },
        "indicator": {
            **make_component("indicator"),
            "formula": indicator.get("formula", ""),
            "parameters": indicator.get("parameters", ""),
            "indicator_stats": {"mean": 0, "std": 0},
        },
        "model": {
            **make_component("model"),
            "spec_elements": model.get("spec_elements", []) if isinstance(model.get("spec_elements"), list) else [],
            "model_type": model.get("model_type", ""),
            "dependent_variable": model.get("dependent_variable", ""),
            "independent_variables": model.get("independent_variables", []) if isinstance(model.get("independent_variables"), list) else [],
            "control_variables": model.get("control_variables", []) if isinstance(model.get("control_variables"), list) else [],
            "coefficients": coefficients,
        },
        "result_table": {
            **make_component("result_table"),
            "produced_tables": [f"Finding: {mf.get('metric', '')}" for mf in main_findings] if main_findings else [],
            "reproduced_values": reproduced_values,
            "observed_direction": observed_direction,
        },
        "claim": {
            "conclusion_claims": claim.get("conclusion_claims", []) if isinstance(claim.get("conclusion_claims"), list) else [],
            "limitations": claim.get("limitations", []) if isinstance(claim.get("limitations"), list) else [],
        },
    }


def _empty_agent_dict() -> dict:
    empty = {"code_executed": {}, "traceable": {}, "hard_coded": {}, "hallucinated": {}}
    return {
        "data_source": {**empty, "data_source": ""},
        "sample": {**empty, "N": 0, "filter_rules": []},
        "indicator": {**empty, "formula": "", "indicator_stats": {"mean": 0, "std": 0}},
        "model": {**empty, "spec_elements": [], "coefficients": {}},
        "result_table": {**empty, "produced_tables": [], "reproduced_values": [], "observed_direction": ""},
        "claim": {**empty, "conclusion_claims": []},
    }


# ── LLM loading ──────────────────────────────────────────────────────────────

def get_available_models() -> dict[str, LLMConfig]:
    models = {}
    # Qwen3-32B via local vLLM
    models["qwen3-32b"] = LLMConfig(
        name="qwen3-32b", provider="openai",
        model=os.environ.get("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/"),
        api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
        base_url=os.environ.get("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1"),
        temperature=0.0, max_tokens=4096,
    )
    # DeepSeek-V4-Pro via Anthropic proxy
    if os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        models["deepseek-v4-pro"] = LLMConfig(
            name="deepseek-v4-pro", provider="anthropic",
            model="deepseek-v4-pro",
            api_key=os.environ["ANTHROPIC_AUTH_TOKEN"],
            base_url=os.environ.get("ANTHROPIC_BASE_URL", ""),
            temperature=0.0, max_tokens=4096,
        )
    # Gemma via local vLLM
    models["gemma"] = LLMConfig(
        name="gemma", provider="openai",
        model="gemma-4-26B-A4B-it", api_key="not-needed",
        base_url="http://192.168.1.127:8000/v1",
        temperature=0.0, max_tokens=4096,
    )
    return models


def create_llm(model_name: str) -> Any:
    if model_name == "mock":
        from src.sciscigpt_local.mock_llm import MockLLM
        return MockLLM()
    available = get_available_models()
    if model_name not in available:
        raise ValueError(f"Model '{model_name}' not available. Available: {list(available.keys())}")
    config = available[model_name]
    # Gemma: 8192 context, reserve ~5K for input, use 3072 output tokens
    if model_name == "gemma":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=config.model, api_key=config.api_key,
                          base_url=config.base_url, temperature=0.0, max_tokens=3072)
    return load_llm_from_config(config)


# ── Runner ────────────────────────────────────────────────────────────────────

class M1FullRunner:
    """Run M1 extraction + scoring on all papers."""

    def __init__(self, model_name: str = "gemma",
                 specs: list[PaperSpec] | None = None,
                 output_dir: str | Path = "refine-logs"):
        self.model_name = model_name
        self.specs = specs or _build_paper_specs()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = None

    def run_single(self, spec: PaperSpec) -> tuple[ReproductionProfile, dict, dict]:
        print(f"  Loading paper...")
        gold = build_gold_dict(spec)
        prompt_text = build_prompt(spec)
        user_prompt = build_extraction_user_prompt(prompt_text)
        print(f"  Prompt: {len(prompt_text)} chars, gold keys: {list(gold.keys())}")

        if self.llm is None:
            self.llm = create_llm(self.model_name)

        print(f"  Extracting components via {self.model_name}...")
        t0 = time.time()
        try:
            response = self.llm.invoke([
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ])
        except Exception as e:
            print(f"  LLM call failed: {e}")
            response = None
        elapsed = time.time() - t0
        print(f"  LLM call: {elapsed:.1f}s")

        agent = parse_llm_extraction(response, spec.paper_id) if response else _empty_agent_dict()
        profile = build_reproduction_profile(spec.paper_id, gold, agent, spec.task_type)
        return profile, gold, agent

    def run_all(self) -> dict:
        results = {}
        profiles = {}

        for i, spec in enumerate(self.specs):
            print(f"\n{'='*70}")
            print(f"[{i+1}/{len(self.specs)}] {spec.paper_id}")
            print(f"  {spec.title[:80]}")
            print(f"  {spec.venue} ({spec.year}) | task_type={spec.task_type.value}")
            print(f"{'='*70}")

            try:
                profile, gold, agent = self.run_single(spec)
                results[spec.paper_id] = {"profile": profile, "gold": gold,
                                          "agent": agent, "status": "OK"}
                profiles[spec.paper_id] = profile
                print_profile_summary(profile, spec.task_type, spec.paper_id)
            except Exception as e:
                print(f"  ERROR: {e}")
                traceback.print_exc()
                results[spec.paper_id] = {"status": "ERROR", "error": str(e)}

        analysis = run_m1_analysis(profiles, {s.paper_id: s.task_type for s in self.specs})
        return {"results": results, "analysis": analysis,
                "model": self.model_name, "timestamp": datetime.now().isoformat()}


# ── Display ───────────────────────────────────────────────────────────────────

def print_profile_summary(profile: ReproductionProfile, task_type: TaskType, paper_id: str) -> None:
    components = ["data_source", "sample", "indicator", "model", "result_table", "claim"]
    all_dims = ["fidelity", "executability", "numerical_accuracy", "claim_consistency", "auditability"]

    print(f"\n  {'Component':<16}", end="")
    for d in all_dims:
        print(f" {d[:6]:>8}", end="")
    print(f"  {'avg':>6}")
    print("  " + "-" * 72)

    for comp in components:
        cs = profile.component_scores.get(comp)
        print(f"  {comp:<16}", end="")
        comp_scores = []
        for dim in all_dims:
            if cs and dim in cs.dimension_scores:
                s = cs.dimension_scores[dim].score
                comp_scores.append(s)
                print(f" {s:8.3f}", end="")
            else:
                print(f" {'—':>8}")
        avg = sum(comp_scores) / len(comp_scores) if comp_scores else 0
        print(f" {avg:6.3f}")

    print("  " + "-" * 72)
    print(f"  {'AVERAGE':<16}", end="")
    dim_totals = {d: [] for d in all_dims}
    for comp in components:
        cs = profile.component_scores.get(comp)
        if cs:
            for dim in all_dims:
                if dim in cs.dimension_scores:
                    dim_totals[dim].append(cs.dimension_scores[dim].score)
    for d in all_dims:
        vals = dim_totals[d]
        avg = sum(vals) / len(vals) if vals else 0
        print(f" {avg:8.3f}", end="")
    print()

    maturity = compute_maturity_level(profile, task_type)
    flags = detect_spurious_reproduction(profile)
    print(f"\n  Maturity: {format_maturity(maturity, task_type)}")
    if flags:
        print(f"  ⚠️  Spurious: {', '.join(flags)}")
    else:
        print(f"  ✓ Spurious: none detected")


# ── M1 Analysis ──────────────────────────────────────────────────────────────

def run_m1_analysis(profiles: dict[str, ReproductionProfile],
                    task_types: dict[str, TaskType]) -> dict:
    all_dims = ["fidelity", "executability", "numerical_accuracy", "claim_consistency", "auditability"]
    components = ["data_source", "sample", "indicator", "model", "result_table", "claim"]

    print(f"\n{'='*70}")
    print("  M1 VALIDATION ANALYSIS")
    print(f"{'='*70}")

    # Test 1: Inter-dimension correlation
    print("\n── Test 1: Inter-dimension Spearman correlation ──")
    dim_scores = {d: [] for d in all_dims}
    for pid, profile in profiles.items():
        for dim in all_dims:
            vals = [cs.dimension_scores[dim].score
                    for cs in profile.component_scores.values()
                    if dim in cs.dimension_scores]
            avg = sum(vals) / len(vals) if vals else 0
            dim_scores[dim].append(avg)

    correlations = {}
    for i, d1 in enumerate(all_dims):
        for j, d2 in enumerate(all_dims):
            if j <= i:
                continue
            x, y = dim_scores[d1], dim_scores[d2]
            n = len(x)
            if n < 3:
                r = 0
            else:
                def rankify(arr):
                    si = sorted(range(len(arr)), key=lambda k: arr[k])
                    ranks = [0] * len(arr)
                    for rank, idx in enumerate(si):
                        ranks[idx] = rank + 1
                    return ranks
                rx, ry = rankify(x), rankify(y)
                mx, my = sum(rx)/n, sum(ry)/n
                num = sum((rx[k]-mx)*(ry[k]-my) for k in range(n))
                den = math.sqrt(sum((rx[k]-mx)**2 for k in range(n)) *
                               sum((ry[k]-my)**2 for k in range(n)))
                r = num/den if den > 1e-10 else 0
            correlations[(d1, d2)] = r

    high_pairs = []
    for (d1, d2), r in sorted(correlations.items(), key=lambda x: -abs(x[1])):
        flag = " ⚠️  HIGH" if abs(r) > 0.85 else ""
        if abs(r) > 0.85:
            high_pairs.append(f"{d1}/{d2}")
        print(f"    {d1} ↔ {d2}: ρ = {r:+.3f}{flag}")
    test1_pass = len(high_pairs) < 3  # Allow up to 2 highly correlated pairs
    print(f"  {'✓ PASS' if test1_pass else '⚠️  WARNING'}: {len(high_pairs)} highly correlated pairs")

    # Test 2: Failure pattern diversity
    print("\n── Test 2: Component score variation across papers ──")
    patterns = {}
    for pid, profile in profiles.items():
        comp_avgs = {}
        for comp_name in components:
            cs = profile.component_scores.get(comp_name)
            if cs:
                comp_avgs[comp_name] = cs.aggregate
        if comp_avgs:
            weakest = min(comp_avgs, key=comp_avgs.get)
            strongest = max(comp_avgs, key=comp_avgs.get)
            spread = comp_avgs[strongest] - comp_avgs[weakest]
            patterns[pid] = (weakest, comp_avgs[weakest], spread)

    unique_weakest = len(set(p[0] for p in patterns.values())) if patterns else 0
    non_uniform = sum(1 for p in patterns.values() if p[2] > 0.3) if patterns else 0

    for pid, (weakest, val, spread) in patterns.items():
        print(f"    {pid:<35} weakest={weakest:<14} ({val:.2f}) spread={spread:.2f}")
    test2_pass = unique_weakest >= 2 or non_uniform >= 3
    print(f"  Unique weakest components: {unique_weakest} | Non-uniform papers: {non_uniform}")
    print(f"  {'✓ PASS' if test2_pass else '⚠️  WARNING'}")

    # Test 3: Per-dimension stats
    print("\n── Test 3: Per-dimension score distribution ──")
    dim_stats = {}
    for dim in all_dims:
        vals = []
        for pid, profile in profiles.items():
            for cs in profile.component_scores.values():
                if dim in cs.dimension_scores:
                    vals.append(cs.dimension_scores[dim].score)
        if vals:
            mean_v = sum(vals)/len(vals)
            dim_stats[dim] = {
                "mean": round(mean_v, 3),
                "min": round(min(vals), 3),
                "max": round(max(vals), 3),
                "std": round((sum((v-mean_v)**2 for v in vals)/len(vals))**0.5, 3),
            }
            print(f"    {dim:<22}: mean={dim_stats[dim]['mean']:.3f} "
                  f"min={dim_stats[dim]['min']:.3f} max={dim_stats[dim]['max']:.3f} "
                  f"std={dim_stats[dim]['std']:.3f}")

    # Test 4: Spurious detection
    print("\n── Test 4: Spurious reproduction detection ──")
    all_flags = {}
    for pid, profile in profiles.items():
        flags = detect_spurious_reproduction(profile)
        all_flags[pid] = flags
        tt = task_types.get(pid, TaskType.METHOD)
        mat = compute_maturity_level(profile, tt)
        if flags:
            print(f"    {pid}: maturity={format_maturity(mat, tt)}  ⚠️  {', '.join(flags)}")
        else:
            print(f"    {pid}: maturity={format_maturity(mat, tt)}  ✓ Clean")
    total_flags = sum(len(f) for f in all_flags.values())

    # Maturity distribution
    print("\n── Maturity Distribution ──")
    mat_dist = {}
    for pid, profile in profiles.items():
        tt = task_types.get(pid, TaskType.METHOD)
        level = compute_maturity_level(profile, tt)
        label = format_maturity(level, tt)
        mat_dist[label] = mat_dist.get(label, 0) + 1
    for label, count in sorted(mat_dist.items()):
        bar = "█" * count
        print(f"    {label}: {bar} ({count})")

    return {
        "test1_correlation": {"pass": test1_pass, "high_pairs": high_pairs,
                             "correlations": {f"{d1}_{d2}": round(r, 4) for (d1, d2), r in correlations.items()}},
        "test2_failure_patterns": {"pass": test2_pass, "unique_weakest": unique_weakest,
                                   "non_uniform_papers": non_uniform,
                                   "patterns": {pid: {"weakest": p[0], "value": round(p[1], 3), "spread": round(p[2], 3)}
                                               for pid, p in patterns.items()}},
        "test3_dim_stats": dim_stats,
        "test4_spurious": {"total_flags": total_flags, "flags": all_flags},
        "maturity_distribution": mat_dist,
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="M1 Full Benchmark — paper validation from metadata")
    parser.add_argument("--model", type=str, default="gemma",
                       help="Model: gemma, qwen3-32b, deepseek-v4-pro, mock")
    parser.add_argument("--papers", type=str, default="all",
                       help="Paper indices (e.g. '1-3', '4,5,6', 'all')")
    parser.add_argument("--max-papers", type=int, default=None,
                       help="Cap on total papers (default: all from metadata, ~114)")
    parser.add_argument("--output", type=str, default="refine-logs")
    args = parser.parse_args()

    specs = _build_paper_specs_from_metadata(max_papers=args.max_papers)

    # Filter papers
    if args.papers != "all":
        selected = set()
        for part in args.papers.split(","):
            part = part.strip()
            if "-" in part:
                lo, hi = part.split("-", 1)
                selected.update(range(int(lo), int(hi) + 1))
            else:
                selected.add(int(part))
        specs = [s for i, s in enumerate(specs, 1) if i in selected]

    print("=" * 70)
    print("  M1: FULL BENCHMARK — 10-PAPER FRAMEWORK VALIDATION")
    print(f"  Papers: {len(specs)} | Model: {args.model}")
    for i, s in enumerate(specs, 1):
        src = "SciSciPaper" if s.sci_paper else ("md+gold" if s.md_path else "gold-only")
        print(f"    {i}. {s.paper_id} [{s.task_type.value}] ({src})")
    print("=" * 70)

    runner = M1FullRunner(model_name=args.model, specs=specs, output_dir=args.output)
    t0 = time.time()
    output = runner.run_all()
    elapsed = time.time() - t0

    # Save
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.output) / f"m1_full_benchmark_{args.model}_{ts}.json"

    serializable = {
        "run_id": ts, "timestamp": output["timestamp"],
        "model": output["model"], "n_papers": len(specs),
        "elapsed_s": round(elapsed, 1), "analysis": output["analysis"],
        "paper_profiles": {},
    }
    for pid, result in output["results"].items():
        if result["status"] == "OK":
            profile = result["profile"]
            serializable["paper_profiles"][pid] = {
                "matrix": profile.to_matrix(),
                "maturity": compute_maturity_level(profile,
                    {s.paper_id: s.task_type for s in specs}.get(pid, TaskType.METHOD)),
                "spurious_flags": detect_spurious_reproduction(profile),
                "component_aggregates": {
                    comp: round(cs.aggregate, 4)
                    for comp, cs in profile.component_scores.items()
                },
            }

    with open(out_path, "w") as f:
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {out_path}")

    # Summary
    analysis = output["analysis"]
    print(f"\n{'='*70}")
    print("  M1 SUMMARY")
    print(f"{'='*70}")
    print(f"  Papers: {len(specs)} | Model: {args.model} | Time: {elapsed:.0f}s")
    print(f"  Test 1 (correlation): {'PASS' if analysis['test1_correlation']['pass'] else 'WARN'}")
    print(f"  Test 2 (failure patterns): {'PASS' if analysis['test2_failure_patterns']['pass'] else 'WARN'}")
    print(f"  Test 4 (spurious flags): {analysis['test4_spurious']['total_flags']} total")
    print(f"  Maturity: {analysis['maturity_distribution']}")


if __name__ == "__main__":
    main()
