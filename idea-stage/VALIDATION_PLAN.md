# 图提取方法与拓扑指标有效性验证方案

**Date**: 2026-06-01
**核心目标**: 证明我们的图提取方法比 baseline 更准，拓扑指标在论文质量评价上有区分力

---

## 实验设计概览

```
Experiment 1: 论证图提取精度验证（Benchmark 层面）
  ├── E1a: ADU 识别 (Sci-Arg, AbstRCT, PE)
  ├── E1b: 论证关系分类 (Sci-Arg, AbstRCT, PE, KIALOPRIME)
  └── E1c: 端到端图构建精度 (Sci-Arg full-text)
       → 证明: 我们的图提取比现有方法更准

Experiment 2: 拓扑指标的区分力验证（论文质量层面）
  ├── E2a: 硬伤撤稿 vs 正常论文的双样本检验
  ├── E2b: 图指标 vs 文本特征 vs 文献计量的对比
  └── E2c: 细粒度分析——不同硬伤类型的图谱差异
       → 证明: 图拓扑指标提供了文本/文献计量之外的独立信号

Experiment 3: 消融实验
  ├── E3a: 置信度过滤阈值对指标区分力的影响
  └── E3b: 不同 LLM 提取的图在拓扑指标上的一致性
       → 证明: 指标对提取噪音具有鲁棒性
```

---

## Experiment 1: 论证图提取精度验证

### E1a: ADU 识别 (Argumentative Discourse Unit Recognition)

**Benchmark 数据集**:

| 数据集 | 领域 | 规模 | 任务 | SOTA |
|--------|------|------|------|------|
| Sci-Arg | 计算语言学 | 40 篇全文 | ADU 分类 (claim/data) | SciBERT+CRF: macro-F1 0.518 (token), 0.532 (span) |
| AbstRCT | 生物医学 | ~3.5K 句 | 论证成分分类 (MajorClaim/Claim/Premise) | LLaMA-3 fine-tuned: F1 ~0.78 |
| PE (Persuasive Essays) | 学生议论文 | 402 篇 | 成分类型 (MajorClaim/Claim/Premise) | LLaMA-3 fine-tuned: F1 ~0.82 |

**Baselines**:
1. SciBERT+CRF (Binder et al. 2022) — 当前 Sci-Arg SOTA
2. LLaMA-3-8B fine-tuned (Hernault et al. COLING 2025) — 泛用 SOTA
3. GPT-4o zero-shot prompt (无微调基准)
4. oAMF 流水线 (Ruiz-Dolz et al. 2025) — 模块化基线

**我们的方法**:
- Claude/DeepSeek 结构化 prompt + 置信度过滤
- Stage 2 (LLM 提取) + Stage 3 (置信度评分) 的 full pipeline

**评估指标**: token-level macro-F1, span-level exact/weak F1, per-class F1

### E1b: 论证关系分类 (Argumentative Relation Extraction)

**Benchmark 数据集**:

| 数据集 | 关系类型 | 规模 | SOTA |
|--------|---------|------|------|
| Sci-Arg | supports/contradicts | 6,389 条 | SciBERT: micro-F1 0.739 |
| AbstRCT | supports/attacks | ~1,800 条 | LLaMA-3 fine-tuned: F1 ~0.64 |
| PE | supports/attacks | ~3,800 条 | LLaMA-3 fine-tuned: F1 ~0.76 |
| KIALOPRIME | support/attack | 1,088,801 条 | Baseline: F1 0.899-0.908 |

**Baselines**:
1. SciBERT (Sci-Arg SOTA)
2. LLaMA-3 fine-tuned (cross-dataset SOTA)
3. GPT-4o zero-shot
4. ARIES benchmark baselines (RoBERTa, DeBERTa, T5)

**我们的方法**: LLM prompt + 关系方向验证 + 高置信度过滤

**评估指标**: micro/macro-F1, per-relation F1 (support vs attack)

### E1c: 端到端图构建精度

在 Sci-Arg 40 篇全文上，端到端构建论证图，与人工标注的 gold graph 对比。

**评估指标**:
- **图编辑距离 (Graph Edit Distance)**: GED(G_pred, G_gold) / |V_gold|
- **节点 F1**: 正确识别+正确分类的 ADU
- **边 F1**: 正确识别+正确分类的关系
- **全图准确率**: 同时正确识别节点和边的比例

**关键对比**:
```
G_full  (所有通过 Stage 3 的边) vs G_gold
G_strict (仅高置信度边)       vs G_gold
G_baseline (SciBERT pipeline) vs G_gold
```

**预期**: G_strict 的边精度应该显著高于 G_baseline，即使边召回率稍低。

---

## Experiment 2: 拓扑指标的区分力验证

### 数据集

- **硬伤样本**: RW 数据库中硬伤类撤稿论文 (data_fabrication + data_issues + unreliable_results + image_manipulation)，约 12,661 篇有 DOI
- **对照组**: 同期刊同年份发表的正常论文，Coarsened Exact Matching (期刊 × 年份 × 类型)
- **复现失败样本**: Reproducibility Project 中"复现失败"的论文 (~150-200 篇)
- **复现成功样本**: Reproducibility Project 中"复现成功"的论文 (~100 篇)

### E2a: 双样本检验 — 硬伤撤稿 vs 正常论文

**假设**:
- H1: 硬伤撤稿论文的 ESR (Evidence Support Ratio) 显著低于正常论文
- H2: 硬伤撤稿论文的 ACC (Argument Chain Coherence) 显著低于正常论文
- H3: 硬伤撤稿论文的 SVI (Structural Vulnerability Index) 显著高于正常论文

**方法**: 
1. 从硬伤样本中随机抽取有全文 PDF 的论文 N=200
2. CEM 匹配 200 篇同期刊同年份正常论文（OpenAlex 获取全文）
3. 用我们的流水线提取两组的论证图
4. 计算 ESR, ACC, SVI 三个指标
5. Welch's t-test + Cohen's d + Mann-Whitney U

**预期效应量**: Cohen's d > 0.4 (中等效应)

### E2b: 特征区分力对比 — 图拓扑 vs 文本特征 vs 文献计量

**特征组**:
| 特征组 | 特征 | 来源 |
|--------|------|------|
| 图拓扑 (our) | ESR, ACC, SVI | 本方法 |
| 文本风格 | 模糊限制语密度、被动语态比例、可读性 | Braud & Søgaard 2017 |
| 文献计量 | 引用数、作者h指数、国际合作、自引率 | Liu et al. 2025 IPM |
| 论证质量 | Freedman & Toni (2024) 特征 | ArgMining 2024 |

**方法**: 
- 4 组特征分别在硬伤 vs 正常论文上训练 XGBoost 分类器
- 5-fold CV，报告 AUC + precision/recall
- DeLong test 比较 AUC 差异是否显著
- 训练融合模型（all features）→ 特征重要性分析

**关键主张**: 图拓扑特征的 AUC 应显著 > 0.5，且独立贡献（融合模型中特征重要性 > 0）超越其他特征。

### E2c: 细粒度分析 — 不同硬伤类型

**分组**:
- data_fabrication (N=2,043)
- data_issues (N=7,629)
- image_manipulation (N=6,028)
- unreliable_results (N=490)

**分析**:
- 四组的 ESR/ACC/SVI 均值是否有显著差异 (ANOVA + Tukey HSD)
- 假设: data_fabrication 组的论证严密性最低（刻意伪造的数据最不可能有自然论证结构）
- image_manipulation 组可能论证严密性正常（单纯 P 图不改变论证逻辑）

---

## Experiment 3: 消融实验

### E3a: 置信度过滤阈值

**变量**: 置信度阈值 t ∈ {2, 3, 4, 5}（保留置信度 ≥ t 的边）

**测量**:
- G_t 与 G_gold 的边 F1（精度指标）
- 硬伤 vs 正常论文在 G_t 下的 ESR/ACC/SVI 效应量 Cohen's d

**预期**: 存在 sweet spot — t=3 时指标区分力最优（平衡了噪音和稀疏性）

### E3b: 跨模型一致性

**变量**: 提取 LLM ∈ {Claude, DeepSeek, GPT-4o, Qwen-2}

**测量**:
- 同一篇论文在不同 LLM 提取下的 ESR/ACC/SVI spearman 相关性
- 不同 LLM 下硬伤 vs 正常的 Cohen's d 是否一致

**预期**: 不同 LLM 提取的绝对指标值可能不同，但硬伤 vs 正常的组间差异方向和效应量应保持一致（r > 0.7）

---

## 论文实验章节结构

```
4. Experiments
  4.1 Graph Extraction Accuracy (E1a, E1b, E1c)
    - Table: ADU F1 comparison across Sci-Arg, AbstRCT, PE
    - Table: Relation F1 comparison across benchmarks
    - Table: End-to-end graph construction accuracy on Sci-Arg
  4.2 Topological Metric Discriminative Power (E2a)
    - Table: ESR/ACC/SVI for retracted vs control (mean, std, p, d)
    - Figure: Raincloud plot of metric distributions
    - Figure: ROC curves for individual metrics
  4.3 Feature Comparison (E2b)
    - Table: AUC of argument-graph vs text-style vs bibliometric features
    - Figure: Feature importance from XGBoost (all features)
  4.4 Fine-grained Analysis (E2c)
    - Table: Metrics by retraction reason category
    - Figure: Heatmap of metric × reason category
  4.5 Ablation Studies (E3a, E3b)
    - Figure: Effect size vs confidence threshold
    - Table: Cross-model Spearman correlation
```

---

## 基线 vs 我们方法的优势总结

| 对比维度 | 现有 SOTA | 我们的方法 | 优势 |
|---------|----------|-----------|------|
| 论证图提取精度 | SciBERT+CRF (Sci-Arg F1=0.53) | LLM + 置信度过滤 | 语义理解更深，关系方向更准 |
| 分析粒度 | 仅摘要 (Freedman) 或仅文本特征 | 全文论证图 + 拓扑指标 | 捕捉全局论证结构 |
| 可解释性 | 特征重要性（黑盒） | 每个指标有明确图论含义 | 解释"为什么这篇论文风险高" |
| 跨数据集泛化 | 差（ARIES 2024 已证明） | LLM zero-shot 泛化 | 不需要逐数据集微调 |
| 论文质量信号 | 引用/文本特征 | 论证结构特征 | 提供新维度的信号 |
