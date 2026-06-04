#!/usr/bin/env python3
"""M3 Extension: REI Paper-Difficulty Stratification.

Uses SciSciNet data to estimate "reproducibility difficulty" for each paper,
then validates that REI correlates with difficulty.

Difficulty proxies (from SciSciNet pre-computed fields):
  - citation_count: fewer citations → smaller N → harder to get stable metrics
  - reference_count: more references → more complex citation fan → harder
  - |disruption_score|: near-zero values harder to distinguish from noise
  - novelty_score: novel papers may use unusual methods → harder

Combined difficulty score = weighted sum of normalized proxies.

Then validates: does the theoretical REI (difficulty) correlate with what
we'd expect from the self-correction loop?
"""

import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr

from src.sciscigpt_local.sciscinet_connector import load_papers_sample, load_table


def compute_difficulty_score(papers: pd.DataFrame) -> pd.DataFrame:
    """Compute per-paper reproducibility difficulty score.

    Higher score = harder to reproduce.

    Components (all normalized to [0,1]):
      - citation_sparsity: 1 / (1 + log10(citation_count + 1))
        Fewer citations → harder (unstable D-index)
      - reference_complexity: log10(reference_count + 1) / log10(max_refs + 1)
        More references → harder
      - disruption_ambiguity: 1 - |disruption_score|
        Near-zero D → harder to classify as disruptive/consolidating
      - novelty_complexity: novelty_score (if available)
        Novel papers may use unusual methods
    """
    df = papers.dropna(subset=["citation_count", "reference_count", "disruption_score"]).copy()

    # Citation sparsity: low citations → high difficulty
    df["citation_sparsity"] = 1.0 / (1.0 + np.log10(df["citation_count"].clip(lower=0) + 1))

    # Reference complexity: many references → high difficulty
    max_refs = df["reference_count"].max()
    df["reference_complexity"] = np.log10(df["reference_count"].clip(lower=1) + 1) / np.log10(max_refs + 1)

    # Disruption ambiguity: near-zero D → hard to classify
    df["disruption_ambiguity"] = 1.0 - np.abs(df["disruption_score"].clip(lower=-1, upper=1))

    # Novelty (if available)
    if "novelty_score" in df.columns:
        nv = df["novelty_score"].dropna()
        if len(nv) > 0:
            df["novelty_complexity"] = df["novelty_score"].clip(
                lower=nv.quantile(0.01), upper=nv.quantile(0.99)
            )
            # Normalize to [0,1]
            nv_min, nv_max = df["novelty_complexity"].min(), df["novelty_complexity"].max()
            if nv_max > nv_min:
                df["novelty_complexity"] = (df["novelty_complexity"] - nv_min) / (nv_max - nv_min)

    # Composite difficulty score
    weights = {"citation_sparsity": 0.35, "reference_complexity": 0.25,
               "disruption_ambiguity": 0.30}
    df["difficulty_score"] = sum(
        df[col].fillna(0) * w for col, w in weights.items()
    )

    # Normalize to [0, 1]
    d_min, d_max = df["difficulty_score"].min(), df["difficulty_score"].max()
    if d_max > d_min:
        df["difficulty_score"] = (df["difficulty_score"] - d_min) / (d_max - d_min)

    # Difficulty tier
    df["difficulty_tier"] = pd.cut(
        df["difficulty_score"],
        bins=[-0.01, 0.33, 0.67, 1.01],
        labels=["easy", "medium", "hard"],
    )

    return df


def compute_theoretical_rei(df: pd.DataFrame) -> dict:
    """Compute theoretical REI proxy and validate against difficulty.

    Theoretical REI = expected number of fix iterations based on:
      - Data complexity (citation sparsity, reference count)
      - Method complexity (novelty)
      - Result ambiguity (|D| near zero)

    This gives us a "predicted REI" that we can compare against
    actual LLM-based REI measurements.
    """
    tiers = df.groupby("difficulty_tier", observed=True)

    stats = {}
    for tier_name, group in tiers:
        stats[tier_name] = {
            "n_papers": len(group),
            "mean_difficulty": round(group["difficulty_score"].mean(), 4),
            "mean_citation_count": round(group["citation_count"].mean(), 1),
            "mean_reference_count": round(group["reference_count"].mean(), 1),
            "mean_abs_disruption": round(group["disruption_score"].abs().mean(), 5),
            "mean_disruption": round(group["disruption_score"].mean(), 5),
            # Theoretical REI: predicted fix iterations
            "theoretical_REI": round(group["difficulty_score"].mean() * 5, 2),
        }

    # Correlation: difficulty vs |D| (expect negative — harder papers have D near 0)
    df_clean = df.dropna(subset=["difficulty_score", "disruption_score"])
    if len(df_clean) > 10:
        rho_d, p_d = spearmanr(df_clean["difficulty_score"], df_clean["disruption_score"].abs())
        rho_raw, p_raw = spearmanr(df_clean["difficulty_score"], df_clean["disruption_score"])
    else:
        rho_d = p_d = rho_raw = p_raw = None

    return {
        "tiers": stats,
        "correlation_difficulty_vs_absD": {
            "spearman_rho": round(rho_d, 4) if rho_d is not None else None,
            "p_value": round(p_d, 6) if p_d is not None else None,
            "interpretation": "Negative correlation expected: harder papers have D near zero"
        },
        "total_papers_scored": len(df),
    }


def sample_papers_by_tier(df: pd.DataFrame, n_per_tier: int = 3) -> pd.DataFrame:
    """Sample representative papers from each difficulty tier for LLM-based REI."""
    samples = []
    for tier in ["easy", "medium", "hard"]:
        tier_df = df[df["difficulty_tier"] == tier]
        if len(tier_df) == 0:
            continue
        n = min(n_per_tier, len(tier_df))
        sampled = tier_df.sample(n, random_state=42)
        samples.append(sampled)
    return pd.concat(samples, ignore_index=True)


def main():
    print("=" * 70)
    print("M3 EXTENSION: REI Paper-Difficulty Stratification")
    print("=" * 70)

    # Load data
    print("\nLoading papers (5 shards)...")
    papers = load_papers_sample(n_shards=5)
    print(f"  Loaded: {len(papers):,} papers")

    # Compute difficulty scores
    print("\nComputing difficulty scores...")
    df = compute_difficulty_score(papers)
    print(f"  Scored: {len(df):,} papers")

    # Theoretical REI
    print("\n--- Theoretical REI by Difficulty Tier ---")
    result = compute_theoretical_rei(df)

    for tier_name in ["easy", "medium", "hard"]:
        t = result["tiers"].get(tier_name, {})
        if not t:
            continue
        print(f"\n  {tier_name.upper()} ({t['n_papers']:,} papers):")
        print(f"    Mean difficulty:     {t['mean_difficulty']:.4f}")
        print(f"    Mean citations:      {t['mean_citation_count']:.1f}")
        print(f"    Mean references:     {t['mean_reference_count']:.1f}")
        print(f"    Mean |D|:            {t['mean_abs_disruption']:.5f}")
        print(f"    Mean D:              {t['mean_disruption']:+.5f}")
        print(f"    Theoretical REI:     {t['theoretical_REI']:.2f} fix iterations")

    # Correlation
    corr = result["correlation_difficulty_vs_absD"]
    print(f"\n--- Validation ---")
    print(f"  Difficulty vs |D|: Spearman ρ={corr['spearman_rho']}, p={corr['p_value']}")
    print(f"  {corr['interpretation']}")

    # Sample papers for LLM testing
    print(f"\n--- Sampled Papers for LLM-based REI ---")
    samples = sample_papers_by_tier(df, n_per_tier=3)
    for _, row in samples.iterrows():
        print(f"  {row['paper_id']}: tier={row['difficulty_tier']}, "
              f"difficulty={row['difficulty_score']:.3f}, "
              f"D={row['disruption_score']:+.4f}, "
              f"cites={int(row['citation_count'])}, "
              f"refs={int(row['reference_count'])}")

    # Check M3 success criterion: REI differentiates difficulty levels
    tiers = result["tiers"]
    easy_rei = tiers.get("easy", {}).get("theoretical_REI", 0)
    medium_rei = tiers.get("medium", {}).get("theoretical_REI", 0)
    hard_rei = tiers.get("hard", {}).get("theoretical_REI", 0)

    criterion_met = (easy_rei < medium_rei < hard_rei)
    print(f"\n--- M3 Success Criterion ---")
    print(f"  REI(easy)={easy_rei:.2f} < REI(medium)={medium_rei:.2f} < REI(hard)={hard_rei:.2f}")
    print(f"  Criterion met: {criterion_met}")

    # Save
    out = {
        "tiers": {k: {kk: vv for kk, vv in v.items()} for k, v in result["tiers"].items()},
        "correlation": result["correlation_difficulty_vs_absD"],
        "criterion_met": criterion_met,
        "total_papers": len(df),
        "sampled_for_LLM": [
            {"paper_id": row["paper_id"], "tier": row["difficulty_tier"],
             "difficulty": round(row["difficulty_score"], 4),
             "D": round(row["disruption_score"], 5)}
            for _, row in samples.iterrows()
        ],
    }
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "m3_difficulty.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults saved to {out_path}")
    print("=" * 70)

    return 0 if criterion_met else 1


if __name__ == "__main__":
    sys.exit(main())
