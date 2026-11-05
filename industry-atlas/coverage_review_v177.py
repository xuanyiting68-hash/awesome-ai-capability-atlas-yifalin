#!/usr/bin/env python3
"""V1.7.7 conservative sector coverage REVIEW queue; source/catalog unchanged.

This does NOT tag sources, approve tools, verify licenses, check URLs, infer user
data, certify industry relevance, scrape sites or call AI models. All proposed
sector associations are human-review-only based on exact frozen editorial topics.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
import argparse
import json
from pathlib import Path
from provider_contract_v174 import ContractError, https_source

ROOT = Path(__file__).resolve().parent
STAGE = "unapproved-sector-proposal"

def load_data(root: Path = ROOT) -> tuple[dict, dict, dict]:
    snapshot = json.loads((root / "discovery_seed.json").read_text(encoding="utf-8"))
    atlas = json.loads((root / "advisor_v16_data.json").read_text(encoding="utf-8"))
    rules = json.loads((root / "coverage_review_rules_v177.json").read_text(encoding="utf-8"))
    return snapshot, atlas, rules

def generate_review(snapshot: dict, atlas: dict, policy: dict) -> dict:
    if not isinstance(snapshot, dict) or snapshot.get("mode") != "cached-editorial-baseline" or snapshot.get("auto_promoted") is not False:
        raise ContractError("Only a frozen non-promotional source snapshot is supported")
    records = snapshot.get("records")
    if not isinstance(records, list) or len(records) != 133 or any(r.get("approved") is not False for r in records):
        raise ContractError("Unapproved source baseline changed")
    sectors = atlas.get("sectors")
    if not isinstance(sectors, list) or len(sectors) != 32:
        raise ContractError("Industry taxonomy size changed")
    by_id = {s["id"]: s for s in sectors}
    if len(by_id) != 32:
        raise ContractError("Duplicate industry IDs")
    if policy.get("schema_version") != "1.0" or not isinstance(policy.get("rules"), list):
        raise ContractError("Invalid coverage policy")
    topic_rules = {}
    for rule in policy["rules"]:
        topic = rule.get("topic")
        targets = rule.get("sector_ids")
        why = rule.get("why")
        if not isinstance(topic, str) or not topic or topic in topic_rules:
            raise ContractError("Ambiguous topic rule")
        if not isinstance(why, str) or not 15 <= len(why) <= 300:
            raise ContractError("Source review rationale absent")
        if not isinstance(targets, list) or not 1 <= len(targets) <= 3 or len(set(targets)) != len(targets) or any(s not in by_id for s in targets):
            raise ContractError("Coverage rule sector invalid")
        topic_rules[topic] = rule

    seen = set()
    declared = Counter()
    proposals = []
    unmapped_ids = []
    for r in records:
        ident = r.get("id")
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ContractError("Duplicate baseline source identity")
        seen.add(ident)
        https_source(r.get("url"))
        if r.get("source_url") != r.get("url"):
            raise ContractError("Unexpected source/origin mismatch")
        sector_ids = r.get("sector_ids")
        if not isinstance(sector_ids, list) or len(sector_ids) != len(set(sector_ids)) or any(s not in by_id for s in sector_ids):
            raise ContractError("Invalid baseline industry tags")
        for sid in sector_ids:
            declared[sid] += 1
        if sector_ids:
            continue  # Critical: NEVER re-label or propose for already-tagged sources.
        unmapped_ids.append(ident)
        rule = topic_rules.get(r.get("topic"))
        if not rule:
            continue  # No fallback guesses.
        proposals.append({
            "record_id": ident,
            "name": str(r.get("name") or "")[:150],
            "url": r["url"],
            "description": str(r.get("description") or "")[:800],
            "topic": r["topic"],
            "proposed_sector_ids": list(rule["sector_ids"]),
            "rationale": rule["why"],
            "review_status": STAGE,
            "approved": False,
            "license_verified": False,
            "security_verified": False,
            "link_checked_live": False,
        })
    proposals.sort(key=lambda x: x["record_id"])
    proposed = Counter()
    for p in proposals:
        for sid in p["proposed_sector_ids"]:
            proposed[sid] += 1
    coverage = []
    for s in sectors:
        sid = s["id"]
        direct = declared[sid]
        suggest = proposed[sid]
        state = "declared-editorial-tags" if direct > 0 else "proposals-only" if suggest > 0 else "no-records"
        coverage.append({
            "sector_id": sid, "sector_name": s["name"],
            "declared_editorial": direct,
            "unreviewed_proposals": suggest,
            "coverage_state": state,
            "verified_sources": 0,
        })
    stats = Counter(row["coverage_state"] for row in coverage)
    if len(unmapped_ids) + (len(records) - len(unmapped_ids)) != len(records):
        raise ContractError("Baseline population mismatch")
    return {
        "schema_version": "1.0",
        "report_type": "industry-proposal-review",
        "source_population": "cached-editorial-baseline",
        "total_records": len(records),
        "without_declared_industry": len(unmapped_ids),
        "proposed_record_count": len(proposals),
        "unresolved_unmapped_count": len(unmapped_ids) - len(proposals),
        "existing_editorial_tagged_sectors": sum(s["declared_editorial"] > 0 for s in coverage),
        "proposal_only_sectors": sum(s["coverage_state"] == "proposals-only" for s in coverage),
        "no_candidate_sectors": sum(s["coverage_state"] == "no-records" for s in coverage),
        "coverage_states": dict(sorted(stats.items())),
        "sectors": coverage,
        "proposals": proposals,
        "automatic_promotions": 0,
        "real_source_checks": 0,
        "verified_source_count": 0,
        "review_decisions": 0,
        "production_release_allowed": False,
        "warning": "All mappings are deterministic editorial suggestions ONLY; no catalog writes, independent task relevance, live link checks, security or licensing verification. Sources without candidates must NOT be treated as market absence."
    }

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args(argv)
    data = generate_review(*load_data())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS V1.7.7 coverage: %d direct-tagged sectors; %d proposal-only; %d no candidates; %d unreviewed candidate sources; 0 promotions" % (
        data["existing_editorial_tagged_sectors"], data["proposal_only_sectors"], data["no_candidate_sectors"], data["proposed_record_count"]))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
