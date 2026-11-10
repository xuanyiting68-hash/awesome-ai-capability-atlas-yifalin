#!/usr/bin/env python3
"""V1.7.9 review-only GitHub repository evidence ledger.

This is a locked *observation* of metadata from documented public GitHub API
calls, not a network validator, security scanner, licence lawyer, verified vendor
registry or production inventory. It MUST NOT alter the frozen radar or Atlas.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from hashlib import sha256
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data, generate_review

ROOT=Path(__file__).resolve().parent
API_HOST="api.github.com"
SOURCE_HOST="github.com"
EXPECTED=10
STATUS="research-lead-unapproved"

def _date(s: str) -> date:
    if not isinstance(s,str):
        raise ContractError("Missing date")
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise ContractError("Invalid ISO date") from None

def parse_stamp(stamp: str) -> date:
    if not isinstance(stamp,str) or not stamp.endswith("Z"):
        raise ContractError("Unverifiable timestamp format")
    try:
        return datetime.fromisoformat(stamp[:-1]+"+00:00").date()
    except ValueError:
        raise ContractError("Invalid repository timestamp") from None

def check_url(value: str, host: str) -> str:
    if not isinstance(value,str):
        raise ContractError("Invalid source URL")
    p=urlsplit(value)
    if p.scheme!="https" or p.hostname!=host or p.port is not None or p.username or p.password or p.query or p.fragment:
        raise ContractError("Source URL must be canonical HTTPS to expected host")
    if p.path.endswith("/") or "//" in p.path or not p.path:
        raise ContractError("Ambiguous repository path")
    return p.path

def validate_ledger(data: dict, snapshot: dict, atlas: dict, rules: dict) -> dict:
    if not isinstance(data,dict) or data.get("schema_version")!="1.0" or data.get("population")!="github-repository-metadata-read-only-spotcheck":
        raise ContractError("Invalid provenance population")
    day=_date(data.get("observation_date"))
    if data.get("observation_precision")!="date-only" or data.get("source_count")!=EXPECTED or data.get("provider")!="GitHub official public repository API /repos/{owner}/{repo}":
        raise ContractError("Unrecognized API observation or count")
    for field in ("approval_count","license_audit_count","security_audit_count","task_validation_count"):
        if data.get(field)!=0:raise ContractError("Unverified audit/approval claims")
    if data.get("production_catalog_modified") is not False:
        raise ContractError("Production catalog must remain unchanged")
    rows=data.get("records")
    if not isinstance(rows,list) or len(rows)!=EXPECTED:
        raise ContractError("Unexpected number of source leads")
    baseline=generate_review(snapshot,atlas,rules)
    missing={x["sector_id"] for x in baseline["sectors"] if x["coverage_state"]=="no-records"}
    known={r["url"].lower().rstrip("/") for r in snapshot["records"]}
    seen_repos, seen_ids, seen_sector=set(),set(),set()
    for row in rows:
        if not isinstance(row,dict):
            raise ContractError("Record must be a dictionary")
        full=row.get("repo_full_name")
        if not isinstance(full,str) or full.count("/")!=1 or not all(part and part not in (".","..") for part in full.split("/")):
            raise ContractError("Unexpected repository name")
        path=check_url(row.get("repo_url"),SOURCE_HOST)
        api_path=check_url(row.get("metadata_api_url"),API_HOST)
        if path!="/"+full or api_path!="/repos/"+full:
            raise ContractError("Canonical repo/API identity mismatch")
        ident="github:"+full.lower()
        if row.get("id")!=ident or ident in seen_ids:
            raise ContractError("Repo source ID mismatch or duplicate")
        if row.get("repo_id") is None or type(row.get("repo_id")) is not int or row["repo_id"]<=0 or row["repo_id"] in seen_repos:
            raise ContractError("Stable provider ID missing/duplicate")
        sector=row.get("sector_id")
        if sector not in missing or sector in seen_sector:
            raise ContractError("Lead must be a distinct uncovered sector in frozen snapshot")
        if row["repo_url"].lower().rstrip("/") in known:
            raise ContractError("Lead already in frozen radar; must not relabel")
        if row.get("review_state")!=STATUS:
            raise ContractError("Unexpected review decision")
        if any(row.get(key) is not False for key in (
            "independent_license_check","independent_safety_check",
            "task_suitability_checked","source_integrity_attested","auto_promoted")):
            raise ContractError("Cannot self-certify external repository")
        meta=row.get("observed_metadata")
        if not isinstance(meta,dict) or meta.get("public") is not True:
            raise ContractError("Must be a public repo metadata observation")
        if type(meta.get("archived")) is not bool or type(meta.get("disabled")) is not bool:
            raise ContractError("Repository archival status not known")
        if not isinstance(meta.get("license_spdx_signal"),str) or not 1<=len(meta["license_spdx_signal"])<=60:
            raise ContractError("Missing license metadata signal")
        pushed=parse_stamp(meta.get("pushed_at"))
        if pushed>day:
            raise ContractError("Future metadata timestamp relative to observation")
        if not isinstance(row.get("description"),str) or not row["description"] or len(row["description"])>800:
            raise ContractError("Description invalid")
        if not isinstance(row.get("editorial_review_cue"),str) or not 12<=len(row["editorial_review_cue"])<=300:
            raise ContractError("Missing review warning")
        if not isinstance(meta.get("default_branch"),str) or not meta["default_branch"] or len(meta["default_branch"])>100:
            raise ContractError("Missing recorded default branch")
        seen_repos.add(row["repo_id"]);seen_ids.add(ident);seen_sector.add(sector)
    return {"as_of":day.isoformat(),"rows":rows,"sector_ids":sorted(seen_sector),
            "unrepresented_sector_count":baseline["no_candidate_sectors"],
            "same_as_old_sources":False}

def make_review_report(data: dict, snapshot: dict, atlas: dict, rules: dict) -> dict:
    check=validate_ledger(data,snapshot,atlas,rules)
    entries=[]
    observed_day=_date(check["as_of"])
    for row in sorted(check["rows"],key=lambda x:x["sector_id"]):
        meta=row["observed_metadata"]
        pushed=parse_stamp(meta["pushed_at"])
        issues=["repository-metadata-only","license-file-not-reviewed","security-not-checked",
                "task-relevance-not-tested","independent-review-not-recorded"]
        if meta["license_spdx_signal"].upper() in ("NOASSERTION","UNKNOWN","NONE"):
            issues.append("github-spdx-not-asserted")
        if meta["archived"] or meta["disabled"]:
            issues.append("repository-status-review-required")
        entries.append({
            "id":row["id"],"sector_id":row["sector_id"],"name":row["repo_full_name"],
            "repo_url":row["repo_url"],"metadata_api_url":row["metadata_api_url"],
            "description":row["description"],"observation_date":check["as_of"],
            "last_pushed_date":pushed.isoformat(),
            "last_pushed_age_days_at_observation":(observed_day-pushed).days,
            "license_spdx_signal":meta["license_spdx_signal"],
            "archived_metadata_flag":meta["archived"],
            "disabled_metadata_flag":meta["disabled"],
            "review_cue":row["editorial_review_cue"],"review_status":STATUS,
            "approval":False,"license_verified":False,"security_verified":False,
            "task_verified":False,"live_available_now":None,
            "issues":issues
        })
    digest=sha256(json.dumps(entries,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")).hexdigest()
    return {
        "schema_version":"1.0","report_type":"external-source-evidence-queue",
        "population":"public-github-api-metadata-observations",
        "observation_date":check["as_of"],"snapshot_sha256":digest,
        "source_leads":len(entries),"source_gap_sectors_in_frozen_radar":check["unrepresented_sector_count"],
        "external_sector_leads":len(check["sector_ids"]),
        "frozen_radar_sources_added":0,"verified_source_count":0,
        "approved_source_count":0,"independent_license_reviews":0,
        "network_requests_during_report":0,
        "rows":entries,
        "required_checks":["publisher-and-repository-identity","real-license-and-dependency-notices",
                           "security-and-privacy","source-rights-and-terms","relevant-task-benchmark",
                           "two-person-independent-review","owner-approval-separate-PR"],
        "release_gate":"HOLD",
        "warning":"Metadata observed on a past date is NOT verified current availability, legal licensing, security, suitability or permission for catalog promotion."
    }

def compare_observations(previous: dict, current: dict) -> dict:
    """Compare valid report structures; historical differences are not security proof."""
    if any(not isinstance(d,dict) or d.get("report_type")!="external-source-evidence-queue"
           or d.get("approved_source_count")!=0 for d in (previous,current)):
        raise ContractError("Not comparable review-only reports")
    if _date(current["observation_date"])<_date(previous["observation_date"]):
        raise ContractError("Cannot compare reverse observation time")
    left={x["id"]:x for x in previous["rows"]}
    right={x["id"]:x for x in current["rows"]}
    events=[]
    for rid in sorted(set(left)|set(right)):
        a,b=left.get(rid),right.get(rid)
        kind=("new-observation" if a is None else "not-seen-in-latest-sample" if b is None
              else "metadata-changed" if any(a.get(k)!=b.get(k) for k in
                  ("last_pushed_date","license_spdx_signal","archived_metadata_flag","disabled_metadata_flag"))
              else "unchanged-repository-metadata")
        events.append({"id":rid,"kind":kind,"deletion_verified":False,"license_verified":False,
                       "approval":"unapproved"})
    return {"comparison_type":"observation-diff-only","counts":dict(sorted(Counter(x["kind"] for x in events).items())),
            "events":events,"automatic_approval":False,"deletion_verified":False}

def main(argv=None) -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args(argv)
    snapshot,atlas,rules=load_data()
    ledger=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
    result=make_review_report(ledger,snapshot,atlas,rules)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS V1.7.9: %d API metadata observation leads, %d sector gaps retained; 0 approvals, 0 network calls"%(
        result["source_leads"],result["source_gap_sectors_in_frozen_radar"]))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
