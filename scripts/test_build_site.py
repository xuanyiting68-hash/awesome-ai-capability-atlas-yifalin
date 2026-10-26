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
                             {'index.html', 'top30.html', 'data', 'docs', 'LICENSE', 'README.md', 'deployment.json'})
            self.assertEqual(json.loads((destination / 'deployment.json').read_text()), manifest)
            self.assertEqual(manifest['source_commit'], 'a' * 40)
            self.assertEqual(manifest['catalog_count'], 5000)
            self.assertEqual(manifest['research_project_count'], 30)

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
