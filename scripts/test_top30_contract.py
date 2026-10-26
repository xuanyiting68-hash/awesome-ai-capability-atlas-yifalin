"""Static contract tests for Top 30 Atlas. No remote execution or dependencies."""
import csv
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


class Top30ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "data/top30_evaluation.csv").open(encoding="utf-8-sig", newline="") as file:
            cls.rows = list(csv.DictReader(file))
        cls.metadata = json.loads((ROOT / "data/repo_metadata.json").read_text(encoding="utf-8"))
        cls.page = (ROOT / "top30.html").read_text(encoding="utf-8")
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.detail = (ROOT / "project.html").read_text(encoding="utf-8")

    def test_count_unique_repo_and_rank(self):
        self.assertEqual(len(self.rows), 30)
        self.assertEqual({int(r["rank"]) for r in self.rows}, set(range(1, 31)))
        self.assertEqual(len({r["github_repository"].lower() for r in self.rows}), 30)

    def test_repository_url_and_metadata_coverage(self):
        repos = self.metadata["repositories"]
        for r in self.rows:
            with self.subTest(repo=r["github_repository"]):
                slug = r["github_repository"]
                self.assertRegex(slug, r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
                url = urlparse(r["url"])
                self.assertEqual(url.scheme, "https")
                self.assertEqual(url.netloc, "github.com")
                self.assertEqual(url.path.strip("/").lower(), slug.lower())
                self.assertIn(slug.lower(), repos)

    def test_no_false_positive_clearance(self):
        for r in self.rows:
            with self.subTest(repo=r["github_repository"]):
                self.assertEqual(r["validation_status"], "not-tested")
                self.assertEqual(r["license_status"], "not-reviewed")
                self.assertEqual(r["security_status"], "not-audited")
                self.assertEqual(r["fork_decision"], "hold-until-license-and-sandbox-validation")

    def test_page_contract(self):
        for term in (
            "data/top30_evaluation.csv", "data/repo_metadata.json",
            "id=\"search\"", "id=\"domain\"", "id=\"priority\"",
            "id=\"status\"", "id=\"license\"", "id=\"maintenance\"",
            "id=\"export\"", "metadata(r).stars", "metadata(r).license_spdx",
            "function parseCSV(", "function exportCSV(", "function loadMetadata(",
            "target=\"_blank\"", "rel=\"noopener noreferrer\"",
        ):
            with self.subTest(term=term):
                self.assertIn(term, self.page)

    def test_comparison_controls(self):
        for term in ('id="comparePanel"', 'id="compareContent"', 'id="clearCompare"', "function toggleCompare(", "function renderComparison(", "data-repo=", "aria-pressed", "最多比较 4 个项目"):
            with self.subTest(term=term):
                self.assertIn(term, self.page)

    def test_project_detail_sources_and_safety(self):
        self.assertIn("./project.html?repo=", self.page)
        for value in ("top30_evaluation.csv", "top30_evidence.json", "repo_metadata.json", "fork_decision", "sandbox_commit_sha", "metadata_source_url", "encodeURIComponent"):
            with self.subTest(value=value):
                self.assertIn(value, self.detail if value != "encodeURIComponent" else self.page)
        self.assertIn("ev.generated_from_snapshot_utc!==meta.generated_at_utc", self.detail)

    def test_business_use_cases_complete(self):
        cases=json.loads((ROOT/"data/business_use_cases.json").read_text(encoding="utf-8"))
        self.assertEqual(cases["status"],"illustrative-blueprints-not-tested")
        for domain in {r["domain"] for r in self.rows}:
            with self.subTest(domain=domain):
                entry=cases["domains"][domain]
                self.assertGreaterEqual(len(entry["flow"]),3)
                for field in ("goal","metric","risk"):
                    self.assertTrue(entry[field])
        self.assertIn("business_use_cases.json",self.detail)
        self.assertIn('id="caseFlow"',self.detail)

    def test_home_links_to_research_lab(self):
        self.assertIn('href="./top30.html"', self.home)

    def test_metadata_snapshot_is_consistent(self):
        self.assertEqual(self.metadata["coverage_count"], len(self.metadata["repositories"]))
        self.assertEqual(self.metadata["expected_count"], self.metadata["coverage_count"])
        self.assertTrue(self.metadata.get("generated_at_utc"))


if __name__ == "__main__":
    unittest.main()
