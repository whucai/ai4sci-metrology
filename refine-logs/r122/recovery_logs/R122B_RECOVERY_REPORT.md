# R122b — NO_PACKAGE Recovery Pass (2026-06-30)

**Scope**: recover legal full-text paper.md for the 4 NO_PACKAGE papers from R122 IO₁ (sun2023, deng2023, galuez2023, zheng2025_male). Sources searched: Crossref (DOI), Unpaywall (OA PDF), OpenAlex, Europe PMC, arXiv, Semantic Scholar, journal/author sites. **No abstracts as substitutes; no paywall bypass.**

## Recovery outcome

| paper | venue (corrected) | DOI | OA source | outcome | paper.md |
|---|---|---|---|---|---|
| sun2023_ranking_mobility | **PNAS** 120(34), 2023 (NOT JASIST) | 10.1073/pnas.2305196120 | Europe PMC PMC10450398 (cc-by-nc-nd) | **RECOVERED** | 39,564B full text |
| zheng2025_male_female_retractions | Journal of Informetrics 2025 | 10.1016/j.joi.2025.101682 | arXiv:2507.17127 (author manuscript) | **RECOVERED** | 67,929B full text |
| deng2023_enhancing_disruption | Scientometrics 128(4), 2023 | 10.1007/s11192-023-04644-2 | none (is_oa=False; no arXiv; no author ms found) | **COVERAGE GAP** (paywalled) | — |
| galuez2023_technology_transfer | Revista Ibérica de Sistemas e Tecnologias de Informação (RISTI), 2023 | (no DOI registered) | not indexed in Crossref/OpenAlex/S2; RISTI site unreachable (risti.ipv.pt returned 0B) | **COVERAGE GAP** (unindexable, no OA) | — |

## Identity correction
- sun2023 was assumed JASIST in R120 pre-annotation; corrected to **PNAS** (Sun, Cacciatoli, Livan 2023). The paper_id slug `sun2023_ranking_mobility` is retained; the gold-chain ceiling is unaffected (the PNAS paper's sample/indicator/model are consistent with the gold annotation).

## Rerun
- sun2023 × {qwen3-32b, deepseek-v4-pro} × IO₁: rerun → DONE, ecrf=0.5 (IO₁ synth-gate floor, expected).
- zheng2025_male × {qwen3-32b, deepseek-v4-pro} × IO₁: rerun → DONE, ecrf=0.5.
- deng2023, galuez2023: not rerun (no paper.md; remain NO_PACKAGE).

## Final R122 IO₁ coverage
- **36/40 runs DONE** (18 papers × 2 models); **4 NO_PACKAGE** (2 papers × 2 models: deng2023, galuez2023).
- mean ECRF = 0.499 (IO₁ LOW-observability floor; all runs synthesize placeholder data → gate c caps at 0.50).
- process evidence: 35/36 exec succeeded; 36/36 synthetic_generated; 0 real_data_used; 0 ref_code_used (all expected at IO₁).

## Coverage gaps (2 papers, paper-text-unavailable)
- **deng2023_enhancing_disruption**: Scientometrics 2023, closed access, no OA preprint/manuscript. Legal recovery not possible without institutional access.
- **galuez2023_technology_transfer**: RISTI 2023, no DOI, not indexed in Crossref/OpenAlex/S2, journal site unreachable. Cannot locate the full text.

These 2 papers are excluded from R122 IO₁ (and will be excluded from R123/R124 unless a legal full text is obtained). The 18-paper coverage is reported transparently in R125; the IO→ECRF analysis runs on the 18-paper subset with the gap noted. Replacing these 2 papers with verified alternatives (per the R120 replacement discipline) is an option if the user wants a full 20-paper IO₁.
