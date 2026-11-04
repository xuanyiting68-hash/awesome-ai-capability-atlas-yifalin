#!/usr/bin/env python3
"""V1.8.0 bounded read-only GitHub observation drift monitor.

Live mode MUST be an explicit scheduled/manual research-only event. Only the
ten pinned GitHub API repository and license-file endpoints are contacted.
The output is a CI artifact, never a source mutation or approval signal.
No untrusted user URL is fetched. Never auto-approve after a successful check.
"""
from __future__ import annotations
from datetime import datetime,timezone
import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError,URLError
from urllib.parse import quote
from urllib.request import Request,build_opener,HTTPRedirectHandler
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from license_evidence_v180 import validate_license_files

ROOT=Path(__file__).resolve().parent
MAX_BODY_BYTES=1_000_000

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

def fetch_metadata(url:str,token:str|None=None)->dict:
    if not url.startswith("https://api.github.com/repos/"):
        raise ContractError("Blocked endpoint")
    headers={"Accept":"application/vnd.github+json",
             "User-Agent":"YIFALIN-public-repo-review-only/1.8.0",
             "X-GitHub-Api-Version":"2022-11-28"}
    if token:
        headers["Authorization"]="Bearer "+token
    opener=build_opener(NoRedirect())
    try:
        with opener.open(Request(url,headers=headers),timeout=8) as response:
            if response.status!=200:
                return {"kind":"unavailable","reason":"unexpected-http-status"}
            data=response.read(MAX_BODY_BYTES+1)
            if len(data)>MAX_BODY_BYTES:
                return {"kind":"unavailable","reason":"response-size-limit"}
            decoded=json.loads(data.decode("utf-8"))
            if not isinstance(decoded,dict):
                return {"kind":"unavailable","reason":"non-object-response"}
            return {"kind":"ok","data":decoded}
    except HTTPError as error:
        return {"kind":"unavailable","reason":"http-"+str(error.code)}
    except (URLError,TimeoutError,UnicodeError,ValueError):
        return {"kind":"unavailable","reason":"network-or-response-error"}

def monitor(leads:dict,files:dict,snapshot:dict,atlas:dict,rules:dict, *,
            as_of:str,mode:str="offline",ack:bool=False,fetcher=fetch_metadata)->dict:
    validated=validate_license_files(files,leads,snapshot,atlas,rules)
    try:
        as_of_day=datetime.fromisoformat(as_of.replace("Z","+00:00"))
        if as_of_day.tzinfo is None or as_of_day.utcoffset()!=timezone.utc.utcoffset(as_of_day):
            raise ValueError("Must be explicit UTC")
    except ValueError:
        raise ContractError("as_of must be UTC ISO timestamp") from None
    if as_of_day.date()<datetime.fromisoformat(leads["observation_date"]+"T00:00:00+00:00").date():
        raise ContractError("Observation date precedes frozen baseline")
    if mode not in ("offline","live") or (mode=="live" and not ack):
        raise ContractError("Live metadata requires explicit acknowledgement")
    entries=[]
    token=os.environ.get("GITHUB_TOKEN") if mode=="live" else None
    for observed in validated["records"]:
        base=next(x for x in leads["records"] if x["id"]==observed["id"])
        slug=base["repo_full_name"]
        # both the repository and file paths originate from the validated
        # allowlisted, fixed ten-file observation ledger; no remote URL inputs.
        repo_endpoint="https://api.github.com/repos/"+slug
        content_endpoint=(repo_endpoint+"/contents/"+quote(observed["license_file_path"],safe="")
                          +"?ref="+quote(observed["observed_branch"],safe=""))
        row={"id":observed["id"],"sector_id":base["sector_id"],
             "repo_url":observed["repo_url"],"reference_file_url":observed["license_file_url"],
             "baseline_repo_id":base["repo_id"],
             "baseline_license_blob_sha":observed["license_blob_sha"],
             "observed_spdx_signal":base["observed_metadata"]["license_spdx_signal"],
             "observation_status":"not-checked" if mode=="offline" else "review-pending",
             "metadata_status":"not-checked","file_status":"not-checked",
             "flags":[],"auto_approved":False,"legal_license_verified":False,
             "security_verified":False,"source_deleted_verified":False,
             "catalog_updated":False}
        if mode=="live":
            meta=fetcher(repo_endpoint,token)
            if meta.get("kind")!="ok":
                row["metadata_status"]="unavailable"
                row["flags"].append("repository-metadata-unavailable-not-deletion")
            else:
                item=meta.get("data",{})
                if item.get("id")!=base["repo_id"] or item.get("full_name","").lower()!=slug.lower():
                    row["metadata_status"]="identity-changed-review"
                    row["flags"].append("repository-id-or-name-mismatch")
                else:
                    row["metadata_status"]="observed"
                    if item.get("archived") is True or item.get("disabled") is True:
                        row["flags"].append("repository-archived-or-disabled-review")
                    signal=(item.get("license") or {}).get("spdx_id")
                    if signal!=row["observed_spdx_signal"]:
                        row["flags"].append("spdx-metadata-changed-review")
                    if item.get("default_branch")!=observed["observed_branch"]:
                        row["flags"].append("default-branch-changed-review")
            file_result=fetcher(content_endpoint,token)
            if file_result.get("kind")!="ok":
                row["file_status"]="unavailable"
                row["flags"].append("file-observation-unavailable-not-deletion")
            else:
                item=file_result.get("data",{})
                if item.get("path")!=observed["license_file_path"] or item.get("type")!="file":
                    row["file_status"]="unexpected-content-review"
                    row["flags"].append("file-path-or-type-mismatch")
                elif item.get("sha")!=observed["license_blob_sha"]:
                    row["file_status"]="blob-changed-review"
                    row["flags"].append("license-file-sha-drift-review")
                else:
                    row["file_status"]="blob-unchanged"
            row["observation_status"]="needs-review" if row["flags"] else "metadata-only-unchanged"
        entries.append(row)
    observed_count=sum(x["metadata_status"]=="observed" for x in entries)
    return {"schema_version":"1.0","report_type":"public-repository-readonly-monitor",
            "mode":mode,"run_as_of":as_of,"total_repositories":len(entries),
            "max_possible_requests":20,"network_requests_attempted":20 if mode=="live" else 0,
            "identity_metadata_observed":observed_count,"approval_count":0,
            "verified_license_count":0,"source_deletion_verified_count":0,
            "catalog_mutations":0,"production_publish":False,"release_gate":"HOLD",
            "entries":entries,
            "warning":"Only repository metadata and file Git SHA compared. API failure is not deletion. Identical SHA is not dependency, legal, security or use-case approval."}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--mode",choices=("offline","live"),default="offline")
    parser.add_argument("--ack-read-only-live",action="store_true")
    parser.add_argument("--as-of",required=True,help="UTC YYYY-MM-DDTHH:MM:SSZ")
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args(argv)
    from pathlib import Path
    snap,atlas,rules=load_data()
    leads=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
    files=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
    report=monitor(leads,files,snap,atlas,rules,as_of=args.as_of,mode=args.mode,ack=args.ack_read_only_live)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS V1.8.0 bounded "+args.mode+" monitor: "+str(report["total_repositories"])+
          " sources, "+str(report["network_requests_attempted"])+" bounded requests; 0 approvals")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
