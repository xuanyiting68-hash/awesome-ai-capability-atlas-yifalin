#!/usr/bin/env python3
"""Rebuild the V1.7 self-contained advisor from the *unchanged* V1.6 editorial snapshot.

The authoritative 32/133/114/69 dataset stays owned by build_advisor_v16.py.
V1.7 changes presentation, not evidence classifications or model availability.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "advisor_v16.html"
TEMPLATE = ROOT / "advisor_v17_template.html"
TARGET = ROOT / "advisor_v17.html"
data = json.loads((ROOT / "advisor_v16_data.json").read_text(encoding="utf-8"))
assert (len(data["sectors"]), len(data["subdomains"]), len(data["tools"]), len(data["learning"])) == (32, 133, 114, 69)
assert data["meta"]["ai_runtime"] is False
html16 = SOURCE.read_text(encoding="utf-8")
match = re.search(r'<script id="atlas-data" type="application/json">[\s\S]*?</script>', html16)
assert match, "Missing V1.6 embedded dataset; rebuild V1.6 first"
embedded = re.search(r">([\s\S]*?)</script>", match.group(0)).group(1)
assert json.loads(embedded) == data, "V1.6 data snapshot differs from built page"
template = TEMPLATE.read_text(encoding="utf-8")
assert template.count("<!--JSON_DATA_SLOT-->") == 1
result = template.replace("<!--JSON_DATA_SLOT-->", match.group(0))
assert 'AI 行业工作台 V1.7' in result and len(result) > 180_000
TARGET.write_text(result, encoding="utf-8")
print("PASS V1.7 reproducible build, original V1.6 evidence snapshot unchanged")
