"""Browser smoke tests for the base offline atlas. pip install playwright; playwright install chromium."""
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(__file__).parent
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 page=b.new_page(viewport={'width':1440,'height':900})
 err=[];page.on('pageerror',lambda e:err.append(str(e)))
 page.set_content((R/'index.html').read_text(encoding='utf-8'),wait_until='load')
 assert '32 个行业' in page.locator('#summary').inner_text()
 assert '114 个工具' in page.locator('#summary').inner_text()
 page.locator('#q').fill('量化')
 assert '证券与资管' in page.locator('#sectorCards').inner_text()
 page.locator('#reset').click()
 page.locator('[data-tab="tools"]').click()
 assert page.locator('#toolCards .card').count()>=100
 assert not err,err
 mob=b.new_page(viewport={'width':390,'height':844});mob.set_content((R/'index.html').read_text(encoding='utf-8'))
 assert mob.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1')
 b.close()
print('PASS base browser smoke tests')
