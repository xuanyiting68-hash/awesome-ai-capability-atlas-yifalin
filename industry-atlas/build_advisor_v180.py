#!/usr/bin/env python3
"""V1.8.0 immutable-page reproducible embed of read-only license file observations."""
from pathlib import Path
import json,re
from coverage_review_v177 import load_data
from external_leads_v179 import make_review_report
from license_evidence_v180 import build_license_report
ROOT=Path(__file__).resolve().parent
snapshot,atlas,rules=load_data()
leads_txt=(ROOT/"external_leads_v179.json").read_text(encoding="utf-8")
files_txt=(ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8")
leads,files=json.loads(leads_txt),json.loads(files_txt)
report=build_license_report(files,leads,snapshot,atlas,rules)
assert report["files_observed"]==10 and report["needs_signal_reconciliation"]==2 and report["legal_licenses_verified"]==0
assert make_review_report(leads,snapshot,atlas,rules)["source_gap_sectors_in_frozen_radar"]==20
prev=(ROOT/"advisor_v179.html").read_text(encoding="utf-8")
src=(ROOT/"advisor_v180_template.html").read_text(encoding="utf-8")
old={"atlas-data":atlas,"atlas-intelligence":snapshot,
     "atlas-rag-topics":json.loads((ROOT/"rag_topics_v175.json").read_text(encoding="utf-8")),
     "atlas-coverage-rules":rules,"atlas-external-leads":leads}
for id,slot in (("atlas-data","JSON_DATA_SLOT"),("atlas-intelligence","INTELLIGENCE_DATA_SLOT"),
                ("atlas-rag-topics","RAG_TOPICS_SLOT"),("atlas-coverage-rules","COVERAGE_RULES_SLOT"),
                ("atlas-external-leads","EXTERNAL_LEADS_SLOT")):
    r=re.search(fr'<script id="{id}" type="application/json">[\s\S]*?</script>',prev)
    assert r and json.loads(r.group(0).split(">",1)[1].rsplit("</script>",1)[0])==old[id]
    assert src.count("<!--"+slot+"-->")==1
    src=src.replace("<!--"+slot+"-->",r.group(0))
assert src.count("<!--LICENSE_FILES_SLOT-->")==1 and "</script" not in files_txt.lower()
src=src.replace("<!--LICENSE_FILES_SLOT-->",'<script id="atlas-license-files" type="application/json">'+files_txt+'</script>')
assert "V1.8.0" in src and "LICENSE_BY_ID" in src
(ROOT/"advisor_v180.html").write_text(src,encoding="utf-8")
print("PASS V1.8.0 reproducible file evidence UI; 2 license flags, 0 approvals")
