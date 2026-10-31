#!/usr/bin/env python3
"""Independent, deterministic stdlib-only three-scenario recipe demo verification."""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from examples.recipe_demos.run_demo import run_from_files  # noqa: E402
CLI=ROOT/"examples/recipe_demos/run_demo.py"


def verify_from_files(root=ROOT):
    root=Path(root)
    contract=json.loads((root/"data/recipe_demo_contract.json").read_text(encoding="utf-8"))
    if contract.get("schema_version")!=1 or contract.get("third_party_execution") is not False:
        raise ValueError("demo contract must be synthetic and first-party")
    if set(contract.get("cases",{}))!={"leads","education","finance"}:
        raise ValueError("incomplete demo acceptance contract")
    report=run_from_files(root)
    if report["all_scenarios"]!=["leads","education","finance"] or not report["all_passed"]:
        raise ValueError("missing demo execution")
    if (report["verified_3rd_party_integrations"] or report["network_requests"]
        or report["models_called"] or report["real_orders"]
        or report["personal_information"] is not False):
        raise ValueError("demo unexpectedly claims external integration or action")
    for scenario,expected in contract["cases"].items():
        actual=report["scenarios"][scenario]
        for key,want in expected.items():
            if actual.get(key)!=want:
                raise ValueError("demo evidence mismatch: "+scenario+"."+key+
                                 " actual="+str(actual.get(key))+" expected="+str(want))
        if actual.get("verified_third_party_integration") is not False:
            raise ValueError("recipe was falsely promoted to verified integration")
    finance=report["scenarios"]["finance"]
    if (finance["dataset_type"]!="fabricated_not_market" or
        finance["has_predictive_edge"]!="not_established" or
        finance["future_prices_used_in_predictor"] is not False or
        any(item["broker_order_sent"] or item["max_predictor_index"]>=item["decision_index"]
            for item in finance["evaluated_decisions"])):
        raise ValueError("finance synthetic analysis risk boundary violated")
    education=report["scenarios"]["education"]
    if education["llm_calls"] or education["student_data_seen"] is not False:
        raise ValueError("education model/identity boundary violated")
    if any((r["answer"] is None)!=(r["citation"] is None) for r in education["responses"]):
        raise ValueError("education source citation mismatch")
    leads=report["scenarios"]["leads"]
    if leads["outbound_messages"] or leads["user_contact_attempts"]:
        raise ValueError("contact unexpectedly performed")
    return report


def verify_independent_subprocesses(root=ROOT):
    root=Path(root)
    independent={}
    for name in ("all","leads","education","finance"):
        result=subprocess.run(
            [sys.executable,str(root/"examples/recipe_demos/run_demo.py"),"--scenario",name],
            cwd=root,capture_output=True,text=True,timeout=20,
            env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1","PYTHONNOUSERSITE":"1"})
        if result.returncode:
            raise RuntimeError("subprocess failed: "+name+": "+result.stderr[-1200:])
        parsed=json.loads(result.stdout)
        if parsed.get("all_passed") is not True or parsed.get("real_orders")!=0:
            raise ValueError("subprocess claims or action mismatch")
        independent[name]=parsed
    canonical=verify_from_files(root)
    if independent["all"]!=canonical:
        raise ValueError("CLI output drift from source file execution")
    for scenario in ("leads","education","finance"):
        if independent[scenario]["scenarios"]!={scenario:canonical["scenarios"][scenario]}:
            raise ValueError("independent CLI scenario drift: "+scenario)
    return {"checks":4,"processes":4,"scenarios":3,
            "all_cases_match":True,"source_report":canonical}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path)
    args=p.parse_args()
    result=verify_independent_subprocesses()
    public={"schema_version":1,"all_passed":True,
            "independent_cli_processes":result["processes"],
            "scenario_count":result["scenarios"],
            "expected_case_contract_passed":True,
            **result["source_report"]}
    if args.output_dir:
        args.output_dir.mkdir(parents=True,exist_ok=True)
        (args.output_dir/"recipe-demo-results.json").write_text(
            json.dumps(public,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
            encoding="utf-8")
    print("PASS recipe demos: 3 independent scenarios and composite, 4 CLI processes; no external integrations")
    return public


if __name__=="__main__":
    main()
