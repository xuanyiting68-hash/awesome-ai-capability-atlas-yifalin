#!/usr/bin/env python3
"""Fail-closed V1.5 recipe data contract. A recipe is a research guide, NOT verified integration."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ID = re.compile(r"^[a-z][a-z0-9_-]{1,31}$")
SCENARIOS = {"content", "growth", "finance", "education"}
LEVELS = {"beginner", "intermediate", "advanced"}


def validate_recipes(data, blueprints, curated, briefs, metadata):
    if data.get("schema_version") != 1 or data.get("version") != "1.5.0":
        raise ValueError("unsupported recipes schema/version")
    if data.get("source_blueprints_version") != blueprints.get("version"):
        raise ValueError("stale source blueprint version")
    if data.get("verified_integration_count") != 0:
        raise ValueError("integrations cannot be promoted without real E2E evidence")
    if "NOT" not in data.get("purpose", "").upper() or "NOT" not in data.get("score_label", "").upper():
        raise ValueError("research limitations not explicit")
    axes = data.get("score_axes", {})
    if not isinstance(axes, dict) or set(axes) != {
        "curated_repo_exists", "official_source_brief", "immutable_source_snapshot",
        "metadata_maintained_recently", "individual_isolated_test", "completed_security_license_audit"
    } or sum(axes.values()) != 100 or any(type(x) is not int or x < 0 for x in axes.values()):
        raise ValueError("incomplete or inflated evidence scoring rubric")
    if data.get("score_cutoffs") != {"recent_days": 90, "older_days": 365}:
        raise ValueError("unversioned freshness thresholds")
    plans = {x["id"]: x for x in blueprints["blueprints"]}
    allowed = {x["repo"].lower(): x for x in curated}
    research = {x["repo"].lower(): x for x in briefs["entries"]}
    if len(allowed) != len(curated) or len(research) != 30:
        raise ValueError("source data missing or duplicated")
    if not isinstance(metadata.get("repositories"), dict) or not metadata.get("generated_at_utc"):
        raise ValueError("metadata provenance missing")
    items = data.get("recipes")
    if not isinstance(items, list) or len(items) != len(plans) or len(items) != 6:
        raise ValueError("expected six canonical recipes")
    ids = set()
    repo_refs = set()
    for item in items:
        rid = item.get("id")
        if not isinstance(rid, str) or not ID.fullmatch(rid) or rid not in plans or rid in ids:
            raise ValueError("invalid or duplicated recipe ID")
        ids.add(rid)
        bp = plans[rid]
        if item.get("title_zh") != bp["name"]:
            raise ValueError("recipe no longer matches source blueprint title")
        if item.get("scenario") not in SCENARIOS or item.get("difficulty") not in LEVELS:
            raise ValueError("unsafe scenario or skill level")
        if (item.get("status"), item.get("license_review"), item.get("security_review")) != (
            "reference-not-integrated", "not-reviewed", "not-audited"
        ):
            raise ValueError("unreviewed reference promoted to integrated/safe")
        tools = item.get("tools")
        if tools != bp["tools"] or len(tools) < 3:
            raise ValueError("tool composition drifted from provenance")
        for repo in tools:
            if not REPO.fullmatch(repo) or repo.lower() not in allowed:
                raise ValueError("unknown, non-curated or unsafe tool " + str(repo))
            repo_refs.add(repo.lower())
            if allowed[repo.lower()].get("safety_review") != "not-audited":
                raise ValueError("source audit status changed; review rubric before release")
        steps = item.get("steps")
        if not isinstance(steps, list) or len(steps) != len(bp["stages"]) or len(steps) < 4:
            raise ValueError("manual reproduction steps incomplete")
        for index, step in enumerate(steps, 1):
            if (step.get("order") != index or step.get("label_zh") != bp["stages"][index-1]
                    or step.get("candidate_repo") not in [None, *tools]
                    or step.get("gate") not in ("human-approval", "manual-review")
                    or not isinstance(step.get("label_en"), str)
                    or len(step["label_en"]) < 12
                    or step.get("output_marker") != f"step-{index}.md"):
                raise ValueError("untraceable step or missing evidence output")
        if steps[0]["gate"] != "human-approval" or steps[-1]["gate"] != "human-approval":
            raise ValueError("bookend human approvals required")
        for key in ("goal_zh", "goal_en", "stop_condition_zh", "stop_condition_en"):
            if not isinstance(item.get(key), str) or len(item[key]) < 12:
                raise ValueError("missing bilingual goal / stop gate")
        for key in ("inputs_zh", "inputs_en", "outputs_zh", "outputs_en",
                    "acceptance_zh", "acceptance_en"):
            vals = item.get(key)
            if not isinstance(vals, list) or len(vals) < 2 or any(not isinstance(v, str) or len(v.strip()) < 6 for v in vals):
                raise ValueError("reproduction evidence missing " + key)
        if not isinstance(item.get("guardrails_en"), list) or len(item["guardrails_en"]) != len(bp["guardrails"]) or any(len(v) < 12 for v in item["guardrails_en"]):
            raise ValueError("incomplete English safety guardrails")
        if item.get("guardrails_zh") != bp["guardrails"] or item.get("metrics_zh") != bp["kpis"]:
            raise ValueError("blueprint guardrails or KPIs were silently altered")
        demo = item.get("offline_demo_path")
        if demo is not None and (rid != "leads" or demo != "examples/consent_lead_triage/run_demo.py"):
            raise ValueError("unverified or external demo path")
    if ids != set(plans) or len(repo_refs) < 15:
        raise ValueError("source blueprint coverage incomplete")
    return {"recipes_count": len(ids), "unique_curated_tool_refs": len(repo_refs),
            "verified_integrations": 0, "scoring_max": sum(axes.values())}


def validate_from_files(root=ROOT):
    root = Path(root)
    def read(name):
        return json.loads((root/name).read_text("utf-8"))
    return validate_recipes(read("data/capability_recipes.json"), read("data/blueprints.json"),
                            read("data/curated.json"), read("data/research_briefs.json"),
                            read("data/repo_metadata.json"))


if __name__ == "__main__":
    print(validate_from_files())
