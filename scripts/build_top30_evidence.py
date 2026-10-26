#!/usr/bin/env python3
"""Compile a traceable Top 30 evidence snapshot from committed metadata; no code execution."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build(rows, metadata):
    source=metadata.get("repositories",{})
    output=[]
    for row in rows:
        slug=row["github_repository"]
        m=source.get(slug.lower())
        if m is None:
            raise ValueError("Missing metadata: "+slug)
        spdx=m.get("license_spdx") or "unknown"
        output.append({
            "rank":int(row["rank"]),"repo":slug,"domain":row["domain"],
            "research_priority":row["research_priority"],
            "source_repository_url":row["url"],
            "metadata_source_url":"https://api.github.com/repos/"+slug,
            "github_stars":m.get("stars"),"github_forks":m.get("forks"),
            "github_license_spdx_detected":spdx,
            "github_last_push":m.get("last_push"),
            "github_archived":m.get("archived"),
            "license_text_review":"not-reviewed",
            "dependency_license_review":"not-reviewed",
            "security_review":"not-audited",
            "reproducibility":"not-tested",
            "sandbox_commit_sha":None,
            "fork_decision":"HOLD",
            "reason":"GitHub metadata only. License, dependencies, sandbox execution and legal review incomplete."
        })
    return output
def main():
    with (ROOT/"data/top30_evaluation.csv").open(encoding="utf-8-sig",newline="") as f:
        rows=list(csv.DictReader(f))
    metadata=json.loads((ROOT/"data/repo_metadata.json").read_text("utf-8"))
    if len(rows)!=30: raise ValueError("Expected 30 entries")
    output={"schema_version":"1.0","generated_from_snapshot_utc":metadata["generated_at_utc"],
            "generated_at_utc":metadata["generated_at_utc"],
            "metadata_source":"data/repo_metadata.json",
            "disclaimer":"Github metadata is not evidence of safety, commercial clearance, or reproducible performance.",
            "reviewed_license_count":0,"approved_fork_count":0,
            "projects":build(rows,metadata)}
    (ROOT/"data/top30_evidence.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Evidence rows:",len(output["projects"]),"approved forks:",0)
if __name__=="__main__": main()
