#!/usr/bin/env node
/* Actual E5-weight-backed, source-grounded research task tool.
 * Closed input: goal + 1 of 6 scenarios; read-only original curated repo snapshots.
 * No user-uploaded files, no network search/scraping, no browser/OS/tool execution.
 */
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {createRequire} from "node:module";
import {pipeline} from "@huggingface/transformers";
const require=createRequire(import.meta.url);
const M=require("../mission-engine.js");
const S=require("../semantic-core.js");
const VERSION="3.8.1";
const installed=require("@huggingface/transformers/package.json");
if(installed.version!==VERSION)throw Error("Pinned model SDK version drift");
const ROOT=new URL("../",import.meta.url);
const read=n=>{
 const bytes=readFileSync(new URL(n,ROOT));
 return {value:JSON.parse(bytes.toString("utf8")),sha256:createHash("sha256").update(bytes).digest("hex")};
};
let raw="";
for await (const chunk of process.stdin){
 raw+=chunk;
 if(raw.length>2000)throw Error("Task input too large");
}
const task=JSON.parse(raw);
if(!task||typeof task.goal!=="string"||task.goal.trim().length<12||task.goal.length>240)
 throw Error("Goal must be 12..240 characters");
if(!Object.prototype.hasOwnProperty.call(M.PROFILES,task.scenario))
 throw Error("Unknown scenario, fail closed");
if(Object.keys(task).sort().join(",")!=="goal,scenario")
 throw Error("Unexpected task input fields");
const curated=read("data/curated.json"),meta=read("data/repo_metadata.json"),briefs=read("data/research_briefs.json");
if(!Array.isArray(curated.value)||curated.value.length!==133||meta.value.coverage_count!==133
 ||!Array.isArray(briefs.value.entries)||briefs.value.entries.length!==30)
 throw Error("Actual repository source contract invalid");
const ranked=M.rank(task.goal,task.scenario,curated.value,meta.value,briefs.value);
if(ranked.length!==133||ranked.some(x=>x.evidence.verifiedIntegration||x.evidence.licenseReview!=="NOT REVIEWED"))
 throw Error("Unsourced or falsely certified candidate data");
const pool=S.passagesFromRanked(ranked,16);
S.validInput(task.goal,pool);
const model=await pipeline("feature-extraction",S.MODEL,{dtype:"q8"});
const texts=["query: "+task.goal,...pool.map(x=>"passage: "+x.passage)];
const rows=[];
for(let n=0;n<texts.length;n+=6){
 const output=await model(texts.slice(n,n+6),{pooling:"mean",normalize:true});
 const value=output.tolist();
 if(!Array.isArray(value)||value.length!==Math.min(6,texts.length-n)
    ||!value.every(v=>Array.isArray(v)&&v.length===384&&v.every(Number.isFinite)))
   throw Error("Real model returned invalid 384D embeddings");
 rows.push(...value);
}
const neural=S.rerank(pool,rows),lookup=new Map(ranked.map(x=>[x.repo,x]));
if(neural.length!==16||neural.some(x=>!lookup.has(x.repo)))throw Error("Model escaped curated shortlist");
const selected=neural.slice(0,4).map((x,i)=>{
 const src=lookup.get(x.repo);
 if(src.url!=="https://github.com/"+src.repo)throw Error("Untrusted source URL");
 return {
  rank:i+1,repo:x.repo,source_url:src.url,description:src.description,
  use_case:src.useCase,topic:src.topic,type:src.type,
  similarity_cosine:Number(x.cosine.toFixed(6)),rule_fit:src.fit,
  research_evidence_coverage:src.evidence.total,
  license_snapshot:src.evidence.license,
  updated_at_snapshot:src.evidence.lastPush,
  risk:src.risk,reviewed_for_security:false,reviewed_for_commercial_use:false,
  verified_tool_compatibility:false,
  blockers:src.blockers
 };
});
const output={
 schema_version:1,kind:"actual_neural_research_tool",
 model:S.MODEL,model_sdk_version:S.SDK,quantization:"q8",
 executed_neural_inference:true,embeddings_computed:rows.length,dimensions:384,
 similarity_is_confidence:false,tool_calls:1,external_action_calls:0,
 source_snapshot_sha256:{
  curated:curated.sha256,repo_metadata:meta.sha256,research_briefs:briefs.sha256
 },
 candidate_pool_size:pool.length,selected,
 source_commit_certification:false,security_certified:false,
 details:"Top 16 RULE-filtered curated projects are NEURAL-reranked; model never executes a repository."
};
process.stdout.write(JSON.stringify(output)+"\n");
