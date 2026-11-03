#!/usr/bin/env python3
"""Generate a self-contained, zero-API industry advisor from the existing V1.4 editorial atlas.
No remote calls, user credentials, model invocations or software installs.
"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'discover_v14_data.json'
OUTPUT = ROOT / 'advisor.html'
DATA_OUT = ROOT / 'advisor_v15_data.json'
d = json.loads(SOURCE.read_text(encoding='utf-8'))
assert (len(d['sectors']),len(d['subdomains']),len(d['tools']),len(d['learning'])) == (32,133,114,69)
d['version'] = '1.5.0'
d['verification'] = '编辑分类 + 浏览器端可解释检索；不包含大模型推理、实时招聘、价格/兼容性核验或实际 Agent 执行'
d['meta'] = {'mode': 'offline-rules', 'ai_runtime': False, 'pricing_verified': False,
             'classification': 'AI 业务应用子领域，非国家行业中类/小类代码',
             'current_roles': '编辑样本，而非完整标准职业名录',
             'sources': ['https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin',
                         'https://www.nist.gov/itl/ai-risk-management-framework']}
DATA_OUT.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
tpl=(ROOT/'advisor_v15_template.html').read_text(encoding='utf-8')
data=json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
html=tpl.replace('<!--JSON_DATA_SLOT-->', '<script id="atlas-data" type="application/json">'+data+'</script>')
assert '<!--JSON_DATA_SLOT-->' not in html
OUTPUT.write_text(html,encoding='utf-8')
print('Created', OUTPUT, 'size', OUTPUT.stat().st_size, 'data', DATA_OUT.stat().st_size)
