#!/usr/bin/env python3
"""V1.7.6 metadata audit desk: NO external fetching, approval or source certification.

"last_modified" describes a previously cached repository metadata observation.
It is NOT a last-verified, checked-links, licence review or safety audit timestamp.
The deterministic as-of date is passed explicitly, not inferred from wall-clock CI.
"""
from __future__ import annotations
from collections import Counter
from datetime import date, datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from provider_contract_v174 import ContractError, https_source

ROOT=Path(__file__).resolve().parent
MAX_ROWS=500
ALLOWED_SECTORS={f"s{i:02d}" for i in range(1,33)}
FIELDS=("name","description","source_url","license_spdx_signal","last_modified","sector_ids","review_state","safety_review","verification")

def _date(text: str) -> date | None:
    if not isinstance(text,str) or not text.strip():
        return None
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}",text):
            return date.fromisoformat(text)
        return datetime.fromisoformat(text.replace("Z","+00:00")).date()
    except ValueError:
        return None

def canonical_key(url: str) -> str:
    https_source(url)
    p=urlsplit(url)
    if p.fragment or p.query or not p.hostname:
        raise ContractError("Evidence identity must be canonical HTTPS without query or fragment")
    return p.hostname.lower()+p.path.rstrip("/").lower()

def validate_snapshot(snapshot: dict) -> list[dict]:
    if not isinstance(snapshot,dict) or snapshot.get("mode")!="cached-editorial-baseline":
        raise ContractError("Wrong editorial snapshot population")
    if snapshot.get("auto_promoted") is not False or snapshot.get("live_llm") is not False:
        raise ContractError("No unapproved or live-model snapshot allowed")
    records=snapshot.get("records")
    if not isinstance(records,list) or not 1<=len(records)<=MAX_ROWS:
        raise ContractError("Unexpected bounded source sample")
    seen_urls,seen_ids=set(),set()
    for r in records:
        if not isinstance(r,dict) or r.get("approved") is not False:
            raise ContractError("Approval must stay false")
        if not isinstance(r.get("id"),str) or not r["id"] or r["id"] in seen_ids:
            raise ContractError("Duplicate/missing source identity")
        key=canonical_key(r.get("url"))
        source=canonical_key(r.get("source_url"))
        if key!=source or key in seen_urls:
            raise ContractError("Duplicate source or unexpected canonical URL")
        if not isinstance(r.get("sector_ids"),list) or set(r["sector_ids"])-ALLOWED_SECTORS:
            raise ContractError("Invalid sector tag")
        if r.get("source_kind")!="editorial-curated-baseline":
            raise ContractError("Unexpected unreviewed source")
        seen_urls.add(key)
        seen_ids.add(r["id"])
    return records

def status(record: dict, as_of: date) -> dict:
    checked=_date(record.get("last_modified"))
    issues=[]
    if checked is None:
        days=None
        band="metadata-date-missing"
        issues.append("metadata-date-unparseable")
    else:
        days=(as_of-checked).days
        if days<0:
            band="metadata-date-in-future"
            issues.append("future-metadata-date")
        else:
            band="within-90d" if days<=90 else "91-365d" if days<=365 else "older-than-365d"
            if days>180: issues.append("metadata-older-than-180d")
    license_signal=str(record.get("license_spdx_signal") or "unknown").strip()
    if license_signal.lower() in ("", "unknown","noassertion","none"):
        issues.append("license-signal-unknown")
    else:
        issues.append("license-not-independently-verified")
    if not record.get("sector_ids"):
        issues.append("no-editorial-sector-mapping")
    if record.get("safety_review")!="audited":
        issues.append("security-not-audited")
    # Even a cached "audited" string is never trusted as a current audit attestation.
    else:
        issues.append("security-attestation-not-independently-verified")
    issues.append("availability-not-live-checked")
    return {
        "id":record["id"],"name":str(record.get("name") or "")[:150],
        "url":record["source_url"],"sector_ids":record["sector_ids"],
        "metadata_date":record.get("last_modified") or None,
        "metadata_age_days":days,"metadata_age_band":band,
        "license_signal":license_signal,
        "license_verified":False,"security_verified":False,
        "link_currently_accessible":None,"task_effectiveness_verified":False,
        "approval":"unapproved","review_gate":"human-verification-required",
        "issues":sorted(set(issues)),
    }

def build_report(snapshot: dict, as_of: date) -> dict:
    entries=validate_snapshot(snapshot)
    if not isinstance(as_of,date):raise ContractError("Explicit as-of date required")
    rows=sorted((status(e,as_of) for e in entries),key=lambda x:x["id"])
    counts=Counter(issue for r in rows for issue in r["issues"])
    source_ids=[r["id"] for r in rows]
    digest=sha256("\n".join(source_ids).encode("utf-8")).hexdigest()
    return {
        "schema_version":"1.0","report_type":"offline-source-governance",
        "source_population":"cached-editorial-baseline",
        "as_of_date":as_of.isoformat(),"dataset_sha256_ids":digest,
        "count":len(rows),"summary_issues":dict(sorted(counts.items())),
        "rows":rows,"independent_review_count":0,"automatically_promoted":False,
        "real_source_network_checks":0,"production_release_allowed":False,
        "warning":"Age is cached source metadata age ONLY; no live link, LICENSE, security, publisher or outcome verification has occurred.",
    }

def compare_reports(previous: dict | None, current: dict) -> dict:
    """Two archived metadata reports are observational, NEVER live source verification."""
    if current.get("report_type")!="offline-source-governance" or current.get("automatically_promoted") is not False:
        raise ContractError("Invalid current governance report")
    if previous is not None:
        if previous.get("report_type")!=current["report_type"] or previous.get("source_population")!=current.get("source_population"):
            raise ContractError("Cannot compare unlike evidence populations")
        if previous.get("as_of_date","")>=current.get("as_of_date",""):
            raise ContractError("New report must have later explicit as-of date")
    old={r["id"]:r for r in previous["rows"]} if previous else {}
    new={r["id"]:r for r in current["rows"]}
    events=[]
    for ident,row in sorted(new.items()):
        prior=old.get(ident)
        observed=[k for k in ("url","sector_ids","license_signal","metadata_date") if prior and row.get(k)!=prior.get(k)]
        events.append({"id":ident,"kind":"first-baseline" if previous is None else "new-in-sample" if prior is None else "metadata-changed" if observed else "unchanged-metadata",
                       "changed_fields":observed,"deleted":False,"approval":"unapproved"})
    for ident in sorted(set(old)-set(new)):
        events.append({"id":ident,"kind":"not-observed-in-latest-snapshot","changed_fields":[],"deleted":False,"approval":"unapproved"})
    return {"schema_version":"1.0","comparison_state":"no-prior-baseline" if previous is None else "compared-cached-observations",
            "previous_as_of":previous["as_of_date"] if previous else None,"current_as_of":current["as_of_date"],
            "auto_promoted":False,"deletions_proven":False,
            "event_counts":dict(sorted(Counter(e["kind"] for e in events).items())),
            "events":events,
            "warning":"No live checks occurred: metadata age changes merely reflect passage of time; sample absence does not prove deletion."}

def _main() -> None:
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--as-of",required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    day=_date(a.as_of)
    if day is None or not re.fullmatch(r"\d{4}-\d{2}-\d{2}",a.as_of):
        raise SystemExit("Explicit YYYY-MM-DD required")
    base=json.loads((ROOT/"discovery_seed.json").read_text(encoding="utf-8"))
    report=build_report(base,day)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("PASS source governance: %s cached-unapproved references, 0 live checks, 0 approvals"%report["count"])

if __name__=="__main__":
    _main()
