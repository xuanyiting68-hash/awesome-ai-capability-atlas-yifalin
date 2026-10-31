#!/usr/bin/env python3
"""Three stdlib-only first-party synthetic recipe demonstrations.

LEADS reuses the Atlas's existing consent gate.
EDUCATION checks extractive answers against source spans (no model).
FINANCE simulates chronological predictions and costs (no live or demo orders).
Absolutely no network, SDK, credentials, external processing, or customer data.
"""
import argparse
import json
import sys
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from examples.consent_lead_triage.run_demo import triage_records  # noqa: E402

FIXTURE_PATH = ROOT / "examples/recipe_demos/synthetic_fixtures.json"
LEADS_PATH = ROOT / "examples/consent_lead_triage/synthetic_leads.json"
FROZEN_AS_OF = "2026-10-27T00:00:00Z"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_decimal(value):
    require(isinstance(value, str), "prices/costs must be decimal STRINGS")
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as err:
        raise ValueError("invalid synthetic decimal") from err
    require(number.is_finite(), "non-finite synthetic decimal")
    return number


def leads_demo(records):
    result = triage_records(records, FROZEN_AS_OF)
    require(result["eligible_count"] + result["blocked_count"] == len(records),
            "consent ledger does not reconcile")
    return {
        "scenario": "leads",
        "method": "first_party_purpose_bound_consent_and_deduplicated_human_triage",
        "input_count": result["input_count"],
        "eligible_count": result["eligible_count"],
        "blocked_count": result["blocked_count"],
        "blocked_reasons": result["blocked_reasons"],
        "human_review_queue": result["human_review_queue"],
        "as_of": result["as_of"],
        "user_contact_attempts": 0,
        "outbound_messages": 0,
        "verified_third_party_integration": False,
    }


def education_demo(fixture):
    require(isinstance(fixture, dict) and set(fixture) == {"sources", "questions"},
            "invalid education fixture")
    sources = fixture["sources"]
    questions = fixture["questions"]
    require(isinstance(sources, list) and 2 <= len(sources) <= 10 and
            isinstance(questions, list) and 2 <= len(questions) <= 20,
            "invalid source/question sizes")
    source_map = {}
    for row in sources:
        require(isinstance(row, dict) and set(row) == {"source_id", "text"},
                "invalid source row")
        key, text = row["source_id"], row["text"]
        require(isinstance(key, str) and key.startswith("lesson-") and
                key not in source_map and isinstance(text, str) and 20 <= len(text) <= 300,
                "invalid/duplicate source")
        source_map[key] = text
    seen, responses, supported, abstained = set(), [], 0, 0
    for row in questions:
        require(isinstance(row, dict) and set(row) == {
            "question_id", "question", "source_id", "answer_span"
        }, "invalid education question")
        qid, question, sid, answer = (row["question_id"], row["question"],
                                       row["source_id"], row["answer_span"])
        require(isinstance(qid, str) and qid.startswith("q-") and qid not in seen
                and isinstance(question, str) and len(question) >= 15,
                "duplicate/invalid question")
        seen.add(qid)
        if sid is None and answer is None:
            abstained += 1
            responses.append({"question_id": qid, "status": "ABSTAIN_UNSUPPORTED",
                              "answer": None, "citation": None})
            continue
        require(isinstance(sid, str) and sid in source_map and
                isinstance(answer, str) and len(answer) >= 6 and
                answer in source_map[sid], "unsupported, fabricated or mismatched quote")
        supported += 1
        responses.append({"question_id": qid, "status": "EXTRACTIVE_SOURCE_SPAN",
                          "answer": answer, "citation": sid})
    return {"scenario": "education", "method": "deterministic_extractive_fixture_span_checks",
            "source_count": len(sources), "question_count": len(questions),
            "supported_count": supported, "abstained_count": abstained,
            "responses": responses, "generated_answers": 0, "student_data_seen": False,
            "llm_calls": 0, "verified_third_party_integration": False}


def finance_demo(fixture):
    required = {"start_date", "symbol", "frequency", "prices", "train_end_index",
                "cost_bps", "rule"}
    require(isinstance(fixture, dict) and set(fixture) == required,
            "unexpected finance fixture fields")
    require(fixture["symbol"] == "SYNTHETIC_XAU_DEMO_NOT_MARKET" and
            fixture["frequency"] == "one_synthetic_observation_per_day",
            "not a strictly synthetic source")
    require(isinstance(fixture["rule"], str) and "price[t-1]-price[t-2]" in fixture["rule"],
            "unfrozen prediction rule")
    try:
        start = date.fromisoformat(fixture["start_date"])
    except (TypeError, ValueError) as err:
        raise ValueError("invalid synthetic start date") from err
    values = fixture["prices"]
    require(isinstance(values, list) and 14 <= len(values) <= 200,
            "incomplete synthetic prices")
    prices = [safe_decimal(x) for x in values]
    require(all(x > 0 for x in prices), "synthetic prices must be positive")
    split = fixture["train_end_index"]
    require(type(split) is int and 5 <= split <= len(prices)-5,
            "invalid chronological holdout boundary")
    cost = fixture["cost_bps"]
    require(isinstance(cost, dict) and set(cost) == {"spread", "commission", "slippage"},
            "cost components incomplete")
    components = {k: safe_decimal(cost[k]) for k in ("spread", "commission", "slippage")}
    require(all(Decimal("0") <= v <= Decimal("30") for v in components.values()),
            "cost outside nonnegative fixture range")
    round_bps = lambda v: str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    total_cost = sum(components.values(), Decimal("0"))
    rows, gross, net, hits = [], Decimal("0"), Decimal("0"), 0
    for t in range(split, len(prices)-1):
        # At synthetic decision index t, ONLY values t-1 and t-2 set direction;
        # price t sets the hypothetical mark, and t+1 is used solely for scoring.
        past_move = prices[t-1]-prices[t-2]
        signal = 1 if past_move > 0 else -1 if past_move < 0 else 0
        future_move = prices[t+1]-prices[t]
        gross_bps = Decimal(signal)*future_move / prices[t]*Decimal("10000")
        charged_bps = total_cost if signal != 0 else Decimal("0")
        net_bps = gross_bps-charged_bps
        gross += gross_bps
        net += net_bps
        hits += int(signal != 0 and signal*future_move > 0)
        rows.append({
            "decision_day": (start+timedelta(days=t)).isoformat(),
            "decision_index": t,
            "max_predictor_index": t-1,
            "signal": signal,
            "future_return_bps": round_bps(future_move/prices[t]*Decimal("10000")),
            "gross_bps": round_bps(gross_bps),
            "charged_cost_bps": round_bps(charged_bps),
            "net_bps": round_bps(net_bps),
            "broker_order_sent": False,
        })
    require(all(r["max_predictor_index"] < r["decision_index"] for r in rows),
            "future-data leakage detected")
    return {
        "scenario": "finance",
        "method": "frozen_naive_momentum_synthetic_chronological_holdout",
        "symbol": fixture["symbol"], "train_end_index": split,
        "first_holdout_day": (start+timedelta(days=split)).isoformat(),
        "holdout_decisions": len(rows),
        "positive_direction_matches": hits,
        "roundtrip_cost_bps": round_bps(total_cost),
        "gross_bps_sum": round_bps(gross), "net_bps_sum": round_bps(net),
        "evaluated_decisions": rows,
        "future_prices_used_in_predictor": False,
        "dataset_type": "fabricated_not_market",
        "has_predictive_edge": "not_established",
        "investment_claims": 0,
        "broker_orders": 0, "api_calls": 0,
        "verified_third_party_integration": False,
    }


def run_from_files(root=ROOT, scenario="all"):
    root = Path(root)
    fixtures = json.loads((root/"examples/recipe_demos/synthetic_fixtures.json").read_text("utf-8"))
    require(isinstance(fixtures, dict) and fixtures.get("schema_version") == 1
            and fixtures.get("fixture_only") is True
            and set(fixtures) == {"schema_version","fixture_only","description","education","finance"},
            "fixture provenance invalid")
    supported = ("leads", "education", "finance")
    require(scenario in (*supported, "all"), "unknown scenario")
    demos = {}
    if scenario in ("leads", "all"):
        rows = json.loads((root/"examples/consent_lead_triage/synthetic_leads.json").read_text("utf-8"))
        demos["leads"] = leads_demo(rows)
    if scenario in ("education", "all"):
        demos["education"] = education_demo(fixtures["education"])
    if scenario in ("finance", "all"):
        demos["finance"] = finance_demo(fixtures["finance"])
    return {
        "schema_version": 1, "version": "1.5.1",
        "execution": "real_first_party_stdlib_local_synthetic_only",
        "all_scenarios": list(demos),
        "all_passed": True, "scenarios": demos,
        "verified_3rd_party_integrations": 0,
        "network_requests": 0, "models_called": 0, "real_orders": 0,
        "personal_information": False,
        "disclaimer": "Actual deterministic FIRST-PARTY fixture execution, NOT third-party Skills/Agents/MCP/tool interoperability or production readiness.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("leads","education","finance","all"), default="all")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_from_files(scenario=args.scenario)
    result = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+"\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(result,encoding="utf-8")
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
