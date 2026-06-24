import numpy as np
import pandas as pd
from src.sciscigpt_local.sciscinet_connector import load_papers_sample

# ----------------------------------------------------------------------
# 1. Load data
# ----------------------------------------------------------------------
df = load_papers_sample(n_shards=10)

# ----------------------------------------------------------------------
# 2. Apply filters
# ----------------------------------------------------------------------
mask = (
    (df['year'] >= 1945) & (df['year'] <= 2010) &
    df['disruption_score'].notna() &
    df['citation_count'].notna() & (df['citation_count'] > 0)
)
filtered = df[mask].copy()

total_loaded = len(df)
after_filter = len(filtered)
year_min = filtered['year'].min()
year_max = filtered['year'].max()

print("\n=== DATA_LOAD ===")
print(f"Total loaded: {total_loaded}")
print(f"After filters: {after_filter}")
print(f"Year range: {year_min} - {year_max}")

# ----------------------------------------------------------------------
# 3. Group by year and compute unweighted + weighted averages
# ----------------------------------------------------------------------
# unweighted mean CD per year
grouped = filtered.groupby('year').agg(
    N=('disruption_score', 'count'),
    total_cites=('citation_count', 'sum'),
    uw_mean=('disruption_score', 'mean')
).reset_index()

# weighted mean CD per year: sum(citation_count * disruption_score) / sum(citation_count)
w_mean_series = filtered.groupby('year').apply(
    lambda g: (g['disruption_score'] * g['citation_count']).sum() / g['citation_count'].sum()
).reset_index(name='w_mean')
grouped = grouped.merge(w_mean_series, on='year')

# ----------------------------------------------------------------------
# 4. Compute overall / post-1970 / change 2000-2010 stats
# ----------------------------------------------------------------------
# overall unweighted mean
overall_uw = filtered['disruption_score'].mean()

# overall weighted mean
overall_w = (filtered['disruption_score'] * filtered['citation_count']).sum() / filtered['citation_count'].sum()

# post-1970 weighted mean
post1970 = filtered[filtered['year'] >= 1970]
post1970_w = (post1970['disruption_score'] * post1970['citation_count']).sum() / post1970['citation_count'].sum()

# weighted CD for years 2000 and 2010
w_2000 = grouped.loc[grouped['year'] == 2000, 'w_mean'].values[0]
w_2010 = grouped.loc[grouped['year'] == 2010, 'w_mean'].values[0]
change_2000_2010 = w_2010 - w_2000

print("\n=== DESCRIPTIVE ===")
print(f"Overall unweighted mean CD: {overall_uw:.6f}")
print(f"Overall weighted mean CD:   {overall_w:.6f}")
print(f"Post-1970 weighted mean CD:  {post1970_w:.6f}")
print(f"Change 2000-2010 (weighted): {change_2000_2010:.6f}")

# ----------------------------------------------------------------------
# 5. Print yearly table
# ----------------------------------------------------------------------
print("\n=== CD_BY_YEAR ===")
for _, row in grouped.iterrows():
    print(f"{int(row['year'])}: uw={row['uw_mean']:.6f}, w={row['w_mean']:.6f}, N={int(row['N'])}, cites={int(row['total_cites'])}")

# ----------------------------------------------------------------------
# 6. Key results (1945 vs 2010)
# ----------------------------------------------------------------------
uw_1945 = grouped.loc[grouped['year'] == 1945, 'uw_mean'].values[0]
uw_2010 = grouped.loc[grouped['year'] == 2010, 'uw_mean'].values[0]
w_1945  = grouped.loc[grouped['year'] == 1945, 'w_mean'].values[0]
w_2010  = grouped.loc[grouped['year'] == 2010, 'w_mean'].values[0]

uw_decline_pct = (uw_1945 - uw_2010) / uw_1945 * 100
w_decline_pct  = (w_1945  - w_2010)  / w_1945  * 100

print("\n=== RESULTS ===")
print(f"Sample N = {after_filter}")
print(f"Years = {int(year_max - year_min + 1)}")
print(f"UW CD 1945 = {uw_1945:.6f}")
print(f"UW CD 2010 = {uw_2010:.6f}")
print(f"W CD 1945 = {w_1945:.6f}")
print(f"W CD 2010 = {w_2010:.6f}")
print(f"UW decline = {uw_decline_pct:.1f}%")
print(f"W decline = {w_decline_pct:.1f}%")

# ----------------------------------------------------------------------
# 7. Markdown-style summary table
# ----------------------------------------------------------------------
print("\n=== DIFF_TABLE ===")
print("| Metric          | Value      |")
print("| --------------- | ---------- |")
print(f"| sample_N        | {after_filter}         |")
print(f"| uw_cd_1945      | {uw_1945:.6f}   |")
print(f"| uw_cd_2010      | {uw_2010:.6f}   |")
print(f"| w_cd_1945       | {w_1945:.6f}   |")
print(f"| w_cd_2010       | {w_2010:.6f}   |")
print(f"| uw_decline_pct  | {uw_decline_pct:.1f}        |")
print(f"| w_decline_pct   | {w_decline_pct:.1f}        |")
print(f"| overall_w_cd    | {overall_w:.6f}   |")
print(f"| post1970_w_cd   | {post1970_w:.6f}   |")
print(f"| change_2000_2010| {change_2000_2010:.6f}   |")
