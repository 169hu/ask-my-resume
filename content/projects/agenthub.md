---
title: AgentHub
path: agenthub
order: 2
tech: [Python, LangGraph, MCP, Neo4j, Streamlit, Guard]
tag: 主打
online_demo: true
demo_url: https://5u25xmjzwlimdaojhrh2tf.streamlit.app/
metrics:
  - label: 多 Agent 编排
    value: 4 Agent
    hint: 主控/研究员/分析师/风控官
  - label: Guard 输入拦截
    value: 命中即拒
    hint: 注入/越权/敏感信息
  - label: MCP 数据源
    value: 3 个
    hint: 内部库/知识图谱/法律检索
  - label: Hit Rate
    value: 0.90
    hint: RAGAS 基线 19/20
highlight:
  - 4 Agent 编排 + Guard 输入输出双重安全
  - MCP 跨项目能力闭环（跨项目复用法律检索）
github: https://github.com/169hu/agenthub
---
## 一句话
AgentHub 是一个供应链风控的多 Agent 协作系统——四类 Agent 分工协作，外加 Guard 安全层全程把关。

## 背景
供应链风控要判断一家公司值不值得继续合作，需要同时查它的档案、它的上下游链路、以及相关法条，信息来源分散、专业门槛高。AgentHub 想把这些散落的信息聚合成一份结构化风险报告。

## 难点
1. 信息来自多个异构数据源（数据库、知识图谱、法律库），如何统一接入？
2. 多步分析（查资料→量化→下结论）单靠一次对话容易发散，如何编排成可控流程？
3. Agent 能查库、能调用工具，如何防止它对危险/越权请求动手？

## 方案
- 用 LangGraph 编排四类 Agent：主控、研究员、分析师、风控官。研究员通过 MCP（Model Context Protocol）并行接入三个数据源：internal-db（公司档案/风险事件）、neo4j-graph（供应链图谱，GraphRAG 实体/社区检索）、跨项目法律检索（复用本机 legal-mcp-server → legal-assistant）。
- 安全上采用 **Guard 双闸**：输入检测（注入/越权/敏感信息）命中即短路拒绝；输出校验对空答/敏感泄漏硬拦截（fail），质量差/幻觉复核标记（warn）。
- **跨项目能力闭环**：`agenthub`（MCP Host）经 MCP → `legal-mcp-server` → 复用 `legal-assistant` 的 BM25+向量+RRF 混合检索，研发出一问即可命中真实法条。

## 迭代 3 六项工程化优化
三个硬优化 + 三个软优化：
- 可观测性（每节点 trace）｜流式输出（astream + 打字机）｜兜底降级（CircuitBreaker 熔断 + 15s 超时，单点故障不中断）。
- LLM 意图路由（legal/supply_chain_risk/company_profile/general）｜记忆压缩（>10 轮历史折叠为摘要）｜RAGAS 离线评测基线。

## 结果与亮点
- RAGAS 基线：Hit Rate 0.90（19/20）、Faithfulness 0.42；通过聚合提示词约束与法律检索聚焦，Faithfulness 0.32 → 0.41、法律 g12 Hit 0→1。
- Guard 输入拦截命中即短路、无一误伤；真实 Neo4j 可用、连接失败自动降级内存图（本地零依赖可跑）。

## 踩过的坑
- 法律检索首次会加载 embedding 模型 + HyDE，耗时长：改为仅在 LLM 意图路由（intent=legal）或关键词兜底命中的必要时才触发。
- 后端 MCP stdio 长连接易阻塞事件循环：改用 async_runner 的持久后台事件循环而不是临时 asyncio.run。
- 供应商名以 ID 存导致检索短路：加 `resolve_company_names` 把 ID 转公司名，Hit Rate 0.70 → 0.90。（真 vs Demo 边界：数据结构为构造样例、跨项目路径本机硬编码，属工程可行性验证，尚非生产交付。）