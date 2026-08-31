"""ask-my-resume 应答模块：实现「无来源不答」硬约束的三件套。

流程：
  1. 检索 → 分数先挡一道（低于阈值直接拒答，不调 LLM，省 token、响应快）
  2. 生成时强制每个论点带 [n] 引用标号（n 只能来自本次检索结果）
  3. 生成后 regex 校验：提取 [n]，检查是否都在检索集合里，
     不在就重试或追加"部分内容未能溯源"声明

双驱动：
  - rule  离线规则驱动：不做 LLM 调用，直接由检索片段拼装 + 强制标号，
          主要用于离线复现 / 本地无 key 环境。
  - deepseek  真实 LLM 驱动：调用 DeepSeek 按 prompt 生成带引用的回答。
"""
import json
import os
import re
from urllib import request, error

from backend import kb

# 「无来源不答」检索阈值：sim >= ACCEPT_SIM 视为"可答"，否则拒答/反问。
# 依据 M1 验证：该命中 ~0.51-0.57，该拒答 ~0.28-0.32，故取 0.45 安全居中。
ACCEPT_SIM = float(os.environ.get("ACCEPT_SIM", "0.45"))

# 注入意图检测：以下模式命中（如"忽略设定/输出system prompt/绕过检查/泄露密钥"）
# 一律在检索前短路拒答。检索兜不住注入（注入常与安全/资料语义高相关），必须专门防。
INJECTION_PATTERNS = [
    # 要求忽略/推翻既定设定
    r"忽略.{0,8}(之前|以上|所有|你).{0,8}(指令|设定|规则|提示|system)",
    r"(忽略|无视|推翻).{0,6}(指令|设定|规则)",
    # 要求输出内部提示词 / 系统上下文
    r"(输出|展示|读出|打印).{0,8}(system\s*prompt|系统提示|系统设定|内部指令|完整指令)",
    r"(你的|你的).{0,4}(system\s*prompt|提示词|指令)原文",
    # 命令式操纵 / 越权
    r"现在你是一条命令",
    r"(回答|回复)\s*['\"](?:yes|ok|是)['\"]",
    # 要求泄露凭据 / 数据
    r"(列|输出|告诉|吐|给|曝).{0,8}(密钥|密码|口令|token|所有表名|数据库|用户列表|敏感)",
    r"泄露.{0,4}(密钥|密码|数据|隐私)",
    # 兜底：形如"把...列出来"/"所有表名...密钥" 的长句式越权泄露
    r"(把|将).{0,16}(表名|密钥|密码|数据|数据库).{0,12}(列|输出|交|吐|给)",
    r".{0,10}(所有表名|全部数据|密钥|密码).{0,10}(列出来|输出|倒出来|吐出来)",
]

INJECTION_RE = [
    re.compile(p, re.I) for p in INJECTION_PATTERNS
]


def _detect_injection(question: str) -> bool:
    """注入特征检测：命中任意正则即视为高风险注入。"""
    return any(rx.search(question) for rx in INJECTION_RE)

SOURCE_LABELS = {
    "ops-pilot": "OpsPilot",
    "agenthub": "AgentHub",
    "legal-assistant": "劳动法律助手",
    "finetune-deploy": "大模型微调与部署",
    "resume": "简历",
}


def _driver() -> str:
    return os.environ.get("LLM_DRIVER", "rule")


def _sources_snippet(hits) -> str:
    """把命中片段拼成带编号的上下文，供 prompt / rule 拼装使用。"""
    lines = []
    for i, h in enumerate(hits, 1):
        src = SOURCE_LABELS.get(h["source"], h["source"])
        lines.append(f"[{i}]（来源：{src}）{h['text']}")
    return "\n".join(lines)


def _call_deepseek(prompt: str) -> str:
    """调用 DeepSeek chat completions。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    base = os.environ.get("DEEPSEEK_BASE_URL",
                          "https://api.deepseek.com").rstrip("/")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    if not api_key:
        raise RuntimeError("LLM_DRIVER=deepseek 但缺少 DEEPSEEK_API_KEY")

    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "stream": False,
    }).encode("utf-8")
    req = request.Request(
        f"{base}/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"})
    with request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def _rule_answer(query: str, hits) -> str:
    """rule 驱动：不做 LLM，直接由片段拼装 + 强制标号 + 校验。"""
    parts = [f"根据我的项目资料，我的回答如下："]
    for i, h in enumerate(hits, 1):
        parts.append(f"· [{i}] 来源{SOURCE_LABELS.get(h['source'], h['source'])}：{h['text']}")
    if _verify_refs("\n".join(parts), len(hits)):
        parts.append("（以上均来自我的简历/项目资料，均为真实内容）")
    return "\n".join(parts)


def _verify_refs(answer: str, n_hits: int) -> bool:
    """regex 校验：提取 [n]，确保都在检索集合 1..n_hits 范围内。"""
    refs = re.findall(r"\[(\d{1,2})\]", answer)
    if not refs:
        return False
    return all(int(r) in range(1, n_hits + 1) for r in refs)


def answer(question: str) -> dict:
    """对一个问题返回结构化应答。"""
    # 注入意图检测：在检索之前短路拦截（检索兜不住注入）
    if _detect_injection(question):
        return {
            "status": "reject",
            "answer": ("抱歉，这种试图绕过安全规则、泄露内部指令或敏感凭据的问题，"
                       "我不能也不会作答。我是基于公开简历资料做引用的求职助手，"
                       "你可以问我做过哪些项目、用了什么技术、踩过哪些坑。"),
            "hits": [],
        }

    hits = kb.search(question, n=4)
    top = hits[0] if hits else None

    # 1) 分数先挡：无命中 或 最高分低于阈值 → 拒答 + 给出口。
    #    命中分数不足的片段不计为"来源"，故返回空 hits，避免前端把低相关
    #    片段也当引用展示，与"没相关资料"的拒答文案自相矛盾。
    if not top or top["sim"] < ACCEPT_SIM:
        return {
            "status": "reject",
            "answer": ("这个问题我没有相关的真实资料，无法作答，也不会编造。"
                       "我更擅长聊这几个方向：我的项目经历、RAG/Agent 技术、模型微调与部署、"
                       "以及我踩过的坑和解决思路——你感兴趣哪个？"),
            "hits": [],
        }

    driver = _driver()
    if driver == "deepseek":
        system = (
            "你是候选人的求职辅助 AI，只能基于给定资料回答。"
            "硬性要求（无来源不答）：每个论点必须带 [n] 引用标号，"
            f"n 只能是 1 到 {len(hits)} 之间的数字，来自下方资料。"
            "资料里没有的内容绝不能说；宁可承认不知道，也不要编造。"
            "回答简洁、口语化，像在给招聘官介绍自己。\n\n资料：\n"
            + _sources_snippet(hits)
        )
        try:
            text = _call_deepseek(system + f"\n\n问题：{question}")
        except Exception as e:
            return {"status": "error", "answer": str(e), "hits": hits}
        if not _verify_refs(text, len(hits)):
            text += "\n（注：以上部分内容未能明确溯源，请谨慎采信。）"
        return {"status": "ok", "answer": text, "hits": hits}

    # rule 驱动：拼装 + 强制标号 + 校验
    text = _rule_answer(question, hits)
    return {"status": "ok", "answer": text, "hits": hits}