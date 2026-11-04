#!/usr/bin/env python3
"""V1.7.6 review gate: synthetic cases NEVER authorize release."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from evidence_eval_v176 import evaluate_synthetic, validate_review_packet
from provider_contract_v174 import ContractError
from rag_retrieval_v175 import load_reference_data

ROOT=Path(__file__).resolve().parent
RECORDS,TOPICS=load_reference_data()
CASES=json.loads((ROOT/"rag_eval_cases_v175.json").read_text(encoding="utf-8"))["cases"]

class EvidenceEvaluationV176(unittest.TestCase):
    def test_synthetic_metrics(self):
        d=evaluate_synthetic(CASES,RECORDS,TOPICS)
        self.assertEqual(d["hit_fraction"],"8/8")
        self.assertEqual(d["abstention_fraction"],"4/4")
        self.assertEqual(d["cases"],12)
        self.assertIsNone(d["field_precision"])
        self.assertIsNone(d["field_recall"])
        self.assertFalse(d["independent_human_reviewed"])
        self.assertEqual(d["release_gate"],"HOLD")
    def test_stratified_sectors(self):
        d=evaluate_synthetic(CASES,RECORDS,TOPICS)
        self.assertGreaterEqual(len(d["by_sector"]),5)
        self.assertTrue(any(row["case_type"]=="negative" for row in d["examples"]))
    def test_k_is_bounded(self):
        with self.assertRaises(ContractError):evaluate_synthetic(CASES,RECORDS,TOPICS,0)
        with self.assertRaises(ContractError):evaluate_synthetic(CASES,RECORDS,TOPICS,32)
    def test_duplicate_case_denied(self):
        with self.assertRaises(ContractError):evaluate_synthetic(CASES+[CASES[0]],RECORDS,TOPICS)
    def test_fake_reviewer_packet_denied(self):
        with self.assertRaises(ContractError):
            validate_review_packet({"schema_version":"1.0","source_population":"synthetic-editorial","cases":CASES})
    def test_no_consent_denied(self):
        rows=[{"id":str(i),"sector_id":"s02","consent_recorded":False,"pii_removed":True,
               "reviewer_a":"a","reviewer_b":"b","adjudicated":True,"evidence_link_checked":True,
               "is_negative":i%2==0} for i in range(25)]
        with self.assertRaises(ContractError):
            validate_review_packet({"schema_version":"1.0","source_population":"real-user-consented-anonymized","cases":rows})
    def test_structurally_valid_packet_still_hold(self):
        rows=[{"id":str(i),"sector_id":"s%02d"%(i%10+1),"consent_recorded":True,"pii_removed":True,
               "reviewer_a":"reviewer-one","reviewer_b":"reviewer-two","adjudicated":True,"evidence_link_checked":True,
               "is_negative":i%3==0} for i in range(30)]
        x=validate_review_packet({"schema_version":"1.0","source_population":"real-user-consented-anonymized","cases":rows})
        self.assertEqual(x["release_gate"],"HOLD")
        self.assertFalse(x["authenticity_proven"])
        self.assertEqual(x["sectors"],10)
    def test_bad_reviewer_denied(self):
        rows=[{"id":str(i),"sector_id":"s02","consent_recorded":True,"pii_removed":True,
               "reviewer_a":"x","reviewer_b":"x","adjudicated":True,"evidence_link_checked":True,
               "is_negative":False} for i in range(25)]
        with self.assertRaises(ContractError):
            validate_review_packet({"schema_version":"1.0","source_population":"real-user-consented-anonymized","cases":rows})

if __name__=="__main__":unittest.main()
