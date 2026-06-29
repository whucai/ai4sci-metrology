# Round 1 Response (Codex gpt-5.5, xhigh)
**threadId**: 019f1188-f6ca-7322-bcbd-b9bd49bfbe4c
**Date**: 2026-06-29

## Evidence status verified by reviewer
- Pilot IO signal real but small-N (R102/R103).
- R₂ FactReview replication only specified, not run (EXPERIMENT_PLAN.md:85).
- 20-paper pool / gold chain not frozen (R120, R121).
- R003 localization concrete (r003_results.json).

## 1. Top-venue assessment
Borderline, not yet top-venue. Promising metrology paper with a serious baseline-alignment flaw. Non-incremental core is NOT "six components instead of claims" — it is: controlled IO manipulation, paired result-vs-component trust-inflation measurement, validated human gold chains, and evidence that a strong claim-level execution audit misses process invalidity. Without the R₂-vs-R₃ gap, reviewers will reduce it to "FactReview with a more detailed rubric." Top-venue condition: R₂ fair and strong, human validation credible, stop leaning on Study 4 as if correlations make the instrument important.

## 2. FactReview contrast — CONDITIONAL, with a deeper problem
"M₁-invisible by construction" only conditionally sound. FactReview executes the released repo and gives claim-level verdicts; it does not inspect an independent agent's reconstruction path → blind to agent-side substitution. ✓

**But:** if R₂ executes the original released repo while R₃ audits the agent-generated reproduction, R₂ and R₃ measure DIFFERENT OBJECTS. R₂="Supported" + R₃="M₁" does not prove FactReview failed — it proves the released repo supports the claim while the agent reconstructed it wrongly.

**Fix:** define R₁/R₂/R₃ over the SAME reproduction trace. R₁ = number match from agent trace. R₂ = FactReview-style claim verdict over the agent trace/code/output, no component provenance. R₃ = component audit of that same trace. Separately report "original FactReview on released repo" as prior-art calibration.

**Also add R₂₊:** a trivial FactReview extension with data/sample provenance check + hard-coded-number scanner. If R₃ only beats original R₂ but not R₂₊, D1 novelty is much weaker.

## 3. Killer experiment
N=3 enough for vivid mechanism demonstration, NOT enough for main statistical claim. Skeptic: 3/120 is cherry-picked, high-risk papers preselected, adjudicators knew hypothesis, baseline defined so it couldn't see provenance. Fix: report denominator (all R₂ Supported, all R₃ invalid, all M₁/M₂ candidates, random sample of unflagged); blind two adjudicators to hypothesis and R₂/R₃ labels; target 5–8 cases across ≥2 papers and ≥2 modes; report rate + CI, not just "≥3 examples."

## 4. Study 2 causality
Downgrade wording. Causal for "the constructed input package changes agent behavior under this harness," NOT causal for "observability determines reproducibility" in the wild. IO levels experimenter-built, paper selection stratified by predicted slope, several papers have IO₂/IO₃ collapse. Call it a controlled input-sensitivity intervention; causal language limited to within-paper randomized artifact package.

## 5. Study 4
Demote. Defensible as exploratory ecological validation, not main claim. N=20+115 observational; field/year/team controls won't remove selection, fame, data-availability, age, team resources, venue, openness confounds. Positive result licenses "ECRF associated with impact indicators," NOT "reproducibility predicts impact." NeurIPS/ICML: appendix/short exploratory. Scientometrics: main exploratory study if modestly framed.

## 6. Minimum high-lift package
1. Freeze R121 first (20/20, 2 annotators, α gate, adjudication log). Do NOT launch full Study 2 while R121 draft.
2. Full 20×3 IO×2 primary models = 120, frozen scorer+thresholds.
3. One repeat seed on 6 stratified papers: 6×3×2 = 36 extra for ICC/stability.
4. Implement R₂ over the SAME agent traces as R₃; calibrate faithful FactReview on its 35-paper set before main claims.
5. Add R₂₊ provenance/hard-code baseline. No new GPU, high lift.
6. Human-adjudicate all R₂-Supported/R₃-invalid candidates + random controls, blinded.
7. Frontier subset: 6×3×2 = 36 runs (clean IO₃, medium-complexity, boundary).
Do NOT spend next GPU week on Study 4.

## 7. Results-to-claims matrix
| S2 IO | S3 FRR | S4 corr | Licensed claim |
|---|---|---|---|
| Yes | Yes | Yes | Full story: IO-sensitive metrology + trust inflation beyond FactReview-style audit + exploratory impact association |
| Yes | Yes | No | Strong ML measurement paper; no scientometric-impact claim |
| Yes | No | Yes | IO sensitivity + possible scientometric association; FactReview likely already fixes main trust bias. Incremental |
| Yes | No | No | Input-sensitivity instrument only; weak top-venue |
| No | Yes | Yes | Component audit detects trust inflation, but IO mechanism unsupported. Drop causal IO theory |
| No | Yes | No | Narrow audit-method paper; still publishable if R₂/R₃ fair |
| No | No | Yes | Correlation uninterpretable; construct not validated |
| No | No | No | No top-venue claim. Reframe or stop |

## 8. Mock NeurIPS review
- **Summary**: ECRF component-level measurement instrument for agentic reproduction; argues result-level and FactReview-style claim-level audits inflate trust vs component-level.
- **Strengths**: important problem; measurement framing > leaderboard; pilot shows IO sensitivity; concrete localization example; human gold-chain plan appropriate.
- **Weaknesses**: FactReview baseline not run and may measure different object than R₃; "M₁-invisible" overstated (provenance-augmented FactReview straightforward); human validation draft not evidence; Study 4 overclaimed; pilot has scorer revisions, anomalies, small N.
- **Questions**: Are R₂/R₃ on same agent trace? Does R₃ beat provenance-augmented R₂₊? Inter-annotator reliability by component? How were killer cases selected + denominator? Are IO packages standardized enough for causal language?
- **Score**: 5/10 as evidenced; 7/10 if full Study 3 lands with aligned R₂/R₃, R₂₊, blinded adjudication, reliability gates.
- **Confidence**: 4/5.
- **Toward accept**: fair same-object R₂ baseline, R₂₊ ablation, frozen human gold chains with α, full 120-run results, blinded case adjudication with denominators, demoted Study 4.
