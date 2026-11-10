#!/usr/bin/env python3
"""Rebuild V1.7.5 offline user-facing evidence UI, frozen V1.7.4 unchanged."""
from pathlib import Path
import json
import re
ROOT=Path(__file__).resolve().parent
previous=(ROOT/"advisor_v174.html").read_text(encoding="utf-8")
radar=json.loads((ROOT/"discovery_seed.json").read_text(encoding="utf-8"))
data=json.loads((ROOT/"advisor_v16_data.json").read_text(encoding="utf-8"))
topics=(ROOT/"rag_topics_v175.json").read_text(encoding="utf-8")
assert len(radar["records"])==133 and all(x.get("approved") is False for x in radar["records"])
assert len(json.loads(topics)["concepts"])==15
assert (len(data["sectors"]),len(data["subdomains"]),len(data["tools"]),len(data["learning"]))==(32,133,114,69)
assert data["meta"]["ai_runtime"] is False
assert not re.search(r"</script",topics,re.I)
baseline=re.search(r'<script id="atlas-data" type="application/json">[\s\S]*?</script>',previous)
intel=re.search(r'<script id="atlas-intelligence" type="application/json">[\s\S]*?</script>',previous)
assert baseline and intel
assert json.loads(baseline.group(0).split(">",1)[1].rsplit("</script>",1)[0]) == data
assert json.loads(intel.group(0).split(">",1)[1].rsplit("</script>",1)[0]) == radar
source=(ROOT/"advisor_v175_template.html").read_text(encoding="utf-8")
for slot in ("JSON_DATA_SLOT","INTELLIGENCE_DATA_SLOT","RAG_TOPICS_SLOT"):
    assert source.count("<!--"+slot+"-->")==1
result=(source.replace("<!--JSON_DATA_SLOT-->",baseline.group(0))
              .replace("<!--INTELLIGENCE_DATA_SLOT-->",intel.group(0))
              .replace("<!--RAG_TOPICS_SLOT-->",'<script id="atlas-rag-topics" type="application/json">'+topics+'</script>'))
assert 'V1.7.5' in result and 'mockRagReply' in result
(ROOT/"advisor_v175.html").write_text(result,encoding="utf-8")
print("PASS V1.7.5 reproducible offline build; original data and V1.7.4 preserved")
