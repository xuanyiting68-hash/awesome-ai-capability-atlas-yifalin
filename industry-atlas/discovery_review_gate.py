#!/usr/bin/env python3
"""Human review gate for Atlas discovery. Evidence requests are NOT approvals.

The tool accepts an explicit reviewer-authored JSON decision file, checks evidence
completeness, and emits a review request report. No auth claim or approval can be
established by a self-declared reviewer name. Only Owner-controlled merge governance
may promote a candidate after independent verification.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

from discovery_review import canonical_url
from discovery_lifecycle import read_snapshot, atomic_write

ALLOWED_DECISIONS = {"investigate", "defer", "reject", "request-promotion"}
REQUIRED = ("license_evidence_url", "safety_review_url", "task_test_evidence_url")
MAX_DECISIONS = 150


def validate_decision(row: dict, candidates: dict) -> dict:
    if not isinstance(row, dict):
        raise ValueError("Each decision must be an object")
    decision = str(row.get("decision") or "")
    if decision not in ALLOWED_DECISIONS:
        raise ValueError("Unrecognized decision")
    url = canonical_url(row.get("url"))
    if not url or url not in candidates:
        raise ValueError("Candidate URL not in this exact snapshot")
    target = candidates[url]
    if row.get("candidate_id") != target["id"]:
        raise ValueError("Candidate ID must match the exact snapshot")
    reviewer = str(row.get("reviewer") or "").strip()
    rationale = str(row.get("rationale") or "").strip()
    if len(reviewer) < 3 or len(reviewer) > 100 or len(rationale) < 20 or len(rationale) > 2000:
        raise ValueError("Reviewer and substantive reason are required")
    status = "research-queued" if decision == "investigate" else "deferred" if decision == "defer" else "not-recommended"
    evidence = row.get("evidence") or {}
    if not isinstance(evidence, dict):
        raise ValueError("Evidence must be an object")
    blockers = []
    if decision == "request-promotion":
        for k in REQUIRED:
            link = canonical_url(evidence.get(k))
            # Evidence links pointing at the resource itself are not independent checks.
            if not link or link == url:
                blockers.append(k)
        if not target.get("sector_ids"):
            blockers.append("industry_fit_unverified")
        if target.get("license_spdx_signal") in (None, "", "unknown", "NOASSERTION"):
            blockers.append("license_signal_unknown")
        # Positive source metadata is not an independent security/commercial audit.
        status = "evidence-incomplete" if blockers else "pending-independent-owner-review"
    return {
        "candidate_id": target["id"], "url": url, "name": target.get("name", ""),
        "decision": decision, "reviewer_declared": reviewer,
        "rationale": rationale, "request_state": status,
        "evidence_links": {k: canonical_url(evidence.get(k)) for k in REQUIRED if canonical_url(evidence.get(k))},
        "missing_evidence": blockers,
        "authenticated_reviewer": False, "approved": False,
        "safety_verified": False, "license_cleared": False,
        "auto_promoted": False,
    }


def prepare(queue: dict, decisions: list[dict]) -> dict:
    if len(decisions) > MAX_DECISIONS:
        raise ValueError("Decision batch too large")
    candidates = {r["url"]: r for r in queue["records"]}
    seen = set()
    outcome = []
    for row in decisions:
        result = validate_decision(row, candidates)
        if result["url"] in seen:
            raise ValueError("Conflicting duplicate decision for resource")
        seen.add(result["url"])
        outcome.append(result)
    return {
        "schema_version": "1.0", "snapshot_generated_at_utc": queue["generated_at_utc"],
        "decision_count": len(outcome), "owner_authenticated": False,
        "approval_count": 0, "auto_promoted": False,
        "notice": ("Manual review request preparation only. Reviewer names and links are self-declared, "
                   "not verified authority, safety, licensing or field performance. "
                   "Independent Owner-controlled signoff remains mandatory."),
        "requests": outcome,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    a = parser.parse_args(argv)
    try:
        queue = read_snapshot(a.queue)
        decisions = json.loads(a.decisions.read_text(encoding="utf-8"))
        if not isinstance(decisions, list):
            raise ValueError("Decisions must be a JSON list")
        report = prepare(queue, decisions)
        atomic_write(a.output, report)
        print(json.dumps({"requests":len(report["requests"]),"approved":0,"auto_promoted":False}))
        return 0
    except Exception as exc:
        print("Review gate failed closed; prior output preserved:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
