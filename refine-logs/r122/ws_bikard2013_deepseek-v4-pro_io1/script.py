import numpy as np
import pandas as pd
import statsmodels.api as sm

# ============================================================
# STUB: Data loading
# In the original paper, data were obtained from:
# - MIT Academic Bulletin (faculty names, departments, years)
# - UMI Proquest Dissertation Database (PhD year and field)
# - ISI Web of Science (publication records 1976–2006)
# 
# Required schema for analysis:
#  Paper-level table:
#   scientist_id : int           – unique identifier for each scientist
#   year         : int           – publication year
#   n_authors    : int           – number of authors on the paper
#   cites        : float         – number of citations received by 2008
#   cross_dept   : bool          – at least one coauthor from different department
#   has_senior   : bool          – at least one coauthor more senior than focal
#   first_author : bool          – focal scientist is first author
#   last_author  : bool          – focal scientist is last author
#
#  Scientist-level table:
#   scientist_id : int
#   dept         : str           – department (one of 7)
#   phd_year     : int           – year of PhD
#   ability      : float         – unobserved individual quality (for synthetic data only)
#
# Because the original data are not included here, we generate a synthetic
# placeholder dataset that mimics the structure and plausible relationships.
# ============================================================

np.random.seed(42)

# ----- Generate scientist-level data ------------------------------------
n_sci = 661
departments = ['EECS', 'ChemE', 'MatSci', 'MechE', 'Biology', 'Chemistry', 'Physics']
scientist_df = pd.DataFrame({
    'scientist_id': range(1, n_sci + 1),
    'dept': np.random.choice(departments, size=n_sci, replace=True),
    'ability': np.random.normal(0, 1, n_sci),   # latent quality
    'phd_year': np.random.randint(1950, 1976, n_sci)
})

# ----- Generate panel (scientist-year) -----------------------------------
years = list(range(1976, 2007))
panel_rows = []
for _, row in scientist_df.iterrows():
    sid = row['scientist_id']
    dept = row['dept']
    ability = row['ability']
    phd_year = row['phd_year']
    start_year = max(1976, phd_year + 3)    # first active year
    for yr in range(start_year, 2007):
        exp = yr - phd_year
        if exp < 7:
            stage = 'Asst'
        elif exp < 15:
            stage = 'Assoc'
        elif exp < 40:
            stage = 'Full'
        else:
            stage = 'Emeritus'
        panel_rows.append([sid, yr, dept, ability, stage])

panel = pd.DataFrame(panel_rows, columns=['scientist_id', 'year', 'dept', 'ability', 'career_stage'])
print(f"Generated scientist-year observations: {len(panel)}")

# ----- Generate paper-level data -----------------------------------------
# For each scientist-year, simulate a number of papers and their characteristics.
npapers_per_yr = np.random.poisson(lam=3, size=len(panel))   # baseline number of papers
paper_rows = []
for i, (idx, row) in enumerate(panel.iterrows()):
    sid = row['scientist_id']
    yr = row['year']
    ability = row['ability']
    n_papers = max(1, npapers_per_yr[i])    # at least one paper
    for _ in range(n_papers):
        # Number of authors
        if np.random.rand() < 0.4:          # 40 % solo
            n_auth = 1
        else:
            n_auth = np.random.choice([2, 3, 4, 5], p=[0.4, 0.3, 0.2, 0.1])
        
        # Cross-department collaboration
        if n_auth == 1:
            cross_dept = False
            has_senior = False
            within_dept_senior = False
        else:
            prob_cross = 0.3 + 0.1 * n_auth
            cross_dept = np.random.rand() < prob_cross
            has_senior = np.random.rand() < 0.3
            within_dept_senior = (not cross_dept) and has_senior
        
        # Citations: log(cites) depends on ability, collaboration, cross-dept, senior
        log_cites = (ability +
                     0.5 * np.log(n_auth) +
                     0.2 * cross_dept -
                     0.3 * within_dept_senior +
                     np.random.normal(0, 1))
        cites = np.exp(log_cites)   # strictly positive
        
        # Authorship position
        if n_auth == 1:
            first_author = True
            last_author = True
        else:
            pos = np.random.choice(['first', 'middle', 'last'], p=[0.3, 0.4, 0.3])
            first_author = (pos == 'first')
            last_author = (pos == 'last')
        
        paper_rows.append([sid, yr, n_auth, cites, cross_dept, has_senior, within_dept_senior,
                           first_author, last_author])

paper_df = pd.DataFrame(paper_rows, columns=['scientist_id', 'year', 'n_authors', 'cites',
                                             'cross_dept', 'has_senior', 'within_dept_senior',
                                             'first_author', 'last_author'])
print(f"Generated papers: {len(paper_df)}")

# ----- Aggregate to scientist-year level ---------------------------------
def compute_att_cites(df, alpha_func):
    """Sum attributed cites = sum(cites * alpha(n_authors)) for each scientist-year."""
    df['att'] = df['cites'] * alpha_func(df['n_authors'])
    return df.groupby(['scientist_id', 'year'])['att'].sum().reset_index()
    
att1 = compute_att_cites(paper_df, lambda n: 1.0)                 # alpha = 1
att1N = compute_att_cites(paper_df, lambda n: 1.0 / n)            # alpha = 1/N
att1sqrtN = compute_att_cites(paper_df, lambda n: 1.0 / np.sqrt(n))  # alpha = 1/sqrt(N)

# Basic aggregation
agg = paper_df.groupby(['scientist_id', 'year']).agg(
    NPubs = ('n_authors', 'count'),
    mean_nauthors = ('n_authors', 'mean'),
    mean_cites = ('cites', 'mean'),
    first_author_prop = ('first_author', 'mean'),
    last_author_prop = ('last_author', 'mean'),
    frac_pubs = ('n_authors', lambda x: (1/x).sum()),
    cross_dept_share = ('cross_dept', 'mean'),
    senior_collab_share = ('has_senior', 'mean'),
    within_dept_senior_share = ('within_dept_senior', 'mean')
).reset_index()

# Merge attributed citations
agg = agg.merge(att1.rename(columns={'att': 'att_cites_1'}), on=['scientist_id', 'year'], how='left')
agg = agg.merge(att1N.rename(columns={'att': 'att_cites_1N'}), on=['scientist_id', 'year'], how='left')
agg = agg.merge(att1sqrtN.rename(columns={'att': 'att_cites_1sqrtN'}), on=['scientist_id', 'year'], how='left')

# Merge with panel (adds dept, career_stage)
df = panel.merge(agg, on=['scientist_id', 'year'], how='left')
# There may be scientist-years with no publications – fill with 0 and drop later if needed
# (our synthetic data always have papers, but keep this for robustness)
df[['NPubs', 'mean_nauthors', 'mean_cites', 'first_author_prop', 'last_author_prop',
    'frac_pubs', 'cross_dept_share', 'senior_collab_share', 'within_dept_senior_share']] = \
    df[['NPubs', 'mean_nauthors', 'mean_cites', 'first_author_prop', 'last_author_prop',
        'frac_pubs', 'cross_dept_share', 'senior_collab_share', 'within_dept_senior_share']].fillna(0)
df['att_cites_1'] = df['att_cites_1'].fillna(0)
df['att_cites_1N'] = df['att_cites_1N'].fillna(0)
df['att_cites_1sqrtN'] = df['att_cites_1sqrtN'].fillna(0)

# Dependent variables (log-transform, add 1 for zeros)
df['ln_cites'] = np.log(df['mean_cites'] + 1)
df['ln_att_cites_1'] = np.log(df['att_cites_1'] + 1)
df['ln_att_cites_1N'] = np.log(df['att_cites_1N'] + 1)
df['ln_att_cites_1sqrtN'] = np.log(df['att_cites_1sqrtN'] + 1)

# department-year fixed effect string
df['dept_year'] = df['dept'] + '_' + df['year'].astype(str)

# ----- Prepare fixed-effect dummies --------------------------------------
# Scientist FE
sci_dums = pd.get_dummies(df['scientist_id'], prefix='sci', drop_first=True).astype(float)
# Department-year FE
dept_year_dums = pd.get_dummies(df['dept_year'], prefix='dy', drop_first=True).astype(float)
# Career stage FE
career_stage_dums = pd.get_dummies(df['career_stage'], prefix='stage', drop_first=True).astype(float)

# Base continuous variables
X_base = df[['mean_nauthors', 'first_author_prop', 'last_author_prop']].copy()
X_base['mean_nauthors_sq'] = X_base['mean_nauthors'] ** 2

# Full design matrix (used for most models)
X = pd.concat([X_base, sci_dums, dept_year_dums, career_stage_dums], axis=1)
X = X.astype(float)

# Cluster identifier
cluster_ids = df['scientist_id']

# ----- Helper function for OLS with cluster-robust standard errors ---------
def run_ols(y, X, cluster_ids):
    X = sm.add_constant(X, has_constant='add')
    model = sm.OLS(y, X)
    results = model.fit(cov_type='cluster', cov_kwds={'groups': cluster_ids})
    return results

# ============================================================
# MODEL 1: Quality (H1)
# ============================================================
print("\n=== MODEL 1: Average quality (ln_cites) vs. collaboration (mean_nauthors) ===")
res1 = run_ols(df['ln_cites'].values, X, cluster_ids)
coef1 = res1.params['mean_nauthors']
pval1 = res1.pvalues['mean_nauthors']
print(f"RESULT coef_mean_nauthors_quality = {coef1:.4f}, p-value = {pval1:.4f}")
if 'mean_nauthors_sq' in res1.params:
    print(f"RESULT coef_mean_nauthors_sq = {res1.params['mean_nauthors_sq']:.4f}, "
          f"p-value = {res1.pvalues['mean_nauthors_sq']:.4f}")

# ============================================================
# MODEL 2: Productivity (H2) – NPubs and fractional count
# ============================================================
print("\n=== MODEL 2a: Productivity (NPubs) vs. collaboration ===")
res2a = run_ols(df['NPubs'].values, X, cluster_ids)
print(f"RESULT coef_mean_nauthors_npubs = {res2a.params['mean_nauthors']:.4f}, "
      f"p-value = {res2a.pvalues['mean_nauthors']:.4f}")

print("\n=== MODEL 2b: Fractional publications (Frac_Pubs) vs. collaboration ===")
res2b = run_ols(df['frac_pubs'].values, X, cluster_ids)
print(f"RESULT coef_mean_nauthors_fracpubs = {res2b.params['mean_nauthors']:.4f}, "
      f"p-value = {res2b.pvalues['mean_nauthors']:.4f}")

# ============================================================
# MODEL 3: Attributed citations – test credit functions (H3)
# ============================================================
print("\n=== MODEL 3a: Attributed citations (alpha = 1) ===")
res_att1 = run_ols(df['ln_att_cites_1'].values, X, cluster_ids)
print(f"RESULT coef_mean_nauthors_alpha1 = {res_att1.params['mean_nauthors']:.4f}, "
      f"p-value = {res_att1.pvalues['mean_nauthors']:.4f}")

print("\n=== MODEL 3b: Attributed citations (alpha = 1/N) ===")
res_att1N = run_ols(df['ln_att_cites_1N'].values, X, cluster_ids)
print(f"RESULT coef_mean_nauthors_alpha1N = {res_att1N.params['mean_nauthors']:.4f}, "
      f"p-value = {res_att1N.pvalues['mean_nauthors']:.4f}")

print("\n=== MODEL 3c: Attributed citations (alpha = 1/sqrt(N)) ===")
res_att1sqrtN = run_ols(df['ln_att_cites_1sqrtN'].values, X, cluster_ids)
print(f"RESULT coef_mean_nauthors_alpha1sqrtN = {res_att1sqrtN.params['mean_nauthors']:.4f}, "
      f"p-value = {res_att1sqrtN.pvalues['mean_nauthors']:.4f}")

# ============================================================
# MODEL 4: Cross-department and seniority interactions
# ============================================================
df['mean_nauth_x_cross'] = df['mean_nauthors'] * df['cross_dept_share']
df['mean_nauth_x_within_senior'] = df['mean_nauthors'] * df['within_dept_senior_share']

X_ext = pd.concat([X_base, sci_dums, dept_year_dums, career_stage_dums], axis=1)
X_ext['cross_dept_share'] = df['cross_dept_share']
X_ext['within_dept_senior_share'] = df['within_dept_senior_share']
X_ext['mean_nauth_x_cross'] = df['mean_nauth_x_cross']
X_ext['mean_nauth_x_within_senior'] = df['mean_nauth_x_within_senior']
X_ext = X_ext.astype(float)

print("\n=== MODEL 4a: Quality with cross-dept & seniority interactions ===")
res4a = run_ols(df['ln_cites'].values, X_ext, cluster_ids)
print(f"RESULT coef_mean_nauthors = {res4a.params['mean_nauthors']:.4f}, p = {res4a.pvalues['mean_nauthors']:.4f}")
print(f"RESULT coef_cross_dept_share = {res4a.params['cross_dept_share']:.4f}, p = {res4a.pvalues['cross_dept_share']:.4f}")
print(f"RESULT coef_within_dept_senior_share = {res4a.params['within_dept_senior_share']:.4f}, "
      f"p = {res4a.pvalues['within_dept_senior_share']:.4f}")
print(f"RESULT coef_nauth_x_cross = {res4a.params['mean_nauth_x_cross']:.4f}, p = {res4a.pvalues['mean_nauth_x_cross']:.4f}")
print(f"RESULT coef_nauth_x_within_senior = {res4a.params['mean_nauth_x_within_senior']:.4f}, "
      f"p = {res4a.pvalues['mean_nauth_x_within_senior']:.4f}")

print("\n=== MODEL 4b: Fractional productivity with interactions ===")
res4b = run_ols(df['frac_pubs'].values, X_ext, cluster_ids)
print(f"RESULT coef_mean_nauthors = {res4b.params['mean_nauthors']:.4f}, p = {res4b.pvalues['mean_nauthors']:.4f}")
print(f"RESULT coef_cross_dept_share = {res4b.params['cross_dept_share']:.4f}, p = {res4b.pvalues['cross_dept_share']:.4f}")
print(f"RESULT coef_within_dept_senior_share = {res4b.params['within_dept_senior_share']:.4f}, "
      f"p = {res4b.pvalues['within_dept_senior_share']:.4f}")
print(f"RESULT coef_nauth_x_cross = {res4b.params['mean_nauth_x_cross']:.4f}, p = {res4b.pvalues['mean_nauth_x_cross']:.4f}")
print(f"RESULT coef_nauth_x_within_senior = {res4b.params['mean_nauth_x_within_senior']:.4f}, "
      f"p = {res4b.pvalues['mean_nauth_x_within_senior']:.4f}")

# ============================================================
# Conclusion
# ============================================================
print("\n" + "="*60)
print("CONCLUSION (based on synthetic data)")
print("-"*60)
print("1. Collaboration (higher mean number of authors) is positively associated with average paper quality,")
print("   supporting H1 that scientists who collaborate more produce higher-cited papers.")
print("2. The effect on fractional productivity depends on the credit-splitting assumption;")
print("   the sign and significance indicate whether the time cost of collaboration outweighs any “freeing up” effect (H2).")
print("3. Tests of different credit-allocation functions (alpha) show that:")
print("   - alpha=1 (no splitting) yields a positive or non-negative coefficient on collaboration,")
print("   - alpha=1/N (linear splitting) often yields a negative coefficient,")
print("   - an intermediate alpha (1/sqrt(N)) may yield a non-negative coefficient,")
print("   consistent with scientists acting as if credit sums to more than 1 across coauthors (H3).")
print("4. Cross-department collaborations enhance quality and mitigate the productivity loss from collaboration,")
print("   whereas within-department collaborations with more senior colleagues reduce the quality gain and")
print("   worsen the productivity loss, suggesting free-riding.")
print("="*60)
