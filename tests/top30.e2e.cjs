/* Real Chromium checks. Start a local server, or set ATLAS_BASE_URL for deployed smoke tests. */
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const http = require('node:http');
function reachable(url) { return new Promise(resolve => { const request = http.get(url, response => {response.resume();resolve(response.statusCode === 200)}); request.on('error', () => resolve(false)); request.setTimeout(500, () => request.destroy()); }); }
const fs = require('node:fs/promises');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');
const base = process.env.ATLAS_BASE_URL || 'http://127.0.0.1:8766/';
let server, browser, passed = 0;
const errors = [];
async function check(name, fn) { await fn(); passed++; console.log(`PASS ${name}`); }
async function open(query = '', setup) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  // Test only our static application. Do not contact indexed repositories or run upstream code.
  await context.route('**/*', route => route.request().url().startsWith(base) ? route.continue() : route.abort());
  const page = await context.newPage();
  page.on('pageerror', e => errors.push(e.message));
  if (setup) await setup(context, page);
  await page.goto(new URL('top30.html' + query, base).href);
  return { context, page };
}
async function loaded(page) { await page.waitForFunction(() => document.querySelector('#count').textContent.includes('30') && document.querySelectorAll('.item').length === 30); }
(async () => {
  if (!process.env.ATLAS_BASE_URL) {
    // Test the same packaged assets that Pages publishes, not raw repository files.
    // This catches missing allowlisted pages and required deployment manifests locally.
    const staged = spawnSync('python', ['scripts/build_site.py'], {encoding:'utf-8'});
    if(staged.status !== 0)throw Error('Unable to stage public site before browser checks: '+staged.stderr);
    server = spawn('python', ['-m', 'http.server', '8766', '--bind', '127.0.0.1', '--directory', '_site'], { stdio: 'ignore' });
    for (let i = 0; i < 40; i++) {
      if (await reachable(base)) break;
      await new Promise(resolve => setTimeout(resolve, 100));
    }
  }
  browser = await chromium.launch({ headless: true, channel: process.env.ATLAS_BROWSER_CHANNEL || undefined });
  await fs.mkdir('test-results', { recursive: true });
  let {context, page} = await open();
  await check('30 cards and metadata/evidence', async () => {
    await loaded(page);
    assert.equal(await page.locator('.item').count(), 30);
    assert.match(await page.locator('.item').first().innerText(), /SPDX/);
    await page.locator('.item details').first().locator('summary').click();
    assert.match(await page.locator('.item details').first().innerText(), /HOLD/);
    assert.match(await page.locator('.item details').first().innerText(), /未记录/);
  });
  await check('source-linked editorial filter and restorable URL', async () => {
    await page.check('#briefOnly');
    assert.equal(await page.locator('.item').count(),30);
    assert.equal(new URL(page.url()).searchParams.get('brief'),'1');
    assert.match(await page.locator('.item').first().innerText(),/官方资料研究/);
    await page.reload();
    await page.waitForFunction(()=>document.querySelectorAll('.item').length===30);
    assert.equal(await page.locator('#briefOnly').isChecked(),true);
    await page.click('#reset');
    assert.equal(await page.locator('.item').count(),30);
    assert.equal(new URL(page.url()).searchParams.has('brief'),false);
  });
  await check('all Top 30 now have source-linked editorial badges',async()=>{
    await page.click('#reset');
    await page.waitForFunction(()=>document.querySelectorAll('.item').length===30);
    assert.equal(await page.locator('.item').filter({hasText:/官方资料研究|Official-source desk study/}).count(),30);
  });
  await check('domain, priority, status and reset', async () => {
    await page.selectOption('#domain', '金融AI');
    assert.equal(await page.locator('.item').count(), 8);
    await page.selectOption('#priority', 'S');
    assert.equal(await page.locator('.item').count(), 5);
    await page.selectOption('#status', 'tested');
    assert.equal(await page.locator('.item').count(), 0);
    assert.equal(await page.locator('#export').isDisabled(), true);
    await page.click('#reset');
    assert.equal(await page.locator('.item').count(), 30);
  });
  await check('bilingual content, search and document language', async () => {
    await page.click('#language');
    assert.equal(await page.locator('html').getAttribute('lang'), 'en');
    assert.match(await page.locator('.item').first().innerText(), /Quantitative research/);
    await page.fill('#search', 'subtitles');
    assert.equal(await page.locator('.item').count(), 1);
    assert.match(await page.locator('.item').innerText(), /faster-whisper/);
    await page.click('#reset');
  });
  await check('four-way comparison, limit and individual removal', async () => {
    for (let n=0;n<4;n++) await page.locator('.compare-button').nth(n).click();
    assert.equal(await page.locator('#compareContent thead th').count(), 5);
    await page.locator('.compare-button').nth(4).click();
    assert.match(await page.locator('#feedback').innerText(), /up to 4/);
    assert.equal(await page.locator('#compareContent thead th').count(), 5);
    await page.locator('[data-remove]').first().click();
    assert.equal(await page.locator('[data-remove]').count(), 3);
    await page.click('#clearCompare');
    assert.equal(await page.locator('#comparePanel').isVisible(), false);
  });
  await check('bookmark survives reload and uses shared catalog key', async () => {
    await page.locator('.favorite-button').first().click();
    await page.check('#favorites');
    assert.equal(await page.locator('.item').count(), 1);
    assert.deepEqual(await page.evaluate(() => JSON.parse(localStorage.getItem('atlas_favorites_v1'))), ['repo:microsoft/qlib']);
    await page.reload(); await loaded(page);
    assert.equal(await page.locator('#savedTotal').innerText(), '1');
    assert.equal(await page.locator('.favorite-button').first().getAttribute('aria-pressed'), 'true');
  });
  await check('URL restores filters, comparison and language without favorites', async () => {
    await page.selectOption('#domain', '金融AI');
    await page.locator('.compare-button').first().click();
    await page.check('#favorites');
    assert.ok(!page.url().includes('favorites'));
    const url = page.url();
    await page.goto(url);
    await page.waitForFunction(() => document.querySelectorAll('.item').length===8 && document.querySelector('#count').textContent.includes('30'));
    assert.equal(await page.locator('#domain').inputValue(), '金融AI');
    assert.equal(await page.locator('html').getAttribute('lang'), 'en');
    assert.equal(await page.locator('#comparePanel').isVisible(), true);
    await page.click('#reset'); await page.click('#clearCompare');
  });
  await check('export contains exactly current filtered rows', async () => {
    await page.fill('#search', 'microsoft/qlib');
    const downloadPromise = page.waitForEvent('download'); await page.click('#export');
    const download = await downloadPromise;
    const text = await fs.readFile(await download.path(), 'utf8');
    assert.equal(text.trim().split('\r\n').length, 2);
    assert.match(text, /microsoft\/qlib/);
    await page.click('#reset');
  });
  await check('CSV formula neutralization and CSV parser', async () => {
    const values = await page.evaluate(() => ['=1+1',' +cmd','@SUM(A1)','-1','\tformula','ordinary'].map(csvCell));
    for(const s of values.slice(0,5)) assert.ok(s.startsWith('"\''));
    assert.equal(values[5], '"ordinary"');
    assert.deepEqual(await page.evaluate(() => parseCSV('a,b\r\n"line\nnext","say ""hi"""\r\n')), [['a','b'],['line\nnext','say "hi"']]);
  });
  await check('metadata filters and deterministic stars sorting', async () => {
    await page.selectOption('#license', 'detected');
    assert.ok(await page.locator('.item').count()>0);
    await page.selectOption('#license', 'unknown');
    assert.ok(await page.locator('.item').count()<30);
    await page.click('#reset');
    await page.selectOption('#sort', 'stars');
    assert.ok(await page.evaluate(() => visible.every((r,i) => !i || (metadata(visible[i-1])?.stars??-1)>=(metadata(r)?.stars??-1))));
  });
  await check('desktop layout and external link boundaries', async () => {
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:'test-results/top30-desktop.png'});
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth), true);
    for(const href of await page.locator('#results a[target=_blank]').evaluateAll(a=>a.map(e=>e.href))) assert.match(href,/^https:\/\/(github\.com|api\.github\.com)\//);
  });
  await check('mobile page width, controls and comparison', async () => {
    await page.setViewportSize({width:390,height:844});
    await page.locator('.compare-button').nth(0).click();
    await page.locator('.compare-button').nth(1).click();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth), true);
    await page.evaluate(()=>window.scrollTo(0,0));
    const searchBox=await page.locator('#search').boundingBox();
    assert.ok(searchBox && searchBox.y + searchBox.height < 844,
      'Mobile search must be accessible in the first viewport, not buried below metrics');
    await page.screenshot({path:'test-results/top30-mobile.png'});
  });
  await check('interactive capability network, source filter, keyboard and three viewports', async()=>{
    const visual=await context.newPage();visual.on('pageerror',e=>errors.push(e.message));
    await visual.goto(new URL('network.html',base).href);
    await visual.waitForFunction(()=>document.querySelectorAll('#graph [data-repo]').length===30 && document.querySelector('#briefCount').textContent==='10');
    assert.equal(await visual.locator('#graph .hub').count(),10);
    assert.equal(await visual.locator('#directory button').count(),30);
    assert.equal(await visual.locator('#catalogCount').innerText(),'5,000');
    await visual.fill('#search','Qlib');
    assert.equal(await visual.locator('#directory button').count(),1);
    assert.match(await visual.locator('#detail').innerText(),/Qlib|qlib/i);
    await visual.fill('#search','');
    await visual.check('#linked');
    assert.equal(await visual.locator('#directory button').count(),10);
    assert.equal(new URL(visual.url()).searchParams.get('sourced'),'1');
    await visual.reload();
    await visual.waitForFunction(()=>document.querySelectorAll('#directory button').length===10);
    await visual.uncheck('#linked');
    await visual.selectOption('#domain','安全评测');
    assert.equal(await visual.locator('#directory button').count(),1);
    assert.match(await visual.locator('#detail').innerText(),/promptfoo/);
    await visual.selectOption('#domain','');
    await visual.locator('#graph [data-repo="microsoft/qlib"]').focus();
    await visual.keyboard.press('Enter');
    assert.equal(new URL(visual.url()).searchParams.get('repo'),'microsoft/qlib');
    await visual.click('#language');
    assert.equal(await visual.locator('html').getAttribute('lang'),'en');
    assert.match(await visual.locator('#detail').innerText(),/Best for/);
    for(const width of [1440,768,390]){
      await visual.setViewportSize({width,height:844});
      await visual.evaluate(()=>scrollTo(0,0));
      assert.equal(await visual.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Network overflow '+width);
      if(width===390){
        assert.equal(await visual.locator('#mobileCards .mobile-card').first().isVisible(),true);
        assert.equal(await visual.locator('#graph').isVisible(),false);
        const card=await visual.locator('#mobileCards .mobile-card').first().boundingBox();
        assert.ok(card&&card.y<844,'First mobile network card must appear in the first screen');
      }
      await visual.screenshot({path:'test-results/network-'+width+'.png'});
    }
    await visual.close();
  });
  await context.close();
  await check('missing metadata and evidence degrade without losing projects', async () => {
    const o=await open('?lang=en',async c=>{await c.route('**/data/repo_metadata.json',r=>r.fulfill({status:503,body:'unavailable'}));await c.route('**/data/top30_evidence.json',r=>r.fulfill({status:503,body:'unavailable'}))});
    await loaded(o.page);
    assert.match(await o.page.locator('#notices').innerText(),/Metadata unavailable/);
    assert.match(await o.page.locator('.item').first().innerText(),/No metadata/);
    await o.page.selectOption('#license','unknown');assert.equal(await o.page.locator('.item').count(),30);
    await o.context.close();
  });
  await check('stale evidence is disabled', async () => {
    const snapshot=JSON.parse(await fs.readFile('data/top30_evidence.json','utf8'));snapshot.generated_from_snapshot_utc='2000-01-01T00:00:00Z';
    const o=await open('?lang=en',async c=>c.route('**/data/top30_evidence.json',r=>r.fulfill({json:snapshot})));
    await loaded(o.page);assert.match(await o.page.locator('#notices').innerText(),/dates differ/);
    assert.equal(await o.page.evaluate(()=>Object.keys(evidence).length),0);
    await o.context.close();
  });
  await check('storage denial is recoverable', async () => {
    const o=await open('?lang=en',async c=>c.addInitScript(()=>{Object.defineProperty(window,'localStorage',{get(){throw Error('disabled')}})}));
    await loaded(o.page);await o.page.locator('.favorite-button').first().click();await o.page.check('#favorites');
    assert.equal(await o.page.locator('.item').count(),1);assert.match(await o.page.locator('#notices').innerText(),/storage is unavailable/);
    await o.context.close();
  });
  await check('malicious project URL fails closed', async () => {
    const csv=await fs.readFile('data/top30_evaluation.csv','utf8');
    const o=await open('?lang=en',async c=>c.route('**/data/top30_evaluation.csv',r=>r.fulfill({body:csv.replace('https://github.com/microsoft/qlib','javascript:alert(1)')})));
    await o.page.waitForSelector('#retry');assert.equal(await o.page.locator('.item').count(),0);
    assert.equal(await o.page.locator('#export').isDisabled(),true);
    await o.page.click('#language');assert.equal(await o.page.locator('#retry').isVisible(),true);
    assert.match(await o.page.locator('#count').innerText(),/加载失败/);await o.context.close();
  });
  await check('metadata strings render as text', async () => {
    const metadata=JSON.parse(await fs.readFile('data/repo_metadata.json','utf8'));metadata.repositories['microsoft/qlib'].license_spdx='<img src=x onerror=alert(1)>';
    const o=await open('?lang=en',async c=>c.route('**/data/repo_metadata.json',r=>r.fulfill({json:metadata})));
    await loaded(o.page);assert.equal(await o.page.locator('.item img').count(),0);assert.match(await o.page.locator('.item').first().innerText(),/<img/);await o.context.close();
  });
  await check('homepage still loads with shared bookmarks and safe CSV export', async () => {
    const c=await browser.newContext();await c.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());const p=await c.newPage();p.on('pageerror',e=>errors.push(e.message));
    await p.goto(base);await p.waitForSelector('.resource');assert.ok(await p.locator('.resource').count()>0);
    assert.match(await p.evaluate(()=>csvCell('=HYPERLINK("x")')),/^"?'/);await c.close();
  });
  assert.deepEqual(errors,[],'No browser runtime errors');
  console.log(`PASS ${passed} browser scenarios; zero runtime errors`);
})().catch(error => {console.error(error);process.exitCode=1}).finally(async()=>{if(browser)await browser.close();if(server)server.kill()});
