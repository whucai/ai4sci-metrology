#!/usr/bin/env python3
"""Fix #6: SciSciNet-backed SDK — disruption_index from local citation data.

Uses SciSciNet's paper_citations table to compute D-index locally,
avoiding OpenAlex API calls entirely. Validates against pre-computed
disruption_score in the papers table.
"""

import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from scipy import stats

from src.sciscigpt_local.sciscinet_connector import load_table, load_papers_sample


def sciscinet_disruption_index(
    paper_id: str,
    paper_citations: pd.DataFrame,
    max_citing: int = 200,
) -> dict:
    """Compute D-index for a paper using SciSciNet citation data.

    Args:
        paper_id: SciSciNet paper ID.
        paper_citations: Full paper_citations table (citing → cited).
        max_citing: Max forward citations to process (for speed).

    Returns:
        dict with n_i, n_j, n_k, D, citing_count, reference_count.
    """
    # Get references (papers cited by this paper)
    references = set(
        paper_citations[paper_citations["citing_paper_id"] == paper_id]["cited_paper_id"].values
    )

    # Get forward citations (papers citing this paper), limited
    citing_all = paper_citations[paper_citations["cited_paper_id"] == paper_id]["citing_paper_id"].values
    citing_papers = citing_all[:max_citing]

    if len(citing_papers) == 0:
        return {
            "paper_id": paper_id,
            "D": 0.0,
            "n_i": 0, "n_j": 0, "n_k": 0,
            "citing_count": len(citing_all),
            "reference_count": len(references),
            "note": "No forward citations",
        }

    # For each citing paper, check if it also cites any reference
    citing_set = set(citing_papers)
    # Get all citations from citing papers
    citing_citations = paper_citations[
        paper_citations["citing_paper_id"].isin(citing_set)
    ]

    n_i = 0  # cite ONLY focal, not references
    n_j = 0  # cite BOTH focal and references
    n_k = 0  # cite ONLY references, not focal

    for citing_paper in citing_papers:
        papers_cited_by_citer = set(
            citing_citations[citing_citations["citing_paper_id"] == citing_paper]["cited_paper_id"].values
        )
        cites_refs = len(papers_cited_by_citer & references) > 0

        if cites_refs:
            n_j += 1
        else:
            n_i += 1

    # For n_k: citing papers that cite references but NOT the focal paper
    # This is harder to compute efficiently, so we estimate from the data
    # n_k ≈ papers citing references but not the focal paper
    # For large datasets, n_k is typically dominated by the reference set
    ref_citing_sets = []
    for ref in list(references)[:10]:  # Sample references for efficiency
        ref_citers = set(paper_citations[paper_citations["cited_paper_id"] == ref]["citing_paper_id"].values[:500])
        ref_citing_sets.append(ref_citers)

    if ref_citing_sets:
        all_ref_citers = set.union(*ref_citing_sets)
        n_k_candidates = all_ref_citers - citing_set
        n_k = min(len(n_k_candidates), max_citing * 10)  # Cap for sanity
    else:
        n_k = 0

    denominator = n_i + n_j + n_k
    D = (n_i - n_j) / denominator if denominator > 0 else 0.0

    return {
        "paper_id": paper_id,
        "D": round(D, 6),
        "n_i": n_i, "n_j": n_j, "n_k": n_k,
        "citing_count": len(citing_all),
        "reference_count": len(references),
    }


def validate_against_sciscinet(
    n_papers: int = 100,
    seed: int = 42,
) -> dict:
    """Validate SciSciNet-computed D-index against pre-computed disruption_score."""
    print(f"Validating against {n_papers} random papers...")
    papers = load_table("papers")
    pc = load_table("paper_citations")

    # Sample papers with citations and references
    valid = papers.dropna(subset=["disruption_score"])
    valid = valid[valid["citation_count"] > 0]
    sample = valid.sample(min(n_papers, len(valid)), random_state=seed)

    results = []
    for i, (_, row) in enumerate(sample.iterrows()):
        pid = row["paper_id"]
        precomputed = row["disruption_score"]
        t0 = time.time()

        try:
            computed = sciscinet_disruption_index(pid, pc, max_citing=200)
            elapsed = time.time() - t0
            results.append({
                "paper_id": pid,
                "precomputed_D": precomputed,
                "computed_D": computed["D"],
                "difference": abs(computed["D"] - precomputed),
                "n_i": computed["n_i"],
                "n_j": computed["n_j"],
                "n_k": computed["n_k"],
                "elapsed": round(elapsed, 3),
            })
        except Exception as e:
            results.append({
                "paper_id": pid,
                "error": str(e)[:200],
            })

        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{n_papers}...")

    # Analysis
    valid_results = [r for r in results if "error" not in r and r["computed_D"] is not None]
    if not valid_results:
        return {"error": "No valid results", "total": len(results)}

    diffs = np.array([r["difference"] for r in valid_results])
    precomputed = np.array([r["precomputed_D"] for r in valid_results])
    computed = np.array([r["computed_D"] for r in valid_results])

    # Correlation between computed and precomputed
    rho, p = stats.spearmanr(computed, precomputed)
    r, rp = stats.pearsonr(computed, precomputed)

    return {
        "n_tested": len(results),
        "n_valid": len(valid_results),
        "n_errors": len(results) - len(valid_results),
        "mean_absolute_diff": round(np.mean(diffs), 6),
        "median_absolute_diff": round(np.median(diffs), 6),
        "max_absolute_diff": round(np.max(diffs), 6),
        "spearman_rho": round(rho, 4) if not np.isnan(rho) else 0.0,
        "spearman_p": round(p, 6) if not np.isnan(p) else 1.0,
        "pearson_r": round(r, 4) if not np.isnan(r) else 0.0,
        "pearson_p": round(rp, 6) if not np.isnan(rp) else 1.0,
        "mean_elapsed": round(np.mean([r["elapsed"] for r in valid_results]), 3),
        "interpretation": "Strong correlation" if abs(rho) > 0.7 else "Moderate correlation" if abs(rho) > 0.4 else "Weak correlation",
    }


def sciscinet_field_normalize(
    metric_values: pd.Series,
    field_ids: pd.Series,
    years: pd.Series,
) -> pd.Series:
    """Field × year Z-score normalization using SciSciNet.

    For each (field, year) group, compute z = (value - group_mean) / group_std.
    """
    df = pd.DataFrame({"metric": metric_values, "field_id": field_ids, "year": years})
    stats_df = df.groupby(["field_id", "year"])["metric"].agg(["mean", "std"]).reset_index()
    stats_df["std"] = stats_df["std"].fillna(stats_df["std"].median())

    merged = df.merge(stats_df, on=["field_id", "year"], how="left")
    merged["z_score"] = (merged["metric"] - merged["mean"]) / merged["std"].clip(lower=1e-10)
    merged["z_score"] = merged["z_score"].fillna(0.0)

    return merged["z_score"]


def main():
    print("=" * 70)
    print("FIX #6: SciSciNet-Backed SDK")
    print("=" * 70)

    # Validate disruption_index
    print("\n--- Validating sciscinet_disruption_index() ---")
    validation = validate_against_sciscinet(n_papers=50)

    for k, v in validation.items():
        print(f"  {k}: {v}")

    # Example: compute D-index for a specific paper
    print("\n--- Example D-index computations ---")
    pc = load_table("paper_citations")
    papers = load_table("papers")
    sample_papers = papers.dropna(subset=["disruption_score"]).sample(5, random_state=42)

    for _, row in sample_papers.iterrows():
        pid = row["paper_id"]
        precomputed = row["disruption_score"]
        computed = sciscinet_disruption_index(pid, pc, max_citing=200)
        print(f"  {pid}: precomputed D={precomputed:+.4f}, computed D={computed['D']:+.4f}, "
              f"n_i={computed['n_i']}, n_j={computed['n_j']}, n_k={computed['n_k']}")

    # Save
    out = {"validation": validation, "n_examples": 5}
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "sciscinet_sdk_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults saved to {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
