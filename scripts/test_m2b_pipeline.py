#!/usr/bin/env python3
"""M2: Focused Paper Reproduction Pipeline + REI.

Uses the targeted reproduction pipeline (not full agent graph) to:
  1. Extract paper structure
  2. Generate reproduction code
  3. Execute in sandbox with self-correction
  4. Compare results
  5. Compute REI (Reproducibility Effort Index)

Usage:
  python scripts/test_m2b_pipeline.py
  python scripts/test_m2b_pipeline.py --max-fixes 5
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Wu et al. (2019) method snippet — realistic reproduction target
WU2019_PAPER = """
Title: Large teams develop and small teams disrupt science and technology
Authors: Lingfei Wu, Dashun Wang, James A. Evans
Published: Nature, 2019

Abstract:
We analyzed over 65 million papers, patents, and software products spanning 1954-2014.
We developed a Disruption Index (D-index) that measures the degree to which a paper
or patent disrupts the existing scientific or technological paradigm.

Methods:
The Disruption Index for a focal paper is defined as:
  D = (n_i - n_j) / (n_i + n_j + n_k)

where:
  - n_i: number of subsequent papers that cite ONLY the focal paper (not its references)
  - n_j: number of subsequent papers that cite BOTH the focal paper AND its references
  - n_k: number of subsequent papers that cite ONLY the focal paper's references (not the focal paper)

We computed this using citation network data from Web of Science.
For each focal paper, we identified:
  1. Its set of references (backward citations)
  2. Its set of citations (forward citations)
  3. For each forward citation, whether it also cites any of the focal paper's references

The D-index ranges from -1 (fully consolidating) to 1 (fully disruptive).
A D-index > 0 indicates the paper disrupts the field.

Key findings:
- Small teams (1-3 authors) tend to produce more disruptive work
- Large teams (4+ authors) tend to develop and consolidate existing ideas
- Mean D-index for solo-authored papers: +0.25
- Mean D-index for large-team papers: -0.10
- Mann-Whitney U test: P < 0.001

Data:
- Web of Science citation data
- 42 million papers published 1954-2014
- 600 million citation relationships

Evaluation:
  - Disruption Index computed for each paper in the dataset
  - Compared D-index distributions by team size
  - Statistical significance: Mann-Whitney U test, P < 0.001
"""


def test_extract_and_generate():
    """Test 1: Extract paper structure and generate reproduction code."""
    import os
    os.environ.setdefault("OPENAI_API_KEY", "not-needed")
    os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
    os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
    os.environ.setdefault("LLM_MAX_TOKENS", "2048")

    from src.sciscigpt_local.llm_backends import load_llm_from_env
    from src.sciscigpt_local.paper_ingestion import extract_paper_structure
    from src.sciscigpt_local.reproduction_pipeline import generate_reproduction_code

    print("--- Test 1: Extract Paper + Generate Code ---")

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}")

    # Step 1: Extract
    structure = extract_paper_structure(WU2019_PAPER, llm)
    print(f"  Extraction fields: {list(structure.keys())}")
    print(f"  Methods: {[m.get('name') for m in structure.get('methods', [])]}")
    print(f"  Analysis steps: {len(structure.get('analysis_steps', []))}")

    if "error" in structure:
        print(f"  FAIL: {structure['error'][:200]}")
        return None

    # Step 2: Generate code
    data_context = {
        "data_source": "OpenAlex API (open access, no auth needed)",
        "paper_id": "W2913773162",  # Wu et al. 2019
        "sdk_available": [
            "scisci_sdk.disruption_index(doi_or_id)",
            "scisci_sdk.search_papers(query)",
            "scisci_sdk.citation_cascade(doi_or_id, depth)",
        ],
        "packages": ["pandas", "numpy", "scipy", "json", "requests"],
    }

    code = generate_reproduction_code(structure, data_context, llm)
    print(f"\n  Generated code ({len(code)} chars):")
    # Show first 30 lines
    for line in code.split("\n")[:20]:
        print(f"    {line}")

    return {"structure": structure, "code": code}


def test_execute_with_correction():
    """Test 2: Execute generated code with self-correction (REI computation)."""
    import os
    os.environ.setdefault("OPENAI_API_KEY", "not-needed")
    os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
    os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
    os.environ.setdefault("LLM_MAX_TOKENS", "2048")

    from src.sciscigpt_local.llm_backends import load_llm_from_env
    from src.sciscigpt_local.reproduction_pipeline import run_reproduction

    print("\n--- Test 2: Execute + Self-Correction + REI ---")

    llm = load_llm_from_env()

    data_context = {
        "data_source": "OpenAlex API",
        "paper_id": "W2913773162",
    }

    print("  Running reproduction pipeline...")
    report = run_reproduction(
        WU2019_PAPER,
        data_context,
        llm,
        max_fix_iterations=3,
    )

    print(f"  Status: {report['status']}")
    print(f"  Fix iterations: {report['fix_iterations']}")
    print(f"  REI: {report['REI']}")
    print(f"  Errors: {len(report.get('errors', []))}")

    if report.get("errors"):
        for err in report["errors"]:
            print(f"    - {err[:200]}")

    if report.get("comparison"):
        comp = report["comparison"]
        print(f"  Match rate: {comp.get('match_rate', 'N/A')}")
        for c in comp.get("comparisons", [])[:5]:
            print(f"    {c['metric']}: expected={c['expected']}, reproduced={c['reproduced']}, match={c['match']}")

    if report.get("result") and report["result"].get("stdout"):
        print(f"\n  STDOUT (first 500 chars):")
        print(f"    {report['result']['stdout'][:500]}")

    return report


def main():
    print("=" * 60)
    print("M2: Focused Reproduction Pipeline + REI")
    print("=" * 60)

    # Test 1: Extract + Generate
    result1 = test_extract_and_generate()
    extraction_ok = result1 is not None and "code" in result1

    # Test 2: Execute with self-correction
    result2 = test_execute_with_correction() if extraction_ok else None
    execution_ok = result2 is not None and result2["status"] == "SUCCESS"

    print("\n" + "=" * 60)
    results = {
        "extraction_and_code_gen": extraction_ok,
        "execution_and_REI": execution_ok,
    }
    if result2:
        results["REI"] = result2["REI"]
        results["fix_iterations"] = result2["fix_iterations"]
        results["status"] = result2["status"]

    passed = sum(1 for v in results.values() if isinstance(v, bool) and v)
    total_checks = 2
    print(f"M2 Result: {passed}/{total_checks} checks passed")
    print(f"Details: {json.dumps(results, default=str, indent=2)}")

    return 0 if passed == total_checks else 1


if __name__ == "__main__":
    sys.exit(main())
