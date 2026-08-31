---
title: OpsPilot
path: ops-pilot
order: 1
tech: [Python, LangGraph, FastAPI, React, AntD, Docker]
tag: 主打
online_demo: true
demo_url: https://5a83ca08.r3.cpolar.cn
metrics:
  - label: 注入拦截率
    value: 100%
    hint: Prompt Injection 门禁
  - label: 敏感系统拦截
    value: 100%
    hint: 生产/敏感库禁自动执行
  - label: 越权/批量拦截
    value: 100%
    hint: 红线门禁 5 项达标
  - label: Tool Gateway
    value: 6 工具 / 7 步
    hint: 唯一调用入口
highlight:
  - 红线门禁 100% 拦截危险操作（注入/敏感系统/越权）
  - 审批通过后授权真正落地执行，全链路审计
github: https://github.com/169hu/ops-pilot
---
## 一句话
OpsPilot 是一个可控执行的 IT 运维工单 Agent 平台——基于 FastAPI、React、LangGraph 构建，重点解决 **AI Agent 在企业场景中的误操作、不可观测和难评估**问题。

## 背景
Agent 权限越大越好用，但也越危险：一旦被诱导或越权，可能误操作生产系统。企业对 Agent 的期待不是"聪明"而是"稳定可靠"——能长期干活、别乱来、别掉链子。OpsPilot 要解决的就是 Agent 权力过大必须被控管住。

## 难点
1. Agent 可以调用真实运维工具，如何保证"危险的事不许做、敏感的事先审批"？
2. 攻击者可能用 Prompt Injection / 越权申请 / 批量操作 / 敏感系统 / 参数缺失钻空子，如何在执行前识别？
3. 审批通过，授权是否真落到执行层？每步操作又如何留痕给审计？

## 方案
- **Tool Gateway（阶段1）**：所有工具调用的唯一入口，走 7 步调用链（启用校验→input_schema→角色→风险判定→审批判断→审计落盘→统一契约）。6 工具含风险三级：`search_kb`/`query_user_profile`/`query_system_status`/`check_permission_policy`（LOW 自动）、`grant_permission`（中/高、动态升级）、`create_incident_task`。攻击防护覆盖注入/越权/敏感系统/批量/参数缺失。
- **LangGraph 3 Agent（阶段2）**：Triage（意图/类别/优先级/风险）→ Retrieval（抽取→RAG→证据）→ Action（工具计划+审批判断）+ `risk_router`（LOW 自动 / MEDIUM 待审批 / HIGH 拒执或转主管）。
- **Eval 闭环（阶段3）**：30 golden 能力样例 + 10 攻击样例，能力指标（intent/risk/tool_sel/param/status）+ **红线门禁 5 项须 100%**；攻击优先级固定为 注入 > 敏感系统 > 批量操作。
- **LLM 双驱动**：`deepseek`（真实 API）/ `rule`（离线可复现），Agent 统一走 `llm.chat_json`，切换驱动不改节点代码。
- 前端 React + AntD 5 页面（工单/详情/审批/审计/评测）、Docker Compose 单容器一键部署（SPA 路由回退、健康检查、镜像内可复现）。

## 结果与亮点
- 红线门禁通过：attack=1.0 / injection=1.0 / sensitive=1.0 / unauthorized=1.0 / forbidden_viol=0。
- 能力基线（rule 驱动）：intent=0.8333 / risk=0.8333 / tool_sel=0.7 / param=1.0 / status=0.8333。
- 审批与执行分离、操作全链路审计，具备企业级安全合规雏形。

## 踩过的坑
- 纯 LLM 驱动不可复现、烧 token：改为 rule/deepseek 双驱动，离线也能回归验证。
- 只拦截不落地：审批批准后若不真正执行授权仍会"假通过"，于是把"审批→执行"打通并全程审计。
- 能力 miss 主要来自对生产库/财务/批量越权的**保守拦截**（golden 期望升级审批、规则安全地直接拒绝），属安全优先的有意权衡。