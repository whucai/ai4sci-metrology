# 三个硬伤的系统性解决方案

**Date**: 2026-06-01
**状态**: 研究设计阶段

---

## 硬伤 1: 数据集陷阱 — 撤稿 ≠ 不可复现

### 问题

Retraction Watch 撤稿原因约 100+ 种标签，许多与论证质量无关：
- 虚假同行评议 → 论文文本/论证可能完美
- 重复发表 → 内容本身可能没问题
- 图像抄袭 → 与论证逻辑无关

如果把这些论文当作"低可复现性"样本，模型学到的是噪声而非信号。

### 解决方案: 科学硬伤过滤 (Scientific Hard-Injury Filter)

RW 数据库已有的 `REASON_CATEGORIES`（见 `src/data/retraction_watch.py:32-97`）：

```
硬伤类（纳入训练）              软伤类（排除）
─────────────────────────      ─────────────────────────
data_fabrication                plagiarism
  - Falsification/Fabrication     - 重复发表
  - of Data/Image/Results         - 抄袭

data_issues                     peer_review
  - Error in Data                  - 虚假同行评议
  - Error in Analyses              - 伪造审稿
  - Error in Results/Conclusions
  - Error in Methods             authorship
                                   - 作者争议
unreliable_results
  - Unreliable Data              ethics_legal
  - Unreliable Results             - 伦理违规
  - Contamination of Materials     - 法律问题

image_manipulation               paper_mill (有争议)
  - Duplication of/in Image        - 论文工厂
  - Manipulation of Images         - Tortured Phrases
  - Concerns about Image           - 注意：论文工厂论文的论证
                                    - 可能确实有结构缺陷，
                                    - 但更适合作为单独实验组
```

**实现**：在 `src/data/retraction_watch.py` 中添加 `filter_hard_injury_papers()` 函数。

**预期数据量**:
- RW 总量: ~50,000
- 有明确撤稿原因的: ~35,000
- 硬伤类过滤后: 估计 ~12,000-18,000 篇
- 有 DOI 可获取全文的: 估计 ~5,000-8,000 篇

### 正面样本（高可复现性）

| 数据源 | 说明 | 预期数量 |
|--------|------|---------|
| Reproducibility Project: Cancer Biology (RP:CB) | 已发表复现结果，明确标注复现成功/失败 | ~200 篇原始论文 |
| Reproducibility Project: Psychology (RPP) | 100 个心理学实验的复现结果 | ~100 篇 |
| ReproNLP Shared Task | NLP 领域的复现研究 | ~50 篇 |
| 正常高引论文（对照组） | 未被撤稿、无复现争议的高引论文 | 与硬伤组 1:5 匹配 |

---

## 硬伤 2: 结构自洽 vs 事实自洽

### 问题

图拓扑指标测量的是论证的**结构严密性**，不是论证的**真实性**。聪明的造假者可以构造逻辑完美的虚假论证图。

### 解决方案: 概念重构

**不要说**: "这篇论文的 AIS 评分低，所以它不可复现"
**要说**: "这篇论文的**论证严密度 (Argumentative Rigor)** 评分低，表明其论证结构存在脆弱性，复现失败的风险更高"

具体调整：

#### 2.1 指标重命名

| 旧名 (撤稿检测) | 新名 (可复现性评价) |
|----------------|---------------------|
| Fraud Score | **Argumentative Rigor Score (ARS)** |
| Support Debt Index | **Evidence Support Ratio (ESR)** |
| Graph Coherence Score | **Argument Chain Coherence (ACC)** |
| Anomaly Score | **Structural Vulnerability Index (SVI)** |

#### 2.2 声明降级

```
强声明 (不可做):
  "Our method predicts reproducibility with AUC 0.85."
  
弱声明 (可做):  
  "Papers with low Argumentative Rigor Score are 3.2x more likely 
   to have been retracted for scientific hard injuries 
   (data fabrication/errors) compared to matched controls."
  
最弱声明 (最安全):
  "We identify a set of argumentation graph topology metrics (ESR, ACC, SVI) 
   that are statistically significantly different between papers retracted 
   for scientific misconduct and matched non-retracted papers 
   (p < 0.001, Cohen's d > 0.5)."
```

#### 2.3 论文标题方向

- "Measuring Argumentative Rigor in Scientific Papers: A Graph Topology Approach"
- "Structural Vulnerability of Scientific Argumentation: Evidence from Retracted Papers"
- "Argumentation Graph Topology as a Signal of Scientific Rigor"

---

## 硬伤 3: 论证挖掘的噪音问题

### 问题

LLM 从长篇 PDF 中提取论证三元组时容易产生幻觉：
- 强行脑补 Claim-Evidence 之间的因果关系
- 把背景陈述误标为 Evidence
- 忽略重要的反驳/限定条件
- 对长文档（>20页）的中间段落提取质量下降

### 解决方案: 多级置信度过滤流水线

```
PDF全文
   │
   ▼
┌─────────────────────────────────────┐
│ Stage 1: 结构化段落提取              │
│ - Grobid / PyMuPDF4LLM 解析章节      │
│ - 只保留: Intro, Methods, Results,   │
│   Discussion                         │
│ - 丢弃: 致谢、参考文献、补充材料       │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Stage 2: LLM 论证三元组提取          │
│ - 逐段处理 (每个 chunk ≤ 2000 words) │
│ - 输出: (claim, premise, evidence,   │
│   relation_type, confidence)         │
│ - Prompt 要求: 必须是显式陈述的      │
│   关系，不得推断隐含关系              │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Stage 3: 置信度评分                  │
│ - LLM 自评置信度 (1-5)              │
│ - 规则过滤:                          │
│   · Claim 必须包含在原文中            │
│   · Evidence 必须来自 Methods/Results │
│   · support/attack 关系必须由显式     │
│     连接词标记 (therefore, however...)│
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Stage 4: 图构建与过滤                │
│ - 高置信度 (≥4): 直接保留            │
│ - 中置信度 (3): 保留但标记           │
│ - 低置信度 (<3): 丢弃                │
│                                      │
│ 构建两个版本的图:                     │
│   G_full: 所有通过 Stage 3 的边       │
│   G_strict: 仅高置信度 (≥4) 的边     │
│                                      │
│ 报告两个版本的指标差异                 │
└──────────────┬──────────────────────┘
               ▼
┌─────────────────────────────────────┐
│ Stage 5: 人机一致性验证 (Pilot)      │
│ - 随机抽样 50 篇论文                 │
│ - 人工标注论证三元组                  │
│ - 计算:                              │
│   · 三元组召回率 (recall@K)          │
│   · 三元组精确率 (precision@K)       │
│   · 图编辑距离 (G_full vs G_human)   │
│   · 图编辑距离 (G_strict vs G_human) │
│ - 验证: G_strict 的精度应显著高于     │
│   G_full，且图编辑距离更小            │
└─────────────────────────────────────┘
```

### 关键设计决策

1. **宁可残缺，不要幻觉。** G_strict 如果只有 40% 的边但 90% 准确，比 G_full 有 80% 的边但 60% 准确更有用。

2. **图拓扑指标应具有鲁棒性。** 测试指标在 G_full 和 G_strict 下的 spearman 相关性。如果 r > 0.8，说明指标对提取噪音鲁棒。

3. **分章节分析。** Introduction 和 Discussion 的论证结构可能不同。可以分别计算每章的图指标，观察章节间的差异本身是否是一个信号。

---

## 实施优先级

| 优先级 | 任务 | 依赖 | 估计工作量 |
|--------|------|------|-----------|
| P0 | RW 数据硬伤过滤脚本 | 已有 REASON_CATEGORIES | 0.5 天 |
| P0 | 正面样本收集 (RP:CB, RPP) | 公开数据 | 1 天 |
| P1 | 论证提取置信度 Prompt 设计 | 需要 GPT-4o/Claude API | 1 天 |
| P1 | 50 篇人工标注 + 人机一致性验证 | 需要领域知识 | 2 天 |
| P2 | G_full vs G_strict 对比实验 | P0, P1 完成 | 1 天 |
| P2 | 指标-撤稿原因关联分析 | P0 完成 | 1 天 |
