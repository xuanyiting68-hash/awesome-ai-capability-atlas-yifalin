#!/usr/bin/env python3
"""V1.7.9 public repo observation ledger fail-closed governance tests."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from external_leads_v179 import validate_ledger,make_review_report,compare_observations

ROOT=Path(__file__).resolve().parent
BASE=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
S,A,P=load_data()
REPORT=make_review_report(BASE,S,A,P)

class ExternalLeadsV179(unittest.TestCase):
    def test_10_distinct_gaps(self):
        self.assertEqual(REPORT["source_leads"],10)
        self.assertEqual(REPORT["external_sector_leads"],10)
        self.assertEqual(REPORT["source_gap_sectors_in_frozen_radar"],20)
        self.assertEqual(len(set(x["sector_id"] for x in REPORT["rows"])),10)
        self.assertEqual(REPORT["frozen_radar_sources_added"],0)
        self.assertEqual(REPORT["network_requests_during_report"],0)
        self.assertEqual(REPORT["release_gate"],"HOLD")
    def test_zero_claims(self):
        self.assertTrue(all(x["review_status"]=="research-lead-unapproved" for x in REPORT["rows"]))
        self.assertTrue(all(x["approval"] is False and x["license_verified"] is False
                            and x["security_verified"] is False and x["task_verified"] is False
                            and x["live_available_now"] is None for x in REPORT["rows"]))
        self.assertEqual(REPORT["verified_source_count"],0)
        self.assertEqual(REPORT["approved_source_count"],0)
    def test_noassertion_is_not_no_license(self):
        row=next(x for x in REPORT["rows"] if x["name"]=="opentripplanner/OpenTripPlanner")
        self.assertEqual(row["license_spdx_signal"],"NOASSERTION")
        self.assertIn("github-spdx-not-asserted",row["issues"])
        self.assertFalse(row["license_verified"])
    def test_metadata_date_is_not_live_now(self):
        self.assertEqual(REPORT["observation_date"],"2026-11-04")
        self.assertTrue(all(x["last_pushed_age_days_at_observation"]>=0 for x in REPORT["rows"]))
        self.assertTrue(all(x["live_available_now"] is None for x in REPORT["rows"]))
    def test_no_original_data_mutation(self):
        previous=(deepcopy(BASE),deepcopy(S),deepcopy(A),deepcopy(P))
        make_review_report(BASE,S,A,P)
        self.assertEqual((BASE,S,A,P),previous)
    def test_duplicate_source_id_denied(self):
        b=deepcopy(BASE)
        b["records"][1]["id"]=b["records"][0]["id"]
        with self.assertRaises(ContractError):validate_ledger(b,S,A,P)
    def test_wrong_api_url_denied(self):
        b=deepcopy(BASE)
        b["records"][0]["metadata_api_url"]="https://api.github.com/repos/another/repo"
        with self.assertRaises(ContractError):validate_ledger(b,S,A,P)
    def test_private_endpoint_denied(self):
        b=deepcopy(BASE)
        b["records"][0]["repo_url"]="https://127.0.0.1/local"
        with self.assertRaises(ContractError):validate_ledger(b,S,A,P)
    def test_https_credentials_denied(self):
        b=deepcopy(BASE)
        b["records"][0]["repo_url"]="https://user:password@github.com/OHIF/Viewers"
        with self.assertRaises(ContractError):validate_ledger(b,S,A,P)
    def test_no_auto_promotion(self):
        for key,value in (("auto_promoted",True),("independent_license_check",True),
                          ("task_suitability_checked",True),("review_state","approved")):
            b=deepcopy(BASE)
            b["records"][0][key]=value
            with self.subTest(key=key),self.assertRaises(ContractError):
                validate_ledger(b,S,A,P)
    def test_future_date_denied(self):
        b=deepcopy(BASE)
        b["records"][0]["observed_metadata"]["pushed_at"]="2099-01-01T00:00:00Z"
        with self.assertRaises(ContractError):validate_ledger(b,S,A,P)
    def test_already_in_frozen_source_denied(self):
        b=deepcopy(BASE)
        b["records"][0]["sector_id"]="s02"
        with self.assertRaises(ContractError):validate_ledger(b,S,A,P)
    def test_status_change_is_not_license_approval(self):
        newer=deepcopy(REPORT)
        newer["rows"][0]["license_spdx_signal"]="UNKNOWN"
        compare=compare_observations(REPORT,newer)
        self.assertEqual(compare["counts"]["metadata-changed"],1)
        self.assertFalse(compare["automatic_approval"])
        self.assertTrue(all(e["approval"]=="unapproved" for e in compare["events"]))
    def test_missing_sample_is_not_deleted(self):
        newer=deepcopy(REPORT)
        removed=newer["rows"].pop()
        compare=compare_observations(REPORT,newer)
        item=next(x for x in compare["events"] if x["id"]==removed["id"])
        self.assertEqual(item["kind"],"not-seen-in-latest-sample")
        self.assertFalse(item["deletion_verified"])
    def test_report_repeatable(self):
        self.assertEqual(REPORT,make_review_report(BASE,S,A,P))

if __name__=="__main__":
    unittest.main()
