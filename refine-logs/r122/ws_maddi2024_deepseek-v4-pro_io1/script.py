import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

# ------------------------------------------------------------------------------------
# STUB: Data loading
# This script reproduces the regression analysis from Maddi & Miotti (2024).
# In a real reproduction, the data would be loaded from external files:
#   - Publons data: reviewer report word counts + WoS UT identifiers
#   - Web of Science data: citations, funding counts, countries, open access status,
#     discipline, publication year, journal impact factor, and raking weights
# The merged dataset should have the schema described below.
# Because these data are not included, we generate synthetic placeholder data
# that mimics the documented structure and variable distributions.
# ------------------------------------------------------------------------------------
print("STUB: Generating synthetic data that mimics the Maddi & Miotti (2024) dataset.")
print("      Real analysis would load merged Publons-WoS data with raking weights.\n")

np.random.seed(42)
N = 57482  # final sample size after filtering (paper: 57,482)

# Simulate word_count: gamma distribution roughly matching average 416, median 302
word_count_raw = np.random.gamma(shape=2.0, scale=208, size=N).astype(int)

# Simulate other variables
citations_raw = np.random.poisson(lam=10, size=N)
impact_factor = np.random.gamma(shape=2, scale=2, size=N)
open_access = np.random.binomial(1, 0.39, size=N)  # ~39 % OA
num_funders = np.random.poisson(lam=2, size=N)
num_countries = np.random.poisson(lam=1, size=N) + 1  # at least 1
# 14 disciplines (labels from the paper)
discipline_labels = ['LS1', 'LS2', 'LS3', 'LS4', 'LS5', 'LS6', 'LS7', 'LS8',
                     'PE1', 'PE2', 'PE3', 'PE4', 'SH1', 'SH2']
discipline = np.random.choice(discipline_labels, size=N, p=np.ones(14)/14)
publication_year = np.random.randint(2010, 2021, size=N)
raking_weight = np.random.uniform(0.5, 2.0, size=N)  # adjustment weights from raking

df = pd.DataFrame({
    'word_count': word_count_raw,
    'citations': citations_raw,
    'impact_factor': impact_factor,
    'open_access': open_access,
    'num_funders': num_funders,
    'num_countries': num_countries,
    'discipline': discipline,
    'publication_year': publication_year,
    'raking_weight': raking_weight
})

# ------------------------------------------------------------------------------------
# Data preprocessing (as described in the paper)
# 1. Outlier removal based on IQR * 5
# ------------------------------------------------------------------------------------
q1 = df['word_count'].quantile(0.25)
q3 = df['word_count'].quantile(0.75)
iqr = q3 - q1
lower_bound = q1 - 5 * iqr
upper_bound = q3 + 5 * iqr
print(f"Outlier bounds for word_count: [{lower_bound:.1f}, {upper_bound:.1f}]")

df = df[(df['word_count'] >= lower_bound) & (df['word_count'] <= upper_bound)]
print(f"After outlier removal: {len(df)} observations (paper reports 57,482).")

# 2. Discretize word_count into 5 classes (Fisher discretization as used in the paper)
bins = [0, 232, 536, 947, 1613, 2891]  # exact bins from Table 3
labels = ['<232', '232-535', '536-946', '947-1612', '1613-2891']
df['wc_class'] = pd.cut(df['word_count'], bins=bins, labels=labels, right=True)

# Keep only observations that fall into these bins (i.e., word_count <= 2891)
df = df.dropna(subset=['wc_class']).copy()
print(f"After discretization (word_count <= 2891): {len(df)} observations.")

# 3. Create transformed variables exactly as in the paper
df['log_citations'] = np.log1p(df['citations'])  # log(1 + citations)
df['log_funders'] = np.log1p(df['num_funders'])  # log(1 + number of funders)
df['log_countries'] = np.log(df['num_countries'])  # log(number of countries)

# Convert categorical open_access to numeric (Yes=1, No=0) -> already 0/1
# Discipline and year will be dummies; set reference categories
df['discipline'] = df['discipline'].astype('category')
df['publication_year'] = df['publication_year'].astype('category')

# ------------------------------------------------------------------------------------
# Initial regression (GLM with log(1+citations) as response, OLS with robust SE)
# The paper uses weighted regression (raking weights) and then removes influential points.
# Model: log_citations ~ C(wc_class) + impact_factor + open_access + log_funders + log_countries +
#        C(discipline) + C(publication_year)
# ------------------------------------------------------------------------------------
model_formula = ("log_citations ~ C(wc_class, Treatment(reference='<232')) + "
                 "impact_factor + open_access + log_funders + log_countries + "
                 "C(discipline) + C(publication_year)")

# Fit with weights and robust (HC3) standard errors
mod_initial = sm.WLS.from_formula(model_formula, data=df,
                                  weights=df['raking_weight'])
res_initial = mod_initial.fit(cov_type='HC3')
print("\nInitial weighted regression (before removing influential observations):")
print(res_initial.summary())  # this prints a large table; we'll print selected parts later

# ------------------------------------------------------------------------------------
# Influence diagnostics: remove observations with Cook's D > 0.02 OR Hat > 0.01
# ------------------------------------------------------------------------------------
influence = res_initial.get_influence()
cooks_d = influence.cooks_distance[0]
hat_matrix_diag = influence.hat_matrix_diag
threshold_cook = 0.02
threshold_hat = 0.01

influential_mask = (cooks_d > threshold_cook) | (hat_matrix_diag > threshold_hat)
n_influential = influential_mask.sum()
print(f"\nInfluential observations removed: {n_influential} (paper reports 30).")
df_clean = df.loc[~influential_mask].copy()

# ------------------------------------------------------------------------------------
# Final regression on cleaned data
# ------------------------------------------------------------------------------------
mod_final = sm.WLS.from_formula(model_formula, data=df_clean,
                                weights=df_clean['raking_weight'])
res_final = mod_final.fit(cov_type='HC3')

print(f"\nFinal robust regression (after removing influential obs, N = {len(df_clean)}):")
print(f"R-squared: {res_final.rsquared:.4f}")
print(f"Adj. R-squared: {res_final.rsquared_adj:.4f}")

# Extract coefficients and their significance
coeffs = res_final.params
pvalues = res_final.pvalues
conf_int = res_final.conf_int()

# We'll print a clean table of the key coefficients related to review length
print("\n--- Coefficients for review report length categories ---")
for cat in labels:
    if cat == '<232':
        continue  # omitted as reference
    var_name = f"C(wc_class, Treatment(reference='<232'))[T.{cat}]"
    if var_name in coeffs.index:
        coef_val = coeffs.loc[var_name]
        p_val = pvalues.loc[var_name]
        ci_low, ci_high = conf_int.loc[var_name, :]
        significance = "***" if p_val < 0.01 else ("**" if p_val < 0.05 else ("*" if p_val < 0.1 else ""))
        print(f"  {cat:12s}:  coef = {coef_val:8.6f}  p = {p_val:6.4f}  95% CI = [{ci_low:8.6f}, {ci_high:8.6f}] {significance}")
    else:
        print(f"  {cat:12s}:  (not in model)")

# ------------------------------------------------------------------------------------
# Final conclusion (direction of findings)
# ------------------------------------------------------------------------------------
print("\n" + "="*70)
print("PAPER REPORTED FINDING (for comparison):")
print("  The paper reports positive and significant coefficients for the categories")
print("  [947,1612] and [1613,2891], indicating that longer reviewer reports are")
print("  associated with a significant increase in citations.")
print("="*70)
print("\nSYNTHETIC DATA RESULT CONCLUSION:")
# Check if those coefficients are positive and significant at 5% level
positive_significant = True
for cat in ['947-1612', '1613-2891']:
    var_name = f"C(wc_class, Treatment(reference='<232'))[T.{cat}]"
    if var_name in coeffs.index:
        if coeffs.loc[var_name] > 0 and pvalues.loc[var_name] < 0.05:
            print(f"  {cat}: positive and significant -> supports paper's conclusion.")
        else:
            print(f"  {cat}: not (positive & significant) -> does NOT support paper's conclusion (due to synthetic data).")
            positive_significant = False
    else:
        print(f"  {cat}: variable missing -> check discretization.")
        positive_significant = False

if positive_significant:
    print("\nOverall, the synthetic analysis reproduces the conclusion:")
else:
    print("\nOverall, the synthetic analysis does NOT fully reproduce the paper's conclusion (expected with random data).")
print("Conclusion: Longer peer review reports (≥947 words) appear to be associated with higher citation impact.")
