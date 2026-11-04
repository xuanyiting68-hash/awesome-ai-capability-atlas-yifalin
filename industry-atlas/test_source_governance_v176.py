#!/usr/bin/env python3
"""V1.7.6 provenance governance gates, no fake verification."""
from copy import deepcopy
from datetime import date
import json
from pathlib import Path
import unittest
from provider_contract_v174 import ContractError
from source_governance_v176 import validate_snapshot,status,build_report,compare_reports

ROOT=Path(__file__).resolve().parent
SNAP=json.loads((ROOT/"discovery_seed.json").read_text(encoding="utf-8"))
BASE=build_report(SNAP,date(2026,11,4))

class GovernanceV176(unittest.TestCase):
    def test_frozen(self):
        self.assertEqual(BASE["count"],133)
        self.assertFalse(BASE["automatically_promoted"])
        self.assertEqual(BASE["real_source_network_checks"],0)
        self.assertEqual(BASE["independent_review_count"],0)
        self.assertEqual(len(BASE["rows"]),133)
        self.assertFalse(any(r["license_verified"] or r["security_verified"] for r in BASE["rows"]))
        self.assertTrue(all(r["link_currently_accessible"] is None for r in BASE["rows"]))
    def test_no_freshness_claim(self):
        self.assertIn("cached source metadata age",BASE["warning"].lower())
        self.assertIn("availability-not-live-checked",BASE["rows"][0]["issues"])
    def test_old_metadata_warning(self):
        record=deepcopy(SNAP["records"][0])
        record["last_modified"]="2023-01-01T00:00:00Z"
        x=status(record,date(2026,11,4))
        self.assertEqual(x["metadata_age_band"],"older-than-365d")
        self.assertIn("metadata-older-than-180d",x["issues"])
        self.assertFalse(x["task_effectiveness_verified"])
    def test_future_metadata_warning(self):
        r=deepcopy(SNAP["records"][0])
        r["last_modified"]="2099-03-01"
        self.assertIn("future-metadata-date",status(r,date(2026,11,4))["issues"])
    def test_unknown_license(self):
        row=next(x for x in BASE["rows"] if x["license_signal"].lower()=="unknown")
        self.assertIn("license-signal-unknown",row["issues"])
        self.assertFalse(row["license_verified"])
    def test_reject_private_url(self):
        s=deepcopy(SNAP)
        s["records"][0]["url"]="https://127.0.0.1/x"
        s["records"][0]["source_url"]="https://127.0.0.1/x"
        with self.assertRaises(ContractError):validate_snapshot(s)
    def test_reject_auto_approval(self):
        s=deepcopy(SNAP)
        s["records"][0]["approved"]=True
        with self.assertRaises(ContractError):validate_snapshot(s)
    def test_reject_duplicate(self):
        s=deepcopy(SNAP)
        s["records"][1]["id"]=s["records"][0]["id"]
        with self.assertRaises(ContractError):validate_snapshot(s)
    def test_reject_unsafe_sector(self):
        s=deepcopy(SNAP)
        s["records"][0]["sector_ids"]=["s99"]
        with self.assertRaises(ContractError):validate_snapshot(s)
    def test_initial_baseline_not_new(self):
        z=compare_reports(None,BASE)
        self.assertEqual(z["event_counts"],{"first-baseline":133})
        self.assertFalse(z["deletions_proven"])
    def test_two_snapshots_date_only_is_unchanged(self):
        new=build_report(SNAP,date(2026,11,5))
        z=compare_reports(BASE,new)
        self.assertEqual(z["event_counts"],{"unchanged-metadata":133})
        self.assertFalse(z["deletions_proven"])
    def test_missing_in_sample_is_not_deletion(self):
        new=deepcopy(build_report(SNAP,date(2026,11,5)))
        old=new["rows"].pop()
        new["count"]-=1
        z=compare_reports(BASE,new)
        self.assertEqual(z["event_counts"]["not-observed-in-latest-snapshot"],1)
        event=next(e for e in z["events"] if e["id"]==old["id"])
        self.assertFalse(event["deleted"])
    def test_metadata_change_unapproved(self):
        s=deepcopy(SNAP)
        s["records"][0]["last_modified"]="2026-11-04T12:00:00Z"
        new=build_report(s,date(2026,11,5))
        z=compare_reports(BASE,new)
        self.assertEqual(z["event_counts"]["metadata-changed"],1)
        self.assertFalse(z["auto_promoted"])
    def test_out_of_order_comparison(self):
        with self.assertRaises(ContractError):compare_reports(BASE,BASE)
    def test_repeatability(self):
        self.assertEqual(BASE,build_report(SNAP,date(2026,11,4)))

if __name__=="__main__":unittest.main()
