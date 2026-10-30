#!/usr/bin/env python3
"""Pilot 10 independent cross-process recovery coordinator verification."""
import argparse
import json
import multiprocessing
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
P07=[sys.executable,"-m","scripts.real_crash_consistency"]
P09=[sys.executable,"-m","scripts.real_checkpoint_faults"]
P10=[sys.executable,"-m","scripts.real_recovery_coordinator"]


def compete_worker(db,ready,go,output,index):
    try:
        from scripts import real_recovery_coordinator as c
        ready.put(index)
        if not go.wait(timeout=30):raise TimeoutError("barrier timeout")
        completed=[]
        for _ in range(8):
            work=c.claim(Path(db),"competitor-"+str(index),lease_seconds=8)
            if work["status"]=="NO_WORK":break
            if work["status"]!="CLAIMED":
                raise AssertionError("unrecognized claim "+str(work))
            result=c.apply(Path(db),work["thread"],work["owner"],work["token"])
            if result["status"]!="DONE":raise AssertionError(str(result))
            completed.append(work["thread"])
        output.put({"worker":index,"done":completed})
    except BaseException as e:
        output.put({"worker":index,"error":type(e).__name__+": "+str(e)})


def execute(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    stages=root/"stages";stages.mkdir(exist_ok=True)
    checks=[];count=0;case_timings={}

    def require(name,ok,evidence=None):
        if not ok:raise AssertionError(name+" | evidence="+json.dumps(evidence,sort_keys=True))
        checks.append(name)

    def cli(case,tool,stage,thread=None,key=None,fault=None,expected_exit=None,**options):
        nonlocal count
        db=root/(case+".sqlite")
        if tool=="p10":
            args=P10+["--db",str(db),"--stage",stage]
            if thread:args+=["--thread",thread]
        elif tool=="p09":
            args=P09+["--db",str(db),"--stage",stage,"--thread",thread]
        else:
            args=P07+["--db",str(db),"--stage",stage,"--thread",thread,
                      "--key",key or ("p09-"+thread)]
        if fault:args+=["--fault",fault]
        for k,v in options.items():
            args+=["--"+k.replace("_","-"),str(v)]
        t=time.monotonic()
        p=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,timeout=55)
        duration=round((time.monotonic()-t)*1000,2)
        count+=1
        evidence={"case":case,"tool":tool,"stage":stage,"thread":thread,
                  "exit_code":p.returncode,"duration_ms":duration,
                  "stdout":p.stdout[-2500:],"stderr":p.stderr[-1200:],"fault":fault}
        (stages/f"{count:03d}-{case}-{tool}-{stage}.json").write_text(
            json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
        if expected_exit is not None:
            require(case+" "+fault+" process abort",p.returncode==expected_exit
                    and not p.stdout.strip(),evidence)
            marker=Path(str(db)+".p10-faults.jsonl")
            events=[json.loads(x) for x in marker.read_text("utf-8").splitlines()]
            require(case+" "+fault+" fsynced marker",
                    events[-1]["site"]==fault and events[-1]["pid"]>0,events)
            return None
        if p.returncode:raise RuntimeError(json.dumps(evidence))
        return json.loads(p.stdout)

    # Seed a real checkpoint crash using the same logger as other stages.
    def seed(case,thread=None,site="checkpoint_before",ttl=60,principal=None):
        nonlocal count
        t=thread or "alpha-"+case
        started=cli(case,"p09","start",thread=t)
        require(case+" "+t+" starts at LangGraph interrupt",
                started["interrupted"] and "review" in started["next"],started)
        grant=cli(case,"p07","grant",thread=t,ttl=ttl,
                  principal=principal or ("beta_owner" if t.startswith("beta-") else "alpha_owner"))
        require(case+" "+t+" mocked ticket persists",grant["granted"],grant)
        db=root/(case+".sqlite")
        args=P09+["--db",str(db),"--stage","fault","--thread",t,"--site",site]
        started=time.monotonic()
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=45)
        count+=1
        log={"case":case,"stage":"fault","site":site,"thread":t,
             "duration_ms":round((time.monotonic()-started)*1000,2),
             "returncode":p.returncode,"stdout":p.stdout[-2000:],"stderr":p.stderr[-1200:]}
        (stages/f"{count:03d}-{case}-p09-fault.json").write_text(
            json.dumps(log,indent=2)+"\n",encoding="utf-8")
        require(case+" "+t+" actually crashed INSIDE checkpoint SQL",
                p.returncode==89 and not p.stdout.strip(),log)
        markers=Path(str(db)+".p09-faults.jsonl")
        require(case+" "+t+" fsynced trigger witness",
                any(json.loads(l)["site"]==site for l in markers.read_text("utf-8").splitlines()))
        return t

    case="orphan"
    thread=seed(case)
    unqueued=cli(case,"p10","inspect")
    require("Detect real approved but unqueued orphan outside LangGraph",
            thread in unqueued["orphaned_unqueued"] and
            unqueued["effect_count"]==0,unqueued)
    start=time.monotonic()
    scanned=cli(case,"p10","scan")
    require("Durable queue enrollment from real approved checkpoint",
            scanned["results"][0]["status"]=="QUEUED",scanned)
    task=cli(case,"p10","claim",owner="worker-one",lease_seconds=4)
    require("SQLite lease claim issued with fencing token",
            task["status"]=="CLAIMED" and task["attempts"]==1,task)
    done=cli(case,"p10","apply",thread=thread,owner="worker-one",token=task["token"])
    result=cli(case,"p10","inspect")
    case_timings["orphan_recovery_ms"]=round((time.monotonic()-start)*1000,2)
    require("Atomic queue completion and local ledger/outbox/audit agreement",
            done["status"]=="DONE" and result["phases"]["DONE"]==1
            and result["effect_count"]==result["outbox_count"]==result["audit_count"]==1
            and result["total_attempts"]==1
            and result["atomic_recovery_verified"],result)
    again=cli(case,"p10","scan")
    no_work=cli(case,"p10","claim")
    require("Repeated scans and claims cannot create duplicate work",
            again["results"][0]["status"]=="ALREADY: local_effect_present"
            and no_work["status"]=="NO_WORK" and
            cli(case,"p10","inspect")["effect_count"]==1)

    case="bad-token"
    thread=seed(case)
    cli(case,"p10","scan")
    task=cli(case,"p10","claim",owner="valid-worker",lease_seconds=4)
    fake=cli(case,"p10","apply",thread=thread,owner="valid-worker",token="forged-token")
    require("Forged fencing token denied before side effect",
            fake["status"]=="BLOCK: stale_or_missing_fenced_lease" and
            cli(case,"p10","inspect")["effect_count"]==0,fake)
    legit=cli(case,"p10","apply",thread=thread,owner="valid-worker",token=task["token"])
    require("Legitimate token still allows exactly one local outcome",
            legit["status"]=="DONE" and
            cli(case,"p10","inspect")["effect_count"]==1)

    case="stale-owner"
    thread=seed(case)
    cli(case,"p10","scan")
    first=cli(case,"p10","claim",owner="old-worker",lease_seconds=0.4)
    time.sleep(0.65)
    second=cli(case,"p10","claim",owner="new-worker",lease_seconds=3)
    refused=cli(case,"p10","apply",thread=thread,owner="old-worker",token=first["token"])
    accepted=cli(case,"p10","apply",thread=thread,owner="new-worker",token=second["token"])
    require("Expired lease is fenced against old process and new lease wins",
            first["status"]==second["status"]=="CLAIMED"
            and second["attempts"]==2
            and refused["status"]=="BLOCK: stale_or_missing_fenced_lease"
            and accepted["status"]=="DONE" and
            cli(case,"p10","inspect")["total_attempts"]==2)

    for crash in ("before_commit","after_commit"):
        case="coordinator-"+crash.replace("_","-")
        thread=seed(case)
        cli(case,"p10","scan")
        lease=cli(case,"p10","claim",owner="crashing-worker",lease_seconds=3.0)
        cli(case,"p10","apply",thread=thread,owner="crashing-worker",
            token=lease["token"],fault=crash,expected_exit=90)
        after=cli(case,"p10","inspect")
        persisted=int(crash=="after_commit")
        require(case+" SQLite effect and task status atomic at crash boundary",
                after["effect_count"]==persisted and after["phases"]["DONE"]==persisted
                and after["phases"]["LEASED"]==1-persisted
                and after["atomic_recovery_verified"] is False if not persisted else
                after["effect_count"]==1 and after["phases"]["DONE"]==1
                and after["atomic_recovery_verified"] is True,after)
        if not persisted:
            time.sleep(3.3)
            renewed=cli(case,"p10","claim",owner="reboot-worker",lease_seconds=3)
            settled=cli(case,"p10","apply",thread=thread,owner="reboot-worker",token=renewed["token"])
            require("Precommit crash rolled back all and replayed with fresh lease",
                    renewed["attempts"]==2 and settled["status"]=="DONE"
                    and cli(case,"p10","inspect")["atomic_recovery_verified"])
        else:
            stopped=cli(case,"p10","claim")
            require("Postcommit crash cannot reapply acknowledged atomic queue item",
                    stopped["status"]=="NO_WORK" and
                    cli(case,"p10","inspect")["effect_count"]==1)

    case="revoked"
    thread=seed(case)
    cli(case,"p10","scan")
    lease=cli(case,"p10","claim",owner="worker-revoked",lease_seconds=4)
    cli(case,"p07","revoke",thread=thread)
    denied=cli(case,"p10","apply",thread=thread,owner=lease["owner"],token=lease["token"])
    blocked=cli(case,"p10","inspect")
    require("Revoked approval after lease but before effect fails closed",
            denied["status"]=="BLOCK: ticket_not_active" and
            blocked["phases"]["BLOCKED"]==1 and blocked["effect_count"]==0
            and blocked["outbox_count"]==blocked["audit_count"]==0,blocked)

    case="expired"
    thread=seed(case,ttl=-1)
    rejected=cli(case,"p10","scan")
    require("Expired approval cannot enter coordinator queue",
            rejected["results"][0]["status"]=="BLOCK: ticket_revoked_expired_or_consumed"
            and cli(case,"p10","inspect")["tasks"]==0,rejected)

    case="pending-review"
    thread="alpha-pending-review"
    started=cli(case,"p09","start",thread=thread)
    cli(case,"p07","grant",thread=thread)
    pending=cli(case,"p10","scan")
    require("Unfinished owner-review interrupt is not approved queue work",
            started["interrupted"] and
            pending["results"][0]["status"]=="BLOCK: no_approved_terminal_graph_checkpoint"
            and cli(case,"p10","inspect")["tasks"]==0,pending)

    case="multi-worker"
    tenants=(("alpha-mw1","alpha_owner"),("alpha-mw2","alpha_owner"),
             ("beta-mw1","beta_owner"),("beta-mw2","beta_owner"))
    for t,principal in tenants:
        seed(case,thread=t,principal=principal)
    enrolled=cli(case,"p10","scan")
    require("Four isolated tenant-scoped graph orphans are queued",
            len(enrolled["results"])==4 and
            all(x["status"]=="QUEUED" for x in enrolled["results"]),enrolled)
    db=root/(case+".sqlite")
    ctx=multiprocessing.get_context("spawn")
    ready=ctx.Queue();output=ctx.Queue();go=ctx.Event()
    processes=[ctx.Process(target=compete_worker,args=(str(db),ready,go,output,i))
               for i in range(8)]
    started=time.monotonic()
    for p in processes:p.start()
    try:
        for _ in processes:ready.get(timeout=30)
        go.set()
        results=[output.get(timeout=40) for _ in processes]
    finally:
        go.set()
        for p in processes:p.join(timeout=20)
        for p in processes:
            if p.is_alive():p.terminate();p.join(timeout=5)
    case_timings["eight_worker_four_task_batch_ms"]=round((time.monotonic()-started)*1000,2)
    require("Eight real independent worker processes return cleanly",
            all(p.exitcode==0 for p in processes)
            and all("error" not in x for x in results),results)
    final=cli(case,"p10","inspect")
    observed=[name for x in results for name in x["done"]]
    require("Eight contenders settle four distinct tenant-scoped orphans once each",
            len(observed)==len(set(observed))==4 and
            set(observed)==set(t for t,_ in tenants)
            and final["phases"]["DONE"]==4
            and final["total_attempts"]==4
            and final["effect_count"]==final["outbox_count"]==final["audit_count"]==4
            and final["atomic_recovery_verified"],{"results":results,"final":final})

    case="audit-corruption"
    thread=seed(case)
    cli(case,"p10","scan")
    lease=cli(case,"p10","claim")
    cli(case,"p10","apply",thread=thread,owner=lease["owner"],token=lease["token"])
    with sqlite3.connect(root/(case+".sqlite")) as db:
        db.execute("DELETE FROM p07_audit")
    detected=cli(case,"p10","inspect")
    require("Independent reconciliation catches missing committed audit evidence",
            detected["all_effects_reconciled"] is False and
            detected["atomic_recovery_verified"] is False,detected)

    output={"schema_version":1,"all_passed":True,"checks":checks,
            "strict_checks":len(checks),"cli_processes":count,
            "contention_workers":8,"recovery_walltime_observations_ms":case_timings,
            "real_langgraph_checkpoint_required":True,
            "independent_durable_queue":True,
            "atomic_ledger_and_task_update":"single SQLite BEGIN IMMEDIATE transaction",
            "no_production_identity":True,"real_external_delivery":False,
            "real_orders":0,"real_model_calls":0,
            "limits":["mock service approvals only, no real RBAC",
                      "SQLite is single-host and shares producer ledger database",
                      "same host wall clock lease, no network/clock skew or distributed HA",
                      "elapsed time measurements are isolated CI observations, not service SLO",
                      "not a repair of original LangGraph checkpoint scheduler state",
                      "no HTTP, external side effects, real orders or customer data"]}
    (root/"pilot10-result.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8")
    print("PASS PILOT 10",len(checks),"checks",count,
          "independent CLI processes plus 8 concurrent workers")
    return output


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path)
    args=p.parse_args()
    if args.output_dir:execute(args.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="atlas-p10-") as d:execute(d)
