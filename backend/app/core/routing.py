from __future__ import annotations

from collections.abc import Iterable

from app.models.schemas import ReviewTicket


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}

ROUTE_BY_TARGET = {
    "ResearchAgent": "research_rerun",
    "SocialListeningAgent": "social_rerun",
    "InteractionAgent": "interaction_rerun",
    "AnalystAgent": "analyst_rerun",
    "EvidenceReviewer": "reviewer_fallback",
}


def eligible_review_tickets(tickets: Iterable[ReviewTicket]) -> list[ReviewTicket]:
    return [
        ticket
        for ticket in tickets
        if ticket.status == "open" and ticket.rerun_count < ticket.max_reruns
    ]


def select_review_ticket(tickets: Iterable[ReviewTicket]) -> ReviewTicket | None:
    candidates = eligible_review_tickets(tickets)
    if not candidates:
        return None
    # Preserve the incoming list order when timestamps collide. The graph
    # appends tickets in creation order, so a random UUID must not influence
    # the deterministic rerun priority.
    return min(
        enumerate(candidates),
        key=lambda item: (
            -SEVERITY_RANK.get(item[1].severity, 0),
            item[1].created_at,
            item[0],
        ),
    )[1]


def route_for_target(target_node: str) -> str:
    return ROUTE_BY_TARGET.get(target_node, "reviewer_fallback")


def route_for_ticket(ticket: ReviewTicket) -> str:
    return route_for_target(ticket.target_node)
