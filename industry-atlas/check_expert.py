"""Browser smoke tests for the V1.1 offline Expert Studio. pip install playwright; playwright install chromium."""
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).parent
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 page=b.new_page(viewport={'width':1440,'height':900},accept_downloads=True)
 err=[];page.on('pageerror',lambda e:err.append(str(e)))
 page.set_content((R/'expert.html').read_text(encoding='utf-8'),wait_until='load')
 assert page.locator('#results .item').count()==64
 page.locator('#query').fill('合同');assert 0<page.locator('#results .item').count()<64
 page.locator('#reset').click();page.locator('#sector').select_option('s04')
 assert page.locator('#results .item').count()==2
 assert '高敏感' in page.locator('#detail').inner_text()
 page.locator('#reset').click();page.locator('#sector').select_option('s21');page.locator('#scene').select_option('legal')
 with page.expect_download() as x:page.locator('#downloadPlan').click()
 assert x.value.suggested_filename.endswith('.md')
 assert '7.0 h' in page.locator('#calcOutput').inner_text() and '260 元' in page.locator('#calcOutput').inner_text()
 page.locator('#after').fill('29');assert '-' in page.locator('#calcOutput').inner_text()
 with page.expect_download() as x:page.locator('#calcExport').click()
 assert x.value.suggested_filename.endswith('.csv')
 page.locator('#reset').click();assert page.locator('#analogs [data-id]').count()>0
 page.locator('#analogs [data-id]').first.click();assert page.locator('#results .item').count()==1
 assert not err,err
 mob=b.new_page(viewport={'width':390,'height':844});mob.set_content((R/'expert.html').read_text(encoding='utf-8'))
 assert mob.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1')
 b.close()
print('PASS expert browser smoke tests')
