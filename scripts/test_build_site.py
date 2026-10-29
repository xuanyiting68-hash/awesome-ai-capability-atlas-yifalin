import json
import tempfile
import unittest
from pathlib import Path
from scripts.build_site import build, ROOT

class PublishBoundaryTests(unittest.TestCase):
    def test_only_public_assets_are_published_with_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / 'site'
            manifest = build(destination, commit='a' * 40)
            self.assertEqual(set(p.name for p in destination.iterdir()),
                             {'index.html', 'top30.html', 'project.html', 'blueprints.html', 'network.html', 'data', 'docs', 'LICENSE', 'README.md', 'deployment.json'})
            self.assertEqual(json.loads((destination / 'deployment.json').read_text()), manifest)
            self.assertEqual(manifest['source_commit'], 'a' * 40)
            self.assertEqual(manifest['catalog_count'], 5000)
            self.assertEqual(manifest['research_project_count'], 30)
            self.assertEqual(manifest['blueprint_count'], 10)
            self.assertEqual(manifest['research_briefs_count'],30)
            self.assertEqual(manifest['research_reviewed_count'],0)
            self.assertTrue((destination / 'data/research_briefs.json').is_file())
            self.assertTrue((destination / 'data/business_use_cases.json').is_file())
            self.assertIn('project.html', (destination / 'top30.html').read_text())
            self.assertIn('blueprints.html', (destination / 'index.html').read_text())
            self.assertIn('network.html', (destination / 'index.html').read_text())
            self.assertIn('data/top30_evaluation.csv', (destination / 'network.html').read_text())

    def test_forged_research_tier_preserves_previous_site(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            build(source,commit='a'*40)
            target = Path(directory) / 'previous'
            target.mkdir()
            (target / 'marker').write_text('keep last good')
            evidence = source / 'data/research_briefs.json'
            doc = json.loads(evidence.read_text())
            doc['entries'][0]['tier'] = 'Production Candidate'
            evidence.write_text(json.dumps(doc))
            with self.assertRaisesRegex(ValueError,'promotion'):
                build(target,source=source,commit='b'*40)
            self.assertEqual((target / 'marker').read_text(), 'keep last good')

    def test_refuses_repository_or_parent_as_destination(self):
        for destination in (ROOT, ROOT.parent):
            with self.assertRaises(ValueError):
                build(destination)

    def test_stale_evidence_preserves_previous_site(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            build(source, commit='a' * 40)
            # package.json is build input but is deliberately excluded from public output.
            (source / 'package.json').write_text('{"version":"test"}')
            destination = Path(directory) / 'previous'
            destination.mkdir()
            (destination / 'marker').write_text('last good build')
            evidence_path = source / 'data/top30_evidence.json'
            evidence = json.loads(evidence_path.read_text())
            evidence['generated_from_snapshot_utc'] = 'invalid'
            evidence_path.write_text(json.dumps(evidence))
            with self.assertRaises(ValueError):
                build(destination, source=source, commit='b' * 40)
            self.assertEqual((destination / 'marker').read_text(), 'last good build')

if __name__ == '__main__':
    unittest.main()
