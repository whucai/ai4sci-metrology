#!/usr/bin/env python3
"""Batch hard reproduction: test N papers, collect REI distribution."""
import sys, os, re, json, time, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "8192")

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.rei_metric import classify_error, ERROR_WEIGHTS
from src.sciscigpt_local.reproduction_pipeline import validate_generated_code
from src.sciscigpt_local.sciscinet_connector import load_table

# Import functions from run_hard_reproduction
from scripts.run_hard_reproduction import (
    find_hard_paper, prepare_hard_data, generate_code,
    fix_code, parse_output, run_hard_reproduction,
)


def main():
    print("=" * 70)
    print("BATCH HARD REPRODUCTION: 5 Papers, REI Distribution")
    print("=" * 70)

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}\n")

    print("Loading SciSciNet...")
    papers = load_table("papers")
    pc = load_table("paper_citations")

    results = []
    attempts = 0
    max_attempts = 20

    while len(results) < 5 and attempts < max_attempts:
        attempts += 1
        print(f"\n--- Paper search attempt {attempts} ---")
        row, refs, citers, n_j = find_hard_paper(
            papers, pc, min_n_j=2, min_abs_D=0.1
        )
        if row is None:
            print("  No hard paper found.")
            break

        pid = int(row["paper_id"])
        if any(r.get("paper_id") == str(pid) for r in results):
            continue

        print(f"  Paper: {pid}")
        print(f"  Title: {str(row.get('title',''))[:80]}...")

        ref_csv, cite_csv, gt = prepare_hard_data(row, refs, citers, pc)
        print(f"  Refs: {gt['n_refs']}, Citers: {gt['n_citers']}, "
              f"n_j: {gt['n_j']}, subgraph_D: {gt['subgraph_D']}")

        result = run_hard_reproduction(llm, ref_csv, cite_csv, gt, max_fixes=4)

        # REI
        if result["status"] in ("SUCCESS", "PARTIAL"):
            weights = sum(ERROR_WEIGHTS.get(e, 3) for e in result["error_types"])
            rei = round(weights / max(result["fix_iterations"], 1), 4) if result["fix_iterations"] > 0 else 0.0
        else:
            rei = 100.0

        result["paper_id"] = str(pid)
        result["title"] = str(row.get("title", ""))[:100]
        result["precomputed_D"] = float(row["disruption_score"])
        result["subgraph_D"] = gt["subgraph_D"]
        result["n_j_gt"] = gt["n_j"]
        result["REI"] = rei

        status_icon = {"SUCCESS": "OK", "PARTIAL": "~", "FAILED": "XX"}.get(result["status"], "??")
        print(f"  -> {status_icon} Status={result['status']}, REI={rei}, "
              f"fixes={result['fix_iterations']}, errors={result.get('error_types', [])}")

        results.append(result)

        # Clean up temps
        try:
            os.unlink(ref_csv)
            os.unlink(cite_csv)
        except OSError:
            pass

    print("\n" + "=" * 70)
    print("BATCH RESULTS SUMMARY")
    print("=" * 70)

    for i, r in enumerate(results):
        print(f"\n{i+1}. Paper {r['paper_id']}")
        print(f"   Title: {r.get('title', '?')[:80]}")
        print(f"   Status: {r['status']}, REI: {r['REI']}, fixes: {r['fix_iterations']}")
        print(f"   Errors: {r.get('error_types', [])}")
        print(f"   Computed D: {r.get('computed_D')}, Subgraph D: {r.get('subgraph_D')}")
        if r.get('n_i_parsed') is not None:
            print(f"   n_i={r['n_i_parsed']}, n_j={r['n_j_parsed']}")

    # Distribution stats
    rei_values = [r["REI"] for r in results]
    nonzero_rei = [r for r in results if r["REI"] > 0]
    print(f"\n--- REI Distribution ---")
    print(f"  Papers tested: {len(results)}")
    print(f"  Nonzero REI: {len(nonzero_rei)}/{len(results)}")
    print(f"  REI range: [{min(rei_values)}, {max(rei_values)}]")
    print(f"  Mean REI: {np.mean(rei_values):.2f}")
    print(f"  Success rate: {sum(1 for r in results if r['status']=='SUCCESS')}/{len(results)}")

    # Save
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "batch_hard_reproduction.json"
    serializable = []
    for r in results:
        sr = {}
        for k, v in r.items():
            if isinstance(v, (str, int, float, bool, list, dict, type(None))):
                sr[k] = v
            else:
                sr[k] = str(v)
        serializable.append(sr)
    out_path.write_text(json.dumps(serializable, indent=2, default=str))
    print(f"\nSaved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
