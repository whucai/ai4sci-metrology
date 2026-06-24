#!/usr/bin/env python3
"""R007 Gold Computation: Bentley2023 citation-weighted disruption index.

Bentley, Valverde, Borycz, Vidiella, Horne, Duran-Nebreda, O'Brien (2023)
"Is disruption decreasing, or is it accelerating?"
Advances in Complex Systems, 2023. DOI: 10.1142/S0219525923500066

Method: Citation-weighted CD5 index to test whether CD5 decline is an artifact
of exponential growth rather than true declining disruptiveness.

Key formula: mCD5(t) = Σ(citation_i * CD5_i) / Σ(citation_i) per year t
"""

import json, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.sciscigpt_local.sciscinet_connector import load_papers_sample

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r007"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading SciSciNet (10 shards)...")
df = load_papers_sample(n_shards=10)
print(f"  Loaded {len(df):,} papers")

# Filter to 1945-2010 with valid CD and citation count
mask = (
    (df["year"] >= 1945) & (df["year"] <= 2010) &
    df["disruption_score"].notna() &
    df["citation_count"].notna() & (df["citation_count"] > 0)
)
period = df[mask].copy()
print(f"  Valid papers 1945-2010 with CD + citations: {len(period):,}")

# Compute per year
yearly = period.groupby("year").agg(
    n=("paper_id", "count"),
    mean_cd=("disruption_score", "mean"),
    std_cd=("disruption_score", "std"),
    total_citations=("citation_count", "sum"),
    mean_citations=("citation_count", "mean"),
)

# Citation-weighted CD: Σ(cit * CD) / Σ(cit)
yearly["weighted_cd_numerator"] = period.groupby("year").apply(
    lambda g: np.sum(g["citation_count"] * g["disruption_score"])
)
yearly["weighted_cd"] = yearly["weighted_cd_numerator"] / yearly["total_citations"]

# Overall
overall_weighted_cd = (
    np.sum(period["citation_count"] * period["disruption_score"]) /
    period["citation_count"].sum()
)

decline_unweighted = float(
    (yearly.loc[1945, "mean_cd"] - yearly.loc[2010, "mean_cd"])
    / abs(yearly.loc[1945, "mean_cd"]) * 100
)
decline_weighted = float(
    (yearly.loc[1945, "weighted_cd"] - yearly.loc[2010, "weighted_cd"])
    / abs(yearly.loc[1945, "weighted_cd"]) * 100
    if abs(yearly.loc[1945, "weighted_cd"]) > 1e-10 else 0
)

print(f"\nSample N: {len(period):,}")
print(f"Years: {len(yearly)}")
print(f"Unweighted CD 1945: {yearly.loc[1945, 'mean_cd']:.6f}")
print(f"Unweighted CD 2010: {yearly.loc[2010, 'mean_cd']:.6f}")
print(f"Unweighted decline: {decline_unweighted:.1f}%")
print(f"Weighted CD 1945: {yearly.loc[1945, 'weighted_cd']:.6f}")
print(f"Weighted CD 2010: {yearly.loc[2010, 'weighted_cd']:.6f}")
print(f"Weighted decline: {decline_weighted:.1f}%")
print(f"Overall weighted CD: {overall_weighted_cd:.6f}")

# Check if weighted CD is "close to zero" after 1970 (key claim)
post1970 = period[period["year"] >= 1970]
post1970_weighted = (
    np.sum(post1970["citation_count"] * post1970["disruption_score"]) /
    post1970["citation_count"].sum()
)
print(f"Weighted CD post-1970: {post1970_weighted:.6f}")
print(f"Claim 'close to zero since ~1970': {'YES' if abs(post1970_weighted) < 0.005 else 'PARTIAL'}")

# Check modest increase since 2000
post2000 = period[period["year"] >= 2000]
yearly_2000_2010 = yearly.loc[2000:2010]
increase_2000 = float(
    yearly_2000_2010["weighted_cd"].iloc[-1] - yearly_2000_2010["weighted_cd"].iloc[0]
)
print(f"Weighted CD change 2000-2010: {increase_2000:+.6f}")
print(f"Claim 'modest increase since 2000': {'YES' if increase_2000 > 0 else 'NO'}")

gold = {
    "paper_id": "bentley2023_disruption",
    "title": "Is disruption decreasing, or is it accelerating?",
    "venue": "Advances in Complex Systems",
    "year": 2023,
    "task_type": "strict",
    "data_source": "SciSciNet (same as Park2023), 10 shards",
    "pre_computed_date": "2026-06-17",
    "methodology": (
        "Citation-weighted disruption index: mCD5(t) = Σ(cit_i * CD5_i) / Σ(cit_i). "
        "Tests whether CD5 decline (Park2023) is an artifact of exponential growth. "
        "Key claim: weighted CD close to zero since ~1970, modest increase since 2000."
    ),
    "filters": {
        "year_range": [1945, 2010],
        "require_cd_score": True,
        "require_citations": True,
    },
    "gold_results": {
        "sample_N": int(len(period)),
        "years_count": int(len(yearly)),
        "unweighted": {
            "cd_1945_mean": round(float(yearly.loc[1945, "mean_cd"]), 8),
            "cd_2010_mean": round(float(yearly.loc[2010, "mean_cd"]), 8),
            "decline_pct": round(decline_unweighted, 4),
            "overall_mean": round(float(period["disruption_score"].mean()), 8),
        },
        "weighted": {
            "cd_1945_mean": round(float(yearly.loc[1945, "weighted_cd"]), 8),
            "cd_2010_mean": round(float(yearly.loc[2010, "weighted_cd"]), 8),
            "decline_pct": round(decline_weighted, 4),
            "overall_mean": round(overall_weighted_cd, 8),
            "post_1970_mean": round(post1970_weighted, 8),
            "change_2000_2010": round(increase_2000, 8),
        },
        "yearly": {
            str(yr): {
                "n": int(yearly.loc[yr, "n"]),
                "mean_cd": round(float(yearly.loc[yr, "mean_cd"]), 8),
                "weighted_cd": round(float(yearly.loc[yr, "weighted_cd"]), 8),
                "total_citations": int(yearly.loc[yr, "total_citations"]),
            }
            for yr in sorted(yearly.index)
        },
    },
    "key_claims": {
        "weighted_cd_near_zero_post1970": bool(abs(post1970_weighted) < 0.005),
        "modest_increase_since_2000": bool(increase_2000 > 0),
        "unweighted_decline_is_artifact": bool(abs(decline_weighted) < abs(decline_unweighted) * 0.5),
    },
}

gold_path = OUTPUT_DIR / "gold_values.json"
with open(gold_path, "w") as f:
    json.dump(gold, f, indent=2)

print(f"\nGold saved to {gold_path}")
print("Done.")
