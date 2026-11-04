#!/usr/bin/env python3
"""Regenerate V1.7.3 from frozen V1.7 and existing unapproved radar seed (no network)."""
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parent
base = (ROOT / "advisor_v17.html").read_text(encoding="utf-8")
data = json.loads((ROOT / "advisor_v16_data.json").read_text(encoding="utf-8"))
seed = (ROOT / "discovery_seed.json").read_text(encoding="utf-8")
records = json.loads(seed)["records"]
assert (len(data["sectors"]), len(data["subdomains"]), len(data["tools"]), len(data["learning"])) == (32, 133, 114, 69)
assert len(records) == 133 and all(r.get("approved") is False for r in records)
assert data["meta"]["ai_runtime"] is False
assert not re.search(r"</script", seed, re.I), "Unsafe embedded metadata"
script = re.search(r'<script id="atlas-data" type="application/json">[\s\S]*?</script>', base)
assert script and json.loads(script.group(0).split(">", 1)[1].rsplit("</script>", 1)[0]) == data
template = (ROOT / "advisor_v173_template.html").read_text(encoding="utf-8")
assert template.count("<!--JSON_DATA_SLOT-->") == template.count("<!--INTELLIGENCE_DATA_SLOT-->") == 1
result = template.replace("<!--JSON_DATA_SLOT-->", script.group(0)).replace(
    "<!--INTELLIGENCE_DATA_SLOT-->", '<script id="atlas-intelligence" type="application/json">' + seed + '</script>')
assert "renderBridge" in result and "V1.7.3" in result
(ROOT / "advisor_v173.html").write_text(result, encoding="utf-8")
print("PASS V1.7.3 self-contained build; frozen V1.7, tool catalog and discovery governance untouched")
