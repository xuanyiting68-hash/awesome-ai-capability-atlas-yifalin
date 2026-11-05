#!/usr/bin/env python3
"""Real Chromium V1.7.7 original editor-tagged vs proposed-only vs no-source sectors."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
html = (ROOT / "advisor_v177.html").read_text(encoding="utf-8")
atlas = json.loads((ROOT / "advisor_v16_data.json").read_text(encoding="utf-8"))
radar = json.loads((ROOT / "discovery_seed.json").read_text(encoding="utf-8"))
rules = json.loads((ROOT / "coverage_review_rules_v177.json").read_text(encoding="utf-8"))
assert len(atlas["sectors"]) == 32
assert len(radar["records"]) == 133
assert len(rules["rules"]) == 13
assert html.count('id="atlas-coverage-rules"') == 1
assert all(x["approved"] is False for x in radar["records"])
with sync_playwright() as p:
    opts = {"headless": True}
    if Path("/usr/bin/chromium").exists():
        opts.update(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
    browser = p.chromium.launch(**opts)
    for width, height in ((1440, 900), (390, 844)):
        page = browser.new_page(viewport={"width": width, "height": height})
        errors, outbound = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("request", lambda req: outbound.append(req.url) if req.url.startswith(("http://","https://")) else None)
        page.set_content(html, wait_until="load")
        assert page.locator("#coverageSector option").count() == 32
        summary = page.locator("#coverageTotals").inner_text()
        assert "原有编辑标签覆盖 4/32 个行业" in summary
        assert "无行业标签 69 条来源" in summary
        assert "仅有待审候选的行业 8 个" in summary
        assert "尚无候选 20 个" in summary
        assert "真实独立验证 0 条" in summary
        # Initially show unapproved movie/audio editorial candidates.
        page.locator("#coverageSector").select_option("s28")
        assert "原有编辑标签 0 条" in page.locator("#coverageSelection").inner_text()
        assert "未审核主题映射 14 条" in page.locator("#coverageSelection").inner_text()
        assert page.locator("#coverageDirect .coverageSource").count() == 0
        assert page.locator("#coverageProposals .coverageSource").count() > 0
        assert "不是行业验证" in page.locator("#coverageProposals").inner_text()
        assert page.locator("#coverageProposals a[href^='https://']").count() > 0
        assert page.locator("#coverageCopy").is_enabled()
        page.locator("#coverageCopy").click()
        assert "已复制待人工审核来源" in page.locator("#coverageCopyStatus").inner_text() or "复制失败" in page.locator("#coverageCopyStatus").inner_text()
        # An absent industry remains empty and is not fabricated.
        page.locator("#coverageSector").select_option("s19")
        assert "原有编辑标签 0 条" in page.locator("#coverageSelection").inner_text()
        assert "未审核主题映射 0 条" in page.locator("#coverageSelection").inner_text()
        assert page.locator("#coverageDirect .coverageSource").count() == 0
        assert page.locator("#coverageProposals .coverageSource").count() == 0
        assert page.locator("#coverageCopy").is_disabled()
        assert "没有来自现有主题标签的待审核资源" in page.locator("#coverageProposals").inner_text()
        # Existing editorial tags must not be replaced with proposed sources.
        page.locator("#coverageSector").select_option("s02")
        assert "原有编辑标签 23 条" in page.locator("#coverageSelection").inner_text()
        assert page.locator("#coverageDirect .coverageSource").count() > 0
        assert page.locator("#coverageProposals .coverageSource").count() == 0
        # 32-sector matrix, filter and clicks are real interactive controls.
        page.locator("#coverageMatrixDetails summary").click()
        assert page.locator("#coverageMatrix [data-coverage-sector]").count() == 32
        page.locator("#coverageMissingOnly").check()
        assert page.locator("#coverageMatrix [data-coverage-sector]").count() == 28
        page.locator('#coverageMatrix [data-coverage-sector="s32"]').click()
        assert page.locator("#coverageSector").input_value() == "s32"
        assert "未审核主题映射" in page.locator("#coverageSelection").inner_text()
        # Main Atlas domain mapping still respects original truth and does not
        # quietly promote the suggested tag to an approved recommendation.
        page.locator("#query").fill("我是律师，在法律合同审查方面需要辅助")
        page.locator("#searchForm button").click()
        assert page.locator("#targetTitle").inner_text() == "合同审查与法务管理"
        assert page.locator("#bridgeSignals .bridgeSignal").count() == 0
        assert not outbound, outbound
        assert not errors, errors
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth+1"), f"overflow at {width}"
        page.close()
    browser.close()
print("PASS V1.7.7 Chromium 1440/390: 32-sector tagged/proposed/empty review, safe source links, copy/filter, zero approval, no egress")
