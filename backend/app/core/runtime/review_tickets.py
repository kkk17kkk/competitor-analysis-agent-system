from __future__ import annotations

from app.models.schemas import GraphState, ReviewTicket, now_iso
from app.core.runtime.tracing import trace_event


def matching_ticket_evidence_ids(state: GraphState, ticket: ReviewTicket) -> list[str]:
    if not ticket.product or not ticket.missing_evidence_type:
        return []
    return [
        item.evidence_id
        for item in state.evidence
        if item.status == "active"
        and item.product.casefold() == ticket.product.casefold()
        and item.evidence_type.casefold() == ticket.missing_evidence_type.casefold()
    ]


def matching_ticket_claim_ids(state: GraphState, ticket: ReviewTicket) -> list[str]:
    evidence_ids = set(matching_ticket_evidence_ids(state, ticket))
    if not evidence_ids:
        return []
    return [
        claim.claim_id
        for claim in state.claims
        if claim.verified_status == "passed"
        and claim.included_in_report
        and claim.product.casefold() == ticket.product.casefold()
        and claim.claim_type.casefold() == ticket.missing_evidence_type.casefold()
        and evidence_ids.intersection(claim.supporting_evidence)
    ]


def matching_ticket_claim_statuses(state: GraphState, ticket: ReviewTicket) -> list[dict[str, object]]:
    if not ticket.product or not ticket.missing_evidence_type:
        return []
    return [
        {
            "claim_id": claim.claim_id,
            "product": claim.product,
            "claim_type": claim.claim_type,
            "verified_status": claim.verified_status,
            "included_in_report": claim.included_in_report,
            "supporting_evidence": list(claim.supporting_evidence),
        }
        for claim in state.claims
        if claim.product.casefold() == ticket.product.casefold()
        and claim.claim_type.casefold() == ticket.missing_evidence_type.casefold()
    ]


def start_review_ticket_rerun(state: GraphState, ticket: ReviewTicket) -> None:
    ticket.status = "rerun_started"
    if not ticket.added_evidence_ids and not ticket.improved_claim_ids:
        ticket.before_evidence_ids = matching_ticket_evidence_ids(state, ticket)
        ticket.before_claim_statuses = matching_ticket_claim_statuses(state, ticket)
    ticket.added_evidence_ids = []
    ticket.improved_claim_ids = []
    ticket.after_claim_statuses = []


def resolve_review_ticket_improvements(state: GraphState) -> int:
    resolved = 0
    for ticket in state.review_tickets:
        if ticket.status != "rerun_started":
            continue
        current = set(matching_ticket_evidence_ids(state, ticket))
        before = set(ticket.before_evidence_ids)
        added = sorted(current - before)
        after_statuses = matching_ticket_claim_statuses(state, ticket)
        before_passed = any(
            item.get("verified_status") == "passed" and item.get("included_in_report")
            for item in ticket.before_claim_statuses
        )
        improved = [
            claim_id
            for claim_id in matching_ticket_claim_ids(state, ticket)
            if any(
                claim.claim_id == claim_id and set(claim.supporting_evidence).intersection(added)
                for claim in state.claims
            )
        ]
        ticket.added_evidence_ids = added
        ticket.improved_claim_ids = improved
        ticket.after_claim_statuses = after_statuses
        if added and improved and not before_passed:
            ticket.status = "resolved"
            ticket.resolution_summary = (
                f"Rerun added {len(added)} matching evidence item(s) and improved {len(improved)} bound claim(s)."
            )
            ticket.resolved_at = now_iso()
            resolved += 1
        else:
            ticket.resolution_summary = (
                "Rerun did not prove a before/after claim improvement with newly bound evidence; keep this ticket in reviewer attention."
            )
    if resolved:
        trace_event(
            state,
            "CriticAgent",
            "critic",
            "review_ticket_improvement_verified",
            f"Verified {resolved} Review Ticket improvement(s) through added evidence and improved claims.",
            [ticket.ticket_id for ticket in state.review_tickets if ticket.status == "resolved" and ticket.added_evidence_ids],
            output_payload={
                ticket.ticket_id: {
                    "added_evidence_ids": ticket.added_evidence_ids,
                    "improved_claim_ids": ticket.improved_claim_ids,
                }
                for ticket in state.review_tickets
                if ticket.status == "resolved" and ticket.added_evidence_ids
            },
        )
    return resolved
