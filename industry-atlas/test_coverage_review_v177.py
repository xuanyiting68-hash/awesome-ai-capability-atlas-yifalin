#!/usr/bin/env python3
"""V1.7.7 sector review: no auto-approval, no invented sector evidence."""
import copy
import json
import unittest
from provider_contract_v174 import ContractError
from coverage_review_v177 import generate_review, load_data

SNAP, ATLAS, RULES = load_data()

class CoverageV177(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate_review(SNAP, ATLAS, RULES)
    def test_snapshot_and_32_sectors(self):
        x=self.data
        self.assertEqual(x["total_records"],133)
        self.assertEqual(x["without_declared_industry"],69)
        self.assertEqual(len(x["sectors"]),32)
        self.assertEqual(x["existing_editorial_tagged_sectors"],4)
        self.assertGreater(x["proposal_only_sectors"],0)
    def test_does_not_write_existing_tags_or_source_snapshot(self):
        before=copy.deepcopy(SNAP)
        generate_review(SNAP,ATLAS,RULES)
        self.assertEqual(SNAP,before)
        self.assertEqual(sum(bool(r["sector_ids"]) for r in SNAP["records"]),64)
    def test_proposals_are_only_unmapped(self):
        by_id={r["id"]:r for r in SNAP["records"]}
        for p in self.data["proposals"]:
            self.assertEqual(by_id[p["record_id"]]["sector_ids"],[])
            self.assertEqual(p["approved"],False)
            self.assertFalse(p["license_verified"])
            self.assertFalse(p["security_verified"])
            self.assertFalse(p["link_checked_live"])
            self.assertEqual(p["review_status"],"unapproved-sector-proposal")
        self.assertEqual(self.data["automatic_promotions"],0)
        self.assertEqual(self.data["real_source_checks"],0)
    def test_topic_rule_exact_and_no_fallback(self):
        chosen=next(x for x in self.data["proposals"] if x["topic"]=="AI视频制作")
        self.assertIn("s28",chosen["proposed_sector_ids"])
        self.assertNotIn("s21",chosen["proposed_sector_ids"])
        # Unknown topic remains unmapped and is never guessed from a name.
        altered=copy.deepcopy(SNAP)
        item=next(x for x in altered["records"] if not x["sector_ids"])
        item["topic"]="unmapped new unknown topic"
        result=generate_review(altered,ATLAS,RULES)
        self.assertNotIn(item["id"],{x["record_id"] for x in result["proposals"]})
    def test_proposal_only_does_not_become_declared(self):
        s=next(x for x in self.data["sectors"] if x["sector_id"]=="s28")
        self.assertEqual(s["declared_editorial"],0)
        self.assertGreater(s["unreviewed_proposals"],0)
        self.assertEqual(s["coverage_state"],"proposals-only")
        self.assertEqual(s["verified_sources"],0)
    def test_sector_with_no_candidate_is_not_filled(self):
        s=next(x for x in self.data["sectors"] if x["sector_id"]=="s19")
        self.assertEqual(s["coverage_state"],"no-records")
        self.assertEqual(s["unreviewed_proposals"],0)
    def test_duplicate_rules_rejected(self):
        rules=copy.deepcopy(RULES)
        rules["rules"].append(copy.deepcopy(rules["rules"][0]))
        with self.assertRaises(ContractError):generate_review(SNAP,ATLAS,rules)
    def test_bad_sector_rule_rejected(self):
        rules=copy.deepcopy(RULES)
        rules["rules"][0]["sector_ids"]=["s99"]
        with self.assertRaises(ContractError):generate_review(SNAP,ATLAS,rules)
    def test_approved_source_rejected(self):
        snap=copy.deepcopy(SNAP)
        snap["records"][0]["approved"]=True
        with self.assertRaises(ContractError):generate_review(snap,ATLAS,RULES)
    def test_unsafe_url_rejected(self):
        snap=copy.deepcopy(SNAP)
        snap["records"][0]["url"]=snap["records"][0]["source_url"]="https://127.0.0.1/private"
        with self.assertRaises(ContractError):generate_review(snap,ATLAS,RULES)
    def test_duplicate_id_rejected(self):
        snap=copy.deepcopy(SNAP)
        snap["records"][1]["id"]=snap["records"][0]["id"]
        with self.assertRaises(ContractError):generate_review(snap,ATLAS,RULES)
    def test_reproducible(self):
        self.assertEqual(self.data,generate_review(SNAP,ATLAS,RULES))
    def test_atlas_original_untouched(self):
        self.assertEqual((len(ATLAS["sectors"]),len(ATLAS["subdomains"]),len(ATLAS["tools"]),len(ATLAS["learning"])),(32,133,114,69))

if __name__=="__main__":
    unittest.main()
