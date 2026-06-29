# Round 2 Response (Codex gpt-5.5, xhigh)
**threadId**: 019f1188-f6ca-7322-bcbd-b9bd49bfbe4c

## Bottom line
Same-object fix rescues the design onto the plausible **7/10 path**. Largest structural flaw fixed. Remaining risk is empirical + measurement-validity (R₃ must prove it's a reliable continuous instrument, not just an elaborate detector).

## Q1: Remaining structural flaw?
No fatal structural flaw if R₂₊ implemented honestly. Three attacks remain:
1. R₂₊ may absorb most of R₃'s detection advantage.
2. Continuous ECRF must be validated as a measurement scale (low reliability/ICC → fallback collapses).
3. Killer cases may be rare (M₁-exact uncommon; M₂ easier).

## Q2: D1 fallback defensible?
Yes, with narrow wording. Defensible if FRR(R₂₊)≈FRR(R₃): "R₃ does not substantially improve binary invalid-trace detection over a provenance-augmented FactReview baseline, but it provides a reliable continuous, component-resolved measurement instrument that supports input-sensitivity analysis, localization, stability analysis, and exploratory scientometric association." NOT defensible: "R₃ beats extended FactReview" if FRR equal. Make fallback credible via: per-component reliability gates; repeat-seed ICC; Component×IO at component level; R₃ localizes better than R₂₊ flags; R₃ continuous scores predict adjudicated validity/severity better than binary R₂₊ flags. Study 2 + reliability + localization carry D1, NOT Study 4.

## Q3: M₁ empirical risk
Prior: M₁ common; M₁ + exact numerical match uncommon (1–5% of M₁); M₁ + claim-level "Supported" under coarse/directional claim ~10–25%; M₂ hard-code = easier source. Don't make killer depend only on "wrong data, right number." Define panel as M₁/M₂ process-invalid-supported; expect M₂ + coarse M₁. Report exact vs directional separately.

## Q4: Minimal NeurIPS D&B outline
1. Intro — result-level reproducibility is invalid trust signal; ECRF component-resolved metrology, same-trace audit ladder, controlled input-sensitivity.
2. Related Work — FactReview, execution-based verification, agent benchmarks, reproducibility studies; position R₂/R₂₊.
3. Measurement Model — evidence chain, ECRF/FRR/M₁–M₄, R₁/R₂/R₂₊/R₃ on same trace.
4. Dataset & Protocol — 20 papers, IO packages, 2 models, isolation, randomization, gold chains, reliability gates.
5. Study 1: Construct & Reliability — agreement, ICC, correlations, non-degeneracy.
6. Study 2: Controlled Input Sensitivity — mixed-effects Component×IO; main fig = component slopes.
7. Study 3: Trust Inflation Ladder — FRR(R₁/R₂/R₂₊/R₃), paired tests, bootstrap CI, R₂₊/R₃, localization.
8. Failure-Mode Adjudication — denominators, blinded, M₁–M₄ rates, case panels.
9. Robustness — frontier, threshold sensitivity, R₃ vs overbuilt R₃′, scorer stability.
10. Exploratory Ecological Validation — appendix/short; ECRF↔impact, clearly exploratory.

Figures: Fig1 same-trace ladder; Fig2 ECRF schema+IO packages; Fig3 Component×IO slopes; Fig4 FRR ladder+CI; Fig5 M₁/M₂ case panel. Tables: T1 pool+IO feasibility; T2 reliability/ICC by component; T3 R₂/R₂₊/R₃ paired; AppFig Study 4.

## Q5: Revised results-to-claims matrix (with R₂₊ column)
| S2 IO | S3 ladder | R₂₊ vs R₃ | S4 | Licensed claim |
|---|---|---|---|---|
| Yes | R1>R2>R2+>R3 | R3 beats R2+ | Pos | Full strong: ECRF reliable, IO-sensitive, beats extended FactReview, exploratory association |
| Yes | R1>R2>R2+>R3 | R3 beats R2+ | Null | Strong NeurIPS; no impact claim |
| Yes | R1>R2>R2+≈R3 | Tie | Pos | ECRF continuous measurement instrument; R₂₊ enough for binary detection |
| Yes | R1>R2>R2+≈R3 | Tie | Null | Still publishable if reliability strong: input-sensitive component metrology, not superior detector |
| Yes | R1>R2, R2+≈R3≈low | Tie | Any | Trivial provenance checks fix most trust inflation; ECRF useful for measurement/localization only |
| Yes | R1>R2, R2+>R3 absent | R3 no better | Any | D1 detection claim fails; input-sensitivity + instrument proposal. Borderline |
| No | R ladder holds | R3 beats R2+ | Any | Trust-inflation audit survives; IO mechanism doesn't |
| No | R ladder weak | Any | Pos | Study 4 insufficient; weak top-venue |
| No | No ladder | R2+≈R3 | Null | No main claim; reframe as negative pilot/method note |

Score: revised design plausible **7/10** if results land + reliability gates pass. If R₂₊ ties R₃, best case ~6.5–7 only if fallback honest + continuous measurement value shown decisively.
