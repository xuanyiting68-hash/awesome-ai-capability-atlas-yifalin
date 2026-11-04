#!/usr/bin/env python3
"""Build V1.7.7 static Atlas coverage desk from frozen v1.7.6 and review-only rules."""
from pathlib import Path
import json, re
from coverage_review_v177 import generate_review, load_data
ROOT=Path(__file__).resolve().parent
snapshot,atlas,policy=load_data()
report=generate_review(snapshot,atlas,policy)
assert report["total_records"]==133 and report["without_declared_industry"]==69
assert report["automatic_promotions"]==report["real_source_checks"]==0
assert (len(atlas["sectors"]),len(atlas["subdomains"]),len(atlas["tools"]),len(atlas["learning"]))==(32,133,114,69)
base=(ROOT/"advisor_v176.html").read_text(encoding="utf-8")
src=(ROOT/"advisor_v177_template.html").read_text(encoding="utf-8")
for key,slot,want in (
    ("atlas-data","JSON_DATA_SLOT",atlas),
    ("atlas-intelligence","INTELLIGENCE_DATA_SLOT",snapshot),
    ("atlas-rag-topics","RAG_TOPICS_SLOT",json.loads((ROOT/"rag_topics_v175.json").read_text(encoding="utf-8"))),
):
    x=re.search(fr'<script id="{key}" type="application/json">[\s\S]*?</script>',base)
    assert x and json.loads(x.group(0).split(">",1)[1].rsplit("</script>",1)[0])==want
    assert src.count("<!--"+slot+"-->")==1
    src=src.replace("<!--"+slot+"-->",x.group(0))
rules=(ROOT/"coverage_review_rules_v177.json").read_text(encoding="utf-8")
assert src.count("<!--COVERAGE_RULES_SLOT-->")==1
assert "</script" not in rules.lower()
src=src.replace("<!--COVERAGE_RULES_SLOT-->",'<script id="atlas-coverage-rules" type="application/json">'+rules+'</script>')
assert 'V1.7.7' in src and 'function renderCoverage()' in src
(ROOT/"advisor_v177.html").write_text(src,encoding="utf-8")
print("PASS V1.7.7 reproducible coverage UI: frozen snapshots, 0 approvals")
