#!/usr/bin/env python3
"""Fail-closed checks for Atlas bookmark/integration recommendations.

This is an action plan, NOT a representation of actual GitHub stars/forks,
third-party license clearance, installed integrations or security audits.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def check_adoption(plan, rows, briefs):
    if not isinstance(plan, dict) or plan.get("schema_version") != 1:
        raise ValueError("adoption: unsupported schema")
    for key in ("basis", "star_policy", "fork_policy", "integration_policy"):
        if not isinstance(plan.get(key), str) or len(plan[key]) < 24:
            raise ValueError("adoption: policy missing " + key)
    projects = {r["github_repository"].lower(): r for r in rows}
    source = {r["repo"].lower(): r for r in briefs["entries"]}
    items = plan.get("items")
    if len(projects) != 30 or not isinstance(items, list) or len(items) != 30 or set(projects) != set(source):
        raise ValueError("adoption: incomplete Top 30 baseline")
    seen, priority = set(), 0
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("adoption: item invalid")
        slug = item.get("repo")
        if not isinstance(slug, str) or not REPO.fullmatch(slug):
            raise ValueError("adoption: unsafe repository name")
        key = slug.lower()
        if key not in projects or key in seen:
            raise ValueError("adoption: duplicate or unknown repository " + key)
        seen.add(key)
        entry = source[key]
        readme = next(s for s in entry["sources"] if s["id"] == "readme")
        canonical = readme.get("canonical_repo", entry["repo"])
        if item.get("canonical_repo") != canonical or not REPO.fullmatch(canonical):
            raise ValueError("adoption: canonical upstream mismatch " + key)
        if item.get("rank") != int(projects[key]["rank"]) or item.get("domain") != projects[key]["domain"]:
            raise ValueError("adoption: Top 30 rank/domain mismatch " + key)
        if (item.get("star"), item.get("star_execution"), item.get("fork"), item.get("integration_state")) != (
                "recommend", "not-verified", "HOLD", "not-integrated"):
            raise ValueError("adoption: unverified star, fork or integration promotion " + key)
        if item.get("priority") not in ("P0", "P1"):
            raise ValueError("adoption: priority invalid")
        if item["priority"] == "P0":
            priority += 1
            if not isinstance(item.get("workstream"), str) or len(item["workstream"]) < 5:
                raise ValueError("adoption: P0 workstream missing " + key)
            fit = item.get("pilot_fit")
            if not isinstance(fit, dict) or any(not isinstance(fit.get(l), str) or len(fit[l]) < 15 for l in ("zh", "en")):
                raise ValueError("adoption: P0 bilingual fit missing " + key)
        elif "pilot_fit" in item or "workstream" in item:
            raise ValueError("adoption: P1 should not imply an approved pilot")
        # Never claim that the license was checked merely by viewing GitHub metadata.
        if entry["review"]["fork_decision"] != "HOLD" or entry["review"]["reproducibility"] != "not-tested":
            raise ValueError("adoption: conflicting research review " + key)
    if seen != set(projects) or priority != 8:
        raise ValueError("adoption: expected 30 candidates with exactly 8 P0")
    return {"star_shortlist_count": 30, "priority_integration_candidates": 8,
            "fork_approved_count": 0, "star_actions_executed_by_atlas": 0}


def validate_from_files(root=ROOT):
    root = Path(root)
    plan = json.loads((root / "data/adoption_plan.json").read_text("utf-8"))
    briefs = json.loads((root / "data/research_briefs.json").read_text("utf-8"))
    with (root / "data/top30_evaluation.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return check_adoption(plan, rows, briefs)


if __name__ == "__main__":
    print(json.dumps(validate_from_files(), sort_keys=True))
