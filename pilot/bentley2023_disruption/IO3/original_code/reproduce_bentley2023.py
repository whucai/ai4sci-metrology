#!/usr/bin/env python3
"""Reference reproduction of Bentley et al. (2023) — 'Is disruption decreasing,
or is it accelerating?', Advances in Complex Systems.

Computes UNWEIGHTED vs CITATION-WEIGHTED mean CD5 disruption by year from the
40K SciSciNet sample, showing the two trends diverge (weighting attenuates/reverses
the unweighted decline).
"""
import pandas as pd
from scipy.stats import spearmanr

DF = pd.read_parquet("/workspace/raw_data/sciscinet_sample.parquet")
DF = DF.dropna(subset=["disruption_score", "citation_count", "year"])
DF = DF[(DF["year"] >= 1945) & (DF["year"] <= 2010)]

g = DF.groupby("year")
unw = g["disruption_score"].mean()
wgt = g.apply(lambda x: (x["citation_count"] * x["disruption_score"]).sum() / x["citation_count"].sum())

rho_unw, p_unw = spearmanr(unw.index, unw.values)
rho_wgt, p_wgt = spearmanr(wgt.index, wgt.values)

print(f"RESULT n_papers = {len(DF)}")
print(f"RESULT unweighted_spearman_rho = {round(rho_unw,4)} (p={p_unw:.3e})")
print(f"RESULT weighted_spearman_rho = {round(rho_wgt,4)} (p={p_wgt:.3e})")
print(f"RESULT unweighted_early_minus_late = {round(unw[unw.index<=1980].mean()-unw[unw.index>=2000].mean(),5)}")
print(f"RESULT weighted_early_minus_late = {round(wgt[wgt.index<=1980].mean()-wgt[wgt.index>=2000].mean(),5)}")
print(f"RESULT direction = unweighted {'declines' if rho_unw<0 else 'rises'}; weighted {'declines' if rho_wgt<0 else 'rises or attenuates'}")
print("PAPER_REPORTED claim = citation-weighting changes the disruption trend vs unweighted")
print("PAPER_REPORTED conclusion = unweighted decline overstates the loss of disruption")
