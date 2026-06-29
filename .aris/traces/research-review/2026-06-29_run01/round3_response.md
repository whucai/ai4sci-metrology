# Round 3 Response (Codex gpt-5.5, xhigh)
**threadId**: 019f1188-f6ca-7322-bcbd-b9bd49bfbe4c

## Q1: Killer operationalization — sound, with the granularity rule
S-exact / S-directional split is sound IF not collapsed rhetorically. S-exact = vivid subcase; S-directional = common scientific-claim subcase.

**Fair-baseline line:** R₂ may call "Supported" only at the granularity of the extracted claim's evidence target. Pre-register claim granularity before scoring.
- Directional support legitimate only when the claim is itself directional/coarse, OR the claim extractor decomposes a broader claim into a directional subclaim BEFORE seeing outcomes.
- If paper claim is numeric/table-cell/effect-size-specific, matching only sign = "Partially-supported" at best, NOT "Supported."
- Agent says "positive & significant" but paper claims "β=0.099, p<0.01" → R₂ may support the directional subclaim, NOT the numeric claim.
- Substitute-data + same qualitative conclusion = real trust inflation ONLY if R₂'s evidence target was qualitative/directional from the start.
- Report Supported-exact and Supported-directional as separate support types. Don't let directional cases inflate the exact-match killer.
- Reviewers accept directional cases IF they see no post-hoc downgrading of numeric claims.

## Q2: Final prioritized TODO (execution order)
| # | Task | Unblocks | Cost | Priority |
|---|---|---|---|---|
| 1 | Rewrite protocol: lock same-trace R1/R2/R2+/R3, S-exact/S-directional, R2 claim-granularity rules | Prevents baseline/strawman critique | 0 GPU, 0.5 day | MUST |
| 2 | Fill paper slot #20 + freeze R120 pool | Full Study 2 launch | 0 GPU, 0.5–1 day | MUST |
| 3 | Freeze R121 gold chains: 20/20, 2 annotators, component α/ICC gates, adjudication log | All main validity claims | Human 2–4 weeks | MUST |
| 4 | Lock scoring code, thresholds, tolerances, claim-extraction schema before runs | Prevents post-hoc scoring critique | 0 GPU, 1–2 days | MUST |
| 5 | Implement trace logging: agent code, chosen data, provenance, outputs, paper-value occurrences | R2+/R3 + blinded adjudication | Low compute, 1–2 days | MUST |
| 6 | Implement R1/R2/R2+/R3 scorers on same trace; pilot on existing 30 runs | Study 3 feasibility | Low API, 2–4 days | MUST |
| 7 | Prior-art calibration cell: original FactReview-style on released repos / 35-paper calibration | Shows R2 fidelity to prior art | API+eng, 3–7 days | SHOULD |
| 8 | Pre-register adjudication packet: denominator, random controls, blinding, case labels | Killer credibility | 0 GPU, 0.5 day | MUST |
| 9 | Run full Study 2: 20×3 IO×2 models = 120 traces | Core dataset | ~80 GPU-h + API | MUST |
| 10 | Repeat-seed stability: 6×3 IO×2 models = 36 traces | ICC/metric stability | ~25 GPU-h + API | MUST |
| 11 | Score all traces R1/R2/R2+/R3; FRR ladder + CIs | Main result table | Low compute/API | MUST |
| 12 | Blinded adjudication: all supported-invalid candidates, all M1/M2 flags, random valid controls | Killer panel + precision/recall | Human 1–2 weeks | MUST |
| 13 | R2+ ablation: provenance-only, hard-code-only, both | Tests whether R3 adds beyond trivial checks | 0 GPU | SHOULD |
| 14 | Frontier subset: 6×3 IO×2 frontier = 36 traces | Boundary condition | API | SHOULD |
| 15 | Sensitivity: thresholds, exact vs directional, excluding boundary papers, excluding data-sub tasks | Reviewer robustness | 0 GPU | MUST |
| 16 | Exploratory Study 4 correlation, demoted | Appendix/ecological | 0 GPU, data queries | NICE/SHOULD (Scientometrics) |
| 17 | Write NeurIPS D&B paper around Studies 1–3; Study 4 in appendix | Submission | 0 GPU | MUST |

**Stop-the-presses gates:** do NOT run full Study 2 before R121 frozen; do NOT claim R3 beats FactReview unless R2/R2+ are same-trace; do NOT count directional support unless claim granularity pre-registered.

## Q3: Remaining fatal structural flaw?
**No remaining fatal structural flaw.** Paper can only be sunk by empirical failure: low human reliability, unstable ECRF, R₂₊ matching R₃ with weak fallback evidence, or too few supported-invalid cases.

**Convergence reached.** threadId 019f1188-f6ca-7322-bcbd-b9bd49bfbe4c saved for future resumption.
