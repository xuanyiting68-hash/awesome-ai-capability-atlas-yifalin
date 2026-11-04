#!/usr/bin/env python3
"""V1.7.9 reproducible self-contained offline review UI over immutable earlier Atlas."""
from pathlib import Path
import json, re
from coverage_review_v177 import generate_review,load_data
from sector_gap_briefs_v178 import build_gap_briefs
from external_leads_v179 import make_review_report
ROOT=Path(__file__).resolve().parent
snap,atlas,rules=load_data()
prior=(ROOT/"advisor_v178.html").read_text(encoding="utf-8")
template=(ROOT/"advisor_v179_template.html").read_text(encoding="utf-8")
ledger_txt=(ROOT/"external_leads_v179.json").read_text(encoding="utf-8")
ledger=json.loads(ledger_txt)
report=make_review_report(ledger,snap,atlas,rules)
assert report["source_leads"]==10 and report["approved_source_count"]==0 and report["frozen_radar_sources_added"]==0
assert build_gap_briefs(snap,atlas,rules)["no_candidate_sectors"]==20
source_keys={
    "atlas-data":(atlas,"JSON_DATA_SLOT"),
    "atlas-intelligence":(snap,"INTELLIGENCE_DATA_SLOT"),
    "atlas-rag-topics":(json.loads((ROOT/"rag_topics_v175.json").read_text(encoding="utf-8")),"RAG_TOPICS_SLOT"),
    "atlas-coverage-rules":(rules,"COVERAGE_RULES_SLOT"),
}
for id,(expected,slot) in source_keys.items():
    found=re.search(fr'<script id="{id}" type="application/json">[\s\S]*?</script>',prior)
    assert found and json.loads(found.group(0).split(">",1)[1].rsplit("</script>",1)[0])==expected
    assert template.count("<!--"+slot+"-->")==1
    template=template.replace("<!--"+slot+"-->",found.group(0))
assert template.count("<!--EXTERNAL_LEADS_SLOT-->")==1 and "</script" not in ledger_txt.lower()
template=template.replace("<!--EXTERNAL_LEADS_SLOT-->",'<script id="atlas-external-leads" type="application/json">'+ledger_txt+'</script>')
assert "V1.7.9" in template and "renderExternal()" in template and "externalChecklist()" in template
(ROOT/"advisor_v179.html").write_text(template,encoding="utf-8")
print("PASS V1.7.9 reproducible 10-source metadata review, 0 approvals, preserved 20 frozen radar gaps")
