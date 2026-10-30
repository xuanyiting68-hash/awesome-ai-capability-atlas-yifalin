#!/usr/bin/env python3
"""Real SQLite checkpoint-write fault verifier; each step runs in a fresh process."""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P09=[sys.executable,"-m","scripts.real_checkpoint_faults"]
P07=[sys.executable,"-m","scripts.real_crash_consistency"]
SITES=("checkpoint_before","checkpoint_after","writes_after")


def execute(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    stages=root/"stages";stages.mkdir(exist_ok=True)
    checks=[];count=0

    def require(label,ok,details=None):
        if not ok:raise AssertionError(label+" | evidence="+json.dumps(details,sort_keys=True))
        checks.append(label)

    def call(db,tool,stage,thread,site=None,expected_exit=None,key=None):
        nonlocal count
        args=(P09+["--db",str(db),"--stage",stage,"--thread",thread]
              +(["--site",site] if site else [])
              if tool=="p09" else
              P07+["--db",str(db),"--stage",stage,"--thread",thread,
                   "--key",key or ("p09-"+thread),"--principal","alpha_owner"])
        done=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=45)
        count+=1
        evidence={"stage":stage,"tool":tool,"thread":thread,"site":site,
                  "exit_code":done.returncode,"stdout":done.stdout[-3000:],
                  "stderr":done.stderr[-1800:]}
        (stages/f"{count:03d}-{thread}-{stage}.json").write_text(
            json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
        if expected_exit is not None:
            require(site+" genuine SQL-trigger abrupt process exit",
                    done.returncode==expected_exit and not done.stdout.strip(),evidence)
            marker=Path(str(db)+".p09-faults.jsonl")
            lines=[json.loads(x) for x in marker.read_text("utf-8").splitlines()]
            require(site+" fsynced inside-SQL witness",
                    len(lines)==1 and lines[0]["site"]==site and
                    lines[0]["pid"]>0 and lines[0]["sqlite_trigger"] is True,lines)
            return None
        if done.returncode:raise RuntimeError("stage exited unexpectedly: "+json.dumps(evidence))
        return json.loads(done.stdout)

    for site in SITES:
        thread="alpha-"+site
        db=root/(site+".sqlite")
        started=call(db,"p09","start",thread)
        require(site+" real durable interrupt persisted",
                started["interrupted"] and "review" in started["next"]
                and started["counts"]["effects"]==0,started)
        approval=call(db,"p07","grant",thread)
        require(site+" synthetic server grant persisted",
                approval["granted"] and approval["identity_is_real"] is False,approval)
        call(db,"p09","fault",thread,site=site,expected_exit=89)
        after=call(db,"p09","inspect",thread)
        require(site+" SQL checkpoint store still readable after abrupt exit",
                after["checkpoint_rows"]>=1 and
                after["write_rows"]>=0 and
                after["counts"]["effects"] in (0,1) and
                after["reconciliation_ok"] is True,after)
        recovered=call(db,"p09","recover",thread)
        finalized=call(db,"p09","inspect",thread)
        require(site+" normal replay converges to one atomic local effect",
                recovered["next"]==[] and
                recovered["outcome"] in
                ("ALLOW: synthetic_draft_committed","ALREADY: synthetic_draft_committed")
                and finalized["next"]==[]
                and finalized["counts"]["effects"]==1
                and finalized["counts"]["outbox"]==1
                and finalized["counts"]["audit"]==1
                and finalized["consumed_approvals"]==1
                and finalized["reconciliation_ok"] is True,
                {"post_crash":after,"recover":recovered,"final":finalized})
        with __import__("sqlite3").connect(db) as conn:
            integrity=conn.execute("PRAGMA integrity_check").fetchone()[0]
        require(site+" SQLite physical integrity_check passes",integrity=="ok",integrity)

    result={"schema_version":1,"all_passed":True,"checks":checks,
            "cases_passed":len(checks),"independent_cli_processes":count,
            "injection_sites":list(SITES),
            "actual_upstream":{"langgraph":"1.2.18",
                               "langgraph-checkpoint-sqlite":"3.1.2"},
            "actual_crash":"os._exit(89) inside SQLite TEMP trigger user function",
            "checkpoint_durability":"sync",
            "real_identity_verified":False,"real_user_data":False,
            "real_orders":0,"real_model_calls":0,
            "failure_scope":"SQLite SQL INSERT trigger, not OS power failure",
            "limits":["Trigger termination is inside SQLite statement, not torn disk sectors",
                      "Do not infer recovery after corruption or loss of an entire disk",
                      "Graph rollback/replay may recompute and local idempotency is required",
                      "No distributed system, customer data, production approval or external effect"]}
    (root/"pilot09-result.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("PASS PILOT 09",len(checks),"checks across",count,
          "distinct Python CLI processes; no production actions")
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output-dir",type=Path)
    a=ap.parse_args()
    if a.output_dir:execute(a.output_dir)
    else:
        with tempfile.TemporaryDirectory(prefix="atlas-checkpoint-p09-") as t:
            execute(t)
