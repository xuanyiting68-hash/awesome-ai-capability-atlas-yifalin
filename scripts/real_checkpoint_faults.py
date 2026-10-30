#!/usr/bin/env python3
"""Pilot 09: execute LangGraph + SqliteSaver with actual SQLite trigger fault hooks.

Trigger callbacks call os._exit(89) *inside* SQLite INSERT statements on
checkpoints or writes, before/after row insertion and before transaction commit.
Independent Python process reopens DB afterward. Synthetic local-only testing.
"""
import argparse
import json
import os
import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from scripts import real_crash_consistency as p07
from scripts import real_durable_recovery as base

SITES={"checkpoint_before":("checkpoints","BEFORE"),
       "checkpoint_after":("checkpoints","AFTER"),
       "writes_after":("writes","AFTER")}


def config(thread):
    return {"configurable":{"thread_id":"pilot07-"+thread}}


def snapshot(db,thread):
    with SqliteSaver.from_conn_string(str(db)) as saver:
        graph=base.graph_for(saver,db)
        state=graph.get_state(config(thread))
        with base.connect(db) as conn:
            checkpoints=conn.execute("SELECT count(*) FROM checkpoints WHERE thread_id=?",
                                     ("pilot07-"+thread,)).fetchone()[0]
            writes=conn.execute("SELECT count(*) FROM writes WHERE thread_id=?",
                                ("pilot07-"+thread,)).fetchone()[0]
        return {"thread":thread,"next":list(state.next),
                "outcome":state.values.get("outcome") if state.values else None,
                "checkpoint_rows":checkpoints,"write_rows":writes,
                **p07.snapshot(db)}


def attach_fault(saver,site,db):
    table,when=SITES[site]
    marker=Path(str(db)+".p09-faults.jsonl")
    def die():
        with marker.open("a",encoding="utf-8") as stream:
            stream.write(json.dumps({"site":site,"pid":os.getpid(),
                                     "sqlite_trigger":True})+"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os._exit(89)

    saver.setup()
    saver.conn.create_function("p09_fail_now",0,die)
    # TEMP trigger belongs to this one connection, so recovered readers never
    # inherit an unknown or unregistered SQL function on restart.
    saver.conn.execute(
        f"CREATE TEMP TRIGGER p09_inject_{table} {when} INSERT ON main.{table} "
        "BEGIN SELECT p09_fail_now(); END")


def run(path,stage,thread,site):
    p07.setup(path)
    with SqliteSaver.from_conn_string(str(path)) as saver:
        graph=base.graph_for(saver,path)
        cfg=config(thread)
        if stage=="start":
            result=graph.invoke({"action":"write_synthetic_draft",
                "evidence":base.EVIDENCE,"idempotency_key":"p09-"+thread,
                "thread_id":thread},config=cfg,durability="sync")
        elif stage=="fault":
            state=graph.get_state(cfg)
            if "review" not in state.next:
                raise AssertionError("must start from durable interrupt")
            attach_fault(saver,site,path)
            result=graph.invoke(Command(resume={"approved":True,
                "source":"owner_session"}),config=cfg,durability="sync")
        elif stage=="recover":
            state=graph.get_state(cfg)
            if "review" in state.next:
                result=graph.invoke(Command(resume={"approved":True,
                    "source":"owner_session"}),config=cfg,durability="sync")
            elif state.next:
                result=graph.invoke(None,config=cfg,durability="sync")
            else:
                result=state.values
        else:raise ValueError(stage)
        state=graph.get_state(cfg)
        return {"stage":stage,"outcome":result.get("outcome"),
                "next":list(state.next),"interrupted":"__interrupt__" in result,
                "pid":os.getpid(),**p07.snapshot(path)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",type=Path,required=True)
    p.add_argument("--stage",choices=("start","fault","recover","inspect"),required=True)
    p.add_argument("--thread",required=True)
    p.add_argument("--site",choices=sorted(SITES),default="checkpoint_before")
    a=p.parse_args()
    if a.stage=="inspect":
        result=snapshot(a.db,a.thread)
    else:
        result=run(a.db,a.stage,a.thread,a.site)
    print(json.dumps(result,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
