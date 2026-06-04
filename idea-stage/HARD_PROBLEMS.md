# Three Hard Problems for AI Reproducibility Metrology

**Date**: 2026-06-01

---

## Hard Problem 1: Environment Reproducibility

### Problem

SciReplicate-Bench 只有 39% 执行准确率，根因不是 LLM 读不懂论文，而是环境问题：
- PyTorch 版本不对、CUDA 版本冲突
- 冷门 R 包缺失、系统库不兼容
- 数据路径硬编码、Python 2 vs 3 问题
- SciSciGPT 依赖 GCP (BigQuery, Vertex AI, Cloud Storage) + Pinecone

### Solution: Containerized Auto-Build + Self-Correction

```
Dockerfile 动态生成:
  1. 提取论文中的依赖声明 (requirements.txt, environment.yml, DESCRIPTION)
  2. 生成初始 Dockerfile
  3. docker build → [失败] → Agent 读报错 → 修复 → 重试
  4. 记录修复迭代次数 → 计入 REI

Stage 1: 解析论文 → 识别语言(Python/R/Julia) → 提取包依赖
Stage 2: 生成基础 Dockerfile → 安装依赖
Stage 3: 尝试运行论文代码 → 记录错误
Stage 4: Agent 分析错误 → 补依赖/换版本/改路径 → 重试
         ↑_____________________________________________↓
         Self-Correction Loop (max 10 iterations)
```

---

## Hard Problem 2: Implicit Knowledge Extraction

### Problem

论文中有大量**隐性知识**未显式声明：
- 超参数可能在附录正文中而非代码中
- 数据预处理步骤可能隐含在"standard preprocessing"一句话里
- 评估指标的具体实现可能参考了另一篇论文
- 随机种子、数据划分方式通常不报告

### Solution: Multi-Pass Reading + Cross-Referencing

```
Pass 1 (Fast scan): 识别论文结构 (IMRaD 章节)、图表、表格
Pass 2 (Deep extraction): LLM 逐段提取:
  - Method: 算法、超参数、包依赖
  - Data: 来源、预处理步骤、划分方式
  - Evaluation: 指标、基准、统计检验
Pass 3 (Gap detection): 识别缺失信息
  - "这个超参数在正文中提到了吗？" → 检查附录
  - "数据的 train/test split 说明了吗？" → 标记为隐性知识
  - "评估指标的具体公式给了吗？" → 交叉引用参考文献
Pass 4 (Reference resolution): 解析引用链
  - "standard preprocessing as in [32]" → 读取 [32] 的方法段
```

---

## Hard Problem 3: Result Comparison Fidelity

### Problem

复现结果与论文声称结果如何比较？

挑战：
- 论文可能只报告了最佳结果（cherry-picking）
- 统计检验的选择可能不同（t-test vs Mann-Whitney vs bootstrap）
- 图表数据的精确值需要从图片中数字提取
- "similar to Figure 3" — 图 3 在 5 页之前

### Solution: Multi-Level Comparison Framework

```
Level 1 — 精确数值比较:
  - 论文报告了均值±标准差 → 直接数值比对
  - 误差公式: ε = |reported − reproduced| / |reported|

Level 2 — 统计等价性:
  - 两样本检验: p值方向一致 (both significant in same direction)
  - 效应量: Cohen's d 在同一范围内
  - 等效检验 (TOST): 复现结果是否与声明的等效区间重叠

Level 3 — 图表比较:
  - 从论文图表中提取数值 (digitization)
  - 趋势一致性: Spearman ρ > 0.9
  - 关键点比对: 峰值、拐点、交叉点

Level 4 — 结论一致性:
  - LLM 比较论文的 Discussion 与复现结果
  - "基于复现结果，论文的核心结论是否仍然成立？"
  - 输出: SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED
```

---

## Implementation Priority

| Priority | Task | Dependencies | Est. Effort |
|----------|------|-------------|-------------|
| P0 | Environment auto-build (Dockerfile generation) | Docker installed | 2 days |
| P0 | Self-Correction loop (read error → fix → retry) | P0 | 2 days |
| P1 | Multi-pass paper reader | LLM API | 2 days |
| P1 | Result comparison framework (Levels 1-4) | P0 | 1 day |
| P2 | Reference resolution (cross-ref lookup) | P1 | 2 days |
| P2 | Chart digitization | matplotlib/OCR | 1 day |
