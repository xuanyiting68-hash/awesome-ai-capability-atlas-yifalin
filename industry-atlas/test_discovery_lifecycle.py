#!/usr/bin/env python3
"""Fully synthetic safety/regression tests: lifecycle vs sampled population and review requests."""
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

import discovery_review as discovery
import discovery_lifecycle as lifecycle
import discovery_review_gate as gate

NOW = datetime(2026, 11, 4, tzinfo=timezone.utc)


def entry(name="finance factor agent", url="https://github.com/sample/finance-factor-agent",
          description="A portfolio research agent with testable methods", modified="2026-10-31T00:00:00Z",
          license="MIT"):
    out = discovery.evaluate({
        "name": name, "url": url, "description": description, "kind": "agent",
        "source_kind": "github-api", "owner": "sample",
        "license_spdx": license, "last_modified": modified,
    }, NOW)
    assert out is not None
    return out


def queue(items, when="2026-11-04T00:00:00+00:00", mode="live"):
    return {
        "schema_version": "1.0", "generated_at_utc": when,
        "mode": mode, "auto_promoted": False, "queue_count": len(items),
        "records": items, "sources": ["GitHub public search API"],
    }


class LifecycleAndGate(TestCase):
    def test_empty_previous_is_baseline_not_new(self):
        current = queue([entry()])
        report = lifecycle.compare(current)
        self.assertEqual(report["comparison_state"], "no-prior-baseline")
        self.assertEqual(report["counts"]["baseline"], 1)
        self.assertFalse(report["deletion_verified"])

    def test_delta_classifies_changes_without_claiming_deletion(self):
        base = entry()
        gone = entry("old warehouse agent", "https://github.com/sample/old-warehouse", "warehouse logistics AI")
        old = queue([base, gone], "2026-10-30T00:00:00+00:00")
        updated = dict(base, last_modified="2026-11-03T02:00:00Z", description="A portfolio research agent with new testing evidence")
        fresh = entry("teacher lesson agent", "https://github.com/sample/teacher-lessons", "teacher classroom assistant")
        newer = queue([updated, fresh], "2026-11-04T00:00:00+00:00")
        result = lifecycle.compare(newer, old)
        self.assertEqual(result["counts"], {
            "metadata-changed": 1, "new-observation": 1, "not-seen-in-sample": 1
        })
        self.assertTrue(all(not x["approved"] and not x["deleted"] for x in result["events"]))
        self.assertTrue(any(x["changed_fields"] == ["description", "last_modified"] for x in result["events"]))

    def test_score_only_drift_is_not_real_product_change(self):
        old = entry()
        newer = dict(old, metadata_score=old["metadata_score"]+9, score_parts={"freshness":0})
        self.assertEqual(lifecycle.record_changes(old, newer), [])
        result = lifecycle.compare(queue([newer]), queue([old], "2026-10-30T00:00:00+00:00"))
        self.assertEqual(result["counts"], {"unchanged": 1})
        self.assertEqual(result["events"], [])

    def test_different_population_rejected(self):
        with self.assertRaises(ValueError):
            lifecycle.compare(queue([entry()], mode="live"), queue([entry()], mode="offline"))

    def test_snapshot_rejects_promotion_duplication_and_bad_urls(self):
        with TemporaryDirectory() as td:
            f = Path(td) / "input.json"
            base = entry()
            for records in (
                [dict(base, approved=True)],
                [base, base],
                [dict(base, url="https://evil.invalid/example")],
            ):
                value=queue(records)
                f.write_text(json.dumps(value), encoding="utf-8")
                with self.assertRaises(ValueError):
                    lifecycle.read_snapshot(f)

    def test_failures_preserve_old_delta_file(self):
        with TemporaryDirectory() as td:
            a = Path(td) / "current.json"
            out = Path(td) / "delta.json"
            a.write_text("{}", encoding="utf-8")
            out.write_text('{"known":"safe"}', encoding="utf-8")
            self.assertEqual(lifecycle.main(["--current",str(a),"--output",str(out)]),2)
            self.assertEqual(json.loads(out.read_text())["known"],"safe")

    def test_manual_request_must_match_snapshot_and_stays_pending(self):
        resource = entry()
        doc = queue([resource])
        review = {
            "candidate_id": resource["id"], "url": resource["url"],
            "reviewer": "research-team", "decision": "request-promotion",
            "rationale": "This candidate has a clear finance use case and needs independent verification.",
            "evidence": {
                "license_evidence_url": "https://github.com/sample/finance-factor-agent/blob/main/LICENSE",
                "safety_review_url": "https://github.com/sample/finance-factor-agent/security",
                "task_test_evidence_url": "https://github.com/sample/finance-factor-agent/actions",
            },
        }
        item = gate.prepare(doc, [review])["requests"][0]
        self.assertEqual(item["request_state"], "pending-independent-owner-review")
        self.assertFalse(item["approved"])
        self.assertFalse(item["authenticated_reviewer"])
        self.assertFalse(item["safety_verified"])
        self.assertFalse(item["license_cleared"])

    def test_missing_license_or_evidence_cannot_pass_request_gate(self):
        resource = entry(license="unknown")
        doc = queue([resource])
        result = gate.prepare(doc, [{
            "candidate_id": resource["id"], "url": resource["url"],
            "reviewer": "sample-reviewer", "decision": "request-promotion",
            "rationale": "Finance relevance is plausible but no independent safety evidence exists.",
            "evidence": {},
        }])["requests"][0]
        self.assertEqual(result["request_state"], "evidence-incomplete")
        self.assertIn("license_signal_unknown", result["missing_evidence"])
        self.assertIn("safety_review_url", result["missing_evidence"])

    def test_forged_or_conflicting_decisions_rejected(self):
        x=entry()
        source=queue([x])
        row={"candidate_id":"wrong", "url":x["url"], "reviewer":"three words", "decision":"defer",
             "rationale":"I have not assessed commercial licensing and the practical usefulness"}
        with self.assertRaises(ValueError):
            gate.prepare(source,[row])
        row["candidate_id"]=x["id"]
        with self.assertRaises(ValueError):
            gate.prepare(source,[row,row])

    def test_review_output_does_not_write_curated_catalog(self):
        x=entry()
        result=gate.prepare(queue([x]), [{
            "candidate_id":x["id"], "url":x["url"], "reviewer":"atlas-editor",
            "decision":"reject", "rationale":"The resource lacks reliable evidence and is not yet suitable."
        }])
        self.assertEqual(result["approval_count"], 0)
        self.assertFalse(result["auto_promoted"])
        self.assertEqual(result["requests"][0]["request_state"],"not-recommended")


if __name__ == "__main__":
    main()
