#!/usr/bin/env python3
"""Task-first Atlas front door: 1440/390 Chromium, progressive disclosure and no egress."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
home=ROOT/"start.html"
advisor=ROOT/"advisor_v181.html"
assert home.is_file() and advisor.is_file()
assert 'id="searchForm"' in advisor.read_text(encoding="utf-8")
html=home.read_text(encoding="utf-8")
assert html.count('id="startTask"')==1
assert 'href="advisor_v181.html#searchForm"' in html
assert '<textarea' not in html and '<form' not in html  # no pretend on-landing AI inference
for page in ("intelligence.html","career.html","expert.html","taxonomy.html","index.html","advisor_v173.html","advisor_v17.html"):
    assert (ROOT/page).is_file(),page

with sync_playwright() as p:
    config={"headless":True}
    if Path("/usr/bin/chromium").exists():
        config.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
    browser=p.chromium.launch(**config)
    for width,height in ((1440,900),(390,844)):
        context=browser.new_context(viewport={"width":width,"height":height},locale="en-US")
        page=context.new_page()
        errors,external=[],[]
        page.on("pageerror",lambda error:errors.append(str(error)))
        page.on("request",lambda req:external.append(req.url) if req.url.startswith(("http://","https://")) else None)
        page.goto(home.as_uri(),wait_until="load")
        assert page.locator("html").get_attribute("lang")=="en"
        assert "What do you do" in page.locator("h1").inner_text()
        assert "primarily in Chinese" in page.locator(".disclosure").inner_text()
        assert page.locator(".routes > a.route").count()==3
        assert not page.locator("#researchMore").get_attribute("open")
        assert not page.locator("#historyMore").get_attribute("open")
        assert page.locator(".links a").count()>=12
        assert page.locator("#startTask").get_attribute("href")=="advisor_v181.html#searchForm"
        page.locator("#zh").click()
        assert page.locator("html").get_attribute("lang")=="zh-CN"
        assert "你现在做什么工作" in page.locator("h1").inner_text()
        assert page.locator("#zh").get_attribute("aria-pressed")=="true"
        page.locator("#en").click()
        assert page.locator("#zh").get_attribute("aria-pressed")=="false"
        assert page.locator("#en").get_attribute("aria-pressed")=="true"
        page.locator("#researchMore summary").click()
        assert page.locator("#researchMore").get_attribute("open") is not None
        page.locator("#historyMore summary").click()
        assert page.locator("#historyMore").get_attribute("open") is not None
        assert page.locator("a[href='advisor_v173.html']").count()==1
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),f"overflow {width}"
        page.locator("#startTask").click()
        page.wait_for_url("**/advisor_v181.html#searchForm")
        assert page.locator("#query").count()==1
        assert page.locator("#searchForm").count()==1
        assert "api_key" not in page.url and "?q=" not in page.url
        assert not errors,errors
        assert not external,external
        context.close()
    browser.close()
print("PASS Atlas task-first 1440/390: bilingual launch, no deceptive input, 3 primary routes, disclosure, legacy links, same-origin advisor, 0 outbound requests")
