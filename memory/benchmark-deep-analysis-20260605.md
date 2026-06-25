---
name: benchmark-deep-analysis-20260605
description: "Deep analysis: bimodal error distribution, 6-category L3 failure taxonomy, L3.5 ablation (0/8)"
metadata: 
  node_type: memory
  type: project
  originSessionId: fa3a8605-3760-41c4-ad97-b735c9e2b100
---

# Benchmark Deep Analysis (2026-06-05)

Three deep analyses of the 120-task 7-metric benchmark:

**Why**: User requested three additional analyses to strengthen the benchmark paper's contribution narrative.

**How to apply**: The bimodal error distribution + L3.5 ablation prove that "the central challenge is not code synthesis but method specification extraction" — with the nuance that extraction and synthesis are NOT independent for current LLMs.

## 7.1 Success vs Perfect (Bimodal Error)

70/106 successes are perfect (< 0.1% error), 0 are in the 0.1%-5% range, 30 are > 20% wrong. The LLM either gets it exactly right or substantially wrong — definitive signal.

## 7.2 L3 Failure Taxonomy

6 categories: method too abstract (12%), no method in paper (12%), needs external data (12%), wrong method extracted (12%), data field mapping error (12%), parameter mismatch (12%), computation error (2%). Only 22% accurate.

## 7.3 L3.5 Ablation (Key Finding)

L3.5 (extract spec → generate code) scored 0/8 success vs L3 direct (68% success). The SAME model that correctly implements D-index from full paper CANNOT extract a clean spec first. This proves method extraction and code synthesis are not independent — the LLM needs simultaneous paper+data+task context.

This is the strongest result for the paper: code synthesis is solved (L1/L2 98-100%), but methodology extraction IS the bottleneck, and current architectures cannot separate these steps.
