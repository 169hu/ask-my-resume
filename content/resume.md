---
title: 简历
path: resume
tag: 个人信息
---
## 基本信息
- 姓名：胡进林
- 求职意向：AI 应用开发工程师
- 经验：应届生
- 现居：广东广州
- 生日：2005.01.14

## 联系方式
- 手机：15363139912
- 邮箱：161725862@qq.com
- GitHub：https://github.com/169hu
- 作品集 & 简历问答：https://169hu.github.io/ask-my-resume/

## 我是谁
黄河科技学院计算机科学与技术专业应届生，主攻 Python / 大模型应用方向。独立完成 RAG / Agent / 微调 / 评测方向的 7 个项目，每个项目都保留可复现的评测数据和开源代码，可当场演示与核查。习惯把每条技术跑通、量出效果、说清原理，不堆名词。

## 实习经历
**茂名清波环保科技有限公司 · AI 应用开发实习生**（2026年8月 - 9月，1 个月）

参与公司大模型智能问答平台的知识库问答模块开发，具体做了：
- 跟着同事清洗、去重、切分业务文档，向量化后入库；对比了 2 种切分粒度（按段落 vs 按语义块）对检索命中率的影响，选出较稳定的一种方案。
- 给问答模块加了"只依据检索资料回答、查不到就明确拒答、回答附来源"的约束规则；定位并处理了 3 个模型编造答案的案例，加了低相关上下文检测后拒答率从 60% 提到 95%。
- 给 Agent 工具调用层补了注入、越权两类测试用例，验证高危操作能被安全网关拦下再放行。
- 搭了四类评测用例（能答 / 该拒答 / 恶意输入 / 闲聊）作为回归基线，改完代码先跑一遍确认效果不回退；参与 Docker 部署、接口调优，整理模块文档交接。

## 会什么
- **语言与框架**：Python（主力）· JavaScript/React · Streamlit · FastAPI
- **大模型工程**：LangChain · LangGraph · Function Calling/ReAct · PyTorch · PEFT/QLoRA（Qwen/DeepSeek）
- **检索与 RAG**：ChromaDB · Neo4j · bge 中文向量模型 · 混合检索（BM25 + 向量 + RRF 融合）· HyDE 伪文档生成
- **评测与部署**：RAGAS 评测 · MCP 协议 · Docker/Docker Compose · Ollama/vLLM · Git

## 做过什么

**1. OpsPilot · 运维工单 Agent**（LangGraph · FastAPI · React/AntD · Docker）
- **任务**：AI Agent 调用运维工具时可能被诱导执行危险操作（注入、越权、碰生产库），需要一层安全网关管住。
- **做了什么**：LangGraph 编排 3 Agent（分诊 → 检索 → 执行）；封装 Tool Gateway 作为 6 个运维工具的唯一调用入口，走 7 步校验（输入 schema → 角色 → 风险分级 → 审批判断 → 审计落盘），LOW 自动放行、MEDIUM/HIGH 必须审批。
- **方法**：DeepSeek API + 离线规则双驱动（便于回归不烧 token）；React + AntD 5 页面、Docker Compose 一键起。
- **结果**：30 条能力样例 + 10 条攻击样例上，红线门禁 5 项（注入 / 敏感系统 / 越权 / 批量 / 参数缺失）全部 100% 拦截；审批通过后授权真正落到执行层并全程审计。

**2. AgentHub · 供应链风控多 Agent**（LangGraph · MCP · Neo4j · Streamlit）
- **任务**：供应商信息散落在数据库、知识图谱、法律库三个异构数据源，需要聚合成结构化风险报告。
- **做了什么**：LangGraph 编排 4 Agent（主控 / 研究员 / 分析师 / 风控官）；研究员通过 MCP 并行接入三个数据源——内部 DB（公司档案）、Neo4j（供应链图谱，GraphRAG 实体/社区检索）、跨项目法律检索（复用本机 legal-mcp-server → legal-assistant 的混合检索）。
- **方法**：Guard 双闸做输入检测（注入/越权/敏感信息命中即拒）+ 输出校验（空答/敏感泄漏硬拦截）；后端 MCP 用 async_runner 持久事件循环替代 asyncio.run，避免 stdio 长连接阻塞主事件循环。
- **结果**：RAGAS 基线 Hit Rate 0.90（19/20）；Guard 输入拦截 0 误伤；Faithfulness 从 0.32 调到 0.41（聚合提示词约束 + 法律检索聚焦），法律类问题命中从 0 提到 1。数据为构造样例、跨项目路径本机硬编码，属工程可行性验证，非生产级数据。

**3. 劳动法律助手**（Python · ChromaDB · DeepSeek · FastAPI · Docker）
- **任务**：法律问答要求回答必须可追溯到具体法条、绝不编造，非法律问题要合规拒答。
- **做了什么**：搭建 Agentic RAG 4-Agent 流水线（意图识别 → 混合检索 → 6 维审查返工 → 回答）；切分时按「条」做 chunk，每条带元数据（条号 / 章 / 来源）；用 bge-small-zh-v1.5 做向量化，ChromaDB 显式配置 `hnsw:space=cosine`（默认 L2 在中文检索上效果差）。
- **方法**：混合检索 = BM25（原 query 字面匹配）+ 向量（HyDE 先生成"伪法条答案"再召回）+ RRF 融合（k=60，recall_k 20 → top_k 3）；审查 Agent 6 维加权平均置信度 < 0.55 强制拒答。
- **结果**：388 条法条上跑评测，关键词命中 90.0%、**Faithfulness 98.0%**、**拒答率 100%**、引文准确率 100%；混合检索相对纯向量 +12.5pp（50% → 62.5%），加 HyDE 再 +6.3pp（→ 68.8%）。

**4. AI 翻译模型训练**（PyTorch · PEFT/QLoRA · Transformers）
- **任务**：在单显卡低资源环境下微调中英翻译模型，并量化评估泛化效果。
- **做了什么**：QLoRA 4-bit 量化 + LoRA 微调 `Qwen/Qwen2-1.5B-Instruct`（PEFT 把可训练参数压到极小，RTX 4060 Laptop 8GB 单卡可跑）；训练配置 `per_device_train_batch_size=1, gradient_accumulation_steps=8`（有效 batch=8），显存约 7GB；DeepSeek API 生成 80 条中英翻译数据，训练 `--max-steps 300 --lr 5e-5`；12 条留出集（训练数据之外）做 BLEU-4 评估。
- **方法**：对 Bad Case 人工分析，定位长句 BLEU 偏低是"语义正确、用词不同"的同义改写（set off/set out、meet/catch up with），并非翻译错误。
- **结果**：留出集平均 BLEU-4 = 0.824；短句（与训练分布接近）8 条 1.000，需泛化长句 4 条 0.472；训练 loss 从 10.27 降到 8.10（30 步冒烟训练，完整 3200 步曲线由 plot 模块生成）；提出引入 chrF/COMET 消除 BLEU 对同义改写的误罚。留出集仅 12 条，结论方向性参考。

**5. AI 智能工作台**（LangGraph · ChromaDB · Neo4j · DeepSeek）
- **任务**：在同一套架构里共存 RAG / Agent / 多 Agent / GraphRAG 四类能力，并量化评估各自效果。
- **做了什么**：分 4 层搭——展示层（Streamlit 多页面）→ 业务逻辑层（RAG / GraphRAG / Agent / 多Agent）→ 统一接入层（LLMClient 云端/本地一键切换）→ 工具层；RAG 引擎 = HyDE + 混合检索 + RRF，GraphRAG 走 Neo4j + Cypher 自动生成。
- **方法**：自动化评估四路对比——关键词命中率 + RAGAS + LLM-as-Judge + 自研评估器；定位到 RAGAS 0.1.0 在 DeepSeek 上 faithfulness 恒报 0/N/A 的根因（内部依赖 n>1 多采样而 DeepSeek 不支持），自行绕开写了拆句逐句判定的评估器。
- **结果**：检索命中率 4 轮迭代从 37.5% → 96.67%；扩展文档库（含语义干扰/专有名词）混合检索 95% vs 纯向量 80%（top_k=3）；自研评估器测出 Faithfulness 1.000、上下文相关性 1.000；LLM-as-Judge 9.67/10。

**6. Agent 评测系统（AgentEval Lab）**（LangGraph · MCP · asyncio）
- **任务**：AI Agent 改一版后如何自动化评测——人测慢且主观，需要 LLM 当 Judge 自动打分。
- **做了什么**：用 LangGraph 编排评测流程——跑被测 Agent → 记录工具调用轨迹 → LLM-Judge 按 Golden QA 打分 → 统计任务完成率、工具合规率并聚类失败原因 → 生成评测报告；支持 A/B 版本自动对比。
- **方法**：MCP 协议接入被测 Agent，用 asyncio 并发跑多条 case；评测用例分 4 类（能答 / 该拒答 / 恶意输入 / 闲聊），红线门禁指标要求 100% 拦截。
- **结果**：让 Agent 交付前先过一遍自动评测，改动后效果不回退；评测报告含量化指标 + 失败聚类，定位问题方向比人工测快很多。

**7. 多角色协作写报告**（LangGraph · LangChain · DeepSeek）
- **任务**：单次对话写长报告容易发散、质量不可控，需要分工 + 质检 + 返工的流水线。
- **做了什么**：LangGraph 状态图编排 9 角色（数据清洗 → 研究员 → 分析师 → 撰稿人 → 校对员/可视化师 → 审稿人 → 终审人 → 格式化工 → 最终报告）；审稿人按 6 维（结构/逻辑/准确/清晰/创新/可操作）加权 0.8~1.0 打分，低于阈值自动返工，最多 3 次（无上限会烧 token）。
- **方法**：ThreadPoolExecutor 并行跑可并发 Agent；每个 Agent 独立记忆，重启后自动加载、支持中断恢复。
- **结果**：完整跑通 9 角色流水线；示例流程审稿评分 8.2/10 → 终审 8.5/10 通过（单次示例结果，非多轮评测均值；暂无独立评测集）。

## 想找什么样的工作
AI 应用开发方向。独立完成 7 个 RAG / Agent / 微调 / 评测方向的项目，全部有可复现的评测数据和开源代码，可当场演示与核查。黄河科技学院计算机科学与技术本科，2027 届应届生，毕业前可全职实习。
