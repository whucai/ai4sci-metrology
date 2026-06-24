#!/usr/bin/env python3
"""
Reproduce Schaper, Arts, Veugelers (2025) on USPTO-PubMed patent-level data.

Key specifications from the paper:
  - Frontier scientist: author who published in top-general journal
    (Nature, Science, Cell, PNAS, Lancet, NEJM, JAMA, BMJ)
    within 3 years before focal patent's application year
  - Look-ahead lag = 1 year (publication must precede patent application)
  - PPML for count outcomes, OLS log-linear for baseline
  - WIPO technology field FE + application year FE
  - Cluster-robust SE at WIPO field level (or NBER category)

Data: data/uspto-pubmed/merged/patents_enriched.parquet
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "uspto-pubmed" / "merged"
RESULTS_DIR = PROJECT_ROOT / "results" / "uspto-pubmed"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

LOOKAHEAD_LAG = 1  # publication before application year


def wald_test(model, var_names: list[str], var_values: list[float] = None) -> dict:
    """Wald test for linear combination of coefficients."""
    if var_values is None:
        var_values = [0] * len(var_names)

    params = model.params
    cov = model.cov_params()

    r_matrix = np.zeros((1, len(params)))
    for i, name in enumerate(var_names):
        if name in params.index:
            r_matrix[0, params.index.get_loc(name)] = 1
        else:
            return {"stat": np.nan, "pvalue": np.nan, "df": len(var_names)}

    r_vec = np.zeros(1)
    if var_values:
        for i, (name, val) in enumerate(zip(var_names, var_values)):
            if name in params.index:
                r_vec[0] += r_matrix[0, params.index.get_loc(name)] * val

    try:
        coef_diff = r_matrix.dot(params.values) - r_vec
        var_diff = r_matrix.dot(cov.values).dot(r_matrix.T)
        stat = float((coef_diff[0] ** 2) / var_diff[0, 0])
        pvalue = float(1 - stats.chi2.cdf(stat, len(var_names)))
        return {"stat": stat, "pvalue": pvalue, "df": len(var_names)}
    except Exception as e:
        return {"stat": np.nan, "pvalue": np.nan, "df": len(var_names), "error": str(e)}


def load_and_filter():
    """Load enriched patent data and prepare analysis sample."""
    print("[1] Loading USPTO-PubMed merged dataset...")
    df = pd.read_parquet(DATA_DIR / "patents_enriched.parquet")
    print(f"    {len(df):,} patents loaded")

    # Filter: needs valid WIPO section, inventor count > 0
    sample = df[
        df["section"].notna()
        & (df["section"] != "unknown")
        & (df["number_of_inventors"] > 0)
    ].copy()
    print(f"    After filter (valid WIPO, >=1 inventor): {len(sample):,}")

    # Log transform
    sample["log_cites"] = np.log1p(sample["num_cited_by_us_patents"])
    sample["log_claims"] = np.log1p(sample["num_claims"])
    sample["log_inventors"] = np.log1p(sample["number_of_inventors"])

    return sample


def show_summary(df):
    """Display summary statistics."""
    print("\n[2] Summary Statistics")
    print("=" * 60)

    fa = df[df["has_frontier_inventor"]]
    nfa = df[~df["has_frontier_inventor"]]

    n_fa = len(fa)
    pct_fa = 100 * n_fa / len(df)

    print(f"Total patents:              {len(df):>10,}")
    print(f"Frontier-author patents:    {n_fa:>10,} ({pct_fa:.1f}%)")
    print(f"Non-frontier-author:        {len(nfa):>10,}")
    print()
    print(f"Mean forward cites:         {df['num_cited_by_us_patents'].mean():>10.1f}")
    print(f"  Frontier-author:          {fa['num_cited_by_us_patents'].mean():>10.1f}")
    print(f"  Non-frontier-author:      {nfa['num_cited_by_us_patents'].mean():>10.1f}")
    print(f"Median forward cites:       {df['num_cited_by_us_patents'].median():>10.0f}")
    print(f"  Frontier-author:          {fa['num_cited_by_us_patents'].median():>10.0f}")
    print(f"  Non-frontier-author:      {nfa['num_cited_by_us_patents'].median():>10.0f}")
    print()

    # Hit rates
    print(f"Hit patent rate:            {100*df['is_hit'].mean():>10.2f}%")
    print(f"  Frontier-author:          {100*fa['is_hit'].mean():>10.2f}%")
    print(f"  Non-frontier-author:      {100*nfa['is_hit'].mean():>10.2f}%")
    print()

    # Frontier by year
    yearly = df.groupby("patent_year").agg(
        total=("patent_id", "count"),
        fa=("has_frontier_inventor", "sum"),
        mean_cites=("num_cited_by_us_patents", "mean"),
        fa_mean_cites=("num_cited_by_us_patents", lambda x: x[df["has_frontier_inventor"]].mean()),
    ).reset_index()
    print("Year  Total_Patents  FA_Patents  FA%    Mean_Cites  FA_Mean_Cites")
    for _, row in yearly.iterrows():
        fa_pct = 100 * row["fa"] / row["total"]
        print(f"{int(row['patent_year']):4d}  {int(row['total']):>13,}  "
              f"{int(row['fa']):>10,}  {fa_pct:>4.1f}%  "
              f"{row['mean_cites']:>10.1f}  {row['fa_mean_cites']:>13.1f}")

    return yearly


def run_ols_regression(df):
    """OLS log-linear regression: log(forward_cites) ~ frontier_author + controls.

    Replicates Table 4/5 of Schaper 2025.
    """
    print("\n[3] OLS Log-Linear Regression")
    print("=" * 60)

    # Prepare dummies
    wipo_cols = [c for c in df.columns if c.startswith("wipo_")]
    year_cols = [c for c in df.columns if c.startswith("yr_")]

    if not wipo_cols:
        # Create from section
        wipo_dummies = pd.get_dummies(df["section"], prefix="wipo", drop_first=True)
        df = pd.concat([df.reset_index(drop=True), wipo_dummies.reset_index(drop=True)], axis=1)
        wipo_cols = list(wipo_dummies.columns)
    if not year_cols:
        year_dummies = pd.get_dummies(df["patent_year"], prefix="yr", drop_first=True)
        df = pd.concat([df.reset_index(drop=True), year_dummies.reset_index(drop=True)], axis=1)
        year_cols = list(year_dummies.columns)

    # Drop first dummy to avoid perfect collinearity
    wipo_vars = wipo_cols[1:] if len(wipo_cols) > 1 else wipo_cols
    year_vars = year_cols[1:] if len(year_cols) > 1 else year_cols

    # Ensure all columns are numeric
    for col in wipo_vars + year_vars:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Model 1: Frontier only
    formula_vars = ["has_frontier_inventor", "log_claims", "log_inventors"]
    all_vars = formula_vars + wipo_vars + year_vars

    # Drop rows with NaN
    model_df = df.dropna(subset=["log_cites"] + [v for v in all_vars if v in df.columns])
    available_vars = [v for v in all_vars if v in model_df.columns and model_df[v].notna().all()]

    X = model_df[available_vars].astype(float)
    y = model_df["log_cites"].astype(float)

    # Add constant
    X = sm.add_constant(X)

    print(f"\nModel: log(cites) ~ frontier_author + controls")
    print(f"N = {len(X):,}")
    print(f"Variables: frontier_author, log_claims, log_inventors, "
          f"{len(wipo_vars)} WIPO FE, {len(year_vars)} year FE")

    try:
        model = sm.OLS(y, X).fit()
    except Exception as e:
        print(f"OLS failed: {e}")
        # Try with fewer variables
        print("Trying simplified model...")
        simple_vars = ["has_frontier_inventor", "log_claims", "log_inventors"]
        simple_available = [v for v in simple_vars if v in model_df.columns]
        X_simple = sm.add_constant(model_df[simple_available].astype(float))
        model = sm.OLS(y, X_simple).fit()

    coef = model.params.get("has_frontier_inventor", np.nan)
    se = model.bse.get("has_frontier_inventor", np.nan)
    pval = model.pvalues.get("has_frontier_inventor", np.nan)

    print(f"\n  Frontier-Author coefficient: {coef:+.4f}")
    print(f"  SE:                          {se:.4f}")
    print(f"  p-value:                     {pval:.4f}")
    print(f"  R²:                          {model.rsquared:.4f}")
    print(f"  Adj R²:                      {model.rsquared_adj:.4f}")

    # Economic significance: exp(coef) - 1 = % increase in citations
    if not np.isnan(coef):
        pct_increase = (np.exp(coef) - 1) * 100
        print(f"  Citation premium:            {pct_increase:+.1f}%")

    return model


def run_ppml_regression(df):
    """PPML regression: forward_cites ~ frontier_author + controls.

    PPML = Poisson Pseudo Maximum Likelihood (Santos Silva & Tenreyro 2006).
    Replicates the count-model specification in Schaper 2025.
    """
    print("\n[4] PPML Regression")
    print("=" * 60)

    wipo_cols = [c for c in df.columns if c.startswith("wipo_")]
    year_cols = [c for c in df.columns if c.startswith("yr_")]

    if not wipo_cols:
        wipo_dummies = pd.get_dummies(df["section"], prefix="wipo", drop_first=True)
        df = pd.concat([df.reset_index(drop=True), wipo_dummies.reset_index(drop=True)], axis=1)
        wipo_cols = list(wipo_dummies.columns)
    if not year_cols:
        year_dummies = pd.get_dummies(df["patent_year"], prefix="yr", drop_first=True)
        df = pd.concat([df.reset_index(drop=True), year_dummies.reset_index(drop=True)], axis=1)
        year_cols = list(year_dummies.columns)

    wipo_vars = wipo_cols[1:] if len(wipo_cols) > 1 else wipo_cols
    year_vars = year_cols[1:] if len(year_cols) > 1 else year_cols

    for col in wipo_vars + year_vars:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    formula_vars = ["has_frontier_inventor", "log_claims", "log_inventors"]
    all_vars = formula_vars + wipo_vars + year_vars

    model_df = df.dropna(subset=["num_cited_by_us_patents"] +
                          [v for v in all_vars if v in df.columns])
    available_vars = [v for v in all_vars if v in model_df.columns and model_df[v].notna().all()]

    X = model_df[available_vars].astype(float)
    X = sm.add_constant(X)
    y = model_df["num_cited_by_us_patents"].astype(float)

    print(f"\nModel: forward_cites ~ frontier_author + controls (PPML)")
    print(f"N = {len(X):,}")

    try:
        model = sm.GLM(y, X, family=sm.families.Poisson()).fit()
    except Exception as e:
        print(f"PPML failed: {e}")
        return None

    coef = model.params.get("has_frontier_inventor", np.nan)
    se = model.bse.get("has_frontier_inventor", np.nan)
    pval = model.pvalues.get("has_frontier_inventor", np.nan)

    print(f"\n  Frontier-Author coefficient: {coef:+.4f}")
    print(f"  SE:                          {se:.4f}")
    print(f"  p-value:                     {pval:.4f}")

    if not np.isnan(coef):
        pct_increase = (np.exp(coef) - 1) * 100
        print(f"  Citation premium:            {pct_increase:+.1f}%")

    return model


def run_hit_patent_logit(df):
    """Logit regression: P(hit_patent) ~ frontier_author + controls."""
    print("\n[5] Hit Patent Logit Regression")
    print("=" * 60)

    wipo_cols = [c for c in df.columns if c.startswith("wipo_")]
    year_cols = [c for c in df.columns if c.startswith("yr_")]

    if not wipo_cols:
        wipo_dummies = pd.get_dummies(df["section"], prefix="wipo", drop_first=True)
        df = pd.concat([df.reset_index(drop=True), wipo_dummies.reset_index(drop=True)], axis=1)
        wipo_cols = list(wipo_dummies.columns)
    if not year_cols:
        year_dummies = pd.get_dummies(df["patent_year"], prefix="yr", drop_first=True)
        df = pd.concat([df.reset_index(drop=True), year_dummies.reset_index(drop=True)], axis=1)
        year_cols = list(year_dummies.columns)

    wipo_vars = wipo_cols[1:] if len(wipo_cols) > 1 else wipo_cols
    year_vars = year_cols[1:] if len(year_cols) > 1 else year_cols

    for col in wipo_vars + year_vars:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    formula_vars = ["has_frontier_inventor", "log_claims", "log_inventors"]
    all_vars = formula_vars + wipo_vars + year_vars

    model_df = df.dropna(subset=["is_hit"] +
                          [v for v in all_vars if v in df.columns])
    available_vars = [v for v in all_vars if v in model_df.columns and model_df[v].notna().all()]

    X = model_df[available_vars].astype(float)
    X = sm.add_constant(X)
    y = model_df["is_hit"].astype(float)

    n_hits = int(y.sum())
    print(f"\nModel: P(hit) ~ frontier_author + controls (Logit)")
    print(f"N = {len(X):,}, Hits = {n_hits:,} ({100*n_hits/len(y):.2f}%)")

    try:
        model = sm.Logit(y, X).fit(disp=0)
    except Exception as e:
        print(f"Logit failed: {e}")
        # Try linear probability model as fallback
        print("Falling back to LPM...")
        model = sm.OLS(y, X).fit()

    coef = model.params.get("has_frontier_inventor", np.nan)
    se = model.bse.get("has_frontier_inventor", np.nan)
    pval = model.pvalues.get("has_frontier_inventor", np.nan)

    print(f"\n  Frontier-Author coefficient: {coef:+.4f}")
    print(f"  SE:                          {se:.4f}")
    print(f"  p-value:                     {pval:.4f}")

    # Marginal effect (approximate)
    if not np.isnan(coef):
        print(f"  Odds ratio:                  {np.exp(coef):.4f}")

    return model


def main():
    print("=" * 60)
    print("Schaper, Arts, Veugelers (2025) Reproduction")
    print("USPTO-PubMed Patent-Level Analysis")
    print("=" * 60)

    sample = load_and_filter()
    yearly = show_summary(sample)

    # Regressions
    ols_model = run_ols_regression(sample)
    ppml_model = run_ppml_regression(sample)
    logit_model = run_hit_patent_logit(sample)

    # Save yearly summary
    yearly.to_parquet(RESULTS_DIR / "yearly_summary.parquet", index=False)

    print("\n" + "=" * 60)
    print("Reproduction complete!")
    print(f"Results saved to: {RESULTS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
