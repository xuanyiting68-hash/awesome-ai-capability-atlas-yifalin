#!/usr/bin/env python3
"""Fetch public GitHub repository metadata. Never clones or executes third-party code."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import os
import re
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
VALID_REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
DEST=ROOT/"data"/"repo_metadata.json"

def normalise(full, data):
    if not isinstance(data,dict):
        raise ValueError("GitHub response must be a JSON object")
    lic=(data.get("license") or {}).get("spdx_id") or "unknown"
    if lic=="NOASSERTION": lic="unknown"
    return {"name":full,"stars":int(data.get("stargazers_count") or 0),
            "forks":int(data.get("forks_count") or 0),
            "last_push":data.get("pushed_at") or None,
            "archived":bool(data.get("archived")),
            "license_spdx":lic,
            "github_url":data.get("html_url") or "https://github.com/"+full}

def fetch(full):
    token=os.environ.get("GITHUB_TOKEN","")
    headers={"Accept":"application/vnd.github+json","User-Agent":"YIFALIN-Capability-Atlas/1.2",
             "X-GitHub-Api-Version":"2022-11-28"}
    if token:headers["Authorization"]="Bearer "+token
    for attempt in range(3):
        try:
            with urlopen(Request("https://api.github.com/repos/"+full,headers=headers),timeout=16) as response:
                raw=json.load(response)
            return full.lower(),normalise(full,raw)
        except HTTPError as err:
            if err.code in (403,429,500,502,503) and attempt<2:
                time.sleep(2*(attempt+1))
                continue
            raise RuntimeError(f"{full}: HTTP {err.code}") from err
        except (URLError,TimeoutError) as err:
            if attempt<2:
                time.sleep(2*(attempt+1))
                continue
            raise RuntimeError(f"{full}: network error") from err

def main():
    curated=json.loads((ROOT/"data"/"curated.json").read_text("utf-8"))
    names=sorted({str(r.get("repo","")).strip()
       for r in curated
       if str(r.get("url","")).startswith("https://github.com/")
       and VALID_REPO.fullmatch(str(r.get("repo","")).strip())})
    if len(names)<100: raise RuntimeError(f"Insufficient curated GitHub repos: {len(names)}")
    if not os.environ.get("GITHUB_TOKEN"): raise RuntimeError("GITHUB_TOKEN is required")
    known={}
    errors=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(fetch,n):n for n in names}
        for future in as_completed(futures):
            try:
                key,metadata=future.result()
                known[key]=metadata
            except Exception as err:
                errors.append(str(err))
    if errors:
        print("Failed closed, preserved last full snapshot:",json.dumps(errors[:25],ensure_ascii=False),file=sys.stderr)
        return 2
    data={"generated_at_utc":datetime.now(timezone.utc).isoformat(),
          "source":"Public GitHub REST API",
          "disclaimer":"Stars do not prove quality; GitHub SPDX is an indicator, not a commercial license clearance.",
          "coverage_count":len(known),"expected_count":len(names),
          "repositories":dict(sorted(known.items()))}
    DEST.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Updated",len(known),"GitHub public metadata entries")
    return 0
if __name__=="__main__":raise SystemExit(main())
