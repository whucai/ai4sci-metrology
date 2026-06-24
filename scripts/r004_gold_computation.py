#!/usr/bin/env python3
"""R004 Gold Computation: Park2023 CD time trend on SciSciNet.

Park et al. (2023) "Papers and patents are becoming less disruptive over time"
Nature, Vol 613, 5 January 2023.

STRICT task: SciSciNet → SciSciNet. Target: exact year-by-year mean CD5 values.
"""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.sciscigpt_local.sciscinet_connector import load_papers_sample

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r004"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Loading SciSciNet (10 shards)...")
df = load_papers_sample(n_shards=10)
print(f"  Loaded {len(df):,} papers")

# Filter to Park2023 period
mask = (
    (df["year"] >= 1945) & (df["year"] <= 2010) &
    df["disruption_score"].notna()
)
period = df[mask].copy()
print(f"  Valid papers 1945-2010 with CD: {len(period):,}")

# CD by year
cd_by_year = period.groupby("year")["disruption_score"].agg(["mean", "std", "count", "median"])

decline_pct = float(
    (cd_by_year.loc[1945, "mean"] - cd_by_year.loc[2010, "mean"])
    / cd_by_year.loc[1945, "mean"] * 100
)

gold = {
    "paper_id": "park2023_disruptive",
    "title": "Papers and patents are becoming less disruptive over time",
    "venue": "Nature",
    "year": 2023,
    "task_type": "strict",
    "data_source": "SciSciNet (cssi/SciSciGPT-SciSciNet), shards 0-9",
    "pre_computed_date": "2026-06-16",
    "methodology": (
        "Compute CD index (CD5) mean by year for papers 1945-2010. "
        "CD index ranges from -1 (consolidating) to 1 (disruptive). "
        "Aggregation: groupby year → mean(disruption_score)."
    ),
    "filters": {
        "year_range": [1945, 2010],
        "require_cd_score": True,
        "drop_na": ["disruption_score", "year"],
    },
    "gold_results": {
        "sample_N": int(len(period)),
        "years_count": int(len(cd_by_year)),
        "overall_mean_cd": round(float(period["disruption_score"].mean()), 8),
        "overall_std_cd": round(float(period["disruption_score"].std()), 8),
        "cd_1945": {
            "mean": round(float(cd_by_year.loc[1945, "mean"]), 8),
            "std": round(float(cd_by_year.loc[1945, "std"]), 8),
            "N": int(cd_by_year.loc[1945, "count"]),
        },
        "cd_2010": {
            "mean": round(float(cd_by_year.loc[2010, "mean"]), 8),
            "std": round(float(cd_by_year.loc[2010, "std"]), 8),
            "N": int(cd_by_year.loc[2010, "count"]),
        },
        "decline_pct": round(decline_pct, 4),
        "cd_by_year": {
            str(yr): {
                "mean": round(float(cd_by_year.loc[yr, "mean"]), 8),
                "std": round(float(cd_by_year.loc[yr, "std"]), 8),
                "N": int(cd_by_year.loc[yr, "count"]),
            }
            for yr in sorted(cd_by_year.index)
        },
    },
    "d3_thresholds": {
        "sample_N_exact_match": True,
        "cd_mean_1945_relative_error": 0.01,
        "cd_mean_2010_relative_error": 0.01,
        "decline_direction_match": True,
        "years_count_exact": True,
    },
    "key_finding": (
        f"Mean CD declines from {cd_by_year.loc[1945, 'mean']:.6f} (1945) to "
        f"{cd_by_year.loc[2010, 'mean']:.6f} (2010), a {decline_pct:.1f}% decline. "
        "Consistent with Park2023 finding of 91.9-100% decline across fields."
    ),
}

gold_path = OUTPUT_DIR / "gold_values.json"
with open(gold_path, "w") as f:
    json.dump(gold, f, indent=2)

print(f"\nGold saved to {gold_path}")
print(f"Sample N: {gold['gold_results']['sample_N']:,}")
print(f"Years: {gold['gold_results']['years_count']}")
print(f"Overall mean CD: {gold['gold_results']['overall_mean_cd']:.6f}")
print(f"CD 1945: mean={gold['gold_results']['cd_1945']['mean']:.6f}, N={gold['gold_results']['cd_1945']['N']}")
print(f"CD 2010: mean={gold['gold_results']['cd_2010']['mean']:.6f}, N={gold['gold_results']['cd_2010']['N']}")
print(f"Decline: {decline_pct:.1f}%")
print("Done.")
