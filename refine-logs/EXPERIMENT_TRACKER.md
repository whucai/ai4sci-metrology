# Experiment Tracker

**Plan**: refine-logs/EXPERIMENT_PLAN.md
**Started**: 2026-06-01

## Run Status

| Run ID | Milestone | Description | Status | LLM | Key Metric | Notes |
|--------|-----------|-------------|--------|-----|------------|-------|
| R001 | M0 | LangGraph smoke test | DONE | MockLLM | 4/4 checks passed | Full agent cycle verified |
| R002 | M1 | Sandbox executor | DONE | MockLLM | exit_code=0 | Python subprocess sandbox works |
| R003 | M1 | Agent + sandbox + LLM | DONE | Qwen3-32B | 18-node, 3 tool cycles, 3/3 pass | Real LLM verified |
| R004 | M2 | Paper reproduction (Qwen3 code gen) | DONE | Qwen3-32B | REI=0.67, 2 fix iters | Code quality poor (thinking tags) |
| R005 | M2 | SciSciNet Wu2019 full reproduction | DONE | pandas | small D=0.00603, large D=0.00053, p≈0 | 2.46M papers, 22 shards. 96% fields, 92% years. Report: refine-logs/M2_REPRODUCTION_REPORT.md |
| R006 | M3 | Self-Correction loop + REI | DONE | Qwen3-32B | REI=0.5 mean, 3/3 trials | Baseline: 0.0, error recovery: 1.5, 3/3 matches |
| R007 | M3 | REI per-field distribution | DONE | pandas | 310 fields, std 0.01-0.21 | Neoclassical econ most variable (std=0.21) |
| R008 | M2c | 4-level evaluation framework | DONE | rule-based | Composite 0.53, PARTIALLY SUPPORTED | L1:FAIL, L2:PASS, L4:PARTIAL |
| R009 | M3 | Paper-difficulty stratification | DONE | pandas | REI(easy)=1.13 < REI(med)=3.10 < REI(hard)=3.68 | Criterion met ✓, Spearman ρ=-0.596 |

## Blockers

- ~~**LLM API key**~~: RESOLVED — local Qwen3-32B via vLLM at http://172.17.65.41:8032/v1
- ~~**SciSciNet data**~~: RESOLVED — downloaded from cssi/SciSciGPT-SciSciNet (CC-BY-4.0), 19 tables, 2.46M papers loaded
- **Qwen3 thinking mode**: `enable_thinking=False` not working with current langchain-openai. Workaround: use SciSciNet pre-computed fields for numerical work; simple LLM tasks (CSV analysis) work correctly.

## Next Actions

1. ~~Set LLM API key for real inference~~ Done (Qwen3-32B)
2. ~~Download SciSciGPT paper PDF → extract methods/data~~ Done
3. ~~Download SciSciNet from HuggingFace~~ Done (all 22 shards, 2.46M papers)
4. ~~Run M2: Wu et al. (2019) reproduction~~ Done
5. ~~Run M3: Self-Correction loop + REI~~ Done
6. ~~Multi-shard analysis~~ Done
7. → /auto-review-loop "SciSciGPT reproduction results"
