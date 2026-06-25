---
name: uspto-sciscinet-data
description: USPTO patent data and SciSciNet datasets downloaded 2026-06-06
metadata: 
  node_type: memory
  type: project
  originSessionId: 5578b0b5-abb6-4418-bb55-52a3c7217538
---

SciSciGPT-SciSciNet dataset fully downloaded from HuggingFace (70GB, 194 files), including 50 USPTO patent shards (~9M patents with title/abstract/date) and 100 paper shards (~11.2M papers with disruption scores).

**Why**: User needed USPTO patent data for Research Policy paper reproduction benchmarks (Arts et al. 2021 NLP on patent text, Schaper et al. 2025 frontier scientists).

**How to apply**: Patent data at `data/sciscinet/patents/shard_*.parquet` (columns: patent_id, type, date, year, title, abstract, abstract_embedding). Paper-patent links at `data/sciscinet/paper_patents.parquet` (6.9M rows). sciscinet-v2 (Northwestern-CSSI) is gated — access requested but not yet granted. Pre-existing data at `data/patentsview/` (5GB) has abstracts+claims from HuggingFace.
