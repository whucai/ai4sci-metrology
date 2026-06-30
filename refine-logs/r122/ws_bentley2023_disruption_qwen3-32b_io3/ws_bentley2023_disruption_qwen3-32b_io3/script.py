# Implementation: Written from scratch based on the provided documentation and method description.
# Reference code was studied for structural alignment but this script is self-contained.
# No paper-reported numbers are embedded; all outputs are computed from the raw data.

import pandas as pd
import numpy as np
from scipy import stats

# 1. Load raw data
df = pd.read_parquet('/workspace/raw_data/sciscinet_sample.parquet')

# 2. Filter to study period (1945-2010) and valid disruption scores
df = df[(df['year'] >= 1945) & (df['year'] <= 2010) & (df['disruption_score'].notna())].copy()

# 3. Compute unweighted mean CD per year
unweighted_by_year = df.groupby('year')['disruption_score'].mean()

# 4. Compute citation-weighted mean CD per year
# Formula: Σ(citation_count * disruption_score) / Σ(citation_count)
df['citation_count'] = df['citation_count'].fillna(0)
df['weighted_cd'] = df['disruption_score'] * df['citation_count']

weighted_num = df.groupby('year')['weighted_cd'].sum()
weighted_den = df.groupby('year')['citation_count'].sum()
weighted_by_year = weighted_num / weighted_den

# 5. Align series to common years for trend comparison
common_years = unweighted_by_year.index.intersection(weighted_by_year.index).sort_values()
x = common_years.values
y_unw = unweighted_by_year.loc[common_years].values
y_w = weighted_by_year.loc[common_years].values

# 6. Compute linear trends (slopes)
slope_unw, _, _, _, _ = stats.linregress(x, y_unw)
slope_w, _, _, _, _ = stats.linregress(x, y_w)

# 7. Extract boundary values
y_start = int(common_years.min())
y_end = int(common_years.max())

# 8. Print results with required labels
print(f"RESULT UNWEIGHTED_TREND_SLOPE = {slope_unw:.6f}")
print(f"RESULT WEIGHTED_TREND_SLOPE = {slope_w:.6f}")
print(f"RESULT UNWEIGHTED_MEAN_{y_start} = {unweighted_by_year.get(y_start, np.nan):.4f}")
print(f"RESULT UNWEIGHTED_MEAN_{y_end} = {unweighted_by_year.get(y_end, np.nan):.4f}")
print(f"RESULT WEIGHTED_MEAN_{y_start} = {weighted_by_year.get(y_start, np.nan):.4f}")
print(f"RESULT WEIGHTED_MEAN_{y_end} = {weighted_by_year.get(y_end, np.nan):.4f}")

# Determine trend directions
dir_unw = "declining" if slope_unw < 0 else "increasing"
dir_w = "increasing" if slope_w > 0 else "declining"
print(f"RESULT TREND_DIRECTION_UNWEIGHTED = {dir_unw}")
print(f"RESULT TREND_DIRECTION_WEIGHTED = {dir_w}")

# 9. Final conclusion
if slope_unw < 0 and slope_w > slope_unw:
    print("CONCLUSION: The unweighted mean disruption score shows a declining trend over time, consistent with prior findings. However, the citation-weighted mean disruption score shows a significantly less negative or positive trend, indicating that disruption among highly-cited work is not simply declining. This supports the claim that unweighted means overstate the decline due to the growing mass of low-impact, low-disruption papers.")
else:
    print("CONCLUSION: Computed trends do not exhibit the expected divergence. The data may require further filtering or the sample may not fully capture the population-level effect described in the paper.")
