"""Verifies true SQLite-backed LangGraph restart evidence in its isolated CI.

The default dependency-free Atlas suite explicitly skips this optional
real-upstream regression when the SDK is not installed.
"""
import json
import tempfile
import unittest
from pathlib import Path

try:
    import langgraph.checkpoint.sqlite
    from scripts.verify_durable_recovery import execute
except ModuleNotFoundError as exc:
    if not (exc.name or "").startswith(("langgraph", "langgraph_checkpoint")):
        raise
    execute=None


@unittest.skipUnless(execute is not None, "Real SQLite checkpointer must run in its pinned upstream workflow")
class DurableSQLiteChecks(unittest.TestCase):
    def test_exact_output_with_restart_provenance(self):
        result=json.loads(Path("test-results/durable/durability-result.json").read_text("utf-8"))
        checks=result["validation"]
        self.assertEqual(checks["cases_total"],13)
        self.assertEqual(checks["cases_passed"],13)
        self.assertTrue(checks["all_passed"])
        self.assertEqual(len(checks["checks"]),13)
        self.assertGreaterEqual(checks["actual_distinct_processes"],17)
        self.assertEqual(result["commit_keys"],["frozen-01","frozen-02","shared-concurrency-key"])
        self.assertEqual(len(result["journal"]),9)

    def test_not_a_production_security_claim(self):
        result=json.loads(Path("test-results/durable/durability-result.json").read_text("utf-8"))
        self.assertIs(result["real_identity_verified"],False)
        self.assertIs(result["production_integrated"],False)
        self.assertEqual(result["real_broker_orders"],0)
        self.assertEqual(result["real_model_calls"],0)
        self.assertEqual(result["checkpoint_storage"],"disk-sqlite")
        self.assertEqual(result["concurrency_scope"],"ledger-only-not-graph")
        self.assertIs(result["validation"]["mid_commit_crash_injected"],False)
        self.assertIs(result["validation"]["authenticated_approvals_tested"],False)
        self.assertIs(result["validation"]["graph_concurrency_tested"],False)

    def test_actual_reproducible_new_process_replay(self):
        with tempfile.TemporaryDirectory(prefix="atlas-independent-durable-") as path:
            outcome=execute(Path(path))
            self.assertEqual(outcome["validation"]["cases_passed"],13)
            self.assertEqual(outcome["commit_keys"],["frozen-01","frozen-02","shared-concurrency-key"])
            self.assertEqual(outcome["journal"][0]["thread"],"accepted")

if __name__=="__main__":
    unittest.main()
