#!/usr/bin/env python3
"""Pilot 10: independent durable task reconciliation, fenced lease and atomic compensation.

Requires real Pilot 09 LangGraph/SqliteSaver checkpoints for enrollment, but the
recovery worker consumes its OWN local SQLite task queue. All effects, approvals,
outbox and audit remain synthetic and LOCAL. No external identity, model or orders.
"""
import argparse
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
from scripts import real_crash_consistency as p07
from scripts import real_durable_recovery as base

FAULTS=("before_commit","after_commit")
PHASES=("PENDING","LEASED","DONE","BLOCKED")


def setup(path):
    p07.setup(path)
    with base.connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS p10_tasks(
          thread TEXT PRIMARY KEY, tenant TEXT NOT NULL, idem TEXT NOT NULL,
          phase TEXT NOT NULL CHECK(phase IN ('PENDING','LEASED','DONE','BLOCKED')),
          lease_owner TEXT, lease_token TEXT, lease_until REAL,
          attempts INTEGER NOT NULL DEFAULT 0,
          last_result TEXT NOT NULL DEFAULT '',
          created REAL NOT NULL, updated REAL NOT NULL,
          UNIQUE(tenant,idem))""")


def ticket(db,thread,tenant,key):
    t=db.execute("""SELECT tenant,resource,idem,expires_at,revoked,consumed
                   FROM p07_approvals WHERE thread=?""",(thread,)).fetchone()
    if t is None or t[:3]!=(tenant,"synthetic_draft",key):
        return None
    return t


def graph_approved(path,thread,key):
    with SqliteSaver.from_conn_string(str(path)) as saver:
        graph=base.graph_for(saver,path)
        state=graph.get_state({"configurable":{"thread_id":"pilot07-"+thread}})
        values=state.values or {}
        return (not state.next and values.get("outcome")=="APPROVED: mock_only"
                and values.get("approved") is True
                and values.get("thread_id")==thread
                and values.get("idempotency_key")==key
                and values.get("evidence")==base.EVIDENCE
                and values.get("action")=="write_synthetic_draft")


def enrollment(path,thread):
    tenant=p07.tenant_for(thread)
    key="p09-"+thread
    if len(key)>64:
        return {"status":"BLOCK: invalid_key"}
    if not graph_approved(path,thread,key):
        return {"status":"BLOCK: no_approved_terminal_graph_checkpoint"}
    now=time.time()
    with base.connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            t=ticket(db,thread,tenant,key)
            if t is None:
                answer={"status":"BLOCK: missing_scoped_ticket"}
            else:
                prior=db.execute("SELECT thread FROM p07_effects WHERE tenant=? AND idem=?",
                                 (tenant,key)).fetchone()
                if prior:
                    answer={"status":"ALREADY: local_effect_present"}
                elif t[4] or t[5] or t[3]<=now:
                    answer={"status":"BLOCK: ticket_revoked_expired_or_consumed"}
                else:
                    old=db.execute("SELECT phase FROM p10_tasks WHERE thread=?",
                                   (thread,)).fetchone()
                    if old:
                        answer={"status":"ALREADY: queued","phase":old[0]}
                    else:
                        collision=db.execute("SELECT thread FROM p10_tasks WHERE tenant=? AND idem=?",
                                             (tenant,key)).fetchone()
                        if collision:
                            answer={"status":"BLOCK: conflicting_queue_key"}
                        else:
                            db.execute("""INSERT INTO p10_tasks
                              (thread,tenant,idem,phase,created,updated)
                              VALUES (?,?,?,'PENDING',?,?)""",
                              (thread,tenant,key,now,now))
                            answer={"status":"QUEUED","thread":thread}
            db.commit()
            return answer
        except Exception:
            db.rollback()
            raise


def scan(path):
    with base.connect(path) as db:
        threads=[x[0] for x in db.execute("SELECT thread FROM p07_approvals ORDER BY thread")]
    return {"results":[{"thread":t,**enrollment(path,t)} for t in threads],
            "identity_is_real":False}


def claim(path,owner,lease_seconds=1.0,tenant=None):
    if not isinstance(owner,str) or not 1<=len(owner)<=48 or not owner.replace("_","").replace("-","").isalnum():
        raise ValueError("invalid synthetic owner")
    if not 0.25<=lease_seconds<=60:
        raise ValueError("lease outside experiment bounds")
    if tenant is not None and tenant not in ("alpha","beta"):
        raise ValueError("only synthetic tenants")
    now=time.time()
    with base.connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            row=db.execute("""SELECT thread,tenant,idem,attempts
              FROM p10_tasks
              WHERE (phase='PENDING' OR (phase='LEASED' AND lease_until<=?))
              AND (? IS NULL OR tenant=?)
              ORDER BY created,thread LIMIT 1""",(now,tenant,tenant)).fetchone()
            if row is None:
                db.commit()
                return {"status":"NO_WORK"}
            thread,t,key,attempts=row
            tk=ticket(db,thread,t,key)
            effect=db.execute("SELECT thread FROM p07_effects WHERE tenant=? AND idem=?",
                              (t,key)).fetchone()
            if tk is None or (not effect and (tk[4] or tk[5] or tk[3]<=now)):
                db.execute("""UPDATE p10_tasks SET phase='BLOCKED',last_result=?,
                    lease_owner=NULL,lease_token=NULL,lease_until=NULL,updated=? WHERE thread=?""",
                    ("ticket_not_active",now,thread))
                db.commit()
                return {"status":"BLOCK: ticket_not_active","thread":thread}
            token=uuid.uuid4().hex
            db.execute("""UPDATE p10_tasks SET phase='LEASED',lease_owner=?,
              lease_token=?,lease_until=?,attempts=attempts+1,updated=? WHERE thread=?""",
              (owner,token,now+lease_seconds,now,thread))
            db.commit()
            return {"status":"CLAIMED","thread":thread,"tenant":t,"key":key,
                    "owner":owner,"token":token,"attempts":attempts+1}
        except Exception:
            db.rollback()
            raise


def mark_crash(path,where):
    marker=Path(str(path)+".p10-faults.jsonl")
    with marker.open("a",encoding="utf-8") as f:
        f.write(json.dumps({"site":where,"pid":os.getpid()})+"\n")
        f.flush()
        os.fsync(f.fileno())
    os._exit(90)


def apply(path,thread,owner,token,fault=None):
    tenant=p07.tenant_for(thread)
    now=time.time()
    with base.connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            task=db.execute("""SELECT tenant,idem,phase,lease_owner,lease_token,lease_until
                  FROM p10_tasks WHERE thread=?""",(thread,)).fetchone()
            if (task is None or task[0]!=tenant or task[2]!="LEASED"
                    or task[3]!=owner or task[4]!=token or task[5]<=now):
                db.commit()
                return {"status":"BLOCK: stale_or_missing_fenced_lease"}
            t,key=task[:2]
            tk=ticket(db,thread,t,key)
            effect=db.execute("SELECT thread,payload FROM p07_effects WHERE tenant=? AND idem=?",
                              (t,key)).fetchone()
            if tk is None or (not effect and (tk[4] or tk[5] or tk[3]<=now)):
                db.execute("""UPDATE p10_tasks SET phase='BLOCKED',last_result='ticket_not_active',
                    lease_owner=NULL,lease_token=NULL,lease_until=NULL,updated=? WHERE thread=?""",
                    (now,thread))
                db.commit()
                return {"status":"BLOCK: ticket_not_active"}
            payload=json.dumps({"kind":"synthetic_draft","tenant":t,"idempotency_key":key},
                               sort_keys=True)
            if effect:
                out=db.execute("SELECT payload FROM p07_outbox WHERE tenant=? AND idem=?",
                               (t,key)).fetchone()
                audit=db.execute("SELECT thread FROM p07_audit WHERE tenant=? AND idem=?",
                                 (t,key)).fetchone()
                if effect!=(thread,payload) or out!=(payload,) or audit!=(thread,):
                    db.commit()
                    return {"status":"BLOCK: inconsistent_existing_effect"}
                decision="ALREADY: validated_local_effect"
            else:
                db.execute("""INSERT INTO p07_effects(tenant,idem,thread,payload)
                          VALUES(?,?,?,?)""",(t,key,thread,payload))
                db.execute("""INSERT INTO p07_outbox(tenant,idem,payload)
                          VALUES(?,?,?)""",(t,key,payload))
                db.execute("""INSERT INTO p07_audit(tenant,idem,thread,event)
                          VALUES(?,?,?,?)""",(t,key,thread,"p10_atomic_recovery"))
                db.execute("UPDATE p07_approvals SET consumed=1 WHERE thread=?",(thread,))
                decision="ALLOW: coordinator_local_compensation"
            db.execute("""UPDATE p10_tasks SET phase='DONE',last_result=?,
               lease_owner=NULL,lease_token=NULL,lease_until=NULL,updated=?
               WHERE thread=?""",(decision,now,thread))
            if fault=="before_commit":
                mark_crash(path,fault)
            db.commit()
            if fault=="after_commit":
                mark_crash(path,fault)
            return {"status":"DONE","decision":decision}
        except Exception:
            db.rollback()
            raise


def reconcile(path):
    with base.connect(path) as db:
        tasks=db.execute("""SELECT thread,tenant,idem,phase,attempts,last_result
             FROM p10_tasks ORDER BY thread""").fetchall()
        effects=db.execute("SELECT tenant,idem,thread,payload FROM p07_effects").fetchall()
        outbox={(t,k):payload for t,k,payload in db.execute(
                "SELECT tenant,idem,payload FROM p07_outbox")}
        audits={(t,k):thread for t,k,thread in db.execute(
                "SELECT tenant,idem,thread FROM p07_audit")}
        tickets={thread:(consumed,revoked) for thread,consumed,revoked in db.execute(
                "SELECT thread,consumed,revoked FROM p07_approvals")}
    ledger_ok=all(
        outbox.get((t,k))==payload and audits.get((t,k))==thread
        and tickets.get(thread,(-1,-1))[0]==1
        for t,k,thread,payload in effects)
    effect_map={(t,k):thread for t,k,thread,_ in effects}
    task_gaps=[thread for thread,t,k,phase,_,_ in tasks
               if (phase=="DONE") != (effect_map.get((t,k))==thread)]
    missing_tasks=[];candidates=0
    # Inspect checkpoint independently from the task queue, not from its phase.
    with base.connect(path) as db:
        approvals=db.execute("SELECT thread,idem FROM p07_approvals ORDER BY thread").fetchall()
    for thread,key in approvals:
        if key!="p09-"+thread:continue
        if graph_approved(path,thread,key):
            candidates+=1
            if thread not in {x[0] for x in tasks} and (p07.tenant_for(thread),key) not in effect_map:
                missing_tasks.append(thread)
    return {"tasks":len(tasks),"phases":{p:sum(x[3]==p for x in tasks) for p in PHASES},
            "effect_count":len(effects),"outbox_count":len(outbox),"audit_count":len(audits),
            "all_effects_reconciled":ledger_ok and len(effects)==len(outbox)==len(audits),
            "done_effect_mismatches":task_gaps,"orphaned_unqueued":missing_tasks,
            "approved_graph_candidates":candidates,
            "total_attempts":sum(x[4] for x in tasks),
            "atomic_recovery_verified":not(task_gaps or missing_tasks) and ledger_ok
                                       and all(x[3]=="DONE" for x in tasks),
            "real_identity_verified":False,"real_external_delivery":False,
            "real_orders":0}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--db",type=Path,required=True)
    parser.add_argument("--stage",choices=("scan","enqueue","claim","apply","inspect"),required=True)
    parser.add_argument("--thread")
    parser.add_argument("--owner",default="worker-one")
    parser.add_argument("--token")
    parser.add_argument("--tenant")
    parser.add_argument("--lease-seconds",type=float,default=1.0)
    parser.add_argument("--fault",choices=FAULTS)
    a=parser.parse_args()
    setup(a.db)
    if a.stage=="scan":value=scan(a.db)
    elif a.stage=="enqueue":value=enrollment(a.db,a.thread)
    elif a.stage=="claim":value=claim(a.db,a.owner,a.lease_seconds,a.tenant)
    elif a.stage=="apply":value=apply(a.db,a.thread,a.owner,a.token,a.fault)
    else:value=reconcile(a.db)
    print(json.dumps(value,ensure_ascii=False,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
