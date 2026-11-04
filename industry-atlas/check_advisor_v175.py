#!/usr/bin/env python3
"""Real Chromium 1440/390 verification of V1.7.5 evidence UI, mock and zero egress."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parent
html=(ROOT/"advisor_v175.html").read_text(encoding="utf-8")
data=json.loads((ROOT/"advisor_v16_data.json").read_text(encoding="utf-8"))
radar=json.loads((ROOT/"discovery_seed.json").read_text(encoding="utf-8"))
topics=json.loads((ROOT/"rag_topics_v175.json").read_text(encoding="utf-8"))
assert len(radar["records"])==133 and all(x["approved"] is False for x in radar["records"])
assert len(topics["concepts"])==15
assert (len(data["sectors"]),len(data["subdomains"]),len(data["tools"]),len(data["learning"]))==(32,133,114,69)
assert html.count('id="atlas-rag-topics"')==1
with sync_playwright() as p:
    cfg={"headless":True}
    if Path("/usr/bin/chromium").exists():
        cfg.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
    browser=p.chromium.launch(**cfg)
    for width,height in [(1440,900),(390,844)]:
        page=browser.new_page(viewport={"width":width,"height":height})
        errors,outbound=[],[]
        page.on("pageerror",lambda e: errors.append(str(e)))
        page.on("request",lambda req: outbound.append(req.url) if req.url.startswith(("http://","https://")) else None)
        page.set_content(html,wait_until="load")
        assert page.locator("#ragMock").is_disabled()
        assert page.locator("#ragSources .ragSource").count()==0
        page.locator("#query").fill("我在证券资管做量化因子研究与回测")
        page.locator("#searchForm button").click()
        assert page.locator("#targetTitle").inner_text()=="量化金融与因子研究"
        assert page.locator("#ragMock").is_enabled()
        assert 1<=page.locator("#ragSources .ragSource").count()<=4
        assert "backtrader" in page.locator("#ragSources").inner_text().lower() or "vectorbt" in page.locator("#ragSources").inner_text().lower()
        assert "许可证信号" in page.locator("#ragSources").inner_text()
        assert page.locator("#ragSources a[href^='https://']").count()>=1
        page.locator("#ragMock").click()
        assert "离线 Mock" in page.locator("#ragAnswer").inner_text()
        assert page.locator("#ragAnswer a[href^='https://']").count()>=1
        assert page.locator("#ragClear").is_enabled()
        page.locator("#ragClear").click()
        assert "已清除" in page.locator("#ragAnswer").inner_text()
        assert page.locator("#ragClear").is_disabled()
        # Recompute on a different task; never preserve stale citations.
        page.locator("#query").fill("我在学校做课程知识库和 RAG 检索")
        page.locator("#searchForm button").click()
        assert "基础教育" in page.locator("#ragCoverage").inner_text()
        assert page.locator("#ragSources .ragSource").count()>0
        assert "Mock 仅" in page.locator("#ragAnswer").inner_text()
        # Sector with no seeded radar sources must abstain rather than cross-link.
        page.locator("#query").fill("我是律师，想自动做合同审查")
        page.locator("#searchForm button").click()
        assert page.locator("#ragSources .ragSource").count()==0
        assert "没有直接的缓存来源命中" in page.locator("#ragCoverage").inner_text()
        page.locator("#ragMock").click()
        assert "拒绝编造" in page.locator("#ragAnswer").inner_text()
        assert page.locator("#ragAnswer a").count()==0
        # Unknown task fails closed.
        page.locator("#query").fill("星际香蕉风铃神秘舞台")
        page.locator("#searchForm button").click()
        assert page.locator("#ragSources .ragSource").count()==0
        assert page.locator("#ragMock").is_disabled()
        assert not outbound,outbound
        assert not errors,errors
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),f"overflow at {width}"
        page.close()
    browser.close()
print("PASS V1.7.5 real Chromium 1440/390: offline evidence retrieval, citations, mock abstention, task reset, no egress and mobile fit")
