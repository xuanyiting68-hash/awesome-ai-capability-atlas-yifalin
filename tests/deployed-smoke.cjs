/* Read-only post-deployment checks. No accounts, third-party components or paid APIs. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const base=process.env.ATLAS_BASE_URL;
if(!base)throw Error('ATLAS_BASE_URL is required');
const errors=[];
(async()=>{
  const browser=await chromium.launch({headless:true,channel:process.env.ATLAS_BROWSER_CHANNEL||undefined});
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
    assert.equal(manifest.research_briefs_count,10,'Ten source-linked research briefs must be shipped');
    assert.equal(manifest.research_reviewed_count,0,'No third-party project is reviewed');
    await page.goto(new URL('top30.html?lang=en',base).href);
    await page.waitForFunction(n=>document.querySelectorAll('.item').length===n&&document.querySelector('#count').textContent.includes('Showing'),manifest.research_project_count);
    assert.equal(await page.locator('html').getAttribute('lang'),'en');
    assert.equal((await page.locator('#notices').innerText()).trim(),'','Production data and translations must load');
    await page.check('#briefOnly');
    assert.equal(await page.locator('.item').count(),manifest.research_briefs_count);
    assert.equal(new URL(page.url()).searchParams.get('brief'),'1');
    await page.reload();
    await page.waitForFunction(n=>document.querySelectorAll('.item').length===n,manifest.research_briefs_count);
    await page.click('#reset');
    await page.locator('.compare-button').first().click();assert.equal(await page.locator('#comparePanel').isVisible(),true);
    await page.locator('.favorite-button').first().click();await page.check('#favorites');assert.equal(await page.locator('.item').count(),1);
    await page.click('#reset');await page.selectOption('#domain','金融AI');assert.equal(await page.locator('.item').count(),8);
    await page.setViewportSize({width:390,height:844});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    await page.evaluate(()=>scrollTo(0,0));await fs.mkdir('test-results',{recursive:true});await page.screenshot({path:'test-results/deployed-mobile.png'});
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:844});
      await page.goto(base);
      await page.waitForSelector('.resource');
      assert.ok(await page.locator('.resource').count()>0,'Homepage must show actual resource cards');
      assert.ok(await page.locator('a[href="./blueprints.html"]').count()>0,'Homepage must link to blueprint hub');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Homepage horizontal overflow at '+width);
      await page.screenshot({path:'test-results/home-'+width+'.png'});
    }
    // Recovered project detail and workflow blueprints must be live, not orphaned source files.
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:844});
      await page.goto(new URL('project.html?repo=microsoft%2Fqlib',base).href);
      await page.waitForSelector('#body:not([hidden])');
      assert.match(await page.locator('#title').innerText(),/microsoft\/qlib/i);
      assert.equal(await page.locator('.quality-step').count(),5,'All five evidence tiers must be visible');
      assert.match(await page.locator('.quality-note').innerText(),/不等于|≠/);
      assert.equal(await page.locator('#briefCard').isVisible(),true,'Source-linked brief visible');
      assert.equal(await page.locator('#briefCapabilities li').count(),2,'Grounded claims rendered');
      assert.equal(await page.locator('#briefSteps li').count(),3,'Three proposed test steps rendered');
      assert.equal(await page.locator('#briefSources a').count(),3,'Official README, immutable blob and docs visible');
      assert.match(await page.locator('#briefDisclaimer').innerText(),/Fork HOLD/);
      await page.click('#briefLang');
      assert.equal(new URL(page.url()).searchParams.get('lang'),'en');
      assert.match(await page.locator('#briefAudience').innerText(),/Best for:/);
      assert.match(await page.locator('#briefPilotHeading').innerText(),/NOT executed/);
      await page.click('#briefLang');
      assert.equal(new URL(page.url()).searchParams.has('lang'),false);

      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Project detail horizontal overflow at '+width);
      await page.evaluate(()=>scrollTo(0,0));
      await page.screenshot({path:'test-results/project-'+width+'.png'});
      await page.goto(new URL('blueprints.html',base).href);
      await page.waitForFunction(()=>document.querySelectorAll('#cards .card').length===10);
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Blueprint horizontal overflow at '+width);
      await page.screenshot({path:'test-results/blueprints-'+width+'.png'});
    }
    // Each editorial pilot resolves; entries outside the first wave fail to an honest empty state.
    for(const name of ['langchain-ai/langgraph','remotion-dev/remotion','TwentyHQ/twenty',
      'microsoft/RD-Agent','docling-project/docling','langgenius/dify','SYSTRAN/faster-whisper',
      'formbricks/formbricks','promptfoo/promptfoo']){
      await page.goto(new URL('project.html?repo='+encodeURIComponent(name),base).href);
      await page.waitForSelector('#body:not([hidden])');
      assert.equal(await page.locator('#briefCard').isVisible(),true,'Missing pilot brief for '+name);
      assert.equal(await page.locator('#briefSources a').count(),3);
    }
    await page.goto(new URL('project.html?repo=AI4Finance-Foundation%2FFinRL',base).href);
    await page.waitForSelector('#body:not([hidden])');
    assert.equal(await page.locator('#briefCard').isVisible(),false);
    assert.equal(await page.locator('#briefEmpty').isVisible(),true,'Do not fabricate research for other projects');
    await page.goto(new URL('blueprints.html',base).href);
    await page.waitForFunction(()=>document.querySelectorAll('#cards .card').length===10);
    await page.locator('#domain').selectOption('视频工厂');
    assert.equal(await page.locator('#cards .card').count(),1);
    assert.equal(new URL(page.url()).searchParams.get('domain'),'视频工厂');
    console.log('PASS 10 evidence-linked bilingual briefs, 20 explicit gaps, three screen sizes and 10 blueprint domains');
    assert.deepEqual(errors,[],'No browser runtime errors');
    console.log('PASS deployed manifest, revision, bilingual data, comparison, bookmarks, filters, mobile width, homepage, zero runtime errors');
    console.log(JSON.stringify(manifest,null,2));
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
