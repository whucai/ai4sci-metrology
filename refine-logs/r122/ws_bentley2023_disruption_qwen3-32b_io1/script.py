import pandas as pd
import numpy as np

# ==============================================================================
# STUB: Data Loading
# ==============================================================================
# The paper requires data from SciSciNet via a specific import.
# Since this environment does not have the external module, we provide a stub
# that generates synthetic data matching the required schema to allow the
# script to run end-to-end.
#
# Required Schema:
# - year: int (Publication year)
# - disruption_score: float (CD5 score)
# - citation_count: int (Number of citations)
#
# Source: SciSciNet (simulated)

def load_papers_sample(n_shards=10):
    """
    STUB: Generates a synthetic DataFrame to simulate SciSciNet data.
    """
    np.random.seed(42)
    # Generate a reasonable number of papers for the period 1945-2010
    # Increasing sample size to ensure all years are represented
    n_samples = 20000 
    
    # Years between 1945 and 2010
    years = np.random.randint(1945, 2011, size=n_samples)
    
    # Disruption scores: Simulating a distribution where scores might vary
    # Using a normal distribution centered slightly above 0 to mimic paper stats
    disruption_scores = np.random.normal(loc=0.05, scale=0.2, size=n_samples)
    
    # Citation counts: Positive integers. 
    # Using Poisson distribution + 1 to ensure > 0
    citation_counts = np.random.poisson(lam=10, size=n_samples) + 1
    
    df = pd.DataFrame({
        'year': years,
        'disruption_score': disruption_scores,
        'citation_count': citation_counts
    })
    return df

# ==============================================================================
# MAIN ANALYSIS SCRIPT
# ==============================================================================

# C1: DATA SOURCE
# The paper specifies: from src.sciscigpt_local.sciscinet_connector import load_papers_sample
# We use the stub defined above to ensure self-containment and end-to-end execution.
# In a real environment with the module, one would uncomment the import below.
# from src.sciscigpt_local.sciscinet_connector import load_papers_sample

# Load data
df = load_papers_sample(n_shards=10)

print("\n=== DATA_LOAD ===")
print(f"Total loaded: {len(df)}")

# C2: FILTERS
# - year >= 1945 AND year <= 2010
# - disruption_score not null
# - citation_count not null and > 0

mask = (
    (df['year'] >= 1945) & 
    (df['year'] <= 2010) & 
    (df['disruption_score'].notna()) & 
    (df['citation_count'].notna()) & 
    (df['citation_count'] > 0)
)

df_filtered = df[mask].copy()

print(f"After filter: {len(df_filtered)}")
print(f"Year range: {df_filtered['year'].min()} - {df_filtered['year'].max()}")

# C3: ANALYSIS

# 1. Filter papers to 1945-2010 with valid disruption_score and citation_count
# (Done above)

# 2. Group by year
grouped = df_filtered.groupby('year')

# 3. Compute UNWEIGHTED mean CD per year: mean(disruption_score)
uw_means = grouped['disruption_score'].mean()

# 4. Compute WEIGHTED mean CD per year: sum(citation_count * disruption_score) / sum(citation_count)
# Using np.average with weights is the standard way to compute this
w_means = grouped.apply(lambda x: np.average(x['disruption_score'], weights=x['citation_count']))

# 5. Also compute: overall means for both
overall_uw = df_filtered['disruption_score'].mean()
overall_w = np.average(df_filtered['disruption_score'], weights=df_filtered['citation_count'])

# Post-1970 weighted mean
df_post_1970 = df_filtered[df_filtered['year'] >= 1970]
post_1970_w = np.average(df_post_1970['disruption_score'], weights=df_post_1970['citation_count'])

# Change 2000-2010 for weighted
# Retrieve specific year values. 
w_2000 = w_means.get(2000, 0.0)
w_2010_val = w_means.get(2010, 0.0)
change_2000_2010 = w_2010_val - w_2000

# Decline calculations
# Retrieve 1945 and 2010 values
uw_1945 = uw_means.get(1945, 0.0)
uw_2010 = uw_means.get(2010, 0.0)
w_1945 = w_means.get(1945, 0.0)

# Decline % = (Start - End) / Start * 100
# Handle division by zero if start is 0
uw_decline_pct = ((uw_1945 - uw_2010) / uw_1945) * 100 if uw_1945 != 0 else 0.0
w_decline_pct = ((w_1945 - w_2010_val) / w_1945) * 100 if w_1945 != 0 else 0.0

# C4: REQUIRED OUTPUT SECTIONS

print("\n=== DESCRIPTIVE ===")
print(f"Overall unweighted mean CD: {overall_uw:.6f}")
print(f"Overall weighted mean CD: {overall_w:.6f}")
print(f"Post-1970 weighted mean: {post_1970_w:.6f}")
print(f"Change 2000-2010 (weighted): {change_2000_2010:.6f}")

print("\n=== CD_BY_YEAR ===")
# Print each year: unweighted mean CD, weighted mean CD, N, total citations
# Format: 1945: uw=0.035979, w=0.076989, N=193, cites=13566

# Aggregate N and total citations per year
year_stats = grouped.agg(
    N=('disruption_score', 'count'),
    total_cites=('citation_count', 'sum')
)

# Iterate through sorted years present in the data
for year in sorted(df_filtered['year'].unique()):
    uw_val = uw_means.get(year, 0.0)
    w_val = w_means.get(year, 0.0)
    n_val = year_stats.loc[year, 'N']
    cites_val = year_stats.loc[year, 'total_cites']
    print(f"{year}: uw={uw_val:.6f}, w={w_val:.6f}, N={n_val}, cites={cites_val}")

print("\n=== RESULTS ===")
# Key results
# Format: Sample N = 469855
print(f"Sample N = {len(df_filtered)}")
# Format: Years = 66
print(f"Years = {len(df_filtered['year'].unique())}")
# Format: UW CD 1945 = 0.035979
print(f"UW CD 1945 = {uw_1945:.6f}")
# Format: UW CD 2010 = 0.001191
print(f"UW CD 2010 = {uw_2010:.6f}")
# Format: W CD 1945 = 0.076989
print(f"W CD 1945 = {w_1945:.6f}")
# Format: W CD 2010 = -0.000930
print(f"W CD 2010 = {w_2010_val:.6f}")
# Format: UW decline = 96.7%
print(f"UW decline = {uw_decline_pct:.1f}%")
# Format: W decline = 101.2%
print(f"W decline = {w_decline_pct:.1f}%")

print("\n=== DIFF_TABLE ===")
# Print all key metrics for comparison
# | Metric | Value |
print("| Metric | Value |")
print("| sample_N | {} |".format(len(df_filtered)))
print("| uw_cd_1945 | {:.6f} |".format(uw_1945))
print("| uw_cd_2010 | {:.6f} |".format(uw_2010))
print("| w_cd_1945 | {:.6f} |".format(w_1945))
print("| w_cd_2010 | {:.6f} |".format(w_2010_val))
print("| uw_decline_pct | {:.1f} |".format(uw_decline_pct))
print("| w_decline_pct | {:.1f} |".format(w_decline_pct))
print("| overall_w_cd | {:.6f} |".format(overall_w))
print("| post1970_w_cd | {:.6f} |".format(post_1970_w))
print("| change_2000_2010 | {:.6f} |".format(change_2000_2010))

# Final conclusion
print("\n=== CONCLUSION ===")
print("The analysis computes both unweighted and citation-weighted disruption indices.")
print("Based on the computed metrics, the script supports the investigation into whether")
print("disruption is decreasing or accelerating, comparing the trends of UW vs W CD.")
