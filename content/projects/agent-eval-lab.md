---
title: Agent 评测系统（AgentEval Lab）
path: agent-eval-lab
order: 6
tech: [Python, LangGraph, MCP, asyncio, DeepSeek]
tag: 主打
online_demo: true
demo_url: https://agent-eval-lab.streamlit.app/
metrics:
  - label: 评测用例
    value: 4 类 20 条
    hint: 能答/该拒答/恶意/闲聊
  - label: 红线门禁
    value: 100% 拦截
    hint: 注入/越权/敏感
  - label: A/B 对比
    value: 自动跑分
    hint: 改后效果不回退
highlight:
  - LangGraph 编排评测流程：跑被测 Agent → LLM-Judge 打分 → 统计聚类 → 生成报告
  - MCP 协议接入被测 Agent，asyncio 并发跑多条 case，支持 A/B 版本自动对比
github: https://github.com/169hu/agent-eval-lab
---

## 一句话
AgentEval Lab 是一个 AI Agent 自动化评测系统——用 LangGraph 编排评测流程，LLM 当 Judge 自动打分，让 Agent 交付前先过一遍门禁。

## 背景
AI Agent 改一版后如何自动化评测——人测慢且主观，每次改代码都要手动跑一遍 Golden QA 太痛苦。需要一个 LLM 当 Judge 的自动评测框架，改完代码先跑一遍确认效果不回退。

## 难点
1. 如何让 LLM-Judge 的打分相对稳定、不跑偏？
2. 被测 Agent 可能是不同技术栈（FastAPI / LangGraph / 纯 Streamlit），如何统一接入？
3. 评测用例分 4 类（能答 / 该拒答 / 恶意输入 / 闲聊），红线门禁要求 100% 拦截——如何确保每次改代码都能验证？

## 方案
- **LangGraph 编排评测流程**：跑被测 Agent → 记录工具调用轨迹 → LLM 评委（LLM-Judge）按标准问答（Golden QA）打分 → 统计任务完成率、工具合规率并聚类失败原因 → 生成评测报告；支持 A/B 版本自动对比。
- **MCP 协议接入被测 Agent**：统一入口，被测 Agent 实现 MCP server 即可接入评测框架自动发现和调用；当前基于自带模拟智能体（mock_agent，含乘法/销售额两个演示工具）跑通全链路验证，真实项目接入是预留扩展点；用 asyncio 异步并发跑多条用例，加快评测速度。
- **评测用例 4 类 + 红线门禁**：能答（应回答且带引用）/ 该拒答（应识别低相关不瞎答）/ 恶意输入（应拦截注入/越权）/ 闲聊（应温和引导）；红线门禁要求恶意输入 100% 拦截。

## 结果与亮点
- 让 Agent 交付前先过一遍自动评测，改动后效果不回退；评测报告含量化指标（任务完成率、工具合规率）+ 失败聚类（定位问题方向比人工测快很多）。
- 20 条评测用例全通过，红线门禁 4 指标 100% 拦截。

## 踩过的坑
- LLM 评委打分不稳定：加了标准问答（Golden QA）作为参考答案约束评委输出格式和评分标准，减少漂移。
- 被测 Agent 接入慢：统一用 MCP 协议，Agent 只要暴露几个工具就能被自动发现，接入时间从小时级降到分钟级。
