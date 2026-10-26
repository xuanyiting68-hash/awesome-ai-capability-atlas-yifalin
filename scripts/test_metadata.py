import unittest
from scripts.sync_repo_metadata import normalise, VALID_REPO
class MetadataTests(unittest.TestCase):
    def test_repo_normalization(self):
        m=normalise("a/B",{"stargazers_count":1203,"forks_count":6,"archived":False,"license":{"spdx_id":"MIT"},"pushed_at":"2026-10-20T08:00:00Z"})
        self.assertEqual(m["stars"],1203)
        self.assertEqual(m["license_spdx"],"MIT")
        self.assertFalse(m["archived"])
    def test_unknown_license(self):
        self.assertEqual(normalise("a/b",{"license":None})["license_spdx"],"unknown")
        self.assertEqual(normalise("a/b",{"license":{"spdx_id":"NOASSERTION"}})["license_spdx"],"unknown")
    def test_repo_slug(self):
        self.assertIsNotNone(VALID_REPO.fullmatch("test-org/Sample_1"))
        self.assertIsNone(VALID_REPO.fullmatch("../private"))
if __name__=="__main__":unittest.main()
