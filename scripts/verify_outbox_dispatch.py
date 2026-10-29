#!/usr/bin/env python3
"""Independent process-level Pilot 08 recovery, contention and consumer-inbox tests."""
import argparse
import json
import multiprocessing
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P07=[sys.executable,"-m","scripts.real_crash_consistency"]
P08=[sys.executable,"-m","scripts.real_outbox_dispatch"]


def worker(sender,recipient,ready,go,queue,index):
    from scripts.real_outbox_dispatch import dispatch, setup
    try:
        setup(Path(sender),Path(recipient))
        ready.put(index)
        if not go.wait(timeout=15):raise TimeoutError("start barrier")
        result=dispatch(Path(sender),Path(recipient),"worker-"+str(index),8.0)
        queue.put({"index":index,"result":result})
    except BaseException as e:
        queue.put({"index":index,"error":type(e).__name__+": "+str(e)})


def lock_holder(sender,marker,hold_seconds):
    from scripts.real_outbox_dispatch import connect
    with connect(Path(sender)) as db:
        db.execute("BEGIN IMMEDIATE")
        Path(marker).write_text("locked",encoding="utf-8")
        time.sleep(hold_seconds)
        db.commit()


def execute(root):
    root=Path(root)
    root.mkdir(parents=True,exist_ok=True)
    stages=root/"stages";stages.mkdir()
    checks=[]
    serial=0

    def require(name,ok,details=None):
        if not ok:
            raise AssertionError(name+" | evidence="+json.dumps(details,sort_keys=True))
        checks.append(name)

    def paths(case):
        return root/(case+".sqlite"),root/(case+"-recipient.sqlite")

    def cmd(case,tool,stage,thread=None,key="shared-key",owner="worker-main",
            fault=None,expect_crash=False,**opts):
        nonlocal serial
        sender,recipient=paths(case)
        if tool=="p07":
            args=P07+["--db",str(sender),"--stage",stage,
                      "--thread",thread or "alpha-"+case,"--key",key]
        else:
            args=P08+["--sender",str(sender),"--recipient",str(recipient),
                      "--stage",stage,"--owner",owner]
        if fault:args+=["--fault",fault]
        for k,v in opts.items():
            args+=["--"+k.replace("_","-"),str(v)]
        started=time.monotonic()
        cp=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=35)
        elapsed=round((time.monotonic()-started)*1000)
        serial+=1
        record={"case":case,"tool":tool,"stage":stage,"returncode":cp.returncode,
                "pid_is_independent":True,"elapsed_ms":elapsed,
                "stdout":cp.stdout[-3500:],"stderr":cp.stderr[-1500:],
                "fault":fault}
        (stages/f"{serial:03d}-{case}-{tool}-{stage}.json").write_text(
            json.dumps(record,indent=2)+"\n",encoding="utf-8")
        if expect_crash:
            require(case+" real abrupt "+fault,cp.returncode==87 and not cp.stdout.strip(),
                    record)
            marks=sender.with_suffix(".p08faults.jsonl")
            events=[json.loads(s) for s in marks.read_text("utf-8").splitlines()]
            require(case+" fsynced exit marker",
                    events[-1]["fault"]==fault and events[-1]["pid"]>0)
            return None
        if cp.returncode!=0:
            raise RuntimeError("subprocess failure: "+json.dumps(record))
        return json.loads(cp.stdout)

    def produce(case,thread=None,key="shared-key",principal="alpha_owner"):
        t=thread or "alpha-"+case
        a=cmd(case,"p07","start",thread=t,key=key)
        g=cmd(case,"p07","grant",thread=t,key=key,principal=principal)
        b=cmd(case,"p07","resume",thread=t,key=key)
        require(case+" actual LangGraph+SQLite producer",
                a["interrupted"] and "review" in a["next"] and g["granted"]
                and b["outcome"]=="ALLOW: synthetic_draft_committed",
                {"started":a,"grant":g,"resumed":b})

    def state(case):
        return cmd(case,"p08","reconcile")

    case="normal"
    produce(case)
    delivered=cmd(case,"p08","dispatch")
    done=state(case)
    require("P08 normal ACK and real separate SQLite recipient",
            delivered["status"]=="ACKED" and delivered["recipient_inserted"]==1
            and done["source_acked"]==done["inbox_unique"]==1
            and done["pending_ack"]==0 and done["consistent"],done)
    no_more=cmd(case,"p08","dispatch")
    require("No repeat when outbox acknowledged",no_more["status"]=="NO_PENDING")

    for fault in ("before_receiver_commit","after_receiver_commit"):
        case="crash-"+fault.replace("_","-")
        produce(case)
        cmd(case,"p08","dispatch",fault=fault,expect_crash=True,
            lease_seconds=0.7)
        after=state(case)
        received=int(fault=="after_receiver_commit")
        require(case+" receiver rollback or persistence before ACK",
                after["source_acked"]==0 and after["inbox_unique"]==received
                and after["pending_ack"]==received
                and after["consistent"],after)
        time.sleep(0.85)
        resumed=cmd(case,"p08","dispatch",owner="worker-after-restart",
                    lease_seconds=4.0)
        recovered=state(case)
        require(case+" recovered ACK with unique receiver effect",
                resumed["status"]=="ACKED" and
                resumed["recipient_inserted"]==1-received
                and resumed["recipient_duplicate"]==bool(received)
                and resumed["attempt"]==2
                and recovered["source_acked"]==recovered["inbox_unique"]==1
                and recovered["attempts_total"]==2
                and recovered["pending_ack"]==0 and recovered["consistent"],
                {"resumed":resumed,"state":recovered})

    case="stale-lease"
    produce(case)
    first=cmd(case,"p08","claim",owner="worker-old",lease_seconds=0.6)
    require("Initial claim issued",first["status"]=="CLAIMED")
    time.sleep(0.8)
    second=cmd(case,"p08","claim",owner="worker-new",lease_seconds=4.0)
    stale=cmd(case,"p08","ack",owner="worker-old",tenant=first["tenant"],
              key=first["key"],token=first["token"])
    valid=cmd(case,"p08","deliver",owner="worker-new",tenant=second["tenant"],
              key=second["key"],token=second["token"])
    require("Expired owner fenced; new owner commits once",
            second["attempts"]==2
            and stale["status"]=="BLOCK: stale_or_missing_claim"
            and valid["status"]=="ACKED"
            and state(case)["inbox_unique"]==1)

    case="tenant"
    produce(case,thread="alpha-twin",key="cross-tenant-key",principal="alpha_owner")
    produce(case,thread="beta-twin",key="cross-tenant-key",principal="beta_owner")
    a=cmd(case,"p08","dispatch",owner="alpha-worker",tenant="alpha")
    b=cmd(case,"p08","dispatch",owner="beta-worker",tenant="beta")
    done=state(case)
    require("Same idempotency key cannot suppress independent tenants",
            a["status"]==b["status"]=="ACKED" and done["source_acked"]==2
            and done["inbox_unique"]==2 and done["consistent"],done)

    case="storm"
    produce(case)
    sender,receiver=paths(case)
    ctx=multiprocessing.get_context("spawn")
    ready,queue=ctx.Queue(),ctx.Queue()
    go=ctx.Event()
    ps=[ctx.Process(target=worker,args=(str(sender),str(receiver),ready,go,queue,i))
        for i in range(8)]
    for p in ps:p.start()
    try:
        for _ in ps:ready.get(timeout=20)
        go.set()
        results=[queue.get(timeout=30) for _ in ps]
    finally:
        go.set()
        for p in ps:p.join(timeout=10)
        for p in ps:
            if p.is_alive():p.terminate();p.join(timeout=5)
    require("All eight worker processes exited cleanly",
            all(p.exitcode==0 for p in ps) and
            all("error" not in d for d in results),results)
    statuses=[x["result"]["status"] for x in results]
    snap=state(case)
    require("Eight-process retry storm claims and delivers one local item",
            statuses.count("ACKED")==1 and statuses.count("NO_PENDING")==7
            and snap["attempts_total"]==1 and snap["inbox_unique"]==1
            and snap["source_acked"]==1 and snap["consistent"],results)

    case="lock-contention"
    produce(case)
    sender,receiver=paths(case)
    marker=root/"lock-ready.txt"
    locker=ctx.Process(target=lock_holder,args=(str(sender),str(marker),1.2))
    locker.start()
    deadline=time.monotonic()+5
    while not marker.exists() and time.monotonic()<deadline:
        time.sleep(0.015)
    require("Real independent SQLite BEGIN IMMEDIATE lock acquired",marker.exists())
    started=time.monotonic()
    result=cmd(case,"p08","dispatch",owner="waiter",lease_seconds=4.0)
    waited=time.monotonic()-started
    locker.join(timeout=7)
    require("Bounded busy_timeout survives real writer lock without duplicate",
            locker.exitcode==0 and waited>=0.2 and result["status"]=="ACKED"
            and state(case)["inbox_unique"]==1,
            {"waited_seconds":round(waited,3),"result":result})

    case="tampered-payload"
    produce(case)
    sender,_=paths(case)
    with sqlite3.connect(sender) as db:
        db.execute("UPDATE p07_outbox SET payload=?",
                   (json.dumps({"kind":"send_order"}),))
    blocked=cmd(case,"p08","dispatch")
    require("Untrusted outbox payload cannot become an executable action",
            blocked["status"]=="BLOCK: invalid_payload"
            and state(case)["inbox_unique"]==0)

    case="lost-inbox"
    produce(case)
    cmd(case,"p08","dispatch")
    sender,recipient=paths(case)
    with sqlite3.connect(recipient) as db:
        db.execute("DELETE FROM p08_inbox")
    detected=state(case)
    require("Lost consumer receipt detected after producer ACK",
            detected["acknowledged_missing"]==1 and
            detected["consistent"] is False,detected)

    output={"schema_version":1,
            "validation":{"all_passed":True,"checks":checks,
                          "cases_passed":len(checks),"processes_run":serial,
                          "storm_worker_processes":8},
            "actual_producer":"LangGraph 1.2.18 / SqliteSaver 3.1.2",
            "dispatcher":"Python sqlite3; separate local SQLite inbox",
            "crash_mode":"os._exit(87) with fsynced witness",
            "no_remote_receiver":True,"real_identity_verified":False,
            "no_production_integration":True,"external_exactly_once_proved":False,
            "no_real_orders":True,"real_model_calls":0,
            "limits":["two local SQLite databases only",
                      "acknowledgement is not atomic across separate SQLite databases",
                      "receiver dedup uses a synthetic inbox unique key",
                      "no network loss or actual external provider",
                      "leases use one host wall clock; no distributed clock skew tests",
                      "no hard power loss or checkpoint-write corruption"]}
    (root/"pilot08-result.json").write_text(
        json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS PILOT 08",len(checks),"checks",serial,
          "subprocess invocations + 8 separate contention workers")
    return output


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path)
    a=p.parse_args()
    if a.output_dir:execute(a.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="atlas-p08-") as d:execute(d)
