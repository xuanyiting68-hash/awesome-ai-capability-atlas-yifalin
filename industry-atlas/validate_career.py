"""Strict first-party V1.2 role/learning migration data contract. Does not attest job market demand."""
from pathlib import Path
import json,re
P=Path(__file__).resolve().parent
d=json.loads((P/"careers.json").read_text(encoding="utf-8"))
core=json.loads((P/"data.json").read_text(encoding="utf-8"))
checks=dict(sectors=32,skill_taxonomy=22,current_roles=225,emerging_roles=50,learning_resources=69,migration_routes=675)
for k,n in checks.items(): assert len(d[k])==n,(k,len(d[k]),n)
ids={x["id"] for x in d["current_roles"]}; targets={x["id"] for x in d["emerging_roles"]}; skills={x["id"] for x in d["skill_taxonomy"]}; knowledge={x["id"] for x in d["learning_resources"]}
assert len(ids)==225 and len(targets)==50
assert len({r["id"] for r in d["migration_routes"]})==675
assert {s["id"] for s in d["sectors"]}=={s["id"] for s in core["sectors"]}
for r in d["current_roles"]: assert r["industry_id"] in {s["id"] for s in d["sectors"]} and set(r["current_skills"])<=skills
for r in d["emerging_roles"]:
 assert r["skills"] and set(r["skills"])<=skills and r["status_code"] in ("emerging","hypothesis")
 assert r["vacancies"]=="未核验" and r["salary"]=="未核验"
for r in d["learning_resources"]:
 assert r["url"].startswith("https://") and set(r["skills"])<=skills
 assert "未逐课实测" in r["verification"]
for r in d["migration_routes"]:
 assert r["from_role"] in ids and r["to_role"] in targets
 assert len(r["weeks_4"])==4 and set(r["learning_ids"])<=knowledge
 assert len(r["shared_skills"])<=5
html=(P/"career.html").read_text(encoding="utf-8")
match=re.search(r'<script id="CAREER_DATA" type="application/json">(.*?)</script>',html,re.S)
assert match
inline=json.loads(match.group(1).replace("<\\/","</"))
assert inline==d,"HTML embedded data must match careers.json"
for fname in ("index.html","expert.html"): assert 'href="career.html"' in (P/fname).read_text(encoding="utf-8"),fname
print("PASS V1.2 career integrity: 225 roles, 50 emerging, 22 competencies, 69 learning entries, 675 routes")
