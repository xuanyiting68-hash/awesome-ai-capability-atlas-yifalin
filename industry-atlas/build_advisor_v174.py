#!/usr/bin/env python3
"""Rebuild V1.7.4 from frozen V1.7.3 and the same unapproved intelligence snapshot."""
from pathlib import Path
import json, re
ROOT=Path(__file__).resolve().parent
base=(ROOT/"advisor_v173.html").read_text(encoding="utf-8")
data=json.loads((ROOT/"advisor_v16_data.json").read_text(encoding="utf-8"))
seed=(ROOT/"discovery_seed.json").read_text(encoding="utf-8")
assert (len(data["sectors"]),len(data["subdomains"]),len(data["tools"]),len(data["learning"]))==(32,133,114,69)
assert data["meta"]["ai_runtime"] is False
assert len(json.loads(seed)["records"])==133 and all(x["approved"] is False for x in json.loads(seed)["records"])
assert not re.search(r"</script",seed,re.I)
script=re.search(r'<script id="atlas-data" type="application/json">[\s\S]*?</script>',base)
assert script and json.loads(script.group(0).split(">",1)[1].rsplit("</script>",1)[0])==data
template=(ROOT/"advisor_v174_template.html").read_text(encoding="utf-8")
assert template.count("<!--JSON_DATA_SLOT-->")==template.count("<!--INTELLIGENCE_DATA_SLOT-->")==1
result=template.replace("<!--JSON_DATA_SLOT-->",script.group(0)).replace("<!--INTELLIGENCE_DATA_SLOT-->",'<script id="atlas-intelligence" type="application/json">'+seed+'</script>')
assert "V1.7.4" in result and "bridgeDismissed" in result
(ROOT/"advisor_v174.html").write_text(result,encoding="utf-8")
print("PASS V1.7.4 reproducible build; frozen V1.7.3 unchanged")
