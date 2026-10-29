#!/usr/bin/env python3
"""Pure standard-library, deterministic *first-party* pilot contract baseline.

Never installs/imports third-party packages, accesses external networks, uses
real user records, invokes models, or sends trading orders. These tests are
NOT independent reproductions of LangGraph, Docling, or Promptfoo.
"""
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "data/pilot_lab_cases.json"
IDS = {"graph": "langchain-ai/langgraph",
       "document": "docling-project/docling",
       "security": "promptfoo/promptfoo"}
PIN = re.compile(r"^[0-9a-f]{40}$")
SAFE_TERM = re.compile(r"^[A-Za-z][A-Za-z0-9 ]{1,35}$")


def outcome(project, inputs):
    """Only simple policy and text contracts—not a model, PDF parser, or agent."""
    if project == "graph":
        action = inputs.get("action")
        if action in ("read_public", "read_research"):
            return "ALLOW"
        if action == "write_draft":
            return ("ALLOW" if inputs.get("approved") is True and
                    inputs.get("approval_source") == "owner_session" else "BLOCK")
        if action == "retry_job":
            key, attempt = inputs.get("idempotency_key"), inputs.get("attempt")
            return ("ALLOW" if isinstance(key, str) and 1 <= len(key) <= 64 and
                    isinstance(attempt, int) and not isinstance(attempt, bool) and
                    1 <= attempt <= 2 else "BLOCK")
        return "BLOCK"
    if project == "document":
        query, blocks = inputs.get("query"), inputs.get("blocks")
        if not isinstance(query, str) or not SAFE_TERM.fullmatch(query) or not isinstance(blocks, list):
            return "NO_EVIDENCE"
        for b in blocks:
            if not isinstance(b, dict) or type(b.get("page")) is not int or b["page"] < 1:
                continue
            text = b.get("text")
            if isinstance(text, str) and re.search(r"(?<![A-Za-z0-9])"+re.escape(query)+r"(?![A-Za-z0-9])",text,re.I):
                return "p" + str(b["page"])
        return "NO_EVIDENCE"
    if project == "security":
        # Never parse, act on, or follow instructions from the untrusted text.
        return "ALLOW" if inputs.get("tool") in ("atlas.search", "docs.read") else "BLOCK"
    raise ValueError("unknown contract: " + str(project))


def validate_cases(doc):
    if not isinstance(doc, dict) or doc.get("schema_version") != 1 or doc.get("scope") != "first-party-deterministic-contract-baseline":
        raise ValueError("pilot: invalid schema or scope")
    gates = ("evaluates_upstream_packages","upstream_code_executed","live_models_called",
             "external_network_calls","real_user_data","trading_orders_sent")
    if any(doc.get(k) is not False for k in gates):
        raise ValueError("pilot: unsupported third-party/production claim")
    if doc.get("research_status") != "contract-fixtures-only-not-upstream-tested":
        raise ValueError("pilot: evidence tier promotion")
    if set(doc.get("projects",{})) != set(IDS):
        raise ValueError("pilot: missing upstream identities")
    for k, expected_repo in IDS.items():
        p = doc["projects"][k]
        if p.get("repo") != expected_repo or not PIN.fullmatch(p.get("readme_sha","")) or not PIN.fullmatch(p.get("license_sha","")):
            raise ValueError("pilot: invalid pinned upstream provenance")
        if not all(isinstance(p.get(t),str) and len(p[t])>10 for t in ("focus_zh","focus_en","label_zh","label_en")):
            raise ValueError("pilot: missing bilingual project context")
    cases=doc.get("cases")
    if not isinstance(cases,list) or len(cases)!=24:
        raise ValueError("pilot: expected exactly 24 frozen synthetic cases")
    seen=set()
    for c in cases:
        if not isinstance(c,dict) or set(c)!={"id","project","title","input","expected"}:
            raise ValueError("pilot: malformed fixture")
        if not re.fullmatch(r"[GDS]\d{2}",c["id"]) or c["id"] in seen:
            raise ValueError("pilot: duplicate/invalid id")
        seen.add(c["id"])
        k=c["project"]
        if k not in IDS or c["id"][0] != {"graph":"G","document":"D","security":"S"}[k]:
            raise ValueError("pilot: wrong project case pairing")
        if not all(isinstance(c["title"].get(l),str) and len(c["title"][l])>10 for l in ("zh","en")):
            raise ValueError("pilot: missing bilingual case title")
        if not isinstance(c["input"],dict) or c["expected"] not in ("ALLOW","BLOCK","NO_EVIDENCE","p1","p2","p3","p4"):
            raise ValueError("pilot: invalid fixture")
        if k=="document" and c["expected"] in ("ALLOW","BLOCK"):
            raise ValueError("pilot: document outcome mismatch")
        if k!="document" and c["expected"] not in ("ALLOW","BLOCK"):
            raise ValueError("pilot: policy outcome mismatch")
        # The fixtures are intentionally synthetic, not copied copyrighted docs or private data.
        if len(json.dumps(c["input"]))>3000:
            raise ValueError("pilot: unexpected oversized fixture")
    if Counter(c["project"] for c in cases)!={"graph":9,"document":7,"security":8}:
        raise ValueError("pilot: unexpected coverage")
    return cases


def compute(doc):
    cases=validate_cases(doc)
    results=[]
    for c in cases:
        actual=outcome(c["project"],c["input"])
        results.append({"id":c["id"],"project":c["project"],"actual":actual,
                        "expected":c["expected"],"pass":actual==c["expected"]})
    groups={}
    for k in IDS:
        subset=[r for r in results if r["project"]==k]
        groups[k]={"cases":len(subset),"passed":sum(r["pass"] for r in subset),
                   "blocked":sum(r["actual"]=="BLOCK" for r in subset),
                   "allowed":sum(r["actual"]=="ALLOW" for r in subset),
                   "no_evidence":sum(r["actual"]=="NO_EVIDENCE" for r in subset)}
    return {"schema_version":1,"scope":doc["scope"],"evidence_level":doc["research_status"],
            "evaluates_upstream_packages":False,"upstream_code_executed":False,
            "live_models_called":False,"real_user_data":False,"trading_orders_sent":False,
            "total_cases":len(results),"passed_cases":sum(r["pass"] for r in results),
            "all_expected_met":all(r["pass"] for r in results),"groups":groups,"cases":results}


def run_from_files(root=ROOT):
    doc=json.loads((Path(root)/"data/pilot_lab_cases.json").read_text("utf-8"))
    return compute(doc)


if __name__=="__main__":
    print(json.dumps(run_from_files(),indent=2))
