# Research Review — v8.1 AI-Agent Metrology of Computational Reproducibility

**Date**: 2026-06-29
**Reviewer**: Codex `gpt-5.5`, xhigh reasoning (external cross-model reviewer)
**Backend**: codex MCP
**threadId**: `019f1188-f6ca-7322-bcbd-b9bd49bfbe4c` (3 rounds; resumable)
**Artifact reviewed**: `refine-logs/COMPLETE_EXPERIMENT_IDEA_V8.1.md` + `refine-logs/EXPERIMENT_PLAN.md` (Block 3a)
**Trace**: `.aris/traces/research-review/2026-06-29_run01/` (rounds 1–3, request + response)

---

## Verdict

**The same-object fix rescues the design onto the plausible 7/10 path.** No remaining fatal structural flaw. The paper can now only be sunk by *empirical* failure (low human reliability, unstable ECRF, R₂₊ tying R₃ with weak fallback, or too few supported-invalid cases). As originally written it was **5/10** (borderline) with a decisive baseline-alignment flaw; the revised design reaches **7/10** if results land and reliability gates pass; **6.5–7** if R₂₊ ties R₃ but the continuous-measurement fallback is shown decisively.

The non-incremental core is **not** "six components instead of claims" — it is: controlled IO manipulation, paired result-vs-component trust-inflation measurement, validated human gold chains, and evidence that a strong claim-level execution audit misses process invalidity. Without the R₂-vs-R₃ gap, reviewers will reduce it to "FactReview with a more detailed rubric."

---

## Round 1 — the flaw that almost sank it

**Baseline-alignment flaw (decisive).** The original design had R₂ = FactReview on the *released repo* while R₃ = component audit of the *agent's reconstruction* — **two different objects**. "R₂=Supported, R₃=M₁" then proves only that the released repo supports the claim while the agent reconstructed it wrongly, NOT that FactReview failed. Reviewer would reject.

Secondary: (a) "M₁-invisible by construction" overstated — a provenance-augmented FactReview (R₂₊) is trivial; (b) N=3 killer cases too few + cherry-pick risk; (c) Study 2 "causal" overclaimed; (d) Study 4 overclaimed; (e) human validation draft, not evidence.

## Round 2 — the fix (accepted)

**Same-trace regimes.** R₁/R₂/R₂₊/R₃ all score the **same agent reproduction trace** at a given IO level:
- **R₁** result-level (agent's numbers vs paper's, within tolerance)
- **R₂** FactReview-style claim verdict over the agent's trace (claim extraction → lit grounding → execute agent's code K=3 wrapper repair → 4-status), no component-provenance scoring
- **R₂₊** R₂ + two trivial bolt-ons: data/sample provenance check + hard-coded-paper-number scanner (the "FactReview extended" baseline reviewers will demand)
- **R₃** ECRF component-level audit of the same trace (Data→Sample→Indicator→Model→Result→Claim, task-contingent)
- **Prior-art calibration cell (separate)**: original FactReview on released repo + 35-paper calibration — reported as prior-art behavior, NOT a head-to-head baseline.

Killer claim becomes fair: **R₂="Supported" (agent's numbers match + claim well-formed) but R₃=M₁/M₂ (agent substituted data / hard-coded) on the same trace** = trust inflation.

**D1 fallback (pre-registered):** if FRR(R₂₊) ≈ FRR(R₃), reframe D1 as the **continuous per-component fidelity score** that enables Study 2's Component×IO sensitivity and Study 4's scientometric correlation (R₂₊ produces binary flags, not continuous per-component scores). NOT defensible to claim "R₃ beats extended FactReview" if FRR equal. D1 carried by Study 2 + reliability + localization, NOT Study 4.

**Study 2** downgraded to "controlled input-sensitivity intervention" (causal language limited to within-paper randomized artifact package). **Study 4** demoted to exploratory ecological validation (appendix for NeurIPS/ICML; modest main study only for Scientometrics).

## Round 3 — killer-case operationalization + final TODO

**Killer panel = "process-invalid supported cases"**, split into two reported strata (NOT collapsed):
- **S-exact**: numeric match within tolerance + R₃ process-invalid (M₂ hard-code expected to populate; M₁ rare here, ~1–5%)
- **S-directional**: directional/qualitative match + R₃ process-invalid (M₁ substitution expected here, ~10–25%)

**Fair-baseline granularity rule (must pre-register before scoring):** R₂ may call "Supported" only at the granularity of the extracted claim's evidence target. Numeric/table-cell/effect-size claims matched only by sign → "Partially-supported," NOT "Supported." Report Supported-exact and Supported-directional as separate support types. Reviewers accept directional cases only if no post-hoc downgrading of numeric claims.

Headline metric: **P(R₂/R₂₊ = Supported | R₃ = process-invalid)**, overall + split by stratum, bootstrap CI, full denominator, blinded two-adjudicator.

---

## Final prioritized TODO (execution order)

| # | Task | Unblocks | Cost | Priority |
|---|---|---|---|---|
| 1 | Rewrite protocol: lock same-trace R1/R2/R2+/R3, S-exact/S-directional, R2 claim-granularity rules | Prevents strawman critique | 0 GPU, 0.5 day | MUST |
| 2 | Fill paper slot #20 + freeze R120 pool | Study 2 launch | 0 GPU, 0.5–1 day | MUST |
| 3 | Freeze R121 gold chains: 20/20, 2 annotators, component α/ICC gates, adjudication log | All validity claims | Human 2–4 wk | MUST |
| 4 | Lock scoring code, thresholds, tolerances, claim-extraction schema before runs | Post-hoc-scoring critique | 0 GPU, 1–2 days | MUST |
| 5 | Implement trace logging (agent code, chosen data, provenance, outputs, paper-value occurrences) | R2+/R3 + adjudication | Low, 1–2 days | MUST |
| 6 | Implement R1/R2/R2+/R3 scorers on same trace; pilot on existing 30 runs | Study 3 feasibility | Low API, 2–4 days | MUST |
| 7 | Prior-art calibration cell (original FactReview on released repos / 35-paper) | R2 fidelity to prior art | API+eng, 3–7 days | SHOULD |
| 8 | Pre-register adjudication packet (denominator, random controls, blinding, labels) | Killer credibility | 0 GPU, 0.5 day | MUST |
| 9 | Run full Study 2: 20×3 IO×2 models = 120 traces | Core dataset | ~80 GPU-h + API | MUST |
| 10 | Repeat-seed stability: 6×3×2 = 36 traces | ICC/stability | ~25 GPU-h + API | MUST |
| 11 | Score all traces R1/R2/R2+/R3; FRR ladder + CIs | Main result table | Low compute/API | MUST |
| 12 | Blinded adjudication (all supported-invalid, all M1/M2 flags, random valid controls) | Killer panel + P/R | Human 1–2 wk | MUST |
| 13 | R2+ ablation (provenance-only, hard-code-only, both) | R3 marginal value | 0 GPU | SHOULD |
| 14 | Frontier subset: 6×3 IO×2 frontier = 36 traces | Boundary | API | SHOULD |
| 15 | Sensitivity (thresholds, exact vs directional, exclude boundary/data-sub) | Robustness | 0 GPU | MUST |
| 16 | Exploratory Study 4 correlation (demoted) | Appendix | 0 GPU, queries | NICE/SHOULD |
| 17 | Write NeurIPS D&B paper around Studies 1–3; Study 4 appendix | Submission | 0 GPU | MUST |

**Stop-the-presses gates:** (i) do NOT run full Study 2 before R121 frozen; (ii) do NOT claim R₃ beats FactReview unless R₂/R₂₊ are same-trace; (iii) do NOT count directional support unless claim granularity pre-registered.

---

## Results-to-claims matrix (with R₂₊ column)

| S2 IO | S3 ladder | R₂₊ vs R₃ | S4 | Licensed claim |
|---|---|---|---|---|
| Yes | R1>R2>R2+>R3 | R3 beats R2+ | Pos | Full strong: ECRF reliable, IO-sensitive, beats extended FactReview, exploratory association |
| Yes | R1>R2>R2+>R3 | R3 beats R2+ | Null | Strong NeurIPS; no impact claim |
| Yes | R1>R2>R2+≈R3 | Tie | Pos | ECRF continuous measurement instrument; R₂₊ enough for binary detection |
| Yes | R1>R2>R2+≈R3 | Tie | Null | Publishable if reliability strong: input-sensitive component metrology, not superior detector |
| Yes | R1>R2, R2+≈R3≈low | Tie | Any | Trivial provenance checks fix most trust inflation; ECRF for measurement/localization only |
| Yes | R1>R2, R2+>R3 absent | R3 no better | Any | D1 detection fails; input-sensitivity + instrument proposal. Borderline |
| No | R ladder holds | R3 beats R2+ | Any | Trust-inflation audit survives; IO mechanism doesn't |
| No | R ladder weak | Any | Pos | Study 4 insufficient; weak top-venue |
| No | No ladder | R2+≈R3 | Null | No main claim; reframe as negative pilot/method note |

---

## NeurIPS D&B paper outline (revised)

1. **Intro** — result-level reproducibility is an invalid trust signal; ECRF as component-resolved metrology, same-trace audit ladder, controlled input-sensitivity.
2. **Related Work** — FactReview, execution-based verification, agent benchmarks, reproducibility studies; position R₂/R₂₊.
3. **Measurement Model** — evidence chain, ECRF/FRR/M₁–M₄, R₁/R₂/R₂₊/R₃ on same trace.
4. **Dataset & Protocol** — 20 papers, IO packages, 2 models, isolation, randomization, gold chains, reliability gates.
5. **Study 1: Construct & Reliability** — agreement, ICC, correlations, non-degeneracy.
6. **Study 2: Controlled Input Sensitivity** — mixed-effects Component×IO; main fig = component slopes.
7. **Study 3: Trust Inflation Ladder** — FRR(R₁/R₂/R₂₊/R₃), paired tests, bootstrap CI, R₂₊/R₃, localization.
8. **Failure-Mode Adjudication** — denominators, blinded, M₁–M₄ rates, case panels.
9. **Robustness** — frontier, threshold sensitivity, R₃ vs overbuilt R₃′, scorer stability.
10. **Exploratory Ecological Validation** — appendix/short; ECRF↔impact, clearly exploratory.

**Figures:** Fig 1 same-trace ladder; Fig 2 ECRF schema + IO packages; Fig 3 Component×IO slopes; Fig 4 FRR ladder + CI; Fig 5 M₁/M₂ case panel. **Tables:** T1 pool + IO feasibility; T2 reliability/ICC by component; T3 R₂/R₂₊/R₃ paired; App Fig Study 4.

---

## Consensus

- **Contribution is top-venue-credible** IF the same-trace R₂/R₂₊/R₃ ladder lands + reliability gates pass + killer panel populated (M₂ + coarse M₁ carry it; exact-M₁ rare is expected and OK).
- **R₂₊ is the real novelty threat** — pre-register FRR(R₂₊) vs FRR(R₃) and the continuous-measurement fallback.
- **Study 4 demoted** to exploratory; do not spend GPU on it until Studies 2–3 land.
- **Study 2** is "controlled input-sensitivity," not population-causal.
- **Reliability (R121 gold chains, per-component α/ICC, repeat seed) is the load-bearing wall** — without it the continuous-measurement fallback collapses.

## Key changes to apply to the plan docs

1. EXPERIMENT_PLAN Block 3a: rewrite R₂ to be **same-trace** (agent's code/data/output, not released repo); add **R₂₊** regime; move original-FactReview-on-released-repo to a **prior-art calibration cell**; add the **S-exact / S-directional** killer split + claim-granularity pre-registration rule.
2. Add **D1 fallback** (continuous per-component score) as pre-registered.
3. Downgrade Study 2 causal language → "controlled input-sensitivity intervention."
4. Demote Study 4 → exploratory (appendix for NeurIPS/ICML).
5. Add reliability-gate stop-the-presses rules + the 17-item TODO.

These edits will be applied to `refine-logs/EXPERIMENT_PLAN.md` and `refine-logs/COMPLETE_EXPERIMENT_IDEA_V8.1.md` in a follow-up commit on dev.
