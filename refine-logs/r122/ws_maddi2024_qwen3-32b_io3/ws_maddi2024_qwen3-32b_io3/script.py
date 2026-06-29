import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# =============================================================================
# 1. DATA AVAILABILITY CHECK
# =============================================================================
raw_data_dir = "/workspace/raw_data/"
original_code_dir = "/workspace/original_code/"

has_raw_data = os.path.exists(raw_data_dir) and len(os.listdir(raw_data_dir)) > 0
has_ref_code = os.path.exists(original_code_dir) and len(os.listdir(original_code_dir)) > 0

print(f"DATA_STATUS raw_data_available = {has_raw_data}")
print(f"DATA_STATUS reference_code_available = {has_ref_code}")

# =============================================================================
# 2. PAPER-REPORTED VALUES (Explicitly labeled, not computed)
# =============================================================================
print("PAPER_REPORTED N_final = 57482")
print("PAPER_REPORTED threshold_significant_words = 947")
print("PAPER_REPORTED avg_report_words = 416.3")
print("PAPER_REPORTED median_report_words = 302")
print("PAPER_REPORTED excluded_iqr_outliers = 212")
print("PAPER_REPORTED excluded_influential_obs = 30")
print("PAPER_REPORTED oa_rate_publons = 0.391")
print("PAPER_REPORTED oa_rate_wos = 0.287")
print("PAPER_REPORTED funding_rate_publons = 0.737")
print("PAPER_REPORTED funding_rate_wos = 0.539")
print("PAPER_REPORTED discretization_bins = [0, 232, 535, 946, 1612, 2891]")
print("PAPER_REPORTED estimator = GLM/OLS on log(1+citations) with HC3 robust SE")

# =============================================================================
# 3. METHODOLOGICAL PIPELINE (Synthetic Stub due to missing raw data)
# =============================================================================
if not has_raw_data:
    print("\nDATA UNAVAILABLE: Raw data files not found. Constructing documented synthetic stub to demonstrate the methodological pipeline.")
    print("NOTE: All numerical outputs below are labeled SYNTHETIC. Exact reproduction is data-blocked.")
    
    # 3.1 Generate synthetic dataset matching paper description
    np.random.seed(2024)
    N = 57482
    df = pd.DataFrame({
        'citations': np.random.poisson(8, N),
        'report_length': np.random.lognormal(mean=5.8, sigma=1.1, size=N),
        'year': np.random.choice(range(2009, 2021), N),
        'oa': np.random.choice([0, 1], N, p=[0.6, 0.4]),
        'funders': np.random.poisson(1.2, N),
        'countries': np.random.choice([1, 2, 3, 4, 5], N, p=[0.5, 0.2, 0.15, 0.1, 0.05]),
        'discipline': np.random.choice(range(14), N),
        'impact_factor': np.random.lognormal(mean=0.5, sigma=0.8, size=N)
    })
    
    # 3.2 Preprocessing: IQR filter (factor 5) as per paper
    Q1, Q3 = df['report_length'].quantile(0.25), df['report_length'].quantile(0.75)
    iqr_threshold = Q3 + 5 * (Q3 - Q1)
    df = df[df['report_length'] <= iqr_threshold].copy()
    
    # 3.3 Discretization (Fisher method approximated by paper's Table 3 bins)
    bins = [0, 232, 535, 946, 1612, 2891]
    labels = ['<232', '232-535', '536-946', '947-1612', '1613-2891']
    df['report_class'] = pd.cut(df['report_length'], bins=bins, labels=labels, right=True)
    df['report_class'] = df['report_class'].astype('category')
    
    # 3.4 DV transformation: log(1 + citations) per Thelwall & Wilson (2014)
    df['log_citations'] = np.log1p(df['citations'])
    
    # 3.5 Prepare design matrix (controls + discretized IV)
    X = pd.get_dummies(df[['year', 'oa', 'funders', 'countries', 'discipline', 'impact_factor', 'report_class']], drop_first=True)
    X = sm.add_constant(X)
    y = df['log_citations']
    
    # 3.6 Influence diagnostics (Cook's D < 0.02, Hat < 0.01)
    model_init = sm.OLS(y, X).fit()
    inf = model_init.get_influence()
    cook_d = inf.cooks_distance[0]
    hat_vals = inf.hat_matrix_diag
    mask = (cook_d < 0.02) & (hat_vals < 0.01)
    X_clean = X[mask]
    y_clean = y[mask]
    
    # 3.7 Robust regression (OLS with HC3 robust standard errors)
    model_robust = sm.OLS(y_clean, X_clean).fit(cov_type='HC3')
    
    # 3.8 Extract key results
    r2 = model_robust.rsquared
    report_params = {k: v for k, v in model_robust.params.items() if 'report_class' in k}
    report_pvals = {k: v for k, v in model_robust.pvalues.items() if 'report_class' in k}
    
    # VIF calculation
    try:
        vifs = [variance_inflation_factor(X_clean.values, i) for i in range(X_clean.shape[1])]
        max_vif = max(vifs)
    except Exception:
        max_vif = np.nan
        
    # =============================================================================
    # 4. PRINT SYNTHETIC RESULTS
    # =============================================================================
    print("SYNTHETIC RESULT N_processed =", len(y_clean))
    print("SYNTHETIC RESULT R_squared =", round(r2, 4))
    print("SYNTHETIC RESULT max_VIF =", round(max_vif, 2))
    print("SYNTHETIC RESULT heteroscedasticity_handled = True (HC3 robust SE)")
    
    for cls, coef in report_params.items():
        pval = report_pvals[cls]
        sig = " (sig)" if pval < 0.05 else ""
        print(f"SYNTHETIC RESULT coef_{cls} = {coef:.4f} p={pval:.4f}{sig}")
        
else:
    print("Raw data found. Processing pipeline would execute here.")
    # Actual data loading and processing would replace the synthetic stub above.

# =============================================================================
# 5. FINAL CONCLUSION
# =============================================================================
print("\nFINAL CONCLUSION: The paper establishes that reviewer reports >=947 words are significantly associated with higher citation counts, supporting the hypothesis that longer, more detailed reviews improve publication quality and visibility. This script replicates the methodological pipeline (IQR filtering, Fisher discretization, influence diagnostics, robust GLM/OLS) but uses synthetic data due to missing raw materials. Exact numerical reproduction is data-blocked.")
