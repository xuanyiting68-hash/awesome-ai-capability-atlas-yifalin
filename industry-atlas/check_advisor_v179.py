#!/usr/bin/env python3
"""Real 1440/390 Chromium: V1.7.9 unapproved external source provenance, review UX."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from coverage_review_v177 import load_data
from external_leads_v179 import make_review_report
import json

ROOT=Path(__file__).resolve().parent
html=(ROOT/"advisor_v179.html").read_text(encoding="utf-8")
snapshot,atlas,rules=load_data()
ledger=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
report=make_review_report(ledger,snapshot,atlas,rules)
assert report["source_leads"]==10 and report["source_gap_sectors_in_frozen_radar"]==20
assert report["approved_source_count"]==0
assert html.count('id="atlas-external-leads"')==1
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
        assert page.locator("#externalLeadFilter option").count()==11
        assert page.locator("#externalLeadRows .externalLeadRow").count()==10
        assert "批准 0 条" in page.locator("#externalLeadSummary").inner_text()
        assert "不计入原有情报覆盖率" in page.locator("#externalLeadSummary").inner_text()
        assert "尚无候选 20 个" in page.locator("#coverageTotals").inner_text()
        assert page.locator("#externalLeadRows a[href^='https://api.github.com/repos/']").count()==10
        assert page.locator("#externalLeadRows a[href^='https://github.com/']").count()==10
        # Full copy is verifiably complete: capture copyText argument through clipboard.
        page.evaluate("""() => {
          Object.defineProperty(navigator,'clipboard',{
            configurable:true,
            value:{writeText:(value)=>{window.__lastAtlasCopy=value;return Promise.resolve()}}
          });
        }""")
        page.locator("#externalLeadCopy").click()
        assert "已复制完整待审清单" in page.locator("#externalLeadCopyStatus").inner_text()
        copied=page.evaluate("window.__lastAtlasCopy")
        assert all(x["repo_full_name"] in copied for x in ledger["records"])
        assert "LICENSE/NOTICE" in copied
        assert "0 个批准" in copied
        # Task and industry filters are client-only, no implicit tag update.
        page.locator("#externalLeadFilter").select_option("s16")
        assert page.locator("#externalLeadRows .externalLeadRow").count()==1
        assert "OpenTripPlanner" in page.locator("#externalLeadRows").inner_text()
        assert "NOASSERTION" in page.locator("#externalLeadRows").inner_text()
        assert "尚无可确认许可证标识" in page.locator("#externalLeadRows").inner_text()
        page.locator("#externalLeadRows [data-external-sector='s16']").click()
        assert "交通运输与出行" in page.locator("#coverageSelection").inner_text()
        assert "原有编辑标签 0 条" in page.locator("#coverageSelection").inner_text()
        assert "未审核主题映射 0 条" in page.locator("#coverageSelection").inner_text()
        assert page.locator("#coverageGap").get_attribute("hidden") is None
        assert "没有来自现有主题标签" in page.locator("#coverageProposals").inner_text()
        # Filtering still doesn't add item to the old source coverage view.
        page.locator("#externalLeadFilter").select_option("s04")
        assert page.locator("#externalLeadRows .externalLeadRow").count()==1
        assert "OHIF/Viewers" in page.locator("#externalLeadRows").inner_text()
        page.locator("#externalLeadFilter").select_option("all")
        assert page.locator("#externalLeadRows .externalLeadRow").count()==10
        assert "真实独立验证 0 条" in page.locator("#coverageTotals").inner_text()
        assert not errors,errors
        assert not outbound,outbound
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),f"overflow at {width}"
        page.close()
    browser.close()
print("PASS V1.7.9 actual Chromium 1440/390: 10 source/API links, complete 10-item copy, no sector promotion, SPDX caution, no egress")
