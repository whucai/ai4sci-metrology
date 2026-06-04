# Literature Survey: AI Reproducibility & SciSci Metrology

**Direction**: AI Agent 自动论文复现 + Science of Science 计量学
**Date**: 2026-06-01

---

## 1. AI Agent 论文复现系统（直接对标）

| 系统 | 机构 | 核心能力 | 局限 |
|------|------|---------|------|
| **SciSciGPT** | 西北大学 | 5-Agent 协作，~10% 人类耗时 | 聚焦 SciSci 领域 |
| SciReplicate-Bench | 多机构 | 100 NLP 任务复现 | 仅 39% 执行准确率 |
| Paper2Code | KAIST | 77% 代码被评为最优 | 仅限 ML 论文 |
| AutoReproduce | — | 论文谱系追溯隐性知识 | 依赖引用链 |
| AI Scientist | Sakana AI | 端到端研究循环 | 42% 实验失败率 |
| MLR-Copilot | — | Idea→Experiment→Code 全流程 | 50% 成功率 |

## 2. 可复现性评估方法论

### 2.1 NLP/ML 可复现性评估
- **ReproNLP 2025 Shared Task** (Belz et al., ACL/GEM 2025): QRA++ 框架区分四种结果类型（CV*、Pearson/Spearman、Fleiss κ、配对排名比例）
- **Reproducibility Crisis in LLMs for SE** (Siddiq et al., arXiv 2025): 7类可复现性气味分类法，可复现性成熟度模型（RMM）
- **Checklists for Computational Reproducibility** (Momeni et al., ACM 2025): 59项检查清单，三阶段：数据访问、分析、共享与归档

### 2.2 本体论与知识图谱
- **Provenance, Assertion and Evidence Ontologies Survey** (Chhetri et al., WWW 2025): 综述23种本体论，使用知识图谱捕捉断言、证据和溯源

---

## 3. Science of Science 计量学（核心对标）

### 3.1 经典工作
- **Wu, Wang & Evans (Nature 2019)**: 用引文图拓扑指标测量科学的"颠覆性"——Science of Science 计量学范式的基础
- **SciSciGPT (Nature Computational Science 2025)**: Wang 团队最新——用 AI Agent 自动做 SciSci 研究，明确了"AI + SciSci"的可行性和发表潜力

### 3.2 科学文献计量
- **OpenAlex**: 最大的开放科学知识图谱（~250M 作品）
- **SciSciNet**: SciSciGPT 配套数据集（~134M 论文，19张表）
- PubMed, ORCID, Dimensions: 标准 SciSci 数据源

---

## 4. 容器化与可复现环境

- **Docker/Apptainer**: 标准容器化工具
- **REPRODUCE-ME** (Sheikh & Cool, 2017): 科学工作流的本体驱动可复现性
- **Code Ocean**: 商业可复现计算平台
- **Binder/MyBinder**: Jupyter Notebook 可复现环境

关键洞察：环境构建是可复现性的最大瓶颈。SciReplicate-Bench 只有 39% 准确率，
根因是 PyTorch/CUDA 版本冲突、冷门包缺失，不是 LLM 读不懂论文。

---

## 5. 自我修复与迭代调试

- **Self-Debugging** (Chen et al., ICLR 2024): LLM 通过解释代码反馈来调试
- **Self-Refine** (Madaan et al., NeurIPS 2023): 迭代自反馈改进 LLM 输出
- **Reflexion** (Shinn et al., NeurIPS 2023): 语言 Agent 通过语言反馈学习
- **SWE-Agent** (Yang et al., 2024): 自主软件工程 Agent，从报错中修复代码

---

## 6. 论证挖掘与科学声明验证（辅助技术）

### 6.1 科学论证语料库
- **Sci-Arg / Argument Web of Science** (Ruosch et al., 2024/2025): 构建跨文档科学论证网络
- **GraphEval** (ICLR 2025): 用 LLM 从论文中提取观点图

### 6.2 图结构声明验证
- **GraphFC** (Huang et al., 2025): 声明转 ⟨subject, relation, object⟩ 有向图，SOTA on HOVER/FEVEROUS/SciFact
- **GraphCheck** (Jeon & Lee, EMNLP 2025): 实体-关系图多路径事实验证
- **EVOCA** (De Felice et al., 2025): AMR 子图对齐声明-证据对

---

## 7. 核心研究空白

| 维度 | 现有工作 | 我们的机会 |
|------|---------|-----------|
| 复现范围 | 单一论文/领域 | **通用可复现性测量仪器** |
| 评价方式 | 二元（成功/失败） | **连续 REI 评分** |
| 环境构建 | 手动 Docker/预配置 | **动态生成 + Self-Correction** |
| 知识提取 | 人类读论文 | **Multi-Pass LLM + 交叉引用** |
| 结果比对 | 人工判断 | **4级自动比对框架** |
