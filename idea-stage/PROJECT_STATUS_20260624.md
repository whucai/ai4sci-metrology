# 项目全局状态总览：研究目的 · 实验进展 · 阶段性结论

**日期**: 2026-06-24
**项目**: AI for Science 计量学范式 — 大模型驱动的计算型论文复现质量评估
**对标**: 王大顺 Science of Science 传统, SciSciGPT (Nature Computational Science 2025)

---

## 一、研究目的总览

### 1.1 三步走宏观框架

| Step | 方向 | 核心问题 | 状态 |
|------|------|---------|------|
| **Step 1** | 自动论文复现环境（AI Reproducibility Metrology） | 造一台"计量仪器"：AI 自动读论文→复现分析→判断可复现性 | 主力推进中 |
| **Step 2** | 人机协作实验设计（AI-Assisted Experiment Design） | AI 根据研究想法+现有数据，自动提出实验方案 | 待 Step 1 完成后启动 |
| **Step 3** | 范式转变论述（Vision Paper） | 从"相关性计量"到"因果性复现"的范式跃迁 | 远期 |

### 1.2 Step 1 内部两条线

#### 线 A: SciSciBench — 大模型科学推理能力基准测试

**核心问题**: LLM 能否从论文的方法和数据出发，重建实验设计并推断科学结论？

**两个 Task**:
- **Task 1 (实验设计重建)**: Idea + Data → Experiment Design（模型、变量、方法识别）
- **Task 2 (结论推断)**: Idea + Data + Experiment → Conclusion（L1/L2/L3 三级难度）

**关键区分**: 这个基准测试的是 LLM 的**科学推理能力**（读论文→推理实验设计→推断结论），不是复现执行能力。

#### 线 B: Reproduction Quality Framework — 论文复现质量多维评估框架

**核心问题**: LLM 执行论文复现时，能否忠实重建从数据→样本→指标→模型→结果→结论的完整证据链？

**五个评估维度**: Task Understanding, Data/Sample, Indicator/Metric, Result, Process Reliability

**六个复现成熟度等级**: L0 (Failure) → L5 (Auditable Reproduction)

**关键区分**: 这个框架评估的是 LLM 的**复现执行质量**（写代码→跑数据→出结果→比结论），不是推理能力。

### 1.3 两条线的关系

```
SciSciBench (推理能力)           Reproduction Framework (执行质量)
      ↓                                    ↓
读论文 → 推理实验设计               读论文 → 写代码 → 跑数据
读结果 → 推断结论                   对比指标 → 判断复现是否成功
      ↓                                    ↓
"LLM 理解科学吗？"                 "LLM 能复现科学吗？"
```

两条线共享相同的论文池和评估基础设施，但回答不同的问题。

---

## 二、线 A: SciSciBench 实验进展与结论

### 2.1 已完成的工作

| 日期 | 里程碑 | 内容 |
|------|--------|------|
| 2026-06-05 | 基准重构 | 4-stage paper reproduction chain 框架（阶段1-4统一包+runner+evaluator） |
| 2026-06-06 | 首次真实 LLM 运行 | Stage 2+4, Qwen3-32B, 24 tasks, 95.8% success, REI-c mean=1.59 |
| 2026-06-11 | 三项工程防御 | 强制 JSON 输出（Task1）、三层污染防御、双轨评估 |
| 2026-06-12 | 全量基准 | 118 papers × 575 tasks, Task1 F1=0.435, Task2 score=0.654 |

### 2.2 四轮自动评审循环（2026-06-12 ~ 2026-06-15）

经过 4 轮 Codex 审查，修复了 **10 个评估器 bug**，建立了 42 个回归测试。

**最终基准结果（Qwen3-32B, 115 papers）**:

| Level | Qwen3 | Template | P(Qwen>template) | 是否区分模型？ |
|-------|-------|----------|-------------------|---------------|
| L1 | 0.674 | 0.659 | 0.775 (NS) | ❌ 不区分 |
| **L2** | **0.907** | 0.759 | 1.000 (***) | ✅ 显著区分 |
| L3 | 0.630 | 0.615 | 0.778 (NS) | ❌ 不区分 |

**L2 组件细节**（唯一有效的 level）:
- direction_accuracy: 0.944
- significance_match: 0.817
- claim_support_score: 0.978
- hallucinated_claim_rate: 0.156

### 2.3 数据集分析发现

- **方法分布严重失衡**: 74% 是描述性统计，仅 4% 是回归分析
- **发表偏倚确认**: 78% 结论方向为正
- **时间偏倚**: 58% 论文来自 2020–2024
- **标注伪影**: 所有论文恰好有 2-3 条 limitations，污染评估全部标记为 "unknown"
- **30% 论文缺少 venue 信息**

### 2.4 线 A 阶段性结论

1. **L2 是唯一有区分力的 level** — Qwen3-32B 显著优于模板基线（+0.148）
2. **L1 和 L3 不区分模型能力** — 模板基线几乎与 Qwen3 持平
3. **L2 可能测量的是"结果提取"而非"科学推理"** — 高 direction/significance 分数可能反映的是从完整结果中解析结构化信息的能力
4. **Gold annotation 未经人类专家验证** — 几乎所有 gold labels 都是 LLM 提取的（insider validation 风险）
5. **仅评估了单一模型** — 无法证明基准能可靠排序模型
6. **当前状态**: 不适合顶会投稿（4/10），可作为 workshop 的基准开发研究（5/10）

### 2.5 L3 评分协议修订（2026-06-24）

**问题**: 旧协议产生 ceiling effect（claim_support=1.000 for all papers），且将谨慎的 "unknown" 预测视为完全错误。

**三项修复**:
1. **方向校准矩阵**: 部分正确（tentative_positive）=0.75, 合理不确定（unknown）=0.25
2. **分级证据支持**: strong=1.0, moderate=0.6, weak=0.3
3. **重新平衡权重**: 0.25×dir + 0.25×css + 0.15×specificity + 0.15×limitation + 0.10×anchor + 0.10×(1-halluc)

**DeepSeek V4 Pro L3 重跑结果（211 papers）**:
- Overall: 0.298（vs Qwen3 旧的 0.689，因消除 ceiling effect 而显著降低）
- direction_accuracy (calibrated): 0.325
- claim_support (graded): 0.300
- support_strength: 100% "weak" — DeepSeek 对证据强度的诚实评估
- **关键发现**: L3 真实能力可能在 0.3-0.5 区间，Qwen3 的 0.689 是人为膨胀的

---

## 三、线 B: Reproduction Quality Framework 实验进展与结论

### 3.1 理论框架（已完成）

**6 组件 × 5 维度评估矩阵**（IDEA_REPORT.md, RESEARCH_BRIEF.md, EXPERIMENT_PLAN.md）:

| Component | Fidelity | Executability | Numerical Accuracy | Claim Consistency | Auditability |
|-----------|----------|---------------|-------------------|-------------------|-------------|
| Data Source | ✓ | ✓ | — | — | ✓ |
| Sample | ✓ | ✓ | ✓ | — | ✓ |
| Indicator | ✓ | ✓ | ✓ | — | ✓ |
| Model | ✓ | ✓ | ✓ | — | ✓ |
| Result Table | ✓ | ✓ | ✓ | ✓ | ✓ |
| Claim | ✓ | — | — | ✓ | ✓ |

**四种任务类型**:
- STRICT: 同数据同模型 → 数值精确匹配
- DATA-SUB: 替代数据 → 方向/机制一致性
- METHOD: 仅复现方法 → 无数值目标
- CLAIM-ROBUST: 新数据测试结论 → 外部有效性

### 3.2 M0 实验进展（6/8 完成）

| Run | Paper | Task Type | Result | Key Finding |
|-----|-------|-----------|--------|-------------|
| R000 | Wu2019 | 模拟 | DONE | 4 种失败模式可区分，spurious 检测有效 |
| R001 | Wu2019 | DATA-SUB L3(ds) | DONE | SciSciNet→Wu2019, 方向正确(NEGATIVE), coef=-0.0093 |
| R001b | Wu2019 | DATA-SUB L3(ds) | DONE | 约束复现，8 模块证据链完整，compliance PASS |
| **R002** | **Petersen2024** | **STRICT L3** | **DONE** | **D3=8/8(100%), 所有系数匹配到 6+ 位小数, N 精确** |
| R003 | Arts2021 | COMPONENT_DIAGNOSIS | DONE | 10 NLP 指标诊断，精确定位公式 bug（行 233-236） |
| **R004** | **Park2023** | **STRICT L3** | **DONE** | **D3=6/6(100%), CD1945=0.035979 精确, 66 年均值精确** |
| R005 | Zhao2025 | METHOD | DONE | 新颖性测量分类法，Overall=0.98, 无数值目标 |
| **R007** | **Bentley2023** | **STRICT L3** | **DONE** | **D3=9/9(100%), citation-weighted CD 精确, 第三篇 STRICT 满分** |

### 3.3 M1 基准测试（已完成，待分析）

**10-paper M1 full benchmark**（Gemma-4-26B-A4B-it）:
- 10/10 papers 成功（2 篇初始 context window overflow → 已修复）
- Pilot papers (1-3): fidelity 0.72-0.77, maturity L1-L2
- Group B papers (4-10): fidelity 0.20-0.44
- Model 组件持续薄弱；Claim 组件在 Group B 中较弱
- M1 四项测试全部 PASS（correlation, failure diversity, spurious）

### 3.4 线 B 阶段性结论

1. **STRICT 复现路径已验证** — 3/3 篇论文 D3=100%（Petersen2024 回归, Park2023 时间趋势, Bentley2023 加权指数），证明框架可以评估精确数值复现
2. **DATA-SUB 路径已验证** — 使用 SciSciNet 替代 WoS 复现 Wu2019，方向一致性得到确认
3. **METHOD 路径已验证** — Zhao2025 分类法复现证明框架支持无数值目标的方法理解型任务
4. **错误源定位能力得到证明** — R003 精确定位到公式子组件 bug（行 233-236），而非数据或预处理错误，证明框架的诊断价值
5. **SciSciNet 数据一致性确认** — R002/R004/R007 三篇均使用 N=469,855 完全一致，数据 pipeline 稳定
6. **M1 框架验证通过** — 维度相关性、失败模式多样性、spurious 检测均达到 Go 标准
7. **M2-M7 尚未开始** — 组件基准、信息条件实验、错误分类、多模型比较均待执行

---

## 四、存档实验（retracted-paper-detection）

**6 阶段实验已完成并归档**（位于 `/mnt/mydisk/PycharmProjects/retracted-paper-detection/`）:

| Phase | 内容 | 关键结果 |
|-------|------|---------|
| Phase 1 | 语义相似度基线 | LR AUC **0.854**（Jina 摘要向量 → kNN/centroid） |
| Phase 2 | 鲁棒性验证 | GroupKFold by journal AUC 0.853（−0.001），非期刊记忆 |
| Phase 3 | 语义增强论证图 | 图相似度 AUC 0.5418 → **0.7089**（+0.21），达预设目标 |
| Phase 4-6 | 图相似度消融、Toulmin 提取试点 | 详见 research-wiki/log.md |

**关键发现**: 撤稿论文与正常论文的区分信号来自写作模板和修辞模式（非期刊记忆、非实体聚类）。

---

## 五、待执行的高优先级任务

### 线 A (SciSciBench)

| 优先级 | 任务 | 阻塞因素 |
|--------|------|---------|
| 🔴 P0 | Gold annotation 人类专家验证（~30 papers） | 需要 2-3 名领域专家 |
| 🔴 P0 | 多模型比较（GPT-4o, Claude, DeepSeek） | 需要 API 访问 |
| 🟡 P1 | L2 构念效度验证（规则基线+人类评分） | 依赖 P0 |
| 🟡 P1 | L1/L3 任务重设计 | 当前不区分模型能力 |
| 🟢 P2 | 跨运行稳定性（3+ 次独立运行） | 计算资源 |

### 线 B (Reproduction Framework)

| 优先级 | 任务 | 状态 |
|--------|------|------|
| 🔴 P0 | M2 组件基准（60 组件评估） | TODO (R012) |
| 🔴 P0 | M3 Spurious 检测（4 类型自动规则+人工审查） | TODO (R013-R014) |
| 🟡 P1 | M4 信息条件实验（C1/C2/C3, 30 runs） | TODO (R015-R017) |
| 🟡 P1 | M5 错误分类（E1-E9, 2 标注者） | TODO (R018) |
| 🟢 P2 | M6 多模型比较（4 models） | TODO (R019-R022) |
| 🟢 P2 | M7 污染审计（Full vs Blind+Obfuscated） | TODO (R023-R025) |

---

## 六、整体项目状态判断

### 已建立的

1. **理论框架完整** — 5 维度 × 6 组件的评估矩阵 + 4 种任务类型 + L0-L5 成熟度等级，是当前文献中最细粒度的论文复现质量框架
2. **SciSciBench 基准可运行** — 118 papers, 575 tasks, 工程基础设施完整（并发评估、回归测试、baselines）
3. **STRICT/DATA-SUB/METHOD 三条复现路径全部验证通过** — 6 篇论文成功复现到 L3 等级
4. **错误诊断能力已证明** — 框架可以区分数据错误、公式错误、模型错误（R003）
5. **L3 评分协议已修订** — 消除 ceiling effect，引入分级评分和方向校准矩阵

### 未建立的（核心风险）

1. **Gold annotation 未经人类验证** — 这是两条线共同的致命弱点
2. **仅评估了单一/少数模型** — Qwen3-32B + DeepSeek + Gemma，缺少 GPT-4o/Claude 等强基线
3. **样本量小** — 线 B 仅 6 篇 M0 论文 + 10 篇 M1 论文，统计说服力有限
4. **L1/L3 不区分模型能力** — SciSciBench 仅 L2 有信号
5. **L2 可能测量提取而非推理** — 构念效度未验证

### 最可行的近期发表路径

**Workshop 论文（2-3 个月）**: 以 L2 为中心，L1/L3 作为负面发现，人类专家验证 30 papers，增加 3+ 模型比较，增加规则提取基线。诚实呈现基准开发的挑战和当前局限。
