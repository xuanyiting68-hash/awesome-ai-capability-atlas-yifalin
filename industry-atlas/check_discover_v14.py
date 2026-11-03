"""V1.4 offline, deterministic browser checks: no network, live model or user data."""
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parent
d=json.loads((R/'discover_v14_data.json').read_text(encoding='utf-8'))
assert len(d['sectors'])==32 and len(d['subdomains'])==133
assert len(d['tools'])==114 and len(d['learning'])==69
assert len(d['workflows'])==64
ids={x['id'] for x in d['sectors']}
assert all(x['sector_id'] in ids for x in d['subdomains'])
assert len({x['id'] for x in d['subdomains']})==133
html=(R/'discover.html').read_text(encoding='utf-8')
match=re.search(r'<script id="embedded-data" type="application/json">(.*?)</script>',html,re.S)
assert match
assert json.loads(match.group(1).replace(r'<\/','</'))==d
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for width in (1440,390):
  page=b.new_page(viewport={'width':width,'height':900},accept_downloads=True)
  errs=[]
  page.on('pageerror',lambda e:errs.append(str(e)))
  page.set_content(html,wait_until='load')
  assert '证券与资管' in page.locator('#crumb').inner_text()
  assert '量化金融与因子研究' in page.locator('#crumb').inner_text()
  assert '67 资本市场服务' in page.locator('#std').inner_text()
  assert page.locator('#domainPills button').count()==8
  assert page.locator('#toolCards a[href^="https://"]').count()>=4
  assert page.locator('#plan .step').count()==4
  assert page.locator('#downloadMd').is_hidden()
  page.locator('#mainQuery').fill('我从事量化金融类工作，研究因子和交易策略')
  page.locator('#mainForm button[type=submit]').click()
  assert '量化金融' in page.locator('#crumb').inner_text()
  page.locator('[data-domain="s02-d03"]').click()
  assert '资产管理与投资组合' in page.locator('#crumb').inner_text()
  page.locator('#advanced summary').click()
  page.locator('#sectorSelect').select_option('s09')
  names=page.locator('#domainSelect option').all_text_contents()
  assert len(names)==4 and all('量化' not in v and '证券' not in v for v in names)
  page.locator('#mainQuery').fill('证券资管的交易执行和市场微观结构')
  page.locator('#mainForm button[type=submit]').click()
  assert '交易执行与市场微观结构' in page.locator('#crumb').inner_text()
  page.locator('#chatInput').fill('有哪些工具和网站？')
  page.locator('#chatForm button[type=submit]').click()
  assert '114 个资源入口' in page.locator('#chatLog').inner_text()
  page.locator('[data-stage="3"]').click()
  assert '验证与评测' in page.locator('#stageNote').inner_text()
  page.locator('div.details:has(#downloadMd) summary').click()
  with page.expect_download() as info: page.locator('#downloadMd').click()
  assert info.value.suggested_filename.endswith('.md')
  assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
  assert not errs,errs
  page.close()
 b.close()
print('PASS V1.4: 32 sectors/133 scoped specialties; quant contextual search, chat, source links, visual stages, optional download, mobile')
