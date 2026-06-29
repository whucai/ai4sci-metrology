# R121 Readiness Table — FROZEN (2026-06-29)

Pool: 20/20 papers frozen | Annotators: A=glm-5.2, B=codex-gpt-5.2 | Adjudicator: senior (Claude)

## Inter-annotator agreement (Round 2, clarified rubric)

| component | Po | kappa | alpha | disagree | >=0.70 |
|---|---|---|---|---|---|
| data_source | 0.95 | 0.907 | 0.981 | 1 | YES |
| sample | 0.6 | 0.200 | 0.594 | 8 | no |
| indicator | 0.95 | 0.900 | 0.951 | 1 | YES |
| model | 0.75 | 0.390 | 0.694 | 5 | no |
| result_table | 0.8 | 0.548 | 0.795 | 4 | YES |
| claim | 1.0 | nan | 1.0 | 0 | YES |
| **OVERALL** | 0.842 | 0.683 | **0.876** | — | YES |

**R122 gate**: overall alpha=0.876 (>=0.70 YES); 4/6 components meet 0.70. Sample=0.594 (borderline, just below 0.60 relaxation — N-pending ambiguity). Model=0.694 (just below 0.70). Status: **BORDERLINE — Sample 0.594 just shy of 0.60**. Pool frozen; recommend one Sample-rubric clarification (N-pending rule) before R122.

## Per-paper frozen gold ECRF (component finals = mean A-clarified, B-clarified)

| # | paper_id | domain | stratum | task | frozen gold ECRF | KU-Leuven? |
|---|---|---|---|---|---|---|
| 1 | petersen2024 | SoS | Low | STRICT | 1.0 | - |
| 2 | wu2019_teams | SoS | Low | STRICT | 0.875 | - |
| 3 | park2023_disruptive | SoS | Low | STRICT | 1.0 | - |
| 4 | bentley2023_disruption | SoS | Low | STRICT | 0.958 | - |
| 5 | maddi2024 | Management_Strategy | Low | METHOD | 0.625 | - |
| 6 | arts2021 | IS_Innovation | Medium | METHOD | 0.792 | YES |
| 7 | ke2015_sleeping_beauties | SoS | Medium | METHOD | 0.583 | - |
| 8 | sun2023_ranking_mobility | SoS | Medium | DATA-SUB | 0.75 | - |
| 9 | liu2018_hotstreaks | SoS | High | METHOD | 0.958 | - |
| 10 | deng2023_enhancing_disruption | SoS | Medium | METHOD | 0.792 | - |
| 11 | schaper2025_frontier | IS_Innovation | Medium | DATA-SUB | 0.583 | YES |
| 12 | galuez2023_technology_transfer | IS_Innovation | Medium | METHOD | 0.792 | - |
| 13 | vasarhelyi2023_who_benefits | IS_Innovation | Medium | DATA-SUB | 0.542 | - |
| 14 | donner2024_data_inaccuracy | Management_Strategy | Medium | METHOD | 0.625 | - |
| 15 | zheng2025_male_female_retractions | Management_Strategy | Medium | DATA-SUB | 0.708 | - |
| 16 | funk2017 | IS_Innovation | High | STRICT | 0.875 | - |
| 17 | gebhart2023_math_framework | SoS | High | METHOD | 0.708 | - |
| 18 | obadage2024_citations_repro | IS_Innovation | High | STRICT | 0.958 | - |
| 19 | bikard2013 | Management_Strategy | High | DATA-SUB | 0.667 | - |
| 20 | arts2021_patent_nlp | Management_Strategy | High | METHOD | 1.0 | YES |

## Caveats & soft blockers
- **KU Leuven/Arts concentration**: 3 papers (#6, #11, #20). Robustness check R-robust-KU planned (exclude/group these; confirm IO->ECRF effect not group-driven).
- **schaper2025 IO3**: retained partial/boundary (PDF fetch blocked via curl; human annotator to confirm linkage release). Does not block R121.
- **Sample component alpha 0.594**: borderline (N-pending rule ambiguity). Recommend one more rubric clarification before R122.
- **R122-R125**: remain BLOCKED per user instruction (and pending the Sample-rubric clarification).
