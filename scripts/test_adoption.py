"""Star Pack adoption identity and conservative promotion tests.

No GitHub account activity in any test.
"""
import copy
import csv
import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
from scripts.validate_adoption import ROOT, check_adoption, validate_from_files
from scripts.star_atlas_repos import get_targets, main


class AdoptionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((ROOT / "data/adoption_plan.json").read_text("utf-8"))
        cls.briefs = json.loads((ROOT / "data/research_briefs.json").read_text("utf-8"))
        with (ROOT / "data/top30_evaluation.csv").open(encoding="utf-8-sig", newline="") as f:
            cls.rows = list(csv.DictReader(f))

    def verify(self, plan):
        return check_adoption(plan, self.rows, self.briefs)

    def test_real_manifest_is_complete_and_honest(self):
        self.assertEqual(self.verify(self.plan), {
            "star_shortlist_count":30, "priority_integration_candidates":8,
            "fork_approved_count":0, "star_actions_executed_by_atlas":0})
        self.assertEqual(validate_from_files()["priority_integration_candidates"],8)

    def test_all_bookmarks_have_canonical_upstream(self):
        targets = get_targets()
        self.assertEqual(len(targets),30)
        self.assertEqual(len({r.lower() for r in targets}),30)
        self.assertIn("openbq-org/OpenBB",targets)
        self.assertIn("OpenHands/OpenHands",targets)
        self.assertNotIn("OpenBB-finance/OpenBB",targets)
        self.assertEqual(len(get_targets(priority_only=True)),8)

    def test_stars_are_not_claimed_executed(self):
        broken = copy.deepcopy(self.plan)
        broken["items"][0]["star_execution"] = "completed"
        with self.assertRaisesRegex(ValueError, "promotion"):
            self.verify(broken)

    def test_fork_cannot_be_faked(self):
        broken = copy.deepcopy(self.plan)
        broken["items"][0]["fork"] = "APPROVED"
        with self.assertRaisesRegex(ValueError, "promotion"):
            self.verify(broken)

    def test_integration_cannot_be_faked(self):
        broken = copy.deepcopy(self.plan)
        broken["items"][0]["integration_state"] = "production"
        with self.assertRaisesRegex(ValueError, "promotion"):
            self.verify(broken)

    def test_slug_and_canonical_spoofing_rejected(self):
        for malicious in ("evil.invalid/Other", "../issue", "https://example.com", "microsoft/not-the-repo"):
            with self.subTest(malicious=malicious):
                broken = copy.deepcopy(self.plan)
                broken["items"][0]["canonical_repo"] = malicious
                with self.assertRaisesRegex(ValueError, "canonical"):
                    self.verify(broken)

    def test_duplicate_project_rejected(self):
        broken = copy.deepcopy(self.plan)
        broken["items"][1] = copy.deepcopy(broken["items"][0])
        with self.assertRaisesRegex(ValueError,"duplicate"):
            self.verify(broken)

    def test_priority_needs_bilingual_justification(self):
        broken = copy.deepcopy(self.plan)
        item = next(i for i in broken["items"] if i["priority"] == "P0")
        item["pilot_fit"]["en"] = "unsafe"
        with self.assertRaisesRegex(ValueError, "bilingual"):
            self.verify(broken)

    def test_cli_default_preview_never_uses_gh(self):
        out = io.StringIO()
        with patch("scripts.star_atlas_repos.subprocess.run") as process:
            with redirect_stdout(out):
                result = main([])
        self.assertEqual(result,0)
        process.assert_not_called()
        self.assertIn("DRY RUN",out.getvalue())
        self.assertIn("30 repositories ready; 0 Star actions executed.",out.getvalue())

    def test_cli_priority_preview_only_eight(self):
        out = io.StringIO()
        with patch("scripts.star_atlas_repos.subprocess.run") as process:
            with redirect_stdout(out):
                result = main(["--priority-only"])
        self.assertEqual(result,0)
        process.assert_not_called()
        self.assertIn("8 repositories ready; 0 Star actions executed.",out.getvalue())


if __name__ == "__main__":
    unittest.main()
