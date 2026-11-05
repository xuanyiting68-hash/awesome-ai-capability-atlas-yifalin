/* Dedicated opt-in model execution worker.
 User prompt is never included in any fetch URI or outbound request body.
 Network only occurs on explicit click: fixed SDK CDN, fixed public model assets.
 */
let extractor=null,lastProgress="";
async function initialize(){
 if(extractor)return extractor;
 postMessage({type:"status",message:"正在加载本地推理引擎；首次需要下载公开模型文件…"});
 const sdk=await import("https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1");
 extractor=await sdk.pipeline("feature-extraction","Xenova/multilingual-e5-small",{
   dtype:"q8",
   progress_callback:info=>{
     const label=String(info.status||"");
     const percent=Number(info.progress);
     const line=label==="progress"&&Number.isFinite(percent)?
       "正在下载公开模型："+Math.round(percent)+"%":
       label==="ready"?"模型已可用":label==="initiate"?"开始获取模型文件…":"";
     if(line&&line!==lastProgress){lastProgress=line;postMessage({type:"status",message:line})}
   }
 });
 return extractor;
}
async function embedBatch(pipe,inputs){
 const tensor=await pipe(inputs,{pooling:"mean",normalize:true});
 const arr=tensor.tolist();
 if(!Array.isArray(arr)||arr.length!==inputs.length||!arr.every(x=>Array.isArray(x)&&x.length===384&&x.every(Number.isFinite)))
   throw Error("模型返回的向量格式异常；保留原规则匹配");
 return arr;
}
self.onmessage=async ev=>{
 const msg=ev.data;
 if(!msg||msg.action!=="run")return;
 try{
   const query=msg.query,items=msg.items,id=msg.id;
   if(typeof query!=="string"||query.trim().length<3||query.length>300||!Array.isArray(items)||items.length>32)
      throw Error("输入或候选数量超出安全限制");
   if(!items.every(x=>x&&typeof x.passage==="string"&&x.passage.length>=8&&x.passage.length<=600))
      throw Error("候选数据格式无效");
   const pipe=await initialize();
   postMessage({type:"status",message:"模型已加载；正在本机计算多语言语义向量…",id});
   const input=["query: "+query.trim(),...items.map(x=>"passage: "+x.passage)];
   const vectors=[];
   for(let start=0;start<input.length;start+=6){
     vectors.push(...await embedBatch(pipe,input.slice(start,start+6)));
     postMessage({type:"status",message:"已在本机编码 "+Math.min(start+6,input.length)+" / "+input.length+" 条文本",id});
   }
   postMessage({type:"done",id,vectors,model:"Xenova/multilingual-e5-small",sdk:"3.8.1"});
 }catch(e){
   postMessage({type:"error",id:msg.id,message:String(e?.message||e).slice(0,240)});
 }
};