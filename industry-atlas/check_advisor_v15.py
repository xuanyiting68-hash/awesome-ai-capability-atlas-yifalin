"""Chromium smoke for the V1.5 offline advisor.
Requires Playwright Python and Chromium. Uses system Chromium when available locally.
"""
from pathlib import Path
import json, os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parent
html=(ROOT/'advisor.html').read_text(encoding='utf-8')
data=json.loads((ROOT/'advisor_v15_data.json').read_text(encoding='utf-8'))
assert (len(data['sectors']),len(data['subdomains']),len(data['tools']),len(data['learning']))==(32,133,114,69)
assert '<script id="atlas-data"' in html and 'https://chatgpt.com/' in html

with sync_playwright() as p:
    args={'headless':True}
    if Path('/usr/bin/chromium').exists():args.update(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    browser=p.chromium.launch(**args)
    for w,h in ((1440,900),(390,844)):
        page=browser.new_page(viewport={'width':w,'height':h},accept_downloads=True)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='load')
        assert 'AI 行业任务顾问 V1.5' in page.title()
        assert page.locator('#steps input').count()==5
        assert '演示' in page.locator('#why').inner_text()
        # Fail closed when an opaque-origin browser blocks localStorage.
        page.locator('#persist').click()
        assert not page.locator('#persist').is_checked()
        assert '不支持本地保存' in page.locator('.message.bot').last.inner_text()
        # Natural language selects relevant sector and strictly scoped professional subdomain.
        page.locator('#query').fill('我在证券资管做量化因子研究，想建立研报知识库并复核回测结果')
        page.locator('#searchForm button').click()
        assert page.locator('#targetTitle').inner_text()=='量化金融与因子研究'
        assert '证券与资管' in page.locator('#breadcrumb').inner_text()
        assert '匹配' in page.locator('#why').inner_text() or '关键词' in page.locator('#why').inner_text()
        assert page.locator('#tools .resource').count()>=1
        # Follow-up retains sector context and includes actual tool URL sources.
        page.locator('#chatInput').fill('有哪些工具官网？')
        page.locator('#chatForm button').click()
        assert '量化金融与因子研究'==page.locator('#targetTitle').inner_text()
        assert page.locator('.message.bot').last.locator('a[href^="https://"]').count()>=1
        page.locator('#chatInput').fill('怎么自动化，但不要自动交易？')
        page.locator('#chatForm button').click()
        assert '审批' in page.locator('.message.bot').last.inner_text()
        # Plan is shown inline, no forced file download.
        assert page.locator('#steps input').count()==5
        page.locator('#steps input').first.check()
        assert page.locator('#taskCount').inner_text()=='1/5 完成'
        # Graph is interactive.
        page.locator('[data-stage="3"]').first.click()
        assert '人工基线' in page.locator('#nodeDesc').inner_text()
        # Domain dropdown contains only subdomains from selected industry.
        assert page.locator('#domain option').count()==8
        # Another explicit query changes industry and resets tasks.
        page.locator('#query').fill('工厂设备预测性维护，减少停机并做故障分析')
        page.locator('#searchForm button').click()
        assert page.locator('#targetTitle').inner_text()=='设备维护与故障预测'
        assert page.locator('#taskCount').inner_text()=='0/5 完成'
        assert page.locator('#domain option').count()==4
        assert '工业制造' in page.locator('#breadcrumb').inner_text()
        page.locator('#query').fill('我是一名律师，希望提升合同审核效率')
        page.locator('#searchForm button').click()
        assert '合同审查与法务管理' in page.locator('#targetTitle').inner_text()
        # Cross-domain disambiguation: explicit aviation / restaurant details win over generic tasks.
        page.locator('#query').fill('民航飞机维修管理')
        page.locator('#searchForm button').click()
        assert page.locator('#targetTitle').inner_text()=='航空与航运运营'
        page.locator('#query').fill('我在中餐厅管理预订和客户服务')
        page.locator('#searchForm button').click()
        assert page.locator('#targetTitle').inner_text()=='餐饮经营与菜品'
        # Unknown questions never inherit the previous industry.
        page.locator('#query').fill('香蕉风铃神秘舞台')
        page.locator('#searchForm button').click()
        assert '还需要一点行业' in page.locator('#targetTitle').inner_text()
        assert page.locator('#tools .resource').count()==0
        assert page.locator('#roles').inner_text()==''
        # Manual selection still works and stays within sector.
        page.locator('#manual summary').click()
        page.locator('#sector').select_option('s02')
        assert page.locator('#domain option').count()==8
        assert page.locator('#targetTitle').inner_text()=='量化金融与因子研究'
        # Downloads are purely optional.
        with page.expect_download() as dl:page.locator('#downloadPlan').click()
        assert dl.value.suggested_filename.endswith('.md')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
        assert not errors,errors
        if w==1440:page.screenshot(path=str(ROOT/'advisor_v15_desktop.png'),full_page=True)
        else:page.screenshot(path=str(ROOT/'advisor_v15_mobile.png'),full_page=True)
        page.close()
    browser.close()
print('PASS V1.5: 32 sectors/133 specialties/114 tools/69 sources, natural language retrieval, context, scoped dropdown, plan, graph, privacy state, downloads, desktop/mobile')
