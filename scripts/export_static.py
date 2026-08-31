#!/usr/bin/env python3
"""导出静态数据快照，供 GitHub Pages 等纯静态托管使用。

后端 API 不可用时，前端降级读取 frontend/public/static-data.json，
内容结构与 /api/projects /api/resume /api/eval 对齐。

用法：py -3 scripts/export_static.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_DIR = ROOT / "content"
PROJECTS_DIR = CONTENT_DIR / "projects"
REPORT_FILE = ROOT / "reports" / "eval.json"
OUT = ROOT / "frontend" / "public" / "static-data.json"

try:
    import frontmatter
except ImportError:
    print("缺少依赖：pip install python-frontmatter")
    sys.exit(1)


def load_project(path: Path) -> dict:
    fm = frontmatter.load(path)
    meta, body = dict(fm.metadata), (fm.content or "").strip()
    tech = meta.get("tech", [])
    metrics = meta.get("metrics", []) or []
    if not isinstance(metrics, list):
        metrics = []
    return {
        "title": meta.get("title", path.stem),
        "path": meta.get("path", path.stem),
        "order": meta.get("order", 999),
        "tech": tech if isinstance(tech, list) else [tech],
        "tag": meta.get("tag", ""),
        "online_demo": str(meta.get("online_demo", "")).lower() == "true",
        "demo_url": meta.get("demo_url", ""),
        "metrics": metrics,
        "highlight": meta.get("highlight", []) or [],
        "github": meta.get("github", ""),
        "summary": meta.get("title", "") + "。 " + body[:220],
        "body": body,
    }


def main() -> None:
    items = []
    for p in sorted(PROJECTS_DIR.glob("*.md")):
        items.append(load_project(p))
    items.sort(key=lambda d: (int(d.get("order", 999)), d.get("path", "")))

    resume = ""
    rp = CONTENT_DIR / "resume.md"
    if rp.exists():
        fm = frontmatter.load(rp)
        resume = (fm.content or "").strip()

    eval_report = None
    if REPORT_FILE.exists():
        eval_report = json.loads(REPORT_FILE.read_text(encoding="utf-8"))

    # 由 ask-my-resume 的 GitHub 仓库地址推导项目演示仓库链接
    github_root = "https://github.com/169hu"
    for it in items:
        it["github_href"] = it.get("github") or f"{github_root}/{it['path']}"

    snapshot = {"projects": items, "resume": resume, "eval": eval_report}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {OUT} ({len(items)} projects, resume {len(resume)} chars, eval={'yes' if eval_report else 'no'})")


if __name__ == "__main__":
    main()