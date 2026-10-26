/* Read-only post-deployment checks. No accounts, third-party components or paid APIs. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const base=process.env.ATLAS_BASE_URL;
if(!base)throw Error('ATLAS_BASE_URL is required');
const errors=[];
(async()=>{
  const browser=await chromium.launch({headless:true});
  try{
    const context=await browser.newContext({viewport:{width:1440,height:1000}});
    // Limit the monitor to the published atlas, including its data files.
    await context.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());
    const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
    const response=await context.request.get(new URL('deployment.json',base).href);
    assert.equal(response.status(),200,'Deployment manifest must be available');
    const manifest=await response.json();
    assert.match(manifest.source_commit,/^[a-f0-9]{40}$/);
    if(process.env.EXPECTED_COMMIT)assert.equal(manifest.source_commit,process.env.EXPECTED_COMMIT,'Published commit must match the Pages run');
    assert.ok(manifest.catalog_count>=manifest.curated_count&&manifest.catalog_count<=5000);
    await page.goto(new URL('top30.html?lang=en',base).href);
    await page.waitForFunction(n=>document.querySelectorAll('.item').length===n&&document.querySelector('#count').textContent.includes('Showing'),manifest.research_project_count);
    assert.equal(await page.locator('html').getAttribute('lang'),'en');
    assert.equal((await page.locator('#notices').innerText()).trim(),'','Production data and translations must load');
    await page.locator('.compare-button').first().click();assert.equal(await page.locator('#comparePanel').isVisible(),true);
    await page.locator('.favorite-button').first().click();await page.check('#favorites');assert.equal(await page.locator('.item').count(),1);
    await page.click('#reset');await page.selectOption('#domain','金融AI');assert.equal(await page.locator('.item').count(),8);
    await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    await page.evaluate(()=>scrollTo(0,0));await fs.mkdir('test-results',{recursive:true});await page.screenshot({path:'test-results/deployed-mobile.png'});
    await page.goto(base);await page.waitForSelector('.resource');assert.ok(await page.locator('.resource').count()>0);
    assert.deepEqual(errors,[],'No browser runtime errors');
    console.log('PASS deployed manifest, revision, bilingual data, comparison, bookmarks, filters, mobile width, homepage, zero runtime errors');
    console.log(JSON.stringify(manifest,null,2));
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
