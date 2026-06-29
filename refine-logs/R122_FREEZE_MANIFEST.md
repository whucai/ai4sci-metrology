# R122–R124 Freeze Manifest

**Date**: 2026-06-29
**Scope**: pre-launch freeze for full Study 2 (R122=IO₁, R123=IO₂, R124=IO₃; R125=analysis). All artifacts below are FROZEN for the duration of R122–R124.

## Frozen artifacts (in `refine-logs/r122_freeze/`)

| Artifact | Path | sha256 (first 12) | Role |
|---|---|---|---|
| Gold chain v1-r3 | `gold_v1_r3.json` | `78efaa05f234` | 20-paper gold reference (post-3-round adjudication) |
| ECRF v2 scorer | `ecrf_v2_scorer.py` | `c77d02ae7947` | recognition rules (v1 weights+gates unchanged) |
| ECRF v1 scorer | `ecrf_v1_scorer.py` | `6697105a83f1` | v1 weights + gates (the contract) |
| IO package manifests | `io_manifests.json` | (in-file) | 20 papers × 3 IO = 60 package declarations |
| Freeze manifest | `freeze_manifest.json` | (in-file) | weights, gates, immutability rule |

**v1 weights**: data_source 0.10 · sample 0.15 · indicator 0.15 · model 0.10 · result 0.35 · claim 0.15 (sum 1.0).
**v1 gates**: (a) no-exec-result → cap 0.60 · (b) result=0 → cap 0.55 · (c) synthetic data → cap 0.50 · (d) claim w/o result → cap 0.60 · (e) paper-reported-as-computed (B₂) → cap 0.50.
**v2 recognition**: data_source=file-load credit · sample=N+window · result=broader evidence + line classifier (PAPER_REPORTED/DATA_SUB/COMPUTED/SYNTHETIC). Weights and gates unchanged from v1.

## Immutability rule (HARD)

During R122–R124, the following are **frozen and must not be modified**:
- the gold chain (`gold_v1_r3.json`)
- the scorer (`ecrf_v2_scorer.py`, `ecrf_v1_scorer.py`)
- the v1 weights and gates
- the IO package definitions (`io_manifests.json` — the `data_provided` / `ref_code_available` flags are the contract the scorer consumes)

**Any correction discovered during the runs MUST go through a separate patch record** in `refine-logs/r122_freeze/patches/` (a dated memo + affected runs list), NOT silent overwriting of the frozen artifacts or the run outputs. Runs are scored against the frozen reference; patch records are appended to the analysis (R125) for transparency.

## Isolation contract (every run)

- Docker `sciscigpt-ds:0.1`, `--network none`, `--read-only`, `--cap-drop=ALL`, `--security-opt=no-new-privileges`, `--user uid:gid`, `tmpfs /tmp`
- Per-run workdir only (mounted rw at `/workspace`); **no sibling IO folders, no caches, no full benchmark pool** exposed to the run
- Network probe baked into the execution wrapper; `network_blocked` asserted per run

## Process-evidence fields (recorded per run, embedded in the run JSON)

Per the run spec, each run record MUST capture:
- `real_data_used` — whether the agent loaded the provided raw_data file (v2 `has_file_load` + `data_provided`)
- `ref_code_used` — whether the agent imported/adapted the provided original/reference code
- `synthetic_generated` — whether the agent generated synthetic/placeholder data (v1 `uses_synthetic_data`)
- `paper_reported_copied` — whether paper-reported values were hard-coded as computed (B₂ `b2_circularity`)
- `executable_code_generated` — `code_parsed` boolean
- `execution_succeeded` — `exec.exit_code == 0` + `status == DONE`

These are computed at run time (not post-hoc) and embedded in the per-run JSON, so R125 aggregation does not re-parse raw responses.

## R121 wording (corrected)

R121 is **independent model-family dual annotation with adjudication** (Annotator A = glm-5.2, Annotator B = codex-gpt-5.2 via Codex MCP), NOT human annotation. The 3-round adjudication produced α=0.945 overall, 6/6 components ≥0.70. A **targeted human audit** of borderline or high-impact components (e.g. the wu2019 claim direction, the schaper2025 data-linkage boundary) is scheduled as a later check, but is not on the R122–R124 critical path.

## Run plan (sequential)

1. **R122** — IO₁ full run: 20 papers × 2 models × IO₁ = 40 runs. Materials: `paper.md` only.
2. **R123** — IO₂ full run: 20 × 2 × IO₂ = 40 runs. Materials: + data_dictionary + sample_notes + raw_data (where data_provided).
3. **R124** — IO₃ full run: 20 × 2 × IO₃ = 40 runs. Materials: + original_code (where ref_code_available). Boundary papers (maddi2024, bikard2013, vasarhelyi2023) IO₃ collapses to IO₂ by design.
4. **R125** — Study 2 aggregation + analysis (monotonic ECRF, Component×IO mixed-effects, H1/H2).
5. **R-robust-KU** — only after R125.

## Assembly status at freeze

- 8/20 papers have IO packages fully assembled on disk (5 pilot + 3 C0: petersen2024, arts2021, funk2017, maddi2024, bikard2013, wu2019_teams, park2023_disruptive, bentley2023_disruption).
- 12/20 pending IO-package assembly (ke2015, sun2023, deng2023, schaper2025, galuez2023, vasarhelyi2023, donner2024, zheng2025_male, gebhart2023, obadage2024, liu2018, arts2021_patent_nlp).
- R122 (IO₁) only needs `paper.md` per paper — the lightest assembly burden; launchable first.
- R123/R124 assembly ramps up (data + code materials); assembled incrementally before each wave.
