from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))


PERCENT_METRICS = {
    "claim_evidence_binding_rate",
    "unsupported_claim_rate",
    "uncertain_blocked_claim_rate",
    "unresolved_ticket_rate",
    "ticket_resolution_rate",
    "rerun_improvement_rate",
    "report_evidence_coverage",
}


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _run_metrics(result) -> dict[str, Any]:
    claims = result.claims
    tickets = result.review_tickets
    unresolved = [ticket for ticket in tickets if ticket.status in {"open", "accepted", "rerun_started"}]
    rerun_tickets = [ticket for ticket in tickets if ticket.rerun_count > 0]
    bound = len([claim for claim in claims if claim.supporting_evidence])
    unsupported = len([claim for claim in claims if claim.verified_status == "unsupported"])
    uncertain_blocked = len([claim for claim in claims if claim.verified_status in {"uncertain", "blocked"}])
    resolved = len([ticket for ticket in tickets if ticket.status == "resolved"])
    new_evidence = len([ticket for ticket in tickets if ticket.added_evidence_ids])
    improved_claims = sum(len(ticket.improved_claim_ids) for ticket in tickets)
    improved_reruns = len([ticket for ticket in rerun_tickets if ticket.improved_claim_ids])
    manifest = result.manifest
    return {
        "_claim_total": len(claims),
        "_bound_claims": bound,
        "_unsupported_claims": unsupported,
        "_uncertain_blocked_claims": uncertain_blocked,
        "_ticket_total": len(tickets),
        "_unresolved_tickets": len(unresolved),
        "_resolved_tickets": resolved,
        "_rerun_tickets": len(rerun_tickets),
        "_improved_reruns": improved_reruns,
        "claim_evidence_binding_rate": _rate(bound, len(claims)),
        "unsupported_claim_rate": _rate(unsupported, len(claims)),
        "uncertain_blocked_claim_rate": _rate(uncertain_blocked, len(claims)),
        "unresolved_ticket_rate": _rate(len(unresolved), len(tickets)),
        "tickets_created": len(tickets),
        "tickets_resolved": resolved,
        "ticket_resolution_rate": _rate(resolved, len(tickets)),
        "tickets_with_new_evidence": new_evidence,
        "claims_improved_after_rerun": improved_claims,
        "rerun_improvement_rate": _rate(improved_reruns, len(rerun_tickets)),
        "total_sources": len(result.sources),
        "total_evidence": len(result.evidence),
        "passed_claims": len([claim for claim in claims if claim.verified_status == "passed"]),
        "report_evidence_coverage": result.report.evidence_coverage_rate if result.report else None,
        "total_llm_tokens": manifest.total_tokens if manifest else None,
        "total_workflow_latency_ms": manifest.total_latency_ms if manifest else None,
        "tool_calls": manifest.total_tool_calls if manifest else len(result.tool_calls),
        "rerun_count": manifest.total_reruns if manifest else sum(ticket.rerun_count for ticket in tickets),
        "loop_count": manifest.total_loops if manifest else None,
    }


def _load_cases() -> list[dict[str, Any]]:
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "eval" / "cases").glob("*.json"))
    ]


def _run_mode(cases: list[dict[str, Any]], mode: str) -> list[dict[str, Any]]:
    from app.core.graph import run_workflow
    from app.models.schemas import Task, TaskConfig

    rows = []
    for case in cases:
        payload = {key: value for key, value in case.items() if key != "case_id"}
        payload["workflow_mode"] = mode
        result = run_workflow(Task(config=TaskConfig(**payload)))
        rows.append({"case_id": case["case_id"], "metrics": _run_metrics(result)})
    return rows


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    claim_total = ticket_total = rerun_total = 0
    bound = unsupported = uncertain_blocked = unresolved = resolved = improved_reruns = 0
    totals: dict[str, int] = {
        "tickets_created": 0,
        "tickets_resolved": 0,
        "tickets_with_new_evidence": 0,
        "claims_improved_after_rerun": 0,
        "total_sources": 0,
        "total_evidence": 0,
        "passed_claims": 0,
        "total_llm_tokens": 0,
        "total_workflow_latency_ms": 0,
        "tool_calls": 0,
        "rerun_count": 0,
        "loop_count": 0,
    }
    report_coverages = []
    for row in rows:
        metrics = row["metrics"]
        claim_total += metrics["_claim_total"]
        bound += metrics["_bound_claims"]
        unsupported += metrics["_unsupported_claims"]
        uncertain_blocked += metrics["_uncertain_blocked_claims"]
        ticket_total += metrics["_ticket_total"]
        unresolved += metrics["_unresolved_tickets"]
        resolved += metrics["_resolved_tickets"]
        rerun_total += metrics["_rerun_tickets"]
        improved_reruns += metrics["_improved_reruns"]
        for key in totals:
            value = metrics.get(key)
            if isinstance(value, int):
                totals[key] += value
        if metrics["report_evidence_coverage"] is not None:
            report_coverages.append(metrics["report_evidence_coverage"])

    result = dict(totals)
    result.update(
        {
            "claim_evidence_binding_rate": _rate(bound, claim_total),
            "unsupported_claim_rate": _rate(unsupported, claim_total),
            "uncertain_blocked_claim_rate": _rate(uncertain_blocked, claim_total),
            "unresolved_ticket_rate": _rate(unresolved, ticket_total),
            "ticket_resolution_rate": _rate(resolved, ticket_total),
            "rerun_improvement_rate": _rate(improved_reruns, rerun_total),
            "report_evidence_coverage": sum(report_coverages) / len(report_coverages) if report_coverages else None,
        }
    )
    return result


def _format(value: Any, metric: str) -> str:
    if value is None:
        return "N/A"
    if metric in PERCENT_METRICS:
        return f"{value:.1%}"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def _markdown(single: dict[str, Any], adaptive: dict[str, Any], case_count: int) -> str:
    metric_order = [
        "claim_evidence_binding_rate",
        "unsupported_claim_rate",
        "uncertain_blocked_claim_rate",
        "unresolved_ticket_rate",
        "tickets_created",
        "tickets_resolved",
        "ticket_resolution_rate",
        "tickets_with_new_evidence",
        "claims_improved_after_rerun",
        "rerun_improvement_rate",
        "total_sources",
        "total_evidence",
        "passed_claims",
        "report_evidence_coverage",
        "total_llm_tokens",
        "total_workflow_latency_ms",
        "tool_calls",
        "rerun_count",
        "loop_count",
    ]
    lines = [
        "# Workflow Evaluation Results",
        "",
        f"Deterministic mock comparison across {case_count} cases. Values are aggregated from actual `WorkflowResult` traces, tool calls, evidence, claims, and Review Tickets.",
        "",
        "| Metric | Single Pass | Adaptive Review | Delta |",
        "|---|---:|---:|---:|",
    ]
    for metric in metric_order:
        left = single.get(metric)
        right = adaptive.get(metric)
        delta = None if left is None or right is None else right - left
        lines.append(f"| {metric} | {_format(left, metric)} | {_format(right, metric)} | {_format(delta, metric)} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Adaptive Review uses the same graph and provider fixtures as Single Pass. Its additional cost is visible in token, latency, tool-call, rerun, and loop metrics; unresolved tickets remain explicit rather than being counted as successful closure.",
            "",
            "## Reproduction",
            "",
            "```bash",
            "python scripts/eval_workflow.py",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the deterministic EvidenceGraph workflow comparison.")
    parser.add_argument("--provider", choices=["mock", "live"], default="mock")
    args = parser.parse_args()
    if args.provider == "mock":
        os.environ["PUBLIC_DEMO_MODE"] = "true"
        os.environ["USE_MOCK_SEARCH"] = "true"
        os.environ["USE_MOCK_LLM"] = "true"
    else:
        os.environ.pop("PUBLIC_DEMO_MODE", None)

    cases = _load_cases()
    single_rows = _run_mode(cases, "single_pass")
    adaptive_rows = _run_mode(cases, "adaptive_review")
    single = _aggregate(single_rows)
    adaptive = _aggregate(adaptive_rows)
    output = {
        "provider": args.provider,
        "case_count": len(cases),
        "modes": {
            "single_pass": {"aggregate": single, "cases": single_rows},
            "adaptive_review": {"aggregate": adaptive, "cases": adaptive_rows},
        },
    }
    result_path = ROOT / "eval" / "results" / "latest.json"
    markdown_path = ROOT / "eval" / "results" / "latest.md"
    result_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown(single, adaptive, len(cases)), encoding="utf-8")
    print(markdown_path.relative_to(ROOT))
    print(json.dumps({"single_pass": single, "adaptive_review": adaptive}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
