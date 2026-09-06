---
title: Agent 评测系统（AgentEval Lab）
path: agent-eval-lab
order: 6
tech: [Python, LangGraph, MCP, asyncio, DeepSeek]
tag: 主打
online_demo: true
demo_url: https://agent-eval-lab.streamlit.app/
metrics:
  - label: 评测指标
    value: 4 项全绿
    hint: 任务完成·工具合规·参数·调用成功率
  - label: A/B 对比
    value: 自动跑分
    hint: 平局但省 7% token / 快 17%
  - label: 评测成本
    value: 6 例 ~0.005$
    hint: 低至可常跑
highlight:
  - LangGraph 编排评测流程：跑被测 Agent → LLM-Judge 打分 → 统计聚类 → 生成报告
  - MCP 协议接入被测 Agent，asyncio 并发跑多条 case，支持 A/B 版本自动对比
github: https://github.com/169hu/agent-eval-lab
---

## 一句话
AgentEval Lab 是一个 AI Agent 自动化评测系统——用 LangGraph 编排评测流程，LLM 当 Judge 自动打分，让 Agent 交付前先过一遍自动评测。

## 背景
AI Agent 改一版后如何自动化评测——人测慢且主观，每次改代码都要手动跑一遍 Golden QA 太痛苦。需要一个 LLM 当 Judge 的自动评测框架，改完代码先跑一遍确认效果不回退。

## 难点
1. 如何让 LLM-Judge 的打分相对稳定、不跑偏？
2. 被测 Agent 可能是不同技术栈（FastAPI / LangGraph / 纯 Streamlit），如何统一接入？
3. 评测用例怎么设计才看得出差异——用例太简单指标全顶到 100% 时，两版提示词到底谁好？

## 方案
- **LangGraph 编排评测流程**：跑被测 Agent → 记录工具调用轨迹 → LLM 评委（LLM-Judge）按标准问答（Golden QA）打分 → 统计任务完成率、工具合规率并聚类失败原因 → 生成评测报告；支持 A/B 版本自动对比。
- **MCP 协议接入被测 Agent**：统一入口，被测 Agent 实现 MCP server 即可接入评测框架自动发现和调用；当前基于自带模拟智能体（mock_agent，含乘法/销售额两个演示工具）跑通全链路验证，真实项目接入是预留扩展点；用 asyncio 异步并发跑多条用例，加快评测速度。
- **评测用例分层设计**：示例评测集 6 条，覆盖 3 类场景——能力类（乘法 / 查销售额，必须调用对应工具并给出正确数值）、反幻觉类（查不到的公司必须如实说查不到，不得编造）、多步组合类（连续两次工具调用后再比较结果）。每条用例携带标准答案（关键词 / 必调工具 / 精确参数），客观校验与裁判打分互相印证。

## 结果与亮点
- 让 Agent 交付前先过一遍自动评测，改动后效果不回退；评测报告含量化指标（任务完成率、工具合规率、参数正确率、调用成功率）+ 失败归因聚类（定位问题方向比人工测快很多）。
- 示例评测集 6 条全通过、四项指标 100%，单次约 6365 tokens、成本约 $0.0045，可低成本常跑；A/B 对比两版四项指标持平，但懒提示版省约 7% token、快约 17% 延迟——结论来自量化而非感觉。

## 踩过的坑
- LLM 评委打分不稳定：加了标准问答（Golden QA）作为参考答案约束评委输出格式和评分标准，减少漂移。
- 被测 Agent 接入慢：统一用 MCP 协议，Agent 只要暴露几个工具就能被自动发现，接入时间从小时级降到分钟级。
- 评测集太简单会撞 100% 天花板：6 条示例全部满分后，A/B 两版四项指标看不出差异，只能从 token 与延迟分辨——评测语料必须分层加难度，指标全绿不等于两版一样好。
