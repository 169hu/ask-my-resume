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

# 强制离线：模型已缓存到本地，联网校验会因无外网而超时卡住（见"教训"）
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer
import chromadb

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
CHROMA_DIR = ROOT / "data" / "chroma"
COLLECTION = "ask_kb"
MODEL = "BAAI/bge-small-zh-v1.5"

# 查询侧指令前缀（v1.5 已放宽，M1 验证"不加前缀"区分度更高，故不启用）
# QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："

_model = None
_client = None
_collection = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL, local_files_only=True)
    return _model


def get_client():
    global _client
    if _client is None:
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
    """向量检索：返回按 sim 降序的命中（sim = 1 - distance）。"""
    if not get_collection().count():
        return []
    model = get_model()
    q_emb = model.encode([query], normalize_embeddings=True).tolist()
    res = get_collection().query(
        query_embeddings=q_emb, n_results=n)
    out = []
    for doc, dist, meta in zip(
            res["documents"][0], res["distances"][0], res["metadatas"][0]):
        sim = 1 - dist
        out.append({
            "text": doc,
            "sim": round(sim, 4),
            "source": (meta or {}).get("source", ""),
        })
    return out


if __name__ == "__main__":
    print("建库 chunk 数:", build())
    for _q in ["项目里怎么防止 AI 乱操作？", "候选人的婚礼在哪办的？"]:
        print(f"\n[{_q}]")
        for hit in search(_q):
            print(f"  sim={hit['sim']:.3f} src={hit['source']}  {hit['text'][:40]}")