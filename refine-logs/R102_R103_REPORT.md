# R102 + R103 Report — Mini Study 2, IO₃ + Green-light Gate (2026-06-24)

**R102**: 5 papers × IO₃ × 2 models = 10 runs. IO₃ = paper + docs + raw_data + original/reference code. Scorer **v2 exactly as R101b** (no changes; v1 weights + gates). Isolated container unchanged (no-network, filesystem jail, per-run workdir). R103 aggregates R100 (IO₁) + R101b (IO₂) + R102 (IO₃), all re-scored with v2 for consistency.

## R102 run status — 10/10

All DONE, exit 0, **network blocked on all 10**, no leakage, no cross-condition artifacts exposed (IO₃ packages contain only paper/docs/raw_data/original_code; no IO₁/IO₂ outputs, no sibling folders, no benchmark pool).

## R102 v2 scores + IO₃ code-usage

| Paper | Model | v2 | used ref? | modified? | synth despite IO₃? | Caps |
|---|---|---|---|---|---|---|
| petersen2024 | qwen3-32b | 0.600 | no | no | no | a no-exec-result |
| petersen2024 | deepseek | 0.600 | no | no | no | a no-exec-result |
| arts2021 | qwen3-32b | **0.825** | no | no | no | none |
| arts2021 | deepseek | 0.500 | yes | no | **yes** | c synthetic |
| funk2017 | qwen3-32b | 0.900 | yes | no | no | none |
| funk2017 | deepseek | 0.750 | no | no | no | none |
| maddi2024 | qwen3-32b | 0.500 | no | no | no | c synthetic |
| maddi2024 | deepseek | 0.500 | no | no | no | a, c |
| bikard2013 | qwen3-32b | **1.000** | no | no | no | none |
| bikard2013 | deepseek | 0.950 | no | no | no | none |

**IO₃ code-usage (recorded per your spec):**
- **Used original/reference code: 2/10** (arts×deepseek, funk×qwen). Most agents wrote their own code rather than importing the reference — an interesting finding (reference code availability didn't automatically translate to usage).
- **Modified reference code: 0/10.**
- **Synthesized data despite real IO₃ materials: 1/10** (arts×deepseek — a B₁ candidate at the highest observability level, the most diagnostic break case).
- **Embedded paper-reported values directly: 0/10** at IO₃ (B₂ gate (e) fired on 0; agents labeled comparisons as PAPER_REPORTED).

## R103 — IO monotonicity (all v2)

**Overall: IO₁ 0.497 < IO₂ 0.552 < IO₃ 0.713** ✅ monotonic.

**Per-paper (v2):**

| Paper | IO₁ | IO₂ | IO₃ | IO₁<IO₃? |
|---|---|---|---|---|
| arts2021 | 0.487 | 0.500 | 0.662 | ✅ |
| bikard2013 | 0.500 | 0.525 | 0.975 | ✅ |
| funk2017 | 0.500 | 0.550 | 0.825 | ✅ |
| maddi2024 | 0.500 | 0.500 | 0.500 | ✗ (flat — no data at any level) |
| petersen2024 | 0.500 | 0.688 | 0.600 | ✅ (but IO₂>IO₃ anomaly) |

**Gate 1 (original criterion: IO₁<IO₃ in ≥4/5 papers): ✅ PASS (4/5).** Also passes on the majority of model×paper pairs (8/10).

### Anomaly notes (not gate failures)
- **maddi2024 flat (0.500/0.500/0.500)**: Publons data unavailable at every IO level → agent always synthesizes → gate (c) caps at 0.50. This is the expected boundary behavior for a paper with no obtainable data; the IO manipulation can't operate without data. Honest boundary case.
- **petersen IO₂ (0.688) > IO₃ (0.600)**: at IO₃ both petersen runs hit gate (a) "no-exec-result" (the agent's execution didn't emit recognized result evidence — likely over-engineering against the reference code). IO₁<IO₃ still holds (0.500<0.600). Worth investigating in S2 but not a gate failure.

## R103 component heterogeneity (Gate 2)

| Component | IO₁ | IO₂ | IO₃ | slope(1→3) |
|---|---|---|---|---|
| data_source | 0.50 | 0.90 | 0.90 | **+0.40** |
| result | 0.50 | 0.55 | 0.90 | **+0.40** |
| model | 0.85 | 0.90 | 0.65 | −0.20 |
| sample | 1.00 | 1.00 | 0.95 | −0.05 |
| indicator | 1.00 | 1.00 | 0.95 | −0.05 |
| claim | 0.95 | 1.00 | 0.90 | −0.05 |

**Gate 2 (≥2 components |slope|>0.1): ✅ PASS (3 components)** — data_source and result rise strongly with IO; model dips at IO₃ (a recognition artifact worth a v3 look, but heterogeneity is clearly present). The asymmetric reconstructability (P2) is visible: data_source/result are IO-sensitive; indicator/claim are not.

## R103 disagreement (Gate 3)

**7 result-vs-component disagreement cases across 30 runs** (components understood but Result=0). **Gate 3 ✅ PASS.** This is the trust-inflation mechanism (P3) in miniature — the core theory phenomenon.

## R103 evidence-break feasibility (Gate 4)

Across 30 runs: **B₁=19, B₃=11, B₄=7, B₂=5** (42 candidates). **B₁ confirmed (R132-lite): 19.** **Gate 4 ✅ PASS.** The detection rules fire across all IO levels; the IO₃ B₁ (arts×deepseek, synth despite real materials) is the strongest single break case.

## R103 verdict — **ALL 4 GATES PASS ✅**

| Gate | Criterion | Result |
|---|---|---|
| G1 | IO₁<IO₃ in ≥4/5 papers | ✅ 4/5 |
| G2 | ≥2 components IO-sensitive | ✅ 3 |
| G3 | ≥1 result≠component disagreement | ✅ 7 |
| G4 | ≥1 B₁–B₄ candidate | ✅ 42 |

**R103 pass rule (≥3/4, G1 mandatory) is met. The IO→ECRF manipulation is validated.**

## Recommendation — proceed to full Study 2 (S2)

The mini Study 2 pilot validates the core mechanism: information observability causally drives evidence-chain reconstruction fidelity (IO₁ 0.497 → IO₂ 0.552 → IO₃ 0.713), asymmetrically across components (data_source/result IO-sensitive; indicator/claim not), with measurable trust-inflation (7 disagreement cases) and feasible break detection (42 candidates, 19 B₁ confirmed).

**Green-light for S2** (full 20-paper × 3 IO × 2 model = 120-run Study 2), gated on:
1. **R120** — finalize the 20-paper pool (pre-annotated, observability-stratified) before any agent run.
2. **R121** — Layer 1 full gold-chain annotation (2 annotators × 20 papers), the human-validation critical path.
3. Carry forward scorer v2 unchanged (do NOT implement v3 line-level DATA_SUB before S2 — per your instruction).

### Known anomalies to monitor in S2 (not blockers)
- Data-unavailable papers stay flat across IO (maddi) — stratify the 20-paper pool to ensure each IO level has papers with constructable materials.
- petersen IO₂>IO₃ execution-artifact — investigate whether reference-code availability causes over-engineering at IO₃ for STRICT papers.
- model component dip at IO₃ — v3 recognition fix candidate (post-S2).

## Artifacts

- `scripts/run_v72_pilot.py` — extended for IO₃ (build_prompt_io3, original_code into workdir)
- `scripts/r102_r103_analysis.py` — R102 v2 scoring + IO₃ code-usage + R103 4-gate aggregation
- `refine-logs/r102/` — 10 IO₃ run JSONs + responses + `r102_r103_aggregation.json`
- `refine-logs/R102_R103_REPORT.md` — this report
