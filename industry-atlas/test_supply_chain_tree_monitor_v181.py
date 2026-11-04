#!/usr/bin/env python3
"""Ten-source bounded tree SHA monitor has no automatic approvals."""
import json,unittest
from pathlib import Path
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from supply_chain_tree_monitor_v181 import monitor_trees
ROOT=Path(__file__).resolve().parent
S,A,P=load_data()
L=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
F=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
E=json.loads((ROOT/"supply_chain_evidence_v181.json").read_text(encoding="utf-8"))
ASOF="2026-11-04T09:00:00Z"
class TreeMonitorV181(unittest.TestCase):
    def test_offline_no_network(self):
        def impossible(*args):raise AssertionError("Network in offline mode")
        r=monitor_trees(E,L,F,S,A,P,as_of=ASOF,fetcher=impossible)
        self.assertEqual(r["requests_attempted"],0)
        self.assertEqual(r["projects"],10)
        self.assertEqual(r["release_gate"],"HOLD")
    def test_live_requires_ack(self):
        with self.assertRaises(ContractError):
            monitor_trees(E,L,F,S,A,P,as_of=ASOF,mode="live")
    def test_api_failure_does_not_prove_deletion(self):
        r=monitor_trees(E,L,F,S,A,P,as_of=ASOF,mode="live",ack=True,
                        fetcher=lambda *args:{"kind":"unavailable"})
        self.assertTrue(all(x["observation_status"]=="unavailable-not-deleted" for x in r["rows"]))
        self.assertTrue(all(x["source_deleted_verified"] is False for x in r["rows"]))
    def test_sha_change_is_review_only(self):
        seen=[]
        def changed(url,token):
            seen.append(url)
            return {"kind":"ok","data":{"sha":"f"*40}}
        r=monitor_trees(E,L,F,S,A,P,as_of=ASOF,mode="live",ack=True,fetcher=changed)
        self.assertEqual(len(seen),10)
        self.assertTrue(all(url.startswith("https://api.github.com/repos/") and "/git/trees/" in url for url in seen))
        self.assertEqual(r["requests_attempted"],10)
        self.assertEqual(r["tree_drift_count"],10)
        self.assertTrue(all(not x["automatic_approval"] for x in r["rows"]))
        self.assertEqual(r["security_checks_passed"],0)
        self.assertEqual(r["catalog_writes"],0)
    def test_same_sha_is_not_security_certification(self):
        def same(url,token):
            match=next(x for x in E["records"] if x["repo_full_name"] in url)
            return {"kind":"ok","data":{"sha":match["git_tree_sha"]}}
        r=monitor_trees(E,L,F,S,A,P,as_of=ASOF,mode="live",ack=True,fetcher=same)
        self.assertEqual(r["tree_drift_count"],0)
        self.assertTrue(all(x["observation_status"]=="tree-unchanged-not-supply-chain-safe" for x in r["rows"]))
        self.assertTrue(all(x["vulnerability_status"]=="not-checked" for x in r["rows"]))
    def test_invalid_timestamp(self):
        for dt in ("2026-11-03T12:00:00Z","2026-11-04","2026-11-04T21:01:00+11:00"):
            with self.subTest(dt=dt),self.assertRaises(ContractError):
                monitor_trees(E,L,F,S,A,P,as_of=dt)
if __name__=="__main__":
    unittest.main()
