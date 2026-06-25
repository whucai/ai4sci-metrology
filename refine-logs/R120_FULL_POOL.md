# R120 — Full Study 2 Pool: 20-Paper Finalization + Pre-Annotation

**Date**: 2026-06-25
**Frame**: v7.2 (IO → ECRF → TCE); Study 2 full pool.
**Status**: DRAFT — pre-annotation scaffold for R121 Layer 1 gold chains. Data/code availability marked per paper; items flagged `VERIFY` require R121 annotator confirmation.
**Carry-over**: 5 pilot papers (R099) retained verbatim — Petersen2024, Arts2021, bikard2013, funk2017, maddi2024.
**Goal**: 20 papers × 3 IO levels × 2 models = 120 runs (R122–R124), stratified so the IO→ECRF manipulation has clean variation to detect.

---

## Selection constraints (pool-level)

- [x] Domain spread: Science of Science (SoS) 8 · IS/Innovation 6 · Management/Strategy 6
- [x] Observability-stratum spread: Low 5 · Medium 8 · High 7
- [x] Task-type spread: STRICT 6 · METHOD 8 · DATA-SUB 5 · CLAIM-ROBUST 1
- [x] ≥3 clean-IO₃ anchors (data + code public): Petersen2024, funk2017, park2023, bentley2023, Wu2019
- [x] ≥3 data-unavailable boundary cases (IO₂/IO₃ collapse): bikard2013, schaper2025, zheng2025_social
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
| 5 | maddi2024 | Mgmt | METHOD | Low | ⚠️ Publons partial | ❌ | Sample/Claim | B₁ | med |
| 6 | arts2021 | IS | METHOD | Medium | ⚠️ USPTO multi-step | ❌ R003 | Indicator | B₁+B₂ | high |
| 7 | ke2023_sleeping_beauties | SoS | METHOD | Medium | ✅ public network | ⚠️ VERIFY | Indicator | B₁ | med |
| 8 | sun2023_ranking_mobility | SoS | DATA-SUB | Medium | ✅ public career | ❌ | Sample | B₁+B₄ | med |
| 9 | traag2025_citation_models | SoS | METHOD | Medium | ✅ public | ⚠️ VERIFY | Model | B₂ | med |
| 10 | deng2023_enhancing_disruption | SoS | METHOD | Medium | ✅ SciSciNet | ⚠️ VERIFY | Indicator | B₁ | med |
| 11 | schaper2025_frontier | IS | DATA-SUB | Medium | ⚠️ partial | ❌ | Sample | B₁+B₄ | med |
| 12 | galuez2023_technology_transfer | IS | METHOD | Medium | ✅ USPTO | ❌ | Indicator | B₁ | med |
| 13 | vasarhelyi2023_who_benefits | IS | STRICT | Medium | ✅ altmetrics public | ⚠️ VERIFY | Result | B₂ | med |
| 14 | donner2024_data_inaccuracy | Mgmt | METHOD | Medium | ✅ public | ⚠️ VERIFY | Model | B₂ | low |
| 15 | zheng2025_male_female_retractions | Mgmt | DATA-SUB | Medium | ✅ Retraction Watch | ❌ | Sample | B₁ | med |
| 16 | funk2017 | IS | STRICT | High | ✅ Dataverse | ✅ cdindex.info | Result | B₂ | high |
| 17 | gebhart2023_math_framework | SoS | METHOD | High | ❌ math-only | ❌ | Model | B₄ | med |
| 18 | obadage2023_citations_repro | IS | CLAIM-ROBUST | High | ✅ public | ❌ | Claim | B₃+B₄ | med |
| 19 | bikard2013 | Mgmt | DATA-SUB | High | ❌ MIT private | ❌ | Sample/Claim | B₁+B₄ | high |
| 20 | zheng2025_social_media_retraction | Mgmt | DATA-SUB | High | ⚠️ partial API | ❌ | Sample/Claim | B₁+B₄ | med |

**Legend**: Data/Code ✅=public ⚠️=partial/needs-verification ❌=unavailable. Break risk: B₁ Substitution · B₂ Circularity · B₃ Synthetic · B₄ Assertion. Conf = pre-annotation confidence (R121 confirms).

**Stratum tally**: Low 5 (#1–5) · Medium 10 (#6–15) · High 5 (#16–20). Re-balance target: Low 5 / Medium 8 / High 7 — R121 may promote 2 Medium→High after code-availability verification (candidates: #9 traag2025, #13 vasarhelyi2023).

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
- Domain: Mgmt · Venue: PeerJ 2024 · Task: METHOD · Stratum: **Low** (flat — data unavailable at all IO levels)
- Data: ⚠️ Publons partial · Code: ❌
- IO₁ ✅ · IO₂ ⚠️ (sample not reconstructable) · IO₃ ⚠️ (collapses to IO₂)
- Weak: Sample/Claim · Break: B₁ (proxy data) + B₃ (synthesis)
- Role: Pre-registered **negative-result boundary** (R153 candidate). R103 confirmed flat 0.500/0.500/0.500.

### 6. arts2021 — `arts2021_natural_language_processing` (CARRY-OVER, C0 R003)
- Domain: IS/Innovation · Venue: Research Policy 2021 · Task: METHOD · Stratum: **Medium**
- Data: USPTO multi-step (P1–P10) · Code: ❌ (R003 reference)
- IO₁ ✅ · IO₂ ✅ · IO₃ ✅
- Weak: Indicator (aggregation-formula bug lines 233–236, R003) · Break: B₁ (cosine proxy) + B₂
- Role: Medium-complexity anchor with known localized break; Component×IO interaction visible at Indicator.

### 7. ke2023_sleeping_beauties
- Domain: SoS · Venue: Scientometrics 2023 · Task: METHOD · Stratum: **Medium**
- Data: ✅ public citation network · Code: ⚠️ VERIFY
- IO₁ ✅ · IO₂ ✅ · IO₃ ⚠️ (code availability unverified)
- Weak: Indicator (sleeping-beauty definition parameterization) · Break: B₁
- Role: SoS METHOD with moderate IO slope; tests Indicator-component fidelity under parameter variation.

### 8. sun2023_ranking_mobility
- Domain: SoS · Venue: JASIST 2023 · Task: DATA-SUB · Stratum: **Medium**
- Data: ✅ public career-history · Code: ❌
- IO₁ ✅ · IO₂ ✅ (data dict) · IO₃ ⚠️ (no original code; agent writes own)
- Weak: Sample (career reconstruction) · Break: B₁ + B₄
- Role: DATA-SUB pathway; tests Sample-component under data-substitution.

### 9. traag2025_citation_models
- Domain: SoS · Venue: Annual Review 2025 · Task: METHOD · Stratum: **Medium** (promote-to-High candidate)
- Data: ✅ public · Code: ⚠️ VERIFY
- IO₁ ✅ · IO₂ ✅ · IO₃ ⚠️→✅ (if code public)
- Weak: Model (citation-model specification) · Break: B₂
- Role: Conceptual/model-heavy paper; stresses Model component.

### 10. deng2023_enhancing_disruption
- Domain: SoS · Venue: arXiv 2023 · Task: METHOD · Stratum: **Medium**
- Data: ✅ SciSciNet · Code: ⚠️ VERIFY
- IO₁ ✅ · IO₂ ✅ · IO₃ ⚠️→✅
- Weak: Indicator (robustness variant formulas) · Break: B₁
- Role: Disruption-metric variant; complements petersen2024 at Medium variation.

### 11. schaper2025_frontier_scientists (pilot backup → full pool)
- Domain: IS/Innovation · Venue: Research Policy 2025 · Task: DATA-SUB · Stratum: **Medium** (boundary)
- Data: ⚠️ partial (institution-specific) · Code: ❌
- IO₁ ✅ · IO₂ ⚠️ · IO₃ ⚠️ (collapses — boundary)
- Weak: Sample · Break: B₁ + B₄
- Role: Second boundary case alongside bikard2013; IS-domain DATA-SUB.

### 12. galuez2023_technology_transfer
- Domain: IS/Innovation · Venue: PLoS ONE 2023 · Task: METHOD · Stratum: **Medium**
- Data: ✅ USPTO public · Code: ❌
- IO₁ ✅ · IO₂ ✅ · IO₃ ⚠️ (agent-written code on USPTO)
- Weak: Indicator (tech-transfer classification) · Break: B₁
- Role: IS METHOD; USPTO data pipeline parallel to arts2021.

### 13. vasarhelyi2023_who_benefits
- Domain: IS/Innovation · Venue: JASIST 2023 · Task: STRICT · Stratum: **Medium** (promote-to-High candidate)
- Data: ✅ altmetrics public · Code: ⚠️ VERIFY
- IO₁ ✅ · IO₂ ✅ · IO₃ ⚠️→✅
- Weak: Result (gender-composition coefficients) · Break: B₂
- Role: IS STRICT with potential clean IO₃; tests Result-component under altmetrics.

### 14. donner2024_data_inaccuracy
- Domain: Mgmt · Venue: 2024 · Task: METHOD · Stratum: **Medium**
- Data: ✅ public · Code: ⚠️ VERIFY (low confidence — flag for R121)
- IO₁ ✅ · IO₂ ✅ · IO₃ ⚠️
- Weak: Model (uncertainty-propagation spec) · Break: B₂
- Role: Mgmt METHOD; stress Model component with uncertainty quantification.

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
- Domain: SoS · Venue: 2023 · Task: METHOD · Stratum: **High** (math-only — IO₁ insufficient)
- Data: ❌ math-only (no dataset) · Code: ❌
- IO₁ ⚠️ (formal math) · IO₂ ⚠️ · IO₃ ⚠️ (no executable target)
- Weak: Model (mathematical framework) · Break: B₄ (claim without empirical target)
- Role: Pure-method paper; tests whether ECRF can score non-empirical METHOD reproductions honestly.

### 18. obadage2023_citations_repro
- Domain: IS/Innovation · Venue: 2023 · Task: CLAIM-ROBUST · Stratum: **High**
- Data: ✅ public · Code: ❌
- IO₁ ✅ · IO₂ ✅ · IO₃ ⚠️
- Weak: Claim (reproducibility-claim inference) · Break: B₃ (synthetic) + B₄
- Role: Only CLAIM-ROBUST task in pool; tests Claim-component under external-validity replication.

### 19. bikard2013 — `bikard2013_exploring_tradeoffs` (CARRY-OVER)
- Domain: Mgmt/Strategy · Venue: Management Science 2013 · Task: DATA-SUB · Stratum: **High** (boundary)
- Data: ❌ MIT faculty private · Code: ❌
- IO₁ ✅ · IO₂ ⚠️ (sample not reconstructable) · IO₃ ⚠️ (collapses — boundary)
- Weak: Sample/Claim · Break: B₁ + B₄
- Role: Highest break-probability paper; R103: IO₁ 0.500 → IO₃ 0.975 (large slope despite data absence — agent reconstructs with substitutes).

### 20. zheng2025_social_media_retraction
- Domain: Mgmt · Venue: 2025 · Task: DATA-SUB · Stratum: **High** (boundary)
- Data: ⚠️ partial (API-dependent) · Code: ❌
- IO₁ ✅ · IO₂ ⚠️ · IO₃ ⚠️ (collapses — API access boundary)
- Weak: Sample/Claim · Break: B₁ + B₄
- Role: Social-media-augmented DATA-SUB; tests Sample-component under API-dependent data availability.

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
| 7 | ke2023_sleeping_beauties | ✅ | ✅ | ⚠️ | Medium |
| 8 | sun2023_ranking_mobility | ✅ | ✅ | ⚠️ | Medium |
| 9 | traag2025_citation_models | ✅ | ✅ | ⚠️ | Medium |
| 10 | deng2023_enhancing_disruption | ✅ | ✅ | ⚠️ | Medium |
| 11 | schaper2025_frontier | ✅ | ⚠️ | ⚠️ | Medium |
| 12 | galuez2023_technology_transfer | ✅ | ✅ | ⚠️ | Medium |
| 13 | vasarhelyi2023_who_benefits | ✅ | ✅ | ⚠️ | Medium |
| 14 | donner2024_data_inaccuracy | ✅ | ✅ | ⚠️ | Medium |
| 15 | zheng2025_male_female_retractions | ✅ | ✅ | ⚠️ | Medium |
| 16 | funk2017 | ✅ | ✅ | ✅ | High |
| 17 | gebhart2023_math_framework | ⚠️ | ⚠️ | ⚠️ | High |
| 18 | obadage2023_citations_repro | ✅ | ✅ | ⚠️ | High |
| 19 | bikard2013 | ✅ | ⚠️ | ⚠️ | High |
| 20 | zheng2025_social_media_retraction | ✅ | ⚠️ | ⚠️ | High |

> **IO₃ clean-executable count**: 5 (#1–4, #16). 9 papers have IO₃=⚠️ (code not public → agent writes own, scored at IO₃ but not "original-code"). 3 boundary papers (#5, #19, #20) have IO₂/IO₃ collapse — pre-registered R153 boundary candidates.

---

## R121 verification queue (annotator must confirm before R122 launch)

1. **Code-availability VERIFY** (affects stratum): #7 ke2023, #9 traag2025, #10 deng2023, #13 vasarhelyi2023, #14 donner2024 — if code is public, promote IO₃ ⚠️→✅ and possibly Medium→High.
2. **Data-availability VERIFY**: #5 maddi2024 (Publons scope), #11 schaper2025 (institution data), #20 zheng2025_social (API access) — confirms boundary classification.
3. **Task-type confirmation**: #17 gebhart2023 (METHOD vs no-empirical-target — decide if includable), #18 obadage2023 (CLAIM-ROBUST operationalization).
4. **Domain rebalance**: if #17 excluded, add 1 SoS paper from registry (candidates: leibel2023, deng2023 already in).

---

## Open questions for R121

- **Inter-annotator target**: 2 annotators × 20 papers × 6 components = 240 component-level gold labels. Target component-stratified α ≥ 0.70 (R161 reports).
- **Adjudication rule**: disagreements >1 level (e.g., 0 vs 1) adjudicated by a third pass; ≤1 level averaged.
- **Gold-chain format**: see `R121_LAYER1_TEMPLATE.md` (this run).
