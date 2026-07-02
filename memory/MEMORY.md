# Memory Index

- [Error detection pattern](error-detection-pattern.md) — never use substring matching on stderr for error detection
- [Stratified benchmark bugfix](stratified-benchmark-bugfix.md) — 3-part bug fix for L2/L3 0% success rate (2026-06-03)
- [Benchmark results 2026-06-04](benchmark-results-20260604.md) — 72-task concurrent benchmark: L1 92%, L2 100%, L3 75% with Qwen3-32B
- [Benchmark results 2026-06-05 v2](benchmark-results-20260605-v2.md) — 120-task 7-metric per-paper benchmark: L1 98%, L2 100%, L3 68% overall (88%)
- [Benchmark deep analysis 2026-06-05](benchmark-deep-analysis-20260605.md) — bimodal error distribution, 6-category L3 taxonomy, L3.5 ablation (0/8 proves extraction-synthesis not independent)
- [Auto-save memory](auto-save-memory.md) — periodically save project memories during long sessions without waiting to be asked
- [SciSciBench engineering defenses](sciscibench-engineering-defenses.md) — 3 critical defenses: forced JSON output for Task 1, 3-layer contamination defense, dual-track evaluation (2026-06-11)
- [Benchmark redesign 2026-06-05](benchmark-redesign-20260605.md) — 4-stage paper reproduction chain framework, Phase 1 in progress
- [Benchmark refactor 2026-06-06](benchmark-refactor-20260606.md) — Phases 1-4 complete, unified package+stages+runner+eval, smoke-tested
- [First real LLM benchmark run](benchmark-first-real-llm-run-20260606.md) — Stage 2+4 with Qwen3-32B: 24 tasks, 95.8% success, REI-c mean=1.59, 2 bugs fixed
- [Benchmark results 2026-06-12](benchmark-results-20260612.md) — Full 118-paper SciSciBench run: Task 1 F1=0.435, Task 2 score=0.654 with Qwen3-32B
- [M1 runner 2026-06-18](m1-runner-20260618.md) — M1 Framework Validation runner built, smoke-tested on 3 pilot papers with Gemma
- [M1 full benchmark 2026-06-18](m1-full-benchmark-20260618.md) — 10-paper M1 benchmark: 10/10 pass, context window fix for Gemma, maturity L0-L3(m)
- [L3 scoring protocol revision 2026-06-24](l3-scoring-protocol-revision-20260624.md) — direction calibration matrix, graded claim support, rebalanced weights, rationale for write-up
- [DeepSeek L3 benchmark 2026-06-24](deepseek-l3-benchmark-20260624.md) — 211 papers with DeepSeek V4 Pro + new scoring: overall=0.298, support_strength 100% weak
- [LLM backend switching](llm-backend-switching.md) — DeepSeek (Anthropic path) vs Qwen3 (OpenAI path) auto-detection
- [L3 experiment DeepSeek backend](l3-experiment-deepseek-backend.md) — vLLM server down, switched L3 experiment to DeepSeek-v4-pro; results not comparable to Qwen3-32B baseline
- [Evidence-chain theory v7.2](evidence-chain-theory-v7.2.md) — UTD paper reframing: IO→ECRF→TCE theory, 4 propositions, 3 studies, mini Study 2 next (2026-06-24)
- [Scientometrics pivot v8](scientometrics-pivot-v8.md) — reframe evidence-chain idea for Scientometrics venue; on worktree branch worktree-scientometrics-pivot (not merged)
- [Git sync policy](git-sync-policy.md) — **MASTER only** (2026-06-29 directive; dev/worktree superseded); periodic local commit; no PDFs/secrets/symlinks; .litellm gitignored; GCP key stripped via filter-repo, normal push OK
- [Parallel worktree setup](parallel-worktree-setup.md) — (legacy) Cursor=master + Claude=dev worktree; SUPERSEDED 2026-06-29 — now master-only, ignore worktrees unless explicitly asked
- [Research review v8.1 outcome](research-review-v8.1-outcome.md) — Codex 3-round review: same-trace R2/R2+/R3 fix rescued design to 7/10; R2+ is real novelty threat; Study 2/4 downgraded (2026-06-29)
- [Session start: stay on master](session-start-v8-dev.md) — on reboot/open, STAY on master (do NOT enter v8-dev worktree); LiteLLM proxy 127.0.0.1:4000 (qwen3-32b/deepseek-v4-pro/glm-5.2/gemma); All_PROXY=127.0.0.1:7897 (2026-07-02)
- [M2 + killer status](m2-and-killer-status.md) — M2 qwen3 done 50/51; v2 rescore IO1=0.50 IO2=0.49 IO3=0.60; 6 Study-3 B1 killer cases (park2023 strongest) (2026-07-02)
- [Study 2 EUC mechanism 2026-07-02](study2-euc-mechanism-2026-07-02.md) — R122-R125 done (105 runs): IO1 0.499/IO2 0.601/IO3 0.591; H_EUC (uptake mediates IO→ECRF); real_data∧¬synth=100% break (0.703), synth=0% (0.497); refcode neither nec nor suff; robust across 4 checks; R121=model-family dual annotation α=0.945
- [codex-image2 MCP wiring](codex-image2-mcp-wiring.md) — native gpt-image-2 figure bridge registered+connected; drive via `run_codex_image` (no restart needed); output under cwd/figures/ai_generated/; figure_final.png done (2026-07-02)

- [DEV terminal role](dev-terminal-role.md) — this terminal = v8-dev worktree on dev; push dev only, never touch master; reboot: open in worktree dir (2026-07-02)
