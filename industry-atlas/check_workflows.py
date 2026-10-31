"""Consistency, provenance and safety contracts for 64 editorial recipes."""
from pathlib import Path
import json,csv,re
R=Path(__file__).parent
w=json.loads((R/'workflows.json').read_text(encoding='utf-8'))
d=json.loads((R/'data.json').read_text(encoding='utf-8'))
ss={s['id']:s for s in d['sectors']};tt={t['id']:t for t in d['tools']};sk={s['id']:s for s in d['first_party_skills']};src={s['id']:s for s in w['sources']}
assert w['version']=='1.1.0' and len(w['workflows'])==64
assert len({r['id'] for r in w['workflows']})==64
assert {r['industry_id'] for r in w['workflows']}==set(ss)
for r in w['workflows']:
 assert r['industry']==ss[r['industry_id']]['name']
 assert r['scenario_id'] in ss[r['industry_id']]['scenarios']
 assert len(r['steps'])==5
 assert r['evidence_status']=='编辑方案 / 未进行真实业务测试'
 assert '风险' in r['risk_tier'] or '审批' in r['risk_tier'] or '人工抽查' in r['risk_tier']
 assert len(r['candidate_tools'])>=1
 for t in r['candidate_tools']:
  assert t['id'] in tt and t['url']==tt[t['id']]['url']
  assert r['scenario_id'] in tt[t['id']]['scenarios']
  assert not tt[t['id']]['industries'] or r['industry'] in tt[t['id']]['industries']
 for s in r['skill_templates']:
  assert s['id'] in sk and (R/s['path']).exists()
  assert r['scenario_id'] in sk[s['id']]['scenarios']
 assert all(k in src for k in r['sources'])
 assert all(t['url'].startswith('https://') for t in r['candidate_tools'])
assert len(list(csv.DictReader((R/'workflows.csv').open(encoding='utf-8-sig'))))==64
page=(R/'expert.html').read_text(encoding='utf-8')
assert 'type="application/json"' in page and '64' in page
assert '<script id="DATA"' in page
assert 'href="expert.html"' in (R/'index.html').read_text(encoding='utf-8')
print('PASS workflows: 64 editorial recipes, valid links/taxonomy, five-step contract, risk gates, first-party Skills, exports and source provenance')