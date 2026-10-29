#!/usr/bin/env node
/* Validate that Promptfoo evaluated outputs from ACTUAL Docling -> LangGraph.
 * Does NOT pretend a mock Echo result constitutes real model safety.
 */
"use strict";
const fs=require("node:fs"),assert=require("node:assert/strict");
const base="test-results/integrated/";
const read=n=>JSON.parse(fs.readFileSync(base+n,"utf8"));
const workflow=read("workflow.json");
assert.equal(workflow.status,"real-cross-tool-integration-sandbox-executed");
assert.deepEqual(workflow.components,{docling:"2.144.0",langgraph:"1.2.18",promptfoo:"0.125.1"});
assert.equal(workflow.cases_total,8);
assert.equal(workflow.cases_passed,8);
assert.equal(workflow.actual_upstream_docling_calls,8);
assert.equal(workflow.actual_upstream_langgraph_runs,8);
assert.equal(workflow.broker_orders,0);
assert.equal(workflow.llm_calls,0);
assert.equal(workflow.production_changes,0);
assert.equal(workflow.user_data_processed,false);
assert.equal(workflow.security_certified,false);
assert.equal(workflow.ocr_tested,false);
assert.equal(workflow.approval,"mock-dict-not-authenticated");
assert.equal(workflow.audit_events.length,8);
const EXPECTED=[
["I01","ALLOW: synthetic_draft_created citations=p1,p2",true],
["I02","BLOCK: owner_denied",true],
["I03","BLOCK: invalid_approval_source",true],
["I04","BLOCK: missing_evidence",false],
["I05","BLOCK: duplicate_idempotency_key",true],
["I06","BLOCK: forbidden_action",false],
["I07","BLOCK: owner_denied",true],
["I08","BLOCK: missing_idempotency_key",true],
];
assert.deepEqual(workflow.outputs.map(x=>[x.id,x.message,x.interrupted]),EXPECTED);
assert.ok(workflow.outputs.every(x=>JSON.stringify(x.pages)==='{"NOFI":1,"45 minutes":2}'));
const configs={positive:read("echo-positive.yaml"),negative:read("echo-negative.yaml")};
for(const c of Object.values(configs)){
  assert.deepEqual(c.providers,["echo"]);
  assert.deepEqual(c.prompts,["{{mock_response}}"]);
}
assert.equal(configs.positive.tests.length,8);
assert.equal(configs.negative.tests.length,1);
for(const [i,x] of workflow.outputs.entries()){
  assert.equal(configs.positive.tests[i].vars.mock_response,x.message);
  assert.deepEqual(configs.positive.tests[i].assert,[{type:"contains",value:EXPECTED[i][1]}]);
}
assert.equal(configs.negative.tests[0].vars.mock_response,"BLOCK: forbidden_action");
assert.equal(configs.negative.tests[0].assert[0].value,"ALLOW: real_order_sent");
function actual(n,count,wantPassed){
  const data=read(n);
  const rows=data.results?.results ?? data.results;
  assert.equal(rows.length,count);
  const passed=rows.filter(x=>x.success===true).length;
  const failed=rows.filter(x=>x.success===false).length;
  assert.equal(passed,wantPassed);
  assert.equal(failed,count-wantPassed);
  assert.ok(rows.every(x=>typeof x.response?.output==="string"));
  return rows;
}
const pos=actual("echo-result-positive.json",8,8);
const neg=actual("echo-result-negative.json",1,0);
assert.deepEqual(pos.map(x=>x.response.output).sort(),workflow.outputs.map(x=>x.message).sort());
assert.equal(neg[0].response.output,"BLOCK: forbidden_action");
assert.equal(pos.find(x=>x.response.output.startsWith("ALLOW:"))?.response.output,
  EXPECTED[0][1]);
assert.ok(pos.every(x=>!x.response.output.includes("real_order_sent")));
assert.ok(workflow.audit_events.every(x=>x.synthetic_approval_only===true));
const summary={
  schema_version:1,
  status:"real-upstream-cross-tool-integration-validated",
  pipeline:"original synthetic PDF -> real Docling -> real LangGraph interrupt/checkpoint -> real Promptfoo Echo assertion",
  real_sdk_packages:workflow.components,
  actual_pdf_to_graph_scenarios:8,
  actual_promptfoo_positive:8,
  actual_promptfoo_negative_detected:1,
  llm_calls:0,
  broker_orders:0,
  user_data_processed:false,
  authenticated_approvals_tested:false,
  durable_resume_tested:false,
  ocr_or_semantic_tables_tested:false,
  security_certified:false,
};
fs.writeFileSync(base+"validated-summary.json",JSON.stringify(summary,null,2)+"\n");
console.log("PASS REAL CROSS-TOOL E2E: 8/8 PDF->graph->Echo results; 1/1 deliberate negative detected; zero model/broker calls");
