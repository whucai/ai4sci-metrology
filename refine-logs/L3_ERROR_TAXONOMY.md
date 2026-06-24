# L3 Error Taxonomy

**Scope:** SciSciBench Task 2, L3 only  
**Audit file:** `/tmp/l3_audit_samples.json`  
**Full L3 set:** 211 papers  
**Sample:** 60 records, grouped as 20 case1, 20 case2, 20 case3

Percentages below use the 20-record audit sample for subtype diagnosis unless the row explicitly says full dataset.

## 1. Overview

| Case type | Full-dataset count | Share of 211 | Audit sample | Definition |
|---|---:|---:|---:|---|
| Case 1 | 151 | 71.6% | 20 | Low direction accuracy plus high uncertainty |
| Case 2 | 53 | 25.1% | 20 | Hallucination rate greater than 0 |
| Case 3 | 27 | 12.8% | 20 | Overall score greater than 0.75 |

The cases overlap: high-scoring records can still contain hallucination or direction errors. In the case3 sample, 6/20 records have nonzero hallucination and 11/20 have imperfect direction accuracy.

## 2. Case 1 - Low Direction Accuracy + High Uncertainty

Sample means: direction accuracy **0.013**, uncertainty recognition **0.800**, hallucination rate **0.300**, overall score **0.690**. All 20 records have limitation awareness **0.000**.

### Direction Error Breakdown

| Direction error type | Papers | Share of case1 sample | Claim-level count | Evidence |
|---|---:|---:|---:|---|
| Always unknown / abstention | 16/20 | 80% | 52/62 claims | Predicted direction is only `unknown` for all gold claims |
| Opposite-direction guessing | 4/20 | 20% | 9/62 claims | Predicted `positive` for negative gold or `negative` for positive gold |
| Evaluator mismatch | 0/20 | 0% | 0/62 claims | No sampled case had the gold direction present but marked wrong |
| Correct match inside otherwise low-direction papers | 2/20 | 10% | 1/62 claims | Rare partial recovery; does not change the dominant error pattern |

Concrete examples:

| Paper | Pattern | Data-backed example |
|---|---|---|
| `arroyomachado2020_science_wikipedia` | Unknown abstention | Gold has three positive claims, including medicine/biochemistry presence and open-access citations; prediction is `unknown` for all three; direction accuracy 0.000 |
| `obadage2023_citations_reproducibility` | Unknown abstention | Gold has positive correlation/F1-score claims; prediction is `unknown` for both; direction accuracy 0.000 |
| `shekar2022_novelty_based` | Opposite guessing | Gold `generalization_score` and `novelty_score` are positive; prediction is `negative` for both; direction accuracy 0.000 |
| `sun2023_ranking_mobility` | Mixed opposite plus one match | Gold includes negative mobility/inequality claims and one positive time trend; prediction is `positive` across claims; direction accuracy 0.250 |

Interpretation: case1 is primarily **excessive uncertainty substitution**, not random direction guessing. The model often produces a supported but underspecified tentative claim, then assigns `unknown` to gold claims that have positive or negative directions. The benchmark is measuring a real L3 capability gap: extracting direction from partial evidence while preserving uncertainty.

## 3. Case 2 - Hallucination

Sample means: hallucination rate **0.950**, direction accuracy **0.175**, uncertainty recognition **0.800**, overall score **0.646**. All 20 records contain at least one hallucinated predicted claim.

### Unsupported-Claim Breakdown

| Hallucination subtype | Papers | Share of case2 sample | Evidence |
|---|---:|---:|---|
| Single forced unsupported claim | 18/20 | 90% | `total_predicted=1`, `hallucinated=1` |
| Partial hallucination with two claims | 2/20 | 10% | `total_predicted=2`, `hallucinated=1` |
| Generic unsupported claim | 1/20 | 5% | `generic_claim_penalty=True` |
| Broad over-generation | 0/20 | 0% | No case has more than two predicted claims |

Direction behavior inside hallucination cases:

| Direction pattern | Papers | Share | Meaning |
|---|---:|---:|---|
| All unknown | 15/20 | 75% | Unsupported claim is usually paired with direction abstention |
| Has opposite direction | 3/20 | 15% | Unsupported claim also gets the wrong sign |
| All matched directions | 2/20 | 10% | Direction can be correct while claim support is still judged hallucinated |

Concrete examples:

| Paper | Hallucination pattern | Data-backed example |
|---|---|---|
| `tiyavorabun2022_badder_seeds` | Generic unsupported claim | `total_predicted=1`, `hallucinated=1`, `generic_claim_penalty=True`, specificity 0.000, direction accuracy 0.000 |
| `petersen2023_citation_inflation` | Unsupported sign-compressed claim | One predicted claim is hallucinated; gold contains negative disruption decline plus positive reference/citation growth, while predictions are negative across claims |
| `funk2017_dynamic_network` | Correct direction but unsupported claim | Direction accuracy 1.000 for positive CDt/mCDt claims, but `total_predicted=1`, `hallucinated=1` |
| `arXiv_2510.19246v2` | Partial hallucination | `total_predicted=2`, `hallucinated=1`; two negative metrics match, positive NDCG is missed |

Is the prompt fix causing over-generation? The sample does **not** show broad over-generation. It shows **minimal forced generation**: 18/20 hallucination records contain exactly one predicted claim. The prompt likely prevents empty abstention, but the failure mode is not too many claims; it is a single low-specificity or unsupported tentative claim when partial evidence is insufficient.

## 4. Case 3 - High Score

Sample means: overall score **0.852**, direction accuracy **0.696**, uncertainty recognition **0.800**, hallucination rate **0.275**. All 20 records have claim support score **1.000** and limitation awareness **0.000**.

### Success Patterns

| Trait | Papers | Share of case3 sample | Evidence |
|---|---:|---:|---|
| No hallucinated claims | 14/20 | 70% | `hallucinated=0` |
| One or two predicted claims | 20/20 | 100% | 13 records have one claim; 7 records have two |
| Fully matched directions | 9/20 | 45% | All gold directions matched |
| Partial direction recovery | 11/20 | 55% | Overall remains high when some directions match and support/uncertainty are strong |
| High uncertainty recognition | 20/20 | 100% | All sampled records have uncertainty recognition 0.800 |

Concrete examples:

| Paper | Success pattern | Data-backed example |
|---|---|---|
| `Scientometrics_2203.06218v2` | Clean high score | Overall 0.940, direction accuracy 1.000, hallucination 0.000, two supported claims |
| `maddi2022_article_processing_charges` | Clean high score | Overall 0.940, direction accuracy 1.000, hallucination 0.000, two supported claims |
| `arXiv_2602.05211v1` | Partial but strong | Overall 0.873, direction accuracy 0.667, hallucination 0.000; positive knowledge-proximity/flow claims match |
| `petersen2024_disruption_index` | Single salient trend recovered | Overall 0.807, hallucination 0.000; negative CD decrease is recovered, but team-size/null-effect directions are missed |

Interpretation: high L3 scores occur when partial evidence contains a **salient directional trend** and the model produces **one or two specific, supported claims** with uncertainty. Perfect limitation matching is not driving success; limitation awareness is 0.000 across the sample.

## 5. Error Taxonomy Table

| Error category | Primary case | Frequency | Diagnosis | Fix target |
|---|---|---:|---|---|
| Direction abstention | Case 1 | 16/20 case1 sample; 52/62 case1 claims | Model maps partial evidence to `unknown` even when gold direction is positive/negative | Prompt and direction-scoring calibration |
| Opposite-direction inference | Case 1/3 | 4/20 case1; 9/20 case3 | Model collapses mixed evidence to one sign or reverses improvement/reduction semantics | Genuine model limitation plus better examples |
| Single unsupported forced claim | Case 2 | 18/20 case2 | Prompt forces at least one claim, but evidence alignment is weak | Benchmark prompt and support scorer audit |
| Partial hallucination | Case 2/3 | 2/20 case2; 1/20 case3 | One supported claim plus one unsupported claim | Claim-level support scoring |
| Generic unsupported claim | Case 2 | 1/20 case2 | Very low specificity, explicit generic-claim penalty | Prompt constraint against generic claims |
| Limitation omission | All cases | 60/60 sample | No sampled record matched gold limitations | Benchmark scoring weight and prompt field design |
| High-score residual errors | Case 3 | 11/20 case3 imperfect direction; 6/20 nonzero hallucination | Overall score can remain high despite direction/hallucination errors | Score aggregation calibration |

## 6. Recommendations

| Recommendation | Benchmark vs model | Rationale |
|---|---|---|
| Keep the no-empty-output L3 prompt, but require evidence anchoring for each claim | Benchmark fix | Case2 shows one forced claim, not broad over-generation; the prompt should require a claim only when tied to observed partial evidence |
| Penalize `unknown` direction when gold is positive/negative, but allow justified uncertainty in a separate field | Benchmark fix | Case1 is dominated by `unknown` substitution: 80% of sampled papers and 84% of sampled claims |
| Add few-shot L3 examples that infer tentative direction from partial evidence | Benchmark fix | The model already recognizes uncertainty at 0.800; it needs calibration on tentative signed inference |
| Audit support/hallucination scorer on cases with direction match but hallucination=1 | Benchmark fix | `funk2017_dynamic_network` and `thelwall2025_openalex_citation` show direction can match while the claim is marked hallucinated |
| Rebalance aggregation so hallucination and direction errors cannot be hidden by support/uncertainty | Benchmark fix | Case3 includes high scores with residual hallucination or imperfect direction |
| Treat opposite-direction errors as genuine model limitations | Model limitation | These require semantic reasoning over sign, reduction, improvement, and mixed results |
| Treat limitation omission separately from conclusion inference | Benchmark design | Limitation awareness is 0.000 in all 60 sampled records, so the current L3 setup is not eliciting or scoring this dimension effectively |

## Bottom Line

The dominant L3 failure is not empty abstention anymore. It is **calibrated directional inference under uncertainty**. Case1 shows overuse of `unknown`; case2 shows a small number of forced but unsupported claims; case3 shows that success comes from specific, supported, low-count claims tied to salient directional evidence. The next benchmark fixes should target direction calibration, evidence anchoring, hallucination aggregation, and the currently nonfunctional limitation-awareness channel.
