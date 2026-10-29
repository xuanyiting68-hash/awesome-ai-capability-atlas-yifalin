#!/usr/bin/env node
/* Validate actual Promptfoo CLI exports; fail closed on missing/mismatched tests.
 * No promptfoo libraries imported; only built-in Node APIs.
 * Echo-provider assertions are NOT evidence of real model safety.
 */
"use strict";
const fs = require("node:fs");
const assert = require("node:assert/strict");

function readResults(file) {
  const data=JSON.parse(fs.readFileSync(file,"utf8"));
  const value=data.results?.results ?? data.results ?? data.eval?.results;
  if(!Array.isArray(value)) throw Error("Promptfoo export has no raw evaluation results list");
  return value;
}
function validate(file,expectedCount,expectedPassed) {
  const rows=readResults(file);
  assert.equal(rows.length,expectedCount,"Promptfoo cases in "+file);
  const passing=rows.filter(x=>x.success===true);
  const failing=rows.filter(x=>x.success===false);
  assert.equal(passing.length,expectedPassed,"Real Promptfoo assertion-pass count in "+file);
  assert.equal(failing.length,expectedCount-expectedPassed,"Real Promptfoo detection count in "+file);
  assert.ok(rows.every(x=>typeof x.response?.output==="string" || typeof x.output==="string"),"Actual provider responses must be present");
  return {total:rows.length,passed:passing.length,failed:failing.length};
}
const positive=validate("test-results/real-promptfoo-positive.json",8,8);
const negative=validate("test-results/real-promptfoo-negative.json",1,0);
const configs=[
  fs.readFileSync("examples/promptfoo_echo/promptfooconfig.yaml","utf8"),
  fs.readFileSync("examples/promptfoo_echo/promptfoo-negative.yaml","utf8")
];
for(const conf of configs) {
  assert.match(conf,/providers:\s*\n\s+- echo\b/);
  assert.doesNotMatch(conf,/\b(?:openai|anthropic|http|https|webhook|mcp):/i);
}
const output={
  schema_version:1,
  project:"promptfoo/promptfoo",
  package:"promptfoo",
  version:"0.125.1",
  status:"real-upstream-echo-evaluation-executed",
  provider:"echo",
  positive,negative,
  total_assertion_cases:positive.total+negative.total,
  successful_positive_cases:positive.passed,
  detected_negative_controls:negative.failed,
  real_model_calls:0,
  real_external_provider_calls:0,
  production_tools_called:0,
  user_data_used:false,
  limitations:[
    "Echo provider replays synthetic expected outputs; it cannot prove a model or Agent will refuse unsafe requests.",
    "Negative control proves the assertion engine detects a predefined mismatch, not prompt-injection defense efficacy.",
    "This is not a vulnerability assessment, adversarial attack campaign or security audit.",
    "No actual trading, customer records, API credentials or production integrations were used.",
    "Upstream package installed with npm; transitive dependencies and package licensing are not fully audited."
  ]
};
fs.writeFileSync("test-results/real-promptfoo-summary.json",JSON.stringify(output,null,2)+"\n");
console.log("PASS REAL PROMPTFOO "+output.version+": "+positive.passed+"/"+positive.total+" synthetic passes; "+negative.failed+"/"+negative.total+" deliberate negative controls detected");
