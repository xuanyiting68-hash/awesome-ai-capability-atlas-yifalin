"""Independent checks around the real LangGraph 1.2.18 sandbox results.

Requires the actual third-party langgraph package, and runs only in its
separate CI workflow. Not part of the base synthetic-only Atlas CI.
"""
import json
import unittest
from pathlib import Path

# The base Atlas suite has no third-party dependencies. When the actual SDK is
# unavailable, this class is explicitly skipped; it must run in the separate
# real-upstream workflow, which pins and installs LangGraph before testing.
try:
    from langgraph.types import Command
    from scripts.real_langgraph_pilot import build_probe, REQUIRED_LANGGRAPH
except ModuleNotFoundError as exc:
    if not exc.name.startswith("langgraph"):
        raise
    Command = None
    build_probe = None
    REQUIRED_LANGGRAPH = "1.2.18"


@unittest.skipUnless(Command is not None, "Real LangGraph tests run in separate pinned upstream workflow")
class RealLangGraphContractTests(unittest.TestCase):
    def test_published_ci_artifact_covers_exact_real_cases(self):
        doc=json.loads(Path("test-results/real-langgraph-result.json").read_text("utf-8"))
        self.assertEqual(doc["project"], "langchain-ai/langgraph")
        self.assertEqual(doc["status"], "real-upstream-sandbox-executed")
        self.assertEqual(doc["upstream_version"], REQUIRED_LANGGRAPH)
        self.assertEqual(doc["cases_total"], 10)
        self.assertEqual(doc["cases_passed"], 10)
        self.assertEqual([x["id"] for x in doc["cases"]],
                         [f"LG{i:02d}" for i in range(1,11)])
        self.assertTrue(all(x["pass"] is True for x in doc["cases"]))
        self.assertEqual(doc["checkpoint_scope"], "process-memory-only")
        self.assertEqual(doc["owner_approval"], "synthetic-dict-not-authenticated-user-identity")

    def test_no_real_tools_or_user_data_were_claimed(self):
        doc=json.loads(Path("test-results/real-langgraph-result.json").read_text("utf-8"))
        self.assertEqual(doc["tool_calls_real"],0)
        self.assertEqual(doc["llm_calls_real"],0)
        self.assertEqual(doc["trading_orders_sent"],0)
        self.assertIs(doc["external_user_data_used"],False)
        self.assertGreaterEqual(len(doc["limitations"]),5)

    def test_real_graph_requires_approval_before_memory_write(self):
        ledger=set()
        graph=build_probe(ledger)
        config={"configurable":{"thread_id":"test-approval"}}
        result=graph.invoke({"action":"write_draft","idempotency_key":"proof"},config=config)
        self.assertIn("__interrupt__",result)
        self.assertEqual(ledger,set())
        output=graph.invoke(Command(resume={"approved":False,"source":"owner_session"}),config=config)
        self.assertEqual(output["outcome"],"owner_denied")
        self.assertEqual(ledger,set())

    def test_real_graph_rejects_all_unknown_actions(self):
        ledger=set()
        graph=build_probe(ledger)
        for i,action in enumerate(("send_order","delete_user_data","email.send","credentials.read")):
            with self.subTest(action=action):
                config={"configurable":{"thread_id":f"test-deny-{i}"}}
                result=graph.invoke({"action":action},config=config)
                self.assertEqual(result["outcome"],"blocked_action")
        self.assertEqual(ledger,set())

    def test_real_graph_idempotent_commit_only_after_synthetic_approval(self):
        ledger=set()
        graph=build_probe(ledger)
        for thread in ("first","again"):
            config={"configurable":{"thread_id":thread}}
            result=graph.invoke({"action":"write_draft","idempotency_key":"same-draft"},config=config)
            self.assertIn("__interrupt__",result)
            result=graph.invoke(Command(resume={"approved":True,"source":"owner_session"}),config=config)
            self.assertIn(result["outcome"],("draft_applied","already_applied"))
        self.assertEqual(ledger,{"same-draft"})


if __name__=="__main__":
    unittest.main()
