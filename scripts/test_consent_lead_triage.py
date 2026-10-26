"""Deterministic consent gate test; runs in the normal no-network CI test suite."""
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from examples.consent_lead_triage.run_demo import triage_records

ROOT = Path(__file__).resolve().parents[1]
AS_OF = datetime(2026, 10, 27, tzinfo=timezone.utc)

class ConsentTriageTests(unittest.TestCase):
    def test_synthetic_end_to_end_counts_and_no_external_actions(self):
        rows = json.loads((ROOT / "examples/consent_lead_triage/synthetic_leads.json").read_text("utf-8"))
        result = triage_records(rows, AS_OF)
        self.assertEqual((result["input_count"], result["eligible_count"], result["blocked_count"]), (8, 3, 5))
        self.assertEqual(result["external_actions"], 0)
        self.assertEqual([x["lead_id"] for x in result["human_review_queue"]],
                         ["demo-001", "demo-006", "demo-007"])
        self.assertEqual(result["blocked_reasons"]["duplicate_or_conflicting_record"], 2)
        self.assertEqual(result["human_review_queue"][0]["category"], "video")
        self.assertEqual(result["human_review_queue"][1]["category"], "finance_research")
        self.assertNotIn("question", json.dumps(result))
        self.assertNotIn("contact_at", json.dumps(result))

    def test_actual_cli_output_is_deterministic(self):
        cmd = [sys.executable, str(ROOT / "examples/consent_lead_triage/run_demo.py"),
               str(ROOT / "examples/consent_lead_triage/synthetic_leads.json"),
               "--as-of", "2026-10-27T00:00:00Z"]
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        result = json.loads(proc.stdout)
        self.assertEqual(result["eligible_count"], 3)
        self.assertEqual(result["external_actions"], 0)
        self.assertEqual(result["blocked_count"], 5)

    def test_explicit_bool_purpose_revocation_and_future_consent(self):
        valid = {"lead_id":"id1", "consent":True, "consent_purpose":"contact_requested",
                 "consent_at":"2026-10-26T00:00:00Z", "opt_out":False, "question":"CRM"}
        invalid = [
            {**valid, "lead_id":"no1", "consent":"true"},
            {**valid, "lead_id":"no2", "consent_purpose":"newsletter"},
            {**valid, "lead_id":"no3", "opt_out":True},
            {**valid, "lead_id":"no4", "consent_at":"2027-01-01T00:00:00Z"},
            {**valid, "lead_id":"no5", "consent_at":"2026-10-26"},
            {**valid, "lead_id":"sensitive@example.com"},
            {**valid, "lead_id":"no7", "opt_out":"false"},
            {**valid, "lead_id":"no8", "opt_out":None},
            {k:v for k,v in {**valid, "lead_id":"no9"}.items() if k != "opt_out"},
        ]
        result = triage_records([valid]+invalid, AS_OF)
        self.assertEqual(result["eligible_count"],1)
        self.assertEqual(result["blocked_count"],len(invalid))

    def test_conflicting_consent_fails_closed(self):
        row = {"lead_id":"id7","consent":True,"consent_purpose":"contact_requested",
               "consent_at":"2026-10-26T00:00:00Z","question":"video"}
        result = triage_records([row, {**row, "consent":False,"opt_out":True}], AS_OF)
        self.assertEqual(result["eligible_count"],0)
        self.assertEqual(result["blocked_reasons"]["duplicate_or_conflicting_record"],2)

if __name__ == "__main__":
    unittest.main()
