# Literature Survey: Argumentation Graph for Scientific Reproducibility Evaluation

**Direction**: 论证图视角的自动科研可复现性评价
**Date**: 2026-06-01
**Previous Direction**: 论证图拓扑指标的撤稿论文检测

---

## 1. 关键参考案例：王平 Nature 论文事件

- **论文**: "Human HDAC6 senses valine abundancy to regulate DNA damage", Nature 637, 215-223 (2025)
- **通讯作者**: 王平（同济大学生命科学与技术学院原院长，长江学者，杰青）
- **事件**: PubPeer 质疑数据存在"非自然规律性"→ 同济大学调查确认第一作者存在学术不端 → 王平被免职
- **核心发现**: 数据异常包括连续35个独立样本差值恰好为0.3%（概率 ~10⁻²³）、末位数字分布异常、不同实验组曲线高度相似
- **启示**: 即使是 Nature 论文，其论证所依赖的数据基础也可能存在系统性问题。如果能从论证结构+数据层面自动评估论文的"可复现风险"，就能在发表前预警

---

## 2. 论证挖掘与论证图构建（技术基础）

### 2.1 科学论证语料库与工具
- **Sci-Arg / Argument Web of Science** (Ruosch et al., 2024/2025, TGDK 3.3.4): 构建跨文档科学论证网络，Sci-Arg 语料库 ~836 篇论文，提出 MIDAS 跨文档论证关系挖掘系统
- **端到端论证挖掘流水线** (Lenz et al., 2020, COMMA): 分段→ADU分类→组件识别→关系预测→图构建
- **oAMF 开放论证挖掘框架** (Ruiz-Dolz et al., 2025): 17个集成模块，统一多种论证挖掘方法，标准化评估
- **ARIES 基准** (Ruiz-Dolz et al., 2024-2025): 论证关系识别的通用基准，覆盖8个数据集

### 2.2 LLM 时代的论证挖掘
- **LLMs in Argument Mining: A Survey** (arXiv:2506.16383, 2025): 综述250篇论文，LLM在claim/premise分类上达68-89%准确率
- **GraphEval** (ICLR 2025): 用 Mistral-7B 从论文中提取观点图（viewpoint graph）
- **Toulmin 模型零样本论证提取** (Gupta et al., ACL 2024): 零样本提取 ⟨claim, reason, warrant⟩ 三元组
- **弱监督科学摘要声明定位** (RATIO 2024): 无需标注数据的声明检测方法

---

## 3. 论证质量评估（直接相关）

### 3.1 论证质量计算评估
- **Computational Argument Quality Assessment Survey** (Ivanova et al., EMNLP 2024): 综述211篇论文、32个数据集，涵盖完整性（completeness）、连贯性（coherence）、说服力（cogency）等维度
- **SPARK** (Deshpande et al., NAACL 2024): 基于上下文知识的论证质量评分，使用LLM生成反馈、隐藏假设、反论证
- **Argument Quality Assessment in the Age of LLMs** (Wachsmuth et al., LREC-COLING 2024): 论证质量评估立场论文

### 3.2 科学欺诈检测（最直接竞争工作）
- **Detecting Scientific Fraud Using Argument Mining** (Freedman & Toni, ArgMining 2024, ACL): **最接近的工作**。使用论证挖掘+论证质量评估检测科学欺诈，在撤稿论文摘要上取得显著效果。但局限：(a) 仅用摘要，(b) 使用论证质量特征而非图拓扑指标，(c) 未构建完整论证图
- **写作风格与撤稿** (Braud & Søgaard, 2017): 撤稿论文在模糊限制语、逻辑连接词使用上存在差异

---

## 4. 科学声明验证与图方法（技术交汇点）

### 4.1 图结构声明验证
- **GraphFC** (Huang et al., 2025): 将声明转为 ⟨subject, relation, object⟩ 有向图，图引导规划+图引导检查，SOTA on HOVER/FEVEROUS/SciFact
- **GraphCheck / DP-GraphCheck** (Jeon & Lee, EMNLP 2025 Findings): 实体-关系图多路径事实验证，策略选择器自适应选择验证深度
- **EVOCA** (De Felice et al., 2025): AMR 子图对齐声明-证据对，生成"子证据"句子
- **SR-MFV** (Zheng et al., 2025): 推理路径作为结构化图信号，GraphFormers 捕捉证据链长程依赖
- **CO-GAT** (IEEE Trans. Big Data, 2025): 置信图注意力网络，节点掩码机制防止噪声传播

### 4.2 科学声明验证基准
- **ClimateViz** (Su et al., EMNLP 2025): 首个大规模科学图表事实验证基准，49,862声明+2,896可视化，含结构化KG解释。最佳模型76-78% vs 人类~90%
- **CHECKWHY** (Si et al., 2024): 19K因果声明-证据-论证结构三元组，论证结构显著改善因果验证
- **SciFact / SciFact-Open**: 科学声明验证标准数据集

### 4.3 形式化论证框架
- **TD-QBAFs** (Potyka & Booth, COMMA 2024): 真值发现量化双极论证框架，发现循环图中收敛失败是常态而非例外——对可复现性有直接影响
- **MArgE** (Ng et al., arXiv 2025): 多LLM证据网格化为论证树，使用QBAF逐步语义进行声明验证
- **不完备容忍的渐进语义** (Rago et al., 2024-2025): 模块化方法论，处理不完全信息下的论证强度评估

---

## 5. 可复现性评估方法论

### 5.1 NLP/ML 可复现性评估
- **ReproNLP 2025 Shared Task** (Belz et al., ACL/GEM 2025): 第六届复现评估共享任务，QRA++ 框架区分四种结果类型（CV*、Pearson/Spearman、Fleiss κ、配对排名比例），首次引入 LLM 理智检查
- **Reproducibility Crisis in LLMs for SE** (Siddiq et al., arXiv 2025): 分析640篇论文，开发7类可复现性气味分类法，提出可复现性成熟度模型（RMM）
- **Checklists for Computational Reproducibility** (Momeni et al., ACM 2025): 59项检查清单，三阶段：数据访问、分析、共享与归档

### 5.2 本体论与知识图谱
- **Provenance, Assertion and Evidence Ontologies Survey** (Chhetri et al., WWW 2025): 综述23种本体论，使用知识图谱捕捉断言、证据和溯源以实现可复现性
- **Reproducibility as a Service (RaaS)** (Hernandez & Colom, Frontiers 2025): 期刊可复现性政策系统性回顾

---

## 6. 核心研究空白（我们的机会）

### 当前状态
```
论证挖掘 ────→ 论证质量评估 ────→ 科学欺诈检测 (Freedman & Toni 2024)
    │                                      ↑ 仅用摘要
    │                                      ↑ 非图拓扑特征
    │                                      ↑ 无完整论证图
    │
    └──→ 科学声明验证 ────→ 图结构验证 (GraphFC, EVOCA, GraphCheck)
    │                                      ↑ 非论文全文
    │                                      ↑ 针对声明而非论文
    │
    └──→ ★ 论文全文论证图 ──→ 拓扑指标 ──→ 可复现性评分 ← 我们的位置
```

### 具体空白

| 维度 | 现有工作 | 我们的机会 |
|------|---------|-----------|
| **文本范围** | 摘要/声明级 | **全文论证图**（含引言、方法、结果、讨论） |
| **分析单元** | 论证质量特征/声明三元组 | **图拓扑指标**（中心性、连通性、层深度等） |
| **评价目标** | 二元分类（欺诈/正常） | **连续可复现性评分**（多维指标体系） |
| **可解释性** | 特征重要性 | **图论意义明确**（如出度=被支撑程度） |
| **应用场景** | 事后检测 | **事前评估**（投稿前/审稿中） |

---

## 7. 推荐的研究方向

### 方向 A: 论证完整性评分（Argumentation Integrity Score, AIS）
- 构建论文全文论证图 → 计算图拓扑指标 → 多维可复现性评分
- 参考 Freedman & Toni (2024) 的评估范式，但升级为全文+图拓扑
- 指标: Support Depth（支撑深度）、Evidence Coverage（证据覆盖率）、Chain Completeness（链条完整性）

### 方向 B: 论证图与数据可复现性交叉验证
- 论证图中声明节点关联到数据/实验 → 检查数据一致性信号
- 参考王平案例：论证结构中的"数据节点"存在统计异常
- 将文本论证结构与统计数据/图表分析结合

### 方向 C: 可复现性风险预警系统
- 基于论证图拓扑指标，建立期刊/会议论文的可复现性风险评分
- 参考 ReproNLP QRA++ 框架 + 论证质量评估
- 应用于投稿预筛查、同行评审辅助

---

## 8. 关键论文列表（按优先级）

1. **Freedman & Toni (2024)** — "Detecting Scientific Fraud Using Argument Mining", ArgMining@ACL — 最直接竞争工作
2. **Ivanova et al. (2024)** — "Quality Dimensions and Annotated Datasets for Computational Argument Quality Assessment", EMNLP — 论证质量评估全景
3. **Ruosch et al. (2025)** — "Mining Inter-Document Argument Structures in Scientific Papers for an Argument Web", TGDK — Sci-Arg语料库
4. **Belz et al. (2025)** — ReproNLP Shared Task, GEM/ACL — QRA++ 可复现性评估框架
5. **Shi et al. (2025)** — "From Text Mining to Intelligent Debate", IP&M — 计算论证综述
6. **GraphFC** (Huang et al., 2025) — 图结构声明验证框架
7. **EVOCA** (De Felice et al., 2025) — AMR图对齐声明验证
8. **Chhetri et al. (2025)** — Provenance/Assertion/Evidence Ontologies Survey, WWW — 溯源本体论
9. **ClimateViz** (Su et al., EMNLP 2025) — 科学图表事实验证基准
10. **TD-QBAFs** (Potyka & Booth, COMMA 2024) — 论证框架收敛性问题
