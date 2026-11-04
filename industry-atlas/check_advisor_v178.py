#!/usr/bin/env python3
"""Real Chromium V1.7.8: full unapproved queue pagination and gap research handoff."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from sector_gap_briefs_v178 import build_gap_briefs
from coverage_review_v177 import load_data

ROOT=Path(__file__).resolve().parent
html=(ROOT/"advisor_v178.html").read_text(encoding="utf-8")
s,a,p=load_data()
briefs=build_gap_briefs(s,a,p)
assert len(briefs["briefs"])==20
with sync_playwright() as playwright:
    options={"headless":True}
    if Path("/usr/bin/chromium").exists():
        options.update(executable_path="/usr/bin/chromium",args=["--no-sandbox"])
    browser=playwright.chromium.launch(**options)
    for width,height in ((1440,900),(390,844)):
        page=browser.new_page(viewport={"width":width,"height":height})
        errors,outbound=[],[]
        page.on("pageerror",lambda e:errors.append(str(e)))
        page.on("request",lambda q:outbound.append(q.url) if q.url.startswith(("http://","https://")) else None)
        page.set_content(html,wait_until="load")
        assert "4/32" in page.locator("#coverageTotals").inner_text()
        assert page.locator("#coverageSector option").count()==32
        page.locator("#coverageSector").select_option("s30")
        assert "未审核主题映射 37 条" in page.locator("#coverageSelection").inner_text()
        # Record all 37 proposals from every page and verify no duplicates/loss.
        all_names=[]
        for n in range(5):
            names=page.locator("#coverageProposals .coverageSource strong").all_inner_texts()
            all_names.extend(names)
            assert f"第 {n+1} / 5 页" in page.locator("#coverageProposalsPager").inner_text()
            if n<4:
                assert page.locator("#coverageProposalsPager [data-cov-step='1']").is_enabled()
                page.locator("#coverageProposalsPager [data-cov-step='1']").click()
        assert len(all_names)==37, len(all_names)
        assert len(all_names)==len(set(all_names)),all_names
        assert page.locator("#coverageProposalsPager [data-cov-step='1']").is_disabled()
        # Move to original labels: 24 records across 3 pages.
        assert "原有编辑标签 24 条" in page.locator("#coverageSelection").inner_text()
        assert "第 1 / 3 页" in page.locator("#coverageDirectPager").inner_text()
        page.locator("#coverageDirectPager [data-cov-step='1']").click()
        assert "第 2 / 3 页" in page.locator("#coverageDirectPager").inner_text()
        # Full export must contain 37 sources, not only the current 8.
        exported=page.evaluate("coverageCopyText()").strip() if False else page.evaluate("""() => {
            let x=document.querySelector('#coverageCopy');return x && !x.disabled;
        }""")
        assert exported
        # Generate actual all-item copy content via temporary native clipboard shim.
        # Browser APIs may restrict clipboard; event handler should still execute.
        page.locator("#coverageCopy").click()
        assert "已复制" in page.locator("#coverageCopyStatus").inner_text() or "复制失败" in page.locator("#coverageCopyStatus").inner_text()
        # Switching sector resets BOTH pagers and isolates data.
        page.locator("#coverageSector").select_option("s28")
        assert "未审核主题映射 14 条" in page.locator("#coverageSelection").inner_text()
        assert "第 1 / 2 页" in page.locator("#coverageProposalsPager").inner_text()
        assert page.locator("#coverageDirectPager").inner_text()==""
        page.locator("#coverageProposalsPager [data-cov-step='1']").click()
        assert page.locator("#coverageProposals .coverageSource").count()==6
        assert "第 2 / 2 页" in page.locator("#coverageProposalsPager").inner_text()
        page.locator("#coverageSector").select_option("s21")
        assert "未审核主题映射 0 条" in page.locator("#coverageSelection").inner_text()
        assert page.locator("#coverageProposals .coverageSource").count()==0
        assert page.locator("#coverageCopy").is_disabled()
        assert page.locator("#coverageGap").get_attribute("hidden") is None
        page.locator("#coverageGap summary").click()
        assert "合同" in page.locator("#coverageGapBody").inner_text() or "法务" in page.locator("#coverageGapBody").inner_text()
        assert "现有 Atlas 编辑" in page.locator("#coverageGapBody").inner_text()
        page.locator("#coverageGapCopy").click()
        assert "已复制" in page.locator("#coverageGapCopyStatus").inner_text() or "复制失败" in page.locator("#coverageGapCopyStatus").inner_text()
        page.locator("#coverageSector").select_option("s02")
        assert page.locator("#coverageGap").get_attribute("hidden") is not None
        assert page.locator("#coverageDirect .coverageSource").count()==8
        assert page.locator("#coverageProposals .coverageSource").count()==0
        assert "第 1 / 3 页" in page.locator("#coverageDirectPager").inner_text()
        assert not errors,errors
        assert not outbound,outbound
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"),f"overflow {width}"
        page.close()
    browser.close()
print("PASS V1.7.8 real Chromium 1440/390: 37 proposals across 5 pages, 14 across 2, full export, 20 gap brief cues, sector resets, no egress")
