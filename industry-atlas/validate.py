"""Fail-closed static contract validation; Python stdlib only."""
from pathlib import Path
import json,csv
R=Path(__file__).parent
d=json.loads((R/'data.json').read_text(encoding='utf-8'))
g=json.loads((R/'graph.json').read_text(encoding='utf-8'))
w=json.loads((R/'workflows.json').read_text(encoding='utf-8'))
assert len(d['sectors'])==32 and len(d['scenarios'])==23 and len(d['tools'])==114 and len(d['first_party_skills'])==14
assert len(g['nodes'])==280 and len(g['edges'])==704 and len(w['workflows'])==64
ids={n['id'] for n in g['nodes']}
assert len(ids)==len(g['nodes'])
assert all(x['source'] in ids and x['target'] in ids for x in g['edges'])
assert len({t['url'] for t in d['tools']})==114
assert all(t['url'].startswith('https://') for t in d['tools'])
assert all((R/'skills'/s['slug']/'SKILL.md').exists() for s in d['first_party_skills'])
for name in ('industries.csv','tools.csv','roles.csv','edges.csv','workflows.csv'):
 with (R/name).open(encoding='utf-8-sig',newline='') as f: assert len(list(csv.DictReader(f)))>0
print('PASS Atlas V1.1: 32 industries, 114 tools, 64 workflows, 280 nodes, 704 edges, 14 skills')
