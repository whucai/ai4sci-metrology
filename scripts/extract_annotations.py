#!/usr/bin/env python3
"""Extract SciSciPaper annotations from bench-mark Markdown papers using LLM.

Reads paper_metadata.json, sends each paper's MD content to Qwen3-32B vLLM,
extracts structured annotations (research_question, hypotheses, variables, etc.),
and saves to a registry JSON for the benchmark runner.

Uses ThreadPoolExecutor for concurrent extraction.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI

# ── Config ──
BASE_URL = os.environ.get("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "not-needed")
MODEL = os.environ.get("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
MAX_CHARS = 12000  # First N chars of paper to send (intro + methods usually sufficient)
MAX_WORKERS = 8
MAX_RETRIES = 3

_client: Any = None
_model: str = MODEL
_base_url: str = BASE_URL


def _get_client() -> Any:
    global _client
    if _client is None:
        _client = OpenAI(base_url=_base_url, api_key=API_KEY)
    return _client


# ── Extraction prompt ──
EXTRACTION_SYSTEM = """You are an expert in scientometrics and the science of science.
Your task is to read a research paper and extract structured information about its
research design, experimental methodology, variables, and conclusions.

CRITICAL: Output ONLY valid JSON. Start with '{' and end with '}'. No markdown code blocks."""

EXTRACTION_PROMPT_TEMPLATE = """Read the following research paper and extract structured information.

## Paper Content
{content}

## Extraction Task

Extract the following fields as a JSON object. If you cannot determine a field from the text, use empty values (empty string, empty list, empty dict).

{{
  "paper_id": "authorYear_keyword (e.g., wu2019_large_teams)",
  "title": "Full paper title",
  "authors": ["Author 1", "Author 2"],
  "venue": "Journal or conference name",
  "year": 2023,
  "doi": "DOI if mentioned",

  "research_idea": "1-2 sentence summary of the core research idea and contribution",
  "research_question": "The main research question the paper investigates",
  "hypotheses": ["Hypothesis 1", "Hypothesis 2"],

  "data_source": "What datasets/databases are used (e.g., Web of Science, USPTO, PubMed)",
  "data_description": "Brief description of the data: size, scope, time period",
  "available_fields": ["field1", "field2", "field3"],
  "sample_scope": {{
    "time_window": "e.g., 1980-2009",
    "fields": ["e.g., biomedical", "all"],
    "filters": ["filter criteria"]
  }},

  "independent_variables": [
    {{"name": "var_name", "type": "continuous|categorical|binary|count", "definition": "what this variable measures"}}
  ],
  "dependent_variables": [
    {{"name": "var_name", "type": "continuous|categorical|binary|count", "formula": "how it is computed"}}
  ],
  "control_variables": [
    {{"name": "var_name", "type": "continuous|categorical|binary|count", "rationale": "why controlled"}}
  ],

  "statistical_method": {{
    "family": "OLS|fixed_effects|logistic|descriptive|nonparametric_test|network_analysis|etc",
    "specification": "Brief description of the model/analysis",
    "estimation": "OLS|MLE|GMM|etc"
  }},
  "network_construction": {{
    "node_type": "paper|author|patent|etc or 'none'",
    "edge_type": "citation|cocitation|coauthorship|etc or 'none'",
    "directed": true,
    "weighted": true,
    "temporal": true,
    "construction_method": "How the network is built"
  }},
  "grouping_strategy": {{
    "groups": ["group1", "group2"],
    "rationale": "Why these groups are compared"
  }},
  "expected_result_form": {{
    "type": "regression_table|descriptive_table|distribution_plot|etc",
    "key_quantities": ["quantity1", "quantity2"]
  }},

  "result_claims": [
    {{"metric": "metric name", "value": "observed value/direction", "direction": "positive|negative|null|unknown", "significance": "p < 0.01 or descriptive"}}
  ],
  "partial_results": [
    {{"metric": "metric name", "note": "why this result is incomplete or uncertain"}}
  ],

  "conclusion_claims": [
    "Main conclusion statement 1",
    "Main conclusion statement 2"
  ],
  "limitations": [
    "Key limitation 1",
    "Key limitation 2"
  ],
  "robustness_checks": [
    {{"method": "robustness test method", "rationale": "why this test"}}
  ]
}}

Output ONLY the JSON object, nothing else."""


def extract_paper(md_path: str, metadata: dict) -> dict | None:
    """Extract annotations from a single paper using LLM."""
    try:
        content = Path(md_path).read_text(encoding="utf-8", errors="replace")
        content = content[:MAX_CHARS]
    except Exception as e:
        print(f"  ERROR reading {md_path}: {e}")
        return None

    for attempt in range(MAX_RETRIES):
        try:
            response = _get_client().chat.completions.create(
                model=_model,
                messages=[
                    {"role": "system", "content": EXTRACTION_SYSTEM},
                    {"role": "user", "content": EXTRACTION_PROMPT_TEMPLATE.format(content=content)},
                ],
                temperature=0.0,
                max_tokens=4096,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)

            parsed = json.loads(raw)
            # Merge metadata from paper_metadata.json
            parsed.setdefault("title", metadata.get("title", ""))
            parsed.setdefault("doi", metadata.get("doi", ""))
            parsed.setdefault("venue", metadata.get("subdir", ""))
            parsed["text_path"] = md_path
            parsed["_source"] = metadata
            return parsed
        except json.JSONDecodeError as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            print(f"  JSON parse error for {md_path} after {MAX_RETRIES} attempts: {e}")
            return None
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
                continue
            print(f"  LLM error for {md_path}: {e}")
            return None
    return None


def extract_concurrent(papers: list[dict], max_workers: int = MAX_WORKERS) -> dict[str, dict]:
    """Extract annotations from multiple papers concurrently."""
    results: dict[str, dict] = {}
    total = len(papers)
    completed = 0
    failed = 0

    print(f"Extracting annotations from {total} papers (concurrent={max_workers})...")
    t0 = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for p in papers:
            md_path = p.get("md_path", "")
            full_path = Path("bench-mark") / md_path
            if not md_path or not full_path.exists():
                print(f"  SKIP: {p.get('title', '?')[:60]} — no MD file at {full_path}")
                failed += 1
                continue
            future = executor.submit(extract_paper, str(full_path), p)
            futures[future] = p

        for future in as_completed(futures):
            p = futures[future]
            title = p.get("title", "?")[:60]
            try:
                result = future.result()
                if result:
                    pid = result.get("paper_id", Path(p.get("md_path", "")).stem)
                    results[pid] = result
                    completed += 1
                    print(f"  [{completed}/{total}] OK: {title}")
                else:
                    failed += 1
                    print(f"  [{completed+failed}/{total}] FAIL: {title}")
            except Exception as e:
                failed += 1
                print(f"  [{completed+failed}/{total}] ERROR: {title} — {e}")

    elapsed = time.time() - t0
    print(f"\nExtraction complete: {completed} OK, {failed} failed ({elapsed:.1f}s)")
    return results


def main():
    global _base_url, _model, _client, BASE_URL, MODEL

    parser = argparse.ArgumentParser(description="Extract SciSciBench annotations from bench-mark papers")
    parser.add_argument("--metadata", default="bench-mark/paper_metadata.json")
    parser.add_argument("--output", default="bench-mark/extracted_registry.json")
    parser.add_argument("--max-papers", type=int, default=0, help="Max papers to process (0=all)")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--model", default=MODEL)
    args = parser.parse_args()

    _base_url = args.base_url
    _model = args.model
    BASE_URL = _base_url
    MODEL = _model
    _client = OpenAI(base_url=_base_url, api_key=API_KEY)

    # Load metadata
    metadata = json.loads(Path(args.metadata).read_text())
    papers = metadata[:args.max_papers] if args.max_papers > 0 else metadata
    print(f"Loaded {len(papers)} papers from {args.metadata}")

    # Filter: only papers with md_path
    papers = [p for p in papers if p.get("md_path")]
    print(f"  {len(papers)} have markdown files")

    # Extract concurrently
    results = extract_concurrent(papers, max_workers=args.workers)

    # Save
    out_path = Path(args.output)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Saved {len(results)} extractions to {out_path}")


if __name__ == "__main__":
    main()
