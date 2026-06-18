#!/usr/bin/env python3
"""M1: Framework Validation — 5-dimension reproduction quality scoring with real LLM.

Smoke test (3 pilot papers) → full run (10 papers).

Pipeline:
  1. Gold annotations: SciSciPaper → gold component dicts
  2. LLM prompt: paper summary → LLM extracts 6 components as JSON
  3. Parse LLM output → agent dict compatible with dimension scorers
  4. Build ReproductionProfile (gold + agent → 6×5 matrix)
  5. M1 validation: inter-dim correlation, failure patterns, spurious detection

Usage:
    python scripts/m1_framework_validation.py --smoke           # 3 pilot papers
    python scripts/m1_framework_validation.py --smoke --mock    # smoke with MockLLM
    python scripts/m1_framework_validation.py --full            # 10 papers
    python scripts/m1_framework_validation.py --papers wu2019_disruption,ke2023_normalized_impact
"""

from __future__ import annotations

import json
import os
import sys
import time
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from typing import Any

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
    DimensionScore,
    ComponentScore,
    COMPONENT_DIMENSION_MAP,
)
from src.sciscigpt_local.llm_backends import LLMConfig, load_llm_from_config


# ── Paper registry ──────────────────────────────────────────────────────────

PILOT_PAPERS: dict[str, SciSciPaper] = {
    "wu2019_disruption": create_wu2019(),
    "ke2023_normalized_impact": create_ke2023(),
    "arts2025_frontier_scientists": create_arts2025(),
}

# Task types for each pilot paper (from M0 runs)
PILOT_TASK_TYPES: dict[str, TaskType] = {
    "wu2019_disruption": TaskType.DATA_SUB,
    "ke2023_normalized_impact": TaskType.STRICT,
    "arts2025_frontier_scientists": TaskType.METHOD,
}


# ── Gold annotation builders ─────────────────────────────────────────────────

def paper_to_rich_summary(paper: SciSciPaper) -> str:
    """Build a structured summary of the paper for the LLM prompt.

    Uses the SciSciPaper annotation to create a dense, information-rich
    description that simulates what an agent would extract from reading
    the full paper.
    """
    parts = []
    parts.append(f"Title: {paper.title}")
    parts.append(f"Authors: {', '.join(paper.authors)}")
    parts.append(f"Venue: {paper.venue} ({paper.year})")
    parts.append(f"DOI: {paper.doi}")
    parts.append("")
    parts.append(f"Research Idea: {paper.research_idea}")
    parts.append(f"Research Question: {paper.research_question}")
    parts.append("")
    parts.append("Hypotheses:")
    for h in paper.hypotheses:
        parts.append(f"  - {h}")
    parts.append("")
    parts.append(f"Data Source: {paper.data_source}")
    parts.append(f"Data Description: {paper.data_description}")
    parts.append(f"Available Fields: {', '.join(paper.available_fields)}")
    parts.append("")
    parts.append("Variables:")
    for label, var_list in [
        ("Independent", paper.independent_variables),
        ("Dependent", paper.dependent_variables),
        ("Control", paper.control_variables),
    ]:
        for v in var_list:
            parts.append(f"  [{label}] {v.get('name', '')}: {v.get('definition', v.get('formula', ''))}")
    parts.append("")
    parts.append(f"Sample Scope: {json.dumps(paper.sample_scope)}")
    parts.append("")
    sm = paper.experiment_design_gold.get("statistical_method", {})
    parts.append(f"Statistical Method: {sm.get('family', '')} — {sm.get('specification', '')}")
    parts.append("")
    parts.append(f"Result Claims: {json.dumps(paper.result_claims)}")
    parts.append(f"Conclusion Claims: {json.dumps(paper.conclusion_claims)}")
    parts.append(f"Limitations: {json.dumps(paper.limitations)}")

    return "\n".join(parts)


def build_gold_dict(paper: SciSciPaper) -> dict:
    """Convert SciSciPaper annotation to gold component dict for dimension scoring.

    Maps the structured annotation fields to the format expected by
    score_fidelity(), score_numerical_accuracy(), etc.
    """
    # Build spec_elements from experiment_design_gold
    sm = paper.experiment_design_gold.get("statistical_method", {})
    spec_elements = []
    if sm.get("family"):
        spec_elements.append(sm["family"])
    if sm.get("estimation"):
        spec_elements.append(sm["estimation"])
    if sm.get("specification", ""):
        # Extract key terms
        spec_text = sm["specification"].lower()
        for term in ["ols", "logit", "fixed_effects", "year_fe", "firm_fe",
                     "clustered_se", "poisson", "negative_binomial", "descriptive"]:
            if term in spec_text:
                spec_elements.append(term.replace("_", " "))
    gs = paper.experiment_design_gold.get("grouping_strategy", {})
    if gs.get("groups"):
        spec_elements.extend(gs["groups"])

    # Coefficients from result_claims
    coefficients = {}
    for rc in paper.result_claims:
        name = rc.get("metric", "unknown")
        val_str = rc.get("value", "")
        # Try to parse numeric values
        try:
            coefficients[name] = float(val_str.replace("%", "").split("+")[0].strip())
        except (ValueError, AttributeError):
            coefficients[name] = 0.0

    # Indicator formula
    dv = paper.dependent_variables[0] if paper.dependent_variables else {}
    formula = dv.get("formula", "")

    # Target values from result_claims
    target_values = []
    for rc in paper.result_claims:
        val_str = rc.get("value", "")
        try:
            val = float(val_str.replace("%", "").replace("+", "").replace("−", "-").split()[0])
        except (ValueError, AttributeError):
            val = 0.0
        target_values.append({
            "label": rc.get("metric", ""),
            "value": val,
        })

    # Expected direction
    directions = [rc.get("direction", "") for rc in paper.result_claims]
    expected_direction = directions[0] if directions else ""

    return {
        "data_source": {
            "data_source": paper.data_source,
            "data_description": paper.data_description,
            "filter_rules": [paper.data_source],
        },
        "sample": {
            "data_source": paper.data_source,
            "N": 0,  # Unknown without actual data
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


# ── LLM Component Extraction ─────────────────────────────────────────────────

EXTRACTION_SYSTEM_PROMPT = """You are an expert in computational scientometrics and research methodology.
Your task is to decompose a research paper into its 6 methodological components.

For each component, extract the relevant information as structured JSON.
Be precise and faithful to the paper — do not invent or assume details not present.

CRITICAL: Output ONLY valid JSON. No markdown, no explanation outside the JSON.
Start with '{' and end with '}'.

For fields you cannot determine from the paper text, use null or empty values.
Do NOT guess — only include what the paper explicitly states."""


def build_extraction_user_prompt(paper: SciSciPaper) -> str:
    """Build the user prompt asking the LLM to extract 6 components."""
    summary = paper_to_rich_summary(paper)
    return f"""Decompose the following research paper into 6 methodological components.
Return a single JSON object with these exact keys:

{{
  "data_source": {{
    "data_source": "Name of the dataset used (e.g., Web of Science, USPTO)",
    "data_description": "Brief description of what the data contains"
  }},
  "sample": {{
    "N": <sample size as integer, or null if unknown>,
    "time_window": "Time period covered (e.g., 1954-2014)",
    "filter_rules": ["list", "of", "inclusion/exclusion", "criteria"]
  }},
  "indicator": {{
    "formula": "The key bibliometric indicator formula (mathematical notation)",
    "parameters": "Key parameters used in the formula"
  }},
  "model": {{
    "spec_elements": ["list", "of", "model", "specification", "elements"],
    "model_type": "OLS, logit, fixed_effects, descriptive, etc.",
    "dependent_variable": "Name of the dependent variable",
    "independent_variables": ["list", "of", "independent", "variables"],
    "control_variables": ["list", "of", "control", "variables"],
    "fixed_effects": ["any", "fixed", "effects", "used"],
    "standard_errors": "Type of standard errors (robust, clustered, etc.) or null"
  }},
  "result_table": {{
    "main_findings": [
      {{"metric": "name", "value": "reported value/effect size", "direction": "positive/negative/null", "significance": "p-value or significance statement"}}
    ],
    "key_coefficients": {{"variable_name": "reported coefficient value"}}
  }},
  "claim": {{
    "conclusion_claims": ["claim 1", "claim 2", ...],
    "limitations": ["limitation 1", ...]
  }}
}}

Paper text:
---
{summary}
---"""


def parse_llm_extraction(response: Any) -> dict:
    """Parse LLM response into agent dict compatible with dimension scorers.

    Handles both string JSON and structured content blocks.
    """
    # Extract text from response
    text = ""
    if isinstance(response, str):
        text = response
    elif isinstance(response, list):
        # Handle [{"type": "text", "text": "..."}, ...] format
        texts = []
        for block in response:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif "text" in block:
                    texts.append(block["text"])
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

    # Try to extract JSON from the response
    # First try: direct parse
    try:
        extracted = json.loads(text)
        if isinstance(extracted, dict):
            return _convert_extraction_to_agent(extracted)
    except json.JSONDecodeError:
        pass

    # Second try: find JSON block between { and }
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
                json_str = text[start:i+1]
                try:
                    extracted = json.loads(json_str)
                    if isinstance(extracted, dict):
                        return _convert_extraction_to_agent(extracted)
                except json.JSONDecodeError:
                    continue
                start = -1

    # Fallback: return empty agent dict
    print("  WARNING: Could not parse LLM extraction — using empty agent dict")
    return _empty_agent_dict()


def _convert_extraction_to_agent(extracted: dict) -> dict:
    """Convert LLM JSON extraction to agent dict format for dimension scoring."""
    ds = extracted.get("data_source", {})
    sample = extracted.get("sample", {})
    indicator = extracted.get("indicator", {})
    model = extracted.get("model", {})
    result = extracted.get("result_table", {})
    claim = extracted.get("claim", {})

    # Parse model coefficients from result_table.key_coefficients
    coefficients = {}
    raw_coefs = result.get("key_coefficients", {})
    if isinstance(raw_coefs, dict):
        for k, v in raw_coefs.items():
            try:
                coefficients[k] = float(v) if isinstance(v, str) else v
            except (ValueError, TypeError):
                coefficients[k] = 0.0

    # Parse target values
    reproduced_values = []
    main_findings = result.get("main_findings", [])
    if isinstance(main_findings, list):
        for mf in main_findings:
            if isinstance(mf, dict):
                val_str = mf.get("value", "0")
                try:
                    val = float(str(val_str).replace("%", "").replace("+", "").split()[0])
                except (ValueError, AttributeError):
                    val = 0.0
                reproduced_values.append({"label": mf.get("metric", ""), "value": val})

    # Direction from first finding
    observed_direction = ""
    if main_findings and isinstance(main_findings[0], dict):
        observed_direction = main_findings[0].get("direction", "")

    # Determine executability — in M1 smoke test, we're extracting not executing,
    # so we mark code_executed based on whether the LLM provided substantive content
    has_substance = {
        "data_source": bool(ds.get("data_source")),
        "sample": bool(sample.get("filter_rules") or sample.get("N")),
        "indicator": bool(indicator.get("formula")),
        "model": bool(model.get("spec_elements") or model.get("model_type")),
        "result_table": bool(main_findings or coefficients),
    }

    return {
        "data_source": {
            "data_source": ds.get("data_source", ""),
            "data_description": ds.get("data_description", ""),
            "code_executed": {"data_source": has_substance["data_source"]},
            "traceable": {"data_source": bool(ds.get("data_source"))},
            "hard_coded": {"data_source": False},
            "hallucinated": {"data_source": False},
        },
        "sample": {
            "N": sample.get("N") or 0,
            "time_window": sample.get("time_window", ""),
            "filter_rules": sample.get("filter_rules", []) if isinstance(sample.get("filter_rules"), list) else [],
            "code_executed": {"sample": has_substance["sample"]},
            "traceable": {"sample": bool(sample.get("filter_rules"))},
            "hard_coded": {"sample": False},
            "hallucinated": {"sample": False},
        },
        "indicator": {
            "formula": indicator.get("formula", ""),
            "parameters": indicator.get("parameters", ""),
            "indicator_stats": {"mean": 0, "std": 0},
            "code_executed": {"indicator": has_substance["indicator"]},
            "traceable": {"indicator": bool(indicator.get("formula"))},
            "hard_coded": {"indicator": False},
            "hallucinated": {"indicator": False},
        },
        "model": {
            "spec_elements": model.get("spec_elements", []) if isinstance(model.get("spec_elements"), list) else [],
            "model_type": model.get("model_type", ""),
            "dependent_variable": model.get("dependent_variable", ""),
            "independent_variables": model.get("independent_variables", []) if isinstance(model.get("independent_variables"), list) else [],
            "control_variables": model.get("control_variables", []) if isinstance(model.get("control_variables"), list) else [],
            "coefficients": coefficients,
            "code_executed": {"model": has_substance["model"]},
            "traceable": {"model": bool(model.get("spec_elements"))},
            "hard_coded": {"model": False},
            "hallucinated": {"model": False},
        },
        "result_table": {
            "produced_tables": [f"Finding: {mf.get('metric', '')}" for mf in main_findings] if main_findings else [],
            "reproduced_values": reproduced_values,
            "observed_direction": observed_direction,
            "code_executed": {"result_table": has_substance["result_table"]},
            "traceable": {"result_table": bool(main_findings)},
            "hard_coded": {"result_table": False},
            "hallucinated": {"result_table": False},
        },
        "claim": {
            "conclusion_claims": claim.get("conclusion_claims", []) if isinstance(claim.get("conclusion_claims"), list) else [],
            "limitations": claim.get("limitations", []) if isinstance(claim.get("limitations"), list) else [],
        },
    }


def _empty_agent_dict() -> dict:
    """Return an empty agent dict for when LLM extraction fails."""
    empty_component = {
        "code_executed": {},
        "traceable": {},
        "hard_coded": {},
        "hallucinated": {},
    }
    return {
        "data_source": {**empty_component, "data_source": ""},
        "sample": {**empty_component, "N": 0, "filter_rules": []},
        "indicator": {**empty_component, "formula": "", "indicator_stats": {"mean": 0, "std": 0}},
        "model": {**empty_component, "spec_elements": [], "coefficients": {}},
        "result_table": {**empty_component, "produced_tables": [], "reproduced_values": [], "observed_direction": ""},
        "claim": {**empty_component, "conclusion_claims": []},
    }


# ── LLM loading ──────────────────────────────────────────────────────────────

def get_available_models() -> dict[str, LLMConfig]:
    models = {}

    # Qwen3-32B via local vLLM (no auth)
    qwen_url = os.environ.get("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
    models["qwen3-32b"] = LLMConfig(
        name="qwen3-32b", provider="openai",
        model=os.environ.get("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/"),
        api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
        base_url=qwen_url,
        temperature=0.0,
        max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4096")),
    )

    # DeepSeek-V4-Pro via Anthropic proxy
    if os.environ.get("ANTHROPIC_AUTH_TOKEN") and os.environ.get("ANTHROPIC_BASE_URL"):
        models["deepseek-v4-pro"] = LLMConfig(
            name="deepseek-v4-pro", provider="anthropic",
            model="deepseek-v4-pro",
            api_key=os.environ["ANTHROPIC_AUTH_TOKEN"],
            base_url=os.environ["ANTHROPIC_BASE_URL"],
            temperature=0.0, max_tokens=4096,
        )

    # Gemma-4-26B via local vLLM (no auth, LAN: 192.168.1.127:8000)
    models["gemma"] = LLMConfig(
        name="gemma", provider="openai",
        model="gemma-4-26B-A4B-it",
        api_key="not-needed",
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

    # Gemma via local vLLM — no Qwen-specific extra_body
    if model_name == "gemma":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ValueError("langchain-openai not installed")
        return ChatOpenAI(
            model=config.model,
            api_key=config.api_key,
            base_url=config.base_url,
            temperature=0.0,
            max_tokens=4096,
        )

    return load_llm_from_config(config)


# ── Core runner ──────────────────────────────────────────────────────────────

class M1Runner:
    """M1 Framework Validation: run LLM extraction → dimension scoring → analysis."""

    def __init__(self, model_name: str = "qwen3-32b",
                 papers: dict[str, SciSciPaper] | None = None,
                 task_types: dict[str, TaskType] | None = None,
                 output_dir: str | Path = "refine-logs"):
        self.model_name = model_name
        self.papers = papers or PILOT_PAPERS
        self.task_types = task_types or PILOT_TASK_TYPES
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = None

    def run_single(self, paper_id: str) -> tuple[ReproductionProfile, dict, dict]:
        """Run extraction + scoring for a single paper.

        Returns (profile, gold_dict, agent_dict).
        """
        paper = self.papers[paper_id]
        task_type = self.task_types.get(paper_id, TaskType.METHOD)

        # Build gold
        gold = build_gold_dict(paper)

        # LLM extraction
        if self.llm is None:
            self.llm = create_llm(self.model_name)

        system_prompt = EXTRACTION_SYSTEM_PROMPT
        user_prompt = build_extraction_user_prompt(paper)

        print(f"  Extracting components via {self.model_name}...")
        t0 = time.time()

        try:
            response = self.llm.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ])
        except Exception as e:
            print(f"  LLM call failed: {e}")
            traceback.print_exc()
            response = None

        elapsed = time.time() - t0
        print(f"  LLM call: {elapsed:.1f}s")

        # Parse
        agent = parse_llm_extraction(response) if response else _empty_agent_dict()

        # Build profile
        profile = build_reproduction_profile(paper_id, gold, agent, task_type)

        return profile, gold, agent

    def run_all(self) -> dict:
        """Run extraction + scoring for all papers. Returns results dict."""
        results = {}
        profiles = {}

        for i, paper_id in enumerate(self.papers):
            print(f"\n[{i+1}/{len(self.papers)}] {paper_id}")
            print("-" * 60)

            try:
                profile, gold, agent = self.run_single(paper_id)
                results[paper_id] = {
                    "profile": profile,
                    "gold": gold,
                    "agent": agent,
                    "status": "OK",
                }
                profiles[paper_id] = profile
                print_profile_summary(profile, self.task_types.get(paper_id, TaskType.METHOD))

            except Exception as e:
                print(f"  ERROR: {e}")
                traceback.print_exc()
                results[paper_id] = {"status": "ERROR", "error": str(e)}

        # Analysis
        analysis = run_m1_analysis(profiles, self.task_types)

        return {
            "results": results,
            "analysis": analysis,
            "model": self.model_name,
            "timestamp": datetime.now().isoformat(),
        }


# ── Display helpers ──────────────────────────────────────────────────────────

def print_profile_summary(profile: ReproductionProfile, task_type: TaskType) -> None:
    """Print the 6×5 component-dimension matrix."""
    components = ["data_source", "sample", "indicator", "model", "result_table", "claim"]
    all_dims = ["fidelity", "executability", "numerical_accuracy", "claim_consistency", "auditability"]

    print(f"\n  {'Component':<16}", end="")
    for d in all_dims:
        print(f" {d[:6]:>8}", end="")
    print(f"  {'avg':>6}")
    print("  " + "-" * 72)

    dim_totals = {d: [] for d in all_dims}

    for comp in components:
        cs = profile.component_scores.get(comp)
        print(f"  {comp:<16}", end="")
        comp_scores = []
        for dim in all_dims:
            if cs and dim in cs.dimension_scores:
                s = cs.dimension_scores[dim].score
                comp_scores.append(s)
                dim_totals[dim].append(s)
                print(f" {s:8.3f}", end="")
            else:
                print(f" {'—':>8}", end="")
        avg = sum(comp_scores) / len(comp_scores) if comp_scores else 0
        print(f" {avg:6.3f}")

    # Averages
    print("  " + "-" * 72)
    print(f"  {'AVERAGE':<16}", end="")
    for d in all_dims:
        vals = dim_totals[d]
        avg = sum(vals) / len(vals) if vals else 0
        print(f" {avg:8.3f}", end="")
    print()

    # Maturity
    maturity = compute_maturity_level(profile, task_type)
    print(f"\n  Maturity: {format_maturity(maturity, task_type)}")

    # Spurious flags
    flags = detect_spurious_reproduction(profile)
    if flags:
        print(f"  Spurious: {', '.join(flags)}")
    else:
        print(f"  Spurious: none detected")


def print_profile_matrix(profile: ReproductionProfile, label: str) -> None:
    """Print full 6×5 matrix with label."""
    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")
    print_profile_summary(profile, TaskType.METHOD)


# ── M1 Analysis ──────────────────────────────────────────────────────────────

def run_m1_analysis(profiles: dict[str, ReproductionProfile],
                    task_types: dict[str, TaskType]) -> dict:
    """Run the 4 M1 validation tests across all papers."""
    import math

    all_dims = ["fidelity", "executability", "numerical_accuracy", "claim_consistency", "auditability"]
    components = ["data_source", "sample", "indicator", "model", "result_table", "claim"]

    print(f"\n{'='*70}")
    print("  M1 VALIDATION ANALYSIS")
    print(f"{'='*70}")

    # ── Test 1: Inter-dimension correlation ──
    print("\n── Test 1: Inter-dimension Spearman correlation ──")
    # Collect dimension averages per paper
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
            x = dim_scores[d1]
            y = dim_scores[d2]
            n = len(x)
            if n < 3:
                r = 0
            else:
                # Spearman (rank) correlation
                def rankify(arr):
                    sorted_idx = sorted(range(len(arr)), key=lambda k: arr[k])
                    ranks = [0] * len(arr)
                    for rank, idx in enumerate(sorted_idx):
                        ranks[idx] = rank + 1
                    return ranks
                rx = rankify(x)
                ry = rankify(y)
                mx, my = sum(rx) / n, sum(ry) / n
                num = sum((rx[k] - mx) * (ry[k] - my) for k in range(n))
                den = math.sqrt(sum((rx[k] - mx) ** 2 for k in range(n)) *
                               sum((ry[k] - my) ** 2 for k in range(n)))
                r = num / den if den > 1e-10 else 0
            correlations[(d1, d2)] = r

    for (d1, d2), r in sorted(correlations.items(), key=lambda x: -abs(x[1])):
        flag = " ⚠️  HIGH" if abs(r) > 0.85 else ""
        print(f"    {d1} ↔ {d2}: ρ = {r:+.3f}{flag}")

    high_corr = sum(1 for r in correlations.values() if abs(r) > 0.85)
    test1_pass = high_corr == 0
    print(f"  {'✓ PASS' if test1_pass else '⚠️  WARNING'}: {high_corr} pair(s) exceed 0.85 threshold")

    # ── Test 2: Failure pattern diversity ──
    print("\n── Test 2: Failure pattern diversity ──")
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

    unique_weakest = len(set(p[0] for p in patterns.values()))
    non_uniform = sum(1 for p in patterns.values() if p[2] > 0.3)

    for pid, (weakest, val, spread) in patterns.items():
        comps_str = ", ".join(f"{c[:4]}={profile.component_scores[c].aggregate:.2f}"
                              if c in profile.component_scores else f"{c[:4]}=NA"
                              for c in components[:4])
        print(f"    {pid:<35} weakest={weakest:<14} ({val:.2f}) spread={spread:.2f}")

    test2_pass = unique_weakest >= 2 or non_uniform >= 2  # Relaxed for 3 papers
    print(f"  Unique weakest components: {unique_weakest} (≥2 expected)")
    print(f"  Papers with non-uniform scores (spread >0.3): {non_uniform}")
    print(f"  {'✓ PASS' if test2_pass else '⚠️  WARNING'}: component decomposition shows variation")

    # ── Test 3: Dimension score distribution ──
    print("\n── Test 3: Per-dimension score distribution ──")
    dim_stats = {}
    for dim in all_dims:
        vals = []
        for pid, profile in profiles.items():
            for cs in profile.component_scores.values():
                if dim in cs.dimension_scores:
                    vals.append(cs.dimension_scores[dim].score)
        if vals:
            dim_stats[dim] = {
                "mean": sum(vals) / len(vals),
                "min": min(vals),
                "max": max(vals),
                "std": (sum((v - sum(vals)/len(vals))**2 for v in vals) / len(vals)) ** 0.5,
            }
            print(f"    {dim:<22}: mean={dim_stats[dim]['mean']:.3f} "
                  f"min={dim_stats[dim]['min']:.3f} max={dim_stats[dim]['max']:.3f} "
                  f"std={dim_stats[dim]['std']:.3f}")

    # ── Test 4: Spurious detection across papers ──
    print("\n── Test 4: Spurious reproduction detection ──")
    all_flags = {}
    for pid, profile in profiles.items():
        flags = detect_spurious_reproduction(profile)
        all_flags[pid] = flags
        task_type = task_types.get(pid, TaskType.METHOD)
        maturity = compute_maturity_level(profile, task_type)
        if flags:
            print(f"    {pid}: maturity={format_maturity(maturity, task_type)}  ⚠️  {', '.join(flags)}")
        else:
            print(f"    {pid}: maturity={format_maturity(maturity, task_type)}  ✓ Clean")

    total_flags = sum(len(f) for f in all_flags.values())
    print(f"  Total flags: {total_flags} across {len(profiles)} papers")

    return {
        "test1_correlation": {
            "pass": test1_pass,
            "high_pairs": high_corr,
            "correlations": {f"{d1}_{d2}": round(r, 4) for (d1, d2), r in correlations.items()},
        },
        "test2_failure_patterns": {
            "pass": test2_pass,
            "unique_weakest": unique_weakest,
            "non_uniform_papers": non_uniform,
            "patterns": {pid: {"weakest": p[0], "value": round(p[1], 3), "spread": round(p[2], 3)}
                        for pid, p in patterns.items()},
        },
        "test3_dim_stats": {dim: {k: round(v, 4) for k, v in stats.items()}
                           for dim, stats in dim_stats.items()},
        "test4_spurious": {
            "total_flags": total_flags,
            "flags": all_flags,
        },
    }


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="M1: Framework Validation")
    parser.add_argument("--smoke", action="store_true",
                       help="Run smoke test on 3 pilot papers")
    parser.add_argument("--full", action="store_true",
                       help="Run full 10-paper validation")
    parser.add_argument("--papers", type=str, default="",
                       help="Comma-separated paper IDs")
    parser.add_argument("--model", type=str, default="qwen3-32b",
                       help="Model name (qwen3-32b, deepseek-v4-pro, mock)")
    parser.add_argument("--output", type=str, default="refine-logs",
                       help="Output directory")
    args = parser.parse_args()

    # Determine papers
    if args.papers:
        paper_ids = [p.strip() for p in args.papers.split(",")]
        papers = {pid: PILOT_PAPERS[pid] for pid in paper_ids if pid in PILOT_PAPERS}
        if not papers:
            print(f"No papers found. Available: {list(PILOT_PAPERS.keys())}")
            return
    elif args.full:
        papers = PILOT_PAPERS  # TODO: expand to 10
        print("Full run: using pilot papers (expand to 10)")
    elif args.smoke:
        papers = PILOT_PAPERS
    else:
        print("Specify --smoke, --full, or --papers")
        return

    print("=" * 70)
    print("  M1: FRAMEWORK VALIDATION")
    print(f"  Papers: {list(papers.keys())}")
    print(f"  Model: {args.model}")
    print("=" * 70)

    task_types = {pid: PILOT_TASK_TYPES.get(pid, TaskType.METHOD) for pid in papers}

    runner = M1Runner(
        model_name=args.model,
        papers=papers,
        task_types=task_types,
        output_dir=args.output,
    )

    t0 = time.time()
    output = runner.run_all()
    elapsed = time.time() - t0

    # Save results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = Path(args.output) / f"m1_framework_validation_{ts}.json"

    # Serialize profiles
    serializable = {
        "run_id": ts,
        "timestamp": output["timestamp"],
        "model": output["model"],
        "papers": list(papers.keys()),
        "elapsed_s": round(elapsed, 1),
        "analysis": output["analysis"],
        "paper_profiles": {},
    }

    for pid, result in output["results"].items():
        if result["status"] == "OK":
            profile = result["profile"]
            serializable["paper_profiles"][pid] = {
                "matrix": profile.to_matrix(),
                "maturity": compute_maturity_level(profile, task_types.get(pid, TaskType.METHOD)),
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
    print(f"  Papers: {len(papers)}")
    print(f"  Model: {args.model}")
    print(f"  Time: {elapsed:.0f}s")
    print(f"  Test 1 (correlation <0.85): {'PASS' if analysis['test1_correlation']['pass'] else 'WARN'}")
    print(f"  Test 2 (failure patterns): {'PASS' if analysis['test2_failure_patterns']['pass'] else 'WARN'}")
    print(f"  Test 4 (spurious flags): {analysis['test4_spurious']['total_flags']} total")


if __name__ == "__main__":
    main()
