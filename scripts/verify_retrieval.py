#!/usr/bin/env python3
"""M1 · 验证 bge-small-zh-v1.5 中文检索区分度（跑通即过 M1 检索验证）。

三个必踩的坑已在脚本里绕开：
  1. Chroma 用 cosine 距离空间（默认 l2）
  2. bge 查询侧指令前缀（v1.5 可放宽，故再加一组"不加前缀"对照）
  3. Chroma 返回的是 distance，越小越相似 → 打印 sim = 1 - dist

验收标准：该命中组 top1 的 sim 明显高于该拒答组的最高分
（例如 0.65+ vs 0.45-）。两种前缀都测，选区分度高的。
"""
from sentence_transformers import SentenceTransformer
import chromadb

MODEL = "BAAI/bge-small-zh-v1.5"
PREFIX = "为这个句子生成表示以用于检索相关文章："

docs = [
    "OpsPilot 是运维工单 Agent，LangGraph 编排，红线门禁 100% 拦截危险操作。",
    "agenthub 多 Agent 协作调度，FastAPI 后端，React 前端。",
    "legal-assistant 基于 RAG 的法律问答，检索法条并附来源。",
]


def main():
    print("加载模型:", MODEL)
    model = SentenceTransformer(MODEL)
    doc_emb = model.encode(docs, normalize_embeddings=True)

    client = chromadb.Client()
    col = client.create_collection("kb_tmp", metadata={"hnsw:space": "cosine"})
    col.add(ids=[str(i) for i in range(len(docs))],
            embeddings=doc_emb.tolist(), documents=docs)

    cases = [
        ("该命中", "项目里怎么防止 AI 乱操作？"),
        ("该拒答", "候选人的婚礼在哪办的？"),
    ]

    for use_prefix in (True, False):
        print("\n======== 查询侧指令前缀:", "加" if use_prefix else "不加",
              "========")
        for label, q in cases:
            q_text = PREFIX + q if use_prefix else q
            q_emb = model.encode([q_text], normalize_embeddings=True)
            res = col.query(query_embeddings=q_emb.tolist(), n_results=3)
            print(f"--- [{label}]: {q}")
            for doc, dist in zip(res["documents"][0], res["distances"][0]):
                print(f"    sim={1 - dist:.3f}  {doc[:36]}")


if __name__ == "__main__":
    main()