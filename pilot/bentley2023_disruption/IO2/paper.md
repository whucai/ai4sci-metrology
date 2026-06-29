# Is disruption decreasing, or is it accelerating?
Bentley et al. (2023), Advances in Complex Systems. DOI: 10.1142/S0219525923500066.

> Structured stub (full text not locally available); reference code + data dictionary carry the method.

## Thesis
Park et al. (2023) showed mean CD-disruption declining over time using UNWEIGHTED means.
Bentley et al. argue this is an artifact: when disruption is weighted by citations
(citation-weighted CD), the trend reverses or attenuates — disruption may be
*accelerating* among highly-cited work. The unweighted decline is driven by the
growing mass of low-impact, low-disruption papers.

## Data
SciSciNet papers 1945–2010 with disruption_score (CD5) and citation_count.

## Method
- Unweighted mean CD per year: mean(disruption_score).
- Citation-weighted mean CD per year: Σ(citation_count * disruption_score) / Σ(citation_count).
- Compare the two trends.

## Key result
Citation-weighted disruption trend differs from (and may oppose) the unweighted trend;
weighting reveals that disruption among cited work is not simply declining.

## Claim
Whether disruption is decreasing or accelerating depends on citation weighting;
unweighted means overstate the decline.
