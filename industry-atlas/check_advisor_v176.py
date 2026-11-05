#!/usr/bin/env python3
"""Actual 1440px / 390px Chromium regression for honest source review UI."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parent
html=(ROOT/"advisor_v176.html").read_text(encoding="utf-8")
data=json.loads((ROOT/"advisor_v16_data.json").read_text(encoding="utf-8"))
seed=json.loads((ROOT/"discovery_seed.json").read_text(encoding="utf-8"))
assert (len(data["sectors"]),len(data["subdomains"]),len(data["tools"]),len(data["learning"]))==(32,133,114,69)
assert len(seed["records"])==133 and all(r["approved"] is False for r in seed["records"])
with sync_playwright() as p:
    opt={"headless":True}
    if Path("/usr/bin/chromium").exists():
        opt.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
    browser=p.chromium.launch(**opt)
    for width,height in ((1440,900),(390,844)):
        page=browser.new_page(viewport={"width":width,"height":height})
        errors,outbound=[],[]
        page.on("pageerror",lambda x:errors.append(str(x)))
        page.on("request",lambda q:outbound.append(q.url) if q.url.startswith(("http://","https://")) else None)
        page.set_content(html,wait_until="load")
        assert page.locator("#auditCopy").is_disabled()
        assert page.locator("#auditRows .auditRow").count()==0
        page.locator("#query").fill("我在证券资管做量化因子研究与回测")
        page.locator("#searchForm button").click()
        assert page.locator("#targetTitle").inner_text()=="量化金融与因子研究"
        page.locator("#auditDetails summary").click()
        assert page.locator("#auditDetails").get_attribute("open") is not None
        assert page.locator("#auditRows .auditRow").count()==page.locator("#ragSources .ragSource").count()
        assert page.locator("#auditCopy").is_enabled()
        assert "独立验证 0 条" in page.locator("#auditSummary").inner_text()
        assert "许可标识未知" in page.locator("#auditSummary").inner_text()
        assert "未实时检查" in page.locator("#auditRows").inner_text()
        assert "未验证商用条款" in page.locator("#auditRows").inner_text() or "许可证信号缺失" in page.locator("#auditRows").inner_text()
        assert page.locator("#auditRows a[href^='https://']").count()>0
        page.locator("#auditCopy").click()
        assert "已复制" in page.locator("#auditCopyStatus").inner_text() or "不允许复制" in page.locator("#auditCopyStatus").inner_text()
        assert "独立验证 0 条" in page.locator("#auditSummary").inner_text()
        page.locator("#ragMock").click()
        assert "离线 Mock" in page.locator("#ragAnswer").inner_text()
        page.locator("#query").fill("我是律师，想在合同审查时减少重复工作")
        page.locator("#searchForm button").click()
        assert page.locator("#auditRows .auditRow").count()==0
        assert page.locator("#auditCopy").is_disabled()
        assert "没有直接命中的编辑元数据" in page.locator("#auditSummary").inner_text()
        assert "Mock 仅" in page.locator("#ragAnswer").inner_text()
        assert not outbound,outbound
        assert not errors,errors
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),f"mobile overflow {width}"
        page.close()
    browser.close()
print("PASS V1.7.6 Chromium 1440/390: evidence audit and 0 independent approvals, copy affordance, scoped refresh, privacy and no egress")
