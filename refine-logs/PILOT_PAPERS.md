# Mini Study 2 Pilot — 5-Paper Selection & Pre-Annotation (R099 / R098 draft)

**Date**: 2026-06-24 (rev 2 — schaper2025 swapped for funk2017)
**Status**: DRAFT — awaiting user confirmation before R100–R102 execution
**Models**: Qwen3-32B + DeepSeek-V4-Pro (GPT-4o/Claude deferred to R150–R152)
**Goal**: De-risk the IO→ECRF manipulation. Highest-risk assumption under test: **can IO₂ cleanly isolate "structured documentation" from "executable code"?**

> **Revision note (rev 2)**: Per user decision, **only one IO-bound boundary case is kept in the first-round pilot** (bikard2013 — DATA-SUB, no original code). schaper2025 was moved to backup because it also lacked original code, risking IO₂/IO₃ collapse and confounding the R103 G1 monotonicity test. Replaced with **funk2017**, which has clean IO₁/IO₂/IO₃ separability (public Dataverse data + public cdindex.info code).

---

## Selection constraints (all satisfied by the Top-5 set)

- [x] ≥1 Low observability variation (Petersen2024)
- [x] ≥1 Medium observability variation (Arts2021, maddi2024)
- [x] ≥1 High observability variation with **clean IO₃** (funk2017 — code+data public)
- [x] 1 boundary case only (bikard2013 — DATA-SUB, IO₂/IO₃ collapse flagged)
- [x] ≥2 domains: Science of Science + IS/Innovation + Management/Strategy (3 covered)
- [x] ≥2 task types: STRICT + METHOD + DATA-SUB (3 covered)
- [x] ≥1 paper with high evidence-break probability (bikard2013, Arts2021)

---

## Top-5 Recommended Pilot Set

### 1. Petersen2024 — `petersen2023_disruption_index`
| Field | Value |
|-------|-------|
| Title | The disruption index is biased by citation inflation |
| Domain | Science of Science |
| Venue | arXiv (2023) |
| **Task type** | **STRICT** |
| **Observability stratum** | **Low** |
| Data availability | SciSciNet (N=469,855) — fully available locally; substitutes WoS |
| Code availability | Reproduce from formulas (R002 already achieved D3=8/8) |
| Likely weak component | Result Table (numerical-identity target is the stress point) |
| IO₁ feasibility | ✅ Paper text — formula CDp=(Ni−Nj)/(Ni+Nj+jNk) is explicit |
| IO₂ feasibility | ✅ Paper + data dictionary + variable docs (team_size, citation_count defs) |
| IO₃ feasibility | ✅ Paper + SciSciNet data + reference reproduce.py from R002 |
| Expected break risk | Low — calibration anchor; B₂ Circularity risk only if agent hard-codes reported coefs |
| Reason for inclusion | **Calibration anchor at the "valid" pole**; reproduces known-good; tests that IO₃ yields D3≈1.00 and IO₁ does not. Establishes the Low-variation floor. |

### 2. Arts2021 — `arts2021_natural_language_processing`
| Field | Value |
|-------|-------|
| Title | Natural Language Processing to Identify the Structure of Innovation in Patent Claims |
| Domain | IS / Innovation (Research Policy) |
| Venue | Research Policy (2021) |
| **Task type** | **METHOD** (10 NLP indicators, no single numerical target) |
| **Observability stratum** | **Medium** |
| Data availability | USPTO patent claims dataset — described but multi-step preprocessing (P1–P10) |
| Code availability | Not provided; 10 indicators reconstructed from formulas |
| Likely weak component | Indicator (known aggregation-formula bug at lines 233–236, R003) |
| IO₁ feasibility | ✅ Paper text — 10 formulas and 10 preprocessing steps described |
| IO₂ feasibility | ✅ Paper + indicator definitions + sample-construction notes |
| IO₃ feasibility | ✅ Paper + USPTO sample data + reference code from R003 |
| Expected break risk | **B₁ Substitution** (cosine-similarity indicator proxy) + **B₂ Circularity** (formula hard-code) |
| Reason for inclusion | **Medium-complexity anchor with a known localized break**; multi-step indicators stress the IO₂↔IO₃ boundary and make Component×IO interaction visible at the Indicator component. |

### 3. bikard2013 — `bikard2013_exploring_tradeoffs`
| Field | Value |
|-------|-------|
| Title | Exploring Tradeoffs in the Organization of Scientific Work |
| Domain | Management / Strategy |
| Venue | NBER → Management Science (2013) |
| **Task type** | **DATA-SUB** (original MIT 661-faculty dataset not public) |
| **Observability stratum** | **High** |
| Data availability | ❌ MIT faculty publications dataset — institution-specific, not publicly available |
| Code availability | ❌ None; fixed-effects regression to reconstruct |
| Likely weak component | Sample (faculty disambiguation) + Claim (claim-result gap) |
| IO₁ feasibility | ✅ Paper text — IV/DV definitions and FE model described |
| IO₂ feasibility | ⚠️ Paper + variable docs, but **sample cannot be reconstructed** → forces substitution |
| IO₃ feasibility | ⚠️ No original code/data → IO₃ collapses toward IO₂ for this paper (informative boundary) |
| Expected break risk | **B₁ Substitution** (SciSciNet/Insitute proxy for MIT) + **B₄ Assertion** (cross-institution claim stretch) |
| Reason for inclusion | **Highest break-probability paper**. Tests DATA-SUB pathway and Claim-component fidelity. The IO₂/IO₃ collapse is itself diagnostic — demonstrates the IO bound where data is genuinely unavailable. Management domain diversifies beyond SoS. |

### 4. funk2017 — `funk2017_dynamic_network`  ← REPLACES schaper2025 (clean IO₃)
| Field | Value |
|-------|-------|
| Title | A Dynamic Network Measure of Technological Change |
| Domain | Management / Strategy (innovation/patents) |
| Venue | Management Science (2017) |
| **Task type** | **STRICT** (regression; numerical targets reconstructable from public data) |
| **Observability stratum** | **Medium-High** (clean separability) |
| Data availability | ✅ Patent Network Dataverse (Li et al.) — **public** |
| Code availability | ✅ **Public code at cdindex.info** (calculates CDt / mCDt indexes); online appendix at doi.org/10.1287/mnsc.2015.2366 |
| Likely weak component | Model (network-measure construction) + Result |
| IO₁ feasibility | ✅ Paper text — CDt/mCDt formulas, IV/DV defined |
| IO₂ feasibility | ✅ Paper + variable docs + sample notes (university-related patents, federal-funding, commercial-engagement filters) **— no code** |
| IO₃ feasibility | ✅ Paper + Dataverse data + **cdindex.info reference code** |
| Expected break risk | **B₂ Circularity** (hard-coding reported index values) + **B₁** (Dataverse subset substitution) |
| Reason for inclusion | **The clean High/Medium-High case the pilot needs** — data + code both public, so IO₁ / IO₂ / IO₃ are sharply separable. Lets R103 G1 (monotonicity) be tested on a paper where IO₃ is genuinely constructable, unlike the bikard2013 boundary case. Management domain; complements Arts2021 (IS). |

### 5. maddi2024 — `maddi2024_peer_review_reports`
| Field | Value |
|-------|-------|
| Title | On the peer review reports: does size matter? |
| Domain | Science of Science |
| Venue | Scientometrics (2024) |
| **Task type** | **STRICT / DATA-SUB** (OLS, single IV/DV) |
| **Observability stratum** | **Medium** |
| Data availability | ⚠️ Publons + Web of Science — Publons access has changed since publication |
| Code availability | ❌ None; simple OLS |
| Likely weak component | Data Source (Publons access drift) + Result |
| IO₁ feasibility | ✅ Paper text — OLS spec explicit |
| IO₂ feasibility | ✅ Paper + variable docs + sample notes |
| IO₃ feasibility | ⚠️ WoS substitutable; Publons partial → IO₃ data-incomplete |
| Expected break risk | **B₁ Substitution** (WoS-only proxy) + **B₂** (coefficient hard-code) |
| Reason for inclusion | **Clean OLS baseline in SoS with realistic data-access drift**. Simplest statistical structure → isolates the Data-Source component effect from Model complexity. Balances the regression-heavy set with a tractable STRICT/DATA-SUB case. |

---

## Coverage matrix (Top-5, rev 2)

| Dimension | Coverage |
|-----------|----------|
| Observability | Low (Petersen) · Med (Arts, maddi) · Med-High/clean (funk2017) · High/boundary (bikard) |
| Domain | SoS (Petersen, maddi) · IS/Innovation (Arts) · Management (funk2017, bikard) |
| Task type | STRICT (Petersen, maddi, funk2017) · METHOD (Arts) · DATA-SUB (bikard) |
| IO₃ cleanly constructable | Petersen ✓ · Arts ✓ · funk2017 ✓ · maddi ⚠️(Publons drift) · bikard ✗(boundary) |
| Break risk | B₁ (Arts, bikard, maddi) · B₂ (Arts, maddi, funk2017) · B₃ — *deferred (schaper in backup)* · B₄ (bikard) |
| Boundary cases | 1 (bikard — DATA-SUB, no code) |
| Models | 2 (Qwen3-32B open-weight, DeepSeek-V4-Pro low-cost API) |

> **Trade-off accepted**: B₃ (Shopping) is no longer exercised in the first-round pilot. This is intentional — B₃ detection will be validated in full Study 2 with schaper2025 and other multi-DV papers once the IO manipulation itself is validated. The pilot's job is to confirm the IO gradient (G1), not to exercise all four break types.

---

## Backup candidates (≥6)

| # | Paper | Domain | Task | Stratum | Code/Data | Why backup / when to swap in |
|---|-------|--------|------|---------|-----------|------------------------------|
| B1 | `schaper2025_frontier_scientists` | IS/Innovation | DATA-SUB/CLAIM-ROBUST | High | ❌ no code | **Demoted from Top-5** — multi-DV (B₃ Shopping) ideal for full Study 2 / boundary analysis once IO gradient validated |
| B2 | `w23913_patent_examiner_specialization` | Management/labor | STRICT/DATA-SUB | Med-High | ✅ Stata code (linked in paper) | **Clean code-available backup**; swap for funk2017 if Dataverse access fails. IS/labor-economics adjacent |
| B3 | `funk2017_dynamic_network` (was B1) | Management Science | STRICT | Med-High | ✅ code+data | Now promoted to Top-5 |
| B4 | `deng2023_enhancing_disruption` | SoS | METHOD | Medium | ⚠️ APS partial | Swap for maddi if a SoS METHOD case is needed |
| B5 | `zheng2025_male_female_retractions` | SoS | DATA-SUB | Med-High | ⚠️ Retraction Watch | B₁ risk; swap for maddi |
| B6 | `ke2018_comparing_scientific_technological_impact` | J. Informetrics | DATA-SUB | Medium | ⚠️ multi-source | Swap if biomedical patent data unavailable |
| B7 | `park2023_disruptive` / `bentley2023_disruption` | SoS | STRICT | Low | ✅ SciSciNet | Alternate Low anchors (R004/R007) |

---

## IO package preparation checklist (feeds R096)

For each pilot paper, prepare three folders before R100–R102:

- **IO₁/** — paper `.md` text only. No web, no data, no code.
- **IO₂/** — paper `.md` + `data_dictionary.md` (variable defs) + `sample_notes.md` (sample construction rules) + (where task requires) controlled raw data file. **No `.py`, no `.R`, no scripts.** This is the key manipulation under test.
- **IO₃/** — paper `.md` + data files + `original_code/` (reproduce.py from R002/R003 where available; reconstructed reference otherwise).

**IO₂ boundary audit (highest-risk assumption):**
- A pre-run check (R097) verifies no file in IO₂/ is executable or contains reported numeric constants beyond legitimate documentation.
- Any paper where IO₂ and IO₃ cannot be distinguished (bikard, schaper — no original code) is flagged as an **IO-bound boundary case**, reported transparently, not forced.

## Pilot gold-chain annotation spec (feeds R098)

Per paper, 2 annotators (or 1 + adjudication if time-constrained) fill:

| Component | Gold content | α target |
|-----------|--------------|----------|
| Data Source | exact source, access status, substitute used | ≥0.75 |
| Sample | N, time window, filters, disambiguation rule | ≥0.67 |
| Indicator | formula(s), preprocessing steps | ≥0.67 |
| Model | spec, IV/DV, FE, estimator | ≥0.67 |
| Result | reported coefficients / distributions | ≥0.80 |
| Claim | conclusion claims, claim-result distance | ≥0.60 |

Disagreements resolved by adjudication **before** R100–R102 ECRF scoring. Below-target components flagged transparently.

---

## Decision required before R100–R102

1. **Confirm Top-5 set** (or swap in backups).
2. **Confirm model pair** (Qwen3-32B + DeepSeek-V4-Pro).
3. **Confirm R098 annotation depth** (2 annotators vs. 1 + adjudication).
4. **Greenlight** R095–R097 prep → then R100–R102.

**Not started in this turn**: R100–R102 execution, R120 (20-paper full pool).
