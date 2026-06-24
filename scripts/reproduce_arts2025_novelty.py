#!/usr/bin/env python3
"""
Reproduce Arts, Melluso & Veugelers (2025) "Beyond Citations: Measuring Novel
Scientific Ideas and their Impact in Publication Text"
— Review of Economics and Statistics, rest_a_01561.

Uses the authors' Zenodo data (data/zenodo_arts2025/) already downloaded locally.
Core claim: text-based novelty metrics outperform citation-based measures in
identifying novel ideas and predicting scientific impact.
"""

import json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl
import statsmodels.api as sm
from scipy import stats

warnings.filterwarnings("ignore")

DATA = Path("data/zenodo_arts2025")
OUT = Path("results/arts2025")
OUT.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════
# 1. LOAD & MERGE
# ═══════════════════════════════════════════════════════════════════
print("=" * 72)
print("Reproducing Arts, Melluso & Veugelers (2025)")
print("Review of Economics and Statistics, rest_a_01561")
print("=" * 72)

SAMPLE_FRAC = 0.25  # Use 25% sample for practical memory usage

print("\n[1/5] Loading Zenodo data...")
# Load text metrics (polars for efficiency)
metrics = pl.read_csv(
    DATA / "papers_textual_metrics.csv",
    columns=["PaperID", "new_word", "new_word_reuse", "new_phrase",
             "new_phrase_reuse", "new_word_comb", "new_word_comb_reuse",
             "new_phrase_comb", "new_phrase_comb_reuse",
             "semantic_distance", "n_words", "n_phrases", "has_abstract"],
    infer_schema_length=10000,
)
print(f"  Text metrics: {len(metrics):,} papers")

# Load paper metadata (only needed columns)
papers = pl.read_csv(
    DATA / "papers.csv",
    columns=["PaperID", "Year", "CitationCount", "ReferenceCount",
             "AuthorCount", "SourceID", "SourceType"],
    infer_schema_length=10000,
)
print(f"  Paper metadata: {len(papers):,} papers")

# Merge
df = papers.join(metrics, on="PaperID", how="inner")
print(f"  Merged: {len(df):,} papers")

# Filter: 1901–2010 (as in paper's citation analysis, Appendix H)
df = df.filter((pl.col("Year") >= 1901) & (pl.col("Year") <= 2010))
print(f"  1901-2010 subset: {len(df):,} papers")

# Sample for practical memory usage
if SAMPLE_FRAC < 1.0:
    df = df.sample(fraction=SAMPLE_FRAC, seed=42)
    print(f"  Sampled {SAMPLE_FRAC*100:.0f}%: {len(df):,} papers")

# Convert to pandas for statsmodels regression
# (polars is fast for ETL; statsmodels needs pandas)
print("  Converting to pandas...")
pdf = df.to_pandas()
print(f"  Memory: {pdf.memory_usage(deep=True).sum() / 1e9:.1f} GB")

# ═══════════════════════════════════════════════════════════════════
# 2. SUMMARY STATISTICS (Table 1)
# ═══════════════════════════════════════════════════════════════════
print("\n[2/5] Table 1: Summary Statistics")

VARS = {
    "new_word": "New Word (count)",
    "new_word_reuse": "New Word Reuse",
    "new_phrase": "New Phrase (count)",
    "new_phrase_reuse": "New Phrase Reuse",
    "new_word_comb": "New Word Combination (count)",
    "new_word_comb_reuse": "New Word Combination Reuse",
    "new_phrase_comb": "New Phrase Combination (count)",
    "new_phrase_comb_reuse": "New Phrase Combination Reuse",
    "semantic_distance": "Semantic Distance",
}

# Binary versions
pdf["new_word_bin"] = (pdf["new_word"] > 0).astype(int)
pdf["new_phrase_bin"] = (pdf["new_phrase"] > 0).astype(int)
pdf["new_word_comb_bin"] = (pdf["new_word_comb"] > 0).astype(int)
pdf["new_phrase_comb_bin"] = (pdf["new_phrase_comb"] > 0).astype(int)

table1 = []
for col, label in VARS.items():
    s = pdf[col]
    table1.append({
        "metric": label,
        "mean": round(float(s.mean()), 4),
        "std": round(float(s.std()), 4),
        "min": round(float(s.min()), 4),
        "p25": round(float(s.quantile(0.25)), 4),
        "p50": round(float(s.median()), 4),
        "p75": round(float(s.quantile(0.75)), 4),
        "p95": round(float(s.quantile(0.95)), 4),
        "p99": round(float(s.quantile(0.99)), 4),
        "max": round(float(s.max()), 4),
        "skew": round(float(s.skew()), 4),
    })

# Binary metrics
for col, label in [
    ("new_word_bin", "New Word (Binary)"),
    ("new_phrase_bin", "New Phrase (Binary)"),
    ("new_word_comb_bin", "New Word Combination (Binary)"),
    ("new_phrase_comb_bin", "New Phrase Combination (Binary)"),
]:
    s = pdf[col]
    table1.append({
        "metric": label,
        "mean": round(float(s.mean()), 4),
        "std": round(float(s.std()), 4),
        "min": round(float(s.min()), 4),
        "p25": round(float(s.quantile(0.25)), 4),
        "p50": round(float(s.median()), 4),
        "p75": round(float(s.quantile(0.75)), 4),
        "p95": round(float(s.quantile(0.95)), 4),
        "p99": round(float(s.quantile(0.99)), 4),
        "max": round(float(s.max()), 4),
        "skew": round(float(s.skew()), 4),
    })

# Print
print(f"{'Metric':<35s} {'Mean':>8s} {'Std':>8s} {'P50':>8s} {'P95':>8s} {'P99':>8s} {'Max':>8s}")
print("-" * 85)
for r in table1[:12]:
    print(f"{r['metric']:<35s} {r['mean']:>8.3f} {r['std']:>8.3f} "
          f"{r['p50']:>8.3f} {r['p95']:>8.3f} {r['p99']:>8.3f} {r['max']:>8.1f}")

# Controls
print(f"\n{'Controls':<35s} {'Mean':>8s} {'Std':>8s} {'P50':>8s} {'P95':>8s} {'P99':>8s} {'Max':>8s}")
print("-" * 85)
for col, label in [
    ("has_abstract", "Abstract (Binary)"),
    ("n_words", "N. of Words"),
    ("n_phrases", "N. of Phrases"),
    ("ReferenceCount", "N. of cited Papers"),
    ("CitationCount", "Citation Count"),
    ("AuthorCount", "Author Count"),
]:
    print(f"{label:<35s} {pdf[col].mean():>8.3f} {pdf[col].std():>8.3f} "
          f"{pdf[col].median():>8.3f} {pdf[col].quantile(0.95):>8.3f} "
          f"{pdf[col].quantile(0.99):>8.3f} {pdf[col].max():>8.1f}")

print(f"\n  N = {len(pdf):,} papers (1901-2010)")

# ═══════════════════════════════════════════════════════════════════
# 3. CORRELATIONS: TEXT METRICS vs CITATIONS
# ═══════════════════════════════════════════════════════════════════
print("\n[3/5] Correlations: Text Metrics vs Citation Impact")

pdf["log_cites"] = np.log1p(pdf["CitationCount"])
pdf["top1pct"] = 0  # placeholder - need subfield-year percentiles

corr_vars = ["new_word", "new_phrase", "new_word_comb", "new_phrase_comb",
             "new_word_reuse", "new_phrase_reuse", "new_word_comb_reuse",
             "new_phrase_comb_reuse", "semantic_distance"]

print(f"{'Metric':<35s} {'r(log_cites)':>14s} {'p-value':>12s}")
print("-" * 62)
corr_results = {}
for col in corr_vars:
    mask = pdf[col].notna()
    r, p = stats.pearsonr(pdf.loc[mask, col], pdf.loc[mask, "log_cites"])
    corr_results[col] = {"r": round(float(r), 4), "p": float(p)}
    sig = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
    print(f"{col:<35s} {r:>+14.4f}{sig} {p:>12.2e}")

def fmt(model, var_name):
    """Format coefficient with significance stars."""
    if var_name not in model.params.index:
        return ""
    b = model.params[var_name]
    p = model.pvalues[var_name]
    stars = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
    return f"{b:+.3f}{stars}"


# ═══════════════════════════════════════════════════════════════════
# 4. REGRESSION: Citations ~ Novelty Metrics (Appendix H)
# ═══════════════════════════════════════════════════════════════════
print("\n[4/5] Regression: log(Citations) ~ Novelty + Controls + FE")

# Prepare regression data
reg_df = pdf.copy()

# Standardize metrics for comparison
metric_cols = ["new_word", "new_phrase", "new_word_comb", "new_phrase_comb",
               "new_word_reuse", "new_phrase_reuse", "new_word_comb_reuse",
               "new_phrase_comb_reuse", "semantic_distance"]
for col in metric_cols:
    reg_df[f"{col}_std"] = (reg_df[col] - reg_df[col].mean()) / reg_df[col].std()

# Controls
reg_df["log_authors"] = np.log1p(reg_df["AuthorCount"])
reg_df["log_refs"] = np.log1p(reg_df["ReferenceCount"])

# Year and Source (journal) FEs - sample top journals to keep FE matrix manageable
top_sources = reg_df["SourceID"].value_counts().head(200).index.tolist()
reg_df["source_fe"] = reg_df["SourceID"].apply(lambda x: x if x in top_sources else "OTHER")

# Build regression matrix
yr_dummies = pd.get_dummies(reg_df["Year"], prefix="yr", drop_first=True, dtype=float)
src_dummies = pd.get_dummies(reg_df["source_fe"], prefix="src", drop_first=True, dtype=float)

print(f"  Year FEs: {len(yr_dummies.columns)}, Source FEs: {len(src_dummies.columns)}")

# Model 1: Baseline (controls only)
X_base = pd.concat([
    reg_df[["has_abstract", "n_words", "n_phrases", "log_authors", "log_refs"]],
    yr_dummies, src_dummies,
], axis=1)
X_base_c = sm.add_constant(X_base, has_constant="add")
m1 = sm.OLS(reg_df["log_cites"].values, X_base_c.astype(float)).fit()
print(f"  Model 1 (controls only): Adj-R² = {m1.rsquared_adj:.3f}")

# Model 2: Ex-ante text novelty metrics
X_exante = pd.concat([
    reg_df[["new_word_std", "new_phrase_std", "new_word_comb_std",
            "new_phrase_comb_std", "semantic_distance_std",
            "has_abstract", "n_words", "n_phrases", "log_authors", "log_refs"]],
    yr_dummies, src_dummies,
], axis=1)
X_exante_c = sm.add_constant(X_exante, has_constant="add")
m2 = sm.OLS(reg_df["log_cites"].values, X_exante_c.astype(float)).fit()
print(f"  Model 2 (+ex-ante text): Adj-R² = {m2.rsquared_adj:.3f}")

# Model 3: Ex-post reuse metrics
X_expost = pd.concat([
    reg_df[["new_word_reuse_std", "new_phrase_reuse_std",
            "new_word_comb_reuse_std", "new_phrase_comb_reuse_std",
            "has_abstract", "n_words", "n_phrases", "log_authors", "log_refs"]],
    yr_dummies, src_dummies,
], axis=1)
X_expost_c = sm.add_constant(X_expost, has_constant="add")
m3 = sm.OLS(reg_df["log_cites"].values, X_expost_c.astype(float)).fit()
print(f"  Model 3 (+ex-post reuse): Adj-R² = {m3.rsquared_adj:.3f}")

# Model 4: All text metrics
X_all = pd.concat([
    reg_df[[f"{c}_std" for c in metric_cols] +
           ["has_abstract", "n_words", "n_phrases", "log_authors", "log_refs"]],
    yr_dummies, src_dummies,
], axis=1)
X_all_c = sm.add_constant(X_all, has_constant="add")
m4 = sm.OLS(reg_df["log_cites"].values, X_all_c.astype(float)).fit()
print(f"  Model 4 (all text metrics): Adj-R² = {m4.rsquared_adj:.3f}")

# ── Extract coefficients for display ──
print(f"\n{'Variable':<30s} {'Model 1':>10s} {'Model 2':>10s} {'Model 3':>10s} {'Model 4':>10s}")
print("-" * 72)

key_vars = [
    ("new_word_std", "New Word (std)"),
    ("new_phrase_std", "New Phrase (std)"),
    ("new_word_comb_std", "New Word Comb (std)"),
    ("new_phrase_comb_std", "New Phrase Comb (std)"),
    ("semantic_distance_std", "Semantic Dist (std)"),
    ("new_word_reuse_std", "New Word Reuse (std)"),
    ("new_phrase_reuse_std", "New Phrase Reuse (std)"),
    ("new_word_comb_reuse_std", "New Word Comb Reuse (std)"),
    ("new_phrase_comb_reuse_std", "New Phrase Comb Reuse (std)"),
]

reg_results = {}
for var_name, label in key_vars:
    m1_c = fmt(m1, var_name) if var_name in m1.params.index else ""
    m2_c = fmt(m2, var_name) if var_name in m2.params.index else ""
    m3_c = fmt(m3, var_name) if var_name in m3.params.index else ""
    m4_c = fmt(m4, var_name) if var_name in m4.params.index else ""
    print(f"{label:<30s} {m1_c:>10s} {m2_c:>10s} {m3_c:>10s} {m4_c:>10s}")
    if var_name in m4.params.index:
        reg_results[var_name] = {
            "coef_m4": round(float(m4.params[var_name]), 4),
            "se_m4": round(float(m4.bse[var_name]), 4),
            "coef_m2": round(float(m2.params[var_name]), 4) if var_name in m2.params.index else None,
            "coef_m3": round(float(m3.params[var_name]), 4) if var_name in m3.params.index else None,
        }

print(f"\n  Observations: {len(reg_df):,}")
print(f"  Δ Adj-R² (M2-M1): +{m2.rsquared_adj - m1.rsquared_adj:.4f} (ex-ante text)")
print(f"  Δ Adj-R² (M3-M1): +{m3.rsquared_adj - m1.rsquared_adj:.4f} (ex-post reuse)")
print(f"  Δ Adj-R² (M4-M1): +{m4.rsquared_adj - m1.rsquared_adj:.4f} (all text)")

# ═══════════════════════════════════════════════════════════════════
# 5. PERCENTILE ANALYSIS (Figure 2)
# ═══════════════════════════════════════════════════════════════════
print("\n[5/5] Figure 2: Novelty Percentile vs Citation Impact")

# Compute within-year percentiles for key metrics (proxy for subfield-year)
print("  Computing within-year percentiles...")
for col in ["new_phrase", "new_phrase_reuse"]:
    pdf[f"{col}_pct"] = pdf.groupby("Year")[col].transform(
        lambda x: x.rank(pct=True))

# Check if top novelty percentile papers get more citations
for col in ["new_phrase", "new_phrase_reuse"]:
    pct_col = f"{col}_pct"
    top1 = pdf[pdf[pct_col] >= 0.99]
    mid = pdf[(pdf[pct_col] >= 0.45) & (pdf[pct_col] <= 0.55)]
    bottom1 = pdf[pdf[pct_col] <= 0.01]

    print(f"\n  {col}:")
    print(f"    Top 1% (N={len(top1):,}):    mean cites={top1['CitationCount'].mean():.1f}, "
          f"top1% cited={top1['CitationCount'].quantile(0.99):.1f}")
    print(f"    Middle (N={len(mid):,}):     mean cites={mid['CitationCount'].mean():.1f}, "
          f"top1% cited={mid['CitationCount'].quantile(0.99):.1f}")
    print(f"    Bottom 1% (N={len(bottom1):,}): mean cites={bottom1['CitationCount'].mean():.1f}, "
          f"top1% cited={bottom1['CitationCount'].quantile(0.99):.1f}")

# ═══════════════════════════════════════════════════════════════════
# SAVE RESULTS
# ═══════════════════════════════════════════════════════════════════
results = {
    "sample": {
        "N_total": int(len(pdf)),
        "year_range": f"{pdf['Year'].min()}-{pdf['Year'].max()}",
    },
    "table1_summary": table1,
    "correlations": corr_results,
    "regression": {
        "model1_adj_r2": round(float(m1.rsquared_adj), 4),
        "model2_adj_r2": round(float(m2.rsquared_adj), 4),
        "model3_adj_r2": round(float(m3.rsquared_adj), 4),
        "model4_adj_r2": round(float(m4.rsquared_adj), 4),
        "delta_r2_exante": round(float(m2.rsquared_adj - m1.rsquared_adj), 4),
        "delta_r2_expost": round(float(m3.rsquared_adj - m1.rsquared_adj), 4),
        "delta_r2_all": round(float(m4.rsquared_adj - m1.rsquared_adj), 4),
        "coefficients": reg_results,
        "N": int(len(reg_df)),
    },
}

out_path = OUT / "reproduction_results.json"
out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
print(f"\nResults saved to {out_path}")
print("Done!")
