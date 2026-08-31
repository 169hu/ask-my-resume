# Ask My Resume · 作品集 + AI 答疑

个人作品集网站：简历 + 项目 + AI 答疑机器人三合一。右下角聊天窗口基于"简历 + 项目资料"的向量知识库问答，**每条回答必须带来源引用**，查不到就拒答、不编造。

## 在线演示

> 演示地址以 `scripts/restore_tunnels.ps1` 运行输出为准；仓库内写死的链接不保证长期有效（免费版 cpolar 每次重启地址都会变，跑一次脚本即刷新）。

- 作品集：见 README 顶部注释或运行恢复脚本获取
- 6 个项目详情页内的「打开项目试玩 Demo」按钮指向各自可运行的演示应用

## 功能

- 首页：个人简介 + 评测门禁 + 关于我详情页
- 项目：6 个项目的卡片 / 详情 / Demo / GitHub 链接
- AI 答疑：基于向量知识库的 RAG 问答，带来源引用，注入攻击拦截、超纲拒答
- 评测门禁：离线的 golden 用例评测（20 条×4 类），注入拦截率 100% 才允许发布

## 技术栈

- 后端：FastAPI（REST API + 托管前端静态文件 + SPA 回退）
- 前端：React + Vite（纸白 + 深蓝 + 宋体风格，响应式）
- 检索：ChromaDB + bge-small-zh-v1.5（本地离线加载）+ BM25 + RRF 混合检索
- 评测：`scripts/evaluator.py` 输出 `/api/eval` 报告

## 本地运行

```bash
# 1. 后端
.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001

# 2. 前端构建
cd frontend && npm install && npm run build   # 构建产物由后端托管
```

或直接双击 `scripts/start_all_demos.ps1` 一键启动包含 6 个项目演示在内的全部服务。

## 公网访问（内网穿透）

```powershell
# 一键重建 7 条隧道 + 自动更新项目详情页 Demo 链接
.\scripts\restore_tunnels.ps1
```

免费版 cpolar 每次重启地址会变，该脚本会自动把 6 个项目 md 的 `demo_url` 换成新地址并打印链接清单。

## AI 答疑质量

评测门禁（`/api/eval`）：能力题 / 超纲拒答 / 注入攻击 / 闲聊 4 类共 20 条用例，全部离线评测、结果可复现。红线：注入拦截率必须 100%。