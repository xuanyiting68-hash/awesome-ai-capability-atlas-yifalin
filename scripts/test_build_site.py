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
                             {'index.html', 'top30.html', 'project.html', 'blueprints.html', 'network.html', 'adoption.html', 'pilot-lab.html', 'recipes.html', 'data', 'docs', 'examples', 'LICENSE', 'README.md', 'deployment.json'})
            self.assertEqual(json.loads((destination / 'deployment.json').read_text()), manifest)
            self.assertEqual(manifest['source_commit'], 'a' * 40)
            self.assertEqual(manifest['catalog_count'], 5000)
            self.assertEqual(manifest['research_project_count'], 30)
            self.assertEqual(manifest['blueprint_count'], 10)
            self.assertEqual(manifest['research_briefs_count'],30)
            self.assertEqual(manifest['research_reviewed_count'],0)
            self.assertEqual(manifest['recipe_count'],6)
            self.assertEqual(manifest['recipe_curated_tool_count'],20)
            self.assertEqual(manifest['recipe_verified_integrations'],0)
            self.assertEqual(manifest['recipe_demo_count'],3)
            self.assertIs(manifest['recipe_demo_contract_passed'],True)
            self.assertEqual(manifest['recipe_demo_upstream_integrations'],0)
            demo=json.loads((destination/'data/recipe_demo_results.json').read_text('utf-8'))
            self.assertEqual(set(demo['scenarios']),{'leads','education','finance'})
            self.assertEqual(demo['scenarios']['finance']['net_bps_sum'],'-133.79')
            self.assertTrue((destination/'examples/recipe_demos/run_demo.py').is_file())
            self.assertTrue((destination/'examples/consent_lead_triage/synthetic_leads.json').is_file())
            self.assertTrue((destination / 'data/capability_recipes.json').is_file())
            self.assertTrue((destination / 'recipes.html').is_file())
            self.assertEqual(manifest['star_shortlist_count'],30)
            self.assertEqual(manifest['pilot_contract_cases'],24)
            self.assertEqual(manifest['pilot_contract_passed'],24)
            self.assertIs(manifest['pilot_upstream_packages_executed'],False)
            result=json.loads((destination/'data/pilot_lab_results.json').read_text('utf-8'))
            self.assertTrue(result['all_expected_met'])
            self.assertFalse(result['upstream_code_executed'])
            self.assertEqual(len(result['cases']),24)
            self.assertEqual(manifest['priority_integration_candidates'],8)
            self.assertEqual(manifest['fork_approved_count'],0)
            self.assertEqual(manifest['star_actions_executed_by_atlas'],0)
            self.assertTrue((destination / 'data/adoption_plan.json').is_file())
            self.assertTrue((destination / 'data/research_briefs.json').is_file())
            self.assertTrue((destination / 'data/business_use_cases.json').is_file())
            self.assertIn('project.html', (destination / 'top30.html').read_text())
            self.assertIn('blueprints.html', (destination / 'index.html').read_text())
            self.assertIn('network.html', (destination / 'index.html').read_text())
            self.assertIn('adoption.html', (destination / 'index.html').read_text())
            self.assertIn('pilot-lab.html', (destination / 'index.html').read_text())
            self.assertIn('data/top30_evaluation.csv', (destination / 'network.html').read_text())

    def test_pilot_failed_expectation_cannot_replace_previous_site(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source'
            build(source,commit='a'*40)
            old=Path(directory)/'old'
            old.mkdir()
            (old/'marker').write_text('keep previous')
            path=source/'data/pilot_lab_cases.json'
            payload=json.loads(path.read_text('utf-8'))
            payload['cases'][0]['expected']='BLOCK'
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,'not reproducible'):
                build(old,source=source,commit='b'*40)
            self.assertEqual((old/'marker').read_text(),'keep previous')

    def test_forged_fork_clearance_preserves_previous_site(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source'
            build(source, commit='a' * 40)
            target = Path(directory) / 'previous'
            target.mkdir()
            (target / 'marker').write_text('keep last good')
            path = source / 'data/adoption_plan.json'
            payload = json.loads(path.read_text('utf-8'))
            payload['items'][0]['fork'] = 'APPROVED'
            path.write_text(json.dumps(payload))
            with self.assertRaisesRegex(ValueError,'promotion'):
                build(target,source=source,commit='b'*40)
            self.assertEqual((target / 'marker').read_text(), 'keep last good')

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
