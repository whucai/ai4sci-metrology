import pandas as pd
import numpy as np

# --------------------------------------------------------------------
# Load the SciSciNet sample data from the provided parquet file
# --------------------------------------------------------------------
data_path = "/workspace/raw_data/sciscinet_sample.parquet"
df = pd.read_parquet(data_path)
total_loaded = len(df)

# --------------------------------------------------------------------
# C2: Filters: year 1945-2010, disruption_score not null
# --------------------------------------------------------------------
# Ensure column exists (the paper uses 'disruption_score' for the CD index)
col_cd = 'disruption_score' if 'disruption_score' in df.columns else 'cd_index'
mask = (
    (df['year'] >= 1945) &
    (df['year'] <= 2010) &
    df[col_cd].notna()
)
df_filtered = df[mask].copy()
sample_n = len(df_filtered)
year_min = df_filtered['year'].min()
year_max = df_filtered['year'].max()

# --------------------------------------------------------------------
# REQUIRED OUTPUT SECTION: DATA_LOAD
# --------------------------------------------------------------------
print("=== DATA_LOAD ===")
print(f"Total papers loaded: {total_loaded}")
print(f"Papers after filter: {sample_n}")
print(f"Year range: {int(year_min)} - {int(year_max)}")

# --------------------------------------------------------------------
# REQUIRED OUTPUT SECTION: DESCRIPTIVE
# --------------------------------------------------------------------
overall_mean = df_filtered[col_cd].mean()
overall_std = df_filtered[col_cd].std()          # sample std (ddof=1)
years_in_data = sorted(df_filtered['year'].unique())

print("\n=== DESCRIPTIVE ===")
print(f"Overall mean CD: {overall_mean:.6f}")
print(f"Std CD: {overall_std:.6f}")
print(f"Years covered: {len(years_in_data)} distinct years")

# --------------------------------------------------------------------
# REQUIRED OUTPUT SECTION: CD_BY_YEAR
# --------------------------------------------------------------------
grouped = df_filtered.groupby('year')[col_cd].agg(['mean', 'count']).reset_index()
grouped = grouped.sort_values('year')  # ensure correct order

print("\n=== CD_BY_YEAR ===")
for _, row in grouped.iterrows():
    year = int(row['year'])
    mean_val = row['mean']
    cnt = int(row['count'])
    print(f"{year}: mean={mean_val:.6f}, N={cnt}")

# --------------------------------------------------------------------
# REQUIRED OUTPUT SECTION: RESULTS
# --------------------------------------------------------------------
print("\n=== RESULTS ===")

cd_1945 = grouped[grouped['year'] == 1945]['mean']
cd_2010 = grouped[grouped['year'] == 2010]['mean']
cd_1945_val = cd_1945.values[0] if len(cd_1945) > 0 else np.nan
cd_2010_val = cd_2010.values[0] if len(cd_2010) > 0 else np.nan

if not (np.isnan(cd_1945_val) or np.isnan(cd_2010_val)) and cd_1945_val != 0:
    decline_pct = (cd_1945_val - cd_2010_val) / cd_1945_val * 100.0
else:
    decline_pct = np.nan

print(f"Sample N = {sample_n}")
print(f"Years = {len(years_in_data)}")
print(f"CD 1945 = {cd_1945_val:.6f}")
print(f"CD 2010 = {cd_2010_val:.6f}")
if not np.isnan(decline_pct):
    print(f"Decline = {decline_pct:.1f}%")
else:
    print("Decline = N/A")

# --------------------------------------------------------------------
# REQUIRED OUTPUT SECTION: DIFF_TABLE
# --------------------------------------------------------------------
print("\n=== DIFF_TABLE ===")
print("| Metric | Value |")
print("|--------|-------|")
print(f"| sample_N | {sample_n} |")
print(f"| years_count | {len(years_in_data)} |")
print(f"| cd_1945_mean | {cd_1945_val:.6f} |" if not np.isnan(cd_1945_val) else "| cd_1945_mean | None |")
print(f"| cd_2010_mean | {cd_2010_val:.6f} |" if not np.isnan(cd_2010_val) else "| cd_2010_mean | None |")
print(f"| decline_pct | {decline_pct:.1f} |" if not np.isnan(decline_pct) else "| decline_pct | None |")
print(f"| overall_mean_cd | {overall_mean:.6f} |")

# --------------------------------------------------------------------
# Print paper-reported values for easy comparison
# --------------------------------------------------------------------
print("\n=== PAPER_REPORTED_VALUES ===")
print("PAPER_REPORTED sample_N = 469855")
print("PAPER_REPORTED years_count = 66")
print("PAPER_REPORTED cd_1945_mean = 0.035979")
print("PAPER_REPORTED cd_2010_mean = 0.001191")
print("PAPER_REPORTED decline_pct = 96.7%")
print("PAPER_REPORTED overall_mean_cd = 0.005724")
