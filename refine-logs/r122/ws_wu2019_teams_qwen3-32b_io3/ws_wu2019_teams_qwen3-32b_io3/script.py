# Reference code usage: Wrote own script. Studied /workspace/original_code/reproduce_wu2019.py for structure but implemented independently to ensure clarity and direct mapping to paper metrics.

import pandas as pd
import numpy as np

# Load raw data
df = pd.read_parquet('/workspace/raw_data/sciscinet_sample.parquet')

# Clean data: keep only rows with valid disruption scores and positive team sizes
df = df.dropna(subset=['disruption_score', 'author_count'])
df = df[df['author_count'] > 0]

# Compute disruption percentile (0-100) as used in the paper's figures
df['disruption_percentile'] = df['disruption_score'].rank(pct=True) * 100

# Define team size groups per paper conventions
solo = df[df['author_count'] == 1]
small = df[df['author_count'] <= 3]
large = df[df['author_count'] >= 10]
ten_person = df[df['author_count'] == 10]

# 1. Mean disruption scores and percentiles
mean_dis_solo = solo['disruption_score'].mean()
mean_dis_small = small['disruption_score'].mean()
mean_dis_large = large['disruption_score'].mean()
mean_pct_small = small['disruption_percentile'].mean()
mean_pct_large = large['disruption_percentile'].mean()

# 2. Correlation between team size and disruption
corr = df['author_count'].corr(df['disruption_score'])

# 3. Linear regression slope: disruption percentile ~ team size
# slope = cov(x,y) / var(x)
slope = np.cov(df['author_count'], df['disruption_percentile'])[0, 1] / np.var(df['author_count'])

# 4. Top 5% disruption analysis
top5_thresh = df['disruption_score'].quantile(0.95)
p_top5_solo = (solo['disruption_score'] >= top5_thresh).mean()
p_top5_ten = (ten_person['disruption_score'] >= top5_thresh).mean()
ratio_top5 = p_top5_solo / p_top5_ten if p_top5_ten > 0 else np.nan

# Print computed results
print("RESULT mean_disruption_solo = {:.4f}".format(mean_dis_solo))
print("RESULT mean_disruption_small = {:.4f}".format(mean_dis_small))
print("RESULT mean_disruption_large = {:.4f}".format(mean_dis_large))
print("RESULT mean_disruption_pct_small = {:.2f}".format(mean_pct_small))
print("RESULT mean_disruption_pct_large = {:.2f}".format(mean_pct_large))
print("RESULT correlation_team_size_disruption = {:.4f}".format(corr))
print("RESULT regression_slope_team_size = {:.6f}".format(slope))
print("RESULT prop_top5_disruption_solo = {:.4f}".format(p_top5_solo))
print("RESULT prop_top5_disruption_ten_person = {:.4f}".format(p_top5_ten))
print("RESULT ratio_top5_solo_over_ten = {:.4f}".format(ratio_top5))

# Paper-reported values for comparison (not computed from sample)
print("PAPER_REPORTED solo_72pct_more_likely_top5_disruptive = True")
print("PAPER_REPORTED disruption_declines_monotonically_with_team_size = True")
print("PAPER_REPORTED nobel_mean_disruption = 0.10")
print("PAPER_REPORTED funded_mean_disruption = -0.0024")

# Final conclusion/direction
if mean_dis_small > mean_dis_large and slope < 0:
    print("CONCLUSION: Direction confirmed. Smaller teams produce more disruptive work, while larger teams produce more developmental work. The negative relationship between team size and disruption holds in the sample, consistent with the paper's main finding.")
else:
    print("CONCLUSION: Direction not confirmed in this sample.")
