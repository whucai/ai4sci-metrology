# 实验设计审视：LLM 文献计量计算能力基准

**Date**: 2026-06-04
**Context**: 对 stratified benchmark 和 manual papers benchmark 的批判性审视

---

## 1. 当前实验的根本问题

### 1.1 概念混淆

当前所有实验混滑了两个完全不同的问题：

| 问题A：论文复现 | 问题B：公式实现 |
|----------------|----------------|
| 给 LLM 论文全文 → 提取方法 → 找数据 → 执行分析 → 对比论文声称的结果 | 给 LLM 公式/概念描述 → 写代码 → 执行 → 对比已知 ground truth |
| 需要：论文理解 + 方法提取 + 数据定位 + 结果对比 | 需要：公式理解 + 代码翻译 |
| Ground truth = 论文自己声称的结果 | Ground truth = SciSciNet 预计算字段 |
| **这是 SciSciGPT 做的事** | **这是你现在测的事** |

你的实验测的是问题 B，但论文叙事（RESEARCH_DIRECTION.md）讲的是问题 A。这个 gap 必须解决。

### 1.2 stratified L2/L3 的致命缺陷

```
stratified L2 设计：
  输入：随机 Management Science 论文的摘要（如 "Optimal Forecasting Groups"）
  任务：推断 D-index 公式并实现
  结果：4% 正确

问题：这些论文根本不描述 D-index。你在测试 "LLM 能不能从无关文本推断公式"，
     而不是 "LLM 能不能从描述公式的文本中提取公式"。
```

这不是 LLM "推理失败"，是实验输入不包含目标信息。

### 1.3 单模型问题

所有实验只用 Qwen3-32B。任何关于"LLM 做不到 X"的结论都无法推广到其他模型。

---

## 2. 重新定义研究问题

### 诚实的研究问题

**"给定不同具体程度的文献计量指标描述，LLM 能否从原始引文数据中正确计算该指标？"**

这有三个子问题，每个测不同的能力：

```
Level 1: 规格翻译 (Specification Translation)
  "给你精确公式和算法步骤，能翻译成正确代码吗？"
  测试：代码生成能力

Level 2: 文本提取 (Text Extraction)  
  "给你一篇描述了公式的方法论论文，能提取公式并应用到新数据吗？"
  测试：阅读理解 + 方法迁移

Level 3: 概念推断 (Conceptual Inference)
  "只给你指标名称和概念描述，能推断出正确公式吗？"
  测试：科学知识 + 推理
```

### 三个 Level 分别回答什么问题

| Level | 输入中包含公式？ | 测试什么 | 实际意义 |
|-------|---------------|---------|---------|
| L1 | ✅ 精确公式+算法 | 代码翻译 | "LLM 能替代程序员吗？" |
| L2 | ✅ 论文描述了公式 | 方法提取 | "LLM 能读论文实现方法吗？" |
| L3 | ❌ 只有概念描述 | 公式推断 | "LLM 能独立做科学推理吗？" |

---

## 3. 新的实验设计

### 3.1 Level 1: Specification Translation (ST)

**RQ**: "When given the exact mathematical specification, can LLMs faithfully implement bibliometric computations?"

```
设计: within-subjects
  模型: Qwen3-32B, GPT-4o, Claude Sonnet 4, DeepSeek-V3
  指标: 5-6 种 (D-index, novelty, conventionality, team size effect, citation prediction, field-normalized citation)
  论文: 每指标 30-50 篇 (ground truth from SciSciNet)
  
Prompt 结构:
  - 精确数学公式 (如 D = (n_i-n_j)/(n_i+n_j+n_k))
  - 每个变量的定义
  - 分步算法描述 (1→2→3→4→5)
  - 数据文件路径和列名
  - 期望的输出格式

评估:
  - 执行成功率
  - 数值正确率 (|computed - gt| / max(|gt|, ε) < 0.01)
  - REI, REI-c
  - 按指标类型、论文特征细分
```

**预期**: 强模型 >95% 正确。这建立 baseline——证明 LLM 至少能做代码翻译。

**已完成**: benchmark_disruption_v2 (Qwen3-32B, 100 papers, D-index, L1) = 99% 正确 ✅

### 3.2 Level 2: Text Extraction (TE)

**RQ**: "When a methodology paper explicitly describes a computational formula, can LLMs extract and correctly apply it to new data?"

```
设计: 独立的方法论文本 × 独立的测试数据
  
方法论论文 (10-15篇):
  选择标准:
    - 论文明确描述了某个文献计量指标的计算公式
    - 该指标在 SciSciNet 中有对应的 ground truth
    - 覆盖不同期刊 (Nature, Science, PNAS, Management Science, Research Policy)
  
  候选论文:
    1. Wu, Wang & Evans (2019) Nature — D-index 公式明确
    2. Park, Leahey & Funk (2023) Nature — D-index + CD index
    3. Ke, Gates & Barabási (2023) PNAS — 网络归一化影响力
    4. Funk & Owen-Smith (2017) MS — D-index 变体
    5. Wang, Song & Barabási (2013) Science — 长期影响力
    6. Uzzi et al. (2013) Science — 非典型组合与影响力
    7. Azoulay et al. (2019) — 突破性创新的测量
    8. Bornmann et al. (2020) — 颠覆性指数综述
    9-15. [需进一步收集]

测试论文 (每方法论论文 × 5篇 = 50-75 tests per model):
  选择标准:
    - 在 SciSciNet 中有完整 ground truth
    - 有足够的引文数据 (≥5 citations, ≥2 references)
    - 分层抽样: disruption 高/中/低

Prompt 结构:
  - 方法论论文全文 (markdown, ≤30K chars)
  - 任务描述: "Read this paper's methodology. Implement [metric name] for test paper X"
  - 测试论文的数据文件路径
  - 输出格式提示 (但不给公式本身)

关键设计决策:
  - 方法论论文和测试论文是分开的:
    方法论论文描述"怎么算 D-index"
    测试论文是需要计算 D-index 的具体论文
  - 这模拟了真实的复现场景:
    读 Wu2019 → 理解 D-index 公式 → 对一篇新论文计算 D-index

评估:
  - 各模型的公式提取成功率
  - 数值正确率
  - 是否出现了"公式幻觉"(编造了看似合理但错误的公式)
  - 按方法论论文难度细分
```

**这是整个实验设计的核心创新**。它测试了 LLM 的真正实用价值：能不能读一篇方法论文，然后把方法应用到新数据上。

**已完成部分**: manual_papers_benchmark v2 (Qwen3-32B, 8 methodology papers, 3 test papers) = 60% L1 success, 21% L2 success ⚠️

### 3.3 Level 3: Conceptual Inference (CI)

**RQ**: "Without access to the formula, can LLMs infer the correct computational method from the metric's name and conceptual description alone?"

```
设计: 只给概念，不给公式

指标: D-index only (最知名、LLM 训练数据中最可能见过的指标)
论文: 50篇

Prompt 结构:
  - 指标名称: "Disruption Index (D-index)"
  - 概念描述: "Measures whether a focal paper is disruptive (cited instead of its references) or consolidating (cited alongside its references)"
  - 数据文件路径
  - 输出格式: D_INDEX = <value>
  - 不给公式、不给算法、不给变量定义

评估:
  - 能推断出 D = (n_i-n_j)/(n_i+n_j+n_k) 或相近公式吗？
  - 区分:
    (a) 正确的 D-index 实现
    (b) 看起来合理但错误的实现 (如 D = n_i/(n_i+n_j))
    (c) 完全不相关的实现
  - 跨模型对比: 更大的模型/更多科学训练数据的模型是否更好？
```

**预期**: 所有模型出错率高。但这个结果本身就很有意义——证明即使是前沿 LLM 也不能独立推断科学公式，必须有人类提供的规格说明。

**已完成**: stratified_benchmark L2/L3 (Qwen3-32B, 50 papers) = 4%/2% 但实验设计有缺陷（论文不一定描述D-index）。需要重做，用清晰的"只给概念" prompt。

---

## 4. 新旧实验对照

| 旧实验 | 问题 | 新设计对应 | 改进 |
|--------|------|----------|------|
| benchmark_disruption_v2 | ✅ L1 设计正确 | Level 1 (ST) | 扩展到多指标、多模型 |
| stratified L2 (no formula) | ❌ 随机论文不描述D-index | Level 3 (CI) | 用标准化概念 prompt，不用随机论文 |
| stratified L3 (full paper) | ❌ 同上 | Level 2 (TE) | 方法论论文必须描述公式 |
| manual_papers v2 L1 | ✅ 真方法论论文+给公式 | Level 1 (ST) | 扩展论文数量 |
| manual_papers v2 L2 | ⚠️ 方法论论文+描述 | Level 2 (TE) | 分离方法论文本和测试数据 |
| e2e "abstract"/"pdf" | ❌ 偷偷给了公式 | — | 删除，这假 L2/L3 没有意义 |

---

## 5. 论文叙事逻辑

```
引言: LLM 被广泛应用于科学代码生成，但其数值可靠性未经验证
  
  └→ Level 1 实验 (ST): 给公式能写对吗？
      结果: [X%] 正确 → "LLMs can translate specifications faithfully"
      
  └→ Level 2 实验 (TE): 读方法论论文能提取公式吗？
      结果: [Y%] 正确 → "But extracting methods from papers is significantly harder"
      
  └→ Level 3 实验 (CI): 不给公式能推断吗？
      结果: [Z%] 正确 → "And inferring formulas from concepts alone is beyond current LLMs"

讨论: 三层级揭示了 LLM 可靠性的明确边界
  - 可以信任 LLM 做: 有精确规格的计算 (Level 1)
  - 需要人类监督: 从论文中提取方法 (Level 2)  
  - 不能信任 LLM 做: 独立推断科学公式 (Level 3)
  - REI-c 提供了统一的可靠性度量框架
```

---

## 6. 实验工作量重估

| 任务 | 模型 | 数据量 | 估计时间 |
|------|------|--------|---------|
| Level 1 多指标扩展 | Qwen3-32B | 6 metrics × 50 papers = 300 | ~3 GPU-hr |
| Level 1 | GPT-4o/Claude/DeepSeek | 同上 ×3 | API 调用 + $50-100 |
| Level 2 方法论论文收集 | — | 找 10-15 篇论文 + PDF→markdown | 1 天 |
| Level 2 实验 | Qwen3-32B | 12 papers × 5 tests = 60 | ~2 GPU-hr |
| Level 2 实验 | 3 API 模型 | 同上 ×3 | API 调用 |
| Level 3 | 全部 4 模型 | 50 papers | ~4 GPU-hr + API |
| 结果分析 + 图表 | — | — | 2 天 |

**总计**: 约 1.5-2 周

---

## 7. 待确认决策

1. **方法论论文选择**: Level 2 需要 10-15 篇明确描述文献计量公式的论文。需要系统检索还是用现有的 bench-mark/ 里的 8 篇就够了？

2. **多模型接入**: 需要确认 GPT-4o、Claude、DeepSeek 的 API key 可用性。如果没有，是否接受只用 2 个模型（Qwen3-32B + 1 个 API 模型）？

3. **Level 3 的必要性**: 如果 Level 1 + Level 2 已经足够支撑论文（三层叙事简化为两层），Level 3 可以裁剪。你觉得呢？

4. **投稿策略**: 三层实验设计的论文规模适合 Scientometrics/QSS。如果要冲 Nature Computational Science，可能需要加 Human Baseline（至少 Level 2 的人机对比）。
