"""Fail-closed policy for scheduled public repository metadata updates."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class RefreshWorkflowPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow=(ROOT/'.github/workflows/repo-metadata.yml').read_text('utf-8')

    def test_never_push_protected_main(self):
        self.assertNotIn('git push origin HEAD:main',self.workflow)
        self.assertNotIn('gh workflow run pages.yml',self.workflow)
        self.assertIn('git push origin HEAD:"refs/heads/$branch"',self.workflow)

    def test_validated_data_preserved_before_any_review_pr(self):
        self.assertLess(self.workflow.index('Verify generated evidence invariants'),
                        self.workflow.index('Preserve generated evidence for review'))
        self.assertLess(self.workflow.index('uses: actions/upload-artifact@v4'),
                        self.workflow.index('gh pr create --base main'))
        self.assertIn('data/repo_metadata.json',self.workflow)
        self.assertIn('data/top30_evidence.json',self.workflow)

    def test_schedule_and_manual_must_propose_draft_only(self):
        self.assertIn('workflow_dispatch:',self.workflow)
        self.assertIn("cron: '34 2 * * 3'",self.workflow)
        self.assertIn('gh pr create --base main --head "$branch" --draft',self.workflow)
        self.assertNotIn('gh pr merge',self.workflow)

    def test_separate_read_only_pr_validator(self):
        self.assertIn('validate-pr:',self.workflow)
        self.assertIn("if: github.event_name == 'pull_request'",self.workflow)
        self.assertIn('persist-credentials: false',self.workflow)
        self.assertIn("if: github.event_name != 'pull_request'",self.workflow)
        self.assertIn('pull-requests: write',self.workflow)
        self.assertIn('  contents: read\njobs:',self.workflow)

    def test_snapshot_proposal_not_construed_as_audited_safe(self):
        self.assertIn('not approved safety or software licenses',self.workflow)
        self.assertIn('review-only public metadata',self.workflow)


if __name__=='__main__':
    unittest.main()
