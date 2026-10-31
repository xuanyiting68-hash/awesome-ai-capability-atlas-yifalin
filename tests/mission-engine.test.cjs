/* Node-level invariant checks for sourced browser-local mission matching. */
const assert=require("node:assert/strict"),test=require("node:test"),fs=require("node:fs"),path=require("node:path");
const E=require("../mission-engine.js");
const data=n=>JSON.parse(fs.readFileSync(path.join(__dirname,"..","data",n),"utf8"));
const curated=data("curated.json"),meta=data("repo_metadata.json"),briefs=data("research_briefs.json");
test("real 133-source snapshot and Top30 metadata",()=>{
 assert.equal(curated.length,133);assert.equal(meta.coverage_count,133);assert.equal(briefs.entries.length,30);
 assert.ok(curated.every(E.validRepo));
});
test("Chinese goals infer six scenarios or fall back",()=>{
 assert.equal(E.inferScenario("将课程材料转成教学练习"),"education");
 assert.equal(E.inferScenario("金融量化因子回测和样本外研究"),"finance");
 assert.equal(E.inferScenario("营销获客CRM线索转化"),"growth");
 assert.equal(E.inferScenario("自动化视频字幕制作"),"content");
 assert.equal(E.inferScenario("工作任务","governance"),"governance");
 assert.equal(E.inferScenario("???"),"engineering");
});
test("all curated candidates rank without fabricated or certified outcomes",()=>{
 const found=E.rank("将公开课程内容变成带原文引用的互动练习","education",curated,meta,briefs);
 assert.equal(found.length,133);assert.equal(new Set(found.map(x=>x.repo)).size,133);
 assert.ok(found.every(x=>x.fit>=0&&x.fit<=100&&x.evidence.total>=0&&x.evidence.total<=100));
 assert.ok(found.every(x=>x.evidence.securityAudit===0&&x.evidence.licenseReview==="NOT REVIEWED"&&!x.evidence.verifiedIntegration));
 assert.ok(found.every(x=>x.blockers.some(b=>b.includes("独立审查"))));
 assert.ok(found.slice(0,8).some(x=>["知识教育","AI研究"].includes(x.topic)));
});
test("Top 30 source dossiers, license and freshness are never interpreted as certification",()=>{
 const q=E.rank("文档课程引用和证据","education",curated,meta,briefs);
 assert.equal(q.filter(x=>x.evidence.officialBrief).length,30);
 assert.ok(q.some(x=>x.evidence.license==="unknown"));
 assert.ok(q.every(x=>x.evidence.total<=85));
 const e=E.evidence({repo:"fake/example"}, {last_push:"2025-01-01",archived:true,license_spdx:"unknown"}, null,meta.generated_at_utc);
 assert.equal(e.freshness,0);assert.equal(e.archived,true);
});
test("maintenance only filter fails closed for missing or old metadata",()=>{
 const q=E.rank("工具编排","engineering",curated,meta,briefs,{onlyMaintained:true});
 assert.ok(q.length>15&&q.length<=133);
 assert.ok(q.every(x=>!x.evidence.archived&&x.evidence.ageDays!==null&&x.evidence.ageDays<=365));
});
test("research plans accept only shortlisted stages and preserve human gates",()=>{
 const ranked=E.rank("金融量化因子和样本外","finance",curated,meta,briefs);
 const chosen=ranked.slice(0,3).map(x=>x.repo);
 const stages=E.getStages("finance");stages[0].tool=chosen[0];stages[1].tool="malicious/not-in-shortlist";
 const plan=E.makePlan({goal:"金融风险研究",scenario:"finance",ranking:ranked,picks:chosen,stages,metadataTime:meta.generated_at_utc});
 assert.equal(plan.candidate_tools.length,3);assert.equal(plan.phases.length,4);
 assert.equal(plan.phases[0].candidate_repository,chosen[0]);assert.equal(plan.phases[1].candidate_repository,null);
 assert.equal(plan.status,"RESEARCH_PLAN_NOT_EXECUTED");assert.equal(plan.independent_3rd_party_integration_verified,false);
 assert.equal(plan.no_live_orders,true);assert.equal(plan.no_api_credentials,true);
 assert.ok(plan.required_approvals.length>=4);
 assert.ok(E.toMarkdown(plan).includes("尚未执行任何第三方组合"));
 assert.ok(E.toMarkdown(plan).includes(chosen[0]));
});
test("unsafe, unverified repository identifiers cannot enter matcher",()=>{
 const corrupt={...curated[0],repo:"javascript:alert(1)"};
 const missing={...curated[0],verification:"just_claimed_integrated"};
 const q=E.rank("agent","engineering",[corrupt,missing,curated[0]],meta,briefs);
 assert.equal(q.length,1);assert.equal(q[0].repo,curated[0].repo);
});
test("export stays a clearly unexecuted, source-backed study",()=>{
 const ranked=E.rank("客户获客与CRM","growth",curated,meta,briefs);
 const plan=E.makePlan({goal:"已授权潜客分类",scenario:"growth",ranking:ranked,picks:ranked.slice(0,4).map(x=>x.repo),stages:E.getStages("growth"),metadataTime:meta.generated_at_utc});
 assert.equal(plan.independent_3rd_party_integration_verified,false);
 assert.equal(plan.no_real_user_data,true);
 assert.ok(plan.candidate_tools.every(x=>x.blockers.length>0));
});
