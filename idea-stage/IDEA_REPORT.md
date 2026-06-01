# Research Idea Report

**Direction**: 撤稿论文检测 — 基于论证图（Argumentation Graph）拓扑指标的撤稿论文识别
**Target Venue**: IPM (Information Processing & Management)
**Date**: 2026-05-27
**Pipeline**: research-lit → idea-creator → novelty-check → research-review
**Novelty Score**: 6/10 (4-5/10 ML method, 7/10 application)
**Reviewer Score**: 6.5/10 → 8/10 (with fixes)
**Recommendation**: PROCEED WITH CAUTION

## Executive Summary

提出一个全新的撤稿论文检测范式：**从论文全文内容层面提取论证结构图（argumentation graph），设计一组可解释的图论拓扑指标来区分撤稿论文和正常论文**。核心洞察是：撤稿/造假论文不仅在引用模式上有异常，其内在的论证逻辑结构本身也存在可量化的缺陷——如论点缺乏证据支撑、论证链断裂、论证孤岛等。目前零篇论文探索此交叉方向（论证图拓扑 + 撤稿检测），是最直接的差异化贡献窗口。

推荐核心指标组合：**Support Debt Index + Graph Coherence Score + Field-Normalized Argument Deviation**，构成一个多维度的"论文论证完整性评分"（Argumentation Integrity Score, AIS）。

## Literature Landscape

### 1. 论证挖掘（Argumentation Mining）—— 技术可及
- **Ruosch et al. (2024/2025, COMMA/TGDK)**: 提出"科学论证网络（Argument Web of Science）"愿景，构建 Sci-Arg 语料库（~836篇论文），开发 MIDAS 跨文档论证关系挖掘系统。
- **Lenz et al. (2020, COMMA)**: 端到端论证挖掘流水线（分段→ADU分类→组件识别→关系预测→图构建）。
- **GraphEval (ICLR 2025)**: 用 Mistral-7B 从论文中提取观点图（viewpoint graph），但仅用于 idea 评估，不涉及撤稿检测。
- **LLM-based 论证分类 (arXiv:2507.08621)**: GPT-4o 在 claim/premise 分类上达到 68-89% 准确率，论证图提取技术已成熟。

### 2. 论证质量与科学欺诈 —— 最近但不同
- **Freedman & Toni (ArgMining 2024, ACL)**: **最直接的竞争工作**。使用论证挖掘+论证质量评估检测科学欺诈，在撤稿论文摘要上取得显著优于基线的效果。但局限明显：(a) 仅使用**摘要**（非全文），(b) 使用论证**质量评估**特征而非图**拓扑**指标，(c) 未构建完整论证图结构，(d) 未提出可解释的图论指标。我们的工作在四个维度上与其差异化。

### 3. 写作风格与欺诈 —— 内容层面但非图结构
- **Braud & Søgaard (2017, arXiv:1707.04095)**: 发现 253 篇撤稿论文与正常论文在模糊限制语（hedging）、逻辑连接词（"therefore" vs "since"）上存在差异。但使用浅层语言学特征而非图结构。

### 4. 文献计量图与撤稿 —— 不同图类型
- **Sharma et al. (2024, arXiv:2411.17447)**: 合作者网络图指标（度中心性 p=0.0024，特征向量中心性 p=0.0018，同配性 p=0.0016）在撤稿与正常作者间差异显著。但分析的是**作者网络**且仅 N=30，非论证图。
- **Zhang et al. (2025, JDIS)**: PDCN 模型用异质引文网络检测论文工厂（F1=81.85%），但用的是**引文图**而非论证内容图。
- **Avros et al. (2023-2024)**: 引文图扰动异常检测（Node2Vec → Graph Transformers），仅关注引文操作，非内容论证。

### 5. 撤稿数据库
- Retraction Watch Database: ~50,000+ 撤稿论文（含撤稿原因分类）
- OpenAlex / PubMed / Scopus: 匹配正常论文

## 核心研究空白

| 维度 | Freedman & Toni (2024) | 我们的工作 |
|------|----------------------|-----------|
| 文本范围 | 摘要（~200词） | **全文**（含引言、方法、结果、讨论） |
| 分析方法 | 论证质量评估 | **图拓扑指标**（可解释的图论度量） |
| 输出 | 分类结果 | **可解释指标 + 分类** |
| 图结构 | 未构建完整论证图 | **节点-边结构图**（claim/premise/evidence + support/attack） |
| 指标可解释性 | 特征重要性（如有） | **图论意义明确**（如出度=被支撑程度） |
| 领域归一化 | 未涉及 | **期刊/领域/年份 Z-score 归一化** |

## Ranked Ideas

### 🏆 Tier 1 — RECOMMENDED for IPM Paper

#### Idea 1: Support Debt Index (SDI) — 论证支撑债务指数
- **Hypothesis**: 撤稿/造假论文存在更多的"论点债务"：核心结论缺乏直接或多跳证据支撑。正常论文的论证图呈现"证据→前提→子结论→主结论"的层状结构，而问题论文的结论节点直接暴露，缺少支撑路径。
- **Graph Metric**: SDI = (无入边的声明节点数) / (总声明节点数)；加权版 = 加权平均声明到证据的最短路径长度
- **Minimum Experiment**: 从200篇撤稿+200篇匹配正常论文提取论证图，计算 SDI，t-test 比较
- **Contribution Type**: Empirical finding + diagnostic
- **Risk**: LOW — 即使负结果也有意义（证明论证拓扑不提供信号）
- **Effort**: 2-3 weeks
- **Reviewer Objection**: "Freedman & Toni 已经做了论证质量，SDI 是否只是老特征的新名字？" → 反驳：他们用摘要的浅层质量特征，SDI 是全文本的图拓扑深度指标，本质不同

#### Idea 2: Graph Coherence Score (GCS) — 论证图跨章节连贯性
- **Hypothesis**: 拼凑/论文工厂论文的论证图可能在不同 IMRaD 章节之间存在"断裂"——引言提出的假设在方法/结果段缺失支撑，讨论中的声明与结果段证据脱节。正常论文的论证图跨章节连接紧密。
- **Graph Metric**: GCS = 跨章节支持边密度 / 图模块度（modularity）；弱连通分量数；结论节点到方法/结果章节证据的可达性
- **Minimum Experiment**: 构建章节感知论证图（节点标注 IMRaD 章节），计算跨章节边比例和模块度，比较撤稿 vs 正常
- **Contribution Type**: Empirical finding
- **Risk**: LOW
- **Effort**: 2-3 weeks

#### Idea 3: Field-Normalized Argument Deviation (FNAD) — 领域归一化论证偏差
- **Hypothesis**: 撤稿信号不是绝对的论证拓扑值，而是**偏离同领域/同期刊/同年份正常论文的异常程度**。生物医学试验、材料科学、计算机科学的正常论证图结构本就不同，需要领域归一化。
- **Graph Metric**: 对每个撤稿论文，匹配 5-10 篇同时期间期刊同主题正常论文，对每个图指标计算 Z-score。FNAD = 多维 Z-score 的加权组合
- **Minimum Experiment**: 选 3 个领域（如生物医学、计算机科学、社会科学），每个领域 50 撤稿+250 正常，验证 Z-score 是否在撤稿论文中系统性偏高
- **Contribution Type**: New method + IPM-friendly scientometric diagnostic
- **Risk**: LOW
- **Effort**: 2-3 months（主要是数据匹配工作）
- **Reviewer Objection**: "匹配论文的质量取决于检索策略" → 已有成熟方法（Coarsened Exact Matching, propensity score matching）

### 🥈 Tier 2 — STRONG CANDIDATES

#### Idea 4: Evidence Concentration Index (ECI) — 证据瓶颈集中度
- **Hypothesis**: 造假论文的论证结构脆弱：少量证据（一张表、一个实验）支撑了异常大量的声明。ECI 通过基尼系数和最大证据节点介数捕捉这种"单点故障"模式
- **Graph Metric**: ECI = 声明节点对证据节点的支撑基尼系数；max_betweenness(evidence_nodes)
- **Contribution**: New method + diagnostic
- **Risk**: MEDIUM — 需要精确将证据节点链接到表格/图表/实验
- **Effort**: Weeks to months

#### Idea 5: Limitation Integration Score (LIS) — 局限性整合度
- **Hypothesis**: 正常论文将局限性有机整合进论证结构（通过 refinement/qualification 边），而造假论文要么没有局限性讨论，要么局限性作为孤立段落存在，与主论证图无连接
- **Graph Metric**: LIS = 局限性节点的度中心性 / 总节点平均度中心性；局限性-声明 refinement 边密度；孤立局限性率
- **Contribution**: Empirical finding + diagnostic
- **Risk**: LOW
- **Effort**: Weeks

#### Idea 6: Inferential Leap Length (ILL) — 推理跳跃距离
- **Hypothesis**: 问题论文可能跳过中间推理步骤，从弱/局部前提出发直接到达宏大结论。ILL 衡量从证据到结论的最短支撑路径长度，以及路径中缺失的中间前提率
- **Graph Metric**: ILL = 顶层结论节点到证据节点的平均最短路径长度；路径中 missing intermediate premise 比率
- **Contribution**: New interpretable method
- **Risk**: MEDIUM
- **Effort**: Weeks

#### Idea 7: Claim-Evidence Strength Mismatch (CESM) — 声明-证据强度不匹配
- **Hypothesis**: 撤稿论文倾向于夸大结论：强因果/普遍性声明仅由弱观察/相关性证据支撑
- **Graph Metric**: CESM = 不匹配率（因果声明+观察证据 / 普遍声明+单一条件实验 / 等）
- **Contribution**: New method + empirical finding
- **Risk**: MEDIUM — 需要细粒度的声明强度和证据类型分类
- **Effort**: Months

#### Idea 8: Argument Extraction Stability (AES) — 论证提取稳定性
- **Hypothesis**: 论证模糊的论文在不同 LLM/prompt 下提取出的论证图不一致——这种提取不稳定性本身就是一个检测信号
- **Graph Metric**: AES = 多 prompt/LLM 提取的节点/边一致性（Jaccard）；图指标的方差
- **Contribution**: Diagnostic + robustness method
- **Risk**: MEDIUM — 需要多次 LLM 调用，成本较高
- **Effort**: Weeks

#### Idea 9: Retraction-Reason Topology Map (RRTM) — 撤稿原因拓扑图谱
- **Hypothesis**: 不同撤稿原因（数据造假、抄袭、图片操纵、伦理问题、诚实错误）应有不同的论证图拓扑特征
- **Graph Metric**: 分组比较各撤稿原因类别下的图指标分布差异
- **Contribution**: Empirical finding — 首次系统揭示撤稿原因的论证拓扑差异
- **Risk**: MEDIUM — Retraction Watch 的撤稿原因标签有噪声
- **Effort**: Months

### ❌ Tier 3 — ELIMINATED

| Idea | Reason Eliminated |
|------|-------------------|
| Attack-Resolution Balance | HIGH risk. 科学论文中很少显式 attack 自己的论证，attack 边提取极为困难。论文间 attack 更适合，论文内几乎不存在 |
| Citation-as-Premise Misuse Metric | HIGH risk. 需要获取并分析所有引用论文的全文以验证引文-声明对齐，对于数百篇论文规模不可行 |
| Pre-Retraction Early-Warning Score | 不是独立指标，而是评估框架。已整合为 Tier 1 指标的评估设置（时序训练/测试划分） |

## 推荐的 IPM 论文框架

### 论文标题（建议）
*"Argumentation Graph Topology Metrics for Detecting Retracted Papers: A Content-Level Approach"*

### 核心贡献
1. **首次**将论证图拓扑分析引入撤稿论文检测
2. 提出一组**可解释的图论指标**（非黑盒 GNN），每个指标有明确的论证结构含义
3. 在 Retraction Watch + 匹配样本上验证指标的有效性
4. 构建**领域归一化**框架，使指标跨学科可比
5. 为学术出版审稿系统提供可操作的**预警工具**

### 方法框架
```
原始论文全文 (PDF/XML)
    ↓
[LLM提取] 论证图 G = (V, E)
    V = {claim, premise, evidence, limitation}
    E = {support, attack, refinement}
    ↓
[图指标计算]
    SDI: 无支撑声明比例
    GCS: 跨章节图连贯性
    ECI: 证据集中度
    LIS: 局限性整合度
    ↓
[领域归一化] Z-score against matched controls
    ↓
[可解释分类] Logistic Regression / XGBoost + SHAP
    ↓
输出: 论文论证完整性评分 (AIS)
```

### 实验设计
1. **数据**: Retraction Watch 中选取 3 个主要撤稿领域（生物医学、CS、社科），每领域 200 撤稿论文 + 1000 正常论文（CEM 匹配期刊/年份）
2. **论证图提取**: GPT-4o 按 IMRaD 章节提取（prompt engineering + few-shot）
3. **人工验证**: 抽取 100 篇论文进行双人标注，评估 LLM 提取的论证图质量
4. **指标有效性**: t-test / Mann-Whitney U 检验每个指标的区分能力
5. **分类性能**: Logistic Regression + SHAP 解释各指标贡献
6. **消融实验**: (a) 仅摘要 vs 全文，(b) 单指标 vs 组合，(c) 有/无领域归一化
7. **鲁棒性**: 不同 LLM (GPT-4o, DeepSeek, Claude) 提取一致性

### 投稿策略
- **IPM** 适合此工作：重视文献计量学分析 + 可操作的信息科学技术 + 实证研究
- IPM 近期发表过 Bibliometric/Scientometric 论文（如 bibliometric retrospective of IPM itself）
- 差异化卖点：从引文层面（传统文献计量）深入到内容层面（论证结构计量），代表了信息处理的"深层"分析

## Suggested Execution Order
1. **Phase 1 (2 weeks)**: 实现 LLM 论证图提取流水线，在小样本上人工验证质量
2. **Phase 2 (2 weeks)**: 数据集构建（Retraction Watch + 匹配 + 全文获取）
3. **Phase 3 (2 weeks)**: 大规模提取论证图，计算所有指标
4. **Phase 4 (2 weeks)**: 统计分析与分类实验
5. **Phase 5 (2 weeks)**: 写论文 + 消融实验

总计：~10 周可完成初稿

---

## Novelty Check Results (Phase 3)

### Overall Assessment: PROCEED WITH CAUTION (6/10)

**Cross-Model Verdict (GPT-5.5, xhigh):** The exact combination — full-text intra-paper argumentation graph topology for retraction detection — is novel. But novelty is combinatorial, not foundational.

### Additional Prior Work Discovered

| Paper | Venue | Year | Relevance | Overlap |
|-------|-------|------|-----------|---------|
| **CLAIM-BENCH** (Javaji et al.) | IJCNLP-AACL | 2025 | Full-paper claim→evidence reasoning benchmark with LLMs | Benchmark only; no retraction, no graph topology |
| **Causal Claims in Economics** (Garg & Fetzer) | arXiv:2501.06873 | 2025 | LLM-extracted evidence-annotated claim graphs from 44K economics papers | Methodology reference; no retraction detection, no integrity metrics |
| **MISSCI** (ACL) | ACL | 2024 | Scientific misinformation detection | Different task (misinformation claims, not retracted papers) |

### Core Claims — Novelty Assessment

| Claim | Novelty | Closest Work |
|-------|---------|-------------|
| LLM extraction of full-text argumentation graphs | MEDIUM | CLAIM-BENCH, Causal Claims in Economics, GraphEval |
| Graph topology metrics (SDI, GCS, ECI, LIS) for argument quality | MEDIUM-HIGH | Freedman & Toni (different metrics, no graph) |
| Field-normalized argument deviation for retraction detection | HIGH | No prior work |
| Overall pipeline: argument graph → topology → retraction classification | HIGH | Zero overlap found |

### Key Differentiator

> "Within-paper, full-text argumentative support topology as a field-normalized integrity signal for retraction detection."

This is the defensible contribution. Not argument mining, not LLM graph extraction, not graph metrics in isolation — the specific combination applied to retraction detection.

---

## External Critical Review (Phase 4)

### Reviewer: GPT-5.5 xhigh (simulated NeurIPS/ICML reviewer for IPM)

**Score: 6.5/10 → 8/10 (with fixes)**

### Strongest Rejection Risk

> "The proposed graph metrics are not convincingly shown to measure real argumentation quality rather than artifacts of LLM extraction, document structure, field genre, or retraction-label confounding."

Without human-validated argumentation graphs, the paper risks becoming "GPT-4o produced graphs, then we computed metrics that classify labels" — weak for IPM.

### Most Likely Failure Modes

1. **Label leakage from post-retraction artifacts**: PDFs may contain "RETRACTED" watermarks, publisher warnings, CrossMark status, retraction notices, or editorial notes
2. **Retraction-reason heterogeneity**: Image manipulation, plagiarism, authorship disputes, ethics issues, and fabricated data likely have different argument topologies — lumping them together washes out the signal
3. **Document length confound**: Graph metrics will scale with paper length/sections — must normalize
4. **Unretracted fraud in control group**: "Normal" controls may include uncaught fraudulent papers

### Minimum Fixes Required

#### 1. Human Validation of Extracted Graphs (MANDATORY)
- Create a gold set of 60-100 papers/sections manually annotated for claims, evidence links, limitations, unsupported claims
- Report node/edge agreement (Cohen's κ) and metric reliability
- Without this, reviewers will dismiss the entire pipeline

#### 2. Retraction-Reason Stratification (MANDATORY)
Separate analysis for:
- Data fabrication/falsification (strongest signal expected)
- Image manipulation
- Plagiarism/duplication
- Ethics/IRB issues
- Authorship/peer-review manipulation
- Honest error

Hypothesis should be strongest for fabrication and paper-mill cases.

#### 3. Leakage-Proof Evaluation (MANDATORY)
- Strip all post-retraction artifacts from PDFs (watermarks, notices, CrossMark)
- Use temporal splits: train on papers retracted before year T, test on papers published before T but retracted after T
- Include matched controls with long unretracted observation windows

#### 4. Document Structure Controls (IMPORTANT)
- All graph metrics normalized by document length, section count, figure/table count
- Include length-matched baselines

### IPM-Specific Strategy

**Reposition from "fraud detector" to "scholarly integrity measurement study":**

For IPM, classification accuracy alone is not the contribution. The paper should answer:

> "Do retracted papers exhibit systematically different internal argumentative organization, after controlling for field, journal, year, length, article type, and retraction reason?"

This is a measurement/characterization contribution — much more IPM-aligned than a detector system.

### Why IPM is the Right Venue

- IPM values: scholarly communication studies, retraction analysis, interpretable diagnostics
- Recent IPM papers include bibliometric/scientometric analyses
- The metrics are explainable and potentially useful for editorial screening
- Field-normalized integrity indicators fit IPM better than black-box classification
- Recent publication: "Half a Century of IPM: A Bibliometric Retrospective" confirms the journal's appetite for scholarly communication research

---

---

## Zotero Integration: Key Papers from Your Library

Your Zotero library contains critical papers that reshape the positioning and strengthen the idea significantly.

### Directly Competing/Complementary Papers (paper mill detection, 7 items)

| # | Paper | Venue | Year | Method | Our Differentiation |
|---|-------|-------|------|--------|---------------------|
| ⭐1 | **Liu, Wang & Liang** — "Bibliometric feature identification and analysis of retracted papers in biomedicine" | **IPM** | 2025 | Interpretable ML (SHAP) + bibliometric features | **Same journal, same problem!** They use bibliometric features; we use argumentation graph topology. Our work extends theirs from "external indicators" to "internal structure." |
| 2 | **Scancar, Byrne et al.** — "ML screening of paper mill publications in cancer research" | **BMJ** | 2025 | ML classifier on paper metadata and text features | Published in BMJ — validates this is a high-impact area. They use shallow text features; we use deep argument structure. |
| 3 | **Fletcher & Stevenson** — "Predicting retracted research: dataset and ML approaches" | RIPR | 2025 | Dataset + ML baselines for retraction prediction | Dataset reference; their features (author, journal, citation) complement ours (argument structure). |
| 4 | **Usman & Balke** — "Scientific Accountability: Detecting Salient Features of Retracted Articles" | ACM | 2025 | Feature salience detection for retracted articles | Complementary approach — they identify which features matter; we propose new features. |
| 5 | **Mascato Fontaíña et al.** — "Identifying common patterns in journals that retracted papers from paper mills" | RIPR | 2025 | Cross-sectional pattern analysis at journal level | Journal-level analysis; our work is paper-level. |
| 6 | **Parker et al.** — "Paper mill challenges: past, present, and future" | JCE | 2024 | Review/position paper | Background context on paper mill detection challenges. |

### Argument Mining Foundation (argument collection, 20 items)

| # | Paper | Venue | Year | How We Use It |
|---|-------|-------|------|---------------|
| 7 | **Lawrence & Reed** — "Argument Mining: A Survey" | Computational Linguistics | 2020 | Comprehensive survey — defines our extraction pipeline architecture |
| 8 | **Kirschner et al.** — "Linking the Thoughts: Analysis of Argumentation Structures in Scientific Publications" | ACL Workshop | 2015 | Pioneering work on extracting argumentation structures from scientific papers |
| 9 | **Accuosto & Saggion** — "Mining arguments in scientific abstracts with discourse-level embeddings" | Data & Knowledge Engineering | 2021 | Discourse-level embeddings for argument mining in scientific text |
| 10 | **Accuosto & Saggion** — "Discourse-Driven Argument Mining in Scientific Abstracts" | — | — | Discourse-driven approach to argument component identification |
| 11 | **Lauscher et al.** — "An Argument-Annotated Corpus of Scientific Publications" | ACL Workshop | 2018 | Annotation framework for scientific argument graphs |
| 12 | **Stab & Gurevych** — "Parsing Argumentation Structures in Persuasive Essays" | — | 2017 | Foundational argument parsing method, applicable to scientific text |

### Claim Extraction & Verification (Claim collection, 72 items)

| # | Paper | Year | How We Use It |
|---|-------|------|---------------|
| 13 | **Wu et al.** — "Extracting Summary Knowledge Graphs from Long Documents" (arXiv:2009.09162) | 2020 | KG extraction from long documents — direct methodology reference for our LLM extraction pipeline |
| 14 | **Hajishirzi et al. (Wadden, Lo, Wang, Cohan)** — "Fact or Fiction: Verifying Scientific Claims" (EMNLP) | 2020 | Scientific claim verification — SciFact dataset and methodology |
| 15 | **Shardlow et al.** — "Identification of research hypotheses and new knowledge from scientific literature" (BMC) | 2018 | Hypothesis extraction from scientific text — component identification methodology |
| 16 | **Solovyev & Zhiltsov** — "Logical structure analysis of scientific publications in mathematics" | 2011 | Early work on logical structure extraction — validates this research direction |

### Key Integration Insight

**Liu et al. (2025, IPM)** is the anchor paper for positioning. They published in our target journal, on our exact problem (retracted paper detection), using the same philosophy (interpretable ML + SHAP). But they used **bibliometric features** (citation counts, journal IF, author h-index, collaboration metrics).

Our contribution: **extend retraction detection from the bibliometric level to the content structure level**, using argumentation graph topology metrics. This positions us as building on IPM's own published work — a compelling narrative for reviewers.

## Refined Positioning Strategy

### Paper Framing (for IPM)

**Title**: *"From Bibliometrics to Argument Structure: Graph Topology Metrics Reveal Content-Level Differences between Retracted and Non-Retracted Papers"*

**Contribution Type**: Measurement study + diagnostic tool

**Core Narrative for IPM Reviewers**:

Liu et al. (2025, IPM) demonstrated that bibliometric features + interpretable ML can identify retracted papers. We extend this line of work **from the external (bibliometric) level to the internal (argument structure) level**. Just as citation anomalies can signal problems, so can anomalies in how a paper constructs its arguments — unsupported claims, fragmented reasoning chains, evidence bottlenecks.

**Three Defensible Claims** (revised):
1. **Empirical**: Retracted papers exhibit systematically different argumentation graph topology compared to matched controls, even after controlling for bibliometric features (Liu et al. baseline)
2. **Methodological**: LLM-extracted argumentation graphs + interpretable topology metrics provide complementary signal to bibliometric features — combining both improves retraction detection
3. **Practical**: The metrics are field-normalized, LLM-agnostic, and interpretable via SHAP, making them suitable for editorial screening workflows

### Revised Baseline Strategy (incorporating Zotero papers)

| Baseline | Source | What it Tests |
|----------|--------|---------------|
| **Liu et al. (2025) bibliometric features** | Your Zotero / IPM | Does argument topology add signal beyond bibliometrics? |
| **Fletcher & Stevenson (2025) ML baselines** | Your Zotero / RIPR | Does our approach beat standard retraction prediction features? |
| **Freedman & Toni (2024) argument quality** | Your Zotero / ArgMining | Does full-text graph topology beat abstract-level argument quality? |
| **Scancar et al. (2025) paper mill classifier** | Your Zotero / BMJ | Does our approach generalize beyond cancer research? |
| **Full-text LLM classifier (no graph)** | New | Does the graph structure add value beyond raw LLM judgment? |
| **Abstract-only graph metrics** | Ablation | Is full text necessary, or do abstracts suffice? |

### Updated Execution Plan

| Phase | Task | Duration | Key Deliverable |
|-------|------|----------|-----------------|
| **0** | Reproduce Liu et al. (2025) bibliometric baseline on our dataset | 1 week | Baseline AUC; feature importance comparison |
| **1** | Human validation gold set (60 papers, dual annotation) | 2 weeks | Inter-annotator agreement; extraction reliability |
| **2** | LLM argumentation graph extraction prototype | 1 week | Prompt-tuned extraction pipeline; pilot on 20 papers |
| **3** | Dataset: Retraction Watch + CEM matching + PDF acquisition + artifact stripping | 3 weeks | Matched dataset with retraction-reason labels |
| **4** | Large-scale extraction + metrics computation | 2 weeks | Multi-LLM comparison (GPT-4o, DeepSeek, Claude) |
| **5** | Statistical analysis + retraction-reason stratification | 2 weeks | Per-reason effect sizes; field-normalized Z-scores |
| **6** | Classification + SHAP + baseline comparison (Liu et al. features + ours) | 1 week | Ablation: bibliometric only vs combined vs argument only |
| **7** | Writing (positioned as IPM extension of Liu et al.) | 2 weeks | Manuscript draft |

**Total: ~14 weeks**

## Next Steps
- [ ] **Priority 1**: Read and reproduce Liu et al. (2025, IPM) bibliometric baseline
  - Understand their exact feature set and SHAP methodology
  - This is the anchor paper for positioning our work as its natural extension
- [ ] **Priority 2**: Build human validation gold set (60 papers, claim-evidence annotation)
  - Use Lauscher et al. and Kirschner et al. annotation frameworks from your Zotero
  - Gating item — if argumentation graphs can't be reliably extracted, pivot
- [ ] **Priority 3**: Acquire Retraction Watch data + match controls
- [ ] **Priority 4**: Pilot extraction on 20 papers → verify hypothesis before scaling
- [ ] If pilot positive → /auto-review-loop for full iteration
- [ ] Or invoke /research-pipeline for the complete end-to-end flow

## Zotero Papers to Read Immediately (for positioning)

| Priority | Paper (from your Zotero) | Why |
|----------|--------------------------|-----|
| 🔴 | Liu, Wang & Liang (2025, IPM) | Anchor paper — same journal, same problem, same philosophy |
| 🔴 | Fletcher & Stevenson (2025, RIPR) | Dataset + ML baselines for retraction prediction |
| 🔴 | Scancar, Byrne et al. (2025, BMJ) | State-of-the-art paper mill ML screening |
| 🟡 | Usman & Balke (2025, ACM) | Salient features of retracted articles |
| 🟡 | Lawrence & Reed (2020, CL) | Argument mining survey — methodology foundation |
| 🟡 | Accuosto & Saggion (2021, DKE) | Discourse embeddings for scientific argument mining |
| 🟢 | Kirschner et al. (2015) | Scientific argumentation structure analysis |
| 🟢 | Lauscher et al. (2018) | Argument-annotated corpus of scientific publications |
| 🟢 | Wu et al. (2020) | KG extraction from long documents — LLM extraction methodology |
