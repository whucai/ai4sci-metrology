# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: AI for Science Metrology (ai4sci-metrology)

研究 AI for Science 的计量学范式——用 AI Agent 自动测量、评估和改善科学研究的可复现性。
Core benchmark: Dashun Wang's Science of Science tradition, SciSciGPT (Nature Computational Science 2025).

## Environment

- Python 3.11+: `conda activate sciscigpt` (preferred, has langchain/langgraph)
- Legacy: `conda activate lzz` (Python 3.9)
- GPU: 1x 4090 (local, no SSH needed)
- Working directory: `/mnt/mydisk/PycharmProjects/ai4sci-metrology`
- Git: main branch = `master`

## Research Direction (三步走)

1. **自动论文复现环境**: AI reads paper → reproduces analysis → judges reproducibility
2. **人机协作实验设计**: Human proposes idea → AI finds data → AI designs experiment
3. **范式转变论述**: From "correlational metrology" to "causal reproducibility" — Vision Paper

## Repository Structure

This is the **meta/planning repo**. The actual experiment code lives in the archived project:
- `/mnt/mydisk/PycharmProjects/retracted-paper-detection/` — 6 phases of experiments completed (see Experimental History below)

This repo contains:
- `idea-stage/` — Research design docs: RESEARCH_DIRECTION, VALIDATION_PLAN, HARD_PROBLEMS, LITERATURE_SURVEY, IDEA_REPORT
- `research-wiki/` — 21 indexed papers + graph edges + log
- `tools/research_wiki.py` — Wiki management CLI (pure stdlib)

## Research Wiki Tool

```bash
python3 tools/research_wiki.py ingest_paper research-wiki --arxiv-id <id> [--thesis "..."] [--tags t1,t2]
python3 tools/research_wiki.py sync research-wiki --arxiv-ids id1,id2,id3
python3 tools/research_wiki.py add_edge research-wiki --from <node_id> --to <node_id> --type <type> --evidence "..."
python3 tools/research_wiki.py rebuild_index research-wiki
python3 tools/research_wiki.py stats research-wiki
python3 tools/research_wiki.py log research-wiki "<message>"
```

Valid edge types: `extends`, `contradicts`, `addresses_gap`, `inspired_by`, `tested_by`, `supports`, `invalidates`, `supersedes`.

Slug format: `author_last + year + keyword_from_title`. Example: `freedman2024_detecting_scientific_fraud`.

## Current Experiments (SciSciGPT Reproduction)

Adapting SciSciGPT's multi-agent LangGraph architecture to local infrastructure.

### Completed
- **M0 (sanity)**: LangGraph state machine smoke test — full agent cycle verified (MockLLM)
- **M1 (baseline)**: Real sandbox executor (subprocess Python) + agent graph integration

### In Progress
- **M2**: Paper reproduction pipeline — feed SciSciGPT PDF, extract method, reproduce one analysis
- **M3**: Self-Correction loop + REI metric

### Source Code
- `src/sciscigpt_local/` — Local adaptation of SciSciGPT multi-agent framework
  - `graph_adapter.py` — LangGraph builder, node functions (RM, specialists, tools, evaluation)
  - `sandbox.py` — Subprocess-based Python/R/Julia sandbox (no Docker yet)
  - `mock_llm.py` — Deterministic mock LLM for testing
  - `llm_backends.py` — Pluggable LLM (Anthropic/OpenAI API, local)
  - `mock_prompts.py` — Embedded prompts (replaces LangChain Hub pulls)
  - `mock_tools.py` — Stub tools (replaces GCP/Pinecone stubs)
  - `state.py`, `messages_utils.py` — Ported from SciSciGPT agents/utils/
- `scripts/test_m0_smoke.py` — M0 sanity test (4/4 checks)
- `scripts/test_m1_baseline.py` — M1 baseline test (sandbox + agent + LLM)
- `sciscigpt_repo/` — Cloned SciSciGPT GitHub repo (reference)
- `refine-logs/EXPERIMENT_PLAN.md` — 4-milestone experiment plan
- `refine-logs/EXPERIMENT_TRACKER.md` — Run tracker

### Archived (retracted-paper-detection)
- `/mnt/mydisk/PycharmProjects/retracted-paper-detection/` — Previous 6-phase experiments on paper mill detection. Semantic similarity (AUC 0.854), Toulmin extraction pilot, graph similarity ablations. See `research-wiki/log.md` for full history.

## Three Hard Problems (see idea-stage/HARD_PROBLEMS.md)

1. **Environment reproducibility**: PyTorch/CUDA conflicts, missing R packages. Solution: dynamic Dockerfile generation + Self-Correction loop.
2. **Implicit knowledge extraction**: Papers omit hyperparameters, preprocessing details. Solution: multi-pass LLM reading + cross-referencing.
3. **Result comparison fidelity**: Cherry-picked results, statistical test differences. Solution: 4-level comparison framework (exact numeric → statistical equivalence → chart comparison → conclusion consistency).
<!-- ARIS:BEGIN -->
## ARIS Skill Scope
ARIS skills installed in this project: 80 entries.
Manifest: `.aris/installed-skills.txt` (lists every skill ARIS installed and its upstream target).
For ARIS workflows, prefer the project-local skills under `.claude/skills/` over global skills.
Do not modify or delete files inside any skill that is a symlink (symlinks point into `/home/caile/下载/Auto-claude-code-research-in-sleep`).
Update with: `bash /home/caile/下载/Auto-claude-code-research-in-sleep/tools/install_aris.sh`  (re-runnable; reconciles new/removed skills).
<!-- ARIS:END -->