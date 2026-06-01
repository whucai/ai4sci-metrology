# AI for Science 计量学范式：三步走研究路线图

**Date**: 2026-06-01
**导师方向**: AI for Science 的计量学范式研究
**核心对标**: 王大顺 (Dashun Wang) Science of Science 研究传统
**最新对标**: SciSciGPT (Nature Computational Science 2025)

---

## 导师的核心意图

导师说的"计量学范式"指的是 **Science of Science (SciSci)** 传统——用大规模数据+计算方法来**测量**科学本身的运行规律。Wu, Wang & Evans (Nature 2019) 用引文图测量"颠覆性"是这个范式的代表作。

现在这个范式进入了 AI Agent 时代。王大顺团队 2025 年 12 月在 **Nature Computational Science** 发表了 **SciSciGPT**——一个五智能体协作系统，能自动复现已发表论文的发现，完成任务时间仅为研究人员的 ~10%。

**导师要你做的，是站在这个范式的前沿。**

---

## 三步走研究框架

### Step 1: 自动论文复现环境（AI Reproducibility Metrology）

**核心问题**: 能不能造一个"计量仪器"——让 AI 自动读论文、自动复现分析、自动判断结论是否可复现？

```
论文PDF → [AI Agent 读取] → 提取实验方案
                ↓
         定位数据集/代码
                ↓
         自动执行分析流水线
                ↓
         对比论文结论 vs 复现结果
                ↓
         输出: 可复现性评估报告
```

**对标工作**:
| 系统 | 机构 | 核心能力 | 局限 |
|------|------|---------|------|
| SciReplicate-Bench | 多机构 | 100 个 NLP 任务复现 | 仅 39% 执行准确率 |
| Paper2Code | KAIST | 77% 生成的代码被评为最优 | 仅限 ML 论文 |
| AutoReproduce | — | 引入"论文谱系"追溯隐性知识 | 依赖引用链 |
| SciSciGPT | 西北大学 | 5 智能体协作，~10% 人类耗时 | 聚焦 SciSci 领域 |
| AI Scientist | Sakana AI | 端到端研究循环 | 42% 实验失败率 |

**核心瓶颈不是代码生成，是环境地狱**

SciReplicate-Bench 只有 39% 执行准确率，根因不是 LLM 读不懂论文，而是：
- PyTorch 版本不对、CUDA 版本冲突
- 冷门 R 包缺失、系统库不兼容
- 数据路径硬编码、Python 2 vs 3 问题

**我们的技术差异点**: 引入 **容器化自动构建 + Self-Correction 循环**

```
提取实验方案 → 动态生成 Dockerfile/Apptainer
                    ↓
              沙箱中执行分析代码
                    ↓
          [失败] → Agent 读取报错信息
                    ↓
          自动修复: 补依赖/换版本/改路径
                    ↓
          [重试] → 直到成功或判定不可复现
```

**系统架构（四模块 + 环境层）**:
1. 论文理解模块（结构化提取方法、数据、分析步骤）
2. 环境构建模块（动态生成容器 + Self-Correction 修复循环）← **技术壁垒**
3. 分析复现模块（沙箱执行 + 结果比对）
4. 可复现性报告模块（自动生成评估报告，标注每个步骤的复现状态）

**为什么这是"计量学"**: 这个环境本质上是一台**可复现性测量仪器**。关键创新在于它不仅测量"结论是否可复现"，还测量"环境构建需要多少次修复迭代"——后者本身就是一个计量指标（Reproducibility Effort Index, REI）。

**产出**: 一篇方法论论文 + 开源系统 + 在小规模论文集合上的验证

---

### Step 2: 人机协作实验设计（AI-Assisted Experiment Design）

**核心问题**: 能不能让 AI 根据研究想法 + 现有数据，自动提出实验方案？

```
人类提出研究想法 → [AI Agent]
                      ├── 搜索可用数据集
                      ├── 分析数据适用性
                      ├── 设计实验方案（假设→方法→预期结果）
                      ├── 规划分析步骤
                      └── 生成可执行的分析代码
                            ↓
                      实验方案文档 + 代码骨架
```

**对标工作**:
| 系统 | 特点 |
|------|------|
| MLR-Copilot | Idea→Experiment→Code，50% 成功率 |
| AgentExpt | 检索 baseline+数据集，生成实验计划 |
| AutoDS (Ai2) | Bayesian surprise 驱动，67% 假设让 PhD 感到意外 |
| PerTurboAgent | 迭代实验设计 + 主动学习循环 |

**核心瓶颈: SciSci 数据集的"大"与"杂"**

OpenAlex、PubMed、ORCID 等 SciSci 标准数据集体量极其庞大（数百 GB 的图或关系表）。让 Agent 直接写 Python 处理这么大的数据，极易：
- 内存溢出 (OOM)
- 上下文窗口超限（一张表几亿行，LLM 根本看不到）
- 执行效率极低

**我们的解决方案: 科学计量 SDK 抽象层**

```
Agent 不写底层代码，而是调用高层 SDK:

  Agent: "计算这篇论文的颠覆性指数 D"
    ↓ 不生成 pd.read_csv + groupby + merge 的几百行代码
    ↓ 而是调用
  SDK: sci.disruption_index(paper_doi)
    ↓ SDK 内部处理:
    ├── 图数据库查询引用网络 (Neo4j/NetworkX)
    ├── 分布式计算 (Spark/Dask 分片)
    ├── 内存管理 (流式处理，避免 OOM)
    └── 返回标量结果 + 置信区间

  Agent: "匹配撤稿论文与正常论文，按期刊+年份 CEM"
    ↓ 调用
  SDK: sci.cem_match(retracted_dois, control_pool, on=['journal','year'])
```

**Agent 的角色转变**: 从"疯狂写底层代码的码农" → **"调用专业工具的科学家"**

SDK 封装的高阶操作：
| SDK 函数 | 底层处理 |
|---------|---------|
| `sci.disruption_index(doi)` | 图数据库查询 + 三元组计数 |
| `sci.cem_match(ids, pool, on)` | 分布式 CEM 匹配 |
| `sci.citation_cascade(doi, depth)` | 引文级联分析（多跳遍历） |
| `sci.coauthor_network(author_id)` | 子图提取 + 中心性计算 |
| `sci.field_normalize(metric, field, year)` | 领域×年份 Z-score 标准化 |
| `sci.survival_analysis(papers, event)` | 生存分析（引用半衰期等） |

**产出**: SciSci SDK + AI 实验设计助手（Agent 通过 SDK 操作数据，而非裸写代码）

---

### Step 3: AI for Science 研究范式转变（Vision Paper）

**核心叙事: 从"相关性计量"到"因果性复现"**

传统的科学计量学（Wu, Wang & Evans 2019）本质上测量的是**"科学留下的痕迹"**——引文网络、合著者图谱。这些都是**事后相关性统计**：论文发表后，引用模式揭示了什么。

用 AI Agent 去复现实验，测量的是**"科学的可运行性与因果链条"**——论文的结论是否可以从其描述的方法和数据中**必然导出**。这不仅测量"论文被如何引用"，而是测量"论文的论证是否成立"。

```
传统计量学（相关性）:
  论文A 引用 论文B → D-index 计算 → "论文B 是否颠覆性"
  测量对象: 科学的社会痕迹
  时间维度: 事后（发表后数年）

AI Agent 计量学（因果性）:
  AI 读取论文A → AI 执行论文A的方法 → AI 比对结论
  测量对象: 科学的内在可运行性
  时间维度: 事前/事中（发表时即可验证）
```

**这是计量学从"事后统计"到"事前/事中验证"的范式跃迁。**

**参考框架**: SciSciGPT 的四层成熟度模型
- L1: 功能能力（单任务执行）
- L2: 工作流编排（多步骤协调）
- L3: 记忆架构（知识积累与复用）
- L4: 人机交互（协作与信任）

**我们的贡献**: 基于 Step 1（复现环境）和 Step 2（实验设计助手）的实际经验，论证：
1. **可复现性从"社会过程"变成了"技术过程"**——不再需要另一个实验室花数月尝试复现，AI Agent 可以在发表时即时验证
2. **科学计量学从"测量痕迹"升级为"测量运行"**——不是看论文被怎么引用，而是看论文能不能跑通
3. **人机协作的最佳边界**——什么该让 AI 自主执行，什么必须人类判断
4. **提出 Reproducibility Effort Index (REI)**——测量复现一篇论文需要多少次环境修复迭代，作为一个新的科学质量指标

**产出**: 一篇 Vision Paper，投 Nature Human Behaviour / PNAS / Science Advances

---

## 与导师给的参考论文的关系

```
Wu, Wang & Evans (Nature 2019)
  └── 用引文图拓扑指标测量科学的"颠覆性"
       └── Science of Science 计量学范式的基础

SciSciGPT (Nature Computational Science 2025)
  └── Wang 团队的最新工作：用 AI Agent 自动做 SciSci 研究
       └── 明确了 "AI + SciSci" 的可行性和发表潜力

你的工作
  └── Step 1: 造一个"可复现性测量仪器"（计量学工具）
  └── Step 2: 让 AI 辅助设计实验（计量学应用）
  └── Step 3: 论述 AI 如何改变科学范式（计量学元思考）
```

---

## 为什么这个方向更好

| 对比维度 | 旧方向（撤稿检测） | 新方向（AI for Sci 计量学） |
|---------|------------------|--------------------------|
| 定位 | 抓造假者 | 造科学测量工具 |
| 对标 | Freedman & Toni (workshop) | 王大顺 (Nature 系列) |
| 方法 | 论证图拓扑 | AI Agent + 数据分析 |
| 技术含量 | 中等 | 高（AI Agent 是当下最前沿） |
| 可扩展性 | 单一问题 | 平台型，可不断扩展领域 |
| 发表潜力 | IPM/科学计量学期刊 | Nature Computational Science / Nature Human Behaviour |
| 导师认可 | 导师觉得太负面 | 导师主动提出的方向 |

---

## 近期行动计划

### 前两周（黄金测试集构建）
- 手工挑选 5 篇"通关 Baseline"论文：GitHub 标星极高、数据和环境极度规范的 SciSci/数据科学论文
- 标准: README 清晰、有 requirements.txt/environment.yml、数据可公开下载
- 复现 SciSciGPT 的核心工作流代码

### 后两周（跑通闭环）
- 不求 Agent 自动化程度 100%，允许人工介入微调环境
- 重点是跑通"提取-执行-对比-报告"的整体管线 (Pipeline)
- 记录每个步骤的失败模式和修复策略（为 Self-Correction 模块积累经验）

### 第二个月
- 在 5 篇 Baseline 上达到 >80% 的管线成功率
- 引入容器化自动构建（Dockerfile 动态生成）
- 扩展到 10 篇难度递增的论文

### 本学期
- Self-Correction 循环开发（根据报错自动修复环境）
- SciSci SDK 原型设计（disruption_index, cem_match 等核心函数）
- 撰写 Step 1 工作论文初稿
