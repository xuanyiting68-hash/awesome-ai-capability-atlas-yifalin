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
    assert.equal(manifest.research_briefs_count,30,'All Top 30 need source-linked editorial briefs');
    assert.equal(manifest.research_reviewed_count,0,'No third-party project is reviewed');
    assert.equal(manifest.pilot_contract_cases,24,'Frozen synthetic cases published');
    assert.equal(manifest.pilot_contract_passed,24,'First-party contract runner must match expectations');
    assert.equal(manifest.pilot_upstream_packages_executed,false,'No third-party packages have been run');
    assert.equal(manifest.star_shortlist_count,30,'All 30 source-linked bookmarks required');
    assert.equal(manifest.priority_integration_candidates,8,'Eight research candidates only');
    assert.equal(manifest.fork_approved_count,0,'No forks approved');
    assert.equal(manifest.star_actions_executed_by_atlas,0,'Never claim account changes');
    assert.equal(manifest.recipe_count,6,'Six sourced research recipes required');
    assert.equal(manifest.recipe_curated_tool_count,20,'Twenty unique sourced component candidates required');
    assert.equal(manifest.recipe_verified_integrations,0,'Never claim untested integrated workflows');
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
    // The network must be a published, sourced and accessible experience.
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:844});
      await page.goto(new URL('network.html',base).href);
      await page.waitForFunction(n=>document.querySelectorAll('#graph [data-repo]').length===n,manifest.research_project_count);
      assert.equal(await page.locator('#briefCount').innerText(),String(manifest.research_briefs_count));
      assert.equal(await page.locator('#graph .hub').count(),10,'Exactly ten documented business domains');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Network horizontal overflow '+width);
      if(width===390){
        assert.ok(await page.locator('#mobileCards .mobile-card').first().isVisible());
        const card=await page.locator('#mobileCards .mobile-card').first().boundingBox();
        assert.ok(card&&card.y<844,'Mobile capability map first item is buried offscreen');
      }
      await page.evaluate(()=>scrollTo(0,0));
      await page.screenshot({path:'test-results/network-staged-'+width+'.png'});
    }
    await page.check('#linked');
    assert.equal(await page.locator('#directory button').count(),manifest.research_briefs_count);
    await page.reload();await page.waitForFunction(n=>document.querySelectorAll('#directory button').length===n,manifest.research_briefs_count);
    assert.equal(await page.locator('#linked').isChecked(),true);
    await page.uncheck('#linked');
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:844});
      await page.goto(new URL('adoption.html',base).href);
      await page.waitForFunction(()=>document.querySelectorAll('#cards .card').length===30);
      assert.equal(await page.locator('#total').innerText(),'30');
      assert.equal(await page.locator('#focus').innerText(),'8');
      assert.equal(await page.locator('#fork').innerText(),'0');
      assert.equal(await page.locator('#done').innerText(),'0');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Star Pack horizontal overflow '+width);
      if(width===390){const card=await page.locator('#cards .card').first().boundingBox();assert.ok(card&&card.y<844,'First mobile Star Pack card should appear in the first screen');}
      assert.equal(await page.locator('.card .flag.hold').count(),30);
      await page.evaluate(()=>scrollTo(0,0));
      await page.screenshot({path:'test-results/adoption-'+width+'.png'});
    }
    await page.selectOption('#priority','P0');
    assert.equal(await page.locator('#cards .card').count(),8);
    await page.selectOption('#priority','all');
    await page.fill('#search','OpenBB');
    assert.equal(await page.locator('#cards .card').count(),1);
    assert.match(await page.locator('.card a.primary').getAttribute('href'),/github.com\/openbq-org\/OpenBB/);
    await page.fill('#search','');
    const pilotResponse=await context.request.get(new URL('data/pilot_lab_results.json',base).href);
    assert.equal(pilotResponse.status(),200);
    const pilot=await pilotResponse.json();
    assert.equal(pilot.total_cases,24);
    assert.equal(pilot.passed_cases,24);
    assert.equal(pilot.evaluates_upstream_packages,false);
    assert.equal(pilot.upstream_code_executed,false);
    assert.equal(pilot.trading_orders_sent,false);
    const fixtureResponse=await context.request.get(new URL('data/pilot_lab_cases.json',base).href);
    const fixtures=await fixtureResponse.json();
    assert.equal(fixtures.cases.length,24);
    assert.deepEqual(new Set(fixtures.cases.map(c=>c.project)),new Set(['graph','document','security']));
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:844});
      await page.goto(new URL('pilot-lab.html',base).href);
      await page.waitForFunction(()=>document.querySelectorAll('#records .case').length===24);
      assert.equal(await page.locator('.project').count(),3);
      assert.equal(await page.locator('#upstream').innerText(),'0');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Pilot Lab overflow '+width);
      await page.evaluate(()=>scrollTo(0,0));
      await page.screenshot({path:'test-results/pilot-lab-'+width+'.png'});
    }
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
    // Recipe Studio: static, sourced, bilingual and browser-local only.
    for(const width of [1440,768,390]){
      await page.setViewportSize({width,height:844});
      await page.goto(new URL('recipes.html?lang=en',base).href);
      await page.waitForFunction(()=>document.querySelectorAll('#cards .card').length===6);
      assert.equal(await page.locator('html').getAttribute('lang'),'en');
      assert.equal(await page.locator('#total').innerText(),'6');
      assert.equal(await page.locator('#projects').innerText(),'20');
      assert.match(await page.locator('#notice').innerText(),/NOT integrated|None of these compositions/i);
      const scores=await page.locator('.rubric strong').allTextContents();
      assert.equal(scores.length,6);
      assert.ok(scores.every(s=>Number(s)>0&&Number(s)<100),'No recipe can be certified by evidence-only score');
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'Recipe horizontal overflow '+width);
      if(width===390){
        const card=await page.locator('#cards .card').first().boundingBox();
        assert.ok(card&&card.y<844,'Mobile first recipe should be visible above fold');
      }
      await page.locator('#cards .card').first().locator('details summary').click();
      assert.ok(await page.locator('#cards .card').first().locator('.steps li').count()>=4);
      assert.match(await page.locator('#cards .card').first().locator('.steps li').first().innerText(),/Check topic and asset permissions/);
      await page.evaluate(()=>scrollTo(0,0));
      await page.screenshot({path:'test-results/recipes-'+width+'.png'});
    }
    await page.selectOption('#scenario','finance');
    assert.equal(await page.locator('#cards .card').count(),1);
    assert.equal(new URL(page.url()).searchParams.get('scenario'),'finance');
    await page.reload();
    await page.waitForFunction(()=>document.querySelectorAll('#cards .card').length===1);
    await page.click('#reset');
    assert.equal(await page.locator('#cards .card').count(),6);
    await page.selectOption('#level','beginner');
    assert.equal(await page.locator('#cards .card').count(),1);
    await page.click('#reset');
    // Existing repository favorites must be shared, but recipe favorites remain separate.
    await page.locator('.save-recipe').first().click();
    await page.check('#savedOnly');
    assert.equal(await page.locator('#cards .card').count(),1);
    assert.equal(await page.locator('#saved').innerText(),'1');
    assert.equal(await page.evaluate(()=>JSON.parse(localStorage.getItem('atlas_recipe_favorites_v1')).length),1);
    await page.uncheck('#savedOnly');
    await page.locator('.save-tool').first().click();
    assert.ok(await page.evaluate(()=>JSON.parse(localStorage.getItem('atlas_favorites_v1')).some(s=>s==='repo:remotion-dev/remotion')));
    await page.click('#language');
    assert.equal(await page.locator('html').getAttribute('lang'),'zh-CN');
    assert.equal(new URL(page.url()).searchParams.has('lang'),false);
    await page.fill('#search','nonexistent---recipe');
    assert.equal(await page.locator('#cards .card').count(),0);
    assert.equal(await page.locator('#empty').isVisible(),true);
    await page.click('#reset');
    assert.equal(await page.locator('#cards .card').count(),6);
    assert.ok(await page.locator('a[href="./recipes.html"]').count()===0,'Recipe page should not link to itself in navbar');
    await page.goto(base);
    assert.ok(await page.locator('a[href="./recipes.html"]').count()>=1,'Home must expose Recipe Studio');
    // Validate every official-source project dossier, not a hard-coded previous wave.
    const sourceResult=await context.request.get(new URL('data/research_briefs.json',base).href);
    assert.equal(sourceResult.status(),200);
    const sourceData=await sourceResult.json();
    assert.equal(sourceData.entries.length,30,'All 30 briefs in published research bundle');
    for(const item of sourceData.entries){
      await page.goto(new URL('project.html?repo='+encodeURIComponent(item.repo),base).href);
      await page.waitForSelector('#body:not([hidden])');
      assert.equal(await page.locator('#briefCard').isVisible(),true,'Missing dossier for '+item.repo);
      assert.equal(await page.locator('#briefSources a').count(),3,'Source link or Git blob missing for '+item.repo);
      assert.equal(await page.locator('#briefEmpty').isVisible(),false);
      assert.match(await page.locator('#briefDisclaimer').innerText(),/Fork HOLD/);
    }
    // A fabricated repository identifier is rejected instead of receiving an invented profile.
    await page.goto(new URL('project.html?repo=fake%2Fnonexistent',base).href);
    await page.waitForFunction(()=>document.querySelector('#title').textContent==='项目暂不可用');
    assert.equal(await page.locator('#body').isVisible(),false);
    await page.goto(new URL('blueprints.html',base).href);
    await page.waitForFunction(()=>document.querySelectorAll('#cards .card').length===10);
    await page.locator('#domain').selectOption('视频工厂');
    assert.equal(await page.locator('#cards .card').count(),1);
    assert.equal(new URL(page.url()).searchParams.get('domain'),'视频工厂');
    console.log('PASS all 30 source-linked bilingual dossiers, 30-URL link checks, three viewport widths and 10 blueprint domains');
    assert.deepEqual(errors,[],'No browser runtime errors');
    console.log('PASS deployed manifest, revision, bilingual data, comparison, bookmarks, filters, mobile width, homepage, zero runtime errors');
    console.log(JSON.stringify(manifest,null,2));
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
