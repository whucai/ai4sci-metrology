# 四阶段论文复现链基准：从实验目的到结论验证

**Date**: 2026-06-05
**Context**: 在 EXPERIMENT_DESIGN_REVIEW.md 的 3-Level 框架之上，用户提出更深层的 4 阶段复现链

---

## 核心洞察

当前的 benchmark（无论是 ST/TE/CI 还是 FG/DO）都只测了**一个点**：给定公式/描述 → 写代码 → 数值对不对。

但真正的论文复现是一条**链**：

```
实验目的 → 研究设计 → 计量实验 → 实验结果 → 科学结论 → 结论可靠性
   ↑           ↑          ↑          ↑          ↑           ↑
 Stage 1    Stage 2    Stage 3    Stage 4    Stage 5?    Stage 6?
```

每个环节测试不同的科学推理能力。LLM 可能在某个环节很强（代码翻译），在另一个环节很弱（从实验目的推断研究设计）。这个链式基准**恰恰能揭示 LLM 科学推理的能力边界在哪儿**。

---

## 四阶段框架

### Stage 1: 研究设计推断 (Research Design Inference)

**问题**: 给定论文的实验目的/研究问题，不看完整论文，LLM 能否设计出一致的研究思路？

```
输入:
  - 论文的 Introduction 部分（描述研究动机和问题）
  - 论文的 Abstract
  - 明确排除: Methods, Results, Discussion

任务:
  - 设计实验方案来回答论文的研究问题
  - 包括: 数据需求、变量定义、分析策略、预期结果方向

评估:
  - 与论文实际 Methods 的语义一致性（LLM-as-judge + 人工抽查）
  - 方法选择的合理性（bibliometric expert 打分）
  - 关键设计要素的命中率（如: 是否选择了正确的指标类型、数据范围、对照组设计）

意义:
  - 测试 LLM 的"科学直觉"——看到问题，能否想到正确的实证策略
  - 这是审稿人的核心能力之一: 看到 intro 就能预判方法是否合理
```

**数据需求**: 10-15 篇 SciSci 方法论论文，每篇有清晰的 Intro+Methods 分离
**难度**: ⭐⭐⭐⭐⭐（最难自动评估）

---

### Stage 2: 计量实验复现 (Bibliometric Experiment Reproduction)

**问题**: 给定研究方法的描述，LLM 能否复现论文中的计量学实验？

```
输入:
  - 论文 Methods 部分（描述指标定义、计算步骤、数据来源）
  - 数据文件路径（SciSciNet parquet）
  - 不给精确公式（如果论文没有显式写出公式）

任务:
  - 从方法描述中提取计算逻辑
  - 编写代码在 SciSciNet 数据上执行
  - 处理数据边界条件（缺失值、异常值）

评估:
  - 数值正确率: |computed - gt| / max(|gt|, ε) < 阈值
  - REI: 需要多少次修复迭代
  - REI-c: 惩罚 silent failure
  - 按指标复杂度细分

意义:
  - 这是当前 benchmark 已经部分在测的（manual_papers L2/L3）
  - 但现在是整条链的一个环节，而非孤立测试
  - 关键区别: Stage 2 的方法描述来自 Stage 1 的输出或论文原始 Methods
```

**数据需求**: SciSciNet ground truth + 方法论论文的方法描述
**难度**: ⭐⭐⭐（已有 baseline）

---

### Stage 3: 科学结论推导 (Conclusion Derivation)

**问题**: 不看论文的 Discussion/Conclusion，只看实验结果，LLM 能否推导出相同的科学结论？

```
输入:
  - Stage 2 复现的实验结果（数值、图表、统计检验）
  - 论文的 Introduction（提供背景）
  - 明确排除: Discussion, Conclusion, 论文对结果的解释

任务:
  - 解读实验结果
  - 提炼科学发现
  - 将发现与原始研究问题联系起来
  - 注意: 这里不是要求 LLM "猜原文结论"，而是"基于数据推导合理结论"

评估:
  - 结论覆盖率: LLM 推导的结论覆盖了论文多少比例的核心声明？
  - 结论一致性: LLM 的结论与论文结论在方向和强度上是否一致？
  - 过度推断检测: LLM 是否声称了数据不支持的结论？
  - 评估方式: LLM-as-judge（GPT-4o/Claude 打分）+ 人工标注子集

意义:
  - 测试 LLM 的"科学解读"能力
  - 最关键的区分度: 好模型能从数据中正确提炼结论，差模型要么过度推断要么遗漏关键发现
```

**数据需求**: 论文的核心声明（claim）列表 + Stage 2 的复现结果
**难度**: ⭐⭐⭐⭐（评估需要良好的 claim schema）

---

### Stage 4: 结论-证据一致性判断 (Conclusion-Evidence Consistency Judgment)

**问题**: 给定论文的原始结论 + 复现的实验结果，LLM 能否判断复现结果是否支撑论文结论？

```
输入:
  - 论文的 Discussion/Conclusion 中的核心声明
  - Stage 2 复现的实验结果
  - 论文声称的结果（如果有）

任务:
  - 对比"论文声称的"和"复现得到的"
  - 判断: 充分支撑 / 部分支撑 / 不支撑 / 矛盾
  - 给出理由: 为什么支撑或不支撑

评估:
  - 与人类专家的判断一致性（需要至少 2 名 bibliometric 研究者标注）
  - F1 on 支撑/不支撑 binary classification
  - 理由质量打分

意义:
  - 这是审稿人的另一个核心能力: 判断作者的结论是否被数据支持
  - 与 Stage 3 互补: Stage 3 是"从数据到结论"，Stage 4 是"结论回到数据验证"
```

**数据需求**: 论文原始结论 + 复现结果 + 人类专家标注
**难度**: ⭐⭐⭐⭐（需要人工标注 ground truth）

---

## 四阶段的逻辑关系

```
Stage 1: 研究设计推断
  ↓ 产出: 方法设计
Stage 2: 计量实验复现
  ↓ 产出: 数值结果
Stage 3: 科学结论推导
  ↓ 产出: 推断的结论
Stage 4: 结论-证据判断
  ↓ 产出: 可复现性判决
```

**关键**: 每个 Stage 的输入可以是**论文原文**（测 LLM 的提取/理解能力）或**上一 Stage 的输出**（测整个链路的累积误差）。

这产生了两个实验条件：
- **Oracle 条件**: 每个 Stage 的输入是论文原文的对应部分（测各 Stage 独立能力）
- **Chain 条件**: 每个 Stage 的输入是上一 Stage 的 LLM 输出（测误差传播）

误差传播分析本身就是很有价值的发现——哪个 Stage 是瓶颈？错误在哪个环节最严重？

---

## 与现有框架的关系

| 现有框架 | 对应关系 |
|---------|---------|
| EXPERIMENT_DESIGN_REVIEW.md 的 ST (L1) | ≈ Stage 2 的简化版（给公式→写代码） |
| EXPERIMENT_DESIGN_REVIEW.md 的 TE (L2) | ≈ Stage 2（给方法描述→写代码） |
| EXPERIMENT_DESIGN_REVIEW.md 的 CI (L3) | ≈ Stage 1 + Stage 2（给概念→推断方法→写代码） |
| RESEARCH_DIRECTION.md Step 1 | = 四阶段整体（论文复现环境） |
| M2 的 4-Level Evaluation | Stage 4 的前身 |

**所以你的新框架不是推倒重来，而是把之前的碎片拼成了一个完整的故事。**

---

## 论文叙事逻辑

```
Introduction:
  - Scientific reproducibility crisis → need for automated verification
  - LLMs can read papers and write code — but can they REPRODUCE science?
  - We propose the first end-to-end benchmark of LLM scientific reproduction capability
  
  4 RQs:
  RQ1: Can LLMs design appropriate methods given only a research question? (Stage 1)
  RQ2: Can LLMs reproduce bibliometric experiments from method descriptions? (Stage 2)
  RQ3: Can LLMs derive valid conclusions from experimental results? (Stage 3)
  RQ4: Can LLMs judge whether conclusions are supported by evidence? (Stage 4)

Methods:
  - 10-15 SciSci papers with SciSciNet ground truth
  - 4 models (Qwen3-32B, GPT-4o, Claude Sonnet 4, DeepSeek-V3)
  - Oracle + Chain conditions
  - REI-c + claim-level evaluation

Results:
  [Stage 1]: Strong models achieve X% design consistency; all models struggle with [specific design elements]
  [Stage 2]: L1 ~95%, L2 ~60-80%, revealing capability boundaries
  [Stage 3]: Models can identify main effects but miss [nuance]; GPT-4o vs Claude show [difference]
  [Stage 4]: Models are conservative judges; false-positive rate [X%]
  [Chain]: Cumulative error from Stage 1→4 degrades overall reliability from [X] to [Y]

Discussion:
  - LLM scientific reasoning is a chain — weakest link determines overall reliability
  - Current LLMs can execute (Stage 2) but struggle with design (Stage 1) and interpretation (Stage 3)
  - Practical recommendation: human-in-the-loop at Stage 1 and Stage 3; trust LLMs at Stage 2 with verification
  - REI-c provides unified reliability metric across the chain
```

---

## 可行性分析

### 哪些 Stage 是可行的

| Stage | 可行性 | 关键挑战 |
|-------|--------|---------|
| Stage 1 | ⚠️ 中 | 评估需要 LLM-as-judge + 人工标注；论文需要清晰的 Intro/Methods 分离 |
| Stage 2 | ✅ 高 | 已有 baseline（manual_papers 92-100% L1, 60-75% L2/L3） |
| Stage 3 | ⚠️ 中 | 需要定义 claim schema；评估较主观 |
| Stage 4 | ✅ 中高 | 可以用 M2 的 4-level evaluation 框架；需要部分人工标注 |

### 最大风险

1. **Stage 1 和 Stage 3 的自动评估可能不可靠**。需要用 LLM-as-judge + 至少 50-100 条人工标注来校准。
2. **论文选择瓶颈**。需要 10-15 篇同时满足：有清晰 Intro/Methods/Results/Conclusion 分离 + 有 SciSciNet ground truth + 涉及 bibliometric 计算（不只是统计）。
3. **工作量**。4 Stages × 2 conditions × 4 models × 15 papers = 480 evaluation points，加上人工标注，估计 3-4 周。

### 建议的最小可行产品 (MVP)

**先做 Stage 2 + Stage 4**，用现有的 manual_papers benchmark 数据（8 篇方法论论文×3 测试论文=24 tests）。

- Stage 2: 已有完整数据（L1/L2/L3 results）
- Stage 4: 对 24 个复现结果，让 LLM 判断是否支撑原论文结论
- 这已经足够写一篇短文（投 QSS/Scientometrics 的 short paper）

**完整四阶段**可以作为后续的完整论文。

---

## 与 SciSciGPT 的定位差异（更新）

| | SciSciGPT | 你的四阶段框架 |
|---|-----------|--------------|
| 做什么 | 用 AI 做研究 | 测量 AI 做研究有多可靠 |
| 输出 | 研究结果 | 可靠性分数 + 能力边界图 |
| 对 LLM 的立场 | 信任（假设 LLM 能行） | 质疑（系统验证 LLM 哪里行哪里不行） |
| 科学贡献 | 工具/系统 | 基准/评测/理解 |
| 可发期刊 | Nature Comp Sci (已发) | Scientometrics / JASIST / QSS / Nature Comp Sci |

**你的工作恰恰是 SciSciGPT 缺失的那篇评测论文。**

---

## 待确认

1. **四阶段全做还是先做 MVP（Stage 2+4）？**
2. **Stage 1 和 Stage 3 的评估：依赖 LLM-as-judge 是否可接受？需要多少人工标注？**
3. **论文选择：优先用已有 8 篇方法论论文，还是系统收集 10-15 篇新的？**
4. **Chain 条件（误差传播分析）是加分项还是必须项？**
