/* Actual Chromium click -> public CDN + real WASM model -> neural UI reranking.
   Only original synthetic input, local test server, read-only GitHub Actions runner.
   Expected to fail if any real browser model dependency is blocked or unsupported.
 */
const {chromium}=require("playwright");
const {spawn}=require("node:child_process");
const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const port=8765,base="http://127.0.0.1:"+port+"/";
async function sleep(n){return new Promise(resolve=>setTimeout(resolve,n))}
(async()=>{
 const server=spawn("python3",["-m","http.server",String(port),"--bind","127.0.0.1"],{
  cwd:path.resolve(__dirname,".."),stdio:"ignore",env:process.env
 });
 let browser;
 try{
  let ready=false;
  for(let i=0;i<35;i++){try{const response=await fetch(base+"semantic-studio.html");if(response.ok){ready=true;break}}catch{}await sleep(250)}
  assert.ok(ready,"Loopback test server not ready");
  browser=await chromium.launch({headless:true});
  const context=await browser.newContext({viewport:{width:1280,height:840},serviceWorkers:"block"});
  const page=await context.newPage();const errors=[],external=[];
  page.on("pageerror",x=>errors.push(x.message));
  page.on("request",x=>{const url=x.url();if(url.startsWith("https://"))external.push(new URL(url).hostname)});
  await page.goto(base+"semantic-studio.html",{waitUntil:"domcontentloaded"});
  await page.waitForFunction(()=>document.querySelectorAll("#results .tool").length===18);
  assert.match(await page.locator("#status").innerText(),/规则筛选 133 个来源项目/);
  assert.equal(external.length,0,"Model assets must never download before explicit opt-in");
  await page.locator("#scenario").selectOption("education");
  await page.locator("#goal").fill("将公开课程讲义整理成带引用依据的互动教育练习");
  await page.locator("#neural").click();
  await page.waitForFunction(()=>document.querySelector("#status").textContent.includes("真实 E5 神经模型推理完成"),null,{timeout:300000});
  assert.equal(await page.locator("#results .tool").count(),18);
  assert.match(await page.locator("#results .tool").first().locator(".score").innerText(),/语义余弦/);
  const cosines=await page.locator("#results .tool .score").allTextContents();
  assert.ok(cosines.every(x=>x.includes("语义余弦")),"Real neural scores must be shown for each visible source");
  assert.ok(external.some(x=>x==="cdn.jsdelivr.net"),"User-initiated upstream JS download not observed");
  assert.ok(external.some(x=>x.includes("huggingface.co")||x.endsWith(".hf.co")),
    "User-initiated real model weights were not fetched");
  assert.deepEqual(errors,[],"Browser runtime exceptions");
  fs.mkdirSync("test-results",{recursive:true});
  await page.screenshot({path:"test-results/semantic-real-browser.png",fullPage:false});
  const result={schema_version:1,all_passed:true,
    executed:"actual Chromium site Worker WASM model on user click",
    local_query_only:true,initial_external_requests:0,
    model:"Xenova/multilingual-e5-small",model_scored_visible_repos:cosines.length,
    external_download_domains:[...new Set(external)].sort(),screenshot:"semantic-real-browser.png",
    no_paid_api:true,no_orders:true,full_supply_chain_review:false};
  fs.writeFileSync("test-results/semantic-real-browser.json",JSON.stringify(result,null,2)+"\n");
  console.log("PASS real browser opt-in model inference and 18 actual reranked repo cards");
 }finally{if(browser)await browser.close();server.kill("SIGTERM")}
})().catch(err=>{console.error(err);process.exitCode=1});
