#!/usr/bin/env python3
"""Independent process-boundary regression harness for the actual LangGraph SQLite pilot.

Uses subprocess.run for every stage (distinct Python processes) and validates
raw JSON snapshots. No external data, LLM, live broker or network calls.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/real_durable_recovery.py"


def invoke(db,output_dir,stage,thread="a",**options):
    name=f"{len(list(output_dir.glob('*.json'))):02d}-{stage}-{thread}"
    result_file=output_dir/(name+".json")
    command=[sys.executable,str(SCRIPT),"--db",str(db),"--stage",stage,
             "--thread",thread,"--output",str(result_file)]
    for key,value in options.items():
        command += ["--"+key.replace("_","-")]
        if value is not True:command.append(str(value))
    completed=subprocess.run(command,check=False,capture_output=True,text=True,timeout=50,cwd=ROOT)
    if completed.returncode != 0:
        raise RuntimeError(f"{name} returned {completed.returncode}: {completed.stderr[-5000:]}")
    if not result_file.exists():
        raise AssertionError(f"No actual stage artifact for {name}: {completed.stdout}")
    content=json.loads(result_file.read_text("utf-8"))
    if not content.get("runner_pid") or content["runner_pid"]==__import__("os").getpid():
        raise AssertionError("Stage did not execute in an independent process")
    return content


def expect(test_name,expr):
    if not expr:raise AssertionError(test_name)
    return test_name


def execute(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    db=root/"checkpoints.sqlite"
    stages=root/"stages";stages.mkdir()
    checks=[]
    a=invoke(db,stages,"start","denied")
    checks.append(expect("D01 interruption persisted",a["pending_review"] is True and a["ledger_commits"]==0))
    a2=invoke(db,stages,"inspect","denied")
    checks.append(expect("D02 new process sees persisted checkpoint",
        a2["checkpoint_exists"] and a2["pending_review"] and a["runner_pid"]!=a2["runner_pid"]))
    a3=invoke(db,stages,"resume","denied",approval="deny")
    checks.append(expect("D03 denied approval no commit",
        a3["outcome"]=="BLOCK: mock_owner_denied" and a3["ledger_commits"]==0 and
        not a3["pending_review"] and a2["runner_pid"]!=a3["runner_pid"]))
    b=invoke(db,stages,"start","accepted",key="frozen-01")
    b2=invoke(db,stages,"resume","accepted",approval="approve")
    checks.append(expect("D04 new process approved synthetic draft",
        b["pending_review"] and b2["outcome"]=="ALLOW: synthetic_draft_committed"
        and b2["ledger_commits"]==1 and b["runner_pid"]!=b2["runner_pid"]))
    c=invoke(db,stages,"start","duplicate",key="frozen-01")
    c2=invoke(db,stages,"resume","duplicate",approval="approve")
    checks.append(expect("D05 new thread replay stays at-most-once",
        c["pending_review"] and c2["outcome"]=="BLOCK: duplicate_idempotency_key"
        and c2["ledger_commits"]==1))
    d=invoke(db,stages,"start","forged")
    d2=invoke(db,stages,"resume","forged",approval="forge")
    checks.append(expect("D06 untrusted webpage spoof cannot approve",
        d["pending_review"] and d2["outcome"]=="BLOCK: spoofed_approval_source"
        and d2["ledger_commits"]==1))
    e=invoke(db,stages,"start","missing",bad_citations=True)
    checks.append(expect("D07 incorrect citation blocks before approval",
        e["outcome"]=="BLOCK: bad_citations" and not e["pending_review"]))
    f=invoke(db,stages,"start","trade",action="send_order")
    checks.append(expect("D08 trading tool path unreachable",
        f["outcome"]=="BLOCK: forbidden_action" and not f["pending_review"]))
    g=invoke(db,stages,"start","pending")
    g2=invoke(db,stages,"inspect","pending")
    checks.append(expect("D09 pending review remains paused across clean process exit",
        g2["pending_review"] and g["runner_pid"]!=g2["runner_pid"]))
    h=invoke(db,stages,"start","second-approval",key="frozen-02")
    h2=invoke(db,stages,"resume","second-approval",approval="approve")
    checks.append(expect("D10 unrelated approved draft commits one new unique key",
        h["pending_review"] and h2["outcome"]=="ALLOW: synthetic_draft_committed"
        and h2["ledger_commits"]==2))
    concurrency=invoke(db,stages,"concurrency",thread="concurrent")
    checks.append(expect("D11 six independent SQLite ledger workers commit key once",
        concurrency["workers"]==6 and concurrency["applied"]==1
        and concurrency["duplicates_blocked"]==5
        and concurrency["graph_scheduler_concurrency_tested"] is False))
    summary=invoke(db,stages,"summary")
    checks.append(expect("D12 durable audit reconciles unique keys and attempts",
        summary["commit_keys"]==["frozen-01","frozen-02","shared-concurrency-key"]
        and len(summary["journal"])==9
        and sum(x["decision"]=="ALLOW: synthetic_draft_committed" for x in summary["journal"])==3
        and len({x["thread"] for x in summary["journal"]})==9))
    checks.append(expect("D13 no production, real identity or durable graph scheduler claim",
        summary["real_identity_verified"] is False and summary["production_integrated"] is False
        and summary["real_broker_orders"]==0 and summary["real_model_calls"]==0
        and summary["concurrency_scope"]=="ledger-only-not-graph"))
    summary["validation"]={
        "schema_version":1,"cases_total":len(checks),"cases_passed":len(checks),
        "all_passed":True,"checks":checks,
        "actual_distinct_processes":len({json.loads(f.read_text("utf-8"))["runner_pid"] for f in stages.glob("*.json")}),
        "runtime_limited_to_synthetic_fixtures":True,
        "process_restart_mode":"clean-separate-invocations-not-sudden-kill",
        "mid_commit_crash_injected":False,
        "authenticated_approvals_tested":False,
        "graph_concurrency_tested":False,
    }
    if summary["validation"]["actual_distinct_processes"]!=len(list(stages.glob("*.json"))):
        raise AssertionError("Expected one new Python process for every stage")
    (root/"durability-result.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PASS REAL SQLITE LANGGRAPH: 13/13 subprocess restart/approval/ledger checks, "
          "6 competing ledger workers, zero trading or real-user actions")
    return summary


def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path)
    args=p.parse_args()
    if args.output_dir:
        execute(args.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="atlas-sqlite-recovery-") as temp:
            execute(temp)


if __name__=="__main__":
    main()
