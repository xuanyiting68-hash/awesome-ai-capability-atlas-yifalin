#!/usr/bin/env python3
"""Actual bounded local research-task runtime: E5 model tool -> real LangGraph -> SQLite checkpoint.

Only existing PUBLIC Atlas metadata is read. Actual neural inference runs in a
pinned Transformers.js Node process. Local review capability gates writing a
research plan into the requested disposable workspace; no business actions.
This is a single-host reference runner, NOT auth, RBAC or a production agent.
"""
from __future__ import annotations
import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {"education", "finance", "growth", "content", "engineering", "governance"}
TASK_ID = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")
ONLY_ACTION = "research_plan"
SOURCE_FILES = ("data/curated.json", "data/repo_metadata.json", "data/research_briefs.json")
TOKEN_LIFETIME_SECONDS = 900


class State(TypedDict, total=False):
    task_id: str
    action: str
    goal: str
    scenario: str
    source_digest: dict[str, str]
    model_evidence: dict
    phase: str
    approved: bool
    report_name: str


def digest_sources():
    return {name.removeprefix("data/").removesuffix(".json"): hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES}


def verify_task(task):
    if not isinstance(task, dict) or set(task) != {"task_id", "action", "goal", "scenario"}:
        raise ValueError("BLOCK: task_schema")
    if not isinstance(task["task_id"], str) or not TASK_ID.fullmatch(task["task_id"]):
        raise ValueError("BLOCK: task_identifier")
    if task["action"] != ONLY_ACTION or task["scenario"] not in SCENARIOS:
        raise ValueError("BLOCK: forbidden_action_or_scenario")
    if not isinstance(task["goal"], str) or not 12 <= len(task["goal"].strip()) <= 240:
        raise ValueError("BLOCK: invalid_goal")


def setup(workspace):
    workspace = Path(workspace).resolve()
    if workspace.is_symlink():
        raise ValueError("BLOCK: symlink_workspace")
    workspace.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(workspace / "checkpoint.sqlite", timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS atlas_review_gates(
      task_id TEXT PRIMARY KEY,
      token_sha256 TEXT NOT NULL,
      goal_sha256 TEXT NOT NULL,
      expires_at REAL NOT NULL,
      phase TEXT NOT NULL CHECK(phase IN ('PENDING','CONSUMED_APPROVE','CONSUMED_DENY')))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS atlas_review_audit(
      task_id TEXT PRIMARY KEY, action TEXT NOT NULL, outcome TEXT NOT NULL,
      report_path TEXT, reviewed_at REAL NOT NULL)""")
    conn.commit()
    return conn


def call_actual_e5(state):
    payload = {"goal": state["goal"], "scenario": state["scenario"]}
    env = dict(os.environ)
    env.update({"HF_HUB_DISABLE_TELEMETRY": "1", "DO_NOT_TRACK": "1",
                "LANGCHAIN_TRACING_V2": "false", "LANGSMITH_TRACING": "false"})
    process = subprocess.run(
        ["node", str(ROOT / "scripts/agent_embed_candidates.mjs")],
        input=json.dumps(payload, ensure_ascii=False), text=True,
        capture_output=True, cwd=ROOT, env=env, timeout=240, check=False,
    )
    if process.returncode:
        raise RuntimeError("BLOCK: model_tool_failed: " + process.stderr[-350:])
    try:
        result = json.loads(process.stdout)
    except (ValueError, TypeError) as exc:
        raise RuntimeError("BLOCK: model_tool_malformed") from exc
    if (result.get("schema_version") != 1 or result.get("executed_neural_inference") is not True
        or result.get("model") != "Xenova/multilingual-e5-small"
        or result.get("dimensions") != 384
        or result.get("embeddings_computed") != 17
        or result.get("candidate_pool_size") != 16
        or result.get("external_action_calls") != 0
        or result.get("source_snapshot_sha256") != state["source_digest"]):
        raise RuntimeError("BLOCK: model_or_source_attestation_mismatch")
    selected = result.get("selected")
    if (not isinstance(selected, list) or len(selected) != 4
        or len({x.get("repo") for x in selected if isinstance(x, dict)}) != 4):
        raise RuntimeError("BLOCK: neural_selection_invalid")
    # Never rely on the model's own statements as an authority or a URL.
    original = {x["repo"]: x for x in json.loads((ROOT / SOURCE_FILES[0]).read_text())}
    for item in selected:
        name = item["repo"]
        source = original.get(name)
        if (source is None or item.get("source_url") != source["url"]
            or source["url"] != f"https://github.com/{name}"
            or item.get("reviewed_for_security") is not False
            or item.get("reviewed_for_commercial_use") is not False
            or item.get("verified_tool_compatibility") is not False
            or not isinstance(item.get("similarity_cosine"), (int, float))
            or not -1 <= item["similarity_cosine"] <= 1
            or not isinstance(item.get("blockers"), list) or not item["blockers"]):
            raise RuntimeError("BLOCK: unsourced_or_unreviewed_candidate")
    return result


def report_payload(state):
    evidence = state["model_evidence"]
    steps = [
        ("Scope and permissions", "Freeze public-source scope; no account credentials or customer content."),
        ("Evidence review", "Review official repository URLs, metadata age and all license blockers."),
        ("Compatibility pilot", "Test one chosen tool inside a separately authorized isolated environment."),
        ("Independent acceptance", "Record failures, rollback, security decision and review signature."),
    ]
    return {
        "schema_version": 1, "task_id": state["task_id"], "goal": state["goal"],
        "scenario": state["scenario"], "status": "LOCAL_APPROVED_RESEARCH_REPORT_NOT_DEPLOYED",
        "actual_neural_tool_executed": True,
        "actual_langgraph_checkpoint_and_interrupt": True,
        "source_snapshot_sha256": evidence["source_snapshot_sha256"],
        "model": evidence["model"], "model_dimensions": evidence["dimensions"],
        "selected": evidence["selected"],
        "steps": [{"number": i + 1, "name": name, "action": action,
                   "requires_human_review": True} for i, (name, action) in enumerate(steps)],
        "permissions": {"public_repo_read_only": True, "local_report_write": True,
                        "external_system_calls": 0, "orders": 0, "paid_models": 0},
        "claims": {"third_party_tool_executed": False, "production_safe": False,
                   "actual_llm_plan_generated": False, "licensed_for_commercial_use": False},
        "approval_boundary": "single-host one-use local capability token; no authenticated owner identity",
        "warning": "A pretrained semantic model selected references; deterministic rules generated the plan. Not an autonomous generative agent.",
    }


def make_graph(saver, workspace):
    root = Path(workspace).resolve()
    out = root / "reports"
    out.mkdir(exist_ok=True)

    def validate(state: State):
        verify_task({k: state[k] for k in ("task_id", "action", "goal", "scenario")})
        return {"source_digest": digest_sources(), "phase": "SOURCE_VALIDATED"}

    def research(state: State):
        result = call_actual_e5(state)
        return {"model_evidence": result, "phase": "ACTUAL_E5_COMPLETED"}

    def review(state: State):
        response = interrupt({"type": "LOCAL_RESEARCH_REVIEW",
                              "task_id": state["task_id"], "scenario": state["scenario"],
                              "repository_candidates": [x["repo"] for x in state["model_evidence"]["selected"]],
                              "requested_action": "write_local_report_only"})
        if not isinstance(response, dict) or response.get("source") != "one_time_local_capability":
            return {"approved": False, "phase": "BLOCK: untrusted_review_source"}
        if response.get("approved") is not True:
            return {"approved": False, "phase": "BLOCK: declined"}
        return {"approved": True, "phase": "LOCAL_APPROVED"}

    def after_review(state):
        return "write" if state.get("approved") is True else END

    def write(state: State):
        if digest_sources() != state["source_digest"]:
            return {"phase": "BLOCK: changed_source_after_approval"}
        record = report_payload(state)
        name = state["task_id"] + ".json"
        target = out / name
        if target.exists() or target.is_symlink():
            return {"phase": "BLOCK: report_exists"}
        # Only creates a new isolated local file: no shell, HTTP, plugin or external action.
        with target.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        return {"phase": "LOCAL_REPORT_WRITTEN", "report_name": "reports/" + name}

    graph = StateGraph(State)
    graph.add_node("validate", validate)
    graph.add_node("neural_research", research)
    graph.add_node("human_review", review)
    graph.add_node("write", write)
    graph.add_edge(START, "validate")
    graph.add_edge("validate", "neural_research")
    graph.add_edge("neural_research", "human_review")
    graph.add_conditional_edges("human_review", after_review, {"write": "write", END: END})
    graph.add_edge("write", END)
    return graph.compile(checkpointer=saver)


def config(task_id):
    return {"configurable": {"thread_id": "atlas-research-" + task_id}}


def prepare(workspace, task):
    verify_task(task)
    with setup(workspace) as db:
        exists = db.execute("SELECT 1 FROM atlas_review_gates WHERE task_id=?",
                            (task["task_id"],)).fetchone()
        if exists:
            raise ValueError("BLOCK: duplicate_task")
    db_path = Path(workspace) / "checkpoint.sqlite"
    with SqliteSaver.from_conn_string(str(db_path)) as saver:
        graph = make_graph(saver, workspace)
        result = graph.invoke(task, config=config(task["task_id"]))
        if "__interrupt__" not in result:
            raise RuntimeError("BLOCK: expected_actual_graph_interrupt")
        state = graph.get_state(config(task["task_id"]))
        if "human_review" not in state.next:
            raise RuntimeError("BLOCK: durable_review_checkpoint_missing")
        if state.values.get("phase") != "ACTUAL_E5_COMPLETED":
            raise RuntimeError("BLOCK: actual_model_not_executed")
    token = secrets.token_urlsafe(32)
    with setup(workspace) as db:
        try:
            db.execute("""INSERT INTO atlas_review_gates
                  (task_id,token_sha256,goal_sha256,expires_at,phase) VALUES (?,?,?,?,?)""",
                (task["task_id"], hashlib.sha256(token.encode()).hexdigest(),
                 hashlib.sha256(task["goal"].encode()).hexdigest(),
                 time.time() + TOKEN_LIFETIME_SECONDS, "PENDING"))
            db.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("BLOCK: duplicate_task") from exc
    return {"task_id": task["task_id"], "status": "PENDING_ONE_TIME_LOCAL_REVIEW",
            "review_token": token, "token_expires_seconds": TOKEN_LIFETIME_SECONDS,
            "actual_neural_model_executed": True, "durable_graph_interrupted": True,
            "candidates": [x["repo"] for x in state.values["model_evidence"]["selected"]],
            "owner_authentication": False, "external_actions": 0}


def resume(workspace, task_id, token, approve):
    if not TASK_ID.fullmatch(task_id):
        raise ValueError("BLOCK: task_identifier")
    db_path = Path(workspace) / "checkpoint.sqlite"
    if not db_path.is_file():
        raise ValueError("BLOCK: no_pending_task")
    with SqliteSaver.from_conn_string(str(db_path)) as saver:
        graph = make_graph(saver, workspace)
        state = graph.get_state(config(task_id))
        values = state.values or {}
        if "human_review" not in state.next or values.get("task_id") != task_id:
            raise ValueError("BLOCK: not_pending_review")
        if digest_sources() != values.get("source_digest"):
            raise ValueError("BLOCK: source_changed")
        with setup(workspace) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT token_sha256,goal_sha256,expires_at,phase FROM atlas_review_gates WHERE task_id=?",
                             (task_id,)).fetchone()
            matched = row is not None and hmac.compare_digest(
                row[0], hashlib.sha256(token.encode()).hexdigest())
            if (not matched or row[3] != "PENDING" or time.time() > row[2]
                or row[1] != hashlib.sha256(values["goal"].encode()).hexdigest()):
                db.rollback()
                raise ValueError("BLOCK: missing_expired_or_consumed_capability")
            db.execute("UPDATE atlas_review_gates SET phase=? WHERE task_id=?",
                       ("CONSUMED_APPROVE" if approve else "CONSUMED_DENY", task_id))
            db.commit()
        # Gap: the one-use token is consumed BEFORE graph resume; a process crash
        # means fail-closed until manually reconciled, not retryable production HA.
        result = graph.invoke(Command(resume={"source": "one_time_local_capability",
                                               "approved": bool(approve)}), config=config(task_id))
        phase = result.get("phase", "BLOCK: incomplete_graph")
        report = result.get("report_name")
        with setup(workspace) as db:
            db.execute("""INSERT INTO atlas_review_audit(task_id,action,outcome,report_path,reviewed_at)
                          VALUES(?,?,?,?,?)""",
                       (task_id, "local_report", phase, report, time.time()))
            db.commit()
    return {"task_id": task_id, "status": phase, "report": report,
            "real_graph_resume": True, "owner_authenticated": False,
            "real_orders": 0, "external_business_actions": 0}


def inspect(workspace, task_id):
    db_path = Path(workspace) / "checkpoint.sqlite"
    if not db_path.is_file():
        raise ValueError("BLOCK: missing_workspace")
    with setup(workspace) as db:
        gate = db.execute("SELECT phase FROM atlas_review_gates WHERE task_id=?", (task_id,)).fetchone()
        audit = db.execute("SELECT outcome,report_path FROM atlas_review_audit WHERE task_id=?", (task_id,)).fetchone()
    with SqliteSaver.from_conn_string(str(db_path)) as saver:
        state = make_graph(saver, workspace).get_state(config(task_id))
    return {"task_id": task_id, "gate": gate[0] if gate else None,
            "graph_next": list(state.next), "phase": (state.values or {}).get("phase"),
            "outcome": audit[0] if audit else None, "report": audit[1] if audit else None,
            "token_disclosed": False}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for action in ("prepare", "approve", "deny", "inspect"):
        p = sub.add_parser(action)
        p.add_argument("--workspace", required=True)
        if action == "prepare":
            p.add_argument("--task-file", required=True)
        else:
            p.add_argument("--task-id", required=True)
        if action in ("approve", "deny"):
            p.add_argument("--token-stdin", action="store_true", required=True,
                           help="Read single-use local capability from stdin; avoid shell history and process argv")
    args = parser.parse_args()
    if args.command == "prepare":
        task = json.loads(Path(args.task_file).read_text(encoding="utf-8"))
        answer = prepare(args.workspace, task)
    elif args.command in ("approve", "deny"):
        capability = sys.stdin.readline(250).strip()
        if not 1 <= len(capability) <= 200:
            raise ValueError("BLOCK: missing_local_capability_stdin")
        answer = resume(args.workspace, args.task_id, capability, args.command == "approve")
    else:
        answer = inspect(args.workspace, args.task_id)
    print(json.dumps(answer, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"status": "BLOCK", "reason": str(exc)[:300]}), file=sys.stderr)
        sys.exit(2)
