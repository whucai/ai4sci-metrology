Reproduce the CD index time-trend analysis from:

  Park, Leahey, Funk (2023) "Papers and patents are becoming less
  disruptive over time." Nature, Vol 613, pp 138-144.

## TASK

Compute the mean CD (disruption) index by year for papers published
between 1945 and 2010, using SciSciNet data.

## MANDATORY CONSTRAINTS

### C1: DATA SOURCE
Use SciSciNet via:
  from src.sciscigpt_local.sciscinet_connector import load_papers_sample
  df = load_papers_sample(n_shards=10)

### C2: FILTERS
- year >= 1945 AND year <= 2010
- disruption_score not null
- No additional filters needed (CD index is pre-computed in the data)

### C3: ANALYSIS
1. Filter papers to 1945-2010 with valid disruption_score
2. Group by year
3. Compute mean disruption_score per year
4. Also compute: overall mean, std, CD in 1945, CD in 2010, decline %

### C4: REQUIRED OUTPUT SECTIONS
print("\n=== DATA_LOAD ===")
# Total papers loaded, papers after filter, year range

print("\n=== DESCRIPTIVE ===")
# Overall mean CD, std, all years

print("\n=== CD_BY_YEAR ===")
# Print each year: mean CD, N papers
# Format: 1945: mean=0.035979, N=193

print("\n=== RESULTS ===")
# Sample N, years count, CD 1945, CD 2010, decline %
# Format: Sample N = 469855
# Format: Years = 66
# Format: CD 1945 = 0.035979
# Format: CD 2010 = 0.001191
# Format: Decline = 96.7%

print("\n=== DIFF_TABLE ===")
# Print key metrics for comparison
# | Metric | Value |
# | sample_N | 469855 |
# | years_count | 66 |
# | cd_1945_mean | 0.035979 |
# | cd_2010_mean | 0.001191 |
# | decline_pct | 96.7 |
# | overall_mean_cd | 0.005724 |

### C5: KEY REQUIREMENTS
- Use pandas groupby for aggregation
- Print all 66 years in CD_BY_YEAR section
- Ensure all sections are printed with the EXACT section headers shown above
- Use np.mean() or .mean() for aggregation — do not use custom formulas
