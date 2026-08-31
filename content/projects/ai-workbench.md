---
title: AI 智能工作台
path: ai-workbench
order: 4
tech: [Python, LangGraph, ChromaDB, Neo4j, Streamlit, GraphRAG, DeepSeek]
tag: 主打
online_demo: true
demo_url: https://4ba43038.r10.cpolar.top
metrics:
  - label: 检索命中率
    value: 96.67%
    hint: 4 轮迭代 37.5% → 96.67%
  - label: Faithfulness
    value: 1.000
    hint: 自研评估器绕过 RAGAS 限制
  - label: 混合检索增益
    value: +15pp
    hint: 扩展库 top_k=3 80%→95%
  - label: LLM-as-Judge
    value: 9.67/10
    hint: 批量 LLM 打分
highlight:
  - RAG / Agent / 多Agent / GraphRAG 全家桶，4 层模块化架构 + 云端/本地模型无缝切换
  - 自研忠实度评估器绕开 RAGAS 的 n>1 多采样限制，测出真实 Faithfulness 1.000
github: https://github.com/169hu/ai-workbench
---
## 一句话
AI 智能工作台是一个集 **RAG / Agent / 多 Agent / GraphRAG** 于一体的综合 AI 平台，4 层模块化架构、云端/本地模型无缝切换、数据驱动的自动化评估。

## 背景
简历上只写单一技术容易显得单薄。这个项目把大模型应用的核心技术栈（检索增强、智能体编排、图检索、评估）统一进一个可运行的工作台，既能系统验证各技术选型，也作为"全家桶"综合能力的直接证据。

## 难点
1. 四类能力（RAG / Agent / 多 Agent / GraphRAG）如何在同一套架构里共存且不互相污染？
2. 云端（DeepSeek）与本地（FastAPI）模型如何切换而不动上层业务代码？
3. RAG 效果如何量化评估？评估工具自身有缺陷时如何修复？

## 方案
- **4 层架构**：展示层（Streamlit 多页面）→ 业务逻辑层（RAG/GraphRAG/Agent/多Agent）→ 统一接入层（LLMClient 云端/本地一键切换）→ 工具层（持久化/文档加载/日志/向量库）。
- **RAG 引擎**：HyDE 伪文档 + 混合检索（BM25+向量）+ RRF 融合 + 重排序；GraphRAG 走 Neo4j + Cypher 自动生成。
- **Agent 双路径 Function Calling**：云端走原生 tools，本地走 JSON 降级。
- **自动化评估闭环**：关键词命中率 + RAGAS + LLM-as-Judge + 自研评估器四路对比。

## 结果与亮点
- 检索命中率经 4 轮迭代从 **37.5% → 96.67%**；扩展文档库（含语义干扰/专有名词）混合检索 **95% vs 纯向量 80%**（top_k=3）。
- **自研评估器**测出 **Faithfulness 1.000 / 上下文相关性 1.000**；LLM-as-Judge 平均 **9.67/10**；无答案问题拒答率 80%。
- Bad Case 分析定位到 RAGAS 0.1.0 在 DeepSeek 上报 0/N/A 的根因（n>1 多采样不支持），自行绕开并修复。

## 踩过的坑
- **RAGAS 在 DeepSeek 上失效**：faithfulness 恒 0/N/A，根因是内部依赖 n>1 多采样而 DeepSeek 不支持——自研拆句逐句判定评估器解决。
- **纯向量在小库看不出差距**：32 条小语料两策略都 100%，扩充到含干扰项的 63 条后才凸显混合检索 +15pp 优势——评测语料必须贴近真实长尾。
- **无答案问题倾向编造**（拒答率 80% 未达 100%）：需在生成层加"低相关上下文检测"强制拒答——这条经验后来直接演进成法律助手的"无来源不答"。