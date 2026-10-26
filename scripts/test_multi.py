import unittest
from scripts.harvest_multi import mkrow,tree_candidate,assemble,evenly_select,topic_from_path
class MultiSourceTests(unittest.TestCase):
    def test_agent_skill(self):
        row=tree_candidate("anthropics/skills","skills/docx/SKILL.md","official-source")
        self.assertEqual(row["type"],"skill")
        self.assertEqual(row["review_level"],"discovery-only")
        self.assertEqual(row["license_review"],"not-checked")
        self.assertTrue(row["url"].startswith("https://github.com/anthropics/skills/blob/main/"))
    def test_openai(self):
        r=tree_candidate("openai/skills","skills/.curated/chatgpt-apps/SKILL.md","official-source")
        self.assertEqual(r["type"],"skill")
    def test_copilot_agent(self):
        r=tree_candidate("github/awesome-copilot","agents/code-review.agent.md","publisher-repository")
        self.assertEqual(r["type"],"agent")
    def test_n8n(self):
        r=tree_candidate("Zie619/n8n-workflows","workflows/Telegram/005_Telegram_Automate.json","workflow-repository")
        self.assertEqual(r["type"],"workflow")
    def test_avoid_plugin_duplicate(self):
        r=tree_candidate("sickn33/agentic-awesome-skills","plugins/agentic-awesome-skills-claude/skills/name/SKILL.md","community-repository")
        self.assertIsNone(r)
    def test_roundtrip_without_duplicate_url(self):
        x=mkrow(name="Example",url="https://github.com/demo/first",repo="demo/first",kind="mcp",ecosystem="github-mcp",source_kind="test")
        rows=assemble([x],{"github-mcp":[x]},5000)
        self.assertEqual(len(rows),1)
    def test_spread(self):
        self.assertEqual(evenly_select(list(range(20)),3),[0,6,13])
    def test_growth_tag(self):
        self.assertEqual(topic_from_path("video-caption-creator"),"AI视频制作")
if __name__=="__main__":unittest.main()
