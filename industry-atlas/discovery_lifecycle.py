#!/usr/bin/env python3
"""Compare successive discovery snapshots without mistaking sample absence for deletion.

Offline/PR checks use synthetic previous snapshots. Scheduled runs may compare with an
audited previous complete run artifact. All events remain unreviewed evidence leads.
This module never modifies catalog, curated entries, GitHub, or production state.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import sys

from discovery_review import canonical_url

VALID_MODES = {"offline", "live"}
FIELDS = ("name", "description", "last_modified", "license_spdx_signal",
          "sector_ids", "source_kind", "review_state", "kind", "source_url")
EVENT_LIMIT = 500


def read_snapshot(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or obj.get("schema_version") != "1.0":
        raise ValueError("Unrecognized discovery snapshot schema")
    if obj.get("mode") not in VALID_MODES or obj.get("auto_promoted") is not False:
        raise ValueError("Only unapproved offline/live snapshots can be compared")
    records = obj.get("records")
    if not isinstance(records, list) or len(records) > 500 or not records:
        raise ValueError("Invalid bounded discovery snapshot")
    urls = set()
    for row in records:
        if not isinstance(row, dict) or row.get("approved") is not False or row.get("verification") != "metadata-only":
            raise ValueError("Snapshot contains an unverified approval or invalid record")
        url = canonical_url(row.get("url"))
        if not url or row.get("url") != url or url in urls:
            raise ValueError("Unsafe, noncanonical or duplicate resource URL")
        if row.get("source_kind") not in ("existing-catalog", "github-api", "huggingface-api", "arxiv-api"):
            raise ValueError("Unrecognized discovery source")
        urls.add(url)
    if obj.get("queue_count") != len(records):
        raise ValueError("Snapshot size metadata mismatch")
    return obj


def record_changes(old: dict, new: dict) -> list[str]:
    changed = [field for field in FIELDS if old.get(field) != new.get(field)]
    # Deliberately do not treat ranking-score drift as a product change.
    return changed


def compare(current: dict, previous: dict | None = None) -> dict:
    if previous and previous.get("mode") != current.get("mode"):
        raise ValueError("Cannot compare distinct offline/live discovery populations")
    now = current.get("generated_at_utc")
    if not isinstance(now, str) or not now:
        raise ValueError("Current snapshot timestamp missing")
    current_by_url = {row["url"]: row for row in current["records"]}
    previous_by_url = {row["url"]: row for row in previous["records"]} if previous else {}
    outcomes = []
    for url in sorted(current_by_url):
        row = current_by_url[url]
        prior = previous_by_url.get(url)
        fields = record_changes(prior, row) if prior else []
        kind = "baseline" if previous is None else "new-observation" if prior is None else "metadata-changed" if fields else "unchanged"
        outcomes.append({
            "url": url, "id": row["id"], "name": row["name"],
            "kind": kind, "changed_fields": fields, "review_state": row["review_state"],
            "source_kind": row["source_kind"], "sector_ids": row.get("sector_ids", []),
            "approved": False, "deleted": False,
        })
    # A bounded top-N scan does NOT prove a resource was taken down or abandoned.
    for url in sorted(set(previous_by_url) - set(current_by_url)):
        row = previous_by_url[url]
        outcomes.append({
            "url": url, "id": row["id"], "name": row["name"],
            "kind": "not-seen-in-sample", "changed_fields": [],
            "review_state": "requires-recheck", "source_kind": row["source_kind"],
            "sector_ids": row.get("sector_ids", []), "approved": False, "deleted": False,
        })
    counts = dict(sorted(Counter(e["kind"] for e in outcomes).items()))
    high_change = [e for e in outcomes if e["kind"] in ("new-observation", "metadata-changed", "not-seen-in-sample")]
    return {
        "schema_version": "1.0", "generated_at_utc": now,
        "current_mode": current["mode"],
        "previous_snapshot_at_utc": previous.get("generated_at_utc") if previous else None,
        "comparison_state": "compared-samples" if previous else "no-prior-baseline",
        "deletion_verified": False, "auto_promoted": False,
        "warning": ("No previous comparable snapshot: initial records are baseline only."
                    if previous is None else
                    "Source samples are bounded and ranked. Missing from a new sample does not prove deletion, inactivity or license revocation."),
        "counts": counts,
        "events": (high_change if previous else outcomes)[:EVENT_LIMIT],
        "omitted_events": max(0, len(high_change if previous else outcomes)-EVENT_LIMIT),
    }


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    tmp.replace(path)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        current = read_snapshot(args.current)
        previous = read_snapshot(args.previous) if args.previous is not None else None
        out = compare(current, previous)
        atomic_write(args.output, out)
        print(json.dumps({"comparison_state":out["comparison_state"],"counts":out["counts"],"auto_promoted":False}))
        return 0
    except Exception as exc:
        print("Fail closed, previous delta report preserved:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
