---
title: 劳动法律助手
path: legal-assistant
order: 3
tech: [Python, RAG, ChromaDB, DeepSeek, Streamlit, FastAPI, Docker]
tag: 主打
online_demo: true
demo_url: https://2gc8vfhnkkzuy7bwjcknye.streamlit.app/
metrics:
  - label: Faithfulness
    value: 98%
    hint: 回答可被法条支撑
  - label: 恶意/闲聊拒答
    value: 100%
    hint: 合规拒答（限定恶意/闲聊场景）
  - label: 引文准确率
    value: 100%
    hint: 引文号确在检索条中
  - label: 混合检索增益
    value: +12.5pp
    hint: 相对纯向量 50%→62.5%
highlight:
  - Agentic RAG：4-Agent 流水线 + HyDE + BM25 + 向量 + RRF
  - 合规拒答双保险，非法律问题温和引导不编造
github: https://github.com/169hu/legal-assistant
---
## 一句话
劳动法律助手是基于 **Agentic RAG** 的低配置可运行劳动法问答系统——先结论、再法条、末尾附引文溯源，问不到就拒答、不编造。

## 背景
劳动法咨询高发、专业门槛高，普通用户难读原文，又怕模型"一本正经地胡说"。法律场景对**可溯源**和**不瞎答**的要求远高于普通问答。

## 难点
1. 口语提问（"怀孕了公司要开掉我怎么办"）与法条书面语差距大，纯向量检索召回差。
2. 回答必须可追溯到具体法条、绝不编造，否则法律后果严重。
3. 非法律问题与低置信度问题必须合规拒答，既要防编造也要温和引导。

## 方案（升级版 10 项能力）
- **Agentic RAG 四 Agent 流水线**：意图识别 → 混合检索 → 6 维审查返工 → 回答。
- **混合检索（HyDE + BM25 + 向量 + RRF）**：HyDE 先生成"伪法条答案"跳向量语义召回，BM25 仍走原 query 字面匹配，RRF（k=60, recall_k 20→top_k 3）融合两路。
- **检索 Agent 自评循环**：判断检索是否充分，不足改写查询补查（最多 2 轮）。
- **6 维审查 + ≤3 次返工环**：准确性/完整性/合规性/清晰性/可溯源/中立加权平均，置信度 < 0.55 强制拒答。
- **合规拒答双保险**：意图识别 Agent 判定非法律问题（温和引导不答）→ 6 维审查置信度 < 0.55 强制拒答，宁可拒答也不编造。
- **多轮上下文记忆**：session_id + 指代消解（"那 3 年的呢？"→自动补全）；**GraphRAG** 法条引用图谱（399 节点/452 边，BFS 2 跳扩展连带引用簇）；**Tool Calling** 双引擎可对比（agentic/tool）。
- **扩展**：法律文书起草（7 类）、案件/合同台账（期限提醒）、IM/OA 网关（企微/飞书/钉钉 webhook）、FastAPI（/ask /draft /ledger /webhook/im）。

## 结果与亮点（本地实测 2026-08-15/16）
- 量化评估：关键词命中 90.0%、**Faithfulness 98.0%**、**恶意/闲聊类拒答 100%**、**引文准确率 100%**。
- 检索策略 Benchmark（16 题）：混合检索 RRF 相对纯向量 **+12.5pp**（50%→62.5%），加 HyDE 再 **+6.3pp**（→68.8%）。
- 冒烟测试 12/12 全通过；知识库 388 条法条；Docker Compose 一键部署。

## 踩过的坑
- 纯向量检索在扩展文档库上稳定性差：换成 BM25 + 向量 + RRF 混合检索提升 12.5pp，HyDE 把口语题拉回法条语义再 +6.3pp。
- ms-marco 英文重排器会严重扭曲中文法条排序：中文场景禁用重排。
- 模型可能漏判非法律问题：用意图识别 + 置信度"双保险"保证恶意/闲聊类拒答 100%，宁可拒答不编造。