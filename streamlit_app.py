"""ask-my-resume 的 Streamlit 部署入口。

对外：一个简洁的「简历问答」Demo 页，HR 打开即可直接提问。
对内：
- 从 Streamlit Secrets（或本地 .env）读取 LLM 配置并注入环境变量。
- 若 chroma 向量库缺失/为空，会在首次启动时自动扫描 content/*.md 重新建库。
- 默认使用 rule 驱动（无需任何 API Key 即可跑通展示）；Secrets 提供了 Key 时自动切换到 deepseek。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import streamlit as st

# ---- 路径：让 backend.* 包可被 import ----
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---- 1) 把 Streamlit Secrets 注入环境变量（保持 answer/kb 代码零改动） ----
_SECRETS_MAP = {
    "DEEPSEEK_API_KEY": "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL": "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL": "DEEPSEEK_MODEL",
    "LLM_DRIVER": "LLM_DRIVER",
    "ACCEPT_SIM": "ACCEPT_SIM",
}

# Streamlit 运行时：st.secrets 总是可用（没有 secrets.toml 则为空 dict）
try:
    for env_key, secret_key in _SECRETS_MAP.items():
        val = st.secrets.get(secret_key) if hasattr(st, "secrets") else None
        if val and not os.environ.get(env_key):
            os.environ[env_key] = str(val)
except Exception:
    pass  # Secrets 读取失败不阻塞，回退到默认值

# 用户未显式配置 LLM_DRIVER 时：有 key → deepseek，否则 → rule
if "LLM_DRIVER" not in os.environ:
    os.environ["LLM_DRIVER"] = "deepseek" if os.environ.get("DEEPSEEK_API_KEY") else "rule"

# Streamlit Cloud 首次部署：本地没有缓存的 embedding 模型，需要允许联网下载。
# 本地开发时保持默认（不强制覆盖已有 HF_HUB_OFFLINE 环境变量）。
os.environ.setdefault("HF_HUB_OFFLINE", "0")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")

from backend import kb, answer  # noqa: E402  (必须在路径/环境变量就绪后再导入)

# ---- 2) 首次启动：向量库不存在则自动重建 ----
@st.cache_resource(show_spinner=False)
def _ensure_kb(attempt_rebuild: bool = True) -> int:
    """确保知识库可用；返回当前 chunk 数（0 表示空/失败）。

    设计：
      - 若仓库里已带 data/chroma（生产部署默认情况）：直接返回已入库的 chunk 数，
        全程不触发 SentenceTransformer 模型下载/加载。
      - 若库为空：尝试 kb.build()；失败（例如云端无 HuggingFace 网络）时吞异常，
        由 search() 内部走「关键词粗排兜底」，整个页面仍然可用。
    """
    col = kb.get_collection()
    n = col.count()
    if n > 0:
        return n
    if not attempt_rebuild:
        return 0
    try:
        return kb.build()
    except Exception as e:  # 模型下载/向量化失败
        st.warning(
            f"首次自动建库未成功（{e}）。聊天仍可用：已自动切换到「关键词检索兜底」，"
            f"如需完整向量检索质量，请在 Streamlit Secrets 里确保服务器可访问 HuggingFace，"
            f"或本地跑一次 `python -m backend.kb` 后把 data/chroma 提交到仓库。"
        )
        return 0

# ---- 3) 页面 UI ----
st.set_page_config(
    page_title="简历问答 · 胡进林",
    page_icon="📝",
    layout="centered",
)

st.title("📝 简历问答")
st.caption(
    "我是胡进林的求职辅助 AI，基于真实简历与项目资料做带引用的回答。"
    " 来源之外的内容我不会编造。"
)

# 侧边栏：展示当前运行模式 / 驱动信息
with st.sidebar:
    st.subheader("运行信息")
    n_chunks = _ensure_kb()
    driver = os.environ.get("LLM_DRIVER", "rule")
    st.info(f"当前驱动：**{driver}**\n\n知识块：{n_chunks}")
    if driver == "rule":
        st.warning(
            "rule 模式：纯检索拼装，用于「无 API Key 也能演示」。"
            " 在 Streamlit Secrets 里填入 `DEEPSEEK_API_KEY` 即可自动启用 LLM 润色。"
        )
    st.markdown("---")
    st.markdown(
        "**硬约束**\n"
        "- 相似度 < 0.45 → 拒答/反问\n"
        "- 注入意图 → 直接拦截\n"
        "- 每个论点必须带可追溯的 [n] 引用"
    )
    if st.button("重建知识库"):
        try:
            # 强制跳过 cache_resource：直接调用 build
            n = kb.build()
            st.success(f"重建完成，共 {n} 条。")
        except Exception as e:
            st.error(str(e))

# 聊天区
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": "你好！可以问我：「你做过哪些项目？」「RAG 怎么防幻觉？」「微调踩过什么坑？」"}
    ]

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        for h in m.get("hits", []):
            with st.expander(f"🔗 [{h.get('source','?')}] sim={h.get('sim',0):.2f}"):
                st.write(h.get("text", ""))

if prompt := st.chat_input("请输入你的问题…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("检索中…" if driver == "rule" else "检索 + LLM 生成中…"):
            resp = answer.answer(prompt)
        status = resp.get("status", "error")
        body = resp.get("answer", "")
        hits = resp.get("hits", [])

        if status == "ok":
            st.markdown(body)
        elif status == "reject":
            st.info(body)
        else:
            st.error(body)

        for h in hits:
            with st.expander(f"🔗 [{h.get('source','?')}] sim={h.get('sim',0):.2f}"):
                st.write(h.get("text", ""))

    st.session_state.messages.append(
        {"role": "assistant", "content": body, "hits": hits}
    )
