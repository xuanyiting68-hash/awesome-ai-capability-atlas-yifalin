#!/usr/bin/env python3
"""V1.8.1 reproducible advisor: selected supply-chain evidence, original data frozen."""
from pathlib import Path
import json,re
from coverage_review_v177 import load_data
from supply_chain_review_v181 import build_report
ROOT=Path(__file__).resolve().parent
snapshot,atlas,rules=load_data()
leads=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
licenses=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
supply_txt=(ROOT/"supply_chain_evidence_v181.json").read_text(encoding="utf-8")
supply=json.loads(supply_txt)
report=build_report(supply,leads,licenses,snapshot,atlas,rules)
assert report["projects"]==10 and report["cve_scans_completed"]==0 and report["security_approvals"]==0
prev=(ROOT/"advisor_v180.html").read_text(encoding="utf-8")
src=(ROOT/"advisor_v181_template.html").read_text(encoding="utf-8")
lookup={"atlas-data":atlas,"atlas-intelligence":snapshot,
        "atlas-rag-topics":json.loads((ROOT/"rag_topics_v175.json").read_text(encoding="utf-8")),
        "atlas-coverage-rules":rules,"atlas-external-leads":leads,"atlas-license-files":licenses}
for id,slot in (("atlas-data","JSON_DATA_SLOT"),("atlas-intelligence","INTELLIGENCE_DATA_SLOT"),
                ("atlas-rag-topics","RAG_TOPICS_SLOT"),("atlas-coverage-rules","COVERAGE_RULES_SLOT"),
                ("atlas-external-leads","EXTERNAL_LEADS_SLOT"),("atlas-license-files","LICENSE_FILES_SLOT")):
    x=re.search(fr'<script id="{id}" type="application/json">[\s\S]*?</script>',prev)
    assert x and json.loads(x.group(0).split(">",1)[1].rsplit("</script>",1)[0])==lookup[id]
    assert src.count("<!--"+slot+"-->")==1
    src=src.replace("<!--"+slot+"-->",x.group(0))
assert src.count("<!--SUPPLY_CHAIN_SLOT-->")==1 and "</script" not in supply_txt.lower()
src=src.replace("<!--SUPPLY_CHAIN_SLOT-->",'<script id="atlas-supply-chain" type="application/json">'+supply_txt+'</script>')
assert "V1.8.1" in src and "SUPPLY_BY_ID" in src
(ROOT/"advisor_v181.html").write_text(src,encoding="utf-8")
print("PASS V1.8.1 reproducible supply-chain file evidence UI, 0 CVE scans, 0 approvals")
