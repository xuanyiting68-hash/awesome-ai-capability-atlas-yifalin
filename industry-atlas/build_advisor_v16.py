#!/usr/bin/env python3
"""Generate YIFALIN V1.6 Guided Workspace as an offline, inspectable standalone page.

No remote model, no user-account auth, no external writes, no analytics. The new
UI operates on the existing V1.5 editorial dataset, without changing it.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'advisor_v15_data.json').read_text(encoding='utf-8'))
assert (len(DATA['sectors']),len(DATA['subdomains']),len(DATA['tools']),len(DATA['learning']))==(32,133,114,69)
DATA['version']='1.6.0'
DATA['verification']='离线规则匹配及可编辑试点工作台；不是实时大模型、自动执行或已验证工具兼容性'
DATA['meta']['ui']='guided-workspace'; DATA['meta']['ai_runtime']=False
(ROOT/'advisor_v16_data.json').write_text(json.dumps(DATA,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
tpl=(ROOT/'advisor_v16_template.html').read_text(encoding='utf-8')
blob=json.dumps(DATA,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
assert tpl.count('<!--JSON_DATA_SLOT-->')==1
html=tpl.replace('<!--JSON_DATA_SLOT-->','<script id="atlas-data" type="application/json">'+blob+'</script>')
assert len(html)>170_000
(ROOT/'advisor_v16.html').write_text(html,encoding='utf-8')
print('V1.6 ready:',len(html),'characters; 32 sectors / 133 specialties / 114 tools / 69 learning gateways')