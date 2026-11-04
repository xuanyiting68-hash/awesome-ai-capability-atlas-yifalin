#!/usr/bin/env python3
"""Real Chromium V1.8.0 file provenance, discrepancy filter, copy, no approval."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
from coverage_review_v177 import load_data
from license_evidence_v180 import build_license_report

ROOT=Path(__file__).resolve().parent
html=(ROOT/"advisor_v180.html").read_text(encoding="utf-8")
files=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
leads=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
snapshot,atlas,rules=load_data()
report=build_license_report(files,leads,snapshot,atlas,rules)
assert report["needs_signal_reconciliation"]==2
for w in (1440,390):
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={"width":w,"height":900 if w==1440 else 844})
        errors,outbound=[],[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.on("request",lambda req:outbound.append(req.url) if req.url.startswith(("https://","http://")) else None)
        page.set_content(html,wait_until="load")
        assert page.locator("#externalLeadRows .externalLeadRow").count()==10
        assert page.locator("#externalLeadRows .licFile").count()==10
        assert page.locator("#externalLeadRows a[href*='/blob/']").count()==10
        assert "2 条许可证信号待进一步核对" in page.locator("#externalLeadSummary").inner_text()
        assert "批准 0" in page.locator("#externalLeadSummary").inner_text()
        assert "尚无候选 20 个" in page.locator("#coverageTotals").inner_text()
        # Two unresolved file vs metadata signals MUST remain visible.
        page.locator("#externalOnlyReconcile").check()
        assert page.locator("#externalLeadRows .externalLeadRow").count()==2
        src=page.locator("#externalLeadRows").inner_text()
        assert "IfcOpenShell/IfcOpenShell" in src
        assert "opentripplanner/OpenTripPlanner" in src
        assert "NOASSERTION" in src
        assert "GPL-3.0" in src
        assert "需复核许可证信号与文件文本差异" in src
        # Ensure full clipboard report includes exact observed file SHA and no
        # hidden suggestion that a source has passed legal review.
        page.evaluate("""() => {
          Object.defineProperty(navigator,'clipboard',{
            configurable:true,value:{writeText:(text)=>{window.__copy=text;return Promise.resolve()}}
          });
        }""")
        page.locator("#externalLeadCopy").click()
        copied=page.evaluate("window.__copy")
        assert copied is not None
        assert "IfcOpenShell/IfcOpenShell" in copied
        assert "opentripplanner/OpenTripPlanner" in copied
        assert "OHIF/Viewers" not in copied
        assert "810fce6e9bf2aa10265b85614db5ac65941ecf81" in copied
        assert "b5b929d7364a8cbe1de10c3917b808d467eb81be" in copied
        assert "批准 0 条" in copied
        page.locator("#externalOnlyReconcile").uncheck()
        assert page.locator("#externalLeadRows .externalLeadRow").count()==10
        page.locator("#externalLeadFilter").select_option("s04")
        assert page.locator("#externalLeadRows .externalLeadRow").count()==1
        assert "OHIF/Viewers" in page.locator("#externalLeadRows").inner_text()
        assert "LICENSE" in page.locator("#externalLeadRows").inner_text()
        page.locator("#externalLeadRows [data-external-sector='s04']").click()
        assert "医疗服务" in page.locator("#coverageSelection").inner_text()
        assert "原有编辑标签 0 条" in page.locator("#coverageSelection").inner_text()
        assert "未审核主题映射 0 条" in page.locator("#coverageSelection").inner_text()
        assert page.locator("#coverageGap").get_attribute("hidden") is None
        assert not outbound,outbound
        assert not errors,errors
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),f"overflow at {w}"
        page.close()
        browser.close()
print("PASS V1.8.0 Chromium 1440/390: 10 license file links, 2 discrepancy flags, scoped evidence copy, untouched industry gaps, no egress")
