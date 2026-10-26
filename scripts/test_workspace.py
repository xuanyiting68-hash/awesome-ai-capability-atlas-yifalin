"""Content coverage for the bilingual research workspace, independent of UI implementation."""
import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class WorkspaceContentTests(unittest.TestCase):
    def test_translation_covers_each_research_project(self):
        with (ROOT / 'data/top30_evaluation.csv').open(encoding='utf-8-sig') as file:
            rows = list(csv.DictReader(file))
        english = json.loads((ROOT / 'data/top30_en.json').read_text())
        self.assertEqual(set(english), {r['github_repository'].lower() for r in rows})
        for repo, entry in english.items():
            with self.subTest(repo=repo):
                self.assertEqual(set(entry), {'capability', 'yifalin_pilot'})
                self.assertTrue(all(isinstance(s, str) and len(s.strip()) > 10 for s in entry.values()))
                self.assertTrue(all(not any('\u4e00' <= c <= '\u9fff' for c in s) for s in entry.values()))

if __name__ == '__main__':
    unittest.main()
