#!/usr/bin/env python3
"""Reference reproduction of Park, Leahey & Funk (2023) — 'Papers and patents are
becoming less disruptive over time', Nature 613:138-142.

Reproduces the central directional finding from the 40K SciSciNet sample:
mean disruption_score declines over time (and is lower for papers than patents,
if doc_type distinguishes).
"""
import pandas as pd
from scipy.stats import spearmanr

DF = pd.read_parquet("/workspace/raw_data/sciscinet_sample.parquet")
DF = DF.dropna(subset=["disruption_score", "year"])
DF = DF[(DF["year"] >= 1945) & (DF["year"] <= 2015)]

by_year = DF.groupby("year")["disruption_score"].mean().reset_index()
rho, p = spearmanr(by_year["year"], by_year["disruption_score"])

early = DF[DF["year"] <= 1980]["disruption_score"].mean()
late = DF[DF["year"] >= 2000]["disruption_score"].mean()

print(f"RESULT n_papers = {len(DF)}")
print(f"RESULT year_range = {int(DF.year.min())}-{int(DF.year.max())}")
print(f"RESULT early_mean_disruption_1945_1980 = {round(early,5)}")
print(f"RESULT late_mean_disruption_2000_2015 = {round(late,5)}")
print(f"RESULT difference_early_minus_late = {round(early-late,5)}")
print(f"RESULT spearman_rho_year_vs_disruption = {round(rho,4)}")
print(f"RESULT spearman_p = {p:.3e}")
print(f"RESULT direction = {'disruption declines over time (negative trend)' if rho < 0 else 'disruption increases (positive trend)'}")

if "doc_type" in DF.columns:
    for dt, g in DF.groupby("doc_type"):
        print(f"RESULT mean_disruption_{dt} = {round(g['disruption_score'].mean(),5)} (n={len(g)})")

print("PAPER_REPORTED direction = disruption has declined over time")
print("PAPER_REPORTED sample = millions of papers + patents, 1945-2010 (this run uses 40K DATA_SUB)")
print("PAPER_REPORTED conclusion = science and technology have become less disruptive")
