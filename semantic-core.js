/* Pure, deterministic retrieval glue; real neural vectors supplied only by optional open model.
 No model download, IO, execution, keys or user data collection in this module. */
(function(root,factory){
 const api=factory();if(typeof module==="object"&&module.exports)module.exports=api;
 else root.AtlasSemantic=api;
})(typeof window!=="undefined"?window:this,function(){
"use strict";
const MODEL="Xenova/multilingual-e5-small";
const SDK="3.8.1";
const MAX_CANDIDATES=32;
function validInput(query,items){
 if(typeof query!=="string"||query.trim().length<3||query.length>300)throw Error("Query must be 3–300 characters");
 if(!Array.isArray(items)||items.length===0||items.length>MAX_CANDIDATES)throw Error("Candidate count exceeds bounded local inference");
 const seen=new Set();
 for(const x of items){
  if(!x||typeof x.repo!=="string"||!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(x.repo)||seen.has(x.repo.toLowerCase()))throw Error("Invalid or duplicate sourced repo");
  if(typeof x.passsage!=="undefined")throw Error("Unexpected passage spelling");
  if(typeof x.passage!=="string"||x.passage.length<8||x.passage.length>600)throw Error("Passage must have bounded sourced text");
  seen.add(x.repo.toLowerCase());
 }
}
function passagesFromRanked(ranked,count=MAX_CANDIDATES){
 if(!Array.isArray(ranked))throw Error("Ranked items must be an array");
 return ranked.slice(0,Math.min(MAX_CANDIDATES,Math.max(1,Number(count)||MAX_CANDIDATES))).map(x=>({
  repo:x.repo,fit:x.fit,
  passage:[x.repo,x.description,x.useCase,x.topic,x.type].filter(Boolean).join(" · ").slice(0,590)
 }));
}
function cosine(a,b){
 if(!Array.isArray(a)||!Array.isArray(b)||a.length!==b.length||a.length<64||a.length>4096)throw Error("Invalid embedding dimensions");
 let sum=0,na=0,nb=0;
 for(let i=0;i<a.length;i++){const x=a[i],y=b[i];if(!Number.isFinite(x)||!Number.isFinite(y))throw Error("Nonfinite embedding");sum+=x*y;na+=x*x;nb+=y*y}
 if(!na||!nb)throw Error("Zero embedding norm");
 return Math.max(-1,Math.min(1,sum/Math.sqrt(na*nb)));
}
function rerank(items,vectorRows){
 if(!Array.isArray(vectorRows)||vectorRows.length!==items.length+1)throw Error("One query plus one vector per candidate required");
 const first=vectorRows[0];
 const out=items.map((item,i)=>({
  repo:item.repo,fit:Number(item.fit)||0,cosine:cosine(first,vectorRows[i+1]),ruleRank:i+1
 }));
 out.sort((a,b)=>b.cosine-a.cosine||b.fit-a.fit||a.repo.localeCompare(b.repo));
 return out.map((x,i)=>({...x,modelRank:i+1,scoreType:"relative_cosine_NOT_probability"}));
}
return {MODEL,SDK,MAX_CANDIDATES,validInput,passagesFromRanked,cosine,rerank};
});