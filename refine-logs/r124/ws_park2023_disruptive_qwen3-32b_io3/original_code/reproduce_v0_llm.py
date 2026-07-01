# Reproduce CD index time-trend analysis from Park, Leahey, Funk (2023)
import numpy as np
from src.sciscigpt_local.sciscinet_connector import load_papers_sample

# C1: Load data
df = load_papers_sample(n_shards=10)

# C2: Filter to 1945-2010 and non-null disruption_score
mask = (df['year'] >= 1945) & (df['year'] <= 2010) & df['disruption_score'].notna()
filtered = df.loc[mask].copy()
total_loaded = len(df)
filtered_count = len(filtered)
year_range = (filtered['year'].min(), filtered['year'].max())

# === DATA_LOAD ===
print("\n=== DATA_LOAD ===")
print(f"Total papers loaded: {total_loaded}")
print(f"Papers after filter (1945-2010, valid CD): {filtered_count}")
print(f"Year range: {year_range[0]} - {year_range[1]}")

# C3: Group by year and compute mean CD
yearly_stats = filtered.groupby('year')['disruption_score'].agg(['mean', 'count']).reset_index()
yearly_stats.columns = ['year', 'mean_cd', 'n_papers']

# Overall descriptive stats
overall_mean = filtered['disruption_score'].mean()
overall_std = filtered['disruption_score'].std()

# === DESCRIPTIVE ===
print("\n=== DESCRIPTIVE ===")
print(f"Overall mean CD: {overall_mean:.6f}")
print(f"Overall std CD: {overall_std:.6f}")
print("Years in analysis:", sorted(yearly_stats['year'].unique()))

# === CD_BY_YEAR ===
print("\n=== CD_BY_YEAR ===")
for _, row in yearly_stats.iterrows():
    y = int(row['year'])
    m = row['mean_cd']
    n = int(row['n_papers'])
    print(f"{y}: mean={m:.6f}, N={n}")

# Extract specific years
cd_1945 = yearly_stats.loc[yearly_stats['year'] == 1945, 'mean_cd'].values[0] if 1945 in yearly_stats['year'].values else np.nan
cd_2010 = yearly_stats.loc[yearly_stats['year'] == 2010, 'mean_cd'].values[0] if 2010 in yearly_stats['year'].values else np.nan

if not np.isnan(cd_1945) and cd_1945 != 0:
    decline_pct = (cd_1945 - cd_2010) / cd_1945 * 100
else:
    decline_pct = np.nan

# === RESULTS ===
print("\n=== RESULTS ===")
print(f"Sample N = {filtered_count}")
print(f"Years = {len(yearly_stats)}")
print(f"CD 1945 = {cd_1945:.6f}")
print(f"CD 2010 = {cd_2010:.6f}")
if not np.isnan(decline_pct):
    print(f"Decline = {decline_pct:.1f}%")
else:
    print("Decline = N/A")

# === DIFF_TABLE ===
print("\n=== DIFF_TABLE ===")
print("| Metric | Value |")
print("|---|---|")
print(f"| sample_N | {filtered_count} |")
print(f"| years_count | {len(yearly_stats)} |")
if not np.isnan(cd_1945):
    print(f"| cd_1945_mean | {cd_1945:.6f} |")
else:
    print("| cd_1945_mean | N/A |")
if not np.isnan(cd_2010):
    print(f"| cd_2010_mean | {cd_2010:.6f} |")
else:
    print("| cd_2010_mean | N/A |")
if not np.isnan(decline_pct):
    print(f"| decline_pct | {decline_pct:.1f} |")
else:
    print("| decline_pct | N/A |")
print(f"| overall_mean_cd | {overall_mean:.6f} |")
