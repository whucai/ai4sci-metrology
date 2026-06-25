---
name: benchmark-results-20260605-v2
description: "7-metric per-paper methodology benchmark — 120 tasks, L1/L2/L3, 8 workers, Qwen3-32B, 88% success"
metadata: 
  node_type: memory
  type: project
  originSessionId: fa3a8605-3760-41c4-ad97-b735c9e2b100
---

# Multi-Metric Benchmark Results (2026-06-05)

120-task benchmark: 8 methodology papers × 5 test papers × 3 levels (L1/L2/L3). Each paper tested against its OWN metric type (not all forced to compute D-index). 325s with 8 concurrent workers.

**Why**: Extended the stratified benchmark from 1 metric (D-index) to 7 metrics, matching each methodology paper to the computational method it actually describes.

**How to apply**: L1/L2 work reliably (98-100%) across all 7 metrics. L3 only works when the paper explicitly describes the target computation. For future benchmarks, use L1/L2 for reliable measurement, L3 for methodology extraction capability.

## 7 Metric Types

| Metric | Paper | Per-Paper/Dataset | L1/L2 Reliable? |
|--------|-------|-------------------|-----------------|
| disruption | MS, arXiv overview, RP 2021 | Per-paper | YES (100% perfect) |
| team_size_effect | NBER w18958 | Dataset | YES (100% perfect) |
| citation_inflation | arXiv 2306.01949 | Dataset | YES (after numpy fix) |
| disruption_temporal | Nature 2023 | Dataset | YES (after numpy fix) |
| network_normalized_impact | PNAS Ke et al. | Per-paper | YES |
| frontier_author_impact | RP 2025 Sam Arts | Dataset | YES (consistent, but GT mismatch) |

## Results by Level

| Level | Success | Perfect | REI-c Mean |
|-------|---------|---------|------------|
| L1 | 39/40 (98%) | 21/40 | 1.41 |
| L2 | 40/40 (100%) | 21/40 | 1.45 |
| L3 | 27/40 (68%) | 7/40 | 35.20 |
| **Total** | **106/120 (88%)** | **47/120** | **10.03** |

## Known Issues

1. **frontier_author_impact**: LLM computes 67.10 vs GT 93.85. Interpretation difference in "top 10% within most recent 5 years" — LLM filters to recent papers first, GT uses threshold on all papers.
2. **Scipy unavailable in sandbox**: Updated disruption_temporal and citation_inflation prompts to use numpy.corrcoef.
3. **L3 for non-disruption papers**: 0/5 for disruption_temporal, frontier_author_impact at L3. Papers don't describe exact computation.

## Prompt Fixes Applied

- citation_inflation: `scipy.stats.pearsonr` → `numpy.corrcoef(x,y)[0,1]`, added `duplicates='drop'` to pd.qcut
- disruption_temporal: `scipy.stats.pearsonr` → `numpy.corrcoef`
- frontier_author_impact: Clarified threshold computation (recent years → threshold → all papers)
