---
name: evidence-chain-theory-v7-2
description: "UTD-targeted paper reframing: Evidence-Chain Theory of AI Reproduction Auditing (v7.2, 2026-06-24), 4 propositions, 3 studies, IO→ECRF→TCE theoretical chain"
metadata: 
  node_type: memory
  type: project
  originSessionId: 3e2728a3-da23-4f38-843c-43c63e2a1084
---

# Evidence-Chain Theory of AI Reproduction Auditing (v7.2)

**Date**: 2026-06-24
**Status**: Theory locked. Ready for mini Study 2 execution pilot.
**Target Venue**: ISR / MISQ / Management Science
**Paper Title**: "When Can We Trust AI-Generated Scientific Reproductions? An Evidence-Chain Theory of Generative Agent Auditing"

## Core Theory Chain

**Information Observability (IO) → Evidence Chain Reconstruction Fidelity (ECRF) → Trust Calibration Error (TCE)**

- **IO**: degree to which each evidence-chain component is explicitly specified and accessible to an AI agent
- **ECRF**: how accurately the agent reconstructs each component (Data→Sample→Indicator→Model→Result→Claim)
- **TCE**: gap between perceived reproduction success (result-level) and actual validity (component-level audit)
- **TIR** (Trust Inflation Rate): P(Human says invalid | Regime says trust) — primary empirical measure in Study 3

## Four Propositions → Four Hypotheses

| P | Statement | H | Study |
|---|-----------|----|-------|
| P1: Observability Bound | AI reproduction fidelity bounded by IO | H1: ECRF increases from IO₁ to IO₃ | Study 2 |
| P2: Asymmetric Reconstructability | IO effect varies across components | H2: Component×IO interaction significant | Study 2 |
| P3: Trust Inflation | Result-level evaluation produces systematic trust inflation | H3: TIR(R₁) > 0 | Study 3 |
| P4: Audit Correction | Component-level audit reduces trust inflation | H4: TIR(R₁) > TIR(R₃) | Study 3 |

## Three Studies

- **Study 1**: Construct validation — ECRF dimensionality (M0/M1 re-analysis). Disagreement rate, error localization rate.
- **Study 2**: IO → ECRF causal test. 20 papers × 3 IO levels (IO₁ narrative / IO₂ structured docs no code / IO₃ full executable) × 2 models = 120 runs + frontier robustness subset (GPT-4o, Claude).
- **Study 3** (MAIN): Trust inflation + audit correction. 3-regime comparison (R₁ result-level / R₂ aggregate / R₃ component audit) against human labels. 4 evidence break types (B₁ Substitution / B₂ Circularity / B₃ Shopping / B₄ Assertion).

## Four Evidence Break Types

B₁: Wrong data/sample/indicator → coincidentally similar results
B₂: Paper values hard-coded as outputs (semantic code review guard)
B₃: Undisclosed specification search (paper-proximity selection without justification)
B₄: Claims unsupported by computational outputs

Each requires 3-layer evidence: automated rule → audit trace → human adjudication.

## Methodology Hardening (Key Design Elements)

- IO₂ explicitly defined as "structured documentation, no executable code" (distinguishes semantic info from executable evidence)
- R₃ is task-contingent: task-critical components pass, not all components
- Fresh isolated workspace per run; condition order randomized; no cross-condition leakage
- Two-layer human validation: Layer 1 (gold evidence chain, component-stratified α targets), Layer 2 (validity adjudication with unflagged sample for recall)
- Paper pool selected and pre-annotated before any agent execution
- Models tier-based: Open-weight / Low-cost API / Commercial frontier A/B

## What Was Deleted from This Paper

- SciSciBench details → one-paragraph motivation only (L3 true capability ~0.3-0.5 establishes need for audit)
- retracted-paper-detection → different project entirely
- ARIS/Codex/Claude engineering → not relevant to IS/management readers
- R000-R007 narrative → aggregated into Study 1 calibration evidence
- "framework"/"pipeline"/"benchmark"/"scoring system" language → replaced with theory language

## Existing Evidence (Pre-Study)

- M0: 6 papers, 3 STRICT D3=100% (Petersen2024, Park2023, Bentley2023)
- M1: 10-paper framework validation (all 4 tests PASS)
- R003: Arts2021 error localized to formula lines 233-236 (proves component-level diagnosis)
- DeepSeek L3: overall=0.298, direction commit 23.4%, 100% weak evidence

## Immediate Next Step

Mini Study 2 (P1): 5 papers × 3 IO levels × 2 models = 30 runs.
Green-light gates (R103): G1 IO₁<IO₃ ECRF in ≥4/5 papers (mandatory), G2 ≥2 components with different IO slopes, G3 result≠component on ≥1 run, G4 ≥1 B₁–B₄ break with audit trace. Pass = ≥3/4 gates, G1 mandatory.

**Pilot set selected 2026-06-24** (refine-logs/PILOT_PAPERS.md, rev2): Petersen2024 (Low/STRICT/SoS), Arts2021 (Med/METHOD/IS), **funk2017** (Med-High/STRICT/Mgmt — clean IO₃ via cdindex.info code + Dataverse), maddi2024 (Med/STRICT-DS/SoS), bikard2013 (High/DATA-SUB/Mgmt — single boundary case, no code). schaper2025 demoted to backup (also no code → would collapse IO₂/IO₃). Rule: first-round pilot keeps only 1 IO-bound boundary case so R103 G1 monotonicity isn't confounded by boundary samples. B₃ Shopping deferred to full Study 2. Backups: schaper2025, w23913 (clean Stata code), deng2023, zheng2025, ke2018, park2023.

**R102 + R103 DONE 2026-06-24 — ALL 4 R103 GATES PASS, GREEN-LIGHT FOR S2** (`R102_R103_REPORT.md`, `scripts/r102_r103_analysis.py`): 10 IO3 runs (paper+docs+raw_data+original_code, isolated, v2 scorer unchanged). IO3 v2 mean=0.713. IO3 code-usage: used_reference 2/10 (arts-deepseek, funk-qwen), modified 0/10, synth-despite-IO3 1/10 (arts×deepseek = strongest B1 at highest observability). R103 aggregation (R100+R101b+R102 all re-scored v2): **IO1 0.497 < IO2 0.552 < IO3 0.713**. G1 IO1<IO3 in 4/5 papers PASS; G2 3 IO-sensitive components (data_source +0.40, result +0.40, model -0.20) PASS; G3 7 result-vs-component disagreements PASS; G4 42 B-candidates (B1=19 confirmed) PASS. Anomalies (not blockers): maddi flat across IO (no Publons data), petersen IO2 0.688 > IO3 0.600 (exec no-result artifact at IO3), model component dip at IO3 (v3 candidate). Next: S2 full (20 papers × 3 IO × 2 models = 120 runs), gated on R120 (20-paper pool) + R121 (Layer 1 2-annotator gold chain). Scorer v2 frozen. Git: master-only, periodic local commit, no push. (`R101_REPORT.md`, `scripts/r101_analysis.py`): 10 IO2 runs (5 papers × qwen3-32b + deepseek), 10/10 isolated. IO2 = paper + data_dictionary/sample_notes + raw_data (SciSciNet 40k sample for petersen/funk/bikard, R003 patent_indicators for arts; maddi docs-only no Publons) + NO code. v1 overall 0.483 (FLAT vs IO1 0.490 — headline criterion FAIL); but Result component 0.35->0.40 (UP, PASS); gate-c synthetic-substitute correctly spares legitimate DATA_SUB (no misfire — 4 runs using real data uncapped, 6 synthesizing capped). 6/10 agents synthesized despite being given real data -> B1 confirmed (agent non-compliance, itself a finding). Scorer artifacts: data_source/sample dropped (keyword scorer credits "mentions source name" not "uses data file"); result-line classifier too strict. **Before R102**: build component v2 (credit data-file usage) + loosen result-line classifier. R102 (IO3 = real data + reference code) is the decisive level. Git: work on dev/benchmark-wiki-updates, periodic local commit, no push (GCP key in ed8a37f history — rotate before any push). (`R100_REPORT.md`, runner `scripts/run_v72_pilot.py`): 10 runs (5 papers × qwen3-32b + deepseek-v4-pro) × IO1, all exit-0, network-blocked, no leakage. qwen3-32b = qwen3.6-27b-fp8 on h100-1/2/3 (172.17.65.41/42/43:8360, 3-node LiteLLM failover); can also call vLLM directly via OpenAI client (skip LiteLLM). Findings: 6/10 result-vs-component disagreement (the theory's trust-inflation pattern — components understood, Result=0); Result component mean 0.35 (the real low-fidelity IO1 signal); B-candidates fired (B2 paper_reported 7/10, B4 6/10, B3 5/10, B1 synthetic-substitution 3/10). **Blocker for R101/R102**: v0 ECRF scorer is keyword-based → ceiling-inflated (overall 0.79 at IO1, not low) because Data_Source/Indicator/Claim score 1.0 for "mentioned concept." Must build ECRF v1 (weight Result/Sample + execution-evidence gate) before R101/R102 so Gate-1 monotonicity is testable. R101/R102 BLOCKED. (refine-logs/PRE_RUN_VALIDATION.md): R095 codebook (DSF/SMF/INF/MDF/RRF/CRS/PRF + TIR/TCE), R096 IO package template (IO₂ hard rule: no .py/.R/.jl/.sh/.do), R097 done — `src/sciscigpt_local/isolated_executor.py` runs Docker `--network none` + `--user uid:gid` + `--read-only` + tmpfs, only per-run workdir mounted (model/control plane stays outside); `scripts/test_r097_isolation.py` **7/7 gates PASS**. R097b done — `sciscigpt-ds:0.1` image (numpy/pandas/scipy/statsmodels/sklearn/pyarrow/openpyxl/matplotlib/networkx/tqdm), digest `2ec5ab91...`, Dockerfile `docker/sciscigpt-ds/Dockerfile`; 7/7 gates PASS + DS-functional OLS offline. R098 DONE — MinerU (magic-pdf 1.3.12, GPU) adjudicated 6 details (`R098_ADJUDICATION.md`): funk2017 N=2.9M patents 1977-2005; maddi2024 window 2009-2020, N=57,482, **estimator = GLM log(1+citations) not OLS** (real correction), 947-word threshold; bikard2013 5,964 obs, 7 depts, OLS+3-way FE (dept-year+individual+career-stage), β=0.099 (H1) / −0.069 (H2), inflection 5.4/9.6. R100–R102 NOT launched; **ready pending greenlight**. Remaining prep: vendor cdindex/USPTO code into IO₃ workdirs + note maddi GLM in codebook.

**Tracker reconciled** (refine-logs/EXPERIMENT_TRACKER.md): milestones renamed C0/S1/P1/S2/S3/R (decoupled from historical M0–M6 to avoid M1 conflict); added Phase-0 pre-run block R095–R099 (codebook, IO package template, isolated-workspace test, pilot gold chain, pilot selection); R130 split into R130a (mechanical) / R130b (vs human); R153 negative-result boundary check. MUST=32 (8 done + 24 TODO), HIGH=5. R098 pilot gold chain MUST precede R100–R102. R120 (20-paper full pool) deferred to Phase 3.

## Related Files

- `idea-stage/IDEA_REPORT.md` — full v7.2 report
- `refine-logs/FINAL_PROPOSAL.md` — compressed proposal
- `refine-logs/EXPERIMENT_PLAN.md` — experiment plan with mini Study 2
- `RESEARCH_BRIEF.md` — UTD strategic framing
- [[benchmark-results-20260612]] — SciSciBench 118-paper baseline
- [[deepseek-l3-benchmark-20260624]] — L3 DeepSeek re-run
- [[l3-scoring-protocol-revision-20260624]] — L3 scoring fixes
- [[m1-full-benchmark-20260618]] — M1 10-paper framework validation
