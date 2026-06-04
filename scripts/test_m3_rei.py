#!/usr/bin/env python3
"""M3: Self-Correction Loop + REI Metric Validation.

Tests the REI (Reproducibility Effort Index) measurement pipeline:
  1. Select N papers from SciSciNet with known disruption_score (ground truth)
  2. LLM generates code to compute D-index via OpenAlex API
  3. Execute in sandbox with self-correction
  4. Compare computed D-index against SciSciNet ground truth
  5. Compute REI = weighted fix iterations / successful steps

Usage:
  python scripts/test_m3_rei.py
  python scripts/test_m3_rei.py --papers 10 --max-fixes 5
"""

from __future__ import annotations

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--papers", type=int, default=6)
    parser.add_argument("--max-fixes", type=int, default=5)
    args = parser.parse_args()

    import os
    os.environ.setdefault("OPENAI_API_KEY", "not-needed")
    os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
    os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
    os.environ.setdefault("LLM_MAX_TOKENS", "2048")

    from src.sciscigpt_local.llm_backends import load_llm_from_env
    from src.sciscigpt_local.rei_metric import run_m3_suite

    print("Loading LLM...")
    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}")

    report = run_m3_suite(llm, n_papers=args.papers, max_fixes=args.max_fixes)

    # Save
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "m3_results.json"
    out_path.write_text(json.dumps(report, indent=2, default=str))

    # Check
    success_rate = report["successful"] / report["total"] if report["total"] > 0 else 0
    print(f"\nM3 Result: {report['successful']}/{report['total']} papers reproduced successfully")
    print(f"Success rate: {success_rate:.1%}")
    print(f"Mean REI: {report['mean_REI']}")

    return 0 if success_rate >= 0.3 else 1


if __name__ == "__main__":
    sys.exit(main())
