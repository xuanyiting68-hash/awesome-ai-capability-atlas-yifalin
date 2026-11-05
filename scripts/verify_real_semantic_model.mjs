#!/usr/bin/env node
/* Real upstream neural model evaluation in a read-only GitHub Actions runner.
   Not user data, not a hosted inference API, no credentials, no external action. */
import {pipeline} from "@huggingface/transformers";
import {readFileSync,mkdirSync,writeFileSync} from "node:fs";
import {dirname} from "node:path";
import assert from "node:assert/strict";
const MODEL="Xenova/multilingual-e5-small";
const LIBRARY="@huggingface/transformers";
const VERSION="3.8.1";
const installed=JSON.parse(readFileSync("node_modules/@huggingface/transformers/package.json","utf8"));
assert.equal(installed.version,VERSION,"Model SDK drift");
const cases=[
 "query: 检索专业课程讲义并生成可溯源的互动练习",
 "passage: 检索专业课程讲义并生成可溯源的互动练习",
 "passage: 财务市场衍生品、股票价格回测与量化交易",
 "passage: retrieve source-backed lesson notes and exercises for teachers"
];
const extractor=await pipeline("feature-extraction",MODEL,{dtype:"q8"});
const tensor=await extractor(cases,{pooling:"mean",normalize:true});
const rows=tensor.tolist();
assert.equal(rows.length,cases.length);
assert.ok(rows.every(v=>Array.isArray(v)&&v.length===384&&v.every(Number.isFinite)));
function dot(a,b){let sum=0;for(let i=0;i<a.length;i++)sum+=a[i]*b[i];return sum}
const scoreSame=dot(rows[0],rows[1]),scoreUnrelated=dot(rows[0],rows[2]),scoreCrossLanguage=dot(rows[0],rows[3]);
assert.ok(scoreSame>0.90,"Actual neural embedding cannot retrieve exact source text");
assert.ok(scoreSame>scoreUnrelated,"Exact source must beat unrelated synthetic finance text");
assert.ok(scoreCrossLanguage>0&&Number.isFinite(scoreCrossLanguage),"Cross-language output invalid");
const result={schema_version:1,pass:true,mode:"real_upstream_neural_embedding_on_runner_CPU",
 model:MODEL,model_revision:"upstream_main_unpinned_NOT_audited",library:LIBRARY,library_version:VERSION,
 embedding_dimensions:384,actual_model_calls:1,cases:cases.length,
 exact_passage_cosine:scoreSame,unrelated_finance_cosine:scoreUnrelated,
 cross_language_cosine_observed:scoreCrossLanguage,
 return_bounds:"cosine_not_certainty_or_performance",
 github_actions_hosted_model_network_only:true,
 user_prompts_used:false,production_sdk_integrations:0,paid_model_calls:0,
 source_security_license_audit:"HOLD",real_orders:0};
const dest=process.argv[2]||"test-results/semantic-real-model.json";
mkdirSync(dirname(dest),{recursive:true});
writeFileSync(dest,JSON.stringify(result,null,2)+"\n");
console.log("PASS REAL E5 pretrained neural model: 4 text embeddings, 384 dimensions, source > unrelated, score is NOT probability");
