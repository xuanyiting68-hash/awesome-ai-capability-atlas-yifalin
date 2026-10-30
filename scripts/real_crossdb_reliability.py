#!/usr/bin/env python3
"""Pilot 11: real separate SQLite sender/receiver/auditor, crash gaps, skew guard.

All three DBs contain GENERATED fixtures only. The audit chain is not a trusted
external anchor and cannot prevent a privileged full rewrite. No network/orders.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import time
from pathlib import Path
from scripts import real_outbox_dispatch as p08
from scripts import real_recovery_coordinator as p10
from scripts import real_durable_recovery as base

FAULTS=("receiver_before_commit","receiver_after_commit","sender_after_ack")
EVENTS=("ACK_OBSERVED","RECONCILED_ACK")
GENESIS="0"*64


def setup(sender,receiver,auditor):
    p10.setup(sender)
    p08.setup(sender,receiver)
    Path(auditor).parent.mkdir(parents=True,exist_ok=True)
    with p08.connect(auditor) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS p11_audit_events(
          seq INTEGER PRIMARY KEY AUTOINCREMENT,
          tenant TEXT NOT NULL, idem TEXT NOT NULL,
          event TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
          prev_sha256 TEXT NOT NULL, row_sha256 TEXT NOT NULL,
          UNIQUE(tenant,idem))""")


def db_clock(db):
    # One locally hosted SQLite DB provides a shared clock for THIS experiment;
    # this is not a distributed time service or cross-host clock consensus.
    return db.execute("SELECT (julianday('now')-2440587.5)*86400.0").fetchone()[0]


def clock_gate(sender,offset):
    if not -86400 <= offset <= 86400:
        raise ValueError("synthetic skew outside bounded test range")
    with base.connect(sender) as db:
        server=db_clock(db)
    client=time.time()+offset
    delta=client-server
    return {"permitted":abs(delta)<=0.75,
            "skew_abs_ms":round(abs(delta)*1000,2),
            "shared_sqlite_clock_only":True}


def source_row(sender,tenant,key):
    with base.connect(sender) as db:
        out=db.execute("SELECT payload,delivered FROM p07_outbox WHERE tenant=? AND idem=?",
                       (tenant,key)).fetchone()
        eff=db.execute("SELECT payload FROM p07_effects WHERE tenant=? AND idem=?",
                       (tenant,key)).fetchone()
        aud=db.execute("SELECT 1 FROM p07_audit WHERE tenant=? AND idem=?",
                       (tenant,key)).fetchone()
    if out and eff and aud and out[0]==eff[0] and p08.strict_payload(tenant,key,out[0]):
        return {"payload":out[0],"delivered":out[1]}
    return None


def crash(sender,site):
    marker=Path(str(sender)+".p11-faults.jsonl")
    with marker.open("a",encoding="utf-8") as f:
        f.write(json.dumps({"fault":site,"pid":os.getpid()})+"\n")
        f.flush()
        os.fsync(f.fileno())
    os._exit(91)


def claim(sender,owner,lease_seconds=0.8,tenant=None,offset=0):
    clock=clock_gate(sender,offset)
    if not clock["permitted"]:
        return {"status":"BLOCK: clock_skew","skew_abs_ms":clock["skew_abs_ms"]}
    task=p08.claim(sender,owner,lease_seconds,tenant)
    return task or {"status":"NO_PENDING"}


def hash_event(prev,event,tenant,key,payload_hash):
    s="v1|"+prev+"|"+event+"|"+tenant+"|"+key+"|"+payload_hash
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def append_audit(auditor,tenant,key,payload,event):
    if event not in EVENTS:raise ValueError("unsupported synthetic event")
    payload_hash=hashlib.sha256(payload.encode("utf-8")).hexdigest()
    with p08.connect(auditor) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            old=db.execute("""SELECT event,payload_sha256 FROM p11_audit_events
                              WHERE tenant=? AND idem=?""",(tenant,key)).fetchone()
            if old:
                db.commit()
                return {"status":"ALREADY: audit_recorded" if old[1]==payload_hash else
                        "BLOCK: audit_payload_conflict"}
            prev=db.execute("SELECT row_sha256 FROM p11_audit_events ORDER BY seq DESC LIMIT 1").fetchone()
            previous=prev[0] if prev else GENESIS
            h=hash_event(previous,event,tenant,key,payload_hash)
            db.execute("""INSERT INTO p11_audit_events
               (tenant,idem,event,payload_sha256,prev_sha256,row_sha256)
               VALUES (?,?,?,?,?,?)""",(tenant,key,event,payload_hash,previous,h))
            db.commit()
            return {"status":"RECORDED","event":event}
        except Exception:
            db.rollback()
            raise


def process(sender,receiver,auditor,tenant,key,owner,token,fault=None,offset=0):
    for n,v in (("tenant",tenant),("key",key),("owner",owner),("token",token)):
        p08.check_id(v,n)
    clock=clock_gate(sender,offset)
    if not clock["permitted"]:
        return {"status":"BLOCK: clock_skew"}
    if not p08.lease_valid(sender,tenant,key,owner,token):
        return {"status":"BLOCK: stale_or_missing_claim"}
    original=source_row(sender,tenant,key)
    if not original or original["delivered"]:
        return {"status":"BLOCK: source_missing_or_already_delivered"}
    payload=original["payload"]
    with p08.connect(receiver) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            old=db.execute("SELECT payload FROM p08_inbox WHERE tenant=? AND idem=?",
                           (tenant,key)).fetchone()
            if old and old[0]!=payload:
                db.rollback()
                return {"status":"BLOCK: receipt_payload_conflict"}
            inserted=0
            if not old:
                inserted=db.execute("INSERT OR IGNORE INTO p08_inbox VALUES(?,?,?)",
                                    (tenant,key,payload)).rowcount
            if fault=="receiver_before_commit":
                crash(sender,fault)
            db.commit()
        except Exception:
            db.rollback()
            raise
    if fault=="receiver_after_commit":
        crash(sender,fault)
    ack=p08.ack(sender,tenant,key,owner,token)
    if ack["status"]!="ACKED":
        return {"status":ack["status"],"receiver_inserted":inserted,
                "receiver_committed":True,"source_ack":False}
    if fault=="sender_after_ack":
        crash(sender,fault)
    evidence=append_audit(auditor,tenant,key,payload,"ACK_OBSERVED")
    return {"status":"DONE" if evidence["status"] in ("RECORDED","ALREADY: audit_recorded")
            else "BLOCK: audit_conflict","receiver_inserted":inserted,
            "receiver_committed":True,"source_ack":True,"audit":evidence["status"]}


def repair_audit(sender,receiver,auditor):
    # Audit-gap recovery never invents a receiver receipt and never changes the
    # source ACK. It adds a separately labelled corroborated observation only.
    with base.connect(sender) as db:
        rows=db.execute("SELECT tenant,idem FROM p07_outbox WHERE delivered=1 ORDER BY tenant,idem").fetchall()
    actions=[]
    with p08.connect(receiver) as db:
        receipts={(t,k):p for t,k,p in db.execute("SELECT tenant,idem,payload FROM p08_inbox")}
    for tenant,key in rows:
        source=source_row(sender,tenant,key)
        if not source or source["delivered"]!=1 or receipts.get((tenant,key))!=source["payload"]:
            actions.append({"tenant":tenant,"key":key,"status":"BLOCK: uncorroborated_ack"})
            continue
        record=append_audit(auditor,tenant,key,source["payload"],"RECONCILED_ACK")
        actions.append({"tenant":tenant,"key":key,**record})
    return {"actions":actions,"synthetic_observation_only":True}


def inspect(sender,receiver,auditor):
    with base.connect(sender) as db:
        effect={(t,k):(thread,p) for t,k,thread,p in db.execute(
            "SELECT tenant,idem,thread,payload FROM p07_effects")}
        out={(t,k):(p,d) for t,k,p,d in db.execute(
            "SELECT tenant,idem,payload,delivered FROM p07_outbox")}
        origin={(t,k):thread for t,k,thread in db.execute(
            "SELECT tenant,idem,thread FROM p07_audit")}
    with p08.connect(receiver) as db:
        receipts={(t,k):p for t,k,p in db.execute("SELECT tenant,idem,payload FROM p08_inbox")}
    with p08.connect(auditor) as db:
        events=db.execute("""SELECT seq,tenant,idem,event,payload_sha256,
                                   prev_sha256,row_sha256
                            FROM p11_audit_events ORDER BY seq""").fetchall()
    prev=GENESIS; chain_ok=True; indexed={}
    for idx,(seq,t,k,event,ph,previous,rowhash) in enumerate(events,1):
        # The sequential index check also detects missing interior rows.
        good=seq==idx and event in EVENTS and previous==prev and              rowhash==hash_event(prev,event,t,k,ph)
        if not good:chain_ok=False
        prev=rowhash
        indexed[(t,k)]=(event,ph)
    source_mismatch=[]
    receipt_orphans=[]
    ack_without_receipt=[]
    ack_without_audit=[]
    receipt_before_ack=[]
    audit_invalid=[]
    for pair,(payload,ack) in out.items():
        t,k=pair
        if not p08.strict_payload(t,k,payload) or effect.get(pair,(None,None))[1]!=payload or pair not in origin:
            source_mismatch.append(pair)
        receipt=receipts.get(pair)
        if ack and receipt!=payload:ack_without_receipt.append(pair)
        if receipt==payload and not ack:receipt_before_ack.append(pair)
        if ack and pair not in indexed:ack_without_audit.append(pair)
        if pair in indexed:
            _,ph=indexed[pair]
            if ph!=hashlib.sha256(payload.encode("utf-8")).hexdigest() or not ack:
                audit_invalid.append(pair)
    receipt_orphans=[pair for pair in receipts if pair not in out]
    for pair in indexed:
        if pair not in out:audit_invalid.append(pair)
    consistent=(chain_ok and not source_mismatch and not receipt_orphans
                and not ack_without_receipt and not ack_without_audit and
                not receipt_before_ack and not audit_invalid
                and len(out)==len(effect)==len(origin))
    return {"source_count":len(out),"source_acked":sum(v[1] for v in out.values()),
            "receiver_unique":len(receipts),"auditor_events":len(events),
            "audit_chain_ok":chain_ok,
            "source_mismatch":len(source_mismatch),
            "ack_without_receipt":len(ack_without_receipt),
            "ack_without_audit":len(ack_without_audit),
            "receipt_before_ack":len(receipt_before_ack),
            "receipt_orphans":len(receipt_orphans),
            "audit_invalid":len(audit_invalid),
            "crossdb_consistency_observed":consistent,
            "distributed_atomicity_proved":False,
            "external_audit_anchor":False,
            "real_orders":0,"real_model_calls":0}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--sender",type=Path,required=True)
    ap.add_argument("--receiver",type=Path,required=True)
    ap.add_argument("--auditor",type=Path,required=True)
    ap.add_argument("--stage",choices=("claim","process","repair","inspect"),required=True)
    ap.add_argument("--tenant")
    ap.add_argument("--key")
    ap.add_argument("--owner",default="synthetic-worker")
    ap.add_argument("--token")
    ap.add_argument("--lease-seconds",type=float,default=0.8)
    ap.add_argument("--clock-offset",type=float,default=0)
    ap.add_argument("--fault",choices=FAULTS)
    a=ap.parse_args()
    setup(a.sender,a.receiver,a.auditor)
    if a.stage=="claim":
        result=claim(a.sender,a.owner,a.lease_seconds,a.tenant,a.clock_offset)
    elif a.stage=="process":
        result=process(a.sender,a.receiver,a.auditor,
                       a.tenant,a.key,a.owner,a.token,a.fault,a.clock_offset)
    elif a.stage=="repair":
        result=repair_audit(a.sender,a.receiver,a.auditor)
    else:result=inspect(a.sender,a.receiver,a.auditor)
    print(json.dumps(result,sort_keys=True,ensure_ascii=False),flush=True)


if __name__=="__main__":
    main()
