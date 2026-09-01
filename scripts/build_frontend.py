#!/usr/bin/env python3
"""构建前端静态产物：把单文件 index.html + public 静态资源组装进 frontend/dist。

取代原来 React+Vite 的 npm run build，输出目录 frontend/dist 与 FastAPI
(backend/main.py 托管 FRONTEND_DIST)、GitHub Actions 部署路径保持一致。

用法：py -3 scripts/build_frontend.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"


def main() -> None:
    DIST.mkdir(parents=True, exist_ok=True)

    # 1. 单文件页面
    shutil.copy2(FRONTEND / "index.html", DIST / "index.html")

    # 2. public 静态资源（favicon / static-data.json 兜底数据）
    public = FRONTEND / "public"
    if public.is_dir():
        for src in public.iterdir():
            dst = DIST / src.name
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

    # 3. 保留空 assets 目录（backend/main.py 启动时会 mount /assets）
    assets = DIST / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / ".gitkeep").touch(exist_ok=True)

    files = sorted(str(p.relative_to(DIST)) for p in DIST.rglob("*") if p.is_file())
    print(f"OK: dist 就绪，共 {len(files)} 个文件")
    for f in files:
        print("  -", f)


if __name__ == "__main__":
    main()