#!/usr/bin/env python3
"""V1.8.0 license evidence provenance, disagreement and fail-closed review."""
import copy,json,unittest
from pathlib import Path
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from license_evidence_v180 import validate_license_files,build_license_report,compare_license_reports
ROOT=Path(__file__).resolve().parent
LEADS=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
FILES=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
S,A,P=load_data()
REPORT=build_license_report(FILES,LEADS,S,A,P)

class LicenseReviewV180(unittest.TestCase):
    def test_ten_files_two_flags(self):
        self.assertEqual(REPORT["files_observed"],10)
        self.assertEqual(REPORT["needs_signal_reconciliation"],2)
        self.assertEqual(REPORT["text_cue_aligned"],8)
        self.assertEqual(REPORT["release_gate"],"HOLD")
        self.assertEqual(REPORT["network_requests"],0)
        self.assertEqual(REPORT["legal_licenses_verified"],0)
        self.assertEqual(REPORT["dependencies_audited"],0)
        self.assertEqual(REPORT["security_audited"],0)
        self.assertEqual(REPORT["approved_sources"],0)
    def test_license_disagreement_not_resolved(self):
        flagged={x["name"]:x for x in REPORT["rows"] if x["reconciliation_status"]=="license-signal-needs-reconciliation"}
        self.assertEqual(set(flagged),{"IfcOpenShell/IfcOpenShell","opentripplanner/OpenTripPlanner"})
        self.assertEqual(flagged["opentripplanner/OpenTripPlanner"]["repo_metadata_spdx_signal"],"NOASSERTION")
        self.assertIn("LGPL",flagged["opentripplanner/OpenTripPlanner"]["textual_cue"])
        self.assertIn("GPL-3",flagged["IfcOpenShell/IfcOpenShell"]["textual_cue"])
        self.assertTrue(all(not v["license_legally_verified"] for v in flagged.values()))
    def test_snapshot_sha_is_40_lower_hex(self):
        self.assertTrue(all(len(x["license_blob_sha"])==40 for x in REPORT["rows"]))
        self.assertTrue(all(x["current_file_verified"] is False and x["source_approved"] is False for x in REPORT["rows"]))
    def test_frozen_data_untouched(self):
        originals=copy.deepcopy((S,A,P,LEADS,FILES))
        build_license_report(FILES,LEADS,S,A,P)
        self.assertEqual((S,A,P,LEADS,FILES),originals)
    def test_fail_approval(self):
        for field in ("legal_license_verified","dependency_audit_verified","security_review_verified",
                      "independent_review_approved","source_promoted"):
            mutated=copy.deepcopy(FILES)
            mutated["records"][0][field]=True
            with self.subTest(field=field),self.assertRaises(ContractError):
                validate_license_files(mutated,LEADS,S,A,P)
    def test_reconciliation_cannot_be_silenced(self):
        m=copy.deepcopy(FILES)
        row=next(x for x in m["records"] if x["repo_full_name"]=="IfcOpenShell/IfcOpenShell")
        row["signal_reconciliation_status"]="metadata-aligned-text-cue"
        with self.assertRaises(ContractError):
            validate_license_files(m,LEADS,S,A,P)
    def test_branch_and_sha_tampering_rejected(self):
        m=copy.deepcopy(FILES)
        m["records"][0]["observed_branch"]="mismatched"
        with self.assertRaises(ContractError):validate_license_files(m,LEADS,S,A,P)
        m=copy.deepcopy(FILES)
        m["records"][0]["license_blob_sha"]="unknown"
        with self.assertRaises(ContractError):validate_license_files(m,LEADS,S,A,P)
    def test_spdx_metadata_change_detected_without_approval(self):
        b=copy.deepcopy(REPORT)
        b["rows"][0]["repo_metadata_spdx_signal"]="NOASSERTION"
        delta=compare_license_reports(REPORT,b)
        self.assertEqual(delta["counts"]["repository-spdx-signal-changed-review-required"],1)
        self.assertFalse(delta["legal_validation_performed"])
    def test_file_blob_change_requires_review(self):
        b=copy.deepcopy(REPORT)
        b["rows"][0]["license_blob_sha"]="a"*40
        delta=compare_license_reports(REPORT,b)
        self.assertEqual(delta["counts"]["license-file-blob-changed-review-required"],1)
        self.assertTrue(all(not x["automatic_approval"] for x in delta["events"]))
    def test_missing_file_not_deleted(self):
        b=copy.deepcopy(REPORT)
        b["rows"].pop()
        delta=compare_license_reports(REPORT,b)
        self.assertEqual(delta["counts"]["not-in-current-sample-not-deletion"],1)
        self.assertTrue(all(not e["verified_deletion"] for e in delta["events"]))
    def test_determinism(self):
        self.assertEqual(REPORT,build_license_report(FILES,LEADS,S,A,P))
if __name__=="__main__":
    unittest.main()
