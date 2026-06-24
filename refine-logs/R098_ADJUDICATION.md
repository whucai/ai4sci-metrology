# R098 MinerU Adjudication Record (2026-06-24)

**Tool**: MinerU / magic-pdf 1.3.12 (GPU cuda, 23 GB). Method `txt` for text-based extraction; `auto` (table mode) attempted for coefficient tables.
**Scope**: 6 pending numeric details flagged in `GOLD_CHAIN_R098.md`. Per user instruction: **result-target refinements only — do not alter the IO manipulation design.** No IO₁/IO₂/IO₃ constructability field was changed.

---

## 1. funk2017 — exact sample N  ✅ RESOLVED

| Field | Value |
|-------|-------|
| Source PDF | `bench-mark/Management Science/A_Dynamic_Network_Measure_of_Technological_Change.pdf` |
| MinerU page/text | §3.1 Descriptive Statistics, "Using data on the 2.9 million U.S. utility patents granted between 1977 and 2005…" + "…analyses exclude 34,889 patents that were outside the scope of the NBER's technology categorization system and 177 patents with substantial missing data." |
| Resolved value | **N = 2.9 million U.S. utility patents, 1977–2005**, after excluding 34,889 (non-NBER-category) + 177 (missing data). Undefined CD/mCD in 82,572 of 2.9M (2.8%). |
| Adjudication note | Fully resolved. Updates gold-chain field 2. **IO design unchanged** (Dataverse + cdindex.info code still construct IO₃). |

## 2. maddi2024 — time window  ✅ RESOLVED

| Field | Value |
|-------|-------|
| Source PDF | `bench-mark/others/2403.18845v1.pdf` |
| MinerU text | "…we limited our dataset to publications with a publication year after 2009. This choice was made because funding information was not well-documented in the metadata before this date." + flowchart "Publons data Matching WoS data (2009-2020)". |
| Resolved value | **Time window 2009–2020** (publication year > 2009, due to funding-metadata availability). |
| Adjudication note | Updates gold-chain field 2 (was "not explicitly stated"). IO design unchanged. |

## 3. maddi2024 — sample N + estimator  ✅ RESOLVED (with correction)

| Field | Value |
|-------|-------|
| MinerU text | "…sample size was reduced to 57,694 publications… exclusion threshold = IQR × 5 (max 13,671 words/report)… excluded 212 extreme observations… sample used for the initial regression consists of 57,482 publications." + "…we have chosen to employ the Generalized Linear Model (GLM)… response variable = log-transformed citations (log(1 + number of citations))… principal IV = word count in reviewers' reports, discretized into 5 classes via Fisher discretization." |
| Resolved value | **N = 57,482** (from 57,694 after IQR×5 outlier removal of 212 obs). **Estimator = GLM with log(1+citations) DV** (NOT plain OLS — correction). IV = report length, 5 Fisher classes. 947-word threshold = the class boundary where significant positive effect begins. |
| Adjudication note | **Real correction to gold-chain field 4**: OLS → GLM (log-link, log(1+citations) DV). This matters for R100 scoring (the agent must reproduce a GLM, not OLS). IO design unchanged. |

## 4. maddi2024 — per-class regression coefficients  ⚠️ SPEC RESOLVED, CELL VALUES PENDING

| Field | Value |
|-------|-------|
| MinerU text | Tables 4–5 render as headers ("Table 4", "Table 5") with `txt` method; cell-level β values not cleanly extracted. |
| Status | Estimator + DV + IV discretization confirmed (item 3). Per-class β coefficients live in Tables 4–5; **pin via MinerU `auto` (table mode) or manual read during R100 scoring**. |
| Adjudication note | Result-target refinement; does not block IO manipulation. Recommendation: run `magic-pdf -m auto` on the result pages before R100 to pin exact β. |

## 5. bikard2013 — sample + estimator spec  ✅ RESOLVED

| Field | Value |
|-------|-------|
| Source PDF | `bench-mark/Management Science/w18958.pdf` |
| MinerU text | "…661 faculty scientists… period 1976 to 2006… seven departments (EECS, ChemE, MatSci, MechE, Biology, Chemistry, Physics)… exclude all scientists who ever took part in projects with more than 20 authors (5 Big-Science subfields)… TABLE 2: …5,964 observations." + "We use an OLS regression with department-year, individual scientist, and career stage fixed effect… robust standard errors clustered at the level of the individual scientist." |
| Resolved value | **N = 661 MIT faculty, 5,964 scientist-year observations, 1976–2006, 7 departments**, >20-author exclusion. **Estimator = OLS with 3-way FE (department-year + individual scientist + career-stage), robust SE clustered at scientist.** For H2/H3 the DV is log-transformed. |
| Adjudication note | Updates gold-chain fields 2 & 4 (adds 5,964 obs, 7 depts, >20-author exclusion, 3-way FE structure). IO design unchanged — bikard remains the DATA-SUB boundary case (private MIT data). |

## 6. bikard2013 — fixed-effects coefficients  ✅ HEADLINE β RESOLVED (cells via prose)

| Field | Value |
|-------|-------|
| MinerU text (table-mode `auto`) | Table *titles* extracted (TABLE 3–9); cell grids still render as headers, **but the result prose quotes the key coefficients directly**: Model (3-1) group-size coef = **0.099** (~10% more citations per added collaborator, highly significant → H1); Model (3-3) fractional-pubs group-size coef = **−0.069** (negative → H2); Models (5-1)/(5-2) concave relationship, inflection points **5.4** and **9.6**. Correlations (Table 2): group-size×year **+0.23**, NAuthors×Cites **+0.09**, NAuthors×NPubs **+0.13**, NAuthors×Frac_Pubs **−0.14**; productivity×year 0.20 (NPubs) / 0.11 (Frac_Pubs). Wald F-stats reported for group-size indicator regressions, e.g. F(9,660)=11.43 (Quality). |
| Status | Headline β resolved from prose. Full per-cell tables (3–9) still need manual read or a dedicated table extractor, but the load-bearing coefficients for H1/H2/H3 are pinned. |
| Adjudication note | Result-target refinement; does not block IO manipulation. bikard remains DATA-SUB boundary case. |

---

## Adjudicated gold-chain changes (summary)

| Paper | Field | Before | After (adjudicated) |
|-------|-------|--------|---------------------|
| funk2017 | 2 (sample) | "exact N not pinned" | 2.9M utility patents, 1977–2005 (excl 34,889 + 177) |
| maddi2024 | 2 (sample) | "time window not stated" | 2009–2020; N=57,482 (from 57,694 after IQR×5, −212) |
| maddi2024 | 4 (model) | "OLS-family" | **GLM, log(1+citations) DV** [correction] |
| maddi2024 | 3 (indicator) | "IV=report length" | IV = report length, Fisher-discretized into 5 classes; 947-word threshold |
| bikard2013 | 2 (sample) | "661 faculty, 1976–2006" | + 5,964 scientist-year obs; 7 depts; >20-author exclusion |
| bikard2013 | 4 (model) | "individual + year FE" | OLS + 3-way FE (department-year + individual + career-stage), robust SE clustered at scientist |

## IO manipulation design — unchanged

No change to IO₁ / IO₂ / IO₃ constructability for any paper. The adjudication touched only result-target fields (sample size, estimator spec, coefficients) — exactly the "result-target refinements" the user scoped. The highest-risk assumption (IO₂ cleanly isolates docs from code) is unaffected.

## Open cell-value items (non-blocking)

- maddi2024 per-class β (Tables 4–5) — pin via MinerU `auto` on result pages or manual read during R100 scoring.
- bikard2013 full per-cell tables (3–9) — headline β already pinned from prose (0.099, −0.069, inflection 5.4/9.6, correlations). Remaining cells are robustness-check detail.

These refine RRF (Result-Reference Fidelity) targets, not the IO design.
