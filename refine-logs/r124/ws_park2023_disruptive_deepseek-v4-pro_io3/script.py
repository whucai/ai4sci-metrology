import pandas as pd
import numpy as np

# Attempt to use the SciSciNet connector as per the paper's constraints.
# If unavailable, fall back to reading the parquet file directly.
try:
    from src.sciscigpt_local.sciscinet_connector import load_papers_sample
    df_raw = load_papers_sample(n_shards=10)
    print("Loaded data via SciSciNet connector.")
except (ModuleNotFoundError, ImportError, FileNotFoundError):
    # Fallback: read the raw parquet file provided
    df_raw = pd.read_parquet('/workspace/raw_data/sciscinet_sample.parquet')
    print("Loaded data directly from parquet file (adapted from original code).")

# --- MANDATORY FILTERS ---
mask = (df_raw['year'] >= 1945) & (df_raw['year'] <= 2010) & df_raw['disruption_score'].notna()
df = df_raw.loc[mask].copy()
total_loaded = len(df_raw)
n_filtered = len(df)
year_min, year_max = df['year'].min(), df['year'].max()

print("\n=== DATA_LOAD ===")
print(f"Total papers loaded: {total_loaded}")
print(f"Papers after filter (1945-2010, disruption_score not null): {n_filtered}")
print(f"Year range: {int(year_min)} - {int(year_max)}")

# --- AGGREGATION ---
yearly = df.groupby('year')['disruption_score'].agg(['mean', 'count']).reset_index()
yearly.columns = ['year', 'mean_cd', 'N']

overall_mean = df['disruption_score'].mean()
overall_std = df['disruption_score'].std()

print("\n=== DESCRIPTIVE ===")
print(f"Overall mean CD: {overall_mean:.6f}")
print(f"Overall std CD: {overall_std:.6f}")
print(f"Years found: {yearly['year'].nunique()}")

# --- YEARLY OUTPUT ---
print("\n=== CD_BY_YEAR ===")
for _, row in yearly.iterrows():
    yr = int(row['year'])
    mean_val = row['mean_cd']
    n_val = row['N']
    print(f"{yr}: mean={mean_val:.6f}, N={n_val}")

# --- KEY METRICS ---
cd_1945 = yearly.loc[yearly['year'] == 1945, 'mean_cd'].iloc[0]
cd_2010 = yearly.loc[yearly['year'] == 2010, 'mean_cd'].iloc[0]
decline_pct = (cd_1945 - cd_2010) / cd_1945 * 100
years_count = yearly['year'].nunique()

print("\n=== RESULTS ===")
print(f"Sample N = {n_filtered}")
print(f"Years = {years_count}")
print(f"CD 1945 = {cd_1945:.6f}")
print(f"CD 2010 = {cd_2010:.6f}")
print(f"Decline = {decline_pct:.1f}%")

# --- DIFF_TABLE (markdown style) ---
print("\n=== DIFF_TABLE ===")
print("| Metric | Value |")
print("|--------|-------|")
print(f"| sample_N | {n_filtered} |")
print(f"| years_count | {years_count} |")
print(f"| cd_1945_mean | {cd_1945:.6f} |")
print(f"| cd_2010_mean | {cd_2010:.6f} |")
print(f"| decline_pct | {decline_pct:.1f} |")
print(f"| overall_mean_cd | {overall_mean:.6f} |")
