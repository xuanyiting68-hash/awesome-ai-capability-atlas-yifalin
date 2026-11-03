#!/usr/bin/env python3
"""Actual Chromium UX regression for V1.7, without a live LLM or external writes."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json

ROOT = Path(__file__).resolve().parent
html = (ROOT / "advisor_v17.html").read_text(encoding="utf-8")
data = json.loads((ROOT / "advisor_v16_data.json").read_text(encoding="utf-8"))
assert (len(data["sectors"]), len(data["subdomains"],), len(data["tools"]), len(data["learning"])) == (32,133,114,69)
assert data["meta"]["ai_runtime"] is False
assert html.count('id="atlas-data"') == 1

with sync_playwright() as p:
    launch = {"headless": True}
    if Path("/usr/bin/chromium").exists():
        launch.update(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    browser = p.chromium.launch(**launch)
    for width,height in [(1440,900),(390,844)]:
        page = browser.new_page(viewport={"width":width,"height":height}, accept_downloads=True)
        errors = []
        outbound = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("request", lambda req: outbound.append(req.url) if req.url.startswith(("https://","http://")) else None)
        page.set_content(html,wait_until="load")
        assert "V1.7" in page.title()
        assert "还需要一点行业" in page.locator("#targetTitle").inner_text()
        assert page.locator("#nextGo").is_disabled()
        assert page.locator("#quickActions button:disabled").count() == 3
        assert page.locator("#dynamicSamples .sample").count() == 4
        assert page.locator("#graphBlock").is_hidden()
        # Context-aware example prompts appear without requiring a multi-stage selector.
        page.locator("#query").fill("量化金融")
        assert "量化研究" in page.locator("#dynamicSamples").inner_text()
        assert "工厂维修" not in page.locator("#dynamicSamples").inner_text()
        page.locator("#dynamicSamples [data-example]").first.click()
        assert page.locator("#targetTitle").inner_text()=="量化金融与因子研究"
        assert page.locator("#domain option").count() == 8
        assert page.locator("#steps .planstep:visible").count() == 1
        assert page.locator("#tools .resource").count() <= 2
        assert page.locator("#quickActions button:enabled").count() == 3
        assert "离线规则" in page.locator("#modeTag").inner_text()
        assert "V1.7" in page.locator("footer").inner_text()
        # Beginner mode: one task at a time. Changes don't erase progress.
        page.locator("#steps .planstep:visible input").check()
        assert "1/5" in page.locator("#taskCount").inner_text()
        assert page.locator("#steps .planstep:visible").count()==1
        assert "准备数据" in page.locator("#nextTitle").inner_text()
        page.locator('[data-view="expert"]').click()
        assert page.locator("#graphBlock").is_visible()
        assert page.locator("#steps .planstep:visible").count() == 5
        assert page.locator("#tools .resource").count() <= 4
        page.locator("#moreTools").click()
        checks = page.locator("#tools [data-compare]")
        assert checks.count() >= 3
        for i in range(3):
            checks.nth(i).check()
        assert page.locator("#compare .comparison").count()==3
        # In-page questions and source-link cards remain accessible.
        page.locator("#chatInput").fill("为什么这样匹配")
        page.locator("#chatForm button").click()
        assert "关键词/领域索引" in page.locator("#chatlog .message.bot").last.inner_text()
        assert page.locator("#tools a[href^='https://']").count() > 0
        # Changing domain must isolate notes and checklist.
        page.locator("#notesBox summary").click()
        page.locator("#workNote").fill("脱敏研究样本 10 份")
        page.locator("#query").fill("我是律师，在合同审核中减少重复工作")
        page.locator("#searchForm button").click()
        assert page.locator("#targetTitle").inner_text()=="合同审查与法务管理"
        assert page.locator("#workNote").input_value() == ""
        assert "0/5" in page.locator("#taskCount").inner_text()
        page.locator("#query").fill("证券资管的量化因子研究")
        page.locator("#searchForm button").click()
        assert "脱敏研究样本" in page.locator("#workNote").input_value()
        assert "1/5" in page.locator("#taskCount").inner_text()
        # Unknown intents must fail closed rather than showing stale business claims.
        page.locator("#query").fill("星际香蕉风铃神秘舞台")
        page.locator("#searchForm button").click()
        assert page.locator("#tools .resource").count()==0
        assert page.locator("#nextGo").is_disabled()
        assert page.locator("#quickActions button:disabled").count()==3
        assert page.locator("#query").input_value()=="星际香蕉风铃神秘舞台"
        assert "星际香蕉" not in page.url
        page.locator('[data-view="beginner"]').click()
        assert page.locator("#graphBlock").is_hidden()
        if width==390:
            assert page.locator(".mobileNav button").count()==4
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1")
        assert not outbound, "The offline UI must not contact third-party APIs"
        assert not errors,errors
        page.close()
    browser.close()
print("PASS V1.7 real Chromium 1440/390: zero-click neutral, dynamic examples, progressive detail, switching, followups, comparison, isolation, privacy")
