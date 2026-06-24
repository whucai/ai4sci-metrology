import numpy as np
import pandas as pd
import statsmodels.api as sm
from src.sciscigpt_local.sciscinet_connector import load_papers_sample

# =============================================================================
# 1. DATA LOADING
# =============================================================================
print("=== DATA_LOAD ===")

# Load data (10 shards as specified)
papers = load_papers_sample(n_shards=10)
print(f"Initial sample size: {len(papers)}")

# Drop rows with NaN in required columns
required_cols = ['disruption_score', 'reference_count', 'author_count', 'citation_count_5y', 'year']
papers = papers.dropna(subset=required_cols)
print(f"After dropping NaNs in key columns: {len(papers)}")

# Convert nullable Int64/Float64 columns to standard types
papers['reference_count'] = papers['reference_count'].astype(float)
papers['author_count'] = papers['author_count'].astype(float)
papers['citation_count_5y'] = papers['citation_count_5y'].astype(float)
papers['disruption_score'] = papers['disruption_score'].astype(float)
papers['year'] = papers['year'].astype(int)

# Year range filter: 2011 to 2015 inclusive
papers = papers[(papers['year'] >= 2011) & (papers['year'] <= 2015)]
print(f"After year filter (2011-2015): {len(papers)}")

# Reference count filter: 10 <= reference_count <= 200
papers = papers[(papers['reference_count'] >= 10) & (papers['reference_count'] <= 200)]
print(f"After reference_count filter (10-200): {len(papers)}")

# Author count filter: 1 <= author_count <= 25
papers = papers[(papers['author_count'] >= 1) & (papers['author_count'] <= 25)]
print(f"After author_count filter (1-25): {len(papers)}")

# Citation count (5yr) filter: 1 <= citation_count_5y <= 1000
papers = papers[(papers['citation_count_5y'] >= 1) & (papers['citation_count_5y'] <= 1000)]
print(f"After citation_count_5y filter (1-1000): {len(papers)}")

# Final check for any remaining NaN in the subset (should be none)
papers = papers.dropna(subset=required_cols)
print(f"Final sample size after all filters: {len(papers)}")

# =============================================================================
# 2. DESCRIPTIVE STATISTICS
# =============================================================================
print("\n=== DESCRIPTIVE ===")

# Create absolute disruption score
papers['abs_CD'] = papers['disruption_score'].abs()

mean_abs_CD = papers['abs_CD'].mean()
mean_rp = papers['reference_count'].mean()
mean_kp = papers['author_count'].mean()
mean_cp5 = papers['citation_count_5y'].mean()
std_abs_CD = papers['abs_CD'].std()

print(f"Mean |CD|: {mean_abs_CD:.6f}")
print(f"Mean reference_count (rp): {mean_rp:.4f}")
print(f"Mean author_count (kp): {mean_kp:.4f}")
print(f"Mean citation_count_5y (cp5): {mean_cp5:.4f}")
print(f"Std |CD|: {std_abs_CD:.6f}")

# =============================================================================
# 3. TRANSFORMATION TO LOGS
# =============================================================================
print("\n=== TRANSFORM ===")

papers['ln_kp'] = np.log(papers['author_count'])
papers['ln_rp'] = np.log(papers['reference_count'])
papers['ln_cp5'] = np.log(papers['citation_count_5y'])

print(f"ln_kp: min={papers['ln_kp'].min():.6f}, max={papers['ln_kp'].max():.6f}")
print(f"ln_rp: min={papers['ln_rp'].min():.6f}, max={papers['ln_rp'].max():.6f}")
print(f"ln_cp5: min={papers['ln_cp5'].min():.6f}, max={papers['ln_cp5'].max():.6f}")

# =============================================================================
# 4. REGRESSION MODEL (Eq. 2)
# =============================================================================
print("\n=== REGRESSION ===")

# Create year dummies (drop first year, 2011, as baseline)
year_dummies = pd.get_dummies(papers['year'], prefix='year', drop_first=True)

# Build design matrix: intercept + log variables + year dummies
X = pd.concat([
    papers[['ln_kp', 'ln_rp', 'ln_cp5']],
    year_dummies.astype(float)
], axis=1)
X = sm.add_constant(X)  # intercept
y = papers['abs_CD'].copy()

# OLS regression (no robust / clustered errors)
model = sm.OLS(y, X).fit()

print(model.summary())

# =============================================================================
# 5. COEFFICIENTS (separate print)
# =============================================================================
print("\n=== COEFFICIENTS ===")

# Extract results for the three log‑transformed variables
coeffs = {
    'ln_kp': model.params['ln_kp'],
    'ln_rp': model.params['ln_rp'],
    'ln_cp5': model.params['ln_cp5']
}
se = {
    'ln_kp': model.bse['ln_kp'],
    'ln_rp': model.bse['ln_rp'],
    'ln_cp5': model.bse['ln_cp5']
}
pvals = {
    'ln_kp': model.pvalues['ln_kp'],
    'ln_rp': model.pvalues['ln_rp'],
    'ln_cp5': model.pvalues['ln_cp5']
}

for var in ['ln_kp', 'ln_rp', 'ln_cp5']:
    print(f"{var}: coef={coeffs[var]:.8f}, std_err={se[var]:.8f}, p_value={pvals[var]:.6f}")

# =============================================================================
# 6. RESULTS SUMMARY
# =============================================================================
print("\n=== RESULTS ===")
print(f"Sample N = {model.nobs}")
print(f"R-squared = {model.rsquared:.6f}")

# Direction of each coefficient
for var in ['ln_kp', 'ln_rp', 'ln_cp5']:
    direction = "positive" if coeffs[var] > 0 else "negative"
    print(f"Direction of {var} coefficient: {direction}")

# =============================================================================
# DIFF TABLE (final required output)
# =============================================================================
print("\n=== DIFF_TABLE ===")
print(f"| Metric | Agent Value |")
print(f"|--------|-------------|")
print(f"| sample_N | {model.nobs} |")
print(f"| R_squared | {model.rsquared:.6f} |")
print(f"| coef_ln_kp | {coeffs['ln_kp']:.6f} |")
print(f"| coef_ln_rp | {coeffs['ln_rp']:.6f} |")
print(f"| coef_ln_cp5 | {coeffs['ln_cp5']:.6f} |")
print(f"| p_ln_kp | {pvals['ln_kp']:.6f} |")
print(f"| p_ln_rp | {pvals['ln_rp']:.6f} |")
print(f"| p_ln_cp5 | {pvals['ln_cp5']:.6f} |")