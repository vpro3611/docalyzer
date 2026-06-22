from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from docalyzer.file_loaders import SUPPORTED_EXTENSIONS, load_file

CHECK_DIR = ROOT / "check"
CHECK_DIR.mkdir(exist_ok=True)

results = []

for ext in SUPPORTED_EXTENSIONS:
    name = f"w{ext}"
    path = CHECK_DIR / name
    created = False
    # create simple placeholder files for text-like extensions
    if not path.exists():
        if ext in (".txt", ".md", ".py", ".js", ".java", ".cpp", ".html", ".csv", ".ipynb"):
            if ext == ".ipynb":
                content = '{"cells": [{"cell_type": "markdown", "source": ["# Notebook"], "metadata": {}}], "metadata": {}, "nbformat": 4, "nbformat_minor": 2}'
                path.write_text(content, encoding="utf-8")
            else:
                path.write_text(f"Sample content for {name}\nLine two.", encoding="utf-8")
            created = True
        else:
            # create an empty binary placeholder
            path.write_bytes(b"")
            created = True

    try:
        text = load_file(path)
        results.append((ext, "ok", len(text), text[:200]))
    except Exception as e:
        results.append((ext, "error", type(e).__name__, str(e)))

print("Loader check report:\n")
for ext, status, a, b in results:
    if status == "ok":
        print(f"{ext}: OK — {a} chars; preview: {repr(b[:120])}")
    else:
        print(f"{ext}: ERROR — {a}: {b}")

# exit status 0 if all ok, otherwise 2
if all(r[1] == "ok" for r in results):
    raise SystemExit(0)
else:
    raise SystemExit(2)
