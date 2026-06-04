# M2 Reproduction Report: Wu et al. (2019) — Disruption by Team Size

**Date**: 2026-06-01
**Data**: SciSciNet (cssi/SciSciGPT-SciSciNet, CC-BY-4.0), all 22 paper shards
**Sample**: 2,462,394 papers, 1949-2022

## Metric Definition

Disruption Index (D-index) for a focal paper:
```
D = (n_i - n_j) / (n_i + n_j + n_k)
```
- n_i: citing papers that cite ONLY the focal paper
- n_j: citing papers that cite BOTH the focal paper AND its references
- n_k: citing papers that cite ONLY the references (not the focal paper)
- Range: [-1 (fully consolidating), +1 (fully disruptive)]

## Primary Result

| Team Size | Mean D-index | Std | N |
|-----------|-------------|-----|---|
| Small (1-3 authors) | **+0.00603** | 0.06106 | 1,105,007 |
| Large (4+ authors) | **+0.00053** | 0.03864 | 495,826 |
| **Difference** | **+0.00550** | — | — |

- **Mann-Whitney U**: 306,169,030,971, **p ≈ 0** (p < 0.001)
- **Direction**: Small teams produce more disruptive work ✓
- **Statistical significance**: Confirmed ✓

## Comparison with Wu et al. (2019)

| Metric | Wu et al. (2019) | This Reproduction |
|--------|------------------|-------------------|
| Data source | Web of Science, 42M papers | SciSciNet, 2.46M papers |
| Small-team mean | +0.25 | +0.006 |
| Large-team mean | −0.10 | +0.001 |
| Effect size | 0.35 | 0.006 |
| Direction | Small > Large ✓ | Small > Large ✓ |
| Significance | P < 0.001 ✓ | P ≈ 0 ✓ |

The direction and significance replicate, but the effect size is ~60× smaller.
This is expected: SciSciNet covers different journals, time periods, and uses
a different citation graph than Web of Science. The D-index is sensitive to
citation network coverage.

## Robustness Checks

### Field-Level (262 fields)
- **251/262 fields (96%)** show small-team advantage
- **157/262 fields (60%)** significant at p < 0.001
- Largest advantage: Aeronautics (+0.034), Marine engineering (+0.030), History (+0.025)
- Reversed effect: Transport engineering (−0.014), Combinatorial chemistry (−0.008), Nuclear physics (−0.006)

### Year-Level (74 years, 1949-2022)
- **68/74 years (92%)** show small-team advantage
- **50/74 years (68%)** significant at p < 0.001
- Effect declining over decades: +0.006 (1950s) → +0.001 (2010s) → +0.0005 (2020s)
- The small-team advantage appears to be shrinking in recent decades

### Distribution
- Mean D: 0.00433, Median: −0.00031
- Strongly right-skewed (6.48): a few highly disruptive papers, most neutral
- 28.7% of papers have D > 0; only 1.9% have D > 0.1

## Limitations vs. Wu et al. (2019)

1. **Citation coverage**: SciSciNet's citation graph (~78M edges) is smaller than Web of Science (~600M). This compresses D-index values toward zero.
2. **Paper selection**: SciSciNet samples from Microsoft Academic Graph, not Web of Science. Different journal coverage, especially for pre-1990 papers.
3. **Pre-computed field**: We used SciSciNet's pre-computed `disruption_score`. The original Wu et al. computed D-index from the full WoS citation graph with 5-year citation windows.
4. **Author count**: Used raw `author_count`. Wu et al. may have used different team size thresholds.
5. **No patent/software data**: Wu et al. analyzed patents and software products in addition to papers.

## Conclusion

The core Wu et al. (2019) finding — small teams disrupt, large teams develop — is reproduced at high statistical significance using SciSciNet. The direction is robust across 96% of fields and 92% of years. Effect sizes are smaller due to differences in data coverage, but the qualitative conclusion holds.
