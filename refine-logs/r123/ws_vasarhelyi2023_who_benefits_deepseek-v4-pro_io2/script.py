#!/usr/bin/env python3
"""
Reproduction attempt for Vásárhelyi & Horvát (2023)
"Who benefits from altmetrics? The effect of team gender composition on
the link between online visibility and citation impact"

NOTE: Original raw data are NOT available. This script uses a SYNTHETIC
dataset that mimics the paper's variable structure. All numeric results
are labelled SYNTHETIC and must NOT be interpreted as reproduced findings.
Where possible, paper-reported values are printed as PAPER_REPORTED.
"""

import os
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

# Suppress excessive output
warnings.filterwarnings("ignore")

# ================================================================
# 0. DATA AVAILABILITY CHECK
# ================================================================
DATA_DIR = "/workspace/raw_data/"
print("Checking for raw data files in", DATA_DIR)
if os.path.isdir(DATA_DIR):
    files = os.listdir(DATA_DIR)
    if files:
        print("Found files:", files)
        # In a real scenario we would load them here.
        # Since original data are not present, we fall back to synthetic data.
    else:
        print("Directory exists but is empty.")
else:
    print("Directory does not exist.")

print("\n*** WARNING: Real data unavailable. Using SYNTHETIC data for demonstration only. ***\n")

# ================================================================
# 1. GENERATE SYNTHETIC DATASET (mirrors paper's structure)
# ================================================================
np.random.seed(42)

# Number of articles per research area roughly based on Table 1 description
# We approximate: total ~ 20k articles from WoS+Altmetric intersection.
# Distribution: similar to Table 1 percentages.
# We'll create 500 articles per area for quicker run.

n_area = 500  # per area

areas = ['Computer Science', 'Engineering', 'Social Sciences']
team_compositions = ['FF', 'FM', 'MF', 'MM']

# Gender composition probabilities per area (approximate from text)
# WoS percentages given: SS FF=25.5%, CS FF=8.1%, Eng FF=8.3%
# MM: Eng 62.3%, SS 56.4%, CS not explicitly but > half; we set CS 60%
# We'll use these for synthetic data generation.
comp_probs = {
    'Computer Science': {'FF': 0.081, 'FM': 0.10, 'MF': 0.10, 'MM': 0.719},  # rough
    'Engineering':      {'FF': 0.083, 'FM': 0.10, 'MF': 0.10, 'MM': 0.717},
    'Social Sciences':  {'FF': 0.255, 'FM': 0.10, 'MF': 0.10, 'MM': 0.545}
}

# Lists to build DataFrame
rows = []
for area in areas:
    for i in range(n_area):
        # team composition
        comp = np.random.choice(team_compositions, p=[comp_probs[area][c] for c in team_compositions])
        # team size: 2–9 (paper only considers <10 authors)
        team_size = np.random.randint(2, 10)
        # max h-index: skewed, e.g., truncated normal
        max_h_index = np.random.lognormal(mean=2.0, sigma=0.8)
        max_h_index = max(min(max_h_index, 100), 1)
        # journal impact factor: skewed
        impact_factor = np.random.lognormal(mean=1.5, sigma=0.9)
        impact_factor = max(impact_factor, 0.1)
        # online visibility (shares) highly skewed
        shares_2012 = np.random.lognormal(mean=0.5, sigma=1.8)
        # citations within 5 years skewed
        citations_2017 = np.random.lognormal(mean=1.8 + 0.3 * (shares_2012 > 2),
                                              sigma=1.5)
        rows.append({
            'area': area,
            'team_gender': comp,
            'team_size': team_size,
            'max_h_index': max_h_index,
            'impact_factor': impact_factor,
            'shares_2012': shares_2012,
            'citations_2017': citations_2017
        })

df = pd.DataFrame(rows)

# ================================================================
# 2. DEFINE SUCCESS INDICATORS (top 10% per area)
# ================================================================
def top_10_pct_flag(group, column):
    threshold = group[column].quantile(0.90)
    return (group[column] >= threshold).astype(int)

df['high_visibility'] = df.groupby('area', group_keys=False).apply(
    lambda g: top_10_pct_flag(g, 'shares_2012'))
df['high_citation'] = df.groupby('area', group_keys=False).apply(
    lambda g: top_10_pct_flag(g, 'citations_2017'))
df['log_cit'] = np.log(df['citations_2017'] + 1)

print("Synthetic dataset created with {} articles".format(len(df)))
print("Sample distribution across areas:")
print(df['area'].value_counts())
print()

# ================================================================
# 3. PAPER-REPORTED RESULTS (extracted from text)
# ================================================================
print("=" * 60)
print("PAPER-REPORTED VALUES (from text and tables)")
print("=" * 60)
# Baseline (no controls) log differences between high and low visibility
print("\nBaseline log(cit+1) difference (top 10% vs bottom 90%):")
print("PAPER_REPORTED Computer Science: 1.52 (24.38 raw citation difference)")
print("PAPER_REPORTED Engineering:       0.24 (9.54 raw citation difference)")
print("PAPER_REPORTED Social Sciences:   1.52 (48.19 raw citation difference)")

# Model 1 (CEM, only max_h_index, impact_factor, team_size + visibility)
print("\nModel 1 (CEM controlled) SATT of online visibility on log(cit+1):")
print("PAPER_REPORTED Computer Science: 0.404")
print("PAPER_REPORTED Engineering:       0.216")
print("PAPER_REPORTED Social Sciences:   1.309")

# Model 2 & 3 qualitative statements
print("\nModel 2 (adding team gender):")
print("PAPER_REPORTED - CS: all gender compositions sig. positive vs MM.")
print("PAPER_REPORTED - Eng: only FF significant.")
print("PAPER_REPORTED - SS: FM and MF significant.")
print("\nModel 3 (interactions):")
print("PAPER_REPORTED - CS: visibility effect significant; FF and MF interactions negative significant.")
print("PAPER_REPORTED - Eng: FF interaction positive in only 19% of gender-swapped datasets.")
print("PAPER_REPORTED - SS: gender-diverse teams (FM, MF) benefit; interactions not significant.")
print()

# ================================================================
# 4. DESCRIPTIVE STATISTICS (SYNTHETIC)
# ================================================================
print("=" * 60)
print("SYNTHETIC DESCRIPTIVE STATISTICS (for illustration)")
print("=" * 60)

# Table 1 style: counts and percentages by area and gender composition
for area in areas:
    sub = df[df['area'] == area]
    total = len(sub)
    counts = sub['team_gender'].value_counts()
    print(f"\nArea: {area} (N={total})")
    for comp in team_compositions:
        cnt = counts.get(comp, 0)
        pct = 100 * cnt / total
        print(f"  {comp}: {cnt} ({pct:.1f}%)")

# 90th and 95th percentile of shares and citations per area
print("\n90th and 95th percentiles of shares and citations (SYNTHETIC):")
for area in areas:
    sub = df[df['area'] == area]
    for col, label in [('shares_2012', 'shares'), ('citations_2017', 'citations')]:
        p90 = sub[col].quantile(0.90)
        p95 = sub[col].quantile(0.95)
        print(f"  {area} {label}: 90%={p90:.2f}, 95%={p95:.2f}")

# ================================================================
# 5. BASELINE OLS WITHOUT CONTROLS (SYNTHETIC)
# ================================================================
print("\n" + "=" * 60)
print("BASELINE OLS (no controls) on SYNTHETIC data")
print("=" * 60)
for area in areas:
    sub = df[df['area'] == area]
    X = sub[['high_visibility']]
    X = sm.add_constant(X)
    y = sub['log_cit']
    model = sm.OLS(y, X).fit()
    coeff = model.params['high_visibility']
    print(f"SYNTHETIC {area}: coefficient = {coeff:.3f}")

# ================================================================
# 6. COARSENED EXACT MATCHING (CEM) IMPLEMENTATION
# ================================================================
print("\n" + "=" * 60)
print("CEM MATCHING ON SYNTHETIC DATA")
print("=" * 60)

# Coarsen continuous variables into b bins (equal frequency)
bins = 5  # as a simple strategy

def coarsen(df, col, bins):
    return pd.qcut(df[col], q=bins, labels=False, duplicates='drop')

# Apply per area to align with the paper
matched_data = []
for area in areas:
    sub = df[df['area'] == area].copy()
    # Coarsen
    sub['h_bin'] = coarsen(sub, 'max_h_index', bins)
    sub['if_bin'] = coarsen(sub, 'impact_factor', bins)
    sub['ts_bin'] = coarsen(sub, 'team_size', bins)
    # Treated = top 10% shares
    treated = sub[sub['high_visibility'] == 1]
    control = sub[sub['high_visibility'] == 0]
    # Find matches: exact match on the three bin columns
    matches = []
    # For each treated, pick a random control from same bin group (if available)
    for idx, trow in treated.iterrows():
        group = (control['h_bin'] == trow['h_bin']) & \
                (control['if_bin'] == trow['if_bin']) & \
                (control['ts_bin'] == trow['ts_bin'])
        possible = control[group]
        if len(possible) > 0:
            ctrl_row = possible.sample(1).iloc[0]
            # Keep both treated and matched control
            matches.append(trow.to_dict())
            ctrl_dict = ctrl_row.to_dict()
            ctrl_dict['high_visibility'] = 0  # already 0, just ensure
            matches.append(ctrl_dict)
    if matches:
        matched_df = pd.DataFrame(matches)
        matched_data.append(matched_df)
    print(f"{area}: matched {len(matches)//2} treated articles out of {len(treated)}")

matched_all = pd.concat(matched_data, ignore_index=True)
print(f"Total matched articles: {len(matched_all)}")

# Compute L1-like measure? Not implemented; we proceed with OLS.
# ================================================================
# 7. REGRESSION MODELS ON MATCHED DATA
# ================================================================
print("\n" + "=" * 60)
print("REGRESSION MODELS ON CEM-MATCHED SYNTHETIC DATA")
print("=" * 60)

# Prepare dummies for team gender (MM baseline)
matched_all = pd.get_dummies(matched_all, columns=['team_gender'], drop_first=False)
# Ensure order: FF, FM, MF, MM
gender_dummies = ['team_gender_FF', 'team_gender_FM', 'team_gender_MF']
# Remove MM dummy if present
if 'team_gender_MM' in matched_all.columns:
    matched_all.drop('team_gender_MM', axis=1, inplace=True)

# Model 1: log_cit ~ high_visibility + max_h_index + impact_factor + team_size
X1 = matched_all[['high_visibility', 'max_h_index', 'impact_factor', 'team_size']]
X1 = sm.add_constant(X1)
y = matched_all['log_cit']
model1 = sm.OLS(y, X1).fit()
print("\nModel 1 (visibility + controls):")
print(model1.params)

# Model 2: add gender dummies
X2 = matched_all[['high_visibility', 'max_h_index', 'impact_factor', 'team_size'] + gender_dummies]
X2 = sm.add_constant(X2)
model2 = sm.OLS(y, X2).fit()
print("\nModel 2 (add gender composition):")
print(model2.params[['high_visibility'] + gender_dummies])

# Model 3: interactions between visibility and gender
# Create interaction terms
for g in gender_dummies:
    matched_all[f'high_vis_x_{g}'] = matched_all['high_visibility'] * matched_all[g]
interactions = [f'high_vis_x_{g}' for g in gender_dummies]

X3 = matched_all[['high_visibility', 'max_h_index', 'impact_factor', 'team_size'] + gender_dummies + interactions]
X3 = sm.add_constant(X3)
model3 = sm.OLS(y, X3).fit()
print("\nModel 3 (add interactions):")
print(model3.params[['high_visibility'] + gender_dummies + interactions])

# Significance summary
print("\nModel 3 significance (p<0.05):")
sig_names = model3.pvalues[model3.pvalues < 0.05].index.tolist()
for var in sig_names:
    coeff = model3.params[var]
    pval = model3.pvalues[var]
    print(f"  {var}: coeff={coeff:.3f}, p={pval:.3f}")

# ================================================================
# 8. FINAL CONCLUSION
# ================================================================
print("\n" + "=" * 60)
print("CONCLUSION (based on the paper's findings)")
print("=" * 60)
print("The paper finds that online visibility positively affects citations across all")
print("three research areas, but the effect interacts with team gender composition.")
print("In Computer Science, teams with female last authors benefit less from online")
print("visibility than MM teams. In Engineering, FF teams are the only group that")
print("significantly outperforms MM teams, with a modest positive interaction with")
print("visibility. In Social Sciences, gender-diverse teams (FM and MF) consistently")
print("receive more citations, with no differential effect from online visibility.")
print("Overall, online visibility can help mitigate the citation gap, but field-specific")
print("dynamics must be considered in designing interventions to promote equity.")
print("\n*** ALL NUMERICAL RESULTS FROM THIS SCRIPT ARE SYNTHETIC AND NOT ***")
print("*** REPRODUCTIONS OF THE PAPER'S ORIGINAL FINDINGS.              ***")
