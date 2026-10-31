"""Taxonomy V1.3 regression: static official-industry skeleton + synthetic-only occupation import."""
import csv,json,re,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parent
data=json.loads((P/'taxonomy_v13.json').read_text(encoding='utf-8'))
assert len(data['sectors'])==20 and len(data['divisions'])==97
assert sorted(x['code'] for x in data['divisions'])==[f'{i:02}' for i in range(1,98)]
assert len({x['code'] for x in data['sectors']})==20
assert len(data['occupation_major_groups'])==8
assert all(x['section_code'] in {s['code'] for s in data['sectors']} for x in data['divisions'])
with (P/'industry_97_v13.csv').open(encoding='utf-8-sig',newline='') as f:
 rows=list(csv.DictReader(f))
assert len(rows)==97
html=(P/'taxonomy.html').read_text(encoding='utf-8')
m=re.search(r'<script id="STATIC_DATA" type="application/json">(.*?)</script>',html,re.S)
assert m and json.loads(m.group(1).replace(r'<\/','</'))==data
fake={'major_categories':data['occupation_major_groups'],'middle_categories':{},'minor_categories':{},'occupations':{}}
for i in range(1639):
 g=i%79;major=str(min(g//10+1,8));middle=f'{major}-{g%10:02}';minor=f'{middle}-00';code=f'{minor}-{i//79:02}'
 fake['middle_categories'][middle]='synthetic middle'
 fake['minor_categories'][minor]='synthetic minor'
 fake['occupations'][str(i)]={'code':code,'name':f'合成测试职业{i}','major':major,'middle':middle,'minor':minor}
assert len(fake['middle_categories'])==79
with tempfile.TemporaryDirectory() as t:
 path=Path(t)/'fake_only.json';path.write_text(json.dumps(fake,ensure_ascii=False),encoding='utf-8')
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  for width in (1440,390):
   page=browser.new_page(viewport={'width':width,'height':870},accept_downloads=True)
   errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.set_content(html,wait_until='load')
   assert '匹配 97 条' in page.locator('#industryStatus').inner_text()
   page.locator('#industrySection').select_option('J')
   assert page.locator('#industryResults .item').count()==4
   page.locator('[data-tab="occupation"]').click()
   assert page.locator('#roleResults .item').count()==0
   page.locator('#uploadMirror').set_input_files(str(path))
   assert '1,639 / 1,639' in page.locator('.numpanel').inner_text()
   assert page.locator('#roleResults .item').count()==80
   page.locator('#roleSearch').fill('合成测试职业128')
   assert page.locator('#roleResults .item').count()>0
   page.locator('#roleSearch').fill('')
   with page.expect_download() as info:page.locator('#exportRole').click()
   assert info.value.suggested_filename.endswith('.csv')
   page.locator('[data-tab="standards"]').click()
   assert page.locator('#standardResults .sourcecard').count()==7
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   assert not errors,errors
   page.close()
  browser.close()
print('PASS V1.3 taxonomy: 20 sections / 97 divisions; synthetic import; desktop+mobile')
