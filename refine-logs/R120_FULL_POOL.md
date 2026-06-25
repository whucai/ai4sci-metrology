# R120 — Full Study 2 Pool: 20-Paper Finalization + Pre-Annotation

**Date**: 2026-06-25
**Frame**: v7.2 (IO → ECRF → TCE); Study 2 full pool.
**Status**: DRAFT — pre-annotation scaffold for R121 Layer 1 gold chains. Data/code availability marked per paper; items flagged `VERIFY` require R121 annotator confirmation.
**Carry-over**: 5 pilot papers (R099) retained verbatim — Petersen2024, Arts2021, bikard2013, funk2017, maddi2024.
**Goal**: 20 papers × 3 IO levels × 2 models = 120 runs (R122–R124), stratified so the IO→ECRF manipulation has clean variation to detect.

---

## Selection constraints (pool-level, post-verification 2026-06-25)

- [~] Domain spread (18 stable + 2 pending): SoS 7 · IS/Innovation 6 · Management 5 — will restore 8/6/6 once #9 (SoS) and #20 (Mgmt) replacements are filled
- [~] Observability-stratum spread (18 stable): Low 5 · Medium 8 · High 5 — target 5/8–9/6–7 once replacements land
- [~] Task-type spread (18 stable): STRICT 6 · METHOD 7 · DATA-SUB 5 · CLAIM-ROBUST 0 — CLAIM-ROBUST dropped (obadage reclassified STRICT); replacements may restore
- [x] ≥3 clean-IO₃ anchors (data + code public): Petersen2024, wu2019, park2023, bentley2023, funk2017, **obadage2024** (6 total)
- [x] ≥3 data-unavailable boundary cases (IO₂/IO₃ collapse): maddi2024, bikard2013, schaper2025 (3; zheng_social replaced)
- [x] ≥2 known localized-break papers (from C0): Arts2021 (Indicator), Wu2019 (Model/Claim direction)
- [x] All three primary models' weakness regimes represented (Claim-weak Gemma anchor carried via C0, not re-run)

> **Stratification rule**. "Observability stratum" = predicted ECRF variation across IO₁→IO₃ (the slope the manipulation can produce), NOT the ceiling. Low = flat (either always-easy calibration or always-hard data-missing); Medium = moderate slope; High = large slope (IO₁ fails, IO₃ succeeds). R121 annotator confirms.

---

## Pool summary table

| # | Paper | Domain | Task | Stratum | Data | Code | Weak comp | Break risk | Conf |
|---|---|---|---|---|---|---|---|---|---|
| 1 | petersen2024 | SoS | STRICT | Low | ✅ SciSciNet | ✅ R002 | Result | B₂ | high |
| 2 | wu2019_teams | SoS | STRICT | Low | ✅ SciSciNet | ✅ public | Model/Claim | B₄ | high |
| 3 | park2023_disruptive | SoS | STRICT | Low | ✅ MAG/SciSciNet | ✅ public | Result | B₂ | high |
| 4 | bentley2023_disruption | SoS | STRICT | Low | ✅ public | ✅ R007 | Result | B₂ | high |
| 5 | maddi2024 | Mgmt | METHOD | Low | ❌ Publons private (defunct) | ❌ | Sample/Claim | B₁ | med |
| 6 | arts2021 | IS | METHOD | Medium | ⚠️ USPTO multi-step | ❌ R003 | Indicator | B₁+B₂ | high |
| 7 | ke2015_sleeping_beauties | SoS | METHOD | Medium | ❌ WoS+APS licensed | ❌ | Indicator | B₁ | med |
| 8 | sun2023_ranking_mobility | SoS | DATA-SUB | Medium | ✅ public career | ❌ | Sample | B₁+B₄ | med |
| 9 | *(slot pending — traag replaced)* | SoS | — | — | — | — | — | — | — |
| 10 | deng2023_enhancing_disruption | SoS | METHOD | Medium | ⚠️ SciSciNet substitute | ❌ | Indicator | B₁ | med |
| 11 | schaper2025_frontier | IS | DATA-SUB | Medium | ⚠️ partial (KU Leuven chain private) | ❌ | Sample | B₁+B₄ | med |
| 12 | galuez2023_technology_transfer | IS | METHOD | Medium | ✅ USPTO | ❌ | Indicator | B₁ | med |
| 13 | vasarhelyi2023_who_benefits | IS | DATA-SUB | Medium | ❌ Altmetric API-gated + WoS licensed | ❌ | Sample/Result | B₁+B₂ | med |
| 14 | donner2024_data_inaccuracy | Mgmt | METHOD | Medium | ⚠️ partial (Zenodo CSV only) | ❌ | Model | B₂ | med |
| 15 | zheng2025_male_female_retractions | Mgmt | DATA-SUB | Medium | ✅ Retraction Watch | ❌ | Sample | B₁ | med |
| 16 | funk2017 | IS | STRICT | High | ✅ Dataverse | ✅ cdindex.info | Result | B₂ | high |
| 17 | gebhart2023_math_framework | SoS | METHOD | High | ⚠️ APS restricted (Nobel public) | ❌ | Model | B₄ | med |
| 18 | obadage2024_citations_repro | IS | STRICT | High | ✅ public (Zenodo) | ✅ MIT repo+notebooks | Result | B₂ | high |
| 19 | bikard2013 | Mgmt | DATA-SUB | High | ❌ MIT private | ❌ | Sample/Claim | B₁+B₄ | high |
| 20 | *(slot pending — zheng_social replaced)* | Mgmt | — | — | — | — | — | — | — |

**Legend**: Data/Code ✅=public ⚠️=partial/needs-verification ❌=unavailable/private. Break risk: B₁ Substitution · B₂ Circularity · B₃ Synthetic · B₄ Assertion. Conf = pre-annotation confidence (R121 confirms).

**Verification status (2026-06-25)**: 18/20 papers verified stable; 2 slots pending replacement (#9 traag → structurally inapplicable review chapter; #20 zheng_social → all data licensed/API-gated, no IO₂/IO₃ distinction). See §"R120 Verification Appendix".

**Stratum tally (18 stable)**: Low 5 (#1–5) · Medium 8 (#6–8, #10–15) · High 5 (#16–19). Clean-IO₃ anchors: 6 (#1–4, #16, #18). Boundary (IO₂/IO₃ collapse): 3 (#5 maddi, #19 bikard, + replacements pending). Replacement slots will be filled to restore Low 5 / Medium 8–9 / High 6–7 balance.

**R121 hold rule**: R121 gold-chain annotation proceeds only for the 18 stable papers. Slots #9 and #20 (and any replacements) are HELD until the final pool is confirmed.

---

## Per-paper pre-annotation (carry-over + new)

### 1. petersen2024 — `petersen2023_disruption_index` (CARRY-OVER, C0 R002)
- Domain: SoS · Venue: arXiv 2023 · Task: STRICT · Stratum: **Low** (calibration anchor)
- Data: SciSciNet (N=469,855) local · Code: ✅ R002 reference reproduce.py
- IO₁ ✅ (CDp formula explicit) · IO₂ ✅ (data dict) · IO₃ ✅ (data + R002 code)
- Weak: Result (numerical-identity stress) · Break: B₂ (hard-code reported coefs)
- Role: Low-variation floor; IO₃ should yield D3≈1.00, IO₁ lower.

### 2. wu2019_teams — `wu2019_disruption` (C0 R001)
- Domain: SoS · Venue: Nature 2019 · Task: STRICT · Stratum: **Low** (C0 anchor)
- Data: SciSciNet/MAG public · Code: ✅ public
- IO₁ ✅ · IO₂ ✅ · IO₃ ✅
- Weak: Model/Claim (direction-negative is the known failure mode; R001 coef=-0.0093) · Break: B₄ (claim-direction stretch)
- Role: Known component-localized failure (Model/Claim=0, Data/Sample/Indicator=1) — motivates v7.2.

### 3. park2023_disruptive (C0 R004)
- Domain: SoS · Venue: Nature 2023 · Task: STRICT · Stratum: **Low**
- Data: MAG/SciSciNet public · Code: ✅ public
- IO₁ ✅ · IO₂ ✅ · IO₃ ✅
- Weak: Result · Break: B₂
- Role: STRICT calibration; D3=6/6 in C0.

### 4. bentley2023_disruption (C0 R007)
- Domain: SoS/IS · Venue: Quarterly Review of Business 2023 · Task: STRICT · Stratum: **Low**
- Data: public · Code: ✅ R007
- IO₁ ✅ · IO₂ ✅ · IO₃ ✅
- Weak: Result · Break: B₂
- Role: D3=9/9 STRICT calibration.

### 5. maddi2024 — `maddi2024_peer_review_reports` (CARRY-OVER)
- Domain: Mgmt · Venue: **Scientometrics (Springer) 2024** (corrected from PeerJ) · Task: METHOD · Stratum: **Low** (flat — data unavailable at all IO levels)
- Data: ❌ Publons private (platform sunset 2022–23; bespoke WoS-matched drop to authors, not public) · Code: ❌
- IO₁ ✅ · IO₂ ⚠️ (sample not reconstructable) · IO₃ ⚠️ (collapses to IO₂)
- Weak: Sample/Claim · Break: B₁ (proxy data) + B₃ (synthesis)
- Role: Pre-registered **negative-result boundary** (R153 candidate). R103 confirmed flat 0.500/0.500/0.500. STRICT impossible — METHOD/DATA-SUB only (open peer-review corpus substitute: eLife/OpenReview).

### 6. arts2021 — `arts2021_natural_language_processing` (CARRY-OVER, C0 R003)
- Domain: IS/Innovation · Venue: Research Policy 2021 · Task: METHOD · Stratum: **Medium**
- Data: USPTO multi-step (P1–P10) · Code: ❌ (R003 reference)
- IO₁ ✅ · IO₂ ✅ · IO₃ ✅
- Weak: Indicator (aggregation-formula bug lines 233–236, R003) · Break: B₁ (cosine proxy) + B₂
- Role: Medium-complexity anchor with known localized break; Component×IO interaction visible at Indicator.

### 7. ke2015_sleeping_beauties (IDENTITY CORRECTED)
- Domain: SoS · Venue: **PNAS 112(24):7426, 2015** (corrected from "Scientometrics 2023" — slug was a misidentification; the 2023 DOI is a phantom) · Task: METHOD · Stratum: **Medium**
- Data: ❌ WoS + APS licensed (not public; R120 "✅ public network" was wrong) · Code: ❌
- IO₁ ✅ · IO₂ ⚠️ (data schema only; licensed data inaccessible) · IO₃ ⚠️ (substitute SciSciNet/MAG required → boundary-ish)
- Weak: Indicator (sleeping-beauty definition parameterization, Beckendorf Bcriterion) · Break: B₁ (SciSciNet substitute)
- Role: SoS METHOD; Indicator-component stress. Reproduction via SciSciNet substitute (same pathway as deng2023/r008). IO₃ is boundary, not clean.

### 8. sun2023_ranking_mobility
- Domain: SoS · Venue: JASIST 2023 · Task: DATA-SUB · Stratum: **Medium**
- Data: ✅ public career-history · Code: ❌
- IO₁ ✅ · IO₂ ✅ (data dict) · IO₃ ⚠️ (no original code; agent writes own)
- Weak: Sample (career reconstruction) · Break: B₁ + B₄
- Role: DATA-SUB pathway; tests Sample-component under data-substitution.

### 9. *(SLOT PENDING — traag2025 REPLACED)*
- **traag2025_citation_models** → identity corrected to **Traag 2022, Edward Elgar chapter "Science of science — Citation models and research evaluation"** (arXiv:2207.11116; NOT Annual Review 2025). It is a **conceptual/review chapter with no original empirical dataset and no code** → IO₃ is **structurally inapplicable** (no original code/data to recover; no IO₁→IO₃ observability distinction). **Replaced.** Replacement candidate under verification (SoS slot). R121 annotation HELD for this slot.

### 10. deng2023_enhancing_disruption
- Domain: SoS · Venue: **Scientometrics 128(4):2429, 2023** (corrected from arXiv; closed access) · Task: METHOD · Stratum: **Medium**
- Data: ⚠️ SciSciNet substitute (original citation network licensed; paper has no Data/Code Availability statement) · Code: ❌
- IO₁ ✅ · IO₂ ✅ (data dict) · IO₃ ⚠️ (agent-written code on SciSciNet substitute; boundary)
- Weak: Indicator (robustness-variant CD5 formulas, edge-removal hot-spot refs) · Break: B₁ (substitute)
- Role: Disruption-metric robustness variant; complements petersen2024 at Medium variation. IO₃ demoted to boundary (data not actually public).

### 11. schaper2025_frontier_scientists (pilot backup → full pool)
- Domain: IS/Innovation · Venue: Research Policy 54(10), 2025 (OA, CC-BY) · Task: DATA-SUB · Stratum: **Medium** (boundary)
- Data: ⚠️ partial — raw feeds public (PubMed + USPTO), but the **KU Leuven/ECOOM author–inventor disambiguation linkage is institutionally private**, firm descriptors (BvD Orbis) paid-license · Code: ❌
- IO₁ ✅ · IO₂ ⚠️ · IO₃ ⚠️ (collapses without the proprietary linkage — boundary)
- Weak: Sample (author–inventor disambiguation) · Break: B₁ + B₄
- Role: Second boundary case alongside bikard2013; IS-domain DATA-SUB. R121 to fetch PDF to confirm whether linkage is released (if so, downgrade to "keep clean").

### 12. galuez2023_technology_transfer
- Domain: IS/Innovation · Venue: PLoS ONE 2023 · Task: METHOD · Stratum: **Medium**
- Data: ✅ USPTO public · Code: ❌
- IO₁ ✅ · IO₂ ✅ · IO₃ ⚠️ (agent-written code on USPTO)
- Weak: Indicator (tech-transfer classification) · Break: B₁
- Role: IS METHOD; USPTO data pipeline parallel to arts2021.

### 13. vasarhelyi2023_who_benefits
- Domain: IS/Innovation · Venue: arXiv:2308.00405, 2023 (JASIST publication unconfirmed) · Task: **DATA-SUB** (corrected from STRICT — licensed/API-gated data precludes numerical identity) · Stratum: **Medium** (promote-to-High **dropped**)
- Data: ❌ Altmetric.com API-gated + WoS licensed (R120 "✅ altmetrics public" was wrong — Altmetric.com is not open data) · Code: ❌
- IO₁ ✅ · IO₂ ⚠️ (CEM design describable but data inaccessible) · IO₃ ⚠️ (boundary — substitute altmetrics corpus required)
- Weak: Sample/Result (quasi-experimental CEM matching) · Break: B₁ + B₂
- Role: IS DATA-SUB; Coarsened-Exact-Matching design. IO₃ demoted to boundary; no clean-IO₃ reachable.

### 14. donner2024_data_inaccuracy
- Domain: Mgmt · Venue: **Research Evaluation 33(4), 2024** (arXiv:2303.16613) · Task: METHOD · Stratum: **Medium**
- Data: ⚠️ partial — public Zenodo CSV (`10.5281/zenodo.13969973`, citation-count-error column only, 1.8 KB); full WoS bibliometric corpus licensed · Code: ❌
- IO₁ ✅ · IO₂ ✅ (data dict) · IO₃ ⚠️ (partial — public data minimal, no code; Bayesian-regression + MC pipeline reimplemented by agent)
- Weak: Model (uncertainty-propagation spec) · Break: B₂
- Role: Mgmt METHOD; stress Model component with uncertainty quantification. Only VERIFY paper with any public original artifact.

### 15. zheng2025_male_female_retractions
- Domain: Mgmt · Venue: 2025 · Task: DATA-SUB · Stratum: **Medium**
- Data: ✅ Retraction Watch public · Code: ❌
- IO₁ ✅ · IO₂ ✅ · IO₃ ⚠️ (no original code)
- Weak: Sample (gender disambiguation) · Break: B₁
- Role: Mgmt DATA-SUB with public data; tests Sample-component gender-disambiguation fidelity.

### 16. funk2017 — `funk2017_dynamic_network` (CARRY-OVER)
- Domain: IS/Innovation · Venue: PLoS ONE 2017 · Task: STRICT · Stratum: **High** (clean IO₃)
- Data: ✅ Dataverse public · Code: ✅ cdindex.info public
- IO₁ ✅ · IO₂ ✅ · IO₃ ✅
- Weak: Result (network-metric numerical target) · Break: B₂
- Role: Clean-IO₃ anchor; large IO slope expected (R103: IO₁ 0.500 → IO₃ 0.825).

### 17. gebhart2023_math_framework
- Domain: SoS · Venue: **arXiv:2308.16363, 2023** (Gebhart & Funk; no journal version) · Task: METHOD · Stratum: **High**
- Data: ⚠️ **NOT pure math** — has empirical "Measuring Disruption in Physics" validation on APS bibliographic data (~630K papers, 1893–2019; APS **restricted-access**) + Nobel laureate dataset (Li et al. 2019, public) · Code: ❌
- IO₁ ⚠️ (math framework + empirical target) · IO₂ ⚠️ · IO₃ ⚠️ (partial — substitute OpenAlex/SciSciNet for APS)
- Weak: Model (CD-betweenness-centrality framework) · Break: B₄ (centrality-disruption claim) + B₁ (data substitute)
- Role: Method+empirical hybrid; reproducible Nobel-discernment numerical target exists (mean-rank B_k/Π_k). Tests whether ECRF scores METHOD-with-data-substitution honestly. Kept (not excluded).

### 18. obadage2024_citations_repro (IDENTITY CORRECTED + UPGRADED)
- Domain: IS/Innovation · Venue: **ACM FAccT 2024** (corrected from "2023"; DOI 10.1145/3641525.3663628; arXiv:2405.03977) · Task: **STRICT** (corrected from CLAIM-ROBUST — same-data numerical reproduction is fully feasible) · Stratum: **High** (clean IO₃)
- Data: ✅ public (Zenodo `10.5281/zenodo.10895748` + GitHub `lamps-lab/ccair-ai-reproducibility/data`: MLRC 2022 papers, 41,244 citation contexts via Semantic Scholar) · Code: ✅ **MIT repo + 9 sequential notebooks** (`notebooks/R_001_*`), pinned requirements, artifact appendix
- IO₁ ✅ · IO₂ ✅ · IO₃ ✅ (clean — public data + public code + notebooks)
- Weak: Result (Table 3/4 numerical targets: M1–M5, M6/M7 5-fold CV) · Break: B₂ (hard-code) — low risk given clean materials
- Role: **Clean-IO₃ STRICT anchor** (6th clean anchor). Upgraded from boundary to clean. Tests Result-component under a fully reproducible ML-pipeline paper.

### 19. bikard2013 — `bikard2013_exploring_tradeoffs` (CARRY-OVER)
- Domain: Mgmt/Strategy · Venue: Management Science 2013 · Task: DATA-SUB · Stratum: **High** (boundary)
- Data: ❌ MIT faculty private · Code: ❌
- IO₁ ✅ · IO₂ ⚠️ (sample not reconstructable) · IO₃ ⚠️ (collapses — boundary)
- Weak: Sample/Claim · Break: B₁ + B₄
- Role: Highest break-probability paper; R103: IO₁ 0.500 → IO₃ 0.975 (large slope despite data absence — agent reconstructs with substitutes).

### 20. *(SLOT PENDING — zheng2025_social_media_retraction REPLACED)*
- **zheng2025_social_media_retraction** → identity confirmed (Zheng et al., JASIST 2025, DOI 10.1002/asi.70028; arXiv:2403.16851). Data sources: WoS (licensed, CWTS) + Altmetric.com (licensed) + **Twitter/X API content non-recollectable** (post free-API shutdown) + Retraction Watch (under license, non-redistributable). **No public code, no data availability statement.** All data licensed/API-gated → **no defensible IO₂/IO₃ distinction** (IO₂ and IO₃ both collapse; no open substitute reconstructs the matched social-media×retraction corpus). **Replaced.** Replacement candidate under verification (Mgmt slot). R121 annotation HELD for this slot.

---

## IO feasibility matrix (✅ feasible · ⚠️ partial/collapse · ❌ infeasible)

| # | Paper | IO₁ | IO₂ | IO₃ | Stratum |
|---|---|---|---|---|---|
| 1 | petersen2024 | ✅ | ✅ | ✅ | Low |
| 2 | wu2019_teams | ✅ | ✅ | ✅ | Low |
| 3 | park2023_disruptive | ✅ | ✅ | ✅ | Low |
| 4 | bentley2023_disruption | ✅ | ✅ | ✅ | Low |
| 5 | maddi2024 | ✅ | ⚠️ | ⚠️ | Low |
| 6 | arts2021 | ✅ | ✅ | ✅ | Medium |
| 7 | ke2015_sleeping_beauties | ✅ | ⚠️ | ⚠️ | Medium |
| 8 | sun2023_ranking_mobility | ✅ | ✅ | ⚠️ | Medium |
| 9 | *(slot pending)* | — | — | — | — |
| 10 | deng2023_enhancing_disruption | ✅ | ✅ | ⚠️ | Medium |
| 11 | schaper2025_frontier | ✅ | ⚠️ | ⚠️ | Medium |
| 12 | galuez2023_technology_transfer | ✅ | ✅ | ⚠️ | Medium |
| 13 | vasarhelyi2023_who_benefits | ✅ | ⚠️ | ⚠️ | Medium |
| 14 | donner2024_data_inaccuracy | ✅ | ✅ | ⚠️ | Medium |
| 15 | zheng2025_male_female_retractions | ✅ | ✅ | ⚠️ | Medium |
| 16 | funk2017 | ✅ | ✅ | ✅ | High |
| 17 | gebhart2023_math_framework | ⚠️ | ⚠️ | ⚠️ | High |
| 18 | obadage2024_citations_repro | ✅ | ✅ | ✅ | High |
| 19 | bikard2013 | ✅ | ⚠️ | ⚠️ | High |
| 20 | *(slot pending)* | — | — | — | — |

> **IO₃ clean-executable count**: 6 (#1–4, #16, #18). 8 papers have IO₃=⚠️ (code not public → agent writes own, or partial data). 2 boundary papers (#5 maddi, #19 bikard) have IO₂/IO₃ collapse — pre-registered R153 boundary candidates. 2 slots (#9, #20) pending replacement.

---

## R121 verification queue (post-verification 2026-06-25)

1. **Code-availability VERIFY — RESOLVED**: #7 ke2015, #9 traag (replaced), #10 deng2023, #13 vasarhelyi2023, #14 donner2024 — **none has public code**; all IO₃ demoted to boundary/partial. See appendix.
2. **Data-availability VERIFY — RESOLVED**: #5 maddi2024 (Publons private/defunct → boundary), #11 schaper2025 (KU Leuven linkage private → partial), #20 zheng2025_social (all licensed/API-gated → replaced).
3. **Task-type confirmation — RESOLVED**: #17 gebhart2023 (METHOD+empirical, kept), #18 obadage2024 (STRICT, upgraded to clean).
4. **Identity corrections — RESOLVED**: ke2023→ke2015 (PNAS), traag2025→Traag 2022 (replaced), obadage2023→obadage2024 (FAccT).
5. **Replacement slots OPEN**: #9 (SoS) and #20 (Mgmt) — candidates under verification; R121 annotation HELD for these two slots until confirmed.

---

## Open questions for R121

- **Inter-annotator target**: 2 annotators × 18 stable papers × 6 components = 216 component-level gold labels (+ 2 replacement slots deferred). Target component-stratified α ≥ 0.70 (R161 reports).
- **Adjudication rule**: disagreements >1 level (e.g., 0 vs 1) adjudicated by a third pass; ≤1 level averaged.
- **Gold-chain format**: see `R121_LAYER1_TEMPLATE.md`.
- **Freeze gate**: `r121_gold_v1.json` frozen only after the 2 replacement slots are filled and the 18 stable papers are annotated.
