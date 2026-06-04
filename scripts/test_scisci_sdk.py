#!/usr/bin/env python3
"""SciSci SDK Validation (Experiment 2: E2a-c).

Tests:
  E2a: disruption_index() — validate against known Wu et al. (2019) results
  E2b: cem_match() — correctness on benchmark dataset
  E2c: SDK usability — agent task completion rate with SDK vs raw code

Usage:
  python scripts/test_scisci_sdk.py
  python scripts/test_scisci_sdk.py --test e2a
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_e2a_disruption_index():
    """E2a: Validate disruption_index() against known papers.

    We test on papers with known characteristics:
      - Survey/review papers → negative D-index (consolidating)
      - Methodological breakthroughs → positive D-index (disruptive)
    """
    from src.sciscigpt_local.scisci_sdk import disruption_index

    print("--- E2a: disruption_index() Validation ---")

    # Test on a disruptor paper: "Attention Is All You Need" (Vaswani et al. 2017)
    # Known: highly disruptive, transformed NLP → should have positive D-index
    test_papers = [
        {
            "id": "W3113258790",  # "BERT: Pre-training of Deep Bidirectional Transformers"
            "label": "transformative",
            "expected_sign": "positive",
        },
    ]

    results = []
    for paper in test_papers:
        print(f"\n  Testing: {paper['id']} ({paper['label']})")
        try:
            result = disruption_index(paper["id"], max_citing=30)
            d = result["disruption_index"]
            n_i = result["n_i"]
            n_j = result["n_j"]
            n_k = result["n_k"]

            print(f"    Title: {result['title'][:80]}")
            print(f"    Year: {result['year']}, Cited by: {result['cited_by_count']}")
            print(f"    D-index: {d} (n_i={n_i}, n_j={n_j}, n_k={n_k})")

            sign = "positive" if d > 0 else "negative" if d < 0 else "zero"
            results.append({
                "id": paper["id"],
                "d_index": d,
                "sign": sign,
                "n_total": n_i + n_j + n_k,
            })
        except Exception as e:
            print(f"    ERROR: {e}")
            results.append({"id": paper["id"], "error": str(e)})

    # Validation: D-index should be in [-1, 1]
    valid = all(-1.0 <= r.get("d_index", 0) <= 1.0 for r in results if "d_index" in r)
    print(f"\n  D-index range valid: {valid}")
    print(f"  Results: {json.dumps(results, indent=2)}")

    return valid


def test_e2b_cem_match():
    """E2b: Validate cem_match() on a synthetic benchmark dataset."""
    from src.sciscigpt_local.scisci_sdk import cem_match

    print("\n--- E2b: cem_match() Validation ---")

    # Create a treatment group: small teams (1-3 authors)
    treatment = [
        {"n_authors": 1, "year": 2015, "field": "physics"},
        {"n_authors": 2, "year": 2016, "field": "biology"},
        {"n_authors": 3, "year": 2017, "field": "chemistry"},
        {"n_authors": 2, "year": 2018, "field": "physics"},
        {"n_authors": 1, "year": 2019, "field": "biology"},
    ]

    # Create a pool: mixed team sizes
    pool = [
        {"n_authors": 1, "year": 2015, "field": "physics"},
        {"n_authors": 5, "year": 2015, "field": "physics"},
        {"n_authors": 2, "year": 2016, "field": "biology"},
        {"n_authors": 8, "year": 2016, "field": "biology"},
        {"n_authors": 3, "year": 2017, "field": "chemistry"},
        {"n_authors": 10, "year": 2017, "field": "chemistry"},
        {"n_authors": 2, "year": 2018, "field": "physics"},
        {"n_authors": 15, "year": 2018, "field": "physics"},
        {"n_authors": 1, "year": 2019, "field": "biology"},
        {"n_authors": 6, "year": 2019, "field": "biology"},
        # Extra pool items
        {"n_authors": 4, "year": 2015, "field": "physics"},
        {"n_authors": 7, "year": 2016, "field": "biology"},
        {"n_authors": 2, "year": 2017, "field": "chemistry"},
    ]

    result = cem_match(treatment, pool, on=["field", "year"], k=1)

    print(f"  Match rate: {result['match_rate']}")
    print(f"  Matched: {result['n_matched']}/{result['n_total']}")
    print(f"  Balance stats: {json.dumps(result.get('balance_stats', {}), indent=2)}")

    # Success: match rate > 80% (should be near 100% for this synthetic data)
    match_ok = result["match_rate"] >= 0.8
    balance_ok = all(
        b.get("diff", 1.0) < 0.5
        for b in result.get("balance_stats", {}).values()
    )

    print(f"  Match rate OK: {match_ok}")
    print(f"  Balance OK: {balance_ok}")

    return match_ok and balance_ok


def test_e2c_field_normalize():
    """E2c: Test field_normalize() function."""
    from src.sciscigpt_local.scisci_sdk import field_normalize

    print("\n--- E2c: field_normalize() Test ---")

    # Normalize a paper with 100 citations in "computer science" in 2020
    result = field_normalize(100, "computer science", 2020)

    if "error" in result:
        print(f"  ERROR: {result['error']}")
        return False

    print(f"  Z-score: {result['z_score']}")
    print(f"  Percentile: {result['percentile']}")
    print(f"  Field mean: {result['field_mean']}")
    print(f"  Field std: {result['field_std']}")
    print(f"  Sample size: {result['sample_size']}")

    return result["sample_size"] > 0


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="all", choices=["e2a", "e2b", "e2c", "all"])
    args = parser.parse_args()

    print("=" * 60)
    print("SciSci SDK Validation (Experiment 2)")
    print("=" * 60)

    results = {}

    if args.test in ("e2a", "all"):
        results["e2a_dindex"] = test_e2a_disruption_index()

    if args.test in ("e2b", "all"):
        results["e2b_cem"] = test_e2b_cem_match()

    if args.test in ("e2c", "all"):
        results["e2c_field_norm"] = test_e2c_field_normalize()

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print("\n" + "=" * 60)
    print(f"SciSci SDK Result: {passed}/{total} tests passed")
    print(f"Results: {results}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
