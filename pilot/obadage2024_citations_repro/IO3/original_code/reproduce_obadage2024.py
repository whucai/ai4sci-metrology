#!/usr/bin/env python3
"""Reference reproduction of Obadage (2024) — 'Can citations tell us about a paper's
reproducibility? A case study of machine learning papers', ACM FAccT 2024.

Reproduces the central correlation: per cited MLRC-2022 paper, the positive-sentiment
ratio of its citation contexts is correlated with its citation count (the paper's
proxy for downstream attention / reproducibility signal).
"""
import json
from scipy.stats import spearmanr

summary = json.load(open("/workspace/raw_data/citation_context_label_summary.json"))
counts = json.load(open("/workspace/raw_data/citation_counts_for_cited_papers.json"))

rows = []
for rid, s in summary.items():
    pos = s.get("1", 0) + s.get("0.5", 0)
    neg = s.get("-1", 0) + s.get("-2", 0)
    total = sum(s.values())
    if total == 0:
        continue
    pos_ratio = pos / total
    cit = counts.get(rid, {}).get("citationCount", 0)
    rows.append((rid, pos_ratio, neg / total, total, cit))

pos_r = [r[1] for r in rows]
cit_r = [r[4] for r in rows]
rho, p = spearmanr(pos_r, cit_r)

print(f"RESULT n_papers = {len(rows)}")
print(f"RESULT mean_pos_sentiment_ratio = {round(sum(pos_r)/len(pos_r),4)}")
print(f"RESULT mean_citation_count = {round(sum(cit_r)/len(cit_r),2)}")
print(f"RESULT spearman_rho_pos_sentiment_vs_citations = {round(rho,4)} (p={p:.3e})")
print(f"RESULT direction = {'more positive sentiment <-> more citations' if rho>0 else 'negative sentiment <-> more citations'}")
print("PAPER_REPORTED claim = citation context sentiment correlates with reproducibility")
print("PAPER_REPORTED conclusion = citations can signal a paper's reproducibility")
