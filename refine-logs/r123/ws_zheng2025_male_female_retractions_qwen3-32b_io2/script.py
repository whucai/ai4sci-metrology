import pandas as pd
import numpy as np
import os
from scipy import stats

# ==============================================================================
# 1. DATA LOADING & SYNTHETIC DATA GENERATION
# ==============================================================================
# The paper does not provide raw data files. We attempt to load from the 
# specified directory. If unavailable, we construct a SYNTHETIC dataset that 
# exactly matches the aggregated counts reported in Table 1 of the paper.
# ==============================================================================

RAW_DATA_DIR = "/workspace/raw_data/"
DATA_FILE = os.path.join(RAW_DATA_DIR, "zheng2025_retraction_data.csv")

try:
    df = pd.read_csv(DATA_FILE)
    print("Loaded raw data from:", DATA_FILE)
except FileNotFoundError:
    print("WARNING: No raw data file found at", DATA_FILE)
    print("Generating SYNTHETIC dataset matching Table 1 counts for reproduction...")
    
    # SYNTHETIC DATA: Aggregated counts from Table 1 (Zheng et al., 2025)
    # These counts are used to exactly reproduce the reported indicators.
    synthetic_data = {
        "article_type": ["Retracted", "Retracted", "Non-retracted", "Non-retracted"],
        "gender": ["Male", "Female", "Male", "Female"],
        "count": [8088, 3534, 12669453, 6805984]
    }
    df = pd.DataFrame(synthetic_data)
    print("SYNTHETIC dataset created. Results will be labeled as DATA_SUB.")

# ==============================================================================
# 2. INDICATOR & MODEL SPECIFICATIONS
# ==============================================================================

def calculate_rr(count_retracted, count_all):
    """Retraction Rate (RR) per 10,000 articles (‱)."""
    return (count_retracted / count_all) * 10000

def wilson_ci(count_success, count_total, confidence=0.95):
    """Wilson Score Confidence Interval for a proportion."""
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    n = count_total
    p = count_success / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return (center - margin) * 10000, (center + margin) * 10000

def mfrr_ci(ret_m, total_m, ret_f, total_f, confidence=0.95):
    """
    Confidence Interval for Male/Female Retraction Ratio (MFRR).
    Uses the log-transform method (Katz et al., 1978 approximation for large samples).
    Var(ln(RR_m/RR_f)) ≈ 1/ret_m - 1/total_m + 1/ret_f - 1/total_f
    """
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    var_log = (1/ret_m - 1/total_m) + (1/ret_f - 1/total_f)
    se_log = np.sqrt(var_log)
    rr_m = ret_m / total_m
    rr_f = ret_f / total_f
    mfrr = rr_m / rr_f
    log_mfrr = np.log(mfrr)
    ci_lower = np.exp(log_mfrr - z * se_log)
    ci_upper = np.exp(log_mfrr + z * se_log)
    return mfrr, ci_lower, ci_upper

# ==============================================================================
# 3. COMPUTATIONS
# ==============================================================================

# Extract counts for Male and Female
row_m_ret = df[(df["gender"] == "Male") & (df["article_type"] == "Retracted")]["count"].values[0]
row_f_ret = df[(df["gender"] == "Female") & (df["article_type"] == "Retracted")]["count"].values[0]
row_m_nonret = df[(df["gender"] == "Male") & (df["article_type"] == "Non-retracted")]["count"].values[0]
row_f_nonret = df[(df["gender"] == "Female") & (df["article_type"] == "Non-retracted")]["count"].values[0]

total_m = row_m_ret + row_m_nonret
total_f = row_f_ret + row_f_nonret

# Calculate Indicators
rr_m = calculate_rr(row_m_ret, total_m)
rr_f = calculate_rr(row_f_ret, total_f)
mfrr, mfrr_ci_low, mfrr_ci_high = mfrr_ci(row_m_ret, total_m, row_f_ret, total_f)

# Confidence Intervals for RR
rr_m_ci_low, rr_m_ci_high = wilson_ci(row_m_ret, total_m)
rr_f_ci_low, rr_f_ci_high = wilson_ci(row_f_ret, total_f)

# ==============================================================================
# 4. OUTPUT RESULTS
# ==============================================================================

print("\n--- PAPER REPORTED VALUES (Zheng et al., 2025) ---")
print("RESULT PAPER_REPORTED_RR_MALE = 6.38")
print("RESULT PAPER_REPORTED_RR_FEMALE = 5.19")
print("RESULT PAPER_REPORTED_MFRR = 1.23")
print("RESULT PAPER_REPORTED_MFRR_95CI = (1.18, 1.28)")

print("\n--- COMPUTED RESULTS (SYNTHETIC DATA SUBSTITUTION) ---")
print(f"RESULT DATA_SUB_RR_MALE = {rr_m:.2f}")
print(f"RESULT DATA_SUB_RR_FEMALE = {rr_f:.2f}")
print(f"RESULT DATA_SUB_MFRR = {mfrr:.2f}")
print(f"RESULT DATA_SUB_MFRR_95CI = ({mfrr_ci_low:.2f}, {mfrr_ci_high:.2f})")
print(f"RESULT DATA_SUB_RR_MALE_95CI = ({rr_m_ci_low:.2f}, {rr_m_ci_high:.2f})")
print(f"RESULT DATA_SUB_RR_FEMALE_95CI = ({rr_f_ci_low:.2f}, {rr_f_ci_high:.2f})")

# ==============================================================================
# 5. CONCLUSION
# ==============================================================================
print("\n--- FINAL CONCLUSION ---")
if mfrr > 1.0 and mfrr_ci_low > 1.0:
    print("CONCLUSION: Male leading authors have a significantly higher retraction rate than female leading authors. The computed MFRR exceeds 1 with a confidence interval strictly above 1, confirming the paper's primary finding.")
elif mfrr < 1.0 and mfrr_ci_high < 1.0:
    print("CONCLUSION: Female leading authors have a significantly higher retraction rate than male leading authors.")
else:
    print("CONCLUSION: No statistically significant gender disparity in retraction rates was detected.")
    
print("DIRECTION: Future analyses should incorporate individual-level covariates (e.g., academic rank, institutional policies) and improve gender inference for ambiguous names (e.g., Chinese transliterations) to refine these findings.")
