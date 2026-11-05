#!/usr/bin/env python3
"""V1.8.0 live monitor tests: fixed allowlist and no silent source approval."""
import copy,json,unittest
from pathlib import Path
from provider_contract_v174 import ContractError
from coverage_review_v177 import load_data
from source_monitor_v180 import monitor

ROOT=Path(__file__).resolve().parent
L=json.loads((ROOT/"external_leads_v179.json").read_text(encoding="utf-8"))
F=json.loads((ROOT/"license_file_evidence_v180.json").read_text(encoding="utf-8"))
S,A,P=load_data()
ASOF="2026-11-04T08:45:00Z"

class SourceMonitorV180(unittest.TestCase):
    def test_offline_does_not_call_network(self):
        def disallowed(*args):
            raise AssertionError("Offline attempted network")
        r=monitor(L,F,S,A,P,as_of=ASOF,fetcher=disallowed)
        self.assertEqual(r["mode"],"offline")
        self.assertEqual(r["network_requests_attempted"],0)
        self.assertEqual(r["approval_count"],0)
        self.assertEqual(len(r["entries"]),10)
        self.assertEqual(r["release_gate"],"HOLD")
    def test_live_requires_explicit_ack(self):
        with self.assertRaises(ContractError):
            monitor(L,F,S,A,P,as_of=ASOF,mode="live")
    def test_bounded_known_https_endpoints(self):
        seen=[]
        def fake(url,token):
            seen.append(url)
            if "/contents/" in url:
                q=next(f for f in F["records"] if f["repo_full_name"] in url)
                return {"kind":"ok","data":{"type":"file","path":q["license_file_path"],"sha":q["license_blob_sha"]}}
            l=next(x for x in L["records"] if x["repo_full_name"] in url)
            return {"kind":"ok","data":{"id":l["repo_id"],"full_name":l["repo_full_name"],
                    "archived":False,"disabled":False,
                    "default_branch":l["observed_metadata"]["default_branch"],
                    "license":{"spdx_id":l["observed_metadata"]["license_spdx_signal"]}}}
        r=monitor(L,F,S,A,P,as_of=ASOF,mode="live",ack=True,fetcher=fake)
        self.assertEqual(len(seen),20)
        self.assertTrue(all(u.startswith("https://api.github.com/repos/") for u in seen))
        self.assertTrue(all(x["file_status"]=="blob-unchanged" for x in r["entries"]))
        self.assertTrue(all(not x["auto_approved"] for x in r["entries"]))
        self.assertEqual(r["verified_license_count"],0)
        self.assertEqual(r["identity_metadata_observed"],10)
    def test_license_file_sha_drift_not_approved(self):
        def fake(url,token):
            if "/contents/" in url:
                q=next(x for x in F["records"] if x["repo_full_name"] in url)
                return {"kind":"ok","data":{"type":"file","path":q["license_file_path"],"sha":"a"*40}}
            l=next(x for x in L["records"] if x["repo_full_name"] in url)
            return {"kind":"ok","data":{"id":l["repo_id"],"full_name":l["repo_full_name"],
                         "archived":False,"disabled":False,
                         "default_branch":l["observed_metadata"]["default_branch"],
                         "license":{"spdx_id":l["observed_metadata"]["license_spdx_signal"]}}}
        r=monitor(L,F,S,A,P,as_of=ASOF,mode="live",ack=True,fetcher=fake)
        self.assertTrue(all(x["file_status"]=="blob-changed-review" for x in r["entries"]))
        self.assertTrue(all(x["observation_status"]=="needs-review" for x in r["entries"]))
        self.assertEqual(r["approval_count"],0)
    def test_api_failure_not_repo_deletion(self):
        r=monitor(L,F,S,A,P,as_of=ASOF,mode="live",ack=True,
                  fetcher=lambda url,token:{"kind":"unavailable","reason":"http-404"})
        self.assertEqual(r["source_deletion_verified_count"],0)
        self.assertTrue(all(x["metadata_status"]=="unavailable" for x in r["entries"]))
        self.assertTrue(all("not-deletion" in x["flags"][0] for x in r["entries"]))
    def test_no_prior_date_and_strict_utc(self):
        for dt in ("2026-11-03T12:00:00Z","2026-11-04","2026-11-04T12:00:00+11:00"):
            with self.subTest(dt=dt),self.assertRaises(ContractError):
                monitor(L,F,S,A,P,as_of=dt)
    def test_snapshot_untouched(self):
        old=copy.deepcopy((L,F,S,A,P))
        monitor(L,F,S,A,P,as_of=ASOF)
        self.assertEqual(old,(L,F,S,A,P))
if __name__=="__main__":
    unittest.main()
