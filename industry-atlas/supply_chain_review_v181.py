#!/usr/bin/env python3
"""V1.8.1 source-based supply-chain observation desk, fail-closed.

Selected manifests, lockfiles, SECURTY.md paths and git blob SHAs
are a snapshot of public Git trees. This is NOT a dependency resolver, SBOM,
license-compatibility review, CVE lookup or a security clearance.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from collections import Counter
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from external_leads_v179 import validate_ledger
from license_evidence_v180 import validate_license_files

ROOT=Path(__file__).resolve().parent
HEX=re.compile(r"^[0-9a-f]{40}$")
ROLES={"dependency-manifest","dependency-lockfile","component-manifest","component-lockfile","configuration"}
def _check_sha(value):
    if not isinstance(value,str) or not HEX.fullmatch(value):
        raise ContractError("Unexpected Git tree/file SHA")

def validate_supply_chain(data:dict,leads:dict,license_files:dict,snapshot:dict,atlas:dict,rules:dict)->list[dict]:
    validate_ledger(leads,snapshot,atlas,rules)
    validate_license_files(license_files,leads,snapshot,atlas,rules)
    if not isinstance(data,dict) or data.get("schema_version")!="1.0" or data.get("population")!="github-tree-readonly-supply-chain-path-snapshot":
        raise ContractError("Unrecognized snapshot")
    if data.get("observed_on")!=leads["observation_date"] or data.get("total_sources")!=10:
        raise ContractError("Observation date/count drift")
    if any(data.get(k)!=0 for k in ("verified_sboms","cve_scans_completed","security_clearances","license_compliance_verified")):
        raise ContractError("Supply chain verification cannot be claimed from file paths")
    rows=data.get("records")
    if not isinstance(rows,list) or len(rows)!=10:raise ContractError("Expected exact ten projects")
    source_by={r["id"]:r for r in leads["records"]}
    ids=set()
    for r in rows:
        if not isinstance(r,dict) or r.get("id") in ids or r.get("id") not in source_by:
            raise ContractError("Missing/duplicate/foreign project identity")
        source=source_by[r["id"]]
        if r.get("repo_full_name")!=source["repo_full_name"] or r.get("observed_branch")!=source["observed_metadata"]["default_branch"]:
            raise ContractError("Tree not tied to trusted existing repository branch")
        _check_sha(r.get("git_tree_sha"))
        if r.get("tree_truncated") is not False:
            raise ContractError("Snapshot tree truncated or unverified")
        if r.get("search_scope")!="selected conventional paths in recursively fetched Git tree; not a full dependency resolution":
            raise ContractError("Observation scope misrepresented")
        if any(r.get(k) is not False for k in (
            "dependency_inventory_complete","sbom_generated","vulnerability_scan_performed",
            "security_policy_effectiveness_verified","dependencies_license_verified",
            "automated_risk_classification_approved","source_promoted")):
            raise ContractError("Cannot self-approve file or scanner evidence")
        selected=r.get("selected_dependency_files")
        if not isinstance(selected,list) or len(selected)>12:
            raise ContractError("Unbounded file set")
        seen=set()
        for entry in selected:
            if not isinstance(entry,dict) or entry.get("role") not in ROLES:
                raise ContractError("Unknown dependency file role")
            path=entry.get("path")
            if not isinstance(path,str) or len(path)>250 or path.startswith("/") or ".." in path.split("/") or "\\" in path:
                raise ContractError("Invalid file path")
            if path in seen:raise ContractError("Duplicate file")
            _check_sha(entry.get("sha"))
            if entry.get("url")!=source["repo_url"]+"/blob/"+r["observed_branch"]+"/"+path:
                raise ContractError("Untrusted Git source file URL")
            seen.add(path)
        policy=r.get("selected_security_policy_file")
        if policy is not None:
            if not isinstance(policy,dict) or policy.get("path") not in ("SECURITY.md",".github/SECURITY.md"):
                raise ContractError("Unknown policy file path")
            _check_sha(policy.get("sha"))
            if policy.get("url")!=source["repo_url"]+"/blob/"+r["observed_branch"]+"/"+policy["path"]:
                raise ContractError("Untrusted policy file URL")
            if not isinstance(policy.get("cue"),str) or not 10<=len(policy["cue"])<=240:
                raise ContractError("Security text cue omitted")
        ids.add(r["id"])
    if ids!=set(source_by):
        raise ContractError("Incomplete external leads crosswalk")
    selected_policies={r["id"] for r in rows if r["selected_security_policy_file"]}
    if selected_policies!={"github:commaai/openpilot","github:open5gs/open5gs"}:
        raise ContractError("Observed security policy crosscheck changed; review required")
    return sorted(rows,key=lambda x:x["id"])

def build_report(data,leads,license_files,snapshot,atlas,rules):
    rows=validate_supply_chain(data,leads,license_files,snapshot,atlas,rules)
    license_by={x["id"]:x for x in license_files["records"]}
    source_by={x["id"]:x for x in leads["records"]}
    result=[]
    for r in rows:
        source=source_by[r["id"]];lic=license_by[r["id"]]
        flags=["sbom-not-generated","cve-scanning-not-performed","transitive-dependencies-not-inventoried",
               "software-security-not-attested"]
        if not r["selected_dependency_files"]:
            flags.append("no-selected-conventional-dependency-file-not-proof-of-absence")
        if r["selected_security_policy_file"] is None:
            flags.append("security-policy-not-observed-in-selected-tree-scan-not-proof-of-absence")
        if lic["signal_reconciliation_status"]=="license-signal-needs-reconciliation":
            flags.append("license-metadata-text-discrepancy")
        result.append({
            "id":r["id"],"repo_name":r["repo_full_name"],"sector_id":source["sector_id"],
            "source_tree_sha":r["git_tree_sha"],"observed_on":data["observed_on"],
            "selected_dependency_files":r["selected_dependency_files"],
            "selected_security_policy_file":r["selected_security_policy_file"],
            "review_flags":flags,"security_approved":False,"cve_clear":None,
            "sbom_verified":False,"license_approved":False,
            "catalog_recommended":False
        })
    return {
        "schema_version":"1.0","report_type":"supply-chain-readiness-review-only",
        "observation_date":data["observed_on"],"projects":len(result),
        "selected_dependency_paths":sum(len(r["selected_dependency_files"]) for r in result),
        "projects_with_selected_dependency_paths":sum(bool(r["selected_dependency_files"]) for r in result),
        "selected_security_policy_paths":sum(r["selected_security_policy_file"] is not None for r in result),
        "license_signal_discrepancies":sum("license-metadata-text-discrepancy" in r["review_flags"] for r in result),
        "sboms_verified":0,"cve_scans_completed":0,"security_approvals":0,
        "auto_promotions":0,"network_requests":0,"release_gate":"HOLD",
        "records":result,
        "required_steps":["generate-sbom-from-pinned-source-and-dependencies","review-lockfile-and-transitive-licenses",
                          "run-licensed-vulnerability-check-with-a-reproducible-database-snapshot",
                          "triage-finding-severity-and-affected-versions","verify-security-reporting-process",
                          "human-review-regulated-sector-deployment-risk",
                          "owner-approval-separate-change"],
        "warning":"This is selected Git tree/path presence evidence only. It contains NO CVE search, dependency license clearance, complete SBOM, source builds or operational security proof."
    }

def compare_reports(previous,current):
    if any(x.get("report_type")!="supply-chain-readiness-review-only" or x.get("security_approvals")!=0 for x in (previous,current)):
        raise ContractError("Invalid unapproved reports")
    a={x["id"]:x for x in previous["records"]};b={x["id"]:x for x in current["records"]}
    events=[]
    for id in sorted(set(a)|set(b)):
        old,new=a.get(id),b.get(id)
        if old is None:kind="new-source-observation"
        elif new is None:kind="missing-in-current-sample-not-deletion"
        elif old["source_tree_sha"]!=new["source_tree_sha"]:kind="source-tree-drift-review"
        elif old["selected_dependency_files"]!=new["selected_dependency_files"]:kind="manifest-path-or-sha-drift-review"
        elif old["selected_security_policy_file"]!=new["selected_security_policy_file"]:kind="security-policy-path-or-sha-drift-review"
        else:kind="no-observed-file-change-not-security-clearance"
        events.append({"id":id,"kind":kind,"source_deletion_verified":False,"vulnerability_cleared":False,
                      "source_approved":False})
    return {"type":"supply-chain-drift-only","events":events,
            "counts":dict(sorted(Counter(e["kind"] for e in events).items())),
            "auto_approved":False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",required=True,type=Path);args=ap.parse_args()
    snapshot,atlas,rules=load_data()
    leads=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
    files=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
    data=json.loads((ROOT/"supply_chain_evidence_v181.json").read_text(encoding="utf-8"))
    result=build_report(data,leads,files,snapshot,atlas,rules)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PASS V1.8.1 supply-chain review: {result['projects']} projects, {result['selected_dependency_paths']} selected files, {result['selected_security_policy_paths']} policy paths, 0 CVE scans/approvals")
if __name__=="__main__":
    main()
