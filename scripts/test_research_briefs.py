"""Evidence research tier and provenance regression tests."""
import copy
import csv
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from scripts.validate_research_briefs import validate_briefs

ROOT=Path(__file__).resolve().parents[1]
AS_OF=datetime(2026,10,30,tzinfo=timezone.utc)

class BriefQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.briefs=json.loads((ROOT/"data/research_briefs.json").read_text("utf-8"))
        with (ROOT/"data/top30_evaluation.csv").open(encoding="utf-8-sig",newline="") as s:
            cls.csv=list(csv.DictReader(s))
        cls.snapshot=json.loads((ROOT/"data/top30_evidence.json").read_text("utf-8"))
        cls.metadata=json.loads((ROOT/"data/repo_metadata.json").read_text("utf-8"))
    def verify(self, records):
        return validate_briefs(records,self.csv,self.snapshot,self.metadata,AS_OF)
    def test_four_grounded_editorial_briefs(self):
        summary=self.verify(self.briefs)
        self.assertEqual(summary,{"count":30,"curated":30,"reviewed":0,
                                  "reproduced":0,"production_candidates":0})
    def test_promotions_require_new_evidence_not_stars(self):
        for tier in ("Reviewed","Reproduced","Production Candidate"):
            with self.subTest(tier=tier):
                d=copy.deepcopy(self.briefs)
                d["entries"][0]["tier"]=tier
                with self.assertRaisesRegex(ValueError,"promotion"):self.verify(d)
    def test_prevent_false_license_or_fork_clearance(self):
        for field,value in (("license_text","reviewed"),("security","audited"),
                            ("reproducibility","reproduced"),("fork_decision","APPROVED"),
                            ("sandbox_sha","a"*40)):
            with self.subTest(field=field):
                d=copy.deepcopy(self.briefs)
                d["entries"][0]["review"][field]=value
                with self.assertRaisesRegex(ValueError,"promotion"):self.verify(d)
    def test_block_untrusted_documentation_host(self):
        for url in ("https://phishing.example/docs","javascript:alert(1)",
                    "https://docs.langchain.com.evil.example/docs",
                    "https://user:pass@docs.langchain.com/oss/python/langgraph/overview",
                    "http://docs.langchain.com/oss/python/langgraph/overview"):
            with self.subTest(url=url):
                d=copy.deepcopy(self.briefs)
                d["entries"][1]["sources"][1]["url"]=url
                with self.assertRaisesRegex(ValueError,"allowlisted"):self.verify(d)
    def test_source_blob_pin_is_not_optional(self):
        for invalid in ("", "not-a-git-blob","1"*39,"g"*40):
            d=copy.deepcopy(self.briefs)
            d["entries"][2]["sources"][0]["git_blob_sha"]=invalid
            with self.assertRaisesRegex(ValueError,"README blob"):self.verify(d)
    def test_master_branch_identity_for_faster_whisper(self):
        candidates=self.briefs["entries"]
        faster=next(e for e in candidates if e["repo"]=="SYSTRAN/faster-whisper")
        self.assertEqual(faster["sources"][0]["readme_ref"],"master")
        self.assertIn("/blob/master/README.md",faster["sources"][0]["url"])
        changed=copy.deepcopy(self.briefs)
        record=next(e for e in changed["entries"] if e["repo"]=="SYSTRAN/faster-whisper")
        record["sources"][0]["readme_ref"]="main"
        with self.assertRaisesRegex(ValueError,"README ref does not match verified default branch"):
            self.verify(changed)

    def test_all_thirty_have_unique_official_source_briefs(self):
        self.assertEqual(len(self.briefs["entries"]),30)
        expected={x["github_repository"].lower() for x in self.csv}
        actual={x["repo"].lower() for x in self.briefs["entries"]}
        self.assertEqual(actual,expected)
        self.verify(self.briefs)

    def test_canonical_owner_aliases_are_audited(self):
        for name in ("OpenBB-finance/OpenBB","All-Hands-AI/OpenHands"):
            with self.subTest(name=name):
                record=next(x for x in self.briefs["entries"] if x["repo"]==name)
                self.assertNotEqual(record["sources"][0]["canonical_repo"].lower(),name.lower())
                self.assertEqual(record["review"]["fork_decision"],"HOLD")
                corrupted=copy.deepcopy(self.briefs)
                chosen=next(x for x in corrupted["entries"] if x["repo"]==name)
                chosen["sources"][0]["canonical_repo"]=name
                with self.assertRaisesRegex(ValueError,"migration"):
                    self.verify(corrupted)

    def test_default_branch_and_cased_readme_are_pinned(self):
        for repo,branch,filename in [
            ("OpenBB-finance/OpenBB","develop","README.md"),
            ("QuantConnect/Lean","master","readme.md"),
            ("n8n-io/n8n","master","README.md"),
            ("chatwoot/chatwoot","develop","README.md"),
        ]:
            with self.subTest(repo=repo):
                record=next(x for x in self.briefs["entries"] if x["repo"]==repo)
                self.assertEqual(record["sources"][0]["readme_ref"],branch)
                self.assertEqual(record["sources"][0].get("readme_filename","README.md"),filename)
                corrupted=copy.deepcopy(self.briefs)
                chosen=next(x for x in corrupted["entries"] if x["repo"]==repo)
                chosen["sources"][0]["readme_filename"]="FAKE.md"
                with self.assertRaisesRegex(ValueError,"filename"):
                    self.verify(corrupted)

    def test_repository_guide_must_point_to_canonical_upstream(self):
        corrupted=copy.deepcopy(self.briefs)
        chosen=next(x for x in corrupted["entries"] if x["repo"]=="AI4Finance-Foundation/FinRobot")
        chosen["sources"][1]["url"]="https://github.com/other-org/other-repo"
        with self.assertRaisesRegex(ValueError,"canonical repo"):
            self.verify(corrupted)

    def test_source_blob_mismatch_rejected(self):
        d=copy.deepcopy(self.briefs)
        d["entries"][0]["sources"][0]["snapshot_url"]="https://api.github.com/repos/microsoft/qlib/git/blobs/"+"0"*40
        with self.assertRaisesRegex(ValueError,"immutable"):self.verify(d)
    def test_no_orphan_or_duplicate_repositories(self):
        for repo in ("unknown/ghost","microsoft/qlib"):
            d=copy.deepcopy(self.briefs)
            d["entries"][1]["repo"]=repo
            with self.assertRaises(ValueError):self.verify(d)
    def test_no_ungrounded_capability_claims(self):
        for ids in ([],["ghost"]):
            d=copy.deepcopy(self.briefs)
            d["entries"][3]["capabilities"][0]["source_ids"]=ids
            with self.assertRaisesRegex(ValueError,"without official source"):self.verify(d)
    def test_missing_bilingual_content_fails(self):
        d=copy.deepcopy(self.briefs)
        del d["entries"][0]["pilot"]["steps"][0]["en"]
        with self.assertRaisesRegex(ValueError,"pilot steps"):self.verify(d)
    def test_incomplete_pilot_or_review_contradiction_fails(self):
        d=copy.deepcopy(self.briefs)
        d["entries"][0]["pilot"]["steps"]=[]
        with self.assertRaisesRegex(ValueError,"pilot steps"):self.verify(d)
        conflicting=copy.deepcopy(self.snapshot)
        conflicting["projects"][0]["security_review"]="audited"
        with self.assertRaisesRegex(ValueError,"evidence conflicts"):
            validate_briefs(self.briefs,self.csv,conflicting,self.metadata,AS_OF)
    def test_invalid_future_timestamp_fails(self):
        d=copy.deepcopy(self.briefs)
        d["researched_at_utc"]="2100-01-01T00:00:00Z"
        with self.assertRaisesRegex(ValueError,"future"):self.verify(d)

if __name__=="__main__":
    unittest.main()
