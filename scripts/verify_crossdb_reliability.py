#!/usr/bin/env python3
"""Independent CLI subprocess tests for Pilot 11 cross-DB crash and audit gaps."""
import argparse
import json
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P07=[sys.executable,"-m","scripts.real_crash_consistency"]
P09=[sys.executable,"-m","scripts.real_checkpoint_faults"]
P10=[sys.executable,"-m","scripts.real_recovery_coordinator"]
P11=[sys.executable,"-m","scripts.real_crossdb_reliability"]


def execute(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    steps=root/"steps";steps.mkdir(exist_ok=True)
    checks=[];calls=0;latency={}

    def check(label,condition,detail=None):
        if not condition:raise AssertionError(label+" | "+json.dumps(detail,sort_keys=True))
        checks.append(label)

    def dbs(case):
        return (root/(case+"-sender.sqlite"),
                root/(case+"-receiver.sqlite"),
                root/(case+"-audit.sqlite"))

    def call(case,tool,stage,thread=None,expect_crash=None,**options):
        nonlocal calls
        sender,receiver,auditor=dbs(case)
        thread=thread or "alpha-"+case
        if tool=="p07":
            args=P07+["--db",str(sender),"--stage",stage,"--thread",thread,
                       "--key","p09-"+thread]
        elif tool=="p09":
            args=P09+["--db",str(sender),"--stage",stage,"--thread",thread]
        elif tool=="p10":
            args=P10+["--db",str(sender),"--stage",stage]
        else:
            args=P11+["--sender",str(sender),"--receiver",str(receiver),
                       "--auditor",str(auditor),"--stage",stage]
        for key,value in options.items():
            args+=["--"+key.replace("_","-"),str(value)]
        begin=time.monotonic()
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=55)
        duration=round((time.monotonic()-begin)*1000,2)
        calls+=1
        evidence={"case":case,"stage":stage,"tool":tool,"thread":thread,
                  "duration_ms":duration,"exit":p.returncode,
                  "stdout":p.stdout[-3500:],"stderr":p.stderr[-1800:]}
        (steps/f"{calls:03d}-{case}-{tool}-{stage}.json").write_text(
            json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
        if expect_crash:
            check(case+" "+stage+" actual abrupt "+str(expect_crash),
                  p.returncode==expect_crash and not p.stdout.strip(),evidence)
            marker=Path(str(sender)+((".p09-faults.jsonl") if expect_crash==89
                                       else ".p11-faults.jsonl"))
            marks=[json.loads(x) for x in marker.read_text("utf-8").splitlines()]
            wanted=options.get("site") if expect_crash==89 else options.get("fault")
            check(case+" "+stage+" fsynced process marker",
                  marks[-1][("site" if expect_crash==89 else "fault")]==wanted
                  and marks[-1]["pid"]>0,marks)
            return None
        if p.returncode:
            raise RuntimeError("unexpected CLI failure "+json.dumps(evidence))
        return json.loads(p.stdout)

    def produce(case):
        thread="alpha-"+case
        initial=call(case,"p09","start")
        check(case+" real LangGraph review",initial["interrupted"]
              and "review" in initial["next"],initial)
        grant=call(case,"p07","grant")
        check(case+" scoped synthetic approval",grant["granted"] is True,grant)
        call(case,"p09","fault",site="checkpoint_before",expect_crash=89)
        enrolled=call(case,"p10","scan")
        check(case+" actual crash orphan enrolled in separate coordinator queue",
              enrolled["results"][0]["status"]=="QUEUED",enrolled)
        lease=call(case,"p10","claim",owner="local-coordinator",lease_seconds=10)
        settled=call(case,"p10","apply",thread=thread,owner=lease["owner"],
                     token=lease["token"])
        check(case+" atomic local effect/outbox/audit from Pilot10",
              lease["status"]=="CLAIMED" and settled["status"]=="DONE",settled)
        return thread

    def get_claim(case,owner="sender-worker",duration=5):
        claim=call(case,"p11","claim",owner=owner,lease_seconds=duration)
        check(case+" "+owner+" got genuine fenced sender claim",
              claim["status"]=="CLAIMED" and len(claim["token"])>=16,claim)
        return claim

    def send(case,task,**options):
        return call(case,"p11","process",tenant=task["tenant"],key=task["key"],
                    owner=task["owner"],token=task["token"],**options)

    def good(case):
        observed=call(case,"p11","inspect")
        check(case+" verified three independent SQLite stores",
              observed["crossdb_consistency_observed"] is True
              and observed["audit_chain_ok"] is True
              and observed["source_count"]==observed["source_acked"]
              ==observed["receiver_unique"]==observed["auditor_events"]==1,
              observed)
        return observed

    case="normal"
    produce(case)
    task=get_claim(case)
    start=time.monotonic()
    done=send(case,task)
    latency["normal_process_ms"]=round((time.monotonic()-start)*1000,2)
    check("Normal dispatch writes distinct recipient, source ACK and separate audit",
          done["status"]=="DONE" and done["receiver_inserted"]==1,done)
    good(case)
    none=call(case,"p11","claim")
    check("ACKed local task is not reclaimed",none["status"]=="NO_PENDING",none)

    for fault in ("receiver_before_commit","receiver_after_commit"):
        case="crash-"+fault.replace("_","-")
        produce(case)
        first=get_claim(case,owner="first-worker",duration=2.5)
        send(case,first,fault=fault,expect_crash=91)
        after=call(case,"p11","inspect")
        committed=int(fault=="receiver_after_commit")
        check(case+" separate DB commit boundary actually observed",
              after["source_acked"]==0 and after["receiver_unique"]==committed
              and after["auditor_events"]==0 and
              after["receipt_before_ack"]==committed and
              after["crossdb_consistency_observed"] is False,after)
        time.sleep(2.8)
        retry=get_claim(case,owner="restart-worker",duration=6)
        check(case+" expired lease rotates fencing token",
              retry["token"]!=first["token"] and retry["attempts"]==2,retry)
        processed=send(case,retry)
        check(case+" recipient unique key prevents duplicate local receipt",
              processed["status"]=="DONE"
              and processed["receiver_inserted"]==1-committed,processed)
        good(case)

    case="crash-sender-after-ack"
    produce(case)
    first=get_claim(case,duration=6)
    send(case,first,fault="sender_after_ack",expect_crash=91)
    observed=call(case,"p11","inspect")
    check("Sender acknowledged but separate auditor missing is DETECTED",
          observed["source_acked"]==observed["receiver_unique"]==1
          and observed["auditor_events"]==0
          and observed["ack_without_audit"]==1
          and not observed["crossdb_consistency_observed"],observed)
    repair=call(case,"p11","repair")
    check("Independent auditor derives labelled ACK evidence only after corroboration",
          repair["actions"][0]["status"]=="RECORDED"
          and repair["actions"][0]["event"]=="RECONCILED_ACK",repair)
    good(case)
    again=call(case,"p11","repair")
    check("Auditor repair is idempotent",
          again["actions"][0]["status"]=="ALREADY: audit_recorded",again)

    case="clock-skew"
    produce(case)
    future=call(case,"p11","claim",owner="clock-forward",clock_offset=3600)
    past=call(case,"p11","claim",owner="clock-backward",clock_offset=-3600)
    check("Injected +3600/-3600 second clock drift fails closed at claim",
          future["status"]==past["status"]=="BLOCK: clock_skew",
          {"forward":future,"backward":past})
    task=get_claim(case,duration=9)
    bad=send(case,task,clock_offset=3600)
    check("Clock jump after claim cannot authorize receipt or sender ACK",
          bad["status"]=="BLOCK: clock_skew"
          and call(case,"p11","inspect")["receiver_unique"]==0,bad)
    valid=send(case,task)
    check("Canonical single-host SQLite time permits subsequent valid send",
          valid["status"]=="DONE",valid)
    good(case)

    case="lost-receipt"
    produce(case)
    task=get_claim(case,duration=8)
    send(case,task)
    _,recipient,_=dbs(case)
    with sqlite3.connect(recipient) as db:
        db.execute("DELETE FROM p08_inbox")
    observed=call(case,"p11","inspect")
    repair=call(case,"p11","repair")
    check("Missing recipient receipt cannot be recreated by audit repair",
          observed["ack_without_receipt"]==1
          and not observed["crossdb_consistency_observed"]
          and repair["actions"][0]["status"]=="BLOCK: uncorroborated_ack",observed)

    case="tampered-audit"
    produce(case)
    task=get_claim(case,duration=8)
    send(case,task)
    _,_,audit=dbs(case)
    with sqlite3.connect(audit) as db:
        db.execute("UPDATE p11_audit_events SET row_sha256=?",("f"*64,))
    observed=call(case,"p11","inspect")
    check("Third-database hash-chain row mutation detected independently",
          not observed["audit_chain_ok"] and
          not observed["crossdb_consistency_observed"],observed)

    result={"schema_version":1,"all_passed":True,"strict_checks":len(checks),
            "checks":checks,"cli_processes":calls,
            "actual_producer":"LangGraph 1.2.18 / SqliteSaver 3.1.2 + P10 coordinator",
            "distinct_sqlite_transaction_domains":3,
            "real_crashes":"os._exit(89) and os._exit(91) with fsynced markers",
            "recovery_time_observation_ms":latency,
            "test_clock_offsets_seconds":[3600,-3600],
            "real_multihost_clock_test":False,"external_audit_anchor":False,
            "true_crossdb_atomicity_proved":False,
            "real_identity_verified":False,"real_orders":0,"real_model_calls":0,
            "limits":["All databases reside on same GitHub Actions host",
                      "No real network partition, NTP discontinuity or distributed quorum",
                      "DB-local shared clock guard uses only one host SQLite time",
                      "Audit hash chain detects row tamper but not malicious full rewrite without anchor",
                      "ACK and independent audit are not one atomic transaction",
                      "Recipient inbox is local synthetic receipt, not real-world side effect"]}
    (root/"pilot11-result.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS PILOT 11",len(checks),"strict checks",calls,
          "separate Python CLI processes across three SQLite databases")
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output-dir",type=Path)
    args=p.parse_args()
    if args.output_dir:execute(args.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="atlas-p11-") as d:execute(d)
