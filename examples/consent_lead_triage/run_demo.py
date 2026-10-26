#!/usr/bin/env python3
"""Synthetic first-party consent gate and deterministic triage. No outgoing messages."""
import argparse
import collections
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

CATEGORIES = {
    "video": ("video", "subtitle", "剪辑", "视频", "字幕"),
    "crm": ("crm", "support", "ticket", "客服", "客户"),
    "finance_research": ("finance", "research", "rag", "金融", "研究"),
}
SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def utc_time(text):
    if not isinstance(text, str):
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def category_of(question):
    if not isinstance(question, str):
        return "manual_review"
    value = question.casefold()
    matches = [name for name, words in CATEGORIES.items() if any(word in value for word in words)]
    return matches[0] if len(matches) == 1 else "manual_review"


def triage_records(records, as_of):
    """Return an aggregate plus permitted, anonymous human-review suggestions only."""
    if not isinstance(records, list):
        raise ValueError("Input must be a JSON array")
    as_of = utc_time(as_of) if isinstance(as_of, str) else as_of
    if not isinstance(as_of, datetime) or as_of.utcoffset() is None:
        raise ValueError("A timezone-aware as_of is required")
    as_of = as_of.astimezone(timezone.utc)
    ids = [r.get("lead_id") if isinstance(r, dict) else None for r in records]
    repeated = {key for key, n in collections.Counter(ids).items() if n > 1}
    blocked = collections.Counter()
    outcomes = []
    for r in records:
        if not isinstance(r, dict):
            blocked["invalid_record"] += 1
            continue
        lead_id = r.get("lead_id")
        if not isinstance(lead_id, str) or not SAFE_ID.fullmatch(lead_id):
            blocked["invalid_anonymous_id"] += 1
            continue
        if lead_id in repeated:
            blocked["duplicate_or_conflicting_record"] += 1
            continue
        if r.get("opt_out") is True:
            blocked["opted_out"] += 1
            continue
        if r.get("consent") is not True or r.get("consent_purpose") != "contact_requested":
            blocked["no_explicit_purpose_bound_consent"] += 1
            continue
        ts = utc_time(r.get("consent_at"))
        if ts is None or not as_of - timedelta(days=90) <= ts <= as_of:
            blocked["missing_future_or_stale_consent"] += 1
            continue
        category = category_of(r.get("question"))
        outcomes.append({
            "lead_id": lead_id,
            "category": category,
            "suggestion": "human_review_only",
            "contact_performed": False,
        })
    outcomes.sort(key=lambda x: x["lead_id"])
    return {
        "schema_version": 1,
        "demo_only": True,
        "as_of": as_of.isoformat(),
        "input_count": len(records),
        "eligible_count": len(outcomes),
        "blocked_count": sum(blocked.values()),
        "blocked_reasons": dict(sorted(blocked.items())),
        "human_review_queue": outcomes,
        "external_actions": 0,
        "privacy_note": "No contacts, emails, phone numbers, raw messages or outbound requests in the output.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON array of synthetic/authorized lead records")
    parser.add_argument("--as-of", default=datetime.now(timezone.utc).isoformat(),
                        help="ISO 8601 timestamp with timezone; pin for reproducibility")
    parser.add_argument("--out", type=Path, help="Optional location for JSON report")
    args = parser.parse_args()
    records = json.loads(args.input.read_text(encoding="utf-8"))
    report = triage_records(records, args.as_of)
    result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(result, encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
