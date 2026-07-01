import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# 1. DATA LOADING & VALIDATION
# =============================================================================
DATA_DIR = "/workspace/raw_data/"
USE_SYNTHETIC = False

# Load error calibration data
try:
    df_errors = pd.read_csv(os.path.join(DATA_DIR, "donner_data.csv"))
    print("Loaded donner_data.csv")
except Exception as e:
    print(f"Warning: Could not load donner_data.csv: {e}")
    df_errors = None
    USE_SYNTHETIC = True

# Load bibliometric sample data
try:
    df_biblio = pd.read_parquet(os.path.join(DATA_DIR, "sciscinet_sample.parquet"))
    print("Loaded sciscinet_sample.parquet")
except Exception as e:
    print(f"Warning: Could not load sciscinet_sample.parquet: {e}")
    df_biblio = None
    USE_SYNTHETIC = True

# =============================================================================
# 2. SYNTHETIC DATA FALLBACK (if raw data missing/malformed)
# =============================================================================
if USE_SYNTHETIC or df_errors is None or df_biblio is None:
    print("Falling back to SYNTHETIC data to demonstrate methodology.")
    np.random.seed(42)
    n_groups = 50
    n_pubs_per_group = np.random.poisson(100, n_groups)
    df_biblio = pd.DataFrame({
        'group_id': np.repeat(range(n_groups), n_pubs_per_group),
        'pub_id': range(sum(n_pubs_per_group)),
        'reported_citations': np.random.poisson(5, sum(n_pubs_per_group)),
        'field': np.random.choice(['Physics', 'Biology', 'Chemistry'], sum(n_pubs_per_group))
    })
    
    # Synthetic error calibration: reported vs true counts
    n_cal = 200
    df_errors = pd.DataFrame({
        'type': ['pub_count'] * 100 + ['citation_count'] * 100,
        'reported': np.random.poisson(50, 200),
        'true': np.random.poisson(50, 200) + np.random.normal(0, 3, 200)
    })
    df_errors['true'] = df_errors['true'].clip(0)
    print("SYNTHETIC data generated for demonstration.")

# =============================================================================
# 3. DATA PREPROCESSING
# =============================================================================
# Aggregate to group level: reported publications and citations
group_stats = df_biblio.groupby('group_id').agg(
    N_rep=('pub_id', 'count'),
    C_rep=('reported_citations', 'sum')
).reset_index()

# Prepare error calibration data
err_pub = df_errors[df_errors['type'] == 'pub_count'] if 'type' in df_errors.columns else df_errors.iloc[:len(df_errors)//2]
err_cit = df_errors[df_errors['type'] == 'citation_count'] if 'type' in df_errors.columns else df_errors.iloc[len(df_errors)//2:]

# =============================================================================
# 4. BAYESIAN REGRESSION MODEL FOR ERROR CORRECTION
# =============================================================================
# Model: true = beta0 + beta1 * reported + epsilon
# We use a conjugate Bayesian linear regression approximation.
# Posterior for beta ~ N(beta_hat, Sigma_beta)
# Posterior for sigma ~ Inverse-Gamma or approximated via residual std

def fit_bayesian_linear(X, Y):
    X = np.array(X).reshape(-1, 1)
    Y = np.array(Y)
    X_aug = np.column_stack([np.ones(len(X)), X])
    
    # OLS estimates
    beta_hat = np.linalg.lstsq(X_aug, Y, rcond=None)[0]
    residuals = Y - X_aug @ beta_hat
    n, p = X_aug.shape
    sigma2_hat = np.sum(residuals**2) / (n - p)
    
    # Bayesian posterior covariance (using weakly informative prior)
    prior_var = 100.0
    Sigma_beta = sigma2_hat * np.linalg.inv(X_aug.T @ X_aug + np.eye(p) / prior_var)
    
    return beta_hat, Sigma_beta, sigma2_hat

# Fit models for publication count and citation count errors
beta_pub, Sigma_pub, sigma_pub = fit_bayesian_linear(err_pub['reported'], err_pub['true'])
beta_cit, Sigma_cit, sigma_cit = fit_bayesian_linear(err_cit['reported'], err_cit['true'])

print("Bayesian error correction models fitted.")

# =============================================================================
# 5. MONTE CARLO SIMULATION & UNCERTAINTY PROPAGATION
# =============================================================================
N_MC = 10000
np.random.seed(2024)

# Pre-allocate storage for MC results
mc_indicators = np.zeros((len(group_stats), N_MC))

for i in range(N_MC):
    # Sample regression coefficients from posterior
    beta_pub_s = np.random.multivariate_normal(beta_pub, Sigma_pub)
    beta_cit_s = np.random.multivariate_normal(beta_cit, Sigma_cit)
    
    # Sample residual noise
    eps_pub = np.random.normal(0, np.sqrt(sigma_pub), len(group_stats))
    eps_cit = np.random.normal(0, np.sqrt(sigma_cit), len(group_stats))
    
    # Predict error-free (true) quantities
    N_true = beta_pub_s[0] + beta_pub_s[1] * group_stats['N_rep'].values + eps_pub
    C_true = beta_cit_s[0] + beta_cit_s[1] * group_stats['C_rep'].values + eps_cit
    
    # Ensure non-negative counts
    N_true = np.maximum(N_true, 1)  # Avoid division by zero
    C_true = np.maximum(C_true, 0)
    
    # Indicator: Average citation impact per publication
    mc_indicators[:, i] = C_true / N_true

# =============================================================================
# 6. AGGREGATE RESULTS & PRINT
# =============================================================================
# Compute summary statistics across MC draws
ind_mean = np.mean(mc_indicators, axis=1)
ind_median = np.median(mc_indicators, axis=1)
ind_lower = np.percentile(mc_indicators, 2.5, axis=1)
ind_upper = np.percentile(mc_indicators, 97.5, axis=1)
ind_mae = np.mean(np.abs(ind_mean - group_stats['C_rep'].values / group_stats['N_rep'].values))

# Global averages across research groups
global_mean = np.mean(ind_mean)
global_median = np.mean(ind_median)
global_ci_low = np.mean(ind_lower)
global_ci_high = np.mean(ind_upper)
global_mae = np.mean(ind_mae)

# Print results with exact labeling format
print("\n--- QUANTITATIVE RESULTS ---")
print(f"RESULT Global_Mean_Citation_Impact = {global_mean:.4f}")
print(f"RESULT Global_Median_Citation_Impact = {global_median:.4f}")
print(f"RESULT Global_95%_CI_Lower = {global_ci_low:.4f}")
print(f"RESULT Global_95%_CI_Upper = {global_ci_high:.4f}")
print(f"RESULT Global_Mean_Absolute_Error_vs_Reported = {global_mae:.4f}")
print(f"RESULT Uncertainty_Spread_Mean = {(global_ci_high - global_ci_low):.4f}")

# Paper-reported comparison (from abstract/context)
print("\n--- PAPER REPORTED COMPARISONS ---")
print("PAPER_REPORTED Qualitative_Finding = 'Average citation impact scores often have large margins of error due to data inaccuracies'")
print("PAPER_REPORTED Error_Categories_Used = 2 (publication count & citation count inaccuracies)")
print("PAPER_REPORTED Method = 'Bayesian regression + direct Monte Carlo simulation'")

# Data substitution label if applicable
if USE_SYNTHETIC:
    print("\nDATA_SUB Note: Results computed on SYNTHETIC/placeholder data due to missing raw files. Methodology matches paper specification.")

# =============================================================================
# 7. FINAL CONCLUSION / DIRECTION
# =============================================================================
print("\n--- FINAL CONCLUSION ---")
if (global_ci_high - global_ci_low) > 0.5 * global_mean:
    print("CONCLUSION: The propagated uncertainty from data inaccuracies is substantial. The 95% credible interval width exceeds 50% of the mean indicator value, confirming the paper's warning that average citation impact scores should be used cautiously in research evaluation.")
else:
    print("CONCLUSION: The propagated uncertainty is moderate. While data inaccuracies introduce measurable variance, the indicator remains relatively stable across Monte Carlo replicates.")
print("DIRECTION: Future work should incorporate additional error categories (e.g., field misclassification, author disambiguation errors) and apply hierarchical Bayesian models to borrow strength across research units, further refining uncertainty bounds for bibliometric evaluation.")
