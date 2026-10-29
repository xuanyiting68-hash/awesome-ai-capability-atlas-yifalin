#!/usr/bin/env python3
"""Independent actual os._exit crash/recovery verification for Pilot Lab 07."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CLI=[sys.executable,"-m","scripts.real_crash_consistency"]


def execute(root):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    logs=root/"stages"
    logs.mkdir(exist_ok=True)
    checks=[]
    serial=0

    def require(name,predicate,details=None):
        if not predicate:
            raise AssertionError(name+" | evidence="+json.dumps(details,sort_keys=True))
        checks.append(name)

    def run(case,stage,thread=None,key="fixture-01",fault=None,expect_crash=False,
            **options):
        nonlocal serial
        db=root/(case+".sqlite")
        command=CLI+["--db",str(db),"--stage",stage,"--thread",
                     thread or ("alpha-"+case),"--key",key]
        if fault: command+=["--fault",fault]
        for k,v in options.items():command+=["--"+k.replace("_","-"),str(v)]
        cp=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=45)
        serial+=1
        record={"case":case,"stage":stage,"returncode":cp.returncode,
                "stdout":cp.stdout[-4000:],"stderr":cp.stderr[-2000:],
                "intentional_fault":fault,"expected_abrupt_exit":expect_crash}
        (logs/f"{serial:03d}-{case}-{stage}.json").write_text(
            json.dumps(record,indent=2)+"\n",encoding="utf-8")
        if expect_crash:
            require(case+" "+fault+" actual abrupt exit",
                    cp.returncode==86 and not cp.stdout.strip())
            markers=db.with_suffix(".faults.jsonl")
            events=[json.loads(x) for x in markers.read_text("utf-8").splitlines()]
            require(case+" fsynced fault evidence",events[-1]["fault"]==fault
                    and events[-1]["pid"]>0)
            return None
        if cp.returncode!=0:
            raise RuntimeError(str(command)+" failed: "+cp.stderr[-4000:])
        return json.loads(cp.stdout)

    for fault in ("before_transaction","before_commit","after_commit"):
        case="hard-"+fault.replace("_","-")
        initial=run(case,"start")
        require(case+" real LangGraph interrupt",
                initial["interrupted"] and "review" in initial["next"])
        grant=run(case,"grant")
        require(case+" simulated server approval",grant["granted"] is True
                and grant["identity_is_real"] is False)
        run(case,"resume",fault=fault,expect_crash=True)
        snapshot=run(case,"inspect")
        committed=int(fault=="after_commit")
        require(case+" SQLite expected crash boundary",
                snapshot["counts"]["effects"]==committed
                and snapshot["counts"]["outbox"]==committed
                and snapshot["counts"]["audit"]==committed
                and snapshot["consumed_approvals"]==committed
                and snapshot["reconciliation_ok"] is True)
        restored=run(case,"recover")
        require(case+" real checkpoint replay produces exact local effect",
                restored["outcome"]==
                ("ALREADY: synthetic_draft_committed" if committed else
                 "ALLOW: synthetic_draft_committed")
                and restored["next"]==[]
                and restored["counts"]["effects"]==1
                and restored["counts"]["outbox"]==1
                and restored["counts"]["audit"]==1
                and restored["consumed_approvals"]==1
                and restored["reconciliation_ok"] is True,
                {"fault":fault,"postcrash":snapshot,"recovered":restored})

    case="no-ticket"
    run(case,"start")
    denied=run(case,"resume")
    require("Mock owner string cannot bypass absent server ticket",
            denied["outcome"]=="BLOCK: missing_server_approval"
            and denied["counts"]["effects"]==0)

    for case,options in (("wrong-tenant",{"principal":"beta_owner"}),
                         ("viewer",{"principal":"alpha_viewer"})):
        run(case,"start")
        not_granted=run(case,"grant",**options)
        denied=run(case,"resume")
        require(case+" synthetic role and tenant protection",
                not not_granted["granted"]
                and denied["outcome"]=="BLOCK: missing_server_approval"
                and denied["counts"]["outbox"]==0)

    for case,mutation in (("expired",{"ttl":-1}),("revoked",{})):
        run(case,"start")
        run(case,"grant",**mutation)
        if case=="revoked":run(case,"revoke")
        denied=run(case,"resume")
        require(case+" expiry or revocation denied",
                denied["outcome"]=="BLOCK: revoked_expired_or_consumed"
                and denied["counts"]["effects"]==0)

    case="duplicate"
    run(case,"start",thread="alpha-first")
    run(case,"grant",thread="alpha-first")
    first=run(case,"resume",thread="alpha-first")
    run(case,"start",thread="alpha-second")
    run(case,"grant",thread="alpha-second")
    again=run(case,"resume",thread="alpha-second")
    require("Cross-thread key collision does not confer approval or second effect",
            first["counts"]["effects"]==1
            and again["outcome"]=="BLOCK: cross_thread_idempotency_collision"
            and again["counts"]["effects"]==1
            and again["counts"]["outbox"]==1
            and again["consumed_approvals"]==1
            and again["reconciliation_ok"] is True)

    case="tenant-isolation"
    for thread,principal in (("alpha-first","alpha_owner"),
                              ("beta-first","beta_owner")):
        run(case,"start",thread=thread)
        run(case,"grant",thread=thread,principal=principal)
        last=run(case,"resume",thread=thread)
    require("Same idempotency string isolated between alpha and beta tenants",
            last["counts"]["effects"]==2 and last["counts"]["outbox"]==2
            and last["counts"]["audit"]==2 and last["reconciliation_ok"])

    case="audit-loss"
    run(case,"start")
    run(case,"grant")
    good=run(case,"resume")
    corrupt=run(case,"tamper_audit")
    require("Synthetic missing audit row is detected, never reported consistent",
            good["reconciliation_ok"] is True
            and corrupt["counts"]["effects"]==1
            and corrupt["counts"]["outbox"]==1
            and corrupt["counts"]["audit"]==0
            and corrupt["reconciliation_ok"] is False)

    result={"schema_version":1,"validation":{"all_passed":True,
            "checks":checks,"cases_passed":len(checks),"processes_run":serial},
            "scope":"actual LangGraph 1.2.18 + SQLite saver 3.1.2; synthetic local effect",
            "fault_injection":"actual os._exit(86), fsynced marker",
            "crash_boundaries":["before_transaction","before_commit","after_commit"],
            "real_identity_verified":False,"external_delivery_tested":False,
            "end_to_end_exactly_once_proved":False,"production_integrated":False,
            "real_orders":0,"real_model_calls":0,
            "limits":["no checkpoint-write crash hook","no OS power loss",
                      "mock test principal is not production authentication",
                      "transactional exactly-once is local SQLite only",
                      "outbox has no external sender or broker delivery guarantee"]}
    (root/"pilot07-result.json").write_text(
        json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("PASS PILOT 07",len(checks),"strict checks",serial,"subprocesses")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",type=Path)
    args=parser.parse_args()
    if args.output_dir:
        execute(args.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="atlas-p07-") as t:execute(t)
