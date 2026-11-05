/* Deterministic core verifier. Neural inference is tested separately with the actual model. */
const test=require("node:test"),assert=require("node:assert/strict"),fs=require("node:fs"),path=require("node:path");
const S=require("../semantic-core.js"),M=require("../mission-engine.js");
const source=n=>JSON.parse(fs.readFileSync(path.join(__dirname,"..","data",n),"utf8"));
const curated=source("curated.json"),metadata=source("repo_metadata.json"),briefs=source("research_briefs.json");
test("133 actual sources produce bounded 32-repository semantic shortlist",()=>{
 const ranked=M.rank("金融宏观市场与量化研究","finance",curated,metadata,briefs);
 assert.equal(ranked.length,133);
 const inputs=S.passagesFromRanked(ranked);
 assert.equal(inputs.length,32);assert.ok(inputs.every(x=>x.repo.includes("/")&&x.passage.length<=600));
 S.validInput("交易市场研究",inputs);
});
test("one neural query and one vector for each candidate, not fabricated confidence",()=>{
 const x=[{repo:"example/one",passage:"education textbook retrieval evidence and questions",fit:90},
          {repo:"example/two",passage:"financial market trading backtest study",fit:70}];
 const q=new Array(384).fill(0);q[0]=1;
 const pos=new Array(384).fill(0);pos[0]=1;
 const neg=new Array(384).fill(0);neg[1]=1;
 assert.equal(S.cosine(q,pos),1);assert.equal(S.cosine(q,neg),0);
 const rank=S.rerank(x,[q,neg,pos]);
 assert.equal(rank[0].repo,"example/two");
 assert.equal(rank[0].scoreType,"relative_cosine_NOT_probability");
 assert.equal(rank[0].modelRank,1);assert.equal(rank[0].ruleRank,2);
});
test("malicious text does not authorize extra repo or malformed vectors",()=>{
 const x=[{repo:"one/legit",fit:80,passage:"well documented tool for source-backed research"}];
 assert.throws(()=>S.validInput("good query",[{...x[0],repo:"javascript:steal"}]),/Invalid/);
 assert.throws(()=>S.validInput("good query",[x[0],x[0]]),/duplicate/);
 assert.throws(()=>S.validInput("good query",new Array(33).fill(x[0])),/bounded/);
 assert.throws(()=>S.rerank(x,[[1,2,3],[3,4,5]]),/embedding dimensions/);
 const v=new Array(384).fill(0);v[0]=Number.NaN;
 assert.throws(()=>S.rerank(x,[v,new Array(384).fill(1)]),/Nonfinite/);
});
test("page does not load external models until explicit user action and discloses download",()=>{
 const page=fs.readFileSync(path.join(__dirname,"..","semantic-studio.html"),"utf8");
 const worker=fs.readFileSync(path.join(__dirname,"..","semantic-worker.js"),"utf8");
 assert.match(page,/id="neural"/);
 assert.match(page,/首次可能超过 100 MB/);
 assert.match(page,/new Worker\("\.\/semantic-worker\.js"/);
 assert.match(page,/no-cache|no-store/);
 assert.ok(!page.includes("api.openai.com"));
 assert.ok(!page.includes("<script src=\"https://"));
 assert.match(worker,/self.onmessage=async/);
 assert.match(worker,/await initialize\(\)/);
 assert.match(worker,/cdn\.jsdelivr\.net\/npm\/@huggingface\/transformers@3\.8\.1/);
 assert.match(worker,/Xenova\/multilingual-e5-small/);
});
