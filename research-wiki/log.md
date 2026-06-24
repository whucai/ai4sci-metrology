# Research Wiki Log

## 2026-06-24
- `2026-06-24T00:00:00Z` protocol_revision: Task 2 L3 scoring protocol revised. The previous implementation produced a ceiling effect in claim support (1.000 for all 211 L3 papers) and treated cautious "unknown" predictions as fully incorrect in directional inference. The revised protocol introduces: (1) a direction calibration matrix with partial credit for tentative predictions (0.75) and justified uncertainty (0.25 for unknown when gold has directional signal), (2) graded evidence support (strong=1.0, moderate=0.6, weak=0.3), and (3) a rebalanced overall score including evidence anchoring and limitation awareness. See `BENCHMARK_SUMMARY_20260618.md` §L3 Scoring Fixes for details.
- `2026-06-24T00:00:00Z` evaluator_enhancement: Added per-conclusion diagnostic fields (conclusion_details, support_strength_distribution, direction_commit_rate, direction_correct_when_committed) to L3 evaluator output for error taxonomy and ablation analysis.

## 2026-05-26
- Wiki initialized- `2026-05-29T05:39:40Z` Wiki initialized
- `2026-06-01T03:22:20Z` ingest_paper: ingested paper:freedman2024_detecting_scientific_fraud (arxiv:)
- `2026-06-01T03:22:23Z` ingest_paper: ingested paper:ivanova2024_lets_discuss_quality (arxiv:)
- `2026-06-01T03:22:26Z` ingest_paper: ingested paper:ruosch2025_mining_interdocument_argument (arxiv:)
- `2026-06-01T03:22:30Z` ingest_paper: ingested paper:belz2025_repronlp_2025_shared (arxiv:)
- `2026-06-01T03:22:35Z` ingest_paper: ingested paper:al2025_from_text_mining (arxiv:)
- `2026-06-01T03:22:38Z` ingest_paper: ingested paper:al2025_graphbased_verification_framework (arxiv:)
- `2026-06-01T03:22:41Z` ingest_paper: ingested paper:felice2025_evoca_explainable_verification (arxiv:)
- `2026-06-01T03:22:44Z` ingest_paper: ingested paper:su2025_climateviz_benchmark_statistical (arxiv:)
- `2026-06-01T03:22:51Z` ingest_paper: ingested paper:potyka2024_empirical_study_quantitative (arxiv:)
- `2026-06-01T03:22:53Z` ingest_paper: ingested paper:ng2025_marge_meshing_argumentative (arxiv:)
- `2026-06-01T03:22:56Z` ingest_paper: ingested paper:al2025_bridging_scientific_knowledge (arxiv:)
- `2026-06-01T03:22:59Z` ingest_paper: ingested paper:jeon2025_graphcheck_multipath_factchecking (arxiv:)
- `2026-06-01T07:15:53Z` ingest_paper: ingested paper:wu2019_large_teams_develop (arxiv:)
- `2026-06-01T07:37:43Z` ingest_paper: ingested paper:binder2022_fulltext_argumentation_mining (arxiv:)
- `2026-06-01T07:37:46Z` ingest_paper: ingested paper:gemechu2024_aries_general_benchmark (arxiv:)
- `2026-06-01T07:37:49Z` ingest_paper: ingested paper:hernault2025_endtoend_argument_mining (arxiv:)
- `2026-06-01T07:37:51Z` ingest_paper: ingested paper:feger2025_limited_generalizability_argument (arxiv:)

## 2026-06-01 — 实验阶段性总结

### 数据集

- 800 篇论文（200 PM + 600 matched control），来自 `data/dataset/pm_scaled_200.csv`
- 每篇有 Qwen3-32B 提取的摘要论证图，存于 `outputs/pm200/graphs/`
- PM 标签来源：Retraction Watch 数据库 keyword 匹配；Control 通过 4-tier 匹配（同期刊→同 ESI+年份→放松 doc_type→年份+abs_len）
- 期刊覆盖：416 unique journals

### Phase 1: 四组特征基线（Group A/B/C/D）

脚本：`scripts/run_enhanced_ablation.py`

| Feature Group | n | LR AUC | 解释 |
|---|---|---|---|
| A — Semantic similarity | 10 | **0.8537** | Jina 摘要向量 → kNN/centroid 特征 |
| B — Graph compression | 12 | 0.5418 | 纯拓扑：密度、组件数、度中心性 |
| C — Over-certainty | 10 | 0.6317 | hedging/certainty/numeric 比率 |
| D — Role-layer alignment | 13 | 0.6119 | 句子角色 B/M/R/C + 图跨层对齐 |
| ALL combined | 45 | 0.8431 | B/C/D 反而稀释了 A 的信号 |

### Phase 2: 语义特征鲁棒性验证

脚本：`scripts/sanity_check_semantic.py`

| Check | AUC | Δ |
|---|---|---|
| Baseline (StratifiedKFold) | 0.8537 | — |
| GroupKFold by journal (416 groups) | 0.8526 | −0.0011 |
| GroupKFold by journal-year (482 groups) | 0.8560 | +0.0023 |
| Entity masking (疾病/基因/药物/细胞系) | 0.8593 | +0.0056 |

→ 信号不是期刊记忆，不是实体聚类。来自写作模板和修辞模式。

### Phase 3: 语义增强论证图 + 图相似度

脚本：`scripts/run_graph_similarity_ablation.py`，代码：`src/metrics/enriched_graphs.py`

每个节点注入：Jina embedding (1024-dim)、rhetorical role、hedging/certainty/numeric/limitation/generic-claim flags。
每条边注入：source/target type & role、semantic distance、role transition、shortcut flag。
图向量 = mean-pool 节点 embedding → cosine similarity → 6 个 kNN 特征。

| 特征组 | AUC | Δ |
|---|---|---|
| B_old (纯拓扑 12 features) | 0.5418 | +0.04 |
| **GS_new (语义图相似度 6 features)** | **0.7089** | **+0.21** |
| B+GS (18 features) | 0.7045 | +0.20 |

Journal GroupKFold: 0.7089 → 0.6965 (Δ=−0.012)

→ 语义增强图相似度从 0.54 → 0.71，达到预设目标区间 (0.68–0.75)。
→ 富化的论证图存于 `outputs/enriched_graphs/`。

### Phase 4: GS_new 信号拆解

脚本：`scripts/decompose_graph_sim.py`

用不同图表示分别计算相似度矩阵：

| 图表示 | AUC | 解释 |
|---|---|---|
| Node semantic (mean-pool) | 0.7089 | **节点文本内容驱动一切** |
| Node by type (分类型 pool) | 0.7003 | 类型分离无增益 |
| Role distribution | 0.4867 | **低于随机** — 无用 |
| Role transition | 0.5237 | 几乎无用 |
| Edge type distribution | 0.5931 | 微弱 |
| Topology (old Group B) | 0.5938 | 微弱 |

与 Group A 互补性：

| 组合 | AUC |
|---|---|
| A only (10 features) | 0.8537 |
| GS only (6 features) | 0.7089 |
| A+GS (16 features) | 0.8534 |

交叉相关 mean |r| = 0.40，top pairs r = 0.72–0.79。

→ 图相似度是摘要全文相似度的噪声版本，不提供增量信息。

### Phase 5: 论证单元消融

脚本：`scripts/ablation_node_units.py`

仅用特定类型/角色的节点做 mean-pool 图相似度：

| 特征组 | AUC | Cohen's d | 覆盖率 |
|---|---|---|---|
| Full abstract semantic | 0.8537 | — | 100% |
| All argument nodes | 0.7089 | +0.749 | 100% |
| **Claim-node only** | **0.6992** | +0.704 | 100% |
| Evidence-node only | 0.6764 | +0.678 | 99.5% |
| Limitation-node only | 0.6208 | +0.403 | 93.1% |
| Result-role only | 0.5677 | +0.264 | 46.6% |
| Conclusion-role only | 0.5568 | +0.352 | 23.8% |
| Method-role only | 0.5767 | +0.146 | 43.9% |
| Background-role only | 0.5225 | +0.153 | 10.1% |
| Objective-role only | 0.4940 | +0.085 | 15.5% |
| Role/edge/topology only | 0.49–0.59 | — | — |

→ Claim 节点几乎独占信号 (0.699 vs all-nodes 0.709)。
→ 论证图类型区分力 >> 修辞角色。摘要缺乏 BOMRC 结构，69% 节点被归为 "U"。

### 核心发现

1. **最强信号**：摘要全文语义相似度 (AUC 0.854)，鲁棒，不依赖期刊/实体记忆
2. **可解释的第二梯队**：论证图的 Claim 节点语义相似度 (AUC 0.699) — PM 论文的**主张模板化**，claims 在语义空间中高度聚集
3. **图结构本身无效**：纯拓扑、边类型、角色转换在 0.49–0.59，接近随机
4. **修辞角色迁移失败**：基于 IMRaD 的角色分类器在摘要上大量输出 "U"
5. **GS 与 A 高度冗余**：图相似度是摘要全文相似度的噪声版本，不提供增量

### 产出文件

- `outputs/ablation_v1/` — 四组特征基线
- `outputs/enriched_graphs/` — 800 个富化论证图 (JSON)
- `outputs/gs_ablation_v1/` — 图相似度消融
- `outputs/gs_decomposition/` — GS 拆解
- `outputs/node_unit_ablation/` — 论证单元消融
- `outputs/gs_case_study.md` — Case study 报告
- `scripts/run_enhanced_ablation.py` — 四组特征消融
- `scripts/sanity_check_semantic.py` — 鲁棒性验证
- `scripts/run_graph_similarity_ablation.py` — 图相似度消融
- `scripts/decompose_graph_sim.py` — GS 拆解
- `scripts/ablation_node_units.py` — 论证单元消融
- `scripts/case_study_graph_sim.py` — Case study
- `src/metrics/enriched_graphs.py` — 语义富化论证图模块

### Phase 6: Toulmin-Model Argumentation Extraction Pilot

脚本：`scripts/run_toulmin_pilot.py`，`scripts/eval_toulmin_pilot.py`
Prompt：`src/extraction/toulmin_prompt.py`

**Redesign rationale**: Previous extraction used BOMRC roles + generic node types. New approach uses simplified Toulmin model (CLAIM/EVIDENCE/LIMITATION/CONTEXT + SUPPORTS/ATTACKS/ELABORATES), discards unstructured background, focuses on core logical subgraph. Few-shot ICL with 2 examples (1 PM biomedical + 1 Ctrl social science).

**Pilot**: 20 papers (10 PM + 10 Ctrl), Qwen3-32B, output at `outputs/toulmin_pilot/`

**Tier 1 — Sanity & Formatting**:
| Metric | Value | Target |
|---|---|---|
| JSON compliance | 100% | 100% |
| Valid node IDs | 100% | 100% |
| Valid node types | 100% | 100% |
| Valid edge relations | 100% | 100% |
| Missing references | 0 | 0 |

**Tier 2 — Structural Logic**:
| Metric | PM | Ctrl |
|---|---|---|
| Avg nodes | 7.4 | 6.7 |
| Avg edges | 7.6 | 6.2 |
| Avg claims | 1.5 | 1.6 |
| Avg evidence | 3.6 | 3.2 |
| Avg context | 2.3 | 1.7 |
| Claim recall | 100% | 100% |
| Isolated node ratio | 0.01 | 0.00 |
| Argumentative depth | 3.80 | 3.70 |
| Orphan evidence (avg) | — | — (0.20 overall) |

**Tier 3 — Topological Divergence**:
| Metric | PM | Ctrl | Cohen's d |
|---|---|---|---|
| Evidence density (SUPPORTS→CLAIM) | 2.18 | 1.60 | **+0.78** |
| Avg CLAIM in-degree | 2.98 | 2.50 | +0.44 |
| CONTEXT→CLAIM depth | 3.20 | 3.00 | +0.16 |
| Attack ratio | 0.01 | 0.03 | −0.29 |
| ELABORATES ratio | 57% | 48% | — |

**Decision**: ALL 7 checklist items ✓ PASSED. Ready to scale to 800 papers.

**Key findings**:
1. PM papers have denser evidence scaffolding (2.18 vs 1.60 SUPPORTS per CLAIM, d=+0.78)
2. PM papers use more CONTEXT nodes (31% vs 25%) and ELABORATES edges (57% vs 48%) — consistent with over-elaboration to seem credible
3. LIMITATION/ATTACKS are rare in both groups — abstracts rarely contain self-criticism
4. Statistical tests not significant at n=20 but effect sizes are promising
5. Argumentative depth (3.75) far exceeds old extraction — logical chains are multi-hop

**产出文件**:
- `outputs/toulmin_pilot/` — 20 graphs + metrics + summary
- `src/extraction/toulmin_prompt.py` — Toulmin prompt with few-shot ICL
- `scripts/run_toulmin_pilot.py` — Pilot extraction script
- `scripts/eval_toulmin_pilot.py` — 3-tier evaluation script
- `2026-06-01T07:59:00Z` ingest_paper: ingested paper:shao2025_sciscigpt_advancing_humanai (arxiv:)
- `2026-06-01T07:59:03Z` ingest_paper: ingested paper:authors2025_from_science_agentic (arxiv:)
- `2026-06-01T07:59:06Z` ingest_paper: ingested paper:al2025_scireplicatebench_benchmarking_llms (arxiv:)
- `2026-06-01T07:59:08Z` ingest_paper: ingested paper:li2024_mlrcopilot_autonomous_machine (arxiv:)
- `2026-06-11T09:45:59Z` ingest_paper: ingested paper:wang2026_firebench_evaluating_agents (arxiv:2602.02905)
- `2026-06-11T09:46:00Z` ingest_paper: ingested paper:lew2026_projectionbench_evaluating_scientific (arxiv:2605.30284)
- `2026-06-11T09:46:00Z` ingest_paper: ingested paper:chen2024_scienceagentbench_toward_rigorous (arxiv:2410.05080)
- `2026-06-11T09:46:01Z` ingest_paper: ingested paper:majumder2024_discoverybench_towards_datadriven (arxiv:2407.01725)
- `2026-06-11T09:46:02Z` ingest_paper: ingested paper:lou2024_aaar10_assessing_ais (arxiv:2410.22394)
- `2026-06-11T09:46:03Z` ingest_paper: ingested paper:siegel2024_corebench_fostering_credibility (arxiv:2409.11363)
- `2026-06-11T09:46:04Z` ingest_paper: ingested paper:nguyen2026_replicatorbench_benchmarking_llm (arxiv:2602.11354)
- `2026-06-11T09:46:05Z` ingest_paper: ingested paper:waltman2018_exploration_reproducibility_issues (arxiv:1804.05024)
- `2026-06-11T09:46:06Z` ingest_paper: ingested paper:velden2018_exploration_reproducibility_issues (arxiv:1804.05026)
- `2026-06-24T04:06:34Z` Wiki initialized
