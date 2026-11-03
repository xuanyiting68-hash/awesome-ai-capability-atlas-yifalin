#!/usr/bin/env python3
"""Real Chromium check of new in-page discovery review console at 1440 and 390px."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

handler = partial(Quiet, directory=str(ROOT))
server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
thread = Thread(target=server.serve_forever, daemon=True)
thread.start()
origin = f"http://127.0.0.1:{server.server_address[1]}"
try:
    with sync_playwright() as p:
        launch={"headless": True}
        if Path("/usr/bin/chromium").exists():
            launch.update(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        browser=p.chromium.launch(**launch)
        for width,height in ((1440,900),(390,844)):
            page=browser.new_page(viewport={"width":width,"height":height})
            errors=[];outbound=[]
            page.on("pageerror",lambda e:errors.append(str(e)))
            page.on("request",lambda r:outbound.append(r.url) if not r.url.startswith(origin) else None)
            page.goto(origin+"/industry-atlas/intelligence.html",wait_until="networkidle")
            assert page.locator("#countTotal").inner_text()=="133"
            assert int(page.locator("#countFiltered").inner_text())==133
            assert page.locator(".item").count()==12
            assert "待审核" in page.locator("#radarDisclaimer").inner_text() or "live" in page.locator("#radarDisclaimer").inner_text().lower()
            assert page.locator("#cards a[href^='https://']").count()>=12
            page.locator("#more").click()
            assert page.locator(".item").count()==24
            page.locator("#langBtn").click()
            assert page.locator("#headline").inner_text().startswith("不只追踪") or page.locator("#headline").inner_text().startswith("Discover useful")
            page.locator("#langBtn").click()
            page.locator("#search").fill("unlikely-absent-specialized-phrase-48219")
            assert page.locator(".item").count()==0
            assert page.locator(".empty").count()==1
            page.locator("#search").fill("")
            page.locator("#sector").select_option("s02")
            assert int(page.locator("#countFiltered").inner_text())>0
            assert int(page.locator("#countFiltered").inner_text())<133
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
            assert not errors,errors
            assert not outbound, "This reference dashboard must not call external APIs"
            page.close()
        browser.close()
finally:
    server.shutdown()
    server.server_close()
print("PASS AI discovery reference radar Chromium 1440/390: provenance, bilingual, search, industry filter, no external requests")
