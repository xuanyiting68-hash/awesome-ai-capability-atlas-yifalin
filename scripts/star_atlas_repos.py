#!/usr/bin/env python3
"""Opt-in GitHub Star batch for YIFALIN's verified Top 30.

Default: DRY RUN, no GitHub call.
Apply: python scripts/star_atlas_repos.py --apply
Requires GitHub CLI (gh) already authenticated to the intended user account.
Never asks for a token, stores credentials, forks or clones repositories.
"""
import argparse
import shutil
import subprocess
if __package__:
    from .validate_adoption import ROOT, validate_from_files
else:
    from validate_adoption import ROOT, validate_from_files
import json


def get_targets(priority_only=False, root=ROOT):
    validate_from_files(root)
    plan = json.loads((root / "data/adoption_plan.json").read_text("utf-8"))
    chosen = [i["canonical_repo"] for i in plan["items"]
              if i["star"] == "recommend" and (not priority_only or i["priority"] == "P0")]
    if len(set(x.lower() for x in chosen)) != len(chosen):
        raise ValueError("duplicate canonical upstream")
    return chosen


def main(argv=None):
    parser = argparse.ArgumentParser(description="30 upstream bookmarks; read-only unless --apply is supplied")
    parser.add_argument("--apply", action="store_true", help="EXPLICITLY execute GitHub Star calls using authenticated gh")
    parser.add_argument("--priority-only", action="store_true", help="Limit to the eight P0 integration candidates")
    args = parser.parse_args(argv)
    targets = get_targets(args.priority_only)
    if not args.apply:
        print("DRY RUN — no account actions. To Star: gh auth login; then rerun with --apply")
        for i, slug in enumerate(targets, 1):
            print(f"{i:02d}. https://github.com/{slug}")
        print(f"{len(targets)} repositories ready; 0 Star actions executed.")
        return 0
    if not shutil.which("gh"):
        parser.error("GitHub CLI 'gh' not found. Install gh and authenticate in the correct account.")
    auth = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if auth.returncode:
        parser.error("GitHub CLI is not authenticated. Run 'gh auth login' first.")
    print(f"Star mode: authenticated GitHub account; submitting {len(targets)} idempotent PUT calls.")
    success, failed = 0, []
    for slug in targets:
        res = subprocess.run(
            ["gh", "api", "-X", "PUT", "-H", "Accept: application/vnd.github+json",
             "/user/starred/" + slug], capture_output=True, text=True)
        if res.returncode == 0:
            success += 1
            print("STAR OK: " + slug)
        else:
            failed.append(slug)
            # Do not print stdout/stderr: gh output may contain private context.
            print("STAR FAILED: " + slug)
    print(f"API results: {success} succeeded, {len(failed)} failed. No forks performed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
