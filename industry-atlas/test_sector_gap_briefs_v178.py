#!/usr/bin/env python3
"""V1.7.8 sector discovery research gaps and pagination contracts."""
import copy
import unittest
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from sector_gap_briefs_v178 import build_gap_briefs

S,A,P=load_data()

class GapBriefsV178(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=build_gap_briefs(S,A,P)
    def test_20_gaps(self):
        x=self.report
        self.assertEqual(x["no_candidate_sectors"],20)
        self.assertEqual(x["covered_by_editorial_tags"],4)
        self.assertEqual(x["proposal_only_sectors"],8)
        self.assertEqual(len(x["briefs"]),20)
        self.assertFalse(x["model_called"])
        self.assertEqual(x["live_requests"],0)
        self.assertEqual(x["new_licensed_sources"],0)
        self.assertEqual(x["auto_approved"],0)
        self.assertEqual(x["release_gate"],"HOLD")
    def test_pure_editorial_task_references(self):
        for b in self.report["briefs"]:
            self.assertEqual(b["coverage_state"],"no-source-candidate")
            self.assertEqual(b["suggested_source_count"],0)
            self.assertFalse(b["human_verified"])
            self.assertTrue(b["editorial_domains"])
            self.assertTrue(b["editorial_workflows"])
            for d in b["editorial_domains"]:
                self.assertEqual(d["classification"],"existing-editorial-task-not-an-external-source")
                self.assertTrue(d["id"].startswith(b["sector_id"]+"-"))
            for w in b["editorial_workflows"]:
                self.assertEqual(w["classification"],"existing-editorial-workflow-not-an-external-source")
                self.assertTrue(w["id"].startswith(b["sector_id"]+"-"))
    def test_target_gaps_explicit(self):
        names={b["sector_name"] for b in self.report["briefs"]}
        for name in ("银行与金融服务","医疗服务","工业制造","法律服务","会计税务与审计","政府与公共服务"):
            self.assertIn(name,names)
    def test_no_original_catalog_mutation(self):
        old=(copy.deepcopy(S),copy.deepcopy(A),copy.deepcopy(P))
        build_gap_briefs(S,A,P)
        self.assertEqual((S,A,P),old)
    def test_determinism(self):
        self.assertEqual(self.report,build_gap_briefs(S,A,P))
    def test_baseline_contract(self):
        changed=copy.deepcopy(A)
        changed["workflows"].pop()
        with self.assertRaises(ContractError):
            build_gap_briefs(S,changed,P)

if __name__=="__main__":
    unittest.main()
