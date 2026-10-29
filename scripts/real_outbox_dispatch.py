#!/usr/bin/env python3
"""Pilot 08: bounded SQLite outbox dispatcher and separate SQLite inbox.

No external network, broker, LLM, real credentials or customer data.
Separate producer and recipient DB transactions deliberately expose the
unavoidable ACK gap. A unique recipient inbox key absorbs duplicate sends.
This does NOT establish end-to-end exactly-once delivery or real auth.
"""
import argparse
import json
import os
import re
import sqlite3
import time
import uuid
from pathlib import Path

VALID = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
FAULTS = ("before_receiver_commit", "after_receiver_commit")


def connect(path):
    conn=sqlite3.connect(str(path), timeout=4.0, isolation_level=None)
    conn.execute("PRAGMA busy_timeout=4000")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def setup(sender, recipient):
    sender=Path(sender); recipient=Path(recipient)
    sender.parent.mkdir(parents=True, exist_ok=True)
    recipient.parent.mkdir(parents=True, exist_ok=True)
    with connect(sender) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS p08_leases(
          tenant TEXT NOT NULL, idem TEXT NOT NULL, owner TEXT NOT NULL,
          token TEXT NOT NULL, lease_until REAL NOT NULL, attempts INTEGER NOT NULL,
          PRIMARY KEY(tenant,idem))""")
    with connect(recipient) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS p08_inbox(
          tenant TEXT NOT NULL, idem TEXT NOT NULL, payload TEXT NOT NULL,
          PRIMARY KEY(tenant,idem))""")


def check_id(value, name):
    if not isinstance(value, str) or not VALID.fullmatch(value):
        raise ValueError("invalid synthetic "+name)
    return value


def strict_payload(tenant, key, payload):
    try:
        data=json.loads(payload)
    except (ValueError, TypeError):
        return False
    return (isinstance(data,dict)
            and data=={"kind":"synthetic_draft",
                       "tenant":tenant,"idempotency_key":key})


def claim(sender, owner, lease_seconds=2.0, tenant=None):
    check_id(owner,"owner")
    if tenant is not None:check_id(tenant,"tenant")
    if not 0.2 <= lease_seconds <= 120:
        raise ValueError("lease out of research bounds")
    now=time.time()
    with connect(sender) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            row=db.execute("""SELECT o.tenant,o.idem,o.payload,e.payload,a.idem
               FROM p07_outbox o LEFT JOIN p08_leases l
               ON o.tenant=l.tenant AND o.idem=l.idem
               LEFT JOIN p07_effects e ON o.tenant=e.tenant AND o.idem=e.idem
               LEFT JOIN p07_audit a ON o.tenant=a.tenant AND o.idem=a.idem
               WHERE o.delivered=0 AND (l.token IS NULL OR l.lease_until <= ?)
               AND (? IS NULL OR o.tenant=?)
               ORDER BY o.tenant,o.idem LIMIT 1""",(now,tenant,tenant)).fetchone()
            if row is None:
                db.commit()
                return None
            t,k,payload,effect_payload,audit_key=row
            check_id(t,"tenant");check_id(k,"idempotency key")
            # Fail closed if the atomic Pilot 07 source evidence is incomplete.
            # A crafted but syntactically valid outbox record is not sufficient.
            if not strict_payload(t,k,payload):
                db.commit()
                return {"status":"BLOCK: invalid_payload","tenant":t,"key":k}
            if effect_payload!=payload or audit_key is None:
                db.commit()
                return {"status":"BLOCK: missing_source_provenance","tenant":t,"key":k}
            token=uuid.uuid4().hex
            db.execute("""INSERT INTO p08_leases(tenant,idem,owner,token,lease_until,attempts)
                VALUES (?,?,?,?,?,1) ON CONFLICT(tenant,idem) DO UPDATE SET
                owner=excluded.owner,token=excluded.token,
                lease_until=excluded.lease_until,attempts=p08_leases.attempts+1""",
                (t,k,owner,token,now+lease_seconds))
            attempts=db.execute("SELECT attempts FROM p08_leases WHERE tenant=? AND idem=?",
                                (t,k)).fetchone()[0]
            db.commit()
            return {"status":"CLAIMED","tenant":t,"key":k,"payload":payload,
                    "token":token,"owner":owner,"attempts":attempts}
        except Exception:
            db.rollback()
            raise


def lease_valid(sender, tenant, key, owner, token):
    with connect(sender) as db:
        item=db.execute("""SELECT l.token,l.owner,l.lease_until,o.payload,o.delivered
           FROM p08_leases l JOIN p07_outbox o ON l.tenant=o.tenant AND l.idem=o.idem
           WHERE l.tenant=? AND l.idem=?""",(tenant,key)).fetchone()
    return bool(item and item[0]==token and item[1]==owner and
                item[2]>time.time() and item[4]==0 and
                strict_payload(tenant,key,item[3]))


def ack(sender, tenant, key, owner, token):
    # Fenced ACK: a stale worker cannot mark a newer owner's claim delivered.
    with connect(sender) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            item=db.execute("""SELECT l.token,l.owner,l.lease_until,o.delivered
              FROM p08_leases l JOIN p07_outbox o ON l.tenant=o.tenant AND l.idem=o.idem
              WHERE l.tenant=? AND l.idem=?""",(tenant,key)).fetchone()
            if (item is None or item[0]!=token or item[1]!=owner or
                    item[2]<=time.time() or item[3]!=0):
                db.commit()
                return {"status":"BLOCK: stale_or_missing_claim"}
            db.execute("UPDATE p07_outbox SET delivered=1 WHERE tenant=? AND idem=?",
                       (tenant,key))
            db.commit()
            return {"status":"ACKED"}
        except Exception:
            db.rollback()
            raise


def crash(sender, place):
    marker=Path(sender).with_suffix(".p08faults.jsonl")
    with open(marker,"a",encoding="utf-8") as file:
        file.write(json.dumps({"fault":place,"pid":os.getpid()})+"\n")
        file.flush()
        os.fsync(file.fileno())
    os._exit(87)


def deliver(sender, recipient, tenant, key, owner, token, fault=None):
    for n,v in (("tenant",tenant),("key",key),("owner",owner),("token",token)):
        check_id(v,n)
    if not lease_valid(sender,tenant,key,owner,token):
        return {"status":"BLOCK: stale_or_missing_claim"}
    with connect(sender) as db:
        payload=db.execute("SELECT payload FROM p07_outbox WHERE tenant=? AND idem=?",
                           (tenant,key)).fetchone()[0]
    if not strict_payload(tenant,key,payload):
        return {"status":"BLOCK: invalid_payload"}
    with connect(recipient) as db:
        db.execute("BEGIN IMMEDIATE")
        try:
            prior=db.execute("SELECT payload FROM p08_inbox WHERE tenant=? AND idem=?",
                             (tenant,key)).fetchone()
            if prior and prior[0]!=payload:
                db.rollback()
                return {"status":"BLOCK: mismatched_inbox_payload"}
            inserted=0
            if prior is None:
                inserted=db.execute("""INSERT OR IGNORE INTO p08_inbox(tenant,idem,payload)
                   VALUES(?,?,?)""",(tenant,key,payload)).rowcount
            if fault=="before_receiver_commit":
                crash(sender,fault)
            db.commit()
        except Exception:
            db.rollback()
            raise
    if fault=="after_receiver_commit":
        crash(sender,fault)
    acked=ack(sender,tenant,key,owner,token)
    return {"status":acked["status"],"recipient_inserted":inserted,
            "recipient_duplicate":bool(prior),"local_only":True}


def dispatch(sender, recipient, owner, lease_seconds=2.0, tenant=None, fault=None):
    task=claim(sender,owner,lease_seconds,tenant)
    if not task: return {"status":"NO_PENDING"}
    if task["status"]!="CLAIMED":return task
    result=deliver(sender,recipient,task["tenant"],task["key"],owner,task["token"],fault)
    return {"tenant":task["tenant"],"key":task["key"],"attempt":task["attempts"],**result}


def reconcile(sender, recipient):
    with connect(sender) as db:
        out=db.execute("SELECT tenant,idem,payload,delivered FROM p07_outbox").fetchall()
        effects=db.execute("SELECT tenant,idem,payload FROM p07_effects").fetchall()
        audit=db.execute("SELECT tenant,idem FROM p07_audit").fetchall()
        attempts=db.execute("SELECT tenant,idem,attempts FROM p08_leases").fetchall()
    with connect(recipient) as db:
        inbox=db.execute("SELECT tenant,idem,payload FROM p08_inbox").fetchall()
    receiver={(r[0],r[1]):r[2] for r in inbox}
    sent={(r[0],r[1]):(r[2],r[3]) for r in out}
    effect_map={(t,k):payload for t,k,payload in effects}
    audit_set=set(audit)
    source_mismatch=sum(bool(effect_map.get((t,k))!=payload or (t,k) not in audit_set
                             or not strict_payload(t,k,payload))
                        for t,k,payload,_ in out)
    source_orphans=sum((t,k) not in sent for t,k,_ in effects)
    source_audit_orphans=sum(pair not in sent for pair in audit_set)
    acknowledged_missing=sum(bool(delivered and receiver.get((t,k))!=payload)
                             for t,k,payload,delivered in out)
    pending_ack=sum(bool(not delivered and receiver.get((t,k))==payload)
                    for t,k,payload,delivered in out)
    payload_mismatch=sum(bool((t,k) in receiver and receiver[(t,k)]!=payload)
                         for t,k,payload,_ in out)
    receiver_orphans=sum((t,k) not in sent for t,k,_ in inbox)
    return {"source_outbox":len(out),"source_acked":sum(row[3] for row in out),
            "inbox_unique":len(inbox),"attempts_total":sum(row[2] for row in attempts),
            "acknowledged_missing":acknowledged_missing,"pending_ack":pending_ack,
            "payload_mismatch":payload_mismatch,"receiver_orphans":receiver_orphans,
            "source_mismatch":source_mismatch,"source_orphans":source_orphans,
            "source_audit_orphans":source_audit_orphans,
            "consistent":not (acknowledged_missing or payload_mismatch or receiver_orphans
                              or source_mismatch or source_orphans or source_audit_orphans),
            "local_recipient_only":True,"real_external_delivery":False,
            "exactly_once_external_claim":False,"pid":os.getpid()}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--sender",type=Path,required=True)
    parser.add_argument("--recipient",type=Path,required=True)
    parser.add_argument("--stage",choices=("claim","deliver","dispatch","ack","reconcile"),
                        required=True)
    parser.add_argument("--tenant")
    parser.add_argument("--key")
    parser.add_argument("--owner",default="synthetic-worker")
    parser.add_argument("--token")
    parser.add_argument("--lease-seconds",type=float,default=2.0)
    parser.add_argument("--fault",choices=FAULTS)
    args=parser.parse_args()
    setup(args.sender,args.recipient)
    if args.stage=="claim":
        result=claim(args.sender,args.owner,args.lease_seconds,args.tenant) or {"status":"NO_PENDING"}
    elif args.stage=="deliver":
        result=deliver(args.sender,args.recipient,args.tenant,args.key,args.owner,args.token,
                       args.fault)
    elif args.stage=="ack":
        result=ack(args.sender,args.tenant,args.key,args.owner,args.token)
    elif args.stage=="dispatch":
        result=dispatch(args.sender,args.recipient,args.owner,args.lease_seconds,args.tenant,
                        args.fault)
    else:
        result=reconcile(args.sender,args.recipient)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
