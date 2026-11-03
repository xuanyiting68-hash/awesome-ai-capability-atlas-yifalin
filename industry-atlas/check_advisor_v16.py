#!/usr/bin/env python3
"""Isolated Chromium regression for YIFALIN V1.6 offline guided workspace.

Uses an in-page storage stub to verify opt-in persistence under Playwright's
opaque-origin testing restrictions. Not a production auth/storage integration.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parent
html=(ROOT/'advisor_v16.html').read_text(encoding='utf-8')
data=json.loads((ROOT/'advisor_v16_data.json').read_text(encoding='utf-8'))
assert (len(data['sectors']),len(data['subdomains']),len(data['tools']),len(data['learning']))==(32,133,114,69)
assert data['meta']['ai_runtime'] is False

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'],headless=True)
    for width,height in [(1440,900),(390,844)]:
        page=browser.new_page(viewport={'width':width,'height':height},accept_downloads=True)
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        # Real browser behavior for opaque-origin localStorage unavailable.
        page.set_content(html,wait_until='load')
        assert 'V1.6' in page.title()
        assert page.locator('#goals [data-goal]').count()==4
        assert page.locator('#nextTitle').inner_text()=='定义问题与验收基线'
        assert page.locator('#steps input').count()==5
        page.locator('#persist').click()
        assert not page.locator('#persist').is_checked(), 'Opaque origin must fail closed'
        assert '不支持本地保存' in page.locator('.message.bot').last.inner_text()
        # Natural language / source-linked results; never write raw prompt in URL.
        page.locator('#query').fill('我在证券资管做量化因子研究，需要整理内部研报代号xF-9324，并建立知识库')
        page.locator('#searchForm button').click()
        assert '量化金融与因子研究'==page.locator('#targetTitle').inner_text()
        assert 'xF-9324' not in page.url
        assert page.locator('#domain option').count()==8
        assert page.locator('#tools .resource a[href^="https://"]').count()>=1
        # Next action follows progress and allows writing notes in situ.
        page.locator('#steps input').first.check()
        assert '1/5' in page.locator('#taskCount').inner_text()
        assert '准备数据' in page.locator('#nextTitle').inner_text()
        page.locator('#nextGo').click()
        assert page.locator('#notesBox').get_attribute('open') is not None
        page.locator('#workNote').fill('10 个脱敏样本 + 两个失败案例；仅供内部模拟')
        assert '当前页面临时保存' in page.locator('#noteStatus').inner_text()
        # Compare up to three candidate tools, without claiming benchmark results.
        page.locator('#moreTools').click()
        assert page.locator('#tools [data-compare]').count()>=4
        checks=page.locator('#tools [data-compare]')
        for i in range(3): checks.nth(i).check()
        assert page.locator('#compare .comparison').count()==3
        assert '未完成实际兼容' in page.locator('#compare').inner_text()
        checks=page.locator('#tools [data-compare]');checks.nth(3).click()
        assert page.locator('#compare .comparison').count()==3
        assert '最多只能比较' in page.locator('#compareStatus').inner_text()
        # Changing industry must isolate notes and progress, restoring on return.
        page.locator('#query').fill('我是一名律师，在合同审核中减少重复工作')
        page.locator('#searchForm button').click()
        assert '合同审查与法务管理' in page.locator('#targetTitle').inner_text()
        assert page.locator('#workNote').input_value()==''
        assert '0/5' in page.locator('#taskCount').inner_text()
        page.locator('#query').fill('证券资管的量化因子研究')
        page.locator('#searchForm button').click()
        assert '10 个脱敏样本' in page.locator('#workNote').input_value()
        assert '1/5' in page.locator('#taskCount').inner_text()
        assert page.locator('#compare .comparison').count()==3
        # Context switch, user feedback and the no-match fail-closed behavior.
        page.locator('[data-goal="learn"]').click()
        assert page.locator('[data-goal="learn"]').get_attribute('aria-pressed')=='true'
        page.locator('[data-feedback="useful"]').click()
        assert page.locator('[data-feedback="useful"]').get_attribute('aria-pressed')=='true'
        page.locator('#query').fill('星际香蕉风铃神秘舞台')
        page.locator('#searchForm button').click()
        assert '还需要一点行业' in page.locator('#targetTitle').inner_text()
        assert page.locator('#nextGo').is_disabled()
        assert page.locator('#tools .resource').count()==0
        assert '0/5' in page.locator('#taskCount').inner_text()
        if width==390:
            assert page.locator('.mobileNav button').count()==4
            page.locator('[data-jump="conversation"]').click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        else:
            assert page.locator('.mobileNav').is_hidden()
        assert not errors,errors
        # Capture a useful example, not the no-match warning screen.
        page.locator('#query').fill('我在证券资管做量化金融研究，希望用 AI 建知识库并评估策略')
        page.locator('#searchForm button').click()
        page.screenshot(path=str(ROOT/f'advisor_v16_{width}.png'),full_page=True)
        page.close()
    # Simulated browser storage — only opt-in persistence, across page reinitialization.
    page=browser.new_page(viewport={'width':1440,'height':900})
    page.evaluate('''() => Object.defineProperty(window,'localStorage',{configurable:true,value:{m:{},setItem(k,v){this.m[k]=v},getItem(k){return this.m[k]||null},removeItem(k){delete this.m[k]}}})''')
    page.set_content(html)
    page.locator('#query').fill('我在证券资管做量化因子研究');page.locator('#searchForm button').click()
    page.locator('#persist').check()
    assert page.locator('#persist').is_checked()
    page.locator('#steps input').first.check()
    page.locator('#nextGo').click()
    page.locator('#workNote').fill('自愿保存的试点记录')
    assert page.evaluate("localStorage.getItem('yifalin-industry-v16')") is not None
    page.set_content(html)
    assert page.locator('#persist').is_checked()
    assert '1/5' in page.locator('#taskCount').inner_text()
    assert page.locator('#workNote').input_value()=='自愿保存的试点记录'
    page.locator('#clear').click()
    assert not page.locator('#persist').is_checked()
    assert page.evaluate("localStorage.getItem('yifalin-industry-v16')") is None
    page.close()
    browser.close()
print('PASS V1.6 offline guided workspace: intent, 3-way comparison, per-domain notes/progress, privacy, feedback, opt-in persistence, desktop/mobile')