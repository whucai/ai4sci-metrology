---
name: benchmark-results-20260604
description: "Manual papers benchmark — 72-task run with Qwen3-32B, 8 concurrent workers, L1/L2/L3 results"
metadata: 
  node_type: memory
  type: project
  originSessionId: fa3a8605-3760-41c4-ad97-b735c9e2b100
---

# Manual Papers Benchmark (2026-06-04)

L1/L2/L3 benchmark using 8 manually downloaded methodology papers (from bench-mark/) tested against 3 SciSciNet papers with known D-index ground truth. 72 tasks run in 178s with 8 concurrent workers (ThreadPoolExecutor).

**Why**: First full-pipeline benchmark with vLLM-served Qwen3-32B to validate the stratified benchmark design and measure methodology extraction capability.

**How to apply**: When interpreting benchmark results or planning the next review round (Round 5), use these baselines. L1/L2 work reliably; L3 requires papers that actually describe D-index.

## Key Results

| Level | Success | Perfect | Meaning |
|-------|---------|---------|---------|
| L1 (formula+algorithm) | 22/24 (92%) | 16/18 disruption | Model can implement D-index when algorithm is explicit |
| L2 (title+algorithm) | 24/24 (100%) | 18/18 disruption | Column-name fix was critical (reference_id, not paper_id) |
| L3 (full paper text) | 18/24 (75%) | 5/18 disruption | Only works for papers that explicitly describe D-index |

## Critical Bug Fixed

`.head(5000)` in citation data export truncated data for papers with many citers (>262 citers). Fixed to `.head(100000)`. This caused papers 2166706824 (568 citers) and 2781525129 (1757 citers) to get wrong L1 results.

## L3 Paper-Specific Findings

- arxiv_2306_01949 (disruption bias paper): Best L3 — explicitly discusses D-index formula → 2/3 perfect
- ms_dynamic_network: Good L3 — describes D-index computation → 2/3 perfect
- nature_2023_disruption: Uses CD-index variant, not exact D formula → 1/3 perfect
- RP/CC-BY papers: Don't describe D-index → wrong metrics extracted (expected failure)
- nber_w18958/pnas: Non-D-index papers → can't extract D-index (expected failure)

## Concurrency

8 workers via ThreadPoolExecutor → 178s for 72 tasks (2.5s/task), ~8x speedup vs sequential.
