#!/usr/bin/env python3
"""V1.7.8 reproducible sector-gap research briefs (offline, zero sources invented).

Merges the REVIEW-ONLY source coverage report with EXISTING Atlas scenario/domain
references. These are editorial investigation prompts, NOT verified external
AI products, source checks, performance proof or a license to auto-promote.
"""
from __future__ import annotations
from pathlib import Path
import argparse
import json
from provider_contract_v174 import ContractError
from coverage_review_v177 import generate_review, load_data

ROOT=Path(__file__).resolve().parent

def build_gap_briefs(snapshot: dict, atlas: dict, policy: dict) -> dict:
    coverage=generate_review(snapshot,atlas,policy)
    domains=atlas.get("subdomains",[])
    workflows=atlas.get("workflows",[])
    if len(domains)!=133 or len(workflows)!=64:
        raise ContractError("Atlas domain/workflow baseline changed")
    seen=set()
    for row in domains:
        if row["id"] in seen: raise ContractError("Duplicate domain")
        seen.add(row["id"])
    brief=[]
    for s in coverage["sectors"]:
        if s["coverage_state"]!="no-records":
            continue
        sid=s["sector_id"]
        found_domains=[d for d in domains if d["sector_id"]==sid]
        found_workflows=[w for w in workflows if w["industry_id"]==sid]
        if not found_domains or not found_workflows:
            raise ContractError("Uncovered industry missing its preexisting editorial references")
        short_domains=[{
            "id":d["id"],"name":d["name"],"task_focus":d.get("focus",""),
            "classification":"existing-editorial-task-not-an-external-source"
        } for d in found_domains[:3]]
        short_workflows=[{
            "id":w["id"],"title":w["title"],"kpi":w.get("kpi",""),
            "guardrail":w.get("guardrail",""),
            "classification":"existing-editorial-workflow-not-an-external-source"
        } for w in found_workflows[:2]]
        brief.append({
            "sector_id":sid,"sector_name":s["sector_name"],
            "coverage_state":"no-source-candidate",
            "editorial_domains":short_domains,
            "editorial_workflows":short_workflows,
            "research_steps":[
                "从现有岗位任务中明确可衡量问题，并寻找可复核的合法公开来源",
                "记录来源发布者、更新时间、使用条款、许可证及适用场景",
                "对候选进行权限、安全、数据隐私及实际任务样本核验",
                "独立复核反例和退出条件；未通过则保持未审核，不晋级推荐"
            ],
            "suggested_source_count":0,
            "sources_live_checked":0,
            "human_verified":False,
            "approval":"research-gap-only",
        })
    if len(brief)!=coverage["no_candidate_sectors"]:
        raise ContractError("Coverage gap count drift")
    return {
        "schema_version":"1.0","report_type":"sector-gap-research-briefs",
        "covered_by_editorial_tags":coverage["existing_editorial_tagged_sectors"],
        "proposal_only_sectors":coverage["proposal_only_sectors"],
        "no_candidate_sectors":len(brief),
        "briefs":brief,"live_requests":0,"new_licensed_sources":0,
        "auto_approved":0,"model_called":False,"release_gate":"HOLD",
        "warning":"These are research questions based on existing task/workflow taxonomy, NOT new external source candidates or proof that an industry lacks AI tools."
    }

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True,type=Path)
    opt=ap.parse_args()
    payload=build_gap_briefs(*load_data())
    opt.output.parent.mkdir(parents=True,exist_ok=True)
    opt.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PASS V1.7.8 gap briefs: %d sectors; 0 invented links; 0 promoted sources"%payload["no_candidate_sectors"])

if __name__=="__main__":
    main()
