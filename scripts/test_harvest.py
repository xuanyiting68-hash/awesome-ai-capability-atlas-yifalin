import unittest
from scripts.harvest import extract, round_robin
class HarvestTests(unittest.TestCase):
    def test_extract(self):
        s="- [Example](https://clawskills.sh/skills/test-example) - A real skill.\n"
        result=extract("ai-and-llms",s)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["verification"],"indexed-upstream")
        self.assertEqual(result[0]["safety_review"],"not-audited")
    def test_curated_first(self):
        item={"id":"x","url":"https://example.com","name":"curated"}
        self.assertEqual(round_robin([item],{},5000),[item])
if __name__=="__main__":
    unittest.main()
