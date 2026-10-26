import csv
import json
import unittest
from pathlib import Path
from scripts.build_top30_evidence import build
ROOT=Path(__file__).resolve().parents[1]
class EvidenceTests(unittest.TestCase):
    def test_evidence_contract(self):
        with (ROOT/"data/top30_evaluation.csv").open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
        metadata=json.loads((ROOT/"data/repo_metadata.json").read_text("utf-8"))
        evidence=build(rows,metadata)
        self.assertEqual(len(evidence),30)
        self.assertTrue(all(r["fork_decision"]=="HOLD" for r in evidence))
        self.assertTrue(all(r["security_review"]=="not-audited" for r in evidence))
        self.assertTrue(all(r["license_text_review"]=="not-reviewed" for r in evidence))
        self.assertEqual(len({r["repo"].lower() for r in evidence}),30)
    def test_committed_snapshot_matches_generator(self):
        rows_path=ROOT/"data/top30_evaluation.csv"
        with rows_path.open(encoding="utf-8-sig",newline="") as f:
            rows=list(csv.DictReader(f))
        source=json.loads((ROOT/"data/repo_metadata.json").read_text("utf-8"))
        saved=json.loads((ROOT/"data/top30_evidence.json").read_text("utf-8"))
        self.assertEqual(saved["generated_from_snapshot_utc"],source["generated_at_utc"])
        self.assertEqual(saved["generated_at_utc"],source["generated_at_utc"])
        self.assertEqual(saved["projects"],build(rows,source))
        self.assertEqual(saved["approved_fork_count"],0)
        self.assertEqual(saved["reviewed_license_count"],0)

    def test_missing_metadata_fails_closed(self):
        with self.assertRaises(ValueError):
            build([{"github_repository":"x/missing","rank":"1","domain":"x","research_priority":"S","url":"https://github.com/x/missing"}],{"repositories":{}})
if __name__=="__main__":unittest.main()
