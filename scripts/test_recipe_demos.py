"""Deterministic first-party recipe demo tests; no third-party SDK or model."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from examples.recipe_demos.run_demo import (ROOT, education_demo, finance_demo,
                                             leads_demo, run_from_files)
from scripts.verify_recipe_demos import verify_from_files, verify_independent_subprocesses


class RecipeDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixtures=json.loads((ROOT/"examples/recipe_demos/synthetic_fixtures.json").read_text("utf-8"))

    def test_three_real_first_party_outputs_match_frozen_contract(self):
        report=verify_from_files()
        self.assertEqual(report["all_scenarios"],["leads","education","finance"])
        self.assertEqual(report["verified_3rd_party_integrations"],0)
        self.assertEqual(report["real_orders"],0)
        self.assertEqual(report["network_requests"],0)
        self.assertIn("FIRST-PARTY",report["disclaimer"])

    def test_cli_round_trip_independent_process(self):
        out=verify_independent_subprocesses()
        self.assertEqual(out["processes"],4)
        self.assertTrue(out["all_cases_match"])

    def test_leads_revocation_and_conflicting_ids_fail_closed(self):
        row={"lead_id":"demo-clean","consent":True,"consent_purpose":"contact_requested",
             "consent_at":"2026-10-26T00:00:00Z","opt_out":False,"question":"video"}
        report=leads_demo([row,{**row,"opt_out":True}, {**row,"lead_id":"another","consent":False}])
        self.assertEqual(report["eligible_count"],0)
        self.assertEqual(report["blocked_count"],3)
        self.assertEqual(report["outbound_messages"],0)
        self.assertNotIn("question",json.dumps(report))

    def test_education_fabricated_or_wrong_citation_is_rejected(self):
        data=copy.deepcopy(self.fixtures["education"])
        data["questions"][0]["answer_span"]="employment guaranteed by OpenAI"
        with self.assertRaisesRegex(ValueError,"fabricated"): education_demo(data)
        other=copy.deepcopy(self.fixtures["education"])
        other["questions"][0]["source_id"]="lesson-03"
        with self.assertRaisesRegex(ValueError,"mismatched"): education_demo(other)

    def test_education_invalid_duplicate_question_and_no_hallucinated_answer(self):
        data=copy.deepcopy(self.fixtures["education"])
        data["questions"][1]["question_id"]=data["questions"][0]["question_id"]
        with self.assertRaisesRegex(ValueError,"duplicate"):education_demo(data)
        observed=education_demo(self.fixtures["education"])
        self.assertEqual(observed["abstained_count"],1)
        self.assertEqual(observed["generated_answers"],0)
        self.assertIsNone(observed["responses"][-1]["answer"])

    def test_finance_only_prior_observations_reach_prediction(self):
        report=finance_demo(self.fixtures["finance"])
        self.assertEqual(report["holdout_decisions"],9)
        self.assertEqual(report["roundtrip_cost_bps"],"16.00")
        self.assertEqual(report["gross_bps_sum"],"10.21")
        self.assertEqual(report["net_bps_sum"],"-133.79")
        self.assertEqual(report["has_predictive_edge"],"not_established")
        self.assertTrue(all(r["max_predictor_index"]<r["decision_index"]
                            and r["broker_order_sent"] is False
                            for r in report["evaluated_decisions"]))
        self.assertEqual(report["broker_orders"],0)

    def test_finance_safety_negative_controls(self):
        data=copy.deepcopy(self.fixtures["finance"])
        data["prices"][-1]="NaN"
        with self.assertRaisesRegex(ValueError,"non-finite"):finance_demo(data)
        data=copy.deepcopy(self.fixtures["finance"])
        data["cost_bps"]["commission"]="-1"
        with self.assertRaisesRegex(ValueError,"cost"):finance_demo(data)
        data=copy.deepcopy(self.fixtures["finance"])
        data["symbol"]="XAUUSD_LIVE"
        with self.assertRaisesRegex(ValueError,"synthetic"):finance_demo(data)
        data=copy.deepcopy(self.fixtures["finance"])
        data["train_end_index"]=len(data["prices"])-2
        with self.assertRaisesRegex(ValueError,"holdout"):finance_demo(data)

    def test_forged_expected_output_cannot_pass_publication_contract(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for relative in ("examples/recipe_demos/synthetic_fixtures.json",
                             "examples/consent_lead_triage/synthetic_leads.json",
                             "data/recipe_demo_contract.json"):
                dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes((ROOT/relative).read_bytes())
            contract=root/"data/recipe_demo_contract.json"
            data=json.loads(contract.read_text("utf-8"))
            data["cases"]["finance"]["net_bps_sum"]="999999.99"
            contract.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"demo evidence mismatch"):verify_from_files(root)


if __name__=="__main__":
    unittest.main()
