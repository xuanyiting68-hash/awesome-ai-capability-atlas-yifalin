#!/usr/bin/env python3
"""V1.7.6 reproducible *synthetic* evaluation and independent review gate.

No real-user labels are supplied. Unit tests must never be presented as field accuracy.
A future hold-out may be ingested ONLY after external attestation/consent checking;
this module intentionally cannot authorize product release or promote source records.
"""
from __future__ import annotations
from collections import defaultdict
import json
from pathlib import Path
from rag_retrieval_v175 import load_reference_data, retrieve
from provider_contract_v174 import ContractError

ROOT=Path(__file__).resolve().parent

def evaluate_synthetic(cases: list[dict], records: list[dict], topics: list[dict], k: int=8) -> dict:
    if type(k) is not int or not 1 <= k <= 8: raise ContractError("Only bounded recall-at-K supported")
    if not isinstance(cases,list) or not 1 <= len(cases) <= 200: raise ContractError("Invalid synthetic corpus")
    ids=set()
    by_sector=defaultdict(lambda: {"positive":0,"hit":0,"negative":0,"abstained":0})
    stats={"positive":0,"hit":0,"negative":0,"abstained":0}
    examples=[]
    for c in cases:
        if not isinstance(c,dict) or not isinstance(c.get("id"),str) or c["id"] in ids:
            raise ContractError("Duplicate/malformed evaluation ID")
        ids.add(c["id"])
        if not isinstance(c.get("expected_any"),list) or any(not isinstance(s,str) for s in c["expected_any"]):
            raise ContractError("Expected targets malformed")
        no_evidence = c.get("expect_empty") is True
        if no_evidence and c["expected_any"] or not no_evidence and not c["expected_any"]:
            raise ContractError("Positive/negative classification ambiguous")
        hits=retrieve(c["task"],c["sector_id"],records,topics,k)
        names={x.title.casefold() for x in hits}
        target={x.casefold() for x in c["expected_any"]}
        if no_evidence:
            stats["negative"]+=1; by_sector[c["sector_id"]]["negative"]+=1
            ok=not hits
            if ok:
                stats["abstained"]+=1;by_sector[c["sector_id"]]["abstained"]+=1
        else:
            stats["positive"]+=1;by_sector[c["sector_id"]]["positive"]+=1
            ok=bool(names&target)
            if ok:
                stats["hit"]+=1;by_sector[c["sector_id"]]["hit"]+=1
        examples.append({"case_id":c["id"],"sector_id":c["sector_id"],"case_type":"negative" if no_evidence else "positive",
                         "passed":ok,"returned_source_names":sorted(names),"expected_any":sorted(target)})
    return {
        "schema_version":"1.0","test_population":"synthetic-editorial",
        "cases":len(examples),"hit_at_k":k,"hit_fraction":f'{stats["hit"]}/{stats["positive"]}',
        "abstention_fraction":f'{stats["abstained"]}/{stats["negative"]}',
        "by_sector":dict(sorted(by_sector.items())),"examples":examples,
        "false_claims_prohibited":True,"field_precision":None,"field_recall":None,
        "independent_human_reviewed":False,"release_gate":"HOLD",
        "warning":"Synthetic expected_any matches measure smoke-test hit@K only. Not independent human relevance, precision@K, live source quality or production safety."
    }

REVIEW_SCHEMA_VERSION="1.0"
def validate_review_packet(packet: dict) -> dict:
    """Checks only self-declared review packet structure; no identity authentication."""
    if not isinstance(packet,dict) or packet.get("schema_version")!=REVIEW_SCHEMA_VERSION:
        raise ContractError("Unknown evaluation packet")
    if packet.get("source_population")!="real-user-consented-anonymized":
        raise ContractError("Synthetic or unconsented corpus cannot claim external evaluation")
    rows=packet.get("cases")
    if not isinstance(rows,list) or not 25<=len(rows)<=500:
        raise ContractError("Insufficient bounded review cases")
    seen=set(); sectors=set(); positives=negatives=0
    for row in rows:
        if not isinstance(row,dict):raise ContractError("Invalid case")
        if not isinstance(row.get("id"),str) or not row["id"] or row["id"] in seen:
            raise ContractError("Duplicate review case")
        seen.add(row["id"])
        if not isinstance(row.get("sector_id"),str) or not row["sector_id"].startswith("s"):
            raise ContractError("Invalid sector")
        if row.get("consent_recorded") is not True or row.get("pii_removed") is not True:
            raise ContractError("Consent/redaction not attested")
        if row.get("reviewer_a") in (None,"") or row.get("reviewer_b") in (None,"") or row.get("reviewer_a")==row.get("reviewer_b"):
            raise ContractError("Two distinct reviewer attestations required")
        if row.get("adjudicated") is not True or row.get("evidence_link_checked") is not True:
            raise ContractError("Unadjudicated / unverified evidence case")
        if row.get("is_negative") is True:negatives+=1
        elif row.get("is_negative") is False:positives+=1
        else:raise ContractError("Unknown negative status")
        sectors.add(row["sector_id"])
    return {
        "schema_validation":"self-declared-only",
        "cases":len(rows),"sectors":len(sectors),
        "positives":positives,"negatives":negatives,
        "independent_identity_verification":False,
        "independent_link_audit":False,
        "authenticity_proven":False,
        "release_gate":"HOLD",
        "reason":"The packet is structurally valid but human identity, consent and source facts require separate independent verification."
    }

def main():
    records,topics=load_reference_data()
    cases=json.loads((ROOT/"rag_eval_cases_v175.json").read_text(encoding="utf-8"))["cases"]
    res=evaluate_synthetic(cases,records,topics,k=8)
    print(json.dumps({k:res[k] for k in ("cases","hit_fraction","abstention_fraction","release_gate")},ensure_ascii=False))
    assert res["release_gate"]=="HOLD" and res["independent_human_reviewed"] is False

if __name__=="__main__":
    main()
