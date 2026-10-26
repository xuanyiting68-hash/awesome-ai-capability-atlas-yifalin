#!/usr/bin/env python3
"""Fail-closed validation for source-linked, editorial-only project research briefs.

No third-party code is installed or executed. Promotion to a higher evidence tier
requires independently recorded artifacts, not GitHub stars/SPDX/push activity.
"""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SHA40 = re.compile(r"^[a-f0-9]{40}$")
SLUG = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ALLOWED_DOCS = {
    "microsoft/qlib": "qlib.readthedocs.io",
    "langchain-ai/langgraph": "docs.langchain.com",
    "remotion-dev/remotion": "www.remotion.dev",
    "twentyhq/twenty": "docs.twenty.com",
    "microsoft/rd-agent": "rdagent.readthedocs.io",
    "docling-project/docling": "docling-project.github.io",
    "langgenius/dify": "docs.dify.ai",
    "systran/faster-whisper": "pypi.org",
    "formbricks/formbricks": "formbricks.com",
    "promptfoo/promptfoo": "www.promptfoo.dev",
}
TIERS = ("Discovery", "Curated", "Reviewed", "Reproduced", "Production Candidate")
STATUS = {"license_text":"not-reviewed", "dependency_licenses":"not-reviewed",
          "security":"not-audited","reproducibility":"not-tested",
          "sandbox_sha":None,"fork_decision":"HOLD"}


def fail(message):
    raise ValueError("research briefs: " + message)


def require(condition, message):
    if not condition:
        fail(message)


def source_url(url, allowed_host):
    try:
        value = urlsplit(url)
    except (ValueError, TypeError):
        return False
    return value.scheme == "https" and value.hostname == allowed_host and not (
        value.username or value.password or value.port or value.fragment
    )


def nonempty_i18n(value):
    return isinstance(value, dict) and all(isinstance(value.get(l), str)
        and 10 <= len(value[l].strip()) <= 600 for l in ("zh", "en"))


def validate_briefs(payload, top30, snapshot, metadata, as_of=None):
    require(isinstance(payload, dict) and payload.get("schema_version") == 1, "unsupported schema")
    require(payload.get("policy", "").startswith("Official documentation review"), "missing editorial boundary")
    checked = payload.get("researched_at_utc")
    try:
        stamp = datetime.fromisoformat(checked.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        fail("invalid research timestamp")
    require(stamp.tzinfo is not None and stamp.utcoffset() is not None, "timestamp lacks UTC offset")
    as_of = as_of or datetime.now(timezone.utc)
    require(stamp.astimezone(timezone.utc) <= as_of.astimezone(timezone.utc), "research timestamp is in the future")
    require(isinstance(payload.get("entries"), list) and 1 <= len(payload["entries"]) <= 30,
            "brief record count outside range")
    allowed_repos = {x["github_repository"].lower() for x in top30}
    evidence_by_repo = {p["repo"].lower():p for p in snapshot["projects"]}
    known_meta = metadata["repositories"]
    require(len(allowed_repos) == 30, "Top 30 baseline malformed")
    seen = set()
    for entry in payload["entries"]:
        require(isinstance(entry, dict), "brief is not an object")
        slug = entry.get("repo")
        require(isinstance(slug, str) and SLUG.fullmatch(slug), "invalid repository slug")
        key = slug.lower()
        require(key not in seen and key in allowed_repos and key in known_meta and key in evidence_by_repo,
                "duplicate or unknown repository " + key)
        seen.add(key)
        require(entry.get("tier") in TIERS, "unknown quality tier for " + key)
        require(entry.get("research_status") == "editorial-desk-study", "unsupported research status " + key)
        for field in ("headline","best_for","not_for"):
            require(nonempty_i18n(entry.get(field)), "invalid " + field + " for " + key)
        sources = entry.get("sources")
        require(isinstance(sources, list) and len(sources) == 2, "expected official README and docs " + key)
        refs = {}
        for source in sources:
            require(isinstance(source, dict) and source.get("id") in ("readme", "docs"),
                    "unexpected source type " + key)
            sid = source["id"]
            require(sid not in refs, "duplicate source ID " + key)
            refs[sid] = source
        require(set(refs) == {"readme","docs"}, "missing official source " + key)
        readme, docs = refs["readme"], refs["docs"]
        sha = readme.get("git_blob_sha")
        require(readme.get("kind") == "official-github-readme" and isinstance(sha,str)
                and SHA40.fullmatch(sha), "README blob missing pin " + key)
        branch = readme.get("readme_ref", "main")
        require(branch in ("main","master"), "README ref must be the exact repository default branch " + key)
        require(readme.get("url") == "https://github.com/" + slug + "/blob/" + branch + "/README.md",
                "README identity mismatch " + key)
        require(readme.get("snapshot_url") == "https://api.github.com/repos/" + slug + "/git/blobs/" + sha,
                "immutable blob URL mismatch " + key)
        require(docs.get("kind") == "official-documentation", "docs source type invalid " + key)
        host = ALLOWED_DOCS.get(key)
        require(host is not None and source_url(docs.get("url"), host), "documentation not from allowlisted official host " + key)
        claims = entry.get("capabilities")
        require(isinstance(claims, list) and len(claims) >= 2,
                "not enough grounded capability claims " + key)
        for claim in [*claims, entry.get("limitations")]:
            require(isinstance(claim,dict) and nonempty_i18n(claim), "claim languages missing " + key)
            ids = claim.get("source_ids")
            require(isinstance(ids,list) and len(ids) > 0 and
                    all(s in refs for s in ids), "claim without official source ID " + key)
        pilot = entry.get("pilot")
        require(isinstance(pilot,dict) and nonempty_i18n(pilot.get("metrics"))
                and nonempty_i18n(pilot), "pilot missing definition or metrics " + key)
        steps = pilot.get("steps")
        require(isinstance(steps,list) and 3 <= len(steps) <= 6
                and all(nonempty_i18n(s) for s in steps), "pilot steps invalid " + key)
        alternatives = entry.get("alternatives")
        require(isinstance(alternatives,list) and 1 <= len(alternatives) <= 4
                and all(isinstance(a,str) and SLUG.fullmatch(a) and a.lower()!=key for a in alternatives),
                "comparison candidates invalid " + key)
        review = entry.get("review")
        require(isinstance(review,dict), "review object missing " + key)
        ev = evidence_by_repo[key]
        # The pilot never promotes a project beyond the existing, explicitly
        # unreviewed Top 30 evidence. Future promotion requires a new gated format.
        require(entry["tier"] == "Curated" and all(review.get(k) == v for k,v in STATUS.items()),
                "evidence promotion without third-party review " + key)
        require(ev.get("fork_decision") == "HOLD" and ev.get("reproducibility") == "not-tested"
                and ev.get("security_review") == "not-audited" and
                ev.get("license_text_review") == "not-reviewed", "existing evidence conflicts " + key)
    return {"count":len(seen),"curated":len(seen),"reviewed":0,"reproduced":0,"production_candidates":0}


def validate_from_files(root=ROOT):
    root = Path(root)
    records = json.loads((root / "data/research_briefs.json").read_text(encoding="utf-8"))
    with (root / "data/top30_evaluation.csv").open(encoding="utf-8-sig", newline="") as stream:
        top30 = list(csv.DictReader(stream))
    snapshot = json.loads((root / "data/top30_evidence.json").read_text(encoding="utf-8"))
    metadata = json.loads((root / "data/repo_metadata.json").read_text(encoding="utf-8"))
    return validate_briefs(records, top30, snapshot, metadata)


if __name__ == "__main__":
    print(json.dumps(validate_from_files(), sort_keys=True))
