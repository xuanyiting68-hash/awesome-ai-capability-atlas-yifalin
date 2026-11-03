"""Playwright Chromium smoke for offline career module. pip install playwright; playwright install chromium."""
from pathlib import Path
from playwright.sync_api import sync_playwright
P=Path(__file__).resolve().parent
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for width in (1440,390):
  page=b.new_page(viewport={"width":width,"height":844},accept_downloads=True)
  errs=[];page.on("pageerror",lambda e:errs.append(str(e)))
  page.set_content((P/"career.html").read_text(encoding="utf-8"),wait_until="load")
  assert page.locator("#role option").count()==225
  assert page.locator("#routeCards .card").count()==3
  with page.expect_download() as d:page.locator("#exportPlan").click()
  assert d.value.suggested_filename.endswith(".md")
  page.locator("#industry").select_option("s02")
  page.locator("#roleSearch").fill("量化")
  assert page.locator("#role option").count()==1
  page.locator('[data-tab="emerging"]').click()
  assert page.locator("#jobCards .card").count()==50
  page.locator("#jobStatus").select_option("hypothesis")
  assert 0<page.locator("#jobCards .card").count()<50
  page.locator('[data-tab="library"]').click()
  assert page.locator("#resources .card").count()==69
  page.locator("#libQuery").fill("n8n")
  assert page.locator("#resources .card").count()>=2
  page.locator('[data-tab="automation"]').click()
  assert page.locator("#stages .card").count()==5
  assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1")
  assert not errs,errs
  page.close()
 b.close()
print("PASS V1.2 offline browser desktop/mobile")
