#!/usr/bin/env python3
"""Real LangGraph 1.2.18 integration probe: in-memory and synthetic ONLY.

Unlike Pilot Lab 01, this does invoke the actual upstream StateGraph,
InMemorySaver, interrupt, Command(resume=...) and get_state APIs.
It never invokes an LLM, trading terminal, network tool, filesystem writer,
external service, or persistent database. This test is NOT a security audit.
"""
import argparse
import json
from importlib.metadata import version
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

REQUIRED_LANGGRAPH = "1.2.18"
UPSTREAM_URL = "https://github.com/langchain-ai/langgraph"
UPSTREAM_RELEASE = "https://github.com/langchain-ai/langgraph/releases/tag/1.2.18"

class WorkflowState(TypedDict, total=False):
    action: str
    idempotency_key: str
    permission: str
    outcome: str


def build_probe(ledger):
    """ledger is synthetic in-memory only; no external writable adapters."""
    def guard(state: WorkflowState):
        if state.get("action") == "read_public":
            return {"permission": "read", "outcome": "public_read"}
        if state.get("action") == "write_draft":
            return {"permission": "pending", "outcome": "awaiting_owner"}
        return {"permission": "deny", "outcome": "blocked_action"}

    def route(state: WorkflowState):
        return "review" if state.get("action") == "write_draft" else END

    def review(state: WorkflowState):
        # IMPORTANT: interrupt is first: resume re-executes this node.
        approval = interrupt({"kind": "owner_review", "requested_action": "write_draft"})
        if (type(approval) is dict and approval.get("approved") is True
                and approval.get("source") == "owner_session"):
            return {"permission": "approved", "outcome": "owner_approved"}
        return {"permission": "deny", "outcome": "owner_denied"}

    def route_after_review(state: WorkflowState):
        return "commit" if state.get("permission") == "approved" else END

    def commit(state: WorkflowState):
        key = state.get("idempotency_key", "")
        if not isinstance(key, str) or not (1 <= len(key) <= 64):
            return {"outcome": "missing_idempotency_key"}
        if key in ledger:
            return {"outcome": "already_applied"}
        ledger.add(key)
        return {"outcome": "draft_applied"}

    builder = StateGraph(WorkflowState)
    builder.add_node("guard", guard)
    builder.add_node("review", review)
    builder.add_node("commit", commit)
    builder.add_edge(START, "guard")
    builder.add_conditional_edges("guard", route, {"review": "review", END: END})
    builder.add_conditional_edges("review", route_after_review, {"commit": "commit", END: END})
    builder.add_edge("commit", END)
    return builder.compile(checkpointer=InMemorySaver())


def probe():
    observed = version("langgraph")
    if observed != REQUIRED_LANGGRAPH:
        raise RuntimeError(f"Pinned upstream version required {REQUIRED_LANGGRAPH}, found {observed}")
    ledger = set()
    graph = build_probe(ledger)
    cases = []
    def record(case_id, condition, detail):
        if not condition:
            raise AssertionError(f"{case_id}: {detail}")
        cases.append({"id": case_id, "pass": True, "observation": detail})

    def cfg(thread):
        return {"configurable": {"thread_id": "atlas-real-lg-" + thread}}

    read = graph.invoke({"action": "read_public"}, config=cfg("public"))
    record("LG01", read["outcome"] == "public_read" and len(ledger) == 0,
           "actual upstream graph traverses read-only route")
    trade = graph.invoke({"action": "send_order"}, config=cfg("trade"))
    record("LG02", trade["outcome"] == "blocked_action" and len(ledger) == 0,
           "simulated send_order cannot reach draft commit node")
    unknown = graph.invoke({"action": "credentials.read"}, config=cfg("unknown"))
    record("LG03", unknown["outcome"] == "blocked_action" and len(ledger) == 0,
           "unknown action rejects without calling a tool")
    held_cfg = cfg("held")
    held = graph.invoke({"action": "write_draft", "idempotency_key": "held-key"}, config=held_cfg)
    snapshot = graph.get_state(held_cfg)
    record("LG04", "__interrupt__" in held and "review" in snapshot.next and len(ledger) == 0,
           "actual checkpoint exposes pending review; no side effects")
    denied = graph.invoke(Command(resume={"approved": False, "source": "owner_session"}), config=held_cfg)
    record("LG05", denied["outcome"] == "owner_denied" and len(ledger) == 0,
           "actual Command resume with denied approval blocks commit")
    forged_cfg = cfg("forged")
    graph.invoke({"action": "write_draft", "idempotency_key": "spoof"}, config=forged_cfg)
    forged = graph.invoke(Command(resume={"approved": True, "source": "untrusted_webpage"}), config=forged_cfg)
    record("LG06", forged["outcome"] == "owner_denied" and "spoof" not in ledger,
           "fake approval source does not count as owner-session approval")
    valid_cfg = cfg("valid")
    graph.invoke({"action": "write_draft", "idempotency_key": "unique-draft"}, config=valid_cfg)
    completed = graph.invoke(Command(resume={"approved": True, "source": "owner_session"}), config=valid_cfg)
    record("LG07", completed["outcome"] == "draft_applied" and ledger == {"unique-draft"},
           "real interrupt and Command resume complete one synthetic draft")
    replay_cfg = cfg("replay")
    graph.invoke({"action": "write_draft", "idempotency_key": "unique-draft"}, config=replay_cfg)
    replay = graph.invoke(Command(resume={"approved": True, "source": "owner_session"}), config=replay_cfg)
    record("LG08", replay["outcome"] == "already_applied" and len(ledger) == 1,
           "duplicate synthetic idempotency key does not duplicate writes")
    missing_cfg = cfg("missing")
    graph.invoke({"action": "write_draft", "idempotency_key": ""}, config=missing_cfg)
    missing = graph.invoke(Command(resume={"approved": True, "source": "owner_session"}), config=missing_cfg)
    record("LG09", missing["outcome"] == "missing_idempotency_key" and len(ledger) == 1,
           "approved action with no idempotency key still cannot write")
    record("LG10", graph.get_state(held_cfg).next == () and graph.get_state(valid_cfg).next == (),
           "completed threads have no pending graph nodes")

    return {
        "schema_version": 1,
        "project": "langchain-ai/langgraph",
        "status": "real-upstream-sandbox-executed",
        "upstream_package": "langgraph",
        "upstream_version": observed,
        "upstream_release": UPSTREAM_RELEASE,
        "upstream_graph_api_used": ["StateGraph", "InMemorySaver", "interrupt", "Command.resume", "get_state"],
        "tool_calls_real": 0,
        "llm_calls_real": 0,
        "trading_orders_sent": 0,
        "external_user_data_used": False,
        "checkpoint_scope": "process-memory-only",
        "owner_approval": "synthetic-dict-not-authenticated-user-identity",
        "cases_total": len(cases),
        "cases_passed": sum(c["pass"] for c in cases),
        "cases": cases,
        "limitations": [
            "No production broker, user account, API keys, remote services, or models connected.",
            "Owner approval is a mock event, not real authentication or RBAC.",
            "InMemorySaver loses all checkpoints on process restart.",
            "In-process ledger is not durable and does not prove cross-process idempotency.",
            "Dependencies beyond the pinned top-level package are recorded by CI but not hash-locked.",
            "No complete license, vulnerability, transitive dependency, performance, or production audit."
        ]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("test-results/real-langgraph-result.json"))
    args = parser.parse_args()
    result = probe()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS REAL LANGGRAPH {result['upstream_version']}: {result['cases_passed']}/{result['cases_total']} synthetic scenarios using upstream SDK")
    print("No network tools, LLM calls, trading orders or real owner authentication")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
