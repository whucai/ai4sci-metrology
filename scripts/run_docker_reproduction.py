#!/usr/bin/env python3
"""Containerized reproduction: runs inside Docker with clean environment.

This script reproduces the D-index computation for a sample paper
using ONLY pandas/numpy — no langchain, no external APIs, no SciSciNet.
The input data (CSV files) must be provided as volume mounts.

Usage:
    docker run --rm -v /path/to/data:/data ai4sci-metrology \
        python scripts/run_docker_reproduction.py --refs /data/refs.csv --cites /data/cites.csv

Or defaults to built-in test data if no args provided.
"""
import sys
import argparse
import pandas as pd
import numpy as np

# Built-in test data (small example)
TEST_REFS = pd.DataFrame({"reference_id": [101, 102, 103, 104, 105, 106, 107]})
TEST_CITES = pd.DataFrame({
    "citing_paper_id": [1, 1, 1, 2, 2, 3, 3, 3, 4, 4, 5, 5, 5, 6, 7, 8, 9, 9, 10, 10, 11, 11],
    "cited_paper_id":  [999,101,888, 999,102, 999,103,777, 999,666, 999,555,104, 999,999,999, 999,105, 999,106, 999,107],
})
# Ground truth for test data: 7 citers with refs (1,2,3,5,9,10,11), 4 without (4,6,7,8)
# n_i=4, n_j=7, D=(4-7)/11=-0.272727


def compute_disruption_index(refs_csv: str, cites_csv: str) -> dict:
    """Compute D-index from raw citation CSV files."""
    refs = pd.read_csv(refs_csv)
    cites = pd.read_csv(cites_csv)

    ref_set = set(refs["reference_id"].values)

    n_i, n_j, n_k = 0, 0, 0
    unique_citers = cites["citing_paper_id"].unique()

    for cid in unique_citers:
        citer_refs = set(cites[cites["citing_paper_id"] == cid]["cited_paper_id"].values)
        if citer_refs & ref_set:
            n_j += 1
        else:
            n_i += 1

    denom = n_i + n_j
    D = (n_i - n_j) / denom if denom > 0 else 0.0

    return {
        "n_i": n_i,
        "n_j": n_j,
        "n_k": n_k,
        "n_citers": len(unique_citers),
        "n_refs": len(ref_set),
        "D_index": round(D, 6),
    }


def main():
    parser = argparse.ArgumentParser(description="Containerized D-index reproduction")
    parser.add_argument("--refs", help="Path to references CSV")
    parser.add_argument("--cites", help="Path to citations CSV")
    args = parser.parse_args()

    print("=" * 60)
    print("CONTAINERIZED D-INDEX REPRODUCTION")
    print("=" * 60)

    # Environment info
    print(f"Python: {sys.version}")
    print(f"Pandas: {pd.__version__}")
    print(f"NumPy: {np.__version__}")
    print()

    if args.refs and args.cites:
        print(f"Refs CSV: {args.refs}")
        print(f"Cites CSV: {args.cites}")
        result = compute_disruption_index(args.refs, args.cites)
    else:
        print("Using built-in test data")
        import tempfile
        refs_path = tempfile.mktemp(suffix="_refs.csv")
        cites_path = tempfile.mktemp(suffix="_cites.csv")
        TEST_REFS.to_csv(refs_path, index=False)
        TEST_CITES.to_csv(cites_path, index=False)
        result = compute_disruption_index(refs_path, cites_path)

    print(f"\n--- Results ---")
    print(f"D_INDEX = {result['D_index']}")
    print(f"n_i = {result['n_i']}")
    print(f"n_j = {result['n_j']}")
    print(f"n_k = {result['n_k']}")
    print(f"n_citers = {result['n_citers']}")
    print(f"n_refs = {result['n_refs']}")

    # Verification for built-in test
    if not (args.refs and args.cites):
        expected_D = -0.272727
        ok = abs(result["D_index"] - expected_D) < 0.001
        print(f"\nVerification: {'PASSED' if ok else 'FAILED'} "
              f"(expected D={expected_D}, got D={result['D_index']})")

    print("\nContainerized reproduction complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
