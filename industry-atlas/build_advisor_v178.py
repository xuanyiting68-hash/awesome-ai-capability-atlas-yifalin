#!/usr/bin/env python3
"""V1.7.8 offline self-contained HTML, preserving the frozen V1.7.7 source."""
from pathlib import Path
import json,re
from coverage_review_v177 import generate_review,load_data
from sector_gap_briefs_v178 import build_gap_briefs
ROOT=Path(__file__).resolve().parent
snapshot,atlas,policy=load_data()
report=generate_review(snapshot,atlas,policy)
gaps=build_gap_briefs(snapshot,atlas,policy)
assert (report["existing_editorial_tagged_sectors"],report["proposal_only_sectors"],report["no_candidate_sectors"])==(4,8,20)
assert len(gaps["briefs"])==20 and report["automatic_promotions"]==0
prev=(ROOT/"advisor_v177.html").read_text(encoding="utf-8")
src=(ROOT/"advisor_v178_template.html").read_text(encoding="utf-8")
expected={"atlas-data":atlas,"atlas-intelligence":snapshot,
          "atlas-rag-topics":json.loads((ROOT/"rag_topics_v175.json").read_text(encoding="utf-8")),
          "atlas-coverage-rules":policy}
for id,slot in (("atlas-data","JSON_DATA_SLOT"),("atlas-intelligence","INTELLIGENCE_DATA_SLOT"),
                ("atlas-rag-topics","RAG_TOPICS_SLOT"),("atlas-coverage-rules","COVERAGE_RULES_SLOT")):
    m=re.search(fr'<script id="{id}" type="application/json">[\s\S]*?</script>',prev)
    assert m and json.loads(m.group(0).split(">",1)[1].rsplit("</script>",1)[0])==expected[id]
    assert src.count("<!--"+slot+"-->")==1
    src=src.replace("<!--"+slot+"-->",m.group(0))
assert 'V1.7.8' in src and 'coverageGapText()' in src and 'coveragePageHtml(' in src
(ROOT/"advisor_v178.html").write_text(src,encoding="utf-8")
print("PASS V1.7.8 deterministic paged review & missing-sector research workspace")
