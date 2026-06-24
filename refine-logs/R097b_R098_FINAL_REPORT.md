# R097b + R098 Final Report (2026-06-24)

**Status**: R097b (data-science image) DONE · R098 (MinerU adjudication) DONE · **R100–R102 NOT launched** — readiness assessment below.

---

## 1. Final Docker image test results

### Image record (R097b)

| Field | Value |
|-------|-------|
| Dockerfile | `docker/sciscigpt-ds/Dockerfile` |
| Image tag | `sciscigpt-ds:0.1` |
| Image ID / digest | `sha256:2ec5ab91abb8c9fe5d91f412851986d1c610b6b4790354d3a5087a23b9412519` |
| Size | 1.07 GB |
| Requirements lock | `docker/sciscigpt-ds/requirements.txt` (pinned versions) |
| Build log | `docker/sciscigpt-ds/build.log` |
| Build-time network | Allowed (pip install) |
| Runtime network | **Blocked** (`--network none`, enforced by `isolated_executor.py`) |

### Stack (all pinned)

numpy 1.26.4 · pandas 2.2.2 · scipy 1.13.1 · statsmodels 0.14.2 · scikit-learn 1.5.1 · pyarrow 16.1.0 · openpyxl 3.1.5 · matplotlib 3.9.1 · networkx 3.3 · tqdm 4.66.4. (Vendor-specific code for funk2017/Arts2021 is **not baked in** — it is mounted as part of the IO₃ workdir per requirement 5.)

### Isolation test — 7/7 gates PASS on `sciscigpt-ds:0.1`

`scripts/test_r097_isolation.py sciscigpt-ds:0.1` → exit 0.

| Gate | Property | Result |
|------|----------|--------|
| G-A | Network egress blocked | PASS (socket→1.1.1.1:53 = OSError) |
| G-E | Container exec succeeded | PASS (exit 0) |
| G-B | Host home unreachable | PASS (`/home/*` = []) |
| G-C | Sibling IO folder unreachable | PASS |
| G-D | Workspace writable | PASS |
| G-F1 | Basic numeric exec | PASS |
| G-F2 | No lingering container | PASS |

### Bonus — DS-functional probe (real OLS under isolation)

A real `statsmodels` OLS (200 obs, true slope 2.0) ran **fully offline** inside the jail: coef = 1.959, p ≈ 1e-110. Confirms the image is reproduction-functional, not just importable. Hardening contract held: `--network none`, `--user uid:gid`, `--read-only` rootfs, tmpfs `/tmp`, only per-run workdir mounted. Model/control plane stays outside (only execution is isolated).

---

## 2. Final IO package feasibility table

| Paper | Stratum | Task | Domain | IO₁ | IO₂ | IO₃ | Constructability | Boundary? |
|-------|---------|------|--------|-----|-----|-----|-------------------|-----------|
| Petersen2024 | Low | STRICT | SoS | ✓ | ✓ | ✓ (SciSciNet + R002 reproduce.py) | Clean | No |
| Arts2021 | Medium | METHOD | IS/Innov | ✓ | ✓ | ✓ (USPTO + R003 ref code) | Clean | No |
| **funk2017** | Med-High | STRICT | Mgmt | ✓ | ✓ | ✓ (Dataverse + cdindex.info code) | **Cleanest IO₃** | No |
| maddi2024 | Medium | STRICT-DS | SoS | ✓ | ✓ | ⚠️ (WoS ok; Publons drift) | Partial IO₃ | Soft |
| bikard2013 | High | DATA-SUB | Mgmt | ✓ | ✓ | ✗ (no code/data) | IO₃→IO₂ collapse | **Yes (by design)** |

3 clean IO₃, 1 partial, 1 boundary — matches design (single boundary case). **Unchanged from R096/R098 draft** — adjudication touched only result-target fields.

---

## 3. Adjudicated gold-chain changes (R098, via MinerU)

Full record: `refine-logs/R098_ADJUDICATION.md`. Summary of changes (all result-target refinements; **IO design untouched**):

| Paper | Field | Before | After |
|-------|-------|--------|-------|
| funk2017 | sample | "exact N not pinned" | **2.9M utility patents, 1977–2005** (excl 34,889 + 177; 2.8% undefined) |
| maddi2024 | sample | "time window not stated" | **2009–2020**; N=**57,482** (from 57,694 after IQR×5, −212) |
| maddi2024 | model | "OLS-family" | **GLM, log(1+citations) DV** ← real correction |
| maddi2024 | indicator | "IV=report length" | + Fisher-discretized into 5 classes; **947-word threshold** |
| bikard2013 | sample | "661 faculty, 1976–2006" | + **5,964 scientist-year obs, 21,054 pubs, 7 depts, >20-author exclusion, mean group 3.8** |
| bikard2013 | model | "individual + year FE" | **OLS + 3-way FE (department-year + individual + career-stage), robust SE clustered at scientist** |
| bikard2013 | results | "qualitative only" | Headline β pinned: **0.099** (H1 quality), **−0.069** (H2 fractional), inflection **5.4/9.6**; correlations +0.23/+0.09/+0.13/−0.14 |

**The one substantive correction**: maddi2024 estimator is a **GLM with log(1+citations)**, not OLS. This matters for R100 scoring (the agent must reproduce a GLM). Flagged for the R095 codebook.

**Remaining cell-level detail (non-blocking)**: maddi per-class β (Tables 4–5), bikard full robustness tables (3–9). Pin during R100 scoring or via MinerU `auto` on result pages.

---

## 4. Is R100–R102 ready to launch?

**Assessment: YES — ready, pending your greenlight.**

| Prerequisite | Status |
|--------------|--------|
| R095 codebook | ✅ approved |
| R096 IO package template | ✅ approved (IO₂ hard rule enforced) |
| R097 isolation (python:3.11-slim) | ✅ 7/7 gates |
| R097b DS image (sciscigpt-ds:0.1) | ✅ 7/7 gates + DS-functional OLS |
| R098 gold chains (5 papers) | ✅ draft + adjudicated (maddi GLM correction flagged) |
| R099 pilot set (rev-2) | ✅ approved |
| Model pair (Qwen3-32B + DeepSeek-V4-Pro) | ✅ confirmed; LiteLLM proxy live |
| Frontier models | ✅ correctly deferred to R150–R152 |

**Before first run, two small prep items** (do not require re-approval):
1. Vendor the funk2017 cdindex code + Arts2021 USPTO loader into each paper's `IO₃/original_code/` (requirement 5 — they mount with the workdir, not baked into the image).
2. Update R095 codebook to note maddi2024 uses GLM (not OLS) so the R₁/R₂/R₃ scorers handle the log-link DV correctly.

**Recommendation**: proceed to vendoring (1) + codebook note (2), then launch **R100 (IO₁) on the 5 pilot papers × 2 models = 10 runs** as the first wave — the cheapest condition and the one that must show the lowest ECRF. If G1 (IO₁ < IO₃) is even plausible after R100, continue to R101/R102.

Awaiting your go/no-go on R100.
