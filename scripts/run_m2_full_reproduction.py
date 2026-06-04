#!/usr/bin/env python3
"""M2 Full Reproduction: Wu et al. (2019) — Disruption Index by Team Size.

Loads all 22 SciSciNet paper shards (~2.4M papers) and reproduces:
  1. Small-team vs large-team disruption comparison (primary)
  2. Field-level robustness check
  3. Year-level robustness check

Bypasses LLM code generation entirely — uses SciSciNet pre-computed fields.
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu
from collections import defaultdict

from src.sciscigpt_local.sciscinet_connector import (
    load_papers_sample, load_table, get_disruption_by_team_size,
)


def load_all_papers() -> pd.DataFrame:
    """Load all 22 paper shards."""
    print("Loading all 22 shards (~2.4M papers)...")
    df = load_papers_sample(n_shards=22)
    print(f"  Loaded: {len(df):,} papers")
    return df


def field_level_disruption(papers: pd.DataFrame) -> pd.DataFrame:
    """Compute disruption_by_team_size per field using paper_fields + fields tables."""
    print("\nComputing field-level disruption...")
    pf = load_table("paper_fields")
    f = load_table("fields")

    merged = papers[["paper_id", "disruption_score", "author_count"]].merge(
        pf, on="paper_id", how="inner"
    ).merge(f, on="field_id", how="inner")

    results = []
    for field_name, group in merged.groupby("field_name"):
        small = group[group["author_count"] <= 3]["disruption_score"].dropna()
        large = group[group["author_count"] >= 4]["disruption_score"].dropna()
        if len(small) < 100 or len(large) < 100:
            continue
        try:
            _, p = mannwhitneyu(small, large, alternative="two-sided")
        except Exception:
            p = 1.0
        results.append({
            "field": field_name,
            "small_mean": round(small.mean(), 5),
            "large_mean": round(large.mean(), 5),
            "difference": round(small.mean() - large.mean(), 5),
            "small_n": len(small),
            "large_n": len(large),
            "p_value": p,
            "significant": p < 0.001,
        })

    return pd.DataFrame(results).sort_values("difference", ascending=False)


def year_level_disruption(papers: pd.DataFrame) -> pd.DataFrame:
    """Compute disruption_by_team_size by year (1950-2024)."""
    print("Computing year-level disruption...")
    df = papers.dropna(subset=["disruption_score", "author_count", "year"]).copy()
    df["year"] = df["year"].astype(int)
    df["team"] = np.where(df["author_count"] <= 3, "small", "large")

    results = []
    for year in sorted(df["year"].unique()):
        small = df[(df["year"] == year) & (df["team"] == "small")]["disruption_score"]
        large = df[(df["year"] == year) & (df["team"] == "large")]["disruption_score"]
        if len(small) < 50 or len(large) < 50:
            continue
        try:
            _, p = mannwhitneyu(small, large, alternative="two-sided")
        except Exception:
            p = 1.0
        results.append({
            "year": year,
            "small_mean": round(small.mean(), 5),
            "large_mean": round(large.mean(), 5),
            "difference": round(small.mean() - large.mean(), 5),
            "small_n": len(small),
            "large_n": len(large),
            "p_value": p,
            "significant_001": p < 0.001,
            "significant_005": p < 0.005,
        })

    return pd.DataFrame(results).sort_values("year")


def main():
    print("=" * 70)
    print("M2 FULL REPRODUCTION: Wu et al. (2019) — All 22 Shards")
    print("=" * 70)

    # ── Load all papers ──
    papers = load_all_papers()

    # ── 1. Primary: small vs large team disruption ──
    print("\n" + "-" * 50)
    print("1. PRIMARY: Small-team vs Large-team Disruption")
    print("-" * 50)
    result = get_disruption_by_team_size(papers)
    for k, v in result.items():
        print(f"  {k}: {v}")

    # ── 2. Field-level robustness ──
    print("\n" + "-" * 50)
    print("2. ROBUSTNESS: Field-Level Analysis")
    print("-" * 50)
    field_df = field_level_disruption(papers)
    n_sig = field_df["significant"].sum()
    n_pos = (field_df["difference"] > 0).sum()
    print(f"  Fields analyzed: {len(field_df)}")
    print(f"  Fields where small > large: {n_pos}/{len(field_df)} ({n_pos/len(field_df)*100:.0f}%)")
    print(f"  Fields with p<0.001: {n_sig}/{len(field_df)}")
    print(f"\n  Top 5 fields (largest small-team advantage):")
    for _, row in field_df.head(5).iterrows():
        sig = "***" if row["significant"] else ""
        print(f"    {row['field']:30s} diff={row['difference']:+.5f}  small={row['small_n']:,}  large={row['large_n']:,} {sig}")
    print(f"\n  Bottom 5 fields (smallest/no advantage):")
    for _, row in field_df.tail(5).iterrows():
        sig = "***" if row["significant"] else ""
        print(f"    {row['field']:30s} diff={row['difference']:+.5f}  small={row['small_n']:,}  large={row['large_n']:,} {sig}")

    # ── 3. Year-level robustness ──
    print("\n" + "-" * 50)
    print("3. ROBUSTNESS: Year-Level Analysis")
    print("-" * 50)
    year_df = year_level_disruption(papers)
    sig_001 = year_df["significant_001"].sum()
    sig_005 = year_df["significant_005"].sum()
    n_years = len(year_df)
    pos_years = (year_df["difference"] > 0).sum()
    print(f"  Years analyzed: {n_years} ({year_df['year'].min()}-{year_df['year'].max()})")
    print(f"  Years where small > large: {pos_years}/{n_years} ({pos_years/n_years*100:.0f}%)")
    print(f"  Years with p<0.001: {sig_001}/{n_years}")
    print(f"  Years with p<0.05: {sig_005}/{n_years}")

    # Show decadal summary
    year_df["decade"] = (year_df["year"] // 10) * 10
    print(f"\n  Decadal averages:")
    for decade, grp in year_df.groupby("decade"):
        print(f"    {decade}s: mean diff={grp['difference'].mean():+.5f}, "
              f"sig_years={grp['significant_001'].sum()}/{len(grp)}")

    # ── 4. Distribution stats ──
    print("\n" + "-" * 50)
    print("4. DISTRIBUTION: Disruption Score Summary")
    print("-" * 50)
    d = papers["disruption_score"].dropna()
    print(f"  Mean:   {d.mean():.5f}")
    print(f"  Median: {d.median():.5f}")
    print(f"  Std:    {d.std():.5f}")
    print(f"  Skew:   {d.skew():.5f}")
    print(f"  Min:    {d.min():.5f}")
    print(f"  Max:    {d.max():.5f}")
    print(f"  % > 0:  {(d > 0).mean()*100:.1f}%")
    print(f"  % > 0.1: {(d > 0.1).mean()*100:.1f}%")

    # ── Save results ──
    out = {
        "primary": result,
        "field_level_n": len(field_df),
        "field_level_sig": int(n_sig),
        "field_level_pos_frac": round(n_pos / len(field_df), 3),
        "year_level_n": n_years,
        "year_level_sig_001": int(sig_001),
        "year_level_sig_005": int(sig_005),
        "year_level_pos_frac": round(pos_years / n_years, 3),
        "distribution_mean": round(d.mean(), 5),
        "distribution_median": round(d.median(), 5),
        "total_papers": len(papers),
    }
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "m2_results.json"
    import json
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults saved to {out_path}")

    print("\n" + "=" * 70)
    print("M2 FULL REPRODUCTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
