# Phase-0 Pre-Run Validation (R095–R098)

**Date**: 2026-06-24
**Status**: Draft products for R095 / R096 / R097 / R098 — review before R100–R102
**Purpose**: De-risk the IO manipulation before any mini-Study-2 agent run. Products are the prerequisites the user asked to confirm.

---

## R095 — Scoring Codebook (fidelity + governance metrics)

### Per-component fidelity metrics (ECRF dimensions)

| Code | Name | Component(s) | Definition | Threshold (pass) |
|------|------|--------------|------------|------------------|
| **DSF** | Data-Source Fidelity | Data Source | reconstructed source matches gold source (or documented, justified substitute for DATA-SUB) | ≥ 0.8 exact; substitute allowed iff justified in DATA-SUB task |
| **SMF** | Sample Fidelity | Sample | N, time window, filters, disambiguation rule match gold | exact N (±2%); filters match |
| **INF** | Indicator Fidelity | Indicator | formula(s) and preprocessing steps match gold | formula exact; preprocessing step coverage ≥ 0.9 |
| **MDF** | Model Fidelity | Model | spec, IV/DV, FE, estimator match gold | estimator family match; all IVs present |
| **RRF** | Result-Reference Fidelity | Result Table | numerical outputs match gold (STRICT) or direction/mechanism (DATA-SUB) | STRICT: D3-style cell match; DATA-SUB: direction + significance |
| **CRS** | Claim Result Support | Claim / Result | claims traceable to computational outputs; no unsupported assertion | every claim has a result pointer |
| **PRF** | Process Reliability Fidelity | Process | no hard-coded paper values (B₂), no unjustified shopping (B₃) | code scan clean + semantic review clean |

> Note: codebook consolidates the previously-scattered dimension names. INF/MDF split Indicator vs Model; CRS covers the Claim↔Result link; PRF covers process integrity (B₂/B₃). ECRF(component) = weighted average of the dimensions applicable to that component (task-contingent — see R₃).

### Component-stratified reliability α (from EXPERIMENT_PLAN)

| Component | Target α |
|-----------|----------|
| Data Source (DSF) | ≥ 0.75 |
| Sample (SMF) | ≥ 0.67 |
| Indicator (INF) | ≥ 0.67 |
| Model (MDF) | ≥ 0.67 |
| Result (RRF) | ≥ 0.80 |
| Claim (CRS) | ≥ 0.60 |

### Governance metrics (Study 3)

| Code | Name | Definition |
|------|------|------------|
| **TIR** | Trust Inflation Rate | P(human says invalid \| regime says trust) — primary |
| **TCE_i^r** | Trust Calibration Error (individual) | 1[regime r trusts run i] − 1[human valid run i] |
| **TIR_decomp** | TIR decomposition | inflation rate vs deflation rate, McNemar paired |

### Maturity levels (L0–L5)

L0 Fail → L1 Partial → L2 Direction → L3(ds) Data-substituted → L3 Strict numerical → L4 Auditable → L5 Reproducible+generalizes. (Carried from C0.)

### Estimator-specific handling (R098 adjudication)

Some papers use estimators that are **not plain OLS**. The scorer must detect the estimator family and apply the right RRF/comparison rule — a log-link DV cannot be compared to a raw citation count.

| Paper | Estimator (adjudicated) | DV transform | RRF / regime rule |
|-------|-------------------------|--------------|-------------------|
| Petersen2024 | OLS + year FE | raw CD (ln_rp) | STRICT: cell match to gold coefs |
| funk2017 | OLS + Negative Binomial | raw CD5 / mCD5 | STRICT: descriptive stats + correlation r match |
| **maddi2024** | **GLM, log-link, log(1+citations) DV** | log(1+citations) | **RRF compares on the log scale**; the 947-word threshold class + per-class β; R₁ "numbers match" must match log-scale coefs, NOT raw citations. Direction = sign of the report-length class coefficient. |
| bikard2013 | OLS + 3-way FE (dept-year + individual + career-stage), robust SE clustered at scientist | log for H2/H3 | DATA-SUB: direction + sign of group-size coef (β=0.099 H1, −0.069 H2) |

**maddi2024 GLM guard (anti-B₂)**: because the DV is log(1+citations), an agent that hard-codes the paper's reported *raw* citation counts as outputs would be a B₂ Circularity signal — the comparison must be on the log-link scale. R₃ component audit checks that the agent's code actually fits a GLM with `log(1+citations)` (e.g., `sm.GLM(..., family=sm.families.Gaussian(link=sm.families.links.log())` or the Thelwall-Wilson OLS-on-log transform), not a raw-count regression.

---

## R096 — IO Package Template (the highest-risk manipulation)

**This is the artifact that must be airtight.** The whole theory test hinges on IO₂ cleanly excluding executable code while IO₃ includes it.

### Folder specification

```
pilot/<paper_id>/
  IO1/   paper.md                       # ONLY the paper text. No data, no code, no URLs acted on.
  IO2/   paper.md
        data_dictionary.md              # variable definitions, units, allowed values
        sample_notes.md                 # N, time window, filters, disambiguation rule
        indicator_defs.md               # formula definitions (prose/formula, NOT runnable)
        raw_data/                       # (only where task strictly requires; DATA-SUB)
        ❌ NO .py .R .jl .sh .ipynb      # hard rule
        ❌ NO reproduce scripts
  IO3/   paper.md
        data_dictionary.md
        sample_notes.md
        raw_data/
        original_code/                  # reference reproduce.py / cdindex code / Stata .do
        reproduce.*                     # executable reference
```

### IO-boundary audit rule (enforced before run, R097)

- **IO₁**: only `paper.md` present. Agent has **no network** and **no filesystem access outside IO1/**.
- **IO₂**: `find IO2/ -regex '.*\.\(py\|R\|jl\|sh\|ipynb\|do\)$'` must return **empty**. `indicator_defs.md` may contain formulas in LaTeX/prose but no runnable code blocks that compute the target.
- **IO₃**: must contain ≥1 executable reference file AND the data it needs.

### Per-paper IO₃ constructability (rev-2 pilot)

| Paper | IO₁ | IO₂ | IO₃ | Note |
|-------|-----|-----|-----|------|
| Petersen2024 | ✓ | ✓ | ✓ (SciSciNet + R002 reproduce.py) | clean |
| Arts2021 | ✓ | ✓ | ✓ (USPTO sample + R003 ref code) | clean |
| funk2017 | ✓ | ✓ | ✓ (Dataverse data + cdindex.info code) | **clean — strongest IO₃** |
| maddi2024 | ✓ | ✓ | ⚠️ (WoS ok; Publons drift) | partial IO₃ |
| bikard2013 | ✓ | ✓ | ✗ (no original code/data) | **boundary — IO₃ collapses to IO₂** |

---

## R097 — Isolated Workspace Test

### Finding (to act on before R100)

The current sandbox (`src/sciscigpt_local/sandbox.py`) uses **subprocess isolation only** and **does NOT enforce no-network / no-filesystem-egress**. It contains no network guard. Therefore IO₁'s "no web" condition is **not yet enforceable at the code level** — an agent could in principle fetch external resources and break the manipulation.

### Required pre-R100 hardening (minimal)

1. **Network egress block**: run agent subprocess under a namespace/firewall with no outbound network (e.g., `unshare -n` / iptables OUTPUT DROP, or a container with `--network none`). This is the physical enforcement of IO₁.
2. **Filesystem jail**: chroot/bind-mount only the `IOx/` folder as writable; agent cannot read sibling IO folders (prevents cross-condition leakage — anti-claim A4).
3. **Session termination**: agent process killed + workspace wiped between conditions (already intended in protocol; verify in harness).
4. **Audit log**: record every file read/written + any network attempt (blocked attempts logged) per run, as input to PRF / B₂ / B₃ detection.

### Checklist (gate)

- [ ] Network egress physically blocked for IO₁ and IO₂ runs
- [ ] Filesystem jail prevents reading other IO folders
- [ ] Per-run workspace created fresh, wiped after run
- [ ] Read/write + blocked-network log emitted per run
- [ ] Smoke test: agent cannot reach a known external URL under IO₁/IO₂

---

## R098 — Pilot Gold-Chain Annotation (lightweight: 1 primary + 1 adjudication)

**Depth**: one primary annotator produces the gold chain; one adjudication reviewer checks and resolves disagreements. Heavier 2-annotator protocol reserved for R121 (full Study 2).

### Per-paper gold-chain template (fill all 9)

| # | Field | Content |
|---|-------|---------|
| 1 | Data source | exact source, access status, substitute used (DATA-SUB) |
| 2 | Sample definition | N, time window, filters, disambiguation rule |
| 3 | Indicator / variable construction | formula(s), preprocessing steps |
| 4 | Model specification | estimator, IV/DV, FE/controls |
| 5 | Target results | reported coefficients / distributions / table cells |
| 6 | Main claim | conclusion claims + claim-result distance |
| 7 | Task-critical components | which of the 6 components are evaluable for this task type (task-contingency for R₃) |
| 8 | IO package feasibility | IO₁ / IO₂ / IO₃ constructable? (from R096 table) |
| 9 | Expected evidence-break risk | B₁/B₂/B₃/B₄ + which component likely weak |

### Fill status

- **Petersen2024**: gold from R002 (D3=8/8) — fields 1–6 known; fields 7–9 to formalize.
- **Arts2021**: gold from R003 (formula bug localized) — fields 1–6 known; 7–9 to formalize.
- **funk2017**: TO READ — Dataverse/cdindex structure; fields 1–6 from paper + appendix.
- **maddi2024**: TO READ — Publons/WoS access status; fields 1–6 from paper.
- **bikard2013**: TO READ — flag boundary in fields 8–9.

> R098 completion requires reading funk2017, maddi2024, bikard2013 papers to fill fields 1–9. Proposed as the immediate next action after this product set is approved.

---

## What is NOT started

- ❌ **R100–R102** (mini-Study-2 agent runs) — not launched; gated on R095–R098 sign-off + the R097 network-hardening fix.
- ❌ **R120** (20-paper full pool) — deferred to Phase 3.

## Decision needed before R100–R102

1. Approve revised Top-5 (Petersen / Arts / funk2017 / maddi / bikard).
2. Approve R095 codebook + R096 IO package template.
3. Approve the **R097 network-hardening** scope (unshare/iptables vs. container `--network none`).
4. Greenlight R098 gold-chain reading pass (funk2017, maddi2024, bikard2013).
