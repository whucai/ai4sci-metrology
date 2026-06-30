# Patch 001 — zheng2025_male_female_retractions IO2 data_provided flag

**Date**: 2026-06-30
**Paper**: zheng2025_male_female_retractions
**IO**: 2
**Frozen manifest says**: data_provided = True (Retraction Watch public)
**Actual**: Retraction Watch database CSV requires free email-registration to download; the public CDN endpoint (retraction.watch/database/retractionwatch.csv) did not resolve without registration. Not autonomously downloadable.
**Patch**: For R123 IO2, treat zheng2025_male as data_provided = False (registration-gated boundary). The paper.md + data_dictionary + sample_notes are provided (IO1-level text); no raw_data file. The agent runs IO2 as a boundary case (no retraction corpus) — consistent with the R120 soft-blocker discipline.
**Effect on gold ceiling**: None. The gold ceiling is unchanged; only the IO2 *provided materials* flag is corrected to match reality. This is a materials-availability correction, not a gold-chain or scorer change.
**Runs affected**: zheng2025_male × {qwen3-32b, deepseek-v4-pro} × IO2 (2 runs) will run as boundary (no raw_data).
