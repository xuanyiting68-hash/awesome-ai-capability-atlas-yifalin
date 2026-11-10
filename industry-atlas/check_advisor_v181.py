#!/usr/bin/env python3
"""Actual Chromium 1440/390: provenance links, explicit unscanned and filtered cases."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
from coverage_review_v177 import load_data
from supply_chain_review_v181 import build_report
ROOT=Path(__file__).resolve().parent
html=(ROOT/"advisor_v181.html").read_text(encoding="utf-8")
E=json.loads((ROOT/"supply_chain_evidence_v181.json").read_text(encoding="utf-8"))
L=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
F=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
S,A,P=load_data()
r=build_report(E,L,F,S,A,P)
assert r["selected_dependency_paths"]==15
assert r["security_approvals"]==0
with sync_playwright() as p:
    options={"headless":True}
    if Path("/usr/bin/chromium").exists():
        options.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
    browser=p.chromium.launch(**options)
    for width,height in ((1440,900),(390,844)):
        page=browser.new_page(viewport={"width":width,"height":height})
        errors,outbound=[],[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.on("request",lambda req:outbound.append(req.url) if req.url.startswith(("http://","https://")) else None)
        page.set_content(html,wait_until="load")
        assert page.locator("#externalLeadRows .externalLeadRow").count()==10
        assert page.locator("#externalLeadRows .supplyEvidence").count()==10
        assert page.locator("#externalLeadRows .supplyLinks a").count()==15
        assert page.locator("#externalLeadRows a[href$='/SECURITY.md']").count()==2
        summary=page.locator("#externalLeadSummary").inner_text()
        assert "15 条选定依赖文件路径" in summary
        assert "2 个已读取 SECURITY.md" in summary
        assert "CVE 扫描 0" in summary and "安全批准 0" in summary
        assert "尚无候选 20 个" in page.locator("#coverageTotals").inner_text()
        # Only VROOM has no selected conventional dependency file.
        page.locator("#externalOnlyDependencyGap").check()
        assert page.locator("#externalLeadRows .externalLeadRow").count()==1
        assert "VROOM-Project/vroom" in page.locator("#externalLeadRows").inner_text()
        assert "不代表完全没有安全渠道" in page.locator("#externalLeadRows").inner_text()
        # Clipboards capture filtered sources, tree SHA and no-SCA caveat.
        page.evaluate("""() => {
           Object.defineProperty(navigator,'clipboard',{configurable:true,
             value:{writeText:(str)=>{window.__lastAtlasCopy=str;return Promise.resolve()}}});
        }""")
        page.locator("#externalLeadCopy").click()
        report=page.evaluate("window.__lastAtlasCopy")
        assert "VROOM-Project/vroom" in report
        assert "OHIF/Viewers" not in report
        assert "07be776fc20b8d6c85d9f78797e38a9f4e44ec44" in report
        assert "CVE 扫描 0" in report
        page.locator("#externalOnlyDependencyGap").uncheck()
        page.locator("#externalOnlyReconcile").check()
        assert page.locator("#externalLeadRows .externalLeadRow").count()==2
        assert "IfcOpenShell/IfcOpenShell" in page.locator("#externalLeadRows").inner_text()
        assert "opentripplanner/OpenTripPlanner" in page.locator("#externalLeadRows").inner_text()
        page.locator("#externalOnlyReconcile").uncheck()
        page.locator("#externalLeadFilter").select_option("s31")
        assert page.locator("#externalLeadRows .externalLeadRow").count()==1
        assert "open5gs/open5gs" in page.locator("#externalLeadRows").inner_text()
        assert page.locator("#externalLeadRows a[href*='/webui/package-lock.json']").count()==1
        page.locator("#externalLeadRows [data-external-sector='s31']").click()
        assert "电信与互联网服务" in page.locator("#coverageSelection").inner_text()
        assert "原有编辑标签 0 条" in page.locator("#coverageSelection").inner_text()
        assert "未审核主题映射 0 条" in page.locator("#coverageSelection").inner_text()
        assert not outbound,outbound
        assert not errors,errors
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),f"mobile overflow {width}"
        page.close()
    browser.close()
print("PASS V1.8.1 Chromium 1440/390: 10 trees, 15 manifest links, 2 policies, VROOM evidence gap, scoped copy, 0 CVE/approval, no egress")
