#!/usr/bin/env python3
"""Rebuild V1.7.6 from the immutable previous V1.7.5 advisor + source snapshots."""
from pathlib import Path
import json
import re
ROOT=Path(__file__).resolve().parent
previous=(ROOT/"advisor_v175.html").read_text(encoding="utf-8")
radar=json.loads((ROOT/"discovery_seed.json").read_text(encoding="utf-8"))
data=json.loads((ROOT/"advisor_v16_data.json").read_text(encoding="utf-8"))
topics=json.loads((ROOT/"rag_topics_v175.json").read_text(encoding="utf-8"))
assert (len(data["sectors"]),len(data["subdomains"]),len(data["tools"]),len(data["learning"]))==(32,133,114,69)
assert len(radar["records"])==133 and all(r.get("approved") is False for r in radar["records"])
assert len(topics["concepts"])==15 and data["meta"]["ai_runtime"] is False
src=(ROOT/"advisor_v176_template.html").read_text(encoding="utf-8")
for id in ("atlas-data","atlas-intelligence","atlas-rag-topics"):
    r=re.search(fr'<script id="{id}" type="application/json">[\s\S]*?</script>',previous)
    assert r
    if id=="atlas-data":assert json.loads(r.group(0).split(">",1)[1].rsplit("</script>",1)[0])==data
    elif id=="atlas-intelligence":assert json.loads(r.group(0).split(">",1)[1].rsplit("</script>",1)[0])==radar
    elif id=="atlas-rag-topics":assert json.loads(r.group(0).split(">",1)[1].rsplit("</script>",1)[0])==topics
    slot={"atlas-data":"JSON_DATA_SLOT","atlas-intelligence":"INTELLIGENCE_DATA_SLOT","atlas-rag-topics":"RAG_TOPICS_SLOT"}[id]
    assert src.count("<!--"+slot+"-->")==1
    src=src.replace("<!--"+slot+"-->",r.group(0))
assert "V1.7.6" in src and "renderAudit()" in src
(ROOT/"advisor_v176.html").write_text(src,encoding="utf-8")
print("PASS V1.7.6 reproducible offline evidence audit desk; frozen advisors unchanged")
