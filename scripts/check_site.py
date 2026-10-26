#!/usr/bin/env python3
"""Static front-end test for inline JavaScript and catalog invariants."""
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/"index.html").read_text("utf-8")
assert html.count("<script>")==1 and html.count("</script>")==1
scripts=re.findall(r"<script>([\s\S]*?)</script>",html)
assert len(scripts)==1
assert "renderRepoMeta" in scripts[0]
assert "data/repo_metadata.json" in html
assert "escapeHTML" in scripts[0]
assert "GitHub Stars" in html
with tempfile.TemporaryDirectory() as directory:
    path=Path(directory)/"site.js"
    path.write_text(scripts[0],"utf-8")
    subprocess.run(["node","--check",str(path)],check=True)
rows=json.loads((ROOT/"data"/"curated.json").read_text("utf-8"))
assert len(rows)==133
assert len({r["url"] for r in rows})==133
print("PASS: JavaScript syntax, 133 distinct curated records, metadata features")
