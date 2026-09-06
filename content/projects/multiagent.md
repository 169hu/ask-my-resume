---
title: 多 Agent 协作系统
path: multiagent
order: 7
tech: [Python, LangGraph, LangChain, DeepSeek, ThreadPool]
tag: 主打
online_demo: true
demo_url: https://multi-agent-playground-mgoykx8wgaug6m95vhytut.streamlit.app/
metrics:
  - label: Agent 角色
    value: 9 个
    hint: 清洗→研究→分析→撰稿→审稿→终审
  - label: 质量闭环
    value: 6 维评分
    hint: 不达标自动返工 ≤3 次
  - label: 并行执行
    value: ThreadPool
    hint: 多 Agent 同时工作
  - label: 记忆持久化
    value: 独立记忆
    hint: 重启自动恢复
highlight:
  - LangGraph 9-角色流水线 + 6 维审核评分，形成质量自检闭环
  - 审核不过自动返工（≤3 次），Agent 独立记忆持久化
github: https://github.com/169hu/multi-agent-playground
---
## 一句话
基于 **LangGraph + DeepSeek** 的多 Agent 协作系统：9 个角色构成从数据清洗到最终报告的自动化流水线，6 维审核保质量、不达标自动返工。

## 背景
单 Agent 回答容易发散、质量不可控。真正的报告类任务需要"分工+质检+返工"的工程流。这个项目用 LangGraph 编排 9 个专职角色，把一次复杂报告生成变成可控的流水线，是 Agent 编排能力的典型证明。

## 难点
1. 9 个 Agent 职责如何划分、如何串联成有向工作流而不乱？
2. 质量如何保证？谁来判断"写得不行"并触发返工？
3. 多 Agent 之间如何通信、状态如何保存（中断后能恢复）？

## 方案
- **LangGraph 状态图编排**：数据清洗 → 研究员 → 分析师 → 撰稿人 → 校对员/可视化师 → 审稿人（6 维评分）→ 终审人（通过/返工）→ 格式化工 → 最终报告。
- **审稿人 6 维评分**（结构/逻辑/准确/清晰/创新/可操作，加权 0.8~1.0），低于阈值自动打回返工（**最多 3 次**）。
- **并行与通信**：ThreadPoolExecutor 并行执行可并发的 Agent；中间产物经 LangGraph GraphState 共享状态传递。
- **状态持久化**：每个 Agent 独立记忆，重启后自动加载，支持中断恢复。

## 结果与亮点
- 完整跑通 9 角色流水线，示例流程审稿评分 8.2/10 → 终审 8.5/10 通过。
- 质量反馈闭环让系统能自检自纠，报告自动生成不依赖人工干预。
- 掌握 LangGraph 状态图、Agent 编排、状态传递与记忆持久化的完整套路。

## 踩过的坑
- **角色不执行**：Agent 职责重叠会导致跳过环节——先用 Prompts 明确单一职责，再画状态图。
- **返工死循环风险**：无上限返工会烧 token——用"≤3 次 + 终审兜底"硬控。