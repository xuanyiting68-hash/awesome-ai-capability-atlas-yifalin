import copy
import json
import unittest
from pathlib import Path
from validate_recipes import validate_recipes, validate_from_files

ROOT=Path(__file__).resolve().parents[1]


class RecipeContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(x):return json.loads((ROOT/x).read_text("utf-8"))
        cls.data=read("data/capability_recipes.json")
        cls.bp=read("data/blueprints.json")
        cls.curated=read("data/curated.json")
        cls.briefs=read("data/research_briefs.json")
        cls.meta=read("data/repo_metadata.json")

    def check(self,d):
        return validate_recipes(d,self.bp,self.curated,self.briefs,self.meta)

    def test_approved_research_only_baseline(self):
        result=validate_from_files()
        self.assertEqual(result["recipes_count"],6)
        self.assertEqual(result["unique_curated_tool_refs"],20)
        self.assertEqual(result["verified_integrations"],0)

    def test_unknown_repository_fails_closed(self):
        data=copy.deepcopy(self.data)
        data["recipes"][0]["tools"][0]="malicious/unlisted"
        with self.assertRaisesRegex(ValueError,"tool composition"):self.check(data)

    def test_unreviewed_license_cannot_be_promoted(self):
        data=copy.deepcopy(self.data)
        data["recipes"][0]["license_review"]="approved"
        with self.assertRaisesRegex(ValueError,"promoted"):self.check(data)

    def test_integration_cannot_be_just_claimed(self):
        data=copy.deepcopy(self.data)
        data["verified_integration_count"]=1
        with self.assertRaisesRegex(ValueError,"integrations"):self.check(data)

    def test_missing_human_gate_is_blocked(self):
        data=copy.deepcopy(self.data)
        data["recipes"][1]["steps"][-1]["gate"]="manual-review"
        with self.assertRaisesRegex(ValueError,"approvals"):self.check(data)

    def test_recipe_input_and_acceptance_required(self):
        data=copy.deepcopy(self.data)
        data["recipes"][2]["acceptance_en"]=[]
        with self.assertRaisesRegex(ValueError,"evidence"):self.check(data)

    def test_score_axes_cannot_total_more_than_100(self):
        data=copy.deepcopy(self.data)
        data["score_axes"]["completed_security_license_audit"]=35
        with self.assertRaisesRegex(ValueError,"rubric"):self.check(data)

    def test_offline_demo_must_be_known_synthetic_path(self):
        data=copy.deepcopy(self.data)
        data["recipes"][0]["offline_demo_path"]="../../secrets"
        with self.assertRaisesRegex(ValueError,"demo"):self.check(data)

    def test_every_candidate_is_curated(self):
        repos={p["repo"].lower() for p in self.curated}
        self.assertEqual(len({r.lower() for x in self.data["recipes"] for r in x["tools"]}),20)
        self.assertTrue(all(t.lower() in repos for x in self.data["recipes"] for t in x["tools"]))


if __name__=="__main__":
    unittest.main()
