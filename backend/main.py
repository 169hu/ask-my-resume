# 依赖：fastapi uvicorn python-frontmatter
import json
import os
from pathlib import Path

import frontmatter
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend import answer, kb

CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
REPORT_FILE = Path(__file__).resolve().parents[1] / "reports" / "eval.json"

app = FastAPI(title="ask-my-resume API", version="0.1.0")


class ChatIn(BaseModel):
    question: str


def load_project(path: Path) -> dict:
    fm = frontmatter.load(path)
    meta, body = dict(fm.metadata), (fm.content or "").strip()
    defs_ = meta.get("tech", [])
    metrics = meta.get("metrics", []) or []
    if not isinstance(metrics, list):
        metrics = []
    return {
        "title": meta.get("title", path.stem),
        "path": meta.get("path", path.stem),
        "order": meta.get("order", 999),
        "tech": defs_ if isinstance(defs_, list) else [defs_],
        "tag": meta.get("tag", ""),
        "online_demo": str(meta.get("online_demo", "")).lower() == "true",
        "demo_url": meta.get("demo_url", ""),
        "metrics": metrics,
        "highlight": meta.get("highlight", []) or [],
        "github": meta.get("github", ""),
        "summary": meta.get("title", "") + "。 " + body[:220],
        "body": body,
    }


def load_resume() -> dict:
    p = CONTENT_DIR / "resume.md"
    if not p.exists():
        return {"body": ""}
    fm = frontmatter.load(p)
    return {"meta": dict(fm.metadata), "body": (fm.content or "").strip()}


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "ask-my-resume"}


@app.get("/api/projects")
def list_projects():
    projects_dir = CONTENT_DIR / "projects"
    items = []
    for p in sorted(projects_dir.glob("*.md")):
        items.append(load_project(p))
    # 按 frontmatter 的 order 升序展示（无 order 时按文件名兜底 < 字母序）
    items.sort(key=lambda d: (int(d.get("order", 999)), d.get("path", "")))
    return {"items": items}


@app.get("/api/projects/{path}")
def project_detail(path: str):
    p = CONTENT_DIR / "projects" / f"{path}.md"
    if not p.exists():
        raise HTTPException(404, "项目不存在")
    return load_project(p)


@app.get("/api/resume")
def resume():
    return load_resume()


@app.get("/api/kb/status")
def kb_status():
    """知识库状态：chunk 数是否为 0（决定前端是否提示未建库）。"""
    try:
        return {"count": kb.get_collection().count(), "ready": True}
    except Exception as e:
        return {"count": 0, "ready": False, "error": str(e)}


@app.post("/api/chat")
def chat(payload: ChatIn):
    q = (payload.question or "").strip()
    if not q:
        raise HTTPException(400, "问题不能为空")
    # 建库懒加载：首次调用才真正编码入库
    if kb.get_collection().count() == 0:
        kb.build()
    return answer.answer(q)


@app.get("/api/eval")
def eval_report():
    """只读离线评测报告（不做实时跑分，防烧 token 后门）。"""
    if not REPORT_FILE.exists():
        return {"ready": False, "msg": "评测报告未生成，请先运行 scripts/evaluator.py"}
    return json.loads(REPORT_FILE.read_text(encoding="utf-8"))


# 托管前端构建产物（frontend/dist），SPA 回退到 index.html
if FRONTEND_DIST.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=FRONTEND_DIST / "assets"),
        name="assets",
    )

    @app.get("/{full_path:path}")
    def spa(full_path: str):
        if full_path and (FRONTEND_DIST / full_path).is_file():
            return FileResponse(FRONTEND_DIST / full_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    def root():
        return {"msg": "前端未构建，请先 npm run build"}