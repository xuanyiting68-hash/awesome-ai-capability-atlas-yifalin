#!/usr/bin/env python3
"""V1.8.0 review-only file-level license provenance and reconciliation ledger.

No legal opinion, no GPL compatibility inference, no dependency/audit claims.
The contents merely record that a GitHub repository file was read on the
specified date and its blob SHA/content cue was observed.
"""
from __future__ import annotations
from collections import Counter
from datetime import date
import argparse
import json
import re
from pathlib import Path
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from external_leads_v179 import validate_ledger

ROOT=Path(__file__).resolve().parent
KNOWN_STATUS={"metadata-aligned-text-cue","license-signal-needs-reconciliation"}
RECONCILE={"github:ifcopenshell/ifcopenshell","github:opentripplanner/opentripplanner"}

def validate_license_files(files:dict, leads:dict, snapshot:dict, atlas:dict, rules:dict)->dict:
    validate_ledger(leads,snapshot,atlas,rules)
    if not isinstance(files,dict) or files.get("schema_version")!="1.0" or files.get("population")!="read-only-public-repository-license-file-observations":
        raise ContractError("Wrong license-file evidence population")
    if files.get("observation_precision")!="date-only" or files.get("observation_date")!=leads.get("observation_date"):
        raise ContractError("License observation provenance date mismatch")
    if files.get("files_observed")!=10 or any(files.get(key)!=0 for key in (
        "independently_legal_verified","dependency_license_audits","security_audits","approved_catalog_entries")):
        raise ContractError("File counts, certification or approval claims invalid")
    recs=files.get("records")
    if not isinstance(recs,list) or len(recs)!=10:
        raise ContractError("Expected 10 exact observed files")
    lead_by={x["id"]:x for x in leads["records"]}
    seen={}
    for r in recs:
        if not isinstance(r,dict) or r.get("id") in seen or r.get("id") not in lead_by:
            raise ContractError("Duplicate, missing or extraneous license source")
        lead=lead_by[r["id"]]
        if r.get("repo_full_name")!=lead["repo_full_name"] or r.get("repo_url")!=lead["repo_url"] or r.get("observed_branch")!=lead["observed_metadata"]["default_branch"]:
            raise ContractError("License file not tied to observed repository and branch")
        path=r.get("license_file_path")
        if path not in ("LICENSE","LICENSE.txt","LICENSE.md","COPYING","COPYING.txt"):
            raise ContractError("Invalid or ambiguous license evidence path")
        expected=r["repo_url"]+"/blob/"+r["observed_branch"]+"/"+path
        if r.get("license_file_url")!=expected:
            raise ContractError("Unanchored license-file URL")
        if not isinstance(r.get("license_blob_sha"),str) or re.fullmatch("[a-f0-9]{40}",r["license_blob_sha"]) is None:
            raise ContractError("Blob SHA must be canonical Git SHA1")
        if not isinstance(r.get("textual_cue"),str) or not 10<=len(r["textual_cue"])<=250:
            raise ContractError("Missing bounded editorial text signal")
        if r.get("signal_reconciliation_status") not in KNOWN_STATUS:
            raise ContractError("Invalid signal discrepancy state")
        if (r["id"] in RECONCILE)!=(r["signal_reconciliation_status"]=="license-signal-needs-reconciliation"):
            raise ContractError("Required discrepancy cannot be silently waived")
        if any(r.get(k) is not False for k in ("legal_license_verified","dependency_audit_verified",
             "security_review_verified","independent_review_approved","source_promoted")):
            raise ContractError("Cannot turn file evidence into legal/security/catalog approval")
        seen[r["id"]]=r
    if set(seen)!=set(lead_by):
        raise ContractError("License source not fully aligned to observed leads")
    return {"records":[seen[k] for k in sorted(seen)],"observation_date":files["observation_date"]}

def build_license_report(files:dict,leads:dict,snapshot:dict,atlas:dict,rules:dict)->dict:
    check=validate_license_files(files,leads,snapshot,atlas,rules)
    lead_by={x["id"]:x for x in leads["records"]}
    rows=[]
    for f in check["records"]:
        lead=lead_by[f["id"]]
        rows.append({
            "id":f["id"],"name":f["repo_full_name"],"sector_id":lead["sector_id"],
            "observation_date":check["observation_date"],
            "repo_metadata_spdx_signal":lead["observed_metadata"]["license_spdx_signal"],
            "license_file_url":f["license_file_url"],"license_file_path":f["license_file_path"],
            "license_blob_sha":f["license_blob_sha"],"textual_cue":f["textual_cue"],
            "reconciliation_status":f["signal_reconciliation_status"],
            "file_was_read":True,"license_legally_verified":False,"dependencies_audited":False,
            "security_audited":False,"source_approved":False,"current_file_verified":False,
            "review_required":True
        })
    counts=Counter(r["reconciliation_status"] for r in rows)
    return {
        "schema_version":"1.0","report_type":"license-file-evidence-review",
        "observation_date":check["observation_date"],
        "files_observed":len(rows),"needs_signal_reconciliation":counts["license-signal-needs-reconciliation"],
        "text_cue_aligned":counts["metadata-aligned-text-cue"],
        "legal_licenses_verified":0,"dependencies_audited":0,"security_audited":0,
        "approved_sources":0,"network_requests":0,"release_gate":"HOLD",
        "rows":rows,
        "warning":"All 10 file paths/SHAs are snapshot evidence only. Even matching headings/SPDX signals do NOT establish actual legal licensing, dependency compliance, safety or commercial permissions."
    }

def compare_license_reports(previous:dict,current:dict)->dict:
    if any(not isinstance(x,dict) or x.get("report_type")!="license-file-evidence-review"
           or x.get("approved_sources")!=0 or x.get("legal_licenses_verified")!=0
           for x in (previous,current)):
        raise ContractError("Reports are not comparable unapproved license observations")
    if date.fromisoformat(current["observation_date"])<date.fromisoformat(previous["observation_date"]):
        raise ContractError("Reverse observation date")
    left={x["id"]:x for x in previous["rows"]}
    right={x["id"]:x for x in current["rows"]}
    events=[]
    for identity in sorted(set(left)|set(right)):
        a=left.get(identity);b=right.get(identity)
        if a is None: state="new-file-observation"
        elif b is None: state="not-in-current-sample-not-deletion"
        elif a.get("license_blob_sha")!=b.get("license_blob_sha"): state="license-file-blob-changed-review-required"
        elif a.get("repo_metadata_spdx_signal")!=b.get("repo_metadata_spdx_signal"): state="repository-spdx-signal-changed-review-required"
        else: state="file-observation-unchanged"
        events.append({"id":identity,"state":state,"verified_deletion":False,
                       "licence_conclusion":None,"automatic_approval":False})
    return {"report_type":"license-file-delta-review-only","events":events,
            "counts":dict(sorted(Counter(x["state"] for x in events).items())),
            "auto_promoted":False,"legal_validation_performed":False}

def main(argv=None)->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args(argv)
    snapshot,atlas,rules=load_data()
    leads=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
    files=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
    report=build_license_report(files,leads,snapshot,atlas,rules)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS V1.8.0 license evidence: 10 observed files, 2 reconciliation flags, 0 legal/security approvals")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
