import pandas as pd
import numpy as np
from scipy import stats
import statsmodels.api as sm
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.families.links import logit
import warnings
warnings.filterwarnings("ignore")

# ── Load the provided sample ────────────────────────────────────────────
DATA_PATH = "/workspace/raw_data/sciscinet_sample.parquet"
try:
    df = pd.read_parquet(DATA_PATH)
    print(f"Loaded data shape: {df.shape}")
    print("Columns present:", df.columns.tolist())
    print("First 3 rows:\n", df.head(3))
except Exception as e:
    print("Failed to load data:", e)
    raise SystemExit(1)

# ── Identify necessary columns ───────────────────────────────────────────
# We need team size and disruption index.
# Try common names (case-insensitive search)
col_team = None
col_d = None
col_n_i = col_n_j = col_n_k = None  # fallback for computing D
col_year = None
col_refs = None
col_cites = None  # total forward citations

for col in df.columns:
    cl = col.lower().strip()
    if col_team is None and cl in ["team_size", "num_authors", "n_authors", "author_count", "authors"]:
        col_team = col
    if col_d is None and cl in ["disruption", "disruption_index", "d_index", "d", "disruptiveness"]:
        col_d = col
    if col_n_i is None and cl in ["n_i", "ni", "only_focal"]:
        col_n_i = col
    if col_n_j is None and cl in ["n_j", "nj", "both"]:
        col_n_j = col
    if col_n_k is None and cl in ["n_k", "nk", "only_refs"]:
        col_n_k = col
    if col_year is None and cl in ["year", "pub_year", "date"]:
        col_year = col
    if col_refs is None and cl in ["n_references", "num_refs", "ref_count"]:
        col_refs = col
    if col_cites is None and cl in ["n_citations", "num_cites", "citation_count", "cites"]:
        col_cites = col

# If disruption not directly present, compute from n_i, n_j, n_k
if col_d is None and (col_n_i is not None and col_n_j is not None and col_n_k is not None):
    print("Computing disruption index D = (n_i - n_j) / (n_i + n_j + n_k)")
    # denominator may be zero; avoid division by zero
    denom = df[col_n_i] + df[col_n_j] + df[col_n_k]
    valid_denom = denom > 0
    df.loc[valid_denom, "D_computed"] = (df.loc[valid_denom, col_n_i] - df.loc[valid_denom, col_n_j]) / denom.loc[valid_denom]
    col_d = "D_computed"
    print("Created 'D_computed' column.")
elif col_d is None:
    print("No direct disruption column and no n_i/n_j/n_k available. Cannot compute disruption index.")
    print("Please provide a column with pre‑computed disruption (e.g., 'disruption') or the raw triad counts.")
    raise SystemExit(1)

if col_team is None:
    print("No team size column found. Aborting.")
    raise SystemExit(1)

print(f"Using team size column: {col_team}")
print(f"Using disruption column: {col_d}")

# ── Data cleaning ────────────────────────────────────────────────────────
# Keep rows where team size > 0 and disruption is not null
df_clean = df.dropna(subset=[col_team, col_d]).copy()
df_clean = df_clean[df_clean[col_team] > 0]

# Also restrict to papers with at least one forward citation? 
# Disruption can be defined only for papers with at least one citing paper.
# We don't have exact citing count column, but if we have total citation count (forward), we can filter.
# If col_cites is available, keep only rows with >0 cites.
if col_cites is not None:
    df_clean = df_clean[df_clean[col_cites] > 0]

print(f"Cleaned sample size: {len(df_clean)}")

# ── Descriptive statistics ───────────────────────────────────────────────
print("\n--- Descriptive stats ---")
print(df_clean[[col_team, col_d]].describe())

# ── CORRELATION: team size vs disruption ─────────────────────────────────
# Paper hypothesises negative correlation: small teams → more disruptive.
pearson_r, pearson_p = stats.pearsonr(df_clean[col_team], df_clean[col_d])
spearman_r, spearman_p = stats.spearmanr(df_clean[col_team], df_clean[col_d])

print("\n=== CORRELATION RESULTS ===")
print(f"RESULT Pearson r = {pearson_r:.4f}, p-value = {pearson_p:.4e}")
print(f"RESULT Spearman ρ = {spearman_r:.4f}, p-value = {spearman_p:.4e}")
print("PAPER_REPORTED direction: negative correlation (small teams more disruptive)")

# ── REGRESSION MODELS (approximating the paper’s fractional logit) ─────
# The paper uses a fractional logit model with the disruption index as outcome.
# Here we implement both:
#   1) OLS as a first approximation
#   2) Fractional logit (quasi‑likelihood) after mapping D from [-1,1] to (0,1)

# Prepare independent variables
X_list = [col_team]
if col_refs is not None:
    df_clean['log_refs'] = np.log1p(df_clean[col_refs])
    X_list.append('log_refs')
if col_cites is not None:
    df_clean['log_cites'] = np.log1p(df_clean[col_cites])
    X_list.append('log_cites')
if col_year is not None:
    # include year as a continuous variable (or dummies; here continuous)
    X_list.append(col_year)

# Ensure no NaN in controls
df_reg = df_clean.dropna(subset=X_list).copy()
X = sm.add_constant(df_reg[X_list])
y = df_reg[col_d]

# ‑‑ OLS with robust standard errors ─────────────────────────────────────
ols_model = sm.OLS(y, X)
ols_results = ols_model.fit(cov_type='HC1')  # robust errors
print("\n=== OLS REGRESSION (Robust SE) ===")
print(ols_results.summary())
coef_team = ols_results.params[col_team]
pval_team = ols_results.pvalues[col_team]
print(f"RESULT OLS coefficient for team size = {coef_team:.4f} (p={pval_team:.4e})")

# ‑‑ Fractional logit (Papke–Wooldridge) ─────────────────────────────────
# Disruption D ∈ [-1, 1]; transform to (0,1) via (D+1)/2
# This is consistent with the original approach where D is a fractional outcome.
y_frac = (y + 1) / 2.0
# Use GLM with Binomial family and logit link, with robust standard errors.
# statsmodels expects binary counts; for fractional response we use the Binomial family
# and pass the transformed response directly (GLM will treat it as proportion with implicit
# weights = 1). This matches Papke–Wooldridge when using robust covariance.
glm_frac = sm.GLM(y_frac, X, family=Binomial(link=logit()))
frac_results = glm_frac.fit(cov_type='HC1')
print("\n=== FRACTIONAL LOGIT (transformed D) ===")
print(frac_results.summary())
coef_team_frac = frac_results.params[col_team]
pval_team_frac = frac_results.pvalues[col_team]
print(f"RESULT Fractional logit coefficient for team size = {coef_team_frac:.4f} (p={pval_team_frac:.4e})")

# ── Final conclusion ─────────────────────────────────────────────────────
print("\n=== CONCLUSION ===")
if coef_team < 0:
    direction_text = "negative, consistent with the paper: small teams tend to produce more disruptive works."
else:
    direction_text = "positive (opposite to the paper's claim)."
print(f"RESULT Team size effect on disruption is {direction_text}")
print("DATA_SUB note: analysis performed on 'sciscinet_sample.parquet', a sample of the original data. Exact numerical values differ from the paper’s full dataset.")
