#!/usr/bin/env python3
"""V1.7.5 offline, source-grounded *metadata* retrieval (no embedding, HTTP or LLM).

Only cached, unapproved editorial radar records are searched. Topic overlap is
a candidate-discovery cue; ranking is NOT evidence quality, security, ROI or
clinical/financial suitability. Provider generation remains offline mock only.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from provider_contract_v174 import (
    ContractError, EvidenceRef, MockProvider, TaskRequest, validate_citations, https_source
)

ROOT = Path(__file__).resolve().parent
MAX_TASK = 400
MAX_RESULTS = 8


def phrase_hit(text: str, term: str) -> bool:
    if not isinstance(text, str) or not isinstance(term, str) or not term.strip():
        return False
    word = term.lower().strip()
    if re.fullmatch(r"[a-z0-9][a-z0-9\s-]*", word):
        pat = r"(?<![a-z0-9])" + re.sub(r"[\s-]+", r"[\\s_-]+", re.escape(word)) + r"(?![a-z0-9])"
        return re.search(pat, text.lower()) is not None
    clean = lambda v: re.sub(r"[\s，。；：！？,.;:!?·_\-\(\)\[\]（）]+", "", v.lower())
    return clean(word) in clean(text)


def load_reference_data(root: Path = ROOT) -> tuple[list[dict], list[dict]]:
    radar = json.loads((root / "discovery_seed.json").read_text(encoding="utf-8"))
    topics = json.loads((root / "rag_topics_v175.json").read_text(encoding="utf-8"))
    if radar.get("mode") != "cached-editorial-baseline" or radar.get("auto_promoted") is not False:
        raise ContractError("Radar source not a frozen non-promotional baseline")
    if len(radar.get("records", [])) != 133:
        raise ContractError("Unexpected editorial radar size")
    groups = topics.get("concepts", [])
    if not 1 <= len(groups) <= 30 or len({x["id"] for x in groups}) != len(groups):
        raise ContractError("Invalid topic index")
    return radar["records"], groups


def topic_matches(text: str, topics: list[dict]) -> set[str]:
    return {g["id"] for g in topics if any(phrase_hit(text, w) for w in g["terms"])}


@dataclass(frozen=True)
class Retrieved:
    evidence_id: str
    record_id: str
    title: str
    url: str
    description: str
    matched_topics: tuple[str, ...]
    score: int
    last_modified: str
    license_signal: str
    evidence_level: str = "unapproved-cached-metadata"

    def as_evidence(self) -> EvidenceRef:
        return EvidenceRef(
            id=self.evidence_id, title=self.title[:150], url=self.url,
            excerpt=self.description[:800], level="metadata-only"
        ).validate()


def retrieve(task: str, sector_id: str, records: list[dict],
             topics: list[dict], limit: int = 4) -> list[Retrieved]:
    if not isinstance(task, str) or not 1 <= len(task.strip()) <= MAX_TASK:
        raise ContractError("Task length invalid")
    if not re.fullmatch(r"s(?:0[1-9]|[12][0-9]|3[0-2])", sector_id):
        raise ContractError("Industry identifier invalid")
    if type(limit) is not int or not 1 <= limit <= MAX_RESULTS:
        raise ContractError("Top-K must be bounded")
    qtopics = topic_matches(task, topics)
    if not qtopics:
        return []
    results, seen = [], set()
    for r in records:
        if r.get("approved") is not False or sector_id not in r.get("sector_ids", []):
            continue
        url = r.get("source_url") or r.get("url") or ""
        try:
            https_source(url)
        except (ValueError, TypeError):
            continue
        # Treat metadata as untrusted strings; never follow links or execute source text.
        description = str(r.get("description") or "")[:800]
        name = str(r.get("name") or "").strip()[:150]
        if not name:
            continue
        overlap = qtopics & topic_matches(name + " " + description, topics)
        if not overlap:
            continue
        parsed = urlsplit(url)
        normalized = parsed.hostname.lower() + parsed.path.rstrip("/").lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        rid = "src-" + sha256(normalized.encode("utf-8")).hexdigest()[:12]
        results.append(Retrieved(
            evidence_id=rid, record_id=str(r.get("id", "")), title=name,
            url=url, description=description, matched_topics=tuple(sorted(overlap)),
            score=4 * len(overlap), last_modified=str(r.get("last_modified") or "")[:10],
            license_signal=str(r.get("license_spdx_signal") or "unknown")[:80]))
    return sorted(results, key=lambda x: (-x.score, x.title.lower(), x.record_id))[:limit]


def mock_research(task: str, sector_id: str, domain_id: str,
                  records: list[dict], topics: list[dict]) -> dict:
    hits = retrieve(task, sector_id, records, topics)
    request = TaskRequest(
        task=task, sector_id=sector_id, domain_id=domain_id,
        evidence=tuple(hit.as_evidence() for hit in hits))
    response = MockProvider().generate(request)
    validate_citations(response, request)
    return {
        "mode": "offline-mock", "answer": response.answer,
        "citation_ids": list(response.citation_ids),
        "sources": [{
            "id": hit.evidence_id, "record_id": hit.record_id,
            "title": hit.title, "url": hit.url, "score": hit.score,
            "matched_topics": list(hit.matched_topics),
            "metadata_date": hit.last_modified,
            "license_signal": hit.license_signal,
            "approval": "unapproved", "verification": "metadata-only"
        } for hit in hits],
        "source_count": len(hits), "billed_usd": 0.0,
        "disclaimer": "Offline editorial metadata only: not current source checks, authenticated audit, production RAG, model answer or verified commercial suitability."
    }


if __name__ == "__main__":
    records, topics = load_reference_data()
    # Only a fixed demo; no command-line ingestion, network or sensitive data.
    r = mock_research("证券资管量化研究：回测策略", "s02", "s02-d01", records, topics)
    print(json.dumps(r, ensure_ascii=False, indent=2))
