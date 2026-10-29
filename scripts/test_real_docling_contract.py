"""Real upstream Docling tests only in isolated package-pinned CI.

Base Atlas validation intentionally does not install Docling. Tests are skipped
there, but MUST execute in the real-upstream workflow before merge.
"""
import json
import unittest
from pathlib import Path

try:
    from scripts.real_docling_pilot import (
        VERSION, PAGES, write_synthetic_pdf, probe,
    )
except ModuleNotFoundError as exc:
    if not (exc.name or "").startswith(("docling","docling_core")):
        raise
    probe = None


@unittest.skipUnless(probe is not None, "Docling API tests require isolated real-upstream workflow")
class RealDoclingContractTests(unittest.TestCase):
    def test_real_pdf_result_artifact_matches_upstream(self):
        p=Path("test-results/real-docling-result.json")
        result=json.loads(p.read_text("utf-8"))
        self.assertEqual(result["version"],VERSION)
        self.assertEqual(result["package"],"docling")
        self.assertEqual(result["project"],"docling-project/docling")
        self.assertEqual(result["status"],"real-upstream-native-pdf-sandbox-executed")
        self.assertEqual(result["cases_total"],12)
        self.assertEqual(result["cases_passed"],12)
        self.assertEqual([c["id"] for c in result["cases"]],[f"DOC{i:02d}" for i in range(1,13)])
        self.assertTrue(all(c["pass"] is True for c in result["cases"]))

    def test_capability_limitations_are_explicit_and_true(self):
        data=json.loads(Path("test-results/real-docling-result.json").read_text("utf-8"))
        self.assertEqual(data["pipeline"],"NativePdfPipeline")
        self.assertIs(data["model_free"],True)
        self.assertEqual(data["semantic_tables_detected"],0)
        self.assertIs(data["semantic_table_accuracy_tested"],False)
        self.assertIs(data["ocr_tested"],False)
        self.assertIs(data["formula_vision_tested"],False)
        self.assertEqual(data["llm_calls"],0)
        self.assertEqual(data["trading_orders"],0)
        self.assertIs(data["real_user_data_used"],False)
        self.assertIs(data["external_document_urls_used"],False)

    def test_pdf_fixture_is_original_three_pages_without_private_content(self):
        import tempfile
        with tempfile.TemporaryDirectory() as name:
            pdf=Path(name)/"synthetic.pdf"
            count=write_synthetic_pdf(pdf)
            raw=pdf.read_bytes()
            self.assertEqual(len(raw),count)
            self.assertTrue(raw.startswith(b"%PDF-1.4"))
            self.assertEqual(raw.count(b"/Type /Page /"),3)
            self.assertIn(b"NOFI",raw)
            self.assertIn(b"45 minutes",raw)
            self.assertIn(b"METRIC_NAME",raw)
            self.assertNotIn(b"BEGIN PRIVATE KEY",raw)

    def test_second_independent_real_conversion_uses_the_same_scope(self):
        # Re-execute the upstream package, not merely compare a prewritten JSON.
        result=probe()
        self.assertEqual(result["cases_passed"],12)
        self.assertEqual(result["pages"],3)
        self.assertEqual(result["semantic_tables_detected"],0)
        self.assertGreaterEqual(result["text_items"],11)


if __name__=="__main__":
    unittest.main()
