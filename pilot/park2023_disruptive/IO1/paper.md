# Papers and patents are becoming less disruptive over time
Park, Leahey & Funk (2023), Nature. DOI: 10.1038/s41586-022-05543-x.

> NOTE: This is a structured stub assembled from the paper's thesis and known method,
> because the full Nature text was not available locally at build time (not in Zotero/bench-mark).
> The reference code + data dictionary carry the operational method for reproduction.

## Thesis
Across millions of papers and patents (1945–2010s), the CD-disruption index has
declined systematically over time: published work has become less disruptive and
more consolidating. The decline is robust across fields, document types (papers,
patents), and after controlling for citation-practice changes.

## Data
Citation networks for papers (Web of Science / OpenAlex / MAG) and patents (USPTO),
millions of records 1945–2010. The CD-disruption index (Funk & Owen-Smith 2017) is
computed per work from its forward and backward citation structure.

## Method / indicator
- CD-disruption index: CD = (n_10 - n_11) / (n_10 + n_11 + n_00), where n_ij classify
  the citing works by whether they cite the focal work's references (j) and the focal work (i).
- Aggregate mean CD per year; test the time trend.

## Key results
- Mean disruption score declines monotonically across the study period.
- Decline holds for papers and for patents separately, and across STEM/social-sciences fields.
- Papers are less disruptive now than in the mid-20th century.

## Claim
Published science and technology has become progressively less disruptive over time.
