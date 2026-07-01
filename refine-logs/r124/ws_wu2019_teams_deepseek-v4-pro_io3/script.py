import pandas as pd
import numpy as np

# Path to raw data
DATA_PATH = "/workspace/raw_data/sciscinet_sample.parquet"

# Load data
df = pd.read_parquet(DATA_PATH)
print("Columns in dataset:", df.columns.tolist())

# Check presence of key columns
if 'disruption_score' not in df.columns:
    raise KeyError("Column 'disruption_score' missing. Check data dictionary.")
if 'team_size' not in df.columns and 'author_count' in df.columns:
    # Use author_count as team_size, as per sample notes
    df['team_size'] = df['author_count']
    print("Using 'author_count' as team_size.")
elif 'team_size' not in df.columns:
    raise KeyError("Neither 'team_size' nor 'author_count' found.")

# Drop missing values in disruption_score or team_size
df_clean = df.dropna(subset=['disruption_score', 'team_size'])
# Remove team_size <= 0
df_clean = df_clean[df_clean['team_size'] > 0].copy()
print(f"Sample size after cleaning: {len(df_clean)}")

# Compute deciles of team_size
df_clean['team_decile'] = pd.qcut(df_clean['team_size'], 10, labels=False) + 1  # labels 1-10

# Mean disruption by decile
mean_disruption_by_decile = df_clean.groupby('team_decile')['disruption_score'].mean()
print("\nMean disruption by team-size decile:")
for decile, val in mean_disruption_by_decile.items():
    print(f"Decile {decile}: {val:.6f}")

# Smallest and largest decile means
d1 = mean_disruption_by_decile.loc[1]
d10 = mean_disruption_by_decile.loc[10]
print("\nRESULT mean_disruption_decile_1 = {:.6f}".format(d1))
print("RESULT mean_disruption_decile_10 = {:.6f}".format(d10))

# Pearson correlation between team_size and disruption_score
corr_matrix = df_clean[['team_size', 'disruption_score']].corr(method='pearson')
r = corr_matrix.loc['team_size', 'disruption_score']
print("RESULT pearson_correlation_team_size_vs_disruption = {:.4f}".format(r))

# Spearman rank correlation
spearman_corr = df_clean[['team_size', 'disruption_score']].corr(method='spearman')
r_s = spearman_corr.loc['team_size', 'disruption_score']
print("RESULT spearman_rank_correlation_team_size_vs_disruption = {:.4f}".format(r_s))

# Directional conclusion
if r < 0:
    print("CONCLUSION: Negative correlation → small teams tend to produce more disruptive work.")
else:
    print("CONCLUSION: No negative correlation detected; check data or method.")

# Note on replication
print("Script computed all values directly from raw data. No paper-reported numerical values were embedded; these results are solely computed from the provided sample.")
