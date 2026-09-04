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
黄河科技学院计算机科学与技术专业应届生，主攻 Python / 大模型应用方向。独立完成 RAG / Agent / 微调 / 评测方向的 5 个主打项目，每个项目都保留可复现的评测数据和开源代码，可当场演示与核查。习惯把每条技术跑通、量出效果、说清原理，不堆名词。**毕业前可全职实习，到岗时间灵活**。

## 实习经历
**茂名清波环保科技有限公司 · AI 应用开发实习生**（2026年8月 - 9月，1 个月）

参与公司大模型智能问答平台的知识库问答模块开发，具体做了：
- 清洗、切分业务文档并向量化入库；对比了两种切分粒度对检索命中率的影响，选出较稳定的一种方案。
- 在问答 Prompt 中嵌入三条硬约束——"只依据检索资料回答""查不到则明确拒答""回答必须附来源"；定位并处理了 3 个模型编造答案的案例，**恶意输入拒答率从约 60% 提升到 95% 以上**。
- 给 Agent 工具调用层补了注入、越权两类测试用例，验证高危操作能被安全网关拦下再放行。
- 搭了四类评测用例（能答 / 该拒答 / 恶意输入 / 闲聊）作为回归基线，改完代码先跑一遍确认效果不回退；参与 Docker 部署、接口调优，整理模块文档交接。

## 会什么
- **语言与框架**：Python（主力）· JavaScript / React / AntD · FastAPI · Streamlit
- **LLM 应用**：LangChain · LangGraph · Function Calling · Prompt Engineering
- **检索与 RAG**：ChromaDB（cosine 距离，踩过 L2 坑）· Neo4j GraphRAG · bge 中文向量 · 混合检索（BM25 + 向量 + RRF k=60）· HyDE · 选型对比过 Milvus / PGVector
- **数据与部署**：Docker · Git · Sqlite / MySQL（关系型 DB 原理 + Sqlite 无缝迁移）· Redis（缓存层选型）· vLLM（PagedAttention 推理加速）
- **微调与评测**：PyTorch · PEFT / QLoRA 4-bit · RAGAS（Hit Rate / Faithfulness）· BLEU-4

## 做过什么

**1. OpsPilot · 运维工单 Agent**（LangGraph · FastAPI · React/AntD · Docker）
- **任务**：AI Agent 调用运维工具时可能被诱导执行危险操作（注入、越权、碰生产库），需要一层安全网关管住。
- **做了什么**：LangGraph 编排 3 Agent（分诊 → 检索 → 执行）；设计 RESTful API 供前端 React 调用；封装 Tool Gateway 作为 6 个运维工具的唯一调用入口，走 7 步校验（输入 schema → 角色 → 风险分级 → 审批判断 → 审计落盘），LOW 自动放行、MEDIUM/HIGH 必须审批；LangGraph AsyncSqliteSaver 持久化对话历史，重启后可从上次中断点继续。
- **方法**：DeepSeek API + 离线规则双驱动（便于回归不烧 token）；React + AntD 5 页面、Docker Compose 一键起。
- **结果**：**30 条正常样例 + 10 条攻击样例上，注入/敏感系统/越权/批量/参数缺失 5 项红线 100% 拦截**；审批通过后授权真正落到执行层并全程审计。

**2. AgentHub · 供应链风控多 Agent**（LangGraph · MCP · Neo4j · Streamlit）【多 Agent 协同 · MCP 工具链 · 熔断降级 · 记忆持久化】
- **任务**：供应商信息散落在 JSON 公司档案库、Neo4j 供应链图谱、法律库三个异构数据源，需要聚合成结构化风险报告。
- **做了什么**：LangGraph 编排 4 Agent（主控 / 研究员 / 分析师 / 风控官）+ AsyncSqliteSaver 持久化对话历史；研究员通过 MCP 并行接入三个数据源——JSON 公司档案库、Neo4j 供应链图谱（GraphRAG 用 Cypher 自动生成查询）、跨项目法律检索（planner 用 LLM 意图路由到 intent=legal 时触发，关键词匹配兜底；复用本机 legal-mcp-server）。
- **方法**：Guard 双闸做输入检测（注入/越权）+ 输出校验（是否有据）；MCP 用 async_runner 持久事件循环替代 asyncio.run 防阻塞；客户端带熔断器（连续 3 次失败熔断 + 15s 超时），单点数据源故障不中断整图，降级时输出标注异常环节。
- **结果**：**RAGAS Hit Rate 0.90（19/20 条 baseline 能检索到答案依据），Guard 输入拦截 0 误伤**；数据为构造样例、跨项目路径本机硬编码，属工程可行性验证，非生产级数据。

**3. 劳动法律问答助手**（Python · ChromaDB · DeepSeek · FastAPI · Docker）
- **任务**：法律问答要求回答必须可追溯到具体法条、绝不编造，非法律问题要合规拒答。
- **做了什么**：搭建 Agentic RAG 4-Agent 流水线（意图识别 → 混合检索 → 6 维审查返工 → 回答）；切分时按「条」做 chunk，每条带元数据（条号 / 章 / 来源）；用 bge-small-zh-v1.5 做向量化，ChromaDB 显式配置 `hnsw:space=cosine`（默认 L2 在中文检索上效果差）。
- **方法**：混合检索 = BM25（原 query 字面匹配）+ 向量（HyDE 先生成"伪法条答案"再召回）+ RRF 融合（k=60，recall_k 20 → top_k 3）；审查 Agent 6 维加权平均置信度 < 0.55 强制拒答。
- **结果**：388 条法条评测集：**Faithfulness 98.0%（回答可被法条支撑）、恶意/闲聊类拒答 100%、引文准确率 100%**；混合检索比纯向量 +12.5pp，加 HyDE 再 +6.3pp。

**4. QLoRA 微调 AI 翻译模型**（PyTorch · PEFT/QLoRA · Transformers）
- **任务**：在单显卡低资源环境下微调中英翻译模型，并量化评估泛化效果。
- **做了什么**：QLoRA 4-bit + LoRA 微调 Qwen2-1.5B-Instruct，RTX 4060 Laptop 8GB 单卡可跑（per_device_batch=1 + gradient_accumulation=8，有效 batch=8，训练时显存约 7GB）；80 条中英对照数据训练 300 步。
- **方法**：DeepSeek API 生成训练数据；对 Bad Case 人工分析。
- **结果**：12 条留出集 BLEU-4 = **0.824**（短句 8 条 1.000 / 长句 4 条 0.472）；Bad Case 分析定位长句 BLEU 偏低是同义改写被 n-gram 误罚，提出用 chrF/COMET 替代。

**5. AI 智能工作台**（LangGraph · ChromaDB · Neo4j · DeepSeek）
- **任务**：在同一套架构里共存 RAG / Agent / 多 Agent / GraphRAG 四类能力，并量化评估各自效果。
- **做了什么**：4 层架构（展示 → 业务逻辑 → 统一接入 → 工具），同一平台共存 RAG / Agent / 多 Agent / GraphRAG 四类能力；RAG 引擎 = HyDE + 混合检索 + RRF，GraphRAG 走 Neo4j + Cypher 自动生成。
- **方法**：自动化评估四路对比——关键词命中率 + RAGAS + LLM-as-Judge + 自研评估器；定位到 RAGAS 0.1.0 在 DeepSeek 上 faithfulness 恒报 0/N/A 的根因（内部依赖 n>1 多采样而 DeepSeek 不支持），自行绕开写了拆句逐句判定的评估器。
- **结果**：**检索命中率 4 轮迭代 37.5% → 96.67%**；扩展库混合检索 95% vs 纯向量 80%；自研评估器测出 Faithfulness 1.000（绕开 RAGAS 在 DeepSeek 上的 n>1 限制）。

## 想找什么样的工作
AI 应用开发方向。独立完成 RAG / Agent / 微调 / 评测方向 5 个主打项目，全部有可复现评测数据与开源代码，可当场演示。黄河科技学院计算机科学与技术本科，2027 届应届生，毕业前可全职实习，到岗时间灵活。
