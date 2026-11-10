#!/usr/bin/env python3
"""V1.8.1 negative safety and proof-boundary tests for Git tree evidence."""
import copy,json,unittest
from pathlib import Path
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from supply_chain_review_v181 import validate_supply_chain,build_report,compare_reports
ROOT=Path(__file__).resolve().parent
E=json.loads((ROOT/"supply_chain_evidence_v181.json").read_text(encoding="utf-8"))
L=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
F=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
S,A,P=load_data()
REPORT=build_report(E,L,F,S,A,P)
def rejected(e):
    with unittest.TestCase().assertRaises(ContractError):
        validate_supply_chain(e,L,F,S,A,P)
class SupplyChainV181(unittest.TestCase):
    def test_honest_counts(self):
        self.assertEqual(REPORT["projects"],10)
        self.assertEqual(REPORT["selected_dependency_paths"],15)
        self.assertEqual(REPORT["projects_with_selected_dependency_paths"],9)
        self.assertEqual(REPORT["selected_security_policy_paths"],2)
        self.assertEqual(REPORT["license_signal_discrepancies"],2)
        self.assertEqual(REPORT["cve_scans_completed"],0)
        self.assertEqual(REPORT["security_approvals"],0)
        self.assertEqual(REPORT["network_requests"],0)
        self.assertEqual(REPORT["release_gate"],"HOLD")
    def test_security_policy_not_approval(self):
        found={x["repo_name"] for x in REPORT["records"] if x["selected_security_policy_file"]}
        self.assertEqual(found,{"commaai/openpilot","open5gs/open5gs"})
        self.assertTrue(all(x["cve_clear"] is None and x["security_approved"] is False for x in REPORT["records"]))
    def test_no_path_does_not_imply_no_dependencies(self):
        row=next(x for x in REPORT["records"] if x["repo_name"]=="VROOM-Project/vroom")
        self.assertFalse(row["selected_dependency_files"])
        self.assertIn("no-selected-conventional-dependency-file-not-proof-of-absence",row["review_flags"])
    def test_reject_certification_flags(self):
        for field in ("dependency_inventory_complete","sbom_generated","vulnerability_scan_performed",
                      "security_policy_effectiveness_verified","dependencies_license_verified",
                      "automated_risk_classification_approved","source_promoted"):
            t=copy.deepcopy(E);t["records"][0][field]=True
            with self.subTest(field=field):
                rejected(t)
    def test_reject_fake_sha(self):
        t=copy.deepcopy(E);t["records"][0]["git_tree_sha"]="unknown";rejected(t)
        t=copy.deepcopy(E);t["records"][0]["selected_dependency_files"][0]["sha"]="a"*39;rejected(t)
    def test_reject_url_identity_spoof(self):
        t=copy.deepcopy(E);t["records"][0]["selected_dependency_files"][0]["url"]="https://evil.example/file";rejected(t)
        t=copy.deepcopy(E);t["records"][0]["selected_dependency_files"][0]["path"]="../a";rejected(t)
    def test_reject_duplicate_or_missing_security_file(self):
        t=copy.deepcopy(E);t["records"][2]["selected_security_policy_file"]=None;rejected(t)
        t=copy.deepcopy(E);t["records"][0]["id"]=t["records"][1]["id"];rejected(t)
    def test_drift_not_vulnerability_clearance(self):
        new=copy.deepcopy(REPORT);new["records"][0]["source_tree_sha"]="f"*40
        delta=compare_reports(REPORT,new)
        self.assertEqual(delta["counts"]["source-tree-drift-review"],1)
        self.assertFalse(delta["auto_approved"])
        self.assertTrue(all(x["source_approved"] is False for x in delta["events"]))
    def test_partial_sample_is_not_verified_deletion(self):
        new=copy.deepcopy(REPORT);new["records"].pop()
        delta=compare_reports(REPORT,new)
        self.assertEqual(delta["counts"]["missing-in-current-sample-not-deletion"],1)
        self.assertTrue(all(not x["source_deletion_verified"] for x in delta["events"]))
    def test_deterministic_and_originals_untouched(self):
        baseline=copy.deepcopy((E,L,F,S,A,P))
        self.assertEqual(REPORT,build_report(E,L,F,S,A,P))
        self.assertEqual(baseline,(E,L,F,S,A,P))
if __name__=="__main__":
    unittest.main()
