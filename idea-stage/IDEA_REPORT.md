# Research Idea Report: AI Reproducibility Metrology

**Direction**: AI Agent 自动论文复现与可复现性计量
**Target Paper**: SciSciGPT (Nature Computational Science 2025)
**Date**: 2026-06-01

## Executive Summary

提出一个新范式：**用 AI Agent 作为"计量仪器"自动测量科学研究的可复现性**。

核心思路：AI Agent 读取论文 → 自动构建复现环境 → 执行分析 → 比对结论 → 输出可复现性评估报告。
关键创新：不仅测量"结论是否可复现"，还测量"环境构建需要多少次修复迭代"——后者本身就是一个计量指标（Reproducibility Effort Index, REI）。

对标 SciSciGPT (Nature Computational Science 2025)，该工作用 5-Agent 协作系统自动做 SciSci 研究，
完成时间为研究人员的 ~10%。我们在此基础上构建**可复现性测量仪器**。

## System Architecture

```
论文 PDF → [Agent 读取] → 提取实验方案(方法/数据/分析步骤)
              ↓
        [环境构建] → 动态生成 Dockerfile
              ↓
        [沙箱执行] → 运行分析代码(支持 Python/R/Julia)
              ↓
        [结果比对] → Agent 输出 vs 论文声称的结果
              ↓
        [失败] → Self-Correction: Agent 读报错 → 修复 → 重试
              ↓
        输出: 可复现性评估报告 + REI 分数
```

## Four Modules

1. **论文理解模块**: 结构化提取方法、数据、分析步骤 (Grobid/LLM)
2. **环境构建模块**: 动态生成容器 + Self-Correction 修复循环 ← 技术壁垒
3. **分析复现模块**: 沙箱执行 + 结果比对 (Python/R/Julia subprocess)
4. **可复现性报告模块**: 自动生成评估报告 (REI + 逐步骤评估)

## Key Innovation: Reproducibility Effort Index (REI)

REI = Σ(每步骤修复迭代次数) / (成功步骤数)

这是首个**可复现性努力的定量计量指标**：
- REI = 0: 一键复现（黄金标准）
- REI ≤ 2: 低努力（常规可复现）
- REI ≤ 5: 中等努力（需要专业调试）
- REI > 5: 高努力（可能需要原作者介入）
- REI = ∞: 不可复现（放弃）

## SciSciGPT Reproduction Strategy

1. 提取 SciSciGPT 的核心多 Agent 架构 (LangGraph StateGraph)
2. 适配到本地基础设施 (Qwen3-32B/DeepSeek, 本地沙箱, 本地存储)
3. 复现论文中的 Case Study 2 (Wu et al. 2019 "大团队发展科学，小团队颠覆科学" 图表复现)
4. 计算 REI，记录所有修复迭代

## SciSci SDK Design (Step 2)

SDK 封装高阶 SciSci 操作，Agent 不再裸写底层代码：

| SDK 函数 | 底层处理 |
|---------|---------|
| `sci.disruption_index(doi)` | 引文网络图查询 + 三元组计数 |
| `sci.cem_match(ids, pool, on)` | 分布式 CEM 匹配 |
| `sci.citation_cascade(doi, depth)` | 引文级联分析（多跳遍历） |
| `sci.coauthor_network(author_id)` | 子图提取 + 中心性计算 |
| `sci.field_normalize(metric, field, year)` | 领域×年份 Z-score 标准化 |

## Experiment Roadmap

| Phase | Task | Status |
|-------|------|--------|
| M0 | Multi-agent graph smoke test | ✓ DONE |
| M1 | Single-specialist + real LLM + sandbox | ✓ DONE (mock), pending (API) |
| M2 | Paper reproduction pipeline | In progress |
| M3 | Self-Correction loop + REI | Planned |
| E2a-c | SciSci SDK validation | Planned |

## Next Steps

1. Configure LLM API key (ANTHROPIC_API_KEY or OPENAI_API_KEY)
2. Run M1 with real LLM → verify >70% task completion
3. Build paper ingestion module (PDF → structured method extraction)
4. Reproduce SciSciGPT Case Study 2 → compute REI
5. Implement SciSci SDK disruption_index(), cem_match()
