Reproduce the citation-weighted disruption analysis from:

  Bentley, Valverde, Borycz, Vidiella, Horne, Duran-Nebreda, O'Brien (2023)
  "Is disruption decreasing, or is it accelerating?"
  Advances in Complex Systems, 2023. DOI: 10.1142/S0219525923500066

## TASK

Compute both the original (unweighted) and citation-weighted CD5 disruption
index by year for papers 1945-2010, using SciSciNet data. The paper argues
that the reported CD5 decline (Park2023) is an artifact of exponential growth
and that a citation-weighted measure shows different trends.

## MANDATORY CONSTRAINTS

### C1: DATA SOURCE
Use SciSciNet via:
  from src.sciscigpt_local.sciscinet_connector import load_papers_sample
  df = load_papers_sample(n_shards=10)

### C2: FILTERS
- year >= 1945 AND year <= 2010
- disruption_score not null
- citation_count not null and > 0

### C3: ANALYSIS
1. Filter papers to 1945-2010 with valid disruption_score and citation_count
2. Group by year
3. Compute UNWEIGHTED mean CD per year: mean(disruption_score)
4. Compute WEIGHTED mean CD per year: sum(citation_count * disruption_score) / sum(citation_count)
5. Also compute: overall means for both, decline %, change 2000-2010 for weighted

### C4: REQUIRED OUTPUT SECTIONS
print("\n=== DATA_LOAD ===")
# Total loaded, after filter, year range

print("\n=== DESCRIPTIVE ===")
# Overall unweighted mean CD, overall weighted mean CD
# Post-1970 weighted mean, change 2000-2010

print("\n=== CD_BY_YEAR ===")
# Print each year: unweighted mean CD, weighted mean CD, N, total citations
# Format: 1945: uw=0.035979, w=0.076989, N=193, cites=13566

print("\n=== RESULTS ===")
# Key results
# Format: Sample N = 469855
# Format: Years = 66
# Format: UW CD 1945 = 0.035979
# Format: UW CD 2010 = 0.001191
# Format: W CD 1945 = 0.076989
# Format: W CD 2010 = -0.000930
# Format: UW decline = 96.7%
# Format: W decline = 101.2%

print("\n=== DIFF_TABLE ===")
# Print all key metrics for comparison
# | Metric | Value |
# | sample_N | 469855 |
# | uw_cd_1945 | 0.035979 |
# | uw_cd_2010 | 0.001191 |
# | w_cd_1945 | 0.076989 |
# | w_cd_2010 | -0.000930 |
# | uw_decline_pct | 96.7 |
# | w_decline_pct | 101.2 |
# | overall_w_cd | 0.014379 |
# | post1970_w_cd | 0.010449 |
# | change_2000_2010 | -0.003413 |

### C5: KEY REQUIREMENTS
- Use pandas groupby for aggregation
- Use citation_count column for weighting (NOT reference_count)
- Weighted formula: sum(citation_count * disruption_score) / sum(citation_count)
- Do NOT use custom formulas — use np.average() with weights or manual sum/sum
