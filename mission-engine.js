/* Atlas V1.6 — local, deterministic evidence-grounded matching. NOT an LLM or runtime. */
(function(root,factory){const api=factory();if(typeof module==="object"&&module.exports)module.exports=api;else root.AtlasMissionEngine=api;})(typeof window!=="undefined"?window:this,function(){
"use strict";
const PROFILES={
 education:{name:"教育与知识",keywords:["教育","课程","教学","讲义","课堂","练习","学生","复习","学习","知识","引用","字幕","education","lesson","learning","study","course","rag","retrieval","docling","edx","教材"],topics:["知识教育","AI研究","企业办公"],types:["tool","project","workflow","framework","mcp"],stages:[
 ["内容来源","检查使用权和来源记录","可追溯课程输入及来源授权清单"],
 ["知识处理","设计原文引用、分块及查证流程","证据片段与引用对照表"],
 ["练习交互","定义问题、弃答、人工复核条件","合成问答与教学测试集"],
 ["独立验收","验证引文覆盖、错误拒绝和数据隔离","验收报告与未通过项"]]},
 finance:{name:"金融与研究",keywords:["金融","投资","交易","量化","因子","预测","回测","价格","行情","风险","黄金","研究","portfolio","quant","finance","trading","factor","research","backtest","market","risk","qlib","lean","macro"],topics:["金融量化","AI研究","安全评测"],types:["framework","project","tool","workflow"],stages:[
 ["研究定义","冻结目标、数据许可、成本及样本外设计","研究假设与数据合同"],
 ["数据与实验","审查未来数据泄漏、样本选择和时间切分","可复现的合成实验与数据说明"],
 ["量化核验","加入点差佣金滑点和失效状态","成本后结果与反例报告"],
 ["风险审查","独立复核、禁止真实下单和收益承诺","人工审批清单与部署禁令"]]},
 growth:{name:"增长与客户",keywords:["增长","获客","营销","客户","crm","线索","转化","销售","广告","社媒","私信","表单","预约","lead","growth","marketing","sales","conversion","customer","crm","form","campaign","booking"],topics:["智能获客","自媒体运营","产品运营","增长分析","客户关系维护","业务自动化"],types:["workflow","tool","project","agent"],stages:[
 ["需求与同意","定义渠道、权限、合法来源和转化目标","合成客户旅程和同意合同"],
 ["线索整理","去重、来源归因、可撤销同意校验","去重后匿名线索清单"],
 ["人工交接","建立资格评估及审批责任","交接示例及退订测试"],
 ["度量与复核","验证误触达、错误分类及转化漏斗","可审计指标与停止条件"]]},
 content:{name:"内容与视频",keywords:["内容","视频","字幕","配音","剪辑","制作","直播","发布","短视频","媒体","文案","图文","video","caption","subtitle","render","content","media","edit","voice","publish","post"],topics:["AI视频制作","自媒体运营","产品运营"],types:["tool","project","workflow","agent"],stages:[
 ["脚本与版权","核验原始资料与媒体使用权","完整脚本及授权记录"],
 ["生产管线","明确视频、字幕和渲染输出接口","合成样片及时间戳"],
 ["质量审查","人工检查事实、字幕和品牌一致性","字幕抽检与审批清单"],
 ["合规发布","核验平台政策及发布授权","可复核发布计划"]]},
 engineering:{name:"Agent 与开发",keywords:["agent","skill","mcp","workflow","工具","开发","编程","代码","编排","插件","自动化","集成","api","python","coding","developer","agentic","orchestration","tool","gateway","browser","系统"],topics:["开发工程","多Agent协作","基础设施","技能目录","浏览器自动化","业务自动化"],types:["skill","mcp","agent","framework","workflow","tool"],stages:[
 ["任务合同","冻结任务、输入输出与可信边界","可检查的任务及工具合同"],
 ["组件选型","核对接口、版本、许可证与权限","候选矩阵和兼容性缺口"],
 ["隔离集成","在合成样本环境建立最小工作流","版本锁定的独立复现记录"],
 ["安全与交付","故障注入、审批、审计、回滚","失败门禁与交付清单"]]},
 governance:{name:"安全与治理",keywords:["安全","治理","审计","合规","许可","权限","隐私","评估","认证","控制","风控","risk","security","policy","audit","privacy","compliance","eval","evaluation","license","permission","guardrail"],topics:["安全评测","基础设施","开发工程","AI研究"],types:["security","mcp","framework","tool","skill"],stages:[
 ["风险识别","确定使用主体、授权和不可逆操作","威胁模型与数据分类"],
 ["控制设计","细分最小权限、人工批准及用途约束","权限矩阵和失败策略"],
 ["验证证据","测试不可信输入、越权和隐私泄漏","负向测试记录和审计样本"],
 ["上线门禁","正式安全/许可证审查与独立签字","未完成项目清单与拒绝条件"]]}
};
const PRIORITY={S:9,A:5,B:2};
function norm(s){return String(s||"").normalize("NFKC").toLowerCase().trim()}
function tokens(s){return norm(s).split(/[\s,，。;；:：/\\|()（）\-]+/u).filter(x=>x.length>=2).slice(0,35)}
function unique(x){return [...new Set(x)]}
function inferScenario(query,selected){
 if(selected&&selected!=="auto"&&PROFILES[selected])return selected;
 const q=norm(query),parts=tokens(q);
 const scores=Object.entries(PROFILES).map(([key,p])=>{
  const hit=p.keywords.reduce((n,word)=>n+(q.includes(norm(word))?(word.length>2?4:2):0),0);
  return {key,score:hit+parts.reduce((n,t)=>n+(p.keywords.some(word=>norm(word)===t)?2:0),0)};
 }).sort((a,b)=>b.score-a.score||a.key.localeCompare(b.key));
 return scores[0].score>0?scores[0].key:"engineering";
}
function validRepo(x){return !!x&&typeof x.repo==="string"&&/^[a-z\d_.-]+\/[a-z\d_.-]+$/i.test(x.repo)&&typeof x.topic==="string"&&typeof x.type==="string"&&x.verification==="repository-exists"}
function evidence(repo,meta,brief,asOf){
 const updated=Date.parse(asOf),pushed=Date.parse(meta?.last_push||"");
 const known=Number.isFinite(updated)&&Number.isFinite(pushed);
 const age=known?Math.max(0,Math.round((updated-pushed)/86400000)):null;
 const archived=meta?.archived===true;
 const freshness=archived?0:age===null?0:age<=90?20:age<=365?10:0;
 const source=10+(brief?.sources?.some(s=>s.kind==="official-github-readme")?20:0);
 const immutable=brief?.sources?.some(s=>/^[a-f\d]{40}$/i.test(s.git_blob_sha||""))?10:0;
 const isolated=repo.repo.toLowerCase()==="docling-project/docling"?25:0;
 return {total:source+immutable+freshness+isolated,source,immutable,freshness,isolated,
  ageDays:age,archived,license:meta?.license_spdx||"unknown",lastPush:meta?.last_push||null,
  officialBrief:!!brief,securityAudit:0,licenseReview:"NOT REVIEWED",verifiedIntegration:false};
}
function rank(query,scenario,curated,metadata,briefs,options={}){
 const area=PROFILES[scenario]||PROFILES.engineering,q=norm(query),words=tokens(query);
 const m=metadata?.repositories||{},ref=new Map((briefs?.entries||[]).map(x=>[norm(x.repo),x]));
 const asOf=metadata?.generated_at_utc||"";
 const items=(curated||[]).filter(validRepo).map(repo=>{
  const info=m[norm(repo.repo)]||m[repo.repo]||null,b=ref.get(norm(repo.repo)),ev=evidence(repo,info,b,asOf);
  const raw=[repo.name,repo.description_zh,repo.use_case,repo.repo].map(norm);
  const topic=area.topics.includes(repo.topic),type=area.types.includes(repo.type);
  const matched=unique(area.keywords.filter(k=>raw.some(s=>s.includes(norm(k)))||norm(repo.topic).includes(norm(k))));
  let fit=topic?42:8;fit+=type?14:0;fit+=Math.min(22,matched.length*5);
  const hitTerms=unique(words.filter(word=>raw.some(s=>s.includes(word))||norm(repo.topic).includes(word)));
  fit+=Math.min(20,hitTerms.length*7);
  fit+=PRIORITY[repo.priority]||0;
  if(ev.archived)fit-=30;
  fit=Math.max(0,Math.min(100,fit));
  const reasons=[topic?"命中该业务领域":"跨领域候选",type?"工具类型适配":null,
    matched.length?"场景关键词："+matched.slice(0,3).join("、"):null,
    hitTerms.length?"目标词："+hitTerms.slice(0,3).join("、"):null,
    b?"Top 30 官方来源档案":null].filter(Boolean);
  const blockers=["第三方安全与商业许可证尚未完成独立审查"];
  if(!info)blockers.push("GitHub 元数据缺失");
  if(ev.archived)blockers.push("GitHub 已归档");
  if(ev.license==="unknown"||ev.license==="NOASSERTION")blockers.push("许可证标识未知；必须人工核验");
  if(ev.ageDays===null||ev.ageDays>365)blockers.push("维护快照缺失或已较久无推送");
  if(repo.risk==="high")blockers.push("原 Atlas 标注高风险");
  return {repo:repo.repo,name:repo.name,description:repo.description_zh||"",useCase:repo.use_case||"",topic:repo.topic,type:repo.type,risk:repo.risk,
   url:repo.url,priority:repo.priority,fit,evidence:ev,reasons,blockers};
 }).sort((a,b)=>b.fit-a.fit||b.evidence.total-a.evidence.total||a.repo.localeCompare(b.repo));
 if(options.onlyMaintained)return items.filter(x=>!x.evidence.archived&&x.evidence.ageDays!==null&&x.evidence.ageDays<=365);
 return items;
}
function getStages(scenario){const p=PROFILES[scenario]||PROFILES.engineering;return p.stages.map(([title,task,output],i)=>({
 index:i+1,title,task,output,gate:(i===0||i===p.stages.length-1)?"必须人工审批":"人工复核",tool:null
}))}
function makePlan({goal,scenario,ranking,picks,stages,metadataTime}){
 const chosen=unique(picks).slice(0,5).map(name=>ranking.find(x=>x.repo===name)).filter(Boolean);
 const allowed=new Set(chosen.map(x=>x.repo));
 const mapped=(stages||getStages(scenario)).map((x,i)=>{
  const selected=typeof x.tool==="string"&&allowed.has(x.tool)?x.tool:null;
  return {index:i+1,title:x.title,task:x.task,output:x.output,gate:x.gate,candidate_repository:selected};
 });
 return {
  schema_version:1,version:"1.6.0",title:String(goal||"").trim().slice(0,240),
  scenario,scenario_label:PROFILES[scenario]?.name||"Agent 与开发",metadata_snapshot:metadataTime||null,
  status:"RESEARCH_PLAN_NOT_EXECUTED",source:"Atlas editor-curated repository snapshot",
  candidate_tools:chosen.map(x=>({repo:x.repo,url:x.url,fit_score_rule_based:x.fit,
   evidence_coverage:x.evidence.total,risk:x.risk,license_spdx_snapshot:x.evidence.license,
   source_brief:x.evidence.officialBrief,blockers:x.blockers})),
  phases:mapped,independent_3rd_party_integration_verified:false,
  required_approvals:["数据用途及隐私","第三方代码安全和许可证","接口兼容性和成本","真实环境测试和人工发布"],
  no_live_orders:true,no_real_user_data:true,no_api_credentials:true,
  disclaimer:"Rule-based research shortlist and unexecuted human-reviewed plan. Not LLM output, verified interoperability, code execution, production safety, or legal clearance."
 };
}
function toMarkdown(plan){
 const line=["# "+plan.title,"","场景："+plan.scenario_label,"研究快照："+(plan.metadata_snapshot||"未知"),"",
 "## 状态与范围","**"+plan.status+"**。尚未执行任何第三方组合。需要完成安全、许可证、权限和实际兼容性审查。","","## 工具候选"];
 for(const x of plan.candidate_tools)line.push("- **"+x.repo+"** — 规则场景相关度 "+x.fit_score_rule_based+"/100，研究证据覆盖 "+x.evidence_coverage+"/100；许可证快照："+x.license_spdx_snapshot+"。<"+x.url+">。阻断："+x.blockers.join("；"));
 line.push("","## 人工工作流与交接证据");
 for(const p of plan.phases)line.push("### "+p.index+". "+p.title,"任务："+p.task,"候选："+(p.candidate_repository||"待人工选择"),"输出："+p.output,"门禁："+p.gate,"");
 line.push("## 必要审批",...plan.required_approvals.map(x=>"- "+x),"","---",plan.disclaimer);
 return line.join("\n");
}
return {PROFILES,norm,inferScenario,validRepo,evidence,rank,getStages,makePlan,toMarkdown};
});