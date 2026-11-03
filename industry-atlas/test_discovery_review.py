#!/usr/bin/env python3
"""Synthetic regression for discovery triage — no external network or model."""
import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main
from unittest.mock import patch
import argparse
import discovery_review as app

NOW = datetime(2026, 11, 4, tzinfo=timezone.utc)

def item(**kw):
    base = {
        "name": "quant-research-agent",
        "url": "https://github.com/verified-lab/quant-research-agent",
        "kind": "agent",
        "description": "Reproducible open-source quant portfolio research agent with tutorials and sample evaluation",
        "source_kind": "github-api",
        "owner": "verified-lab",
        "last_modified": "2026-10-25T00:00:00Z",
        "license_spdx": "Apache-2.0",
    }
    base.update(kw)
    return base

class DiscoveryReview(TestCase):
    def test_official_domain_and_canonicalization(self):
        self.assertEqual(app.canonical_url("https://github.com/a/b/?utm_source=x#details"), "https://github.com/a/b")
        for url in ("http://github.com/a/b", "https://github.com.evil.com/x", "https://user:pass@github.com/a", "https://evil.tld/x", "javascript:alert(1)"):
            self.assertEqual(app.canonical_url(url), "")
        self.assertEqual(app.canonical_url("https://huggingface.co/demo/model"), "https://huggingface.co/demo/model")

    def test_score_is_not_approval(self):
        high = app.evaluate(item(owner="openai"), NOW)
        self.assertGreaterEqual(high["metadata_score"], 60)
        self.assertFalse(high["approved"])
        self.assertEqual(high["verification"], "metadata-only")
        self.assertEqual(high["safety_review"], "not-audited")
        self.assertIn("s02", high["sector_ids"])
        self.assertNotIn("s04", high["sector_ids"])
        no_license = app.evaluate(item(license_spdx="unknown"), NOW)
        self.assertEqual(no_license["review_state"], "needs-evidence")
        no_industry = app.evaluate(item(name="misc-helper", description="generic utility"), NOW)
        self.assertEqual(no_industry["review_state"], "needs-evidence")

    def test_unsafe_and_archived_exclusions(self):
        self.assertIsNone(app.evaluate(item(description="credential stealer library"), NOW))
        self.assertIsNone(app.evaluate(item(archived=True), NOW))
        self.assertIsNone(app.evaluate(item(url="https://malicious.test/bad"), NOW))

    def test_dedup_and_priorities_stable(self):
        out = app.assemble([item(), item(url="https://github.com/verified-lab/quant-research-agent/"), item(name="warehouse-robot", url="https://github.com/research/warehouse-robot", description="warehouse logistics automation", license_spdx="MIT")], NOW, "live", 10)
        self.assertEqual(out["total_input"], 3)
        self.assertEqual(out["deduplicated"], 2)
        self.assertEqual(out["queue_count"], 2)
        self.assertFalse(out["auto_promoted"])
        self.assertEqual(out["records"][0]["review_state"], "review-priority")
        self.assertTrue(any("s15" in row["sector_ids"] for row in out["records"]))

    def test_unauthorized_fetch_refused_before_network(self):
        with self.assertRaises(ValueError):
            app.request_json("https://example.com/api/items")
        with self.assertRaises(ValueError):
            app.request_json("http://api.github.com/search/repositories")
        with self.assertRaises(ValueError):
            app.request_json("https://api.github.com.evil.test/")

    def test_failed_live_fetch_preserves_previous_file(self):
        with TemporaryDirectory() as td:
            target = Path(td) / "review.json"
            target.write_text('{"previous":"safe"}', encoding="utf-8")
            with patch.object(app, "live_candidates", side_effect=RuntimeError("429 rate limit")):
                with patch.object(app, "existing_candidates", side_effect=AssertionError("offline fallback forbidden")):
                    rc = app.main(["--mode", "live", "--output", str(target)])
            self.assertEqual(rc, 2)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["previous"], "safe")

    def test_synthetic_live_api_adapter(self):
        gh = {"items": [{"full_name":"research-org/warehouse-helper", "html_url":"https://github.com/research-org/warehouse-helper", "description":"warehouse logistics assistant", "owner":{"login":"research-org"}, "license":{"spdx_id":"MIT"}, "pushed_at":"2026-10-31T10:00:00Z", "archived":False}], "incomplete_results":False}
        hf = [{"id":"demo/finance-model", "pipeline_tag":"text-generation", "tags":["finance","license:apache-2.0"],"lastModified":"2026-11-01T12:00:00Z"}]
        from xml.etree import ElementTree as ET
        atom = ET.fromstring('<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>https://arxiv.org/abs/2611.00001v1</id><title>Quant portfolio evaluation</title><summary>A reproducible portfolio research paper.</summary><updated>2026-11-03T10:00:00Z</updated></entry></feed>')
        with patch.object(app, "request_json", side_effect=[gh, gh, hf]) as req, patch.object(app, "request_atom", return_value=atom) as papers:
            items = app.live_candidates(NOW)
        self.assertEqual(len(items), 4)
        self.assertEqual(req.call_count, 3)
        self.assertEqual(papers.call_count, 1)
        out = app.assemble(items, NOW, "live", 90)
        self.assertEqual(out["deduplicated"], 3)
        self.assertTrue(any(r["kind"]=="paper" and r["review_state"]=="needs-evidence" for r in out["records"]))
        self.assertTrue(all(not r["approved"] for r in out["records"]))

if __name__ == "__main__":
    main()
