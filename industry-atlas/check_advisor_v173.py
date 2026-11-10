#!/usr/bin/env python3
"""Actual Chromium regression for the evidence-graded V1.7.3 task bridge."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json

ROOT = Path(__file__).resolve().parent
html = (ROOT / "advisor_v173.html").read_text(encoding="utf-8")
data = json.loads((ROOT / "advisor_v16_data.json").read_text(encoding="utf-8"))
radar = json.loads((ROOT / "discovery_seed.json").read_text(encoding="utf-8"))
assert (len(data["sectors"]), len(data["subdomains"]), len(data["tools"]), len(data["learning"])) == (32, 133, 114, 69)
assert len(radar["records"]) == 133 and all(r["approved"] is False for r in radar["records"])
assert html.count('id="atlas-data"') == html.count('id="atlas-intelligence"') == 1
assert data["meta"]["ai_runtime"] is False

with sync_playwright() as p:
    cfg = {"headless": True}
    if Path("/usr/bin/chromium").exists():
        cfg.update(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    browser = p.chromium.launch(**cfg)
    for width, height in [(1440, 900), (390, 844)]:
        page = browser.new_page(viewport={"width": width, "height": height})
        errors, outbound = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("request", lambda request: outbound.append(request.url) if request.url.startswith(("https://","http://")) else None)
        page.set_content(html, wait_until="load")
        assert page.locator("#bridgeCandidates .bridgeCard").count() == 0
        assert page.locator("#bridgePilot").is_disabled()
        assert page.locator("#bridgeState").inner_text() == "待识别"
        page.locator("#query").fill("我在证券资管行业做量化因子研究，希望 AI 自动分析论文、整理因子并回测策略")
        page.locator("#searchForm button").click()
        assert page.locator("#targetTitle").inner_text() == "量化金融与因子研究"
        assert page.locator("#bridgeCandidates .bridgeCard").count() >= 2
        assert page.locator("#bridgeSignals .bridgeSignal").count() >= 1
        assert page.locator("#bridgeCandidates a[href^='https://']").count() >= 1
        assert "费用/接入条件" in page.locator("#bridgeCandidates").inner_text()
        assert "未审计" in page.locator("#bridgeCandidates").inner_text()
        assert "未经独立安全" in page.locator("#taskBridge").inner_text()
        assert "任务：" in page.locator("#bridgeTask").inner_text()
        page.locator('[data-bridge-focus="sources"]').click()
        assert page.locator('[data-bridge-focus="sources"]').get_attribute("aria-pressed") == "true"
        assert "第二条元数据" in page.locator("#bridgeDisclosure").inner_text()
        page.locator("#bridgeCandidates [data-bridge-compare]").first.click()
        assert page.locator("#compare .comparison").count() == 1
        page.locator("#query").fill("我是律师，在合同审核中减少重复工作")
        page.locator("#searchForm button").click()
        assert page.locator("#targetTitle").inner_text() == "合同审查与法务管理"
        assert page.locator("#bridgeSignals .bridgeSignal").count() == 0
        assert "暂无专属情报参考" in page.locator("#bridgeSignals").inner_text()
        assert "法律" in page.locator("#bridgeTask").inner_text()
        page.locator("#bridgePilot").click()
        assert page.locator("#notesBox").get_attribute("open") is not None
        page.locator("#query").fill("星际香蕉风铃神秘舞台")
        page.locator("#searchForm button").click()
        assert page.locator("#bridgeCandidates .bridgeCard").count() == 0
        assert page.locator("#bridgeSignals .bridgeSignal").count() == 0
        assert page.locator("#bridgePilot").is_disabled()
        assert "暂不推荐未知行业" in page.locator("#bridgeEvidence").inner_text()
        assert "星际香蕉" not in page.url
        assert not outbound, outbound
        assert not errors, errors
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"), f"horizontal overflow at {width}"
        page.close()
    browser.close()
print("PASS V1.7.3 Chromium 1440/390: intent → evidence → action, sector isolation, preference, comparison, unknown fail-closed, offline safety")
