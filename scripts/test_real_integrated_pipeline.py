"""Real integration tests: run only in pinned isolated upstream workflow."""
import tempfile
import unittest
from pathlib import Path

try:
    from scripts.real_integrated_pipeline import run, promptfoo_config, make_graph, SCENARIOS, VERSIONS
except ModuleNotFoundError as exc:
    if not (exc.name or "").startswith(("docling","langgraph","docling_core")):
        raise
    run=None


@unittest.skipUnless(run is not None, "Real Docling/LangGraph integration tests require isolated upstream workflow")
class IntegratedPipelineTests(unittest.TestCase):
    def test_real_e2e_executes_with_all_three_software_version_pins(self):
        result=run()
        self.assertEqual(result["components"],VERSIONS)
        self.assertEqual(result["cases_total"],8)
        self.assertEqual(result["cases_passed"],8)
        self.assertEqual(result["actual_upstream_docling_calls"],8)
        self.assertEqual(result["actual_upstream_langgraph_runs"],8)
        self.assertEqual(result["broker_orders"],0)
        self.assertEqual(result["llm_calls"],0)
        self.assertIs(result["security_certified"],False)
        self.assertIs(result["user_data_processed"],False)

    def test_gate_is_fail_closed_for_orders_and_untrusted_approval(self):
        result=run()
        observed={x["id"]:x for x in result["outputs"]}
        self.assertEqual(observed["I06"]["message"],"BLOCK: forbidden_action")
        self.assertFalse(observed["I06"]["interrupted"])
        self.assertEqual(observed["I03"]["message"],"BLOCK: invalid_approval_source")
        self.assertTrue(observed["I03"]["interrupted"])
        self.assertEqual(observed["I04"]["message"],"BLOCK: missing_evidence")
        self.assertFalse(observed["I04"]["interrupted"])

    def test_real_docling_provenance_and_duplicate_contract(self):
        result=run()
        self.assertEqual(result["outputs"][0]["pages"],{"NOFI":1,"45 minutes":2})
        self.assertEqual(result["outputs"][0]["message"],
                         "ALLOW: synthetic_draft_created citations=p1,p2")
        self.assertEqual(result["outputs"][4]["message"],
                         "BLOCK: duplicate_idempotency_key")
        self.assertEqual(result["outputs"][7]["message"],
                         "BLOCK: missing_idempotency_key")

    def test_generated_echo_config_carries_actual_graph_outputs(self):
        result=run()
        config=promptfoo_config(result)
        self.assertEqual(config["providers"],["echo"])
        self.assertEqual(len(config["tests"]),8)
        for case,entry in zip(result["outputs"],config["tests"]):
            self.assertEqual(entry["vars"]["mock_response"],case["message"])
            self.assertEqual(entry["assert"][0]["value"],case["expected"])
        negative=promptfoo_config(result,negative=True)
        self.assertEqual(len(negative["tests"]),1)
        self.assertEqual(negative["tests"][0]["vars"]["mock_response"],"BLOCK: forbidden_action")
        self.assertEqual(negative["tests"][0]["assert"][0]["value"],"ALLOW: real_order_sent")


if __name__=="__main__":
    unittest.main()
