import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class BlueprintTests(unittest.TestCase):
    def test_six_risk_gated_blueprints(self):
        d=json.loads((ROOT/'data'/'blueprints.json').read_text('utf-8'))
        plans=d['blueprints']
        self.assertEqual(len(plans),6)
        self.assertEqual({p['id'] for p in plans},{'video','social','leads','crm','finance','education'})
        for p in plans:
            self.assertEqual(p['status'],'not-implemented')
            self.assertEqual(p['security_review'],'not-audited')
            self.assertEqual(p['commercial_license_review'],'not-checked')
            self.assertGreaterEqual(len(p['tools']),3)
            self.assertGreaterEqual(len(p['stages']),4)
            self.assertTrue(p['guardrails'])
    def test_source_filter_and_blueprint_links(self):
        html=(ROOT/'index.html').read_text('utf-8')
        self.assertIn('id="sourceFilter"',html)
        self.assertIn('id="blueprintsPanel"',html)
        self.assertIn('data-view="blueprints"',html)
        self.assertIn('source_kind',html)
        for name in ['video','social','leads','crm','finance','education']:
            self.assertIn('docs/BLUEPRINTS_CN.md#'+name,html)
        docs=(ROOT/'docs'/'BLUEPRINTS_CN.md').read_text('utf-8')
        for name in ['video','social','leads','crm','finance','education']:
            self.assertIn('<a id="'+name+'"></a>',docs)
    def test_source_policy_exists(self):
        doc=(ROOT/'docs'/'SOURCE_AND_REVIEW_CN.md').read_text('utf-8')
        self.assertIn('not-audited',doc)
        self.assertIn('license_review',doc)

if __name__=='__main__': unittest.main()
