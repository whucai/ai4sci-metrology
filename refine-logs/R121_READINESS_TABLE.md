# R121 Readiness Table — FROZEN v1-r3 (2026-06-29)

Pool: 20/20 papers frozen | A=glm-5.2, B=codex-gpt-5.2 | 3-round adjudication | **GATE PASSES**

## Inter-annotator agreement (Round 3, fully clarified rubric)

| component | Po | kappa | alpha | disagree | >=0.70 |
|---|---|---|---|---|---|
| data_source | 0.95 | 0.907 | **0.981** | 1 | YES |
| sample | 0.9 | 0.459 | **0.729** | 2 | YES |
| indicator | 0.95 | 0.900 | **0.951** | 1 | YES |
| model | 1.0 | 1.000 | **1.0** | 0 | YES |
| result_table | 0.8 | 0.548 | **0.795** | 4 | YES |
| claim | 1.0 | nan | **1.0** | 0 | YES |
| **OVERALL** | 0.933 | 0.852 | **0.945** | — | YES |

**R122 gate**: overall alpha=0.945 (>=0.70); 6/6 components meet 0.70; Sample=0.729, Claim=1.0. **GATE PASSES — all thresholds cleared.**

## Round history

| round | overall alpha | components >=0.70 | clarification |
|---|---|---|---|
| R1 original | 0.717 | 2/6 (Data, Indicator) | — |
| R2 (Model/Result/Claim) | 0.876 | 4/6 (+Result, +Claim) | Model=spec/code-independent; Result=exact-targets; Claim=stated |
| **R3 (Sample+Model)** | **0.945** | **6/6** | Sample=N-pending!=not-stated; Model=estimator+vars+FE enumerated |

## Per-paper frozen gold ECRF

| # | paper_id | domain | stratum | task | frozen gold ECRF | KU-Leuven? |
|---|---|---|---|---|---|---|
| 1 | petersen2024 | SoS | Low | STRICT | 1.0 | - |
| 2 | wu2019_teams | SoS | Low | STRICT | 0.917 | - |
| 3 | park2023_disruptive | SoS | Low | STRICT | 1.0 | - |
| 4 | bentley2023_disruption | SoS | Low | STRICT | 0.958 | - |
| 5 | maddi2024 | Management_Strategy | Low | METHOD | 0.625 | - |
| 6 | arts2021 | IS_Innovation | Medium | METHOD | 0.792 | YES |
| 7 | ke2015_sleeping_beauties | SoS | Medium | METHOD | 0.625 | - |
| 8 | sun2023_ranking_mobility | SoS | Medium | DATA-SUB | 0.833 | - |
| 9 | liu2018_hotstreaks | SoS | High | METHOD | 1.0 | - |
| 10 | deng2023_enhancing_disruption | SoS | Medium | METHOD | 0.792 | - |
| 11 | schaper2025_frontier | IS_Innovation | Medium | DATA-SUB | 0.583 | YES |
| 12 | galuez2023_technology_transfer | IS_Innovation | Medium | METHOD | 0.833 | - |
| 13 | vasarhelyi2023_who_benefits | IS_Innovation | Medium | DATA-SUB | 0.667 | - |
| 14 | donner2024_data_inaccuracy | Management_Strategy | Medium | METHOD | 0.667 | - |
| 15 | zheng2025_male_female_retractions | Management_Strategy | Medium | DATA-SUB | 0.833 | - |
| 16 | funk2017 | IS_Innovation | High | STRICT | 0.958 | - |
| 17 | gebhart2023_math_framework | SoS | High | METHOD | 0.75 | - |
| 18 | obadage2024_citations_repro | IS_Innovation | High | STRICT | 0.958 | - |
| 19 | bikard2013 | Management_Strategy | High | DATA-SUB | 0.708 | - |
| 20 | arts2021_patent_nlp | Management_Strategy | High | METHOD | 1.0 | YES |

## Caveats
- **KU Leuven/Arts concentration**: 3 papers (#6, #11, #20). Robustness check R-robust-KU planned (exclude/group; confirm IO->ECRF not group-driven).
- **schaper2025 IO3**: partial/boundary retained (PDF fetch blocked via curl; human to confirm linkage release).
- **R122-R125**: gate PASSES but remain BLOCKED per user instruction (do not launch yet).
