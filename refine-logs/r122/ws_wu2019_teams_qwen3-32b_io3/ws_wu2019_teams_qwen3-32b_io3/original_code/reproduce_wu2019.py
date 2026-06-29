#!/usr/bin/env python3
"""Reference reproduction of Wu, Wang & Evans (2019) — "Large teams develop and
small teams disrupt science and technology", Nature 566:378-382.

Reproduces the central directional finding from the 40K SciSciNet sample:
small teams (<=3 authors) have higher disruption scores than large teams (>=10).

Run inside the isolated executor with raw_data/ mounted at /workspace/raw_data/.
"""
import pandas as pd
from scipy.stats import mannwhitneyu

DF = pd.read_parquet("/workspace/raw_data/sciscinet_sample.parquet")
DF = DF.dropna(subset=["disruption_score", "author_count"])

# Team-size split (paper uses multiple thresholds; <=3 vs >=10 is the cleanest)
small = DF[DF["author_count"] <= 3]
large = DF[DF["author_count"] >= 10]

small_mean = small["disruption_score"].mean()
large_mean = large["disruption_score"].mean()
diff = small_mean - large_mean

stat, p = mannwhitneyu(small["disruption_score"], large["disruption_score"], alternative="two-sided")

print(f"RESULT n_small = {len(small)}")
print(f"RESULT n_large = {len(large)}")
print(f"RESULT small_mean_disruption = {round(small_mean, 5)}")
print(f"RESULT large_mean_disruption = {round(large_mean, 5)}")
print(f"RESULT difference_small_minus_large = {round(diff, 5)}")
print(f"RESULT mannwhitney_p = {p:.3e}")
print(f"RESULT direction = {'small teams disrupt more (positive gap)' if diff > 0 else 'large teams disrupt more (negative gap)'}")

# PAPER_REPORTED comparison values (from the 65M-work original)
print("PAPER_REPORTED direction = small teams disrupt more than large teams")
print("PAPER_REPORTED sample = >65M works, 1954-2014 (this run uses 40K DATA_SUB sample)")
print("PAPER_REPORTED conclusion = smaller teams tend to disrupt; larger teams tend to develop")
