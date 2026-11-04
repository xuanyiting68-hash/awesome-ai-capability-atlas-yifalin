#!/usr/bin/env python3
"""V1.7.4 annotated intent evaluation + desktop/mobile Chromium interaction checks."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
html=(ROOT/"advisor_v174.html").read_text(encoding="utf-8")
fixtures=json.loads((ROOT/"task_eval_cases_v174.json").read_text(encoding="utf-8"))
data=json.loads((ROOT/"advisor_v16_data.json").read_text(encoding="utf-8"))
radar=json.loads((ROOT/"discovery_seed.json").read_text(encoding="utf-8"))
assert len(fixtures["cases"])==30 and len({c["id"] for c in fixtures["cases"]})==30
assert (len(data["sectors"]),len(data["subdomains"]),len(data["tools"]),len(data["learning"]))==(32,133,114,69)
assert len(radar["records"])==133 and all(r["approved"] is False for r in radar["records"])
assert html.count('id="atlas-data"')==html.count('id="atlas-intelligence"')==1
assert data["meta"]["ai_runtime"] is False
assert all((c["domain_id"] is None and c["sector_id"] is None) or
           any(d["id"]==c["domain_id"] and d["sector_id"]==c["sector_id"] for d in data["subdomains"])
           for c in fixtures["cases"])
with sync_playwright() as p:
    opts={"headless":True}
    if Path("/usr/bin/chromium").exists():
        opts.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
    browser=p.chromium.launch(**opts)
    for width,height in [(1440,900),(390,844)]:
        page=browser.new_page(viewport={"width":width,"height":height})
        errors,outbound=[],[]
        page.on("pageerror",lambda e: errors.append(str(e)))
        page.on("request",lambda q: outbound.append(q.url) if q.url.startswith(("http://","https://")) else None)
        page.set_content(html,wait_until="load")
        assert page.locator("#bridgeCandidates .bridgeCard").count()==0
        for c in fixtures["cases"]:
            page.locator("#query").fill(c["query"])
            page.locator("#searchForm button").click()
            if c["domain_id"] is None:
                assert page.locator("#bridgeCandidates .bridgeCard").count()==0,c["id"]
                assert page.locator("#bridgePilot").is_disabled(),c["id"]
            else:
                actual=page.locator("#domain").input_value()
                assert actual==c["domain_id"],f'{width} {c["id"]}: {actual} != {c["domain_id"]}'
                assert page.locator("#sector").input_value()==c["sector_id"],c["id"]
                assert page.locator("#bridgePilot").is_enabled(),c["id"]
            assert c["query"] not in page.url,c["id"]
        # Relevance evidence must actually match the specific user task rather than recency only.
        quant="我在证券资管行业做量化因子研究，希望 AI 自动分析论文、整理因子并回测策略"
        page.locator("#query").fill(quant)
        page.locator("#searchForm button").click()
        assert page.locator("#bridgeCandidates .bridgeCard").count()>=2
        assert page.locator("#bridgeSignals .bridgeSignal").count()>=1
        assert "匹配词" in page.locator("#bridgeSignals").inner_text()
        first=page.locator("#bridgeCandidates [data-bridge-dismiss]").first
        first_id=first.get_attribute("data-bridge-dismiss")
        first.click()
        assert page.locator(f'[data-bridge-dismiss="{first_id}"]').count()==0
        assert page.locator("#bridgeRestore").is_visible()
        assert "已隐藏 1 项" in page.locator("#bridgeHiddenStatus").inner_text()
        page.locator("#query").fill("我是律师，在合同审核中减少重复工作")
        page.locator("#searchForm button").click()
        assert page.locator("#bridgeSignals .bridgeSignal").count()==0
        assert "没有足够直接的情报" in page.locator("#bridgeSignals").inner_text()
        assert page.locator("#bridgeRestore").is_hidden()
        page.locator("#query").fill(quant)
        page.locator("#searchForm button").click()
        assert page.locator(f'[data-bridge-dismiss="{first_id}"]').count()==0, "domain scoped dismiss lost"
        page.locator("#bridgeRestore").click()
        assert page.locator(f'[data-bridge-dismiss="{first_id}"]').count()==1
        assert page.locator("#bridgeRestore").is_hidden()
        page.locator('[data-bridge-focus="sources"]').click()
        assert page.locator('[data-bridge-focus="sources"]').get_attribute("aria-pressed")=="true"
        page.locator("#bridgeCandidates [data-bridge-compare]").first.click()
        assert page.locator("#compare .comparison").count()==1
        assert not outbound,outbound
        assert not errors,errors
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),f"overflow {width}"
        page.close()
    browser.close()
print("PASS V1.7.4: 30 labelled synthetic task cases on 1440/390 Chromium, relevance-only radar, scoped negative feedback, restore, compare, privacy")
