#!/usr/bin/env python3
"""
Reproduction of the main quantitative analysis from:
Wu, Wang, Evans (2019) "Large teams develop and small teams disrupt science and technology"
Nature 566, 378-382.

This script implements the disruption index (D-index) and regressions linking
team size to disruptiveness and citation impact using a SYNTHETIC dataset.

REAL DATA REQUIREMENTS (stub):
  - Table `papers`: paper_id (int), authors_count (int), year (int), field (int/str), num_refs (int)
  - Table `citations`: citing_paper_id (int) -> cited_paper_id (int)
  - Actual sources: Web of Science, USPTO, GitHub (65M+ papers/patents/software)
  - Disruption index computation requires the full citation graph to classify
    future papers into n_i, n_j, n_k as defined in Funk & Owen-Smith (2017).

We generate a small synthetic citation network that mimics the reported patterns:
small teams produce more disruptive work (higher D-index), large teams receive more citations.
"""

import numpy as np
import pandas as pd
import math
import warnings

warnings.filterwarnings('ignore')

# ========================== DATA GENERATION (STUB) ==========================
np.random.seed(42)
N = 2000                       # number of papers
n_fields = 3
year_start, year_end = 2000, 2020

# IDs and monotonic years (stricly increasing, ensures temporal order)
ids = np.arange(N)
years = np.array([year_start + int(i * (year_end - year_start) / N) for i in range(N)])

# Team size: lognormal with median ~ 3
authors_count = np.round(np.random.lognormal(mean=1.0, sigma=0.5, size=N)).astype(int)
authors_count = np.maximum(authors_count, 1)

# Field (categorical)
field = np.random.randint(0, n_fields, size=N)

papers = pd.DataFrame({
    'id': ids,
    'authors_count': authors_count,
    'year': years,
    'field': field
})

# ---------- citation graph construction ----------
# refs[i] : set of papers cited by i (must have ID < i)
refs = {i: set() for i in range(N)}

# Bias toward citing larger teams (to create positive team size – citation correlation)
gamma = 0.6
weights = np.exp(gamma * np.log(authors_count))  # weight for being cited

for j in range(1, N):
    n_refs = np.random.poisson(10)
    n_refs = min(n_refs, j)   # cannot cite more than j earlier papers
    if n_refs == 0:
        continue
    w = weights[:j].copy()
    p = w / w.sum()
    chosen = np.random.choice(j, size=n_refs, replace=False, p=p)
    refs[j].update(chosen)

# ---------- post-process to enforce disruption pattern ----------
median_team = np.median(authors_count)

for i in range(N):
    team = authors_count[i]
    # all future papers j that cite i
    citing = [j for j in range(i+1, N) if i in refs[j]]
    for j in citing:
        if team <= median_team:
            # small team → disrupt: remove references of i from j's reference list
            common = refs[i].intersection(refs[j])
            if common:
                refs[j].difference_update(common)
        else:
            # large team → develop: ensure j also cites all references of i
            refs[j].update(refs[i])

# ===================== DISRUPTION INDEX COMPUTATION =========================
def compute_disruption(i, refs, N):
    """Compute D-index for paper i using future papers (ID > i)."""
    refs_i = refs[i]
    ni = nj = nk = 0
    for j in range(i+1, N):
        refs_j = refs[j]
        cites_focal = (i in refs_j)
        cites_any_ref = not refs_i.isdisjoint(refs_j)
        if cites_focal and not cites_any_ref:
            ni += 1
        elif cites_focal and cites_any_ref:
            nj += 1
        elif not cites_focal and cites_any_ref:
            nk += 1
    denom = ni + nj + nk
    if denom == 0:
        return 0.0
    return (ni - nk) / denom

D = np.array([compute_disruption(i, refs, N) for i in range(N)])

# Citation count (future citations only, as used for citation impact)
cit_count = np.array([
    sum(1 for j in range(i+1, N) if i in refs[j])
    for i in range(N)
], dtype=int)

# Number of references (control variable)
num_refs = np.array([len(refs[i]) for i in range(N)])

# add to DataFrame
papers['disruption'] = D
papers['log_authors'] = np.log(authors_count)
papers['log_num_refs'] = np.log(num_refs + 1e-5)  # avoid log(0)
papers['log_cit'] = np.log(cit_count + 1.0)       # citation impact

# ===================== REGRESSION ANALYSES =========================
# Dummy variables for field and year
field_dummies = pd.get_dummies(papers['field'], prefix='field', drop_first=True)
year_dummies = pd.get_dummies(papers['year'], prefix='year', drop_first=True)

# Build design matrix with constant
X_vars = pd.concat([
    papers[['log_authors', 'log_num_refs']],
    field_dummies,
    year_dummies
], axis=1)
X_df = pd.concat([pd.Series(np.ones(N), name='const'), X_vars], axis=1)

# ----- manual OLS helper (uses normal approx for p-values) -----
def ols_fit(X, y):
    """Fit OLS, return coeffs, se, t, p (normal approx)."""
    Xm = X.values if isinstance(X, pd.DataFrame) else X
    ym = y
    coeffs, residuals, rank, s = np.linalg.lstsq(Xm, ym, rcond=None)
    # standard errors
    n, k = Xm.shape
    df_resid = n - k
    residuals = ym - Xm @ coeffs
    sig2 = np.sum(residuals**2) / df_resid
    var_covar = sig2 * np.linalg.pinv(Xm.T @ Xm)
    ses = np.sqrt(np.diag(var_covar))
    t_vals = coeffs / ses
    # p-values (two-sided using normal approximation, valid for large df)
    p_vals = [2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2)))) for t in t_vals]
    return coeffs, ses, t_vals, p_vals

# disruption model
Xmat = X_df.values
y_dis = papers['disruption'].values
coef_dis, se_dis, t_dis, p_dis = ols_fit(X_df, y_dis)

# citation impact model
y_cit = papers['log_cit'].values
coef_cit, se_cit, t_cit, p_cit = ols_fit(X_df, y_cit)

# extract key coefficient
idx_log_auth = list(X_df.columns).index('log_authors')

print("="*60)
print("Regression results: Disruption ~ log(team_size) + controls")
print(f"coef(log_authors) = {coef_dis[idx_log_auth]:.4f}, p = {p_dis[idx_log_auth]:.4f}")
print("\nRegression results: log(citation_count) ~ log(team_size) + controls")
print(f"coef(log_authors) = {coef_cit[idx_log_auth]:.4f}, p = {p_cit[idx_log_auth]:.4f}")

# Additional descriptive statistics: average D by team size quartiles
papers['team_size_q'] = pd.qcut(papers['authors_count'], q=4, labels=['Q1(small)', 'Q2', 'Q3', 'Q4(large)'])
mean_d_by_q = papers.groupby('team_size_q')['disruption'].mean()
print("\nMean disruption by team-size quartile:")
print(mean_d_by_q)

# Conclusion
if coef_dis[idx_log_auth] < 0 and coef_cit[idx_log_auth] > 0:
    print("\nCONCLUSION: Small teams are associated with higher disruption (negative coefficient),")
    print("while large teams are associated with higher citation impact (positive coefficient).")
    print("This matches the paper's core finding: 'large teams develop, small teams disrupt'.")
else:
    print("\nCONCLUSION: The sign pattern did not fully emerge in this synthetic run; check data generation parameters.")

print("="*60)
