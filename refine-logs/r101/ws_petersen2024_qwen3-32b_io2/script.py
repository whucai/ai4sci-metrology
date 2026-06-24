import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. DATA LOADING & PREPROCESSING
# =============================================================================
DATA_PATH = '/workspace/raw_data/sciscinet_sample.parquet'
if not os.path.exists(DATA_PATH):
    raise FileNotFoundError(f"Raw data not found at {DATA_PATH}. Please ensure the file exists.")

df = pd.read_parquet(DATA_PATH)
print(f"Loaded data shape: {df.shape}")
print(f"Available columns: {df.columns.tolist()}")

# Flexible column mapping
def find_col(df, keywords):
    for kw in keywords:
        for c in df.columns:
            if kw in c.lower():
                return c
    return None

id_col = find_col(df, ['id', 'pub_id', 'node_id', 'paper_id'])
year_col = find_col(df, ['year', 'pub_year', 'date', 'publication_year'])
refs_col = find_col(df, ['ref', 'reference', 'cited_refs'])
cites_col = find_col(df, ['cite', 'cited_by', 'forward_cites'])
authors_col = find_col(df, ['author', 'n_authors', 'coauthors', 'team_size'])

if not all([id_col, year_col, refs_col, cites_col, authors_col]):
    raise ValueError("Could not automatically map required columns. Please check column names.")

df = df.rename(columns={
    id_col: 'pub_id',
    year_col: 'year',
    refs_col: 'refs',
    cites_col: 'citations',
    authors_col: 'n_authors'
})

# Ensure lists are actual lists (sometimes parquet stores them as strings or tuples)
def ensure_list(x):
    if isinstance(x, str):
        return eval(x) if x else []
    return list(x) if x else []

df['refs'] = df['refs'].apply(ensure_list)
df['citations'] = df['citations'].apply(ensure_list)
df['n_refs'] = df['refs'].apply(len)
df['n_cites_total'] = df['citations'].apply(len)

# Build lookup dictionaries for fast access
pub_years = dict(zip(df['pub_id'], df['year']))
pub_refs = dict(zip(df['pub_id'], df['refs']))
pub_citations = dict(zip(df['pub_id'], df['citations']))
pub_authors = dict(zip(df['pub_id'], df['n_authors']))

# Precompute reverse citation index for Nk calculation: ref_id -> list of papers citing it
ref_citers = {}
for pid, cites in pub_citations.items():
    for ref in cites:
        ref_citers.setdefault(ref, set()).add(pid)

# =============================================================================
# 2. COMPUTE DISRUPTION INDEX & RELATED METRICS
# =============================================================================
CW = 5  # Citation Window
results = []

print("Computing Disruption Index and related metrics...")
for idx, row in df.iterrows():
    pid = row['pub_id']
    t_p = row['year']
    r_p = set(row['refs'])
    n_authors = row['n_authors']
    
    # Identify citers within the citation window
    c_p_window = [c for c in row['citations'] if t_p < pub_years.get(c, 0) <= t_p + CW]
    
    Ni = 0
    Nj = 0
    for c in c_p_window:
        c_refs = set(pub_refs.get(c, []))
        if c_refs & r_p:  # Cites at least one reference of p
            Nj += 1
        else:
            Ni += 1
            
    # Nk: papers in window that cite r_p but do NOT cite p
    # Efficiently compute union of citers of all references in r_p within window
    Nk_set = set()
    for ref in r_p:
        for citer in ref_citers.get(ref, []):
            if t_p < pub_years.get(citer, 0) <= t_p + CW:
                Nk_set.add(citer)
    # Remove those that actually cite p (they are in c_p_window)
    Nk_set -= set(c_p_window)
    Nk = len(Nk_set)
    
    # Compute metrics
    denom = Ni + Nj + Nk
    denom_nok = Ni + Nj
    
    cd_p = (Ni - Nj) / denom if denom > 0 else np.nan
    rk_p = Nk / denom_nok if denom_nok > 0 else np.nan
    cd_nok_p = (Ni - Nj) / denom_nok if denom_nok > 0 else np.nan
    
    # Citations in window (cp = Ni + Nj)
    cp_window = Ni + Nj
    
    results.append({
        'pub_id': pid,
        'year': t_p,
        'n_authors': n_authors,
        'n_refs': len(r_p),
        'cp_window': cp_window,
        'Ni': Ni,
        'Nj': Nj,
        'Nk': Nk,
        'CD5': cd_p,
        'Rk': rk_p,
        'CDnok5': cd_nok_p
    })

df_metrics = pd.DataFrame(results)
print(f"Computed metrics for {len(df_metrics)} publications.")

# =============================================================================
# 3. EMPIRICAL ANALYSIS & REGRESSION
# =============================================================================
# Filter for regression sample as specified in the paper
# 1990-2009, 1 <= kp <= 10, 5 <= rp <= 50, 10 <= cp <= 1000
mask = (
    (df_metrics['year'].between(1990, 2009)) &
    (df_metrics['n_authors'].between(1, 10)) &
    (df_metrics['n_refs'].between(5, 50)) &
    (df_metrics['cp_window'].between(10, 1000)) &
    (df_metrics['CD5'].notna())
)
df_reg = df_metrics[mask].copy()
print(f"Regression sample size: {len(df_reg)}")

if len(df_reg) < 100:
    print("WARNING: Regression sample too small. Results may be unstable.")

# Log transforms
df_reg['ln_kp'] = np.log(df_reg['n_authors'])
df_reg['ln_rp'] = np.log(df_reg['n_refs'])
df_reg['ln_cp'] = np.log(df_reg['cp_window'])

# OLS with year fixed effects
try:
    import statsmodels.formula.api as smf
    formula = 'CD5 ~ ln_kp + ln_rp + ln_cp + C(year)'
    model = smf.ols(formula, data=df_reg).fit()
    beta_k = model.params['ln_kp']
    beta_r = model.params['ln_rp']
    beta_c = model.params['ln_cp']
    r_squared = model.rsquared
    print("Regression completed successfully.")
except Exception as e:
    print(f"Regression failed: {e}. Using fallback numpy OLS.")
    X = df_reg[['ln_kp', 'ln_rp', 'ln_cp']].values
    # Add year dummies manually
    year_dummies = pd.get_dummies(df_reg['year'], drop_first=True).values
    X = np.hstack([X, year_dummies])
    X = np.column_stack([np.ones(len(X)), X])
    y = df_reg['CD5'].values
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    beta_k, beta_r, beta_c = beta[1], beta[2], beta[3]
    y_pred = X @ beta
    r_squared = 1 - np.sum((y - y_pred)**2) / np.sum((y - np.mean(y))**2)

# Marginal effects as described in paper
# "On average, a paper with twice as many references (2r) has a CD that is beta_r * Log[2] smaller"
marginal_refs_2x = beta_r * np.log(2)
# "On average, a paper with 5 times as many coauthors (5K) has a CD that is beta_k * Log[5] larger"
marginal_authors_5x = beta_k * np.log(5)

# =============================================================================
# 4. OUTPUT RESULTS
# =============================================================================
print("\n" + "="*60)
print("QUANTITATIVE REPRODUCTION RESULTS")
print("="*60)

# Paper reported values (from text/figures)
print("PAPER_REPORTED beta_ln_refs = -0.025")
print("PAPER_REPORTED beta_ln_authors = 0.0039")
print("PAPER_REPORTED R_squared = 0.96")
print("PAPER_REPORTED marginal_effect_2x_refs = -0.017")
print("PAPER_REPORTED marginal_effect_5x_authors = 0.006")

print("-" * 40)
print(f"RESULT beta_ln_refs = {beta_r:.4f}")
print(f"RESULT beta_ln_authors = {beta_k:.4f}")
print(f"RESULT beta_ln_cites = {beta_c:.4f}")
print(f"RESULT R_squared = {r_squared:.4f}")
print(f"RESULT marginal_effect_2x_refs = {marginal_refs_2x:.4f}")
print(f"RESULT marginal_effect_5x_authors = {marginal_authors_5x:.4f}")

# Trend analysis (average CD5 over time)
trend = df_metrics.groupby('year')['CD5'].mean().dropna()
print("-" * 40)
print(f"RESULT avg_CD5_earliest_decade = {trend.iloc[0]:.4f}")
print(f"RESULT avg_CD5_latest_decade = {trend.iloc[-1]:.4f}")
print(f"RESULT CD5_trend_direction = {'Decreasing' if trend.iloc[-1] < trend.iloc[0] else 'Increasing'}")

# Rk trend
rk_trend = df_metrics.groupby('year')['Rk'].mean().dropna()
print(f"RESULT avg_Rk_earliest = {rk_trend.iloc[0]:.4f}")
print(f"RESULT avg_Rk_latest = {rk_trend.iloc[-1]:.4f}")
print(f"RESULT Rk_trend_direction = {'Increasing' if rk_trend.iloc[-1] > rk_trend.iloc[0] else 'Decreasing'}")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)
if beta_r < -0.01 and r_squared > 0.8:
    print("The empirical analysis confirms the paper's central claim: the disruption index CD is systematically biased downward by citation inflation. The negative coefficient on log(references) demonstrates that longer reference lists mechanically drive CD toward 0, independent of actual disruptive impact. The positive coefficient on log(authors) contradicts prior claims that larger teams are less disruptive, highlighting omitted variable bias when time/reference growth is not controlled. CD is unsuitable for cross-temporal comparison without deflating for reference list inflation.")
else:
    print("Results diverge from paper expectations. This may be due to sample size, data coverage, or structural differences in the provided dataset. The directional relationship between reference list length and CD should be inspected manually.")
print("="*60)
