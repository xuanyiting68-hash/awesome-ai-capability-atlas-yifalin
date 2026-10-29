#!/usr/bin/env python3
"""Pilot 07: REAL LangGraph/SqliteSaver hard-crash windows + atomic local outbox.

Fully synthetic, local SQLite only. CLI principals are test fixtures, NOT authentication.
No network, broker, production YIFALIN, LLM, customer information or external effects.
This intentionally reuses Pilot 06's real StateGraph, interrupt and SqliteSaver.
"""
import argparse
import json
import os
import sqlite3
import time
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from scripts import real_durable_recovery as base

ROLES = {"alpha_owner": ("alpha", "owner"), "beta_owner": ("beta", "owner"),
         "alpha_viewer": ("alpha", "viewer")}
FAULTS = {"before_transaction", "before_commit", "after_commit"}
FAULT = None
MARKER = None


def setup(path):
    base.initialize(path)
    with base.connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS p07_approvals (
            thread TEXT PRIMARY KEY, tenant TEXT NOT NULL, actor TEXT NOT NULL,
            resource TEXT NOT NULL, idem TEXT NOT NULL, expires_at REAL NOT NULL,
            revoked INTEGER NOT NULL DEFAULT 0, consumed INTEGER NOT NULL DEFAULT 0
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS p07_effects (
            tenant TEXT NOT NULL, idem TEXT NOT NULL, thread TEXT NOT NULL,
            payload TEXT NOT NULL, PRIMARY KEY(tenant, idem)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS p07_outbox (
            tenant TEXT NOT NULL, idem TEXT NOT NULL, payload TEXT NOT NULL,
            delivered INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(tenant, idem)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS p07_audit (
            tenant TEXT NOT NULL, idem TEXT NOT NULL, thread TEXT NOT NULL,
            event TEXT NOT NULL, PRIMARY KEY(tenant, idem)
        )""")


def tenant_for(thread):
    tenant = thread.split("-", 1)[0]
    if tenant not in ("alpha", "beta"):
        raise ValueError("only alpha/beta synthetic tenants exist")
    return tenant


def grant(path, thread, key, principal, ttl=60):
    tenant = tenant_for(thread)
    identity = ROLES.get(principal)
    if identity != (tenant, "owner"):
        return {"granted": False, "reason": "test_service_role_or_tenant_denied"}
    with base.connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            db.execute("""INSERT INTO p07_approvals(thread,tenant,actor,resource,idem,expires_at)
                VALUES (?,?,?,?,?,?)""",
                (thread, tenant, principal, "synthetic_draft", key, time.time()+ttl))
            db.commit()
        except Exception:
            db.rollback()
            raise
    return {"granted": True, "identity_is_real": False}


def mark_and_die(where):
    if FAULT != where:
        return
    # Flush a sanitized marker before an actual abrupt os._exit, never exception/clean exit.
    with open(MARKER, "a", encoding="utf-8") as log:
        log.write(json.dumps({"fault": where, "pid": os.getpid()})+"\n")
        log.flush()
        os.fsync(log.fileno())
    os._exit(86)


def consistent_commit(path, thread, key):
    tenant = tenant_for(thread)
    mark_and_die("before_transaction")
    with base.connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            existing = db.execute(
                "SELECT thread FROM p07_effects WHERE tenant=? AND idem=?",
                (tenant, key)).fetchone()
            if existing:
                # Exactly the same local effect is already atomically committed.
                # In particular the approval must NOT be consumed a second time.
                db.commit()
                return "ALREADY: synthetic_draft_committed"
            approval = db.execute("""SELECT tenant,resource,idem,expires_at,revoked,consumed
                FROM p07_approvals WHERE thread=?""", (thread,)).fetchone()
            if not approval:
                db.commit()
                return "BLOCK: missing_server_approval"
            a_tenant, resource, a_key, expires, revoked, consumed = approval
            if a_tenant != tenant or resource != "synthetic_draft" or a_key != key:
                db.commit()
                return "BLOCK: approval_scope_mismatch"
            if revoked or expires <= time.time() or consumed:
                db.commit()
                return "BLOCK: revoked_expired_or_consumed"
            payload = json.dumps({"kind": "synthetic_draft", "tenant": tenant,
                                  "idempotency_key": key}, sort_keys=True)
            db.execute("""INSERT INTO p07_effects(tenant,idem,thread,payload)
                VALUES (?,?,?,?)""", (tenant, key, thread, payload))
            db.execute("""INSERT INTO p07_outbox(tenant,idem,payload)
                VALUES (?,?,?)""", (tenant, key, payload))
            db.execute("""INSERT INTO p07_audit(tenant,idem,thread,event)
                VALUES (?,?,?,?)""", (tenant, key, thread, "local_atomic_commit"))
            db.execute("UPDATE p07_approvals SET consumed=1 WHERE thread=?", (thread,))
            mark_and_die("before_commit")
            db.commit()
            mark_and_die("after_commit")
            return "ALLOW: synthetic_draft_committed"
        except Exception:
            db.rollback()
            raise


# The reused real Pilot 06 graph calls durable_commit as a module global.
base.durable_commit = consistent_commit


def snapshot(path):
    with base.connect(path) as db:
        counts = {table: db.execute("SELECT count(*) FROM p07_"+table).fetchone()[0]
                  for table in ("approvals", "effects", "outbox", "audit")}
        consumed = db.execute(
            "SELECT count(*) FROM p07_approvals WHERE consumed=1").fetchone()[0]
        rows = db.execute("""SELECT e.tenant,e.idem,e.thread
             FROM p07_effects e LEFT JOIN p07_outbox o
               ON e.tenant=o.tenant AND e.idem=o.idem
             LEFT JOIN p07_audit a
               ON e.tenant=a.tenant AND e.idem=a.idem
             WHERE o.idem IS NULL OR a.idem IS NULL OR o.payload!=e.payload""").fetchall()
        orphans = db.execute("""SELECT count(*) FROM p07_outbox o LEFT JOIN p07_effects e
             ON o.tenant=e.tenant AND o.idem=e.idem WHERE e.idem IS NULL""").fetchone()[0]
        return {"counts":counts, "consumed_approvals":consumed,
                "reconciliation_ok":not rows and not orphans and
                counts["effects"]==counts["outbox"]==counts["audit"],
                "real_identity_verified":False, "external_delivery_tested":False,
                "end_to_end_exactly_once_proved":False, "trading_orders":0}


def run_graph(path, stage, thread, key):
    cfg={"configurable":{"thread_id":"pilot07-"+thread}}
    with SqliteSaver.from_conn_string(str(path)) as saver:
        graph=base.graph_for(saver,path)
        if stage=="start":
            result=graph.invoke({"action":"write_synthetic_draft",
                 "evidence":base.EVIDENCE,"idempotency_key":key,"thread_id":thread},
                 config=cfg)
        elif stage=="resume":
            # THIS MOCK SOURCE IS NOT AN AUTH TOKEN: database ticket is decisive.
            result=graph.invoke(Command(resume={"approved":True,
                "source":"owner_session"}),config=cfg)
        elif stage=="recover":
            # Runnable graph continuation from last persisted checkpoint after os._exit(86).
            result=graph.invoke(None,config=cfg)
        else:
            raise ValueError(stage)
        state=graph.get_state(cfg)
        return {"stage":stage,"outcome":result.get("outcome"),
                "next":list(state.next),"interrupted":"__interrupt__" in result,
                "pid":os.getpid(),**snapshot(path)}


def main():
    global FAULT, MARKER
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--stage",required=True,
                   choices=("start","resume","recover","grant","revoke","inspect"))
    p.add_argument("--thread",default="alpha-example")
    p.add_argument("--key",default="fixture-01")
    p.add_argument("--principal",default="alpha_owner")
    p.add_argument("--ttl",type=float,default=60)
    p.add_argument("--fault",choices=sorted(FAULTS))
    args=p.parse_args()
    FAULT=args.fault
    MARKER=str(args.db.with_suffix(".faults.jsonl"))
    setup(args.db)
    if args.stage=="grant":
        result=grant(args.db,args.thread,args.key,args.principal,args.ttl)
    elif args.stage=="revoke":
        with base.connect(args.db) as db:
            db.execute("UPDATE p07_approvals SET revoked=1 WHERE thread=?",
                       (args.thread,))
        result={"revoked":True}
    elif args.stage=="inspect":
        result=snapshot(args.db)
    else:
        result=run_graph(args.db,args.stage,args.thread,args.key)
    print(json.dumps(result,sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
