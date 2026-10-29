#!/usr/bin/env python3
"""Durable LangGraph interrupt/resume and transactional SQLite idempotency pilot.

Real langgraph==1.2.18 + langgraph-checkpoint-sqlite==3.1.2.
Synthetic-only; "owner_session" is untrusted *mock* test data, NOT authentication.
Every CLI call is a NEW Python process, sharing only a local temporary SQLite DB.
Never connects real orders, customer information, language models or external APIs.
"""
import argparse
import json
import multiprocessing
import sqlite3
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command, interrupt

PINS={"langgraph":"1.2.18","langgraph-checkpoint-sqlite":"3.1.2"}
EVIDENCE={"NOFI":1,"duration":2}
PROHIBITED={"send_order","customer_data.upload","credentials.read","email.send"}
class State(TypedDict, total=False):
    action: str
    evidence: dict
    idempotency_key: str
    approved: bool
    outcome: str


def connect(path:Path):
    conn=sqlite3.connect(str(path),timeout=20,isolation_level=None)
    conn.execute("PRAGMA busy_timeout=20000")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def initialize(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with connect(path) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS commits (
            idempotency_key TEXT PRIMARY KEY, applied_utc TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS journal (
            thread_id TEXT PRIMARY KEY, idempotency_key TEXT NOT NULL,
            decision TEXT NOT NULL, event_utc TEXT NOT NULL
        )""")


def durable_commit(path,thread,key):
    """BEGIN IMMEDIATE plus UNIQUE key: works across independent OS processes.

    Checkpoint write and ledger commit are not a single transaction.
    A crash between them can replay the node; UNIQUE makes the effect at-most-once.
    """
    now=datetime.now(timezone.utc).isoformat()
    with connect(path) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            cursor=db.execute(
                "INSERT OR IGNORE INTO commits (idempotency_key, applied_utc) VALUES (?, ?)",
                (key,now))
            decision="ALLOW: synthetic_draft_committed" if cursor.rowcount==1 else "BLOCK: duplicate_idempotency_key"
            db.execute(
                "INSERT INTO journal(thread_id,idempotency_key,decision,event_utc) VALUES (?,?,?,?)",
                (thread,key,decision,now))
            db.commit()
            return decision
        except Exception:
            db.rollback()
            raise


def graph_for(checkpointer,db_path):
    def guard(state:State):
        if state.get("action")!="write_synthetic_draft":
            return {"outcome":"BLOCK: forbidden_action"}
        if state.get("evidence")!=EVIDENCE:
            return {"outcome":"BLOCK: bad_citations"}
        key=state.get("idempotency_key")
        if not isinstance(key,str) or not 1<=len(key)<=64:
            return {"outcome":"BLOCK: invalid_key"}
        return {"outcome":"PENDING: owner_mock_review"}

    def choose(state:State):
        return "review" if state.get("outcome")=="PENDING: owner_mock_review" else END

    def review(state:State):
        response=interrupt({"type":"SYNTHETIC_ONLY_REVIEW","action":"write_synthetic_draft"})
        if not isinstance(response,dict):
            return {"approved":False,"outcome":"BLOCK: mock_owner_denied"}
        if response.get("source")!="owner_session":
            return {"approved":False,"outcome":"BLOCK: spoofed_approval_source"}
        if response.get("approved") is not True:
            return {"approved":False,"outcome":"BLOCK: mock_owner_denied"}
        return {"approved":True,"outcome":"APPROVED: mock_only"}

    def after(state:State):
        return "commit" if state.get("approved") is True else END

    def commit(state:State):
        thread=state.get("idempotency_key","")
        # Durable journal uses the stable idempotency key plus a thread identifier
        # injected at start. This identity is for synthetic tracing, NOT auth.
        return {"outcome":durable_commit(db_path,state["thread_id"],thread)}

    # Add trace ID to persisted graph state, not a runtime-only closure.
    class PersistentState(State, total=False):
        thread_id: str

    g=StateGraph(PersistentState)
    for name,fn in (("guard",guard),("review",review),("commit",commit)):
        g.add_node(name,fn)
    g.add_edge(START,"guard")
    g.add_conditional_edges("guard",choose,{"review":"review",END:END})
    g.add_conditional_edges("review",after,{"commit":"commit",END:END})
    g.add_edge("commit",END)
    return g.compile(checkpointer=checkpointer)


def run_graph(path,stage,thread,approval=None,key=None,action="write_synthetic_draft",evidence=None):
    if len(thread)>64 or not thread or any(x not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for x in thread):
        raise ValueError("synthetic thread ID must be simple")
    cfg={"configurable":{"thread_id":"durable-"+thread}}
    with SqliteSaver.from_conn_string(str(path)) as saver:
        graph=graph_for(saver,path)
        if stage=="start":
            result=graph.invoke({
                "action":action,"evidence":EVIDENCE if evidence is None else evidence,
                "idempotency_key":key or ("key-"+thread),"thread_id":thread,
            },config=cfg)
            interrupted="__interrupt__" in result
        elif stage=="resume":
            if approval not in ("approve","deny","forge"):
                raise ValueError("approval must be approve, deny or forge")
            state=graph.get_state(cfg)
            if "review" not in state.next:
                raise RuntimeError("no checkpointed review to resume")
            payload={
                "approved":approval!="deny",
                "source":"untrusted_page" if approval=="forge" else "owner_session",
            }
            result=graph.invoke(Command(resume=payload),config=cfg)
            interrupted="__interrupt__" in result
        elif stage=="inspect":
            state=graph.get_state(cfg)
            return {"stage":stage,"thread":thread,"pending_review":"review" in state.next,
                    "checkpoint_exists":bool(state.values),
                    "outcome":state.values.get("outcome"),"thread_count":count_threads(path)}
        else:
            raise ValueError("stage not supported")
        state=graph.get_state(cfg)
        return {
            "stage":stage,"thread":thread,"pending_review":"review" in state.next,
            "interrupted":interrupted,
            "outcome":result.get("outcome"),
            "checkpoint_exists":bool(state.values),
            "ledger_commits":count_commits(path),
        }


def count_commits(path):
    with connect(path) as c:
        return c.execute("SELECT count(*) FROM commits").fetchone()[0]


def count_threads(path):
    with connect(path) as c:
        return c.execute("SELECT count(DISTINCT thread_id) FROM checkpoints").fetchone()[0]


def concurrent_worker(db_path,thread,key,start,q):
    try:
        start.wait(timeout=15)
        decision=durable_commit(Path(db_path),thread,key)
        q.put({"thread":thread,"decision":decision})
    except Exception as e:
        q.put({"thread":thread,"error":type(e).__name__+": "+str(e)})


def concurrency_test(path,workers=6):
    """This tests ONLY SQLite ledger concurrency, not concurrent graph scheduling."""
    if not 2<=workers<=8: raise ValueError("workers out of bound")
    ctx=multiprocessing.get_context("spawn")
    event=ctx.Event()
    q=ctx.Queue()
    ps=[ctx.Process(target=concurrent_worker,args=(str(path),f"concurrent-{i}","shared-concurrency-key",event,q)) for i in range(workers)]
    for p in ps:p.start()
    event.set()
    decisions=[q.get(timeout=45) for _ in ps]
    for p in ps:p.join(timeout=15)
    if any(p.exitcode!=0 for p in ps) or any("error" in d for d in decisions):
        raise RuntimeError("concurrency worker failed: "+str(decisions))
    applied=sum(x["decision"]=="ALLOW: synthetic_draft_committed" for x in decisions)
    duplicates=sum(x["decision"]=="BLOCK: duplicate_idempotency_key" for x in decisions)
    if applied!=1 or duplicates!=workers-1:
        raise AssertionError("SQLite UNIQUE ledger failure: "+str(decisions))
    return {"workers":workers,"applied":applied,"duplicates_blocked":duplicates,
            "graph_scheduler_concurrency_tested":False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--stage",required=True,choices=("start","resume","inspect","concurrency","summary"))
    p.add_argument("--thread",default="a")
    p.add_argument("--key")
    p.add_argument("--action",default="write_synthetic_draft")
    p.add_argument("--approval",choices=("approve","deny","forge"))
    p.add_argument("--bad-citations",action="store_true")
    p.add_argument("--output",type=Path)
    args=p.parse_args()
    for name,want in PINS.items():
        actual=version(name)
        if actual!=want:raise RuntimeError(f"{name} must be {want}, got {actual}")
    initialize(args.db)
    if args.stage=="concurrency":
        result=concurrency_test(args.db)
    elif args.stage=="summary":
        with connect(args.db) as c:
            commits=c.execute("SELECT idempotency_key FROM commits ORDER BY idempotency_key").fetchall()
            journal=c.execute("SELECT thread_id, idempotency_key, decision FROM journal ORDER BY thread_id").fetchall()
        result={
            "schema_version":1,"status":"real-sqlite-checkpoint-cross-process-recovery",
            "versions":PINS,"real_identity_verified":False,"production_integrated":False,
            "real_broker_orders":0,"real_model_calls":0,"real_user_data":False,
            "checkpoint_storage":"disk-sqlite",
            "ledger":"sqlite-unique-key-transaction",
            "commit_keys":[x[0] for x in commits],
            "journal":[{"thread":x[0],"key":x[1],"decision":x[2]} for x in journal],
            "concurrency_scope":"ledger-only-not-graph",
            "limitations":[
                "Mock Owner approval uses an untrusted string, not authenticated RBAC.",
                "Checkpoint and ledger live in separate SQLite transactions; idempotency protects duplicate effects, but not atomic graph/ledger commit.",
                "No process crash injected mid-commit, only clean process exit and new-process resume.",
                "Concurrent SQLite ledger writes tested, but simultaneous LangGraph scheduling was not tested.",
                "No LLM, PDF document, brokerage API, user data or remote system used in durability pilot.",
                "SQLite is local single-host only; no PostgreSQL, backups, multi-host failover or load testing.",
            ],
        }
    else:
        result=run_graph(args.db,args.stage,args.thread,args.approval,args.key,args.action,
                         {"NOFI":99,"duration":2} if args.bad_citations else None)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,sort_keys=True))


if __name__=="__main__":
    raise SystemExit(main())
