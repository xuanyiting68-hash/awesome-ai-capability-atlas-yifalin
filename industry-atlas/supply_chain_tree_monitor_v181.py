#!/usr/bin/env python3
"""V1.8.1 bounded tree SHA observation drift check, no SBOM/CVE assertions.

On scheduled/manual events only, ten immutable GitHub tree endpoints are read.
A changed tree is a HUMAN REVIEW signal, not a vulnerability finding, source
deletion, license approval or product promotion.
"""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote
import argparse,json,os
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from supply_chain_review_v181 import validate_supply_chain
from source_monitor_v180 import fetch_metadata

ROOT=Path(__file__).resolve().parent
def monitor_trees(supply,leads,licenses,snap,atlas,rules, *,
                  as_of,mode="offline",ack=False,fetcher=fetch_metadata):
    rows=validate_supply_chain(supply,leads,licenses,snap,atlas,rules)
    try:
        dt=datetime.fromisoformat(as_of.replace("Z","+00:00"))
        if not dt.tzinfo or dt.utcoffset()!=timezone.utc.utcoffset(dt):
            raise ValueError("Must be UTC")
    except ValueError:
        raise ContractError("as_of timestamp must be UTC") from None
    if dt.date()<datetime.fromisoformat(supply["observed_on"]+"T00:00:00+00:00").date():
        raise ContractError("Cannot compare to pre-baseline date")
    if mode not in ("offline","live") or (mode=="live" and not ack):
        raise ContractError("Live requires explicit approval flag")
    report=[]
    for r in rows:
        status="not-checked";reason=None
        if mode=="live":
            endpoint="https://api.github.com/repos/"+r["repo_full_name"]+"/git/trees/"+quote(r["observed_branch"],safe="")
            observed=fetcher(endpoint,os.environ.get('GITHUB_TOKEN') if mode=='live' else None)
            if observed.get("kind")!="ok":
                status="unavailable-not-deleted";reason="network-or-api-limitation"
            else:
                tree=observed.get("data",{})
                sha=tree.get("sha")
                if not isinstance(sha,str) or len(sha)!=40 or any(k not in "0123456789abcdef" for k in sha):
                    status="invalid-tree-metadata";reason="malformed-git-tree"
                elif sha==r["git_tree_sha"]:
                    status="tree-unchanged-not-supply-chain-safe"
                else:
                    status="tree-changed-review-required";reason="git-tree-sha-drift"
        report.append({
            "id":r["id"],"repo":r["repo_full_name"],"baseline_tree_sha":r["git_tree_sha"],
            "observation_status":status,"review_reason":reason,
            "source_deleted_verified":False,"sbom_verified":False,
            "vulnerability_status":"not-checked","automatic_approval":False
        })
    return {"schema_version":"1.0","report_type":"github-root-tree-drift-review",
            "mode":mode,"as_of":as_of,"projects":10,
            "max_external_requests":10,"requests_attempted":10 if mode=="live" else 0,
            "tree_drift_count":sum(r["observation_status"]=="tree-changed-review-required" for r in report),
            "sboms_verified":0,"security_checks_passed":0,"auto_promoted":0,
            "catalog_writes":0,"release_gate":"HOLD","rows":report,
            "warning":"Only Git root tree SHA is checked. A change is not a vulnerability; no change is not proof of safety or latest license correctness."}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--mode",choices=("offline","live"),default="offline")
    ap.add_argument("--ack-read-only-live",action="store_true")
    ap.add_argument("--as-of",required=True)
    ap.add_argument("--output",required=True,type=Path)
    args=ap.parse_args()
    snap,atlas,rules=load_data()
    leads=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
    licenses=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
    supply=json.loads((ROOT/"supply_chain_evidence_v181.json").read_text(encoding="utf-8"))
    report=monitor_trees(supply,leads,licenses,snap,atlas,rules,as_of=args.as_of,
                         mode=args.mode,ack=args.ack_read_only_live)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PASS V1.8.1 {args.mode} tree monitor: {report['projects']} repos, {report['requests_attempted']} requests, 0 approvals")
if __name__=="__main__":
    main()
