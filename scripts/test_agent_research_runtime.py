"""Real subprocess end-to-end checkpoint and permission tests (requires actual E5 + LangGraph)."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import agent_research_runtime as runtime

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/agent_research_runtime.py"


def call(*args, success=True):
    p = subprocess.run(
        [sys.executable, str(CLI), *map(str, args)],
        cwd=ROOT, capture_output=True, text=True, timeout=290,
    )
    if success and p.returncode != 0:
        raise AssertionError("CLI failed: " + p.stderr[-1600:])
    if not success and p.returncode == 0:
        raise AssertionError("Expected fail-closed command: " + p.stdout)
    return json.loads(p.stdout if success else p.stderr.splitlines()[-1])


class LocalRuntimeTests(unittest.TestCase):
    def test_schema_action_and_injection_fail_closed_before_model(self):
        example = json.loads((ROOT / "examples/research_agent/education_task.json").read_text())
        runtime.verify_task(example)
        for update in (
            {"action": "send_order"},
            {"action": "send_email"},
            {"action": "run_shell"},
            {"scenario": "unknown"},
            {"task_id": "../escape"},
            {"goal": "too short"},
            {"secret": "unexpected"},
        ):
            with self.subTest(update=update):
                with self.assertRaises(ValueError):
                    runtime.verify_task({**example, **update})

    def test_real_education_model_persistent_restart_and_one_use_approval(self):
        with tempfile.TemporaryDirectory(prefix="atlas-real-edu-") as temp:
            workspace = Path(temp) / "run"
            fixture = ROOT / "examples/research_agent/education_task.json"
            pending = call("prepare", "--workspace", workspace, "--task-file", fixture)
            self.assertEqual(pending["status"], "PENDING_ONE_TIME_LOCAL_REVIEW")
            self.assertTrue(pending["actual_neural_model_executed"])
            self.assertTrue(pending["durable_graph_interrupted"])
            self.assertEqual(len(pending["candidates"]), 4)
            self.assertFalse(pending["owner_authentication"])
            self.assertEqual(pending["external_actions"], 0)
            token = pending["review_token"]
            self.assertGreater(len(token), 30)
            self.assertFalse(token in (workspace / "checkpoint.sqlite").read_bytes().decode("latin1"),
                             "Token must only be stored as a digest")
            task = pending["task_id"]
            before = call("inspect", "--workspace", workspace, "--task-id", task)
            self.assertEqual(before["gate"], "PENDING")
            self.assertIn("human_review", before["graph_next"])
            self.assertFalse(before["token_disclosed"])
            bad = call("approve", "--workspace", workspace, "--task-id", task,
                       "--token", "not_the_correct_capability", success=False)
            self.assertEqual(bad["status"], "BLOCK")
            self.assertFalse((workspace / "reports" / (task + ".json")).exists())
            complete = call("approve", "--workspace", workspace, "--task-id", task, "--token", token)
            self.assertEqual(complete["status"], "LOCAL_REPORT_WRITTEN")
            self.assertEqual(complete["real_orders"], 0)
            self.assertFalse(complete["owner_authenticated"])
            after = call("inspect", "--workspace", workspace, "--task-id", task)
            self.assertEqual(after["gate"], "CONSUMED_APPROVE")
            self.assertEqual(after["graph_next"], [])
            self.assertEqual(after["outcome"], "LOCAL_REPORT_WRITTEN")
            report = json.loads((workspace / complete["report"]).read_text())
            self.assertEqual(report["status"], "LOCAL_APPROVED_RESEARCH_REPORT_NOT_DEPLOYED")
            self.assertEqual(report["model"], "Xenova/multilingual-e5-small")
            self.assertEqual(report["model_dimensions"], 384)
            self.assertEqual(len(report["selected"]), 4)
            self.assertEqual(len(report["steps"]), 4)
            self.assertTrue(all(x["source_url"] == "https://github.com/" + x["repo"]
                                and x["reviewed_for_security"] is False
                                and x["verified_tool_compatibility"] is False
                                and x["blockers"]
                                for x in report["selected"]))
            self.assertFalse(report["claims"]["third_party_tool_executed"])
            self.assertFalse(report["claims"]["production_safe"])
            self.assertEqual(report["permissions"]["external_system_calls"], 0)
            reuse = call("approve", "--workspace", workspace, "--task-id", task, "--token", token,
                         success=False)
            self.assertEqual(reuse["status"], "BLOCK")
            duplicate = call("prepare", "--workspace", workspace, "--task-file", fixture,
                             success=False)
            self.assertEqual(duplicate["status"], "BLOCK")
            count = len(list((workspace / "reports").glob("*.json")))
            self.assertEqual(count, 1, "At most one local plan was written")

    def test_real_finance_model_denial_never_writes_report(self):
        with tempfile.TemporaryDirectory(prefix="atlas-real-denial-") as temp:
            ws = Path(temp) / "run"
            fixture = ROOT / "examples/research_agent/finance_task.json"
            prepare = call("prepare", "--workspace", ws, "--task-file", fixture)
            self.assertEqual(prepare["status"], "PENDING_ONE_TIME_LOCAL_REVIEW")
            result = call("deny", "--workspace", ws, "--task-id", prepare["task_id"],
                          "--token", prepare["review_token"])
            self.assertEqual(result["status"], "BLOCK: declined")
            self.assertIsNone(result["report"])
            self.assertFalse(list((ws / "reports").glob("*.json")))
            after = call("inspect", "--workspace", ws, "--task-id", prepare["task_id"])
            self.assertEqual(after["gate"], "CONSUMED_DENY")
            self.assertEqual(after["outcome"], "BLOCK: declined")
            self.assertEqual(after["graph_next"], [])
            retry = call("approve", "--workspace", ws, "--task-id", prepare["task_id"],
                         "--token", prepare["review_token"], success=False)
            self.assertEqual(retry["status"], "BLOCK")

    def test_unauthorized_approval_without_workspace_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            answer = call("approve", "--workspace", Path(temp) / "missing",
                          "--task-id", "forged-task", "--token", "fake", success=False)
            self.assertEqual(answer["status"], "BLOCK")


if __name__ == "__main__":
    unittest.main()
