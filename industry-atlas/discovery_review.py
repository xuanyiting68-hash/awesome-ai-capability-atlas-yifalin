#!/usr/bin/env python3
"""YIFALIN discovery-to-review pipeline. Metadata only; no plugin/skill execution.

Two non-promotional channels:
  --mode offline: re-rank existing Atlas index with cached metadata (no network).
  --mode live: bounded official GitHub search + Hugging Face public model metadata.

Every output is an *unreviewed candidate queue*, never a trusted recommendation.
The script never changes curated.json, catalog.json, Atlas deployment or GitHub.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from xml.etree import ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FETCH_HOSTS = {"api.github.com", "huggingface.co", "export.arxiv.org"}
ALLOWED_LINK_HOSTS = {"github.com", "huggingface.co", "arxiv.org", "clawskills.sh"}
MAX_RESPONSE = 2_500_000
MAX_LIVE = 90
MAX_OFFLINE = 250
USER_AGENT = "YIFALIN-Atlas-Discovery-Review/1.1 (metadata-only, 4 bounded queries)"
KNOWN_PUBLISHERS = {"openai", "anthropics", "microsoft", "google", "huggingface", "meta-llama"}
TOPICS = [
    ("s02", ("quant", "trading", "portfolio", "stock", "investment", "finance", "factor", "finance")),
    ("s09", ("manufacturing", "industry", "production", "predictive maintenance", "industrial")),
    ("s06", ("teacher", "school", "classroom", "student", "lesson")),
    ("s04", ("medical", "hospital", "clinical", "healthcare", "radiology")),
    ("s15", ("logistics", "supply chain", "warehouse", "inventory", "shipping")),
    ("s17", ("agriculture", "farming", "crop", "soil")),
    ("s21", ("legal", "lawyer", "contract", "litigation")),
    ("s29", ("restaurant", "hospitality", "hotel", "travel")),
    ("s30", ("coding", "developer", "software", "code assistant", "devops")),
    ("s25", ("government", "public service", "civic", "policy")),
]
UNSAFE_WORDS = ("credential stealer", "keylogger", "crack", "malware", "password dump")
VALID_KINDS = {"skill", "agent", "workflow", "model", "project", "tool", "paper", "repository", "mcp"}
ALLOWED_SOURCE_KIND = {"existing-catalog", "github-api", "huggingface-api", "arxiv-api"}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise ValueError("Redirect rejected: discovery API host must not change")


def canonical_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw.startswith("https://") or len(raw) > 700:
        return ""
    parts = urlsplit(raw)
    if parts.hostname not in ALLOWED_LINK_HOSTS or parts.username or parts.password or parts.port:
        return ""
    path = re.sub(r"/+", "/", parts.path).rstrip("/") or "/"
    return urlunsplit(("https", parts.hostname.lower(), path, "", ""))


def request_json(url: str) -> object:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_FETCH_HOSTS or parts.port or parts.username:
        raise ValueError("Unapproved discovery endpoint")
    headers = {"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json" if parts.hostname == "api.github.com" else "application/json"}
    token = os.environ.get("GITHUB_TOKEN", "")
    if token and parts.hostname == "api.github.com":
        headers["Authorization"] = "Bearer " + token
    req = Request(url, headers=headers)
    try:
        with build_opener(NoRedirect()).open(req, timeout=18) as response:
            if response.status != 200 or urlsplit(response.geturl()).hostname != parts.hostname:
                raise RuntimeError("Invalid discovery response")
            payload = response.read(MAX_RESPONSE + 1)
    except (HTTPError, URLError, TimeoutError) as error:
        # No blind retries on 403/429; preserve prior successful snapshot.
        raise RuntimeError("Public source unavailable; no partial queue published: " + str(error)) from error
    if len(payload) > MAX_RESPONSE:
        raise ValueError("Public metadata response exceeded byte limit")
    return json.loads(payload.decode("utf-8"))



def request_atom(url: str) -> ET.Element:
    """One bounded arXiv official Atom request, never full-paper crawling."""
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != "export.arxiv.org" or parts.port or parts.username:
        raise ValueError("Unapproved arXiv endpoint")
    req = Request(url, headers={"Accept": "application/atom+xml", "User-Agent": USER_AGENT})
    try:
        with build_opener(NoRedirect()).open(req, timeout=18) as response:
            if response.status != 200 or urlsplit(response.geturl()).hostname != "export.arxiv.org":
                raise RuntimeError("Invalid arXiv response")
            payload = response.read(MAX_RESPONSE + 1)
    except (HTTPError, URLError, TimeoutError) as error:
        raise RuntimeError("arXiv metadata unavailable; previous queue preserved: " + str(error)) from error
    if len(payload) > MAX_RESPONSE:
        raise ValueError("arXiv metadata exceeded byte limit")
    root = ET.fromstring(payload)
    if root.tag != "{http://www.w3.org/2005/Atom}feed":
        raise ValueError("Unexpected arXiv Atom structure")
    return root


def arxiv_candidates() -> list[dict]:
    url = "https://export.arxiv.org/api/query?" + urlencode({
        "search_query": "cat:cs.AI OR cat:cs.LG", "start": "0",
        "max_results": "20", "sortBy": "submittedDate", "sortOrder": "descending",
    })
    root = request_atom(url)
    ns = "{http://www.w3.org/2005/Atom}"
    rows = []
    for entry in root.findall(ns + "entry"):
        identifier = entry.findtext(ns + "id") or ""
        # arXiv ID, not untrusted Atom link: construct a canonical HTTPS abstract URL.
        match = re.search(r"/abs/(\d{4}\.\d{4,5}(?:v\d+)?)$", identifier)
        if not match:
            continue
        title = " ".join((entry.findtext(ns + "title") or "").split())
        summary = " ".join((entry.findtext(ns + "summary") or "").split())[:450]
        rows.append({
            "name": title[:120], "url": "https://arxiv.org/abs/" + match.group(1),
            "kind": "paper", "description": summary, "source_kind": "arxiv-api",
            "source_url": "https://arxiv.org/abs/" + match.group(1),
            "owner": "arxiv", "last_modified": entry.findtext(ns + "updated") or "",
            # Individual preprints have varying rights; metadata is not permission to republish.
            "license_spdx": "unknown",
        })
    return rows

def age_days(iso_date: str, now: datetime) -> int | None:
    try:
        date = datetime.fromisoformat(str(iso_date).replace("Z", "+00:00"))
        if date.tzinfo is None:
            return None
        return max(0, (now - date.astimezone(timezone.utc)).days)
    except (ValueError, TypeError):
        return None


def infer_sectors(name: str, description: str) -> list[str]:
    text = (name + " " + description).casefold()
    return [ident for ident, words in TOPICS if any(word in text for word in words)]


def evaluate(item: dict, now: datetime) -> dict | None:
    url = canonical_url(item.get("url", ""))
    name = str(item.get("name", "")).strip()[:120]
    source = str(item.get("source_kind", ""))
    if not url or not name or source not in ALLOWED_SOURCE_KIND:
        return None
    desc = str(item.get("description") or "")[:450].strip()
    if any(term in (name + " " + desc).casefold() for term in UNSAFE_WORDS):
        return None
    if item.get("archived") is True:
        return None
    license_id = str(item.get("license_spdx") or "unknown").strip()[:60]
    if license_id.upper() == "NOASSERTION":
        license_id = "unknown"
    age = age_days(item.get("last_modified", ""), now)
    sectors = infer_sectors(name, desc)
    owner = str(item.get("owner") or "").casefold()
    # A metadata score for triage, NOT an estimate of commercial suitability.
    evidence = (12 if len(desc) >= 30 else 5 if desc else 0) + (6 if license_id not in ("", "unknown") else 0)
    provenance = 18 if source in ("github-api", "huggingface-api") else 8
    if owner in KNOWN_PUBLISHERS:
        provenance += 5  # Publisher signal only; not independent quality certification.
    currency = 14 if age is not None and age <= 30 else 9 if age is not None and age <= 180 else 3 if age is not None and age <= 365 else 0
    applicability = 18 if len(sectors) >= 1 else 3
    actionability = 10 if item.get("kind") in ("skill", "workflow", "tool", "agent", "mcp") else 5
    safety = 10 if license_id not in ("", "unknown") else 0
    score_parts = {"evidence": evidence, "provenance": provenance, "freshness": currency, "industry_fit": applicability, "task_readiness": actionability, "license_signal": safety}
    score = min(100, sum(score_parts.values()))
    # Missing license or sector match may NEVER be silently promoted.
    if not sectors or license_id in ("", "unknown"):
        triage = "needs-evidence"
    elif score >= 67:
        triage = "review-priority"
    elif score >= 45:
        triage = "watch"
    else:
        triage = "needs-evidence"
    kind = str(item.get("kind") or "project").lower()
    if kind not in VALID_KINDS:
        kind = "project"
    identifier = "discovery:" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:20]
    return {
        "id": identifier, "name": name, "url": url, "kind": kind,
        "description": desc, "sector_ids": sectors, "source_kind": source,
        "source_url": canonical_url(item.get("source_url", "")) or url,
        "last_modified": str(item.get("last_modified") or "")[:32],
        "license_spdx_signal": license_id, "metadata_score": score,
        "score_parts": score_parts, "review_state": triage,
        "verification": "metadata-only", "safety_review": "not-audited",
        "approved": False, "evaluated_at_utc": now.isoformat(),
        "warnings": [
            "Score ranks investigation priority; not verified utility, safety, license rights or ROI.",
            *([] if sectors else ["No justified industry match; do not recommend."]),
            *([] if license_id not in ("", "unknown") else ["License not independently confirmed."]),
        ],
    }


def existing_candidates() -> list[dict]:
    catalog = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
    meta_path = ROOT / "data" / "repo_metadata.json"
    metadata = json.loads(meta_path.read_text(encoding="utf-8")).get("repositories", {}) if meta_path.exists() else {}
    curated = json.loads((ROOT / "data" / "curated.json").read_text(encoding="utf-8"))
    curated_urls = {canonical_url(i.get("url", "")) for i in curated}
    if not isinstance(catalog, list) or len(catalog) < len(curated):
        raise ValueError("Invalid legacy Atlas catalog snapshot")
    results = []
    for row in catalog:
        url = canonical_url(row.get("url", ""))
        if not url or url in curated_urls:  # Already editorial-curated; no duplicate promotion.
            continue
        repo = str(row.get("repo") or "").lower()
        m = metadata.get(repo, {})
        if m.get("archived") is True:
            continue
        results.append({
            "name": row.get("name"), "url": url, "kind": row.get("type") or "project",
            "description": row.get("description_zh") or row.get("use_case") or "",
            "source_kind": "existing-catalog", "source_url": row.get("url"),
            "owner": repo.split("/")[0], "archived": m.get("archived"),
            "last_modified": m.get("last_push") or "",
            "license_spdx": m.get("license_spdx") or "unknown",
        })
    return results


def live_candidates(now: datetime) -> list[dict]:
    date_floor = (now - timedelta(days=45)).date().isoformat()
    queries = [f"topic:ai-agent pushed:>={date_floor}", f"topic:rag pushed:>={date_floor}"]
    records = []
    for query in queries:
        url = "https://api.github.com/search/repositories?" + urlencode({"q": query, "sort": "updated", "order": "desc", "per_page": "20"})
        obj = request_json(url)
        if not isinstance(obj, dict) or not isinstance(obj.get("items"), list) or obj.get("incomplete_results"):
            raise ValueError("Incomplete GitHub search; refusing partial candidate output")
        for row in obj["items"]:
            if not isinstance(row, dict):
                continue
            lic = row.get("license") or {}
            owner = row.get("owner") or {}
            records.append({
                "name": row.get("full_name"), "url": row.get("html_url"), "kind": "repository",
                "description": row.get("description") or "", "source_kind": "github-api",
                "source_url": row.get("html_url"), "owner": owner.get("login"),
                "archived": row.get("archived"), "license_spdx": lic.get("spdx_id") or "unknown",
                "last_modified": row.get("pushed_at") or "",
            })
    hf_url = "https://huggingface.co/api/models?" + urlencode({"sort": "lastModified", "direction": "-1", "limit": "25"})
    models = request_json(hf_url)
    if not isinstance(models, list):
        raise ValueError("Unexpected Hugging Face model API response")
    for model in models:
        if not isinstance(model, dict) or not model.get("id"):
            continue
        model_id = str(model["id"])[:200]
        tags = model.get("tags") or []
        model_card = model.get("cardData") or {}
        records.append({
            "name": model_id, "url": "https://huggingface.co/" + model_id,
            "kind": "model", "description": "Pipeline: " + str(model.get("pipeline_tag") or "unspecified") + "; tags: " + ", ".join(str(t) for t in tags[:8]),
            "source_kind": "huggingface-api", "source_url": "https://huggingface.co/" + model_id,
            "owner": model_id.split("/")[0],
            "last_modified": model.get("lastModified") or "",
            "license_spdx": model_card.get("license") or next((str(t).split(":", 1)[1] for t in tags if str(t).startswith("license:")), "unknown"),
        })
    records.extend(arxiv_candidates())
    return records[:MAX_LIVE]


def assemble(rows: list[dict], now: datetime, mode: str, limit: int) -> dict:
    seen = set()
    scored = []
    for raw in rows:
        row = evaluate(raw, now)
        if row and row["url"] not in seen:
            seen.add(row["url"])
            scored.append(row)
    scored.sort(key=lambda r: (-r["metadata_score"], r["url"]))
    selected = scored[:limit]
    return {
        "schema_version": "1.0", "generated_at_utc": now.isoformat(), "mode": mode,
        "reviewed_for_safety": False, "live_llm": False, "auto_promoted": False,
        "total_input": len(rows), "deduplicated": len(scored), "queue_count": len(selected),
        "sources": ["Existing Atlas catalog + cached metadata"] if mode == "offline" else ["GitHub public search API", "Hugging Face Hub public models API", "arXiv official Atom metadata API"],
        "score_notice": "Heuristic triage, NOT evaluated quality, license rights, security or job fit.",
        "records": selected,
    }


def run(args: argparse.Namespace) -> dict:
    now = datetime.now(timezone.utc)
    if args.mode == "live":
        source = live_candidates(now)
        if not source:
            raise ValueError("Live discovery returned no candidates; preserving previous queue")
    else:
        source = existing_candidates()
    return assemble(source, now, args.mode, min(args.limit, MAX_LIVE if args.mode == "live" else MAX_OFFLINE))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("offline", "live"), default="offline")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.limit < 1:
        parser.error("--limit must be positive")
    try:
        result = run(args)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temp = args.output.with_suffix(args.output.suffix + ".tmp")
        temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temp.replace(args.output)  # atomic only after every required source succeeded
    except Exception as exc:
        print("Discovery safely aborted, previous results untouched:", str(exc), file=sys.stderr)
        return 2
    print(json.dumps({k: result[k] for k in ("mode", "total_input", "deduplicated", "queue_count", "auto_promoted")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
