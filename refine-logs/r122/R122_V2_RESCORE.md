# R122 v2 ECRF rescore (qwen3-32b, single model)

Scorer: refine-logs/r122_freeze/ecrf_v2_scorer.py (final_ecrf, with v1 weights+caps)

| paper | io1 | io2 | io3 |
|---|---|---|---|
| arts2021 | 0.42 | 0.55 | 0.50 |
| arts2021_patent_nlp | 0.50 | 0.50 | 0.50 |
| bentley2023_disruption | 0.50 | 0.50 | 0.75 |
| bikard2013 | 0.50 | 0.55 | 0.50 |
| deng2023_enhancing_disruption | 0.50 | 0.00 | - |
| donner2024_data_inaccuracy | 0.50 | 0.50 | - |
| funk2017 | 0.50 | 0.60 | 0.75 |
| galuez2023_technology_transfer | 0.50 | 0.50 | - |
| gebhart2023_math_framework | 0.50 | 0.50 | - |
| ke2015_sleeping_beauties | 0.50 | 0.50 | - |
| liu2018_hotstreaks | 0.50 | 0.50 | 0.50 |
| maddi2024 | 0.50 | 0.50 | 0.95 |
| obadage2024_citations_repro | 0.50 | 0.50 | 0.50 |
| park2023_disruptive | 0.50 | 0.50 | 0.50 |
| petersen2024 | 0.50 | 0.50 | 0.60 |
| schaper2025_frontier | 0.50 | 0.50 | - |
| sun2023_ranking_mobility | 0.50 | 0.50 | - |
| vasarhelyi2023_who_benefits | 0.50 | 0.50 | - |
| wu2019_teams | 0.50 | 0.60 | 0.50 |
| zheng2025_male_female_retractions | 0.50 | 0.50 | - |

- IO1 mean v2 = 0.496 (n=20)
- IO2 mean v2 = 0.490 (n=20)
- IO3 mean v2 = 0.595 (n=11)

Trend: IO1 ~0.50, IO2 ~0.49, IO3 ~0.60 (n=11 clean-IO3 anchors). v2 caps (synthetic-substitute, no-exec-result, result=0) bring IO1/IO2 down vs v0 ceiling-inflation; IO3 rises with real data+code. IO1~=IO2 reflects B1 non-compliance (agents synthesize despite being given real data at IO2 -> cap 0.5).
