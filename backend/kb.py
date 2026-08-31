"""ask-my-resume 知识库：把 content/ 下的项目与简历语料分块向量化入 Chroma，并提供检索。

设计要点（对应方案"无来源不答"）：
- 一次只做一件事：build() 建库，search() 检索，互不绑定。
- chunk 的 metadata 固定带 source（项目名 / resume），供前端引用标号点击。
- Chroma 用 cosine 空间（中文检索，和 M1 验证一致）。
- 检索返回 sim = 1 - distance 归一化分数。
"""
from pathlib import Path
import os
import re

# 说明：默认不强制离线。本地开发可在 shell 里设置 HF_HUB_OFFLINE=1（模型已缓存时更快）。
# Streamlit Cloud 首次部署需要联网下载 bge-small-zh-v1.5，因此不能写死 OFFLINE=1。
# 为避免 HuggingFace 官方域名下载慢/失败，默认走镜像。
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
# 也允许调用方显式设置 OFFLINE（例如 streamlit_app.py 在本地跑时会改成 0/1）。

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
CHROMA_DIR = ROOT / "data" / "chroma"
COLLECTION = "ask_kb"
MODEL = "BAAI/bge-small-zh-v1.5"
# 注意：sentence_transformers / chromadb 均延迟到 get_model()/get_client() 内导入。
# 原因详见 get_model：云端缺 torch/torchvision 时，顶层导入会使整个 Streamlit 应用崩掉。

# 查询侧指令前缀（v1.5 已放宽，M1 验证"不加前缀"区分度更高，故不启用）
# QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："

_model = None
_client = None
_collection = None


def get_model():  # -> SentenceTransformer（延迟导入，避免顶层 import 拖崩云端）
    global _model
    if _model is None:
        # 延迟导入：云端若缺少 torch/torchvision 等重型依赖，只有真正请求模型下载/
        # 向量化时才失败，查询链路会走到 search() 的关键词粗排兜底，页面不会整体崩。
        from sentence_transformers import SentenceTransformer
        # HF_HUB_OFFLINE=1 时走本地缓存；否则允许联网（Streamlit Cloud 首次部署需要）。
        offline = os.environ.get("HF_HUB_OFFLINE", "0") in ("1", "true", "True", "yes")
        _model = SentenceTransformer(MODEL, local_files_only=offline)
    return _model


def get_client():
    global _client
    if _client is None:
        import chromadb  # 延迟导入：避免云端缺重型依赖时顶层 import 把整个 app 拖崩
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def get_collection():
    global _collection, _client
    if _collection is None:
        c = get_client()
        _collection = c.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"})
    return _collection


def _split_sentences(text: str, chunk=220) -> list[str]:
    """按句号切分并合并到接近 chunk 长度，保留语义完整。"""
    parts = re.split(r"(?<=[。！？；\n])", text)
    chunks, cur = [], ""
    for p in parts:
        p = p.strip()
        if not p:
            continue
        cur += p
        if len(cur) >= chunk:
            chunks.append(cur)
            cur = ""
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c]


def _project_chunks() -> list[dict]:
    """把 content/projects/*.md 切成带 source 的 chunk。"""
    items = []
    for p in sorted((CONTENT_DIR / "projects").glob("*.md")):
        meta = _parse_frontmatter(p.read_text(encoding="utf-8"))
        source = meta.get("path", p.stem)
        for i, c in enumerate(_split_sentences(_strip_frontmatter(p))):
            items.append({"source": source, "text": c, "idx": i})
    return items


def _resume_chunks() -> list[dict]:
    p = CONTENT_DIR / "resume.md"
    if not p.exists():
        return []
    items = []
    for i, c in enumerate(_split_sentences(_strip_frontmatter(p))):
        items.append({"source": "resume", "text": c, "idx": i})
    return items


def _parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def _strip_frontmatter(p: Path) -> str:
    text = p.read_text(encoding="utf-8")
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.S).strip()


def build() -> int:
    """把全部语料向量化入库，返回 chunk 总数。"""
    chunks = _project_chunks() + _resume_chunks()
    if not chunks:
        return 0
    model = get_model()
    col = get_collection()
    # 幂等：清空重建
    try:
        col.delete(where={})
    except Exception:
        pass
    docs = [c["text"] for c in chunks]
    embs = model.encode(docs, normalize_embeddings=True).tolist()
    col.add(
        ids=[f"{c['source']}::{c['idx']}" for c in chunks],
        embeddings=embs,
        documents=docs,
        metadatas=[{"source": c["source"]} for c in chunks],
    )
    return len(chunks)


def search(query: str, n=4, min_sim: float = 0.0) -> list[dict]:
    """向量检索：返回按 sim 降序的命中（sim = 1 - distance）。

    兼容策略：
      - 优先使用本地向量化的 bge-small-zh-v1.5。
      - 若模型下载/加载失败（典型 Streamlit Cloud 无 HF 网络的情况），退化做
       「包含关键词的文档按命中条数粗排」兜底返回，避免整个问答功能挂掉。
    """
    col = get_collection()
    if not col.count():
        return []

    try:
        model = get_model()
        q_emb = model.encode([query], normalize_embeddings=True).tolist()
        res = col.query(query_embeddings=q_emb, n_results=n)
        out = []
        for doc, dist, meta in zip(
                res["documents"][0], res["distances"][0], res["metadatas"][0]):
            sim = 1 - dist
            if sim >= min_sim:
                out.append({
                    "text": doc,
                    "sim": round(sim, 4),
                    "source": (meta or {}).get("source", ""),
                })
        return out
    except Exception:
        # Fallback：把库里所有文档拿出来，按「查询词里单字/词组命中」做粗打分。
        # 仅在向量检索链路完全不可用时走，避免因为模型下载不到就 0 结果导致全拒答。
        all_docs = col.get(include=["documents", "metadatas"])
        ids = all_docs.get("ids") or []
        docs = all_docs.get("documents") or []
        metas = all_docs.get("metadatas") or []
        if not docs:
            return []

        # 把查询拆成 1-gram + 2-gram token
        q = query.strip()
        tokens = set(q) | {q[i:i + 2] for i in range(len(q) - 1)}
        scored = []
        for doc, meta in zip(docs, metas):
            if not doc:
                continue
            hits = sum(1 for t in tokens if t and t in doc)
            if hits <= 0:
                continue
            # 归一化成 0-1：命中 token 数 / (token 总数 + 1)，避免除以 0
            sim = min(0.99, hits / (len(tokens) + 1))
            scored.append((sim, doc, (meta or {}).get("source", "")))
        scored.sort(key=lambda x: -x[0])
        return [
            {"text": d, "sim": round(s, 4), "source": src}
            for s, d, src in scored[:n]
        ]


if __name__ == "__main__":
    print("建库 chunk 数:", build())
    for _q in ["项目里怎么防止 AI 乱操作？", "候选人的婚礼在哪办的？"]:
        print(f"\n[{_q}]")
        for hit in search(_q):
            print(f"  sim={hit['sim']:.3f} src={hit['source']}  {hit['text'][:40]}")