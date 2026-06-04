#!/usr/bin/env python3
"""Subgraph-D vs Full-D Error Decomposition.

Analyzes why subgraph D-index differs from precomputed full SciSciNet D-index,
decomposing error into: n_k omission, citation closure, and sampling bias.
"""
import sys, os, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from scipy import stats

from src.sciscigpt_local.sciscinet_connector import load_table


def compute_full_components(pid, pc, refs):
    """Compute n_i, n_j, n_k from the FULL citation graph (all citers, all their refs)."""
    all_citers = pc[pc["cited_paper_id"] == pid]["citing_paper_id"].values
    if len(all_citers) == 0:
        return 0, 0, 0

    n_i, n_j, n_k = 0, 0, 0
    for cp in all_citers:
        cp_refs = set(pc[pc["citing_paper_id"] == cp]["cited_paper_id"].values)
        if cp_refs & refs:
            n_j += 1
        else:
            n_i += 1

    # n_k from SciSciNet definition: citations to focal paper from papers with unknown refs
    return n_i, n_j, n_k


def compute_subgraph_components(pid, pc, refs, max_citers=30):
    """Compute n_i, n_j from a sampled subgraph (capped citers and their refs)."""
    citers = pc[pc["cited_paper_id"] == pid]["citing_paper_id"].values[:max_citers]
    if len(citers) == 0:
        return 0, 0, {}

    n_i, n_j = 0, 0
    details = {}
    for cp in citers:
        cp_refs = set(pc[pc["citing_paper_id"] == cp]["cited_paper_id"].values[:100])
        if cp_refs & refs:
            n_j += 1
        else:
            n_i += 1
    return n_i, n_j, {"n_citers_sampled": len(citers)}


def main():
    print("=" * 70)
    print("Subgraph-D vs Full-D Error Decomposition")
    print("=" * 70)

    papers = load_table("papers")
    pc = load_table("paper_citations")

    # Select diverse papers
    valid = papers.dropna(subset=["disruption_score", "citation_count", "title"])
    valid = valid[(valid["citation_count"] >= 10) & (valid["citation_count"] <= 100)]

    results = []
    for _, row in valid.sample(min(100, len(valid)), random_state=42).iterrows():
        pid = int(row["paper_id"])
        refs = set(pc[pc["citing_paper_id"] == pid]["cited_paper_id"].values)
        if len(refs) < 5:
            continue

        # Full graph
        full_ni, full_nj, full_nk = compute_full_components(pid, pc, refs)
        full_denom = full_ni + full_nj + full_nk
        full_D = (full_ni - full_nj) / full_denom if full_denom > 0 else 0.0

        # Subgraph (capped)
        sub_ni, sub_nj, sub_meta = compute_subgraph_components(pid, pc, refs, max_citers=30)
        sub_denom = sub_ni + sub_nj
        sub_D = (sub_ni - sub_nj) / sub_denom if sub_denom > 0 else 0.0

        pre_D = float(row["disruption_score"])

        results.append({
            "paper_id": pid,
            "title": str(row.get("title", ""))[:80],
            "year": int(row.get("year", 0)),
            "n_refs": len(refs),
            "citation_count": int(row["citation_count"]),
            "precomputed_D": round(pre_D, 6),
            "full_ni": full_ni, "full_nj": full_nj, "full_nk": full_nk,
            "full_D": round(full_D, 6),
            "sub_ni": sub_ni, "sub_nj": sub_nj,
            "sub_D": round(sub_D, 6),
            "abs_error_full_vs_precomputed": round(abs(full_D - pre_D), 6),
            "abs_error_sub_vs_full": round(abs(sub_D - full_D), 6),
            "abs_error_sub_vs_precomputed": round(abs(sub_D - pre_D), 6),
        })

        if len(results) >= 30:
            break

    df = pd.DataFrame(results)

    print(f"\nAnalyzed {len(df)} papers\n")

    # Error decomposition
    print("--- Error Decomposition ---")
    print(f"{'Metric':<40} {'Mean':>10} {'Median':>10} {'Std':>10}")
    print("-" * 70)

    for col, label in [
        ("abs_error_full_vs_precomputed", "|Full D - Precomputed D|"),
        ("abs_error_sub_vs_full", "|Subgraph D - Full D| (sampling)"),
        ("abs_error_sub_vs_precomputed", "|Subgraph D - Precomputed D| (total)"),
    ]:
        vals = df[col]
        print(f"{label:<40} {vals.mean():>10.6f} {vals.median():>10.6f} {vals.std():>10.6f}")

    # Error attribution
    print(f"\n--- Error Attribution ---")
    df["sampling_error_pct"] = 100 * df["abs_error_sub_vs_full"] / (df["abs_error_sub_vs_precomputed"] + 0.0001)
    df["nk_error_pct"] = 100 * df["abs_error_full_vs_precomputed"] / (df["abs_error_sub_vs_precomputed"] + 0.0001)

    print(f"Sampling error (subgraph vs full): {df['abs_error_sub_vs_full'].mean():.4f} mean, "
          f"{df['sampling_error_pct'].median():.1f}% median of total error")
    print(f"n_k + closure error (full vs precomputed): {df['abs_error_full_vs_precomputed'].mean():.4f} mean, "
          f"{df['nk_error_pct'].median():.1f}% median of total error")

    # n_k analysis
    print(f"\n--- n_k Analysis ---")
    has_nk = df[df["full_nk"] > 0]
    print(f"Papers with n_k > 0: {len(has_nk)}/{len(df)} ({100*len(has_nk)/len(df):.1f}%)")
    if len(has_nk) > 0:
        print(f"Mean n_k when > 0: {has_nk['full_nk'].mean():.1f}")
        print(f"Mean denom (full): {(has_nk['full_ni'] + has_nk['full_nj'] + has_nk['full_nk']).mean():.1f}")

    # Subgraph D vs Precomputed D correlation
    r, p = stats.spearmanr(df["sub_D"], df["precomputed_D"])
    print(f"\n--- Subgraph D vs Precomputed D ---")
    print(f"Spearman ρ = {r:.4f} (p={p:.6f})")
    rp, pp = stats.pearsonr(df["sub_D"], df["precomputed_D"])
    print(f"Pearson r = {rp:.4f} (p={pp:.6f})")

    # Show top 5 examples
    print(f"\n--- Top 5 Papers by Total Error ---")
    top = df.nlargest(5, "abs_error_sub_vs_precomputed")
    for _, r in top.iterrows():
        print(f"\n  Paper {r['paper_id']} ({r['year']})")
        print(f"  Title: {r['title']}")
        print(f"  Precomputed D: {r['precomputed_D']:+.4f}")
        print(f"  Full D:        {r['full_D']:+.4f}  (n_i={r['full_ni']}, n_j={r['full_nj']}, n_k={r['full_nk']})")
        print(f"  Subgraph D:    {r['sub_D']:+.4f}  (n_i={r['sub_ni']}, n_j={r['sub_nj']})")
        print(f"  |Sub - Pre|:   {r['abs_error_sub_vs_precomputed']:.4f}")
        print(f"  |Sub - Full|:  {r['abs_error_sub_vs_full']:.4f} (sampling)")
        print(f"  |Full - Pre|:  {r['abs_error_full_vs_precomputed']:.4f} (n_k/closure)")

    # Save
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "subgraph_d_analysis.json"
    out_path.write_text(df.to_json(orient="records", indent=2))
    print(f"\nSaved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
