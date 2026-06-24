# Experiment Tracker — Evidence-Chain Theory (v7.2)

**Plan**: refine-logs/EXPERIMENT_PLAN.md (v7.2)
**Theory**: IO → ECRF → TCE; propositions P1–P4; Studies 1–3
**Updated**: 2026-06-24

---

## Reference Tables

### Task Type

| Code | Meaning | Numerical Accuracy |
|------|---------|--------------------|
| STRICT | Same data, same sample, same model; numerical identity | High — correctness |
| DATA-SUB | Different data source; direction/mechanism consistency | Reference-only |
| METHOD | Reproduce method only; no numerical targets | N/A |
| CLAIM-ROBUST | New data tests original conclusions | External validity |

### IO Level (Study 2 / 3)

| Level | Observability | Allowed Input | External Access |
|-------|-------------|--------------|-----------------|
| IO₁ | Low — narrative only | Paper text | None |
| IO₂ | Medium — structured docs, no executable code | Paper + data dictionary + variable docs + sample notes | Controlled raw data where task requires; **no original code** |
| IO₃ | High — full executable materials | Paper + data + original code | Provided materials only |

### Evaluation Regime (Study 3)

| Regime | Trust Signal | Expected Inflation |
|--------|-------------|---------------------|
| R₁ Result-level | Numbers match → trust | High |
| R₂ Aggregate composite | Composite > threshold → trust | Moderate |
| R₃ Component audit (task-contingent) | All task-critical components pass, no break → trust | Low |

### Milestone naming (stable, decoupled from historical "M0–M6")

| Code | Meaning | Status |
|------|---------|--------|
| **C0** | Historical calibration evidence (retained R000–R007) | DONE |
| **S1** | Study 1 — Construct validation / ECRF dimensionality (re-analysis) | TODO |
| **P1** | Pilot IO manipulation (mini Study 2, 5 papers) | TODO |
| **S2** | Study 2 — Full IO → ECRF experiment | TODO |
| **S3** | Study 3 — Trust calibration + audit (main contribution) | TODO |
| **R**  | Robustness checks (simplicity, frontier, negative-result boundary) | TODO |

> Note: the historical "M1 10-paper full benchmark" (Gemma, 2026-06-18) is **not** this P1. It lives under C0 as calibration evidence. Do not conflate.

---

## Completed Runs (C0 — calibration evidence, retained)

| Run ID | Study | Task Type | Paper | System | Result | Notes |
|--------|-------|-----------|-------|--------|--------|-------|
| R000 | C0 | SIM | Wu2019 | 4 simulated scenarios | DONE | 4 failure modes distinct; spurious detection working |
| R001 | C0 | DATA-SUB | Wu2019 | DeepSeek-V4-Pro, C1 | DONE | Direction NEGATIVE ✓; coef=-0.0093; L3(ds) |
| R001b | C0 | DATA-SUB | Wu2019 | DeepSeek-V4-Pro + Codex pre-val | DONE | PASS; 8 evidence modules preserved |
| R002 | C0 | STRICT | Petersen2024 | DeepSeek-V4-Pro | DONE | **D3=8/8 (100%)** |
| R003 | C0 | COMPONENT_DIAG | Arts2021 | DeepSeek-V4-Pro | DONE | Error localized to formula lines 233–236 |
| R004 | C0 | STRICT | Park2023 | DeepSeek-V4-Pro | DONE | **D3=6/6 (100%)** |
| R005 | C0 | METHOD | Zhao2025 | DeepSeek-V4-Pro | DONE | Overall=0.98 |
| R007 | C0 | STRICT | Bentley2023 | DeepSeek-V4-Pro | DONE | **D3=9/9 (100%)** |

---

## TODO Runs — v7.2 aligned

### Phase 0: Pre-run validation (blocks P1)

| Run ID | Milestone | Purpose | Output | Priority | Status |
|--------|-----------|---------|--------|----------|--------|
| R095 | P1 | Finalize scoring codebook | Define DSF/SMF/INF/MDF/RRF/CRS/PRF + TIR/TCE, thresholds, component applicability per task type — see `PRE_RUN_VALIDATION.md` | MUST | DONE (approved) |
| R096 | P1 | IO package template | Specify IO₁/IO₂/IO₃ folder contents + IO-boundary audit rule — see `PRE_RUN_VALIDATION.md` | MUST | DONE (approved) |
| R097 | P1 | Isolated workspace test | Container `--network none` + filesystem jail + `--user uid:gid` + `--read-only` + tmpfs. **7/7 gates PASS** (`test_r097_isolation.py`). See `PRE_RUN_VALIDATION.md` + `R097_ISOLATION_REPORT.md` | MUST | DONE |
| R097b | P1 | DS execution image | `sciscigpt-ds:0.1` Docker image (numpy/pandas/scipy/statsmodels/sklearn/pyarrow/openpyxl/matplotlib/networkx/tqdm). Build-time net ok, runtime `--network none`. **7/7 gates PASS + DS-functional OLS**. Dockerfile: `docker/sciscigpt-ds/Dockerfile`, digest `2ec5ab91...`. See `R097b_R098_FINAL_REPORT.md` | MUST | DONE |
| R098 | P1 | Pilot gold-chain annotation | 1 primary + 1 adjudication × 5 papers. **MinerU adjudication DONE** — see `R098_ADJUDICATION.md`. maddi estimator corrected to GLM; funk2017 N / maddi window / bikard β pinned | MUST | DONE |
| R099 | P1 | Pilot paper selection | **rev2: Petersen/Arts/funk2017/maddi/bikard** (schaper2025 → backup; only 1 boundary case). Approved. See `PILOT_PAPERS.md` | MUST | DONE (approved) |

### Phase 1: Immediate re-analysis (parallel, no compute)

| Run ID | Milestone | Study | Purpose | Split | Metrics | Priority | Status |
|--------|-----------|-------|---------|-------|---------|----------|--------|
| R110 | S1 | S1 | ECRF dimensionality re-analysis | C0 16 papers | Disagreement (>0.15), localization (>0.60), ρ-matrix (<0.75) | MUST | TODO |

### Phase 2: Mini IO pilot (P1)

| Run ID | Milestone | Study | Purpose | System | Split | Metrics | Priority | Status |
|--------|-----------|-------|---------|--------|-------|---------|----------|--------|
| R100 | P1 | S2 | Mini pilot — IO₁ | 5 papers × IO₁ × 2 models (qwen3-32b, deepseek-v4-pro) | 10 runs DONE | ECRF v0 (R100) + v1 rescoring (R100b). v0=0.79 -> v1=0.49 (IO1 now LOW). See `R100_REPORT.md` + `R100B_REPORT.md` | MUST | DONE |
| R100b | P1 | S2 | ECRF v1 rescoring + B1 adjudication | existing 10 R100 outputs, no new runs | — | v1 weights+gates; 3/3 B1 CONFIRMED. See `R100B_REPORT.md` | MUST | DONE |
| R101b | P1 | S2 | ECRF v2 rescoring | existing 10 R101 IO2 outputs, no new runs | — | v2 recognition (file-load/computed-sample/broad-result); IO2 v2=0.552 > IO1 0.490; data-using 0.631 > synth 0.500; gate-c no misfire. See `R101B_REPORT.md` | MUST | DONE |
| R101 | P1 | S2 | Mini pilot — IO₂ | 5 papers × IO₂ × 2 models (qwen3-32b, deepseek-v4-pro) | 10 runs DONE | ECRF v1: overall 0.483 (vs IO1 0.490, flat); Result 0.35->0.40 UP; gate-c no misfire. See `R101_REPORT.md` | MUST | DONE (criterion partial) |
| R102 | P1 | S2 | Mini pilot — IO₃ | 5 papers × IO₃ × 2 models | 5 pilot | Per-component ECRF | MUST | READY — scorer v2 validated (R101b) |
| R103 | P1 | S2 | Mini-pilot green-light gate | Aggregate R100–R102 | 30 runs | 4 gates (below) | MUST | TODO |

**R103 green-light gates (pre-registered):**
- **Gate 1 — IO manipulation works**: mean ECRF(IO₁) < mean ECRF(IO₃) in ≥4/5 papers (or majority of model×paper pairs). *If Gate 1 fails → IO manipulation not valid; fix IO conditions before scaling. Do not proceed to S2.*
- **Gate 2 — Component heterogeneity**: ≥2 components show different IO slopes (interaction visible, not flat).
- **Gate 3 — Audit disagreement exists**: ≥1 run where result-level success ≠ component-level validity.
- **Gate 4 — Break detection feasible**: ≥1 candidate B₁–B₄ break with audit trace.

Pass rule: **≥3/4 gates** → scale to S2. Gate 1 is mandatory.

### Phase 3: Full study preparation (S2 prep, only after R103 pass)

| Run ID | Milestone | Purpose | Split | Metrics | Priority | Status |
|--------|-----------|---------|-------|---------|----------|--------|
| R120 | S2 | 20-paper full pool finalization + pre-annotation | 20 papers | Observability-stratified, pre-agent | MUST | TODO |
| R121 | S2 | Layer 1 gold chain (full) | 2 annotators × 20 papers | 20 papers | Component-stratified α | MUST | TODO — blocks S3 |

### Phase 4: Full Study 2 (S2)

| Run ID | Milestone | Study | Purpose | Split | Metrics | Priority | Status |
|--------|-----------|-------|---------|-------|---------|----------|--------|
| R122 | S2 | S2 | Study 2 full — IO₁ | 20 × IO₁ × 2 models (40) | Per-component ECRF | MUST | TODO |
| R123 | S2 | S2 | Study 2 full — IO₂ | 20 × IO₂ × 2 models (40) | Per-component ECRF | MUST | TODO |
| R124 | S2 | S2 | Study 2 full — IO₃ | 20 × IO₃ × 2 models (40) | Per-component ECRF | MUST | TODO |
| R125 | S2 | S2 | Study 2 analysis | 120 runs | Monotonic ECRF, Component×IO mixed-effects (H1, H2) | MUST | TODO |

### Phase 5: Study 3 — main contribution (S3, C1)

| Run ID | Milestone | Study | Purpose | Split | Metrics | Priority | Status |
|--------|-----------|-------|---------|-------|---------|----------|--------|
| R130a | S3 | S3 | Mechanical regime scoring — apply R₁/R₂/R₃ rules to all outputs | All Study 2 runs × 3 | Regime-level trust labels | MUST | TODO |
| R131 | S3 | S3 | B₁–B₄ automated screening | Flagged + unflagged sample | Rule precision/recall | MUST | TODO |
| R132 | S3 | S3 | Human validity adjudication (Layer 2) | 2 adjudicators | Confirmed-break ≥5, ≥2 types; recall on unflagged | MUST | TODO — depends R121 |
| R130b | S3 | S3 | Regime scoring against human labels | R130a ∪ R132 | TIR per regime, TCE | MUST | TODO |
| R133 | S3 | S3 | Study 3 analysis | Aggregate | TIR(R₁)>0; TIR(R₁)>TIR(R₃) McNemar p<0.05 (H3, H4) | MUST | TODO — **main result** |

### Phase 6: Robustness (R)

| Run ID | Milestone | Study | Purpose | Split | Metrics | Priority | Status |
|--------|-----------|-------|---------|-------|---------|----------|--------|
| R140 | R | S3 | Simplicity: R₃ vs overbuilt R₃′ (all-6-must-pass) | Re-score | TIR, deflation, localization | MUST | TODO |
| R141 | R | S3 | Simplicity: R₃ vs threshold-lowered R₂ | Re-score | Localization ≠ R₃ (defends anti-claim A2) | MUST | TODO |
| R150 | R | S2 | Frontier — GPT-4o | 8–10 × 3 IO | ECRF slope, TIR(R₁) | HIGH | TODO |
| R151 | R | S2 | Frontier — Claude Sonnet/Opus | 8–10 × 3 IO | ECRF slope, TIR(R₁) | HIGH | TODO |
| R152 | R | S2 | Frontier consistency analysis | Aggregate | IO direction consistent; TIR>0 (defends A3) | HIGH | TODO |
| R153 | R | S2 | **Negative-result boundary check** — inspect any non-monotonic ECRF | Any S2 paper failing monotonicity | Diagnose: IO₃ overload vs code-complexity vs noisy docs; report as boundary condition, not failure | MUST | TODO |

### Phase 7: Figures and tables

| Run ID | Milestone | Purpose | Output | Priority | Status |
|--------|-----------|---------|--------|----------|--------|
| R160 | — | Figures + heatmaps | ECRF×IO×Component, break-type matrix | HIGH | TODO |
| R161 | — | Reliability tables (Layer 1/2) | Component α, rule P/R | MUST | TODO |

---

## Negative-Result Handling (pre-registered boundary condition)

If IO₁ → IO₃ monotonicity **fails** at the full-Study-2 level (R153), the protocol is:
1. Inspect whether failure is (a) agent overload under IO₃, (b) code-execution complexity, or (c) noisy/contradictory documentation.
2. Report as a **boundary condition**, not hide it. The theoretical value: *"More observability may increase cognitive/tool complexity, producing non-monotonic ECRF for weaker agents"* — this is itself a contribution about the interaction between IO and agent capability.
3. If the effect concentrates in weaker models, fold into the frontier-robustness narrative (R-block).

---

## Summary (reconciled counts)

| Priority | Total | Done | TODO | Notes |
|----------|-------|------|------|-------|
| MUST | 32 | 8 | 24 | includes Phase-0 pre-run (R095–R099), R130 a/b split, R153 boundary |
| HIGH | 5 | 0 | 5 | frontier + figures |
| **Active TODO** | **29** | — | 29 | MUST 24 + HIGH 5 |

> Breakdown of the 24 MUST-TODO: Phase 0 (R095–R099) = 5 · Phase 1 (R110) = 1 · Phase 2 (R100–R103) = 4 · Phase 3 (R120–R121) = 2 · Phase 4 (R122–R125) = 4 · Phase 5 (R130a/R130b/R131/R132/R133) = 5 · Phase 6 (R140/R141/R153) = 3 · Phase 7 (R161) = 0 counted here → figures HIGH. Net = 24.

## Blockers

- **R095–R099** (pre-run validation + pilot gold chain) block R100–R102. **R098 pilot gold chain is required before any ECRF scoring** — without it, R103 has no trusted gold to score against.
- **R121** (Layer 1 full annotation) blocks S3 (R130b/R133) — human annotation is the critical path, not compute.
- **R103** is the gate: do not scale a broken IO manipulation.

## Next 3 runs to launch (revised)

1. **R110** — Study 1 re-analysis on existing C0 data (zero compute; unblocks calibration narrative immediately)
2. **R099 → R098** — finalize 5 pilot papers (`PILOT_PAPERS.md`) + draft pilot gold chain (this turn)
3. **R095–R097** — scoring codebook + IO package template + isolated-workspace test (prepares R100–R102)

> R120 (20-paper full pool) is **deliberately deferred** to Phase 3 — no full-pool pressure before the mini pilot passes.

## Archived (SciSciGPT / SciSciBench legacy)

Prior M1–M6 benchmark rows and June 1–11 SciSciBench runs are in git history. They motivate the paper (L3 true capability ~0.3–0.5) but are no longer headline experiments under v7.2.
