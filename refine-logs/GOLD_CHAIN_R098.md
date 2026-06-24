# R098 — Pilot Gold-Chain Annotation (1 primary + 1 adjudication)

**Date**: 2026-06-24
**Annotator**: primary draft (Claude) — pending adjudication reviewer sign-off
**Status**: DRAFT — fields 1–9 filled for all 5 pilot papers. Numbers quoted from paper text; adjudicator to verify against source PDFs.

> Reuse: Petersen2024 and Arts2021 fields 1–6 carried from C0 (R002/R003) and consistency-checked against the v7.2 template. funk2017, maddi2024, bikard2013 read this pass.

---

## 1. Petersen2024 — `petersen2023_disruption_index` (Low / STRICT / SoS)

| # | Field | Gold |
|---|-------|------|
| 1 | Data source | Clarivate Web of Science + Microsoft Academic Graph (MAG). **Substitute available**: SciSciNet (N=469,855, local) — used in R002. Access: SciSciNet public/local; WoS paywalled. |
| 2 | Sample definition | N=469,855 papers (SciSciNet, matches R002/R004/R007); time window 1960s–2010s; all fields; publications + patents with complete citation data. |
| 3 | Indicator construction | Disruption index CDp = (Ni − Nj)/(Ni + Nj + Nk); plus citation-inflation decomposition (reference-list length, self-citations). Preprocessing: citation-network construction from reference lists. |
| 4 | Model specification | OLS regression with year FE. DV: disruption_index_CD. IV: citation_inflation, reference_list_length. Controls: team_size, citation_count. |
| 5 | Target results | ln_rp coef = −0.002322 (p<0.001); sample N exact 102,550 (2011–2015 subset, R002); R² = 0.120403 exact; all p-value significances match. Direction: NEGATIVE. |
| 6 | Main claim | CD systematically declines over time due to citation inflation (not true decline in innovation); unsuitable for cross-temporal analysis. Claim-result distance: small — claims directly supported by the negative coefficient. |
| 7 | Task-critical components | Result Table (STRICT numerical-identity target is the load-bearing pole) > Indicator > Model. |
| 8 | IO package feasibility | IO₁ ✓ (paper text — formula explicit) · IO₂ ✓ (paper + data dictionary + variable docs) · IO₃ ✓ (SciSciNet + R002 reproduce.py). **Cleanest Low anchor.** |
| 9 | Expected break risk | Low. B₂ Circularity only if agent hard-codes reported coefs. Calibration anchor — expected D3≈1.00 at IO₃. |
| **Consistency check vs v7.2 template** | ✅ All 9 fields map; fields 1–6 unchanged from C0; fields 7–9 newly formalized. |

---

## 2. Arts2021 — `arts2021_natural_language_processing` (Medium / METHOD / IS-Innovation)

| # | Field | Gold |
|---|-------|------|
| 1 | Data source | USPTO patent claims research dataset + PatentsView. Access: USPTO public; multi-step preprocessing P1–P10. |
| 2 | Sample definition | U.S. patent claims; sample construction via 10 preprocessing steps (P1–P10) — tokenization, lemmatization, stopword removal, n-gram extraction, etc. (per R003). |
| 3 | Indicator construction | 10 NLP indicators: I1–I5 novelty (5 formulas, all correct in R003); I6–I9 reuse indicators with **known aggregation-formula bug at lines 233–236** (|set|*(1+Σui) should be |set|+Σui); I5/I10 cosine-similarity. |
| 4 | Model specification | METHOD task — no single regression; descriptive aggregation of 10 indicators. No FE. |
| 5 | Target results | Cosine-similarity indicators I5, I10 match gold within 1–5% (R003). D1=1.00, D2=1.00, D3=0.80, D4=0.85, D5=0.85, Overall=0.90. |
| 6 | Main claim | NLP indicators identify the structure of innovation in patent claims; novelty vs reuse dimensions. Claim-result distance: moderate (aggregation bug means reuse claims partially under-supported). |
| 7 | Task-critical components | Indicator (multi-step, load-bearing) > Data Source > Sample. |
| 8 | IO package feasibility | IO₁ ✓ · IO₂ ✓ (paper + indicator defs + sample notes, no code) · IO₃ ✓ (USPTO sample + R003 reference code). Clean. |
| 9 | Expected break risk | **B₁ Substitution** (cosine-sim proxy) + **B₂ Circularity** (formula hard-code). Known localized break at Indicator component — ideal for testing break-localization (G4). |
| **Consistency check vs v7.2 template** | ✅ All 9 fields map; fields 1–6 from C0; fields 7–9 newly formalized. |

---

## 3. funk2017 — `funk2017_dynamic_network` (Medium-High / STRICT / Management)  ← NEW

| # | Field | Gold |
|---|-------|------|
| 1 | Data source | NBER U.S. Patent Citations Data File + **Patent Network Dataverse (Li et al.)** — both public. **Code public at cdindex.info** (calculates CDt/mCDt). Online appendix at doi.org/10.1287/mnsc.2015.2366. |
| 2 | Sample definition | University-related patents + federal-funding + commercial-engagement subsets; 14 NBER tech categories (Chemical, Computers, Drugs, Electrical, Mechanical, Others…); 5-year citation window (CD5/mCD5). Exact N not yet pinned (adjudicator to confirm from Table 1). |
| 3 | Indicator construction | **CDt index** = Eq. (1), range −1 to 1, mean 0.07, SD 0.23 (line 532). **mCDt index** = impact-weighted CDt, mean 0.31, SD 1.75 (line 548). Graph G(V1,V2,V3,E); −2 correction in numerator (line 455). |
| 4 | Model specification | OLS + **Negative Binomial regression** of CD5/mCD5 indexes (line 1780/1873). IVs: commercial engagement, federal support. DVs: CD5, mCD5. |
| 5 | Target results | CD5 positively correlated with impact (r=0.03, p<0.001, line 546); firm assignee r=−0.00 (p<0.01); universities r=0.02 (p<0.001); government r=0.02 (p<0.001). Table 1/3 numerical targets. |
| 6 | Main claim | The CDt/mCDt indexes measure technological change direction + magnitude; engagement & federal support positively related to disruption. Claim-result distance: small-moderate. |
| 7 | Task-critical components | Indicator (network-measure construction, load-bearing) > Model > Result. |
| 8 | IO package feasibility | IO₁ ✓ · IO₂ ✓ (paper + variable docs + sample notes, **no code**) · IO₃ ✓ (Dataverse data + **cdindex.info code**). **Strongest clean IO₃ in the pilot.** |
| 9 | Expected break risk | **B₂ Circularity** (hard-coding reported index values) + **B₁ Substitution** (Dataverse subset). Indicator is the stress point. |
| **Status** | Fields 2 (exact N) pending adjudicator confirmation from Table 1. |

---

## 4. maddi2024 — `maddi2024_peer_review_reports` (Medium / STRICT-DS / SoS)  ← NEW

| # | Field | Gold |
|---|-------|------|
| 1 | Data source | **Publons** (publons.com, reviewer-report length) + **Web of Science** (Clarivate, SCIE/SSCI/AHCI/CPCI-SSH/CPCI; bibliometric indicators). **Access risk**: Publons platform has changed since 2024 — access drift likely. |
| 2 | Sample definition | N = **57,482 publications** (line 57/653), Publons→WoS adjusted dataset. Time window: not explicitly stated (adjudicator to confirm). |
| 3 | Indicator construction | IV = **length of reviewer reports** (words; IQR computed, line 641 — outlier control). DV = citations received (bibliometric). Preprocessing: IQR-based outlier removal. |
| 4 | Model specification | **Robust regression** (line 63/201), OLS-family. One IV, one DV; controls via econometric model to neutralize confounders (line 197/233). |
| 5 | Target results | **Threshold finding**: beginning from **947 words**, report length significantly associated with increase in citations (line 63). Positive relationship (line 65/223). Exact coefficients in regression tables (adjudicator to pin). |
| 6 | Main claim | Longer reviewer reports → more citations (positive link), with a 947-word threshold. Claim-result distance: small. |
| 7 | Task-critical components | Data Source (Publons access drift, load-bearing) > Indicator (length measure) > Result. |
| 8 | IO package feasibility | IO₁ ✓ · IO₂ ✓ · IO₃ ⚠️ — WoS substitutable, **Publons partial** (access drift). IO₃ data-incomplete; flagged as partial-IO₃ case. |
| 9 | Expected break risk | **B₁ Substitution** (WoS-only proxy for Publons) + **B₂ Circularity** (coefficient hard-code). Data Source is the stress point. |
| **Status** | Exact time window + coefficients pending adjudicator confirmation. |

---

## 5. bikard2013 — `bikard2013_exploring_tradeoffs` (High / DATA-SUB / Management)  ← NEW, BOUNDARY CASE

| # | Field | Gold |
|---|-------|------|
| 1 | Data source | **Academic publications of 661 MIT faculty scientists** (line 42/132), over 30 years. **Private / institution-specific — NOT publicly available.** No public substitute at the faculty level. Designated DATA-SUB boundary case. |
| 2 | Sample definition | N = 661 MIT faculty; time window 1976–2006 (30-year period, per registry + line 42/133); scientist-year level analysis; researcher disambiguation required (MIT-internal). |
| 3 | Indicator construction | Collaboration measures (co-authorship) + scientific recognition (citations). Revealed-preference approach; quartile regressions on citation probability (line 238). Credit-allocation fraction α (line 499). |
| 4 | Model specification | **Individual + year fixed-effects regression** (line 909/918), scientist-year level. DVs: collaboration, credit (2 DVs per registry). IVs: 3. Controls: individual tendency, organizational environment. |
| 5 | Target results | Collaboration associated with more credit; up to 4 coauthors, collaboration associated with more papers/author (line 147–151). Credit sums to >1 across coauthors (line 154). Quartile-regression: collaboration reduces probability of poor citations (line 238). Exact coefficients in tables (adjudicator to pin). |
| 6 | Main claim | Tradeoff between collaboration and reward at individual faculty level; credit allocation not simply divided among authors. Claim-result distance: moderate — cross-institution generalization from single MIT sample is the stretch. |
| 7 | Task-critical components | Sample (faculty disambiguation, load-bearing) > Claim (generalization) > Model. |
| 8 | IO package feasibility | IO₁ ✓ · IO₂ ⚠️ (paper + variable docs, but **sample cannot be reconstructed** → forces substitution) · IO₃ ✗ (**no original code/data** → IO₃ collapses to IO₂). **The boundary case.** |
| 9 | Expected break risk | **B₁ Substitution** (SciSciNet/institute proxy for MIT faculty — highest risk) + **B₄ Assertion** (cross-institution claim stretch from single-institution data). Sample + Claim stress points. |
| **Status** | Exact coefficients pending adjudicator confirmation. The IO₃ collapse is **by design** — it is the diagnostic boundary case (demonstrates the IO bound where data is genuinely unavailable). |

---

## Adjudication review checklist (for reviewer)

- [ ] Confirm funk2017 exact N (Table 1) — field 2.
- [ ] Confirm maddi2024 time window + regression coefficients — fields 2, 5.
- [ ] Confirm bikard2013 fixed-effects coefficients — field 5.
- [ ] Verify all quoted line numbers against source PDFs.
- [ ] Sign off fields 7–9 (task-critical components, IO feasibility, break risk) for all 5.
- [ ] Below-α components flagged (Claim α target 0.60 — qualitative treatment if unmet).

## Outcome of R098

- 5/5 pilot papers have a gold-chain draft (fields 1–9).
- 2/5 fully anchored (Petersen, Arts — from C0, consistency-checked).
- 3/5 newly read (funk2017, maddi, bikard) — 6 numeric details pending adjudicator confirmation (none block the IO manipulation design; all are result-target details refinable in R100 scoring).
- **IO₃ constructability confirmed**: 3 clean (Petersen, Arts, funk2017), 1 partial (maddi — Publons drift), 1 boundary (bikard — by design). This matches the R096 feasibility table.
