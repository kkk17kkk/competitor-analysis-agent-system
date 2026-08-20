from __future__ import annotations

import time
from collections.abc import Iterator

from langgraph.graph import END, START, StateGraph

from app.core.nodes import (
    analyst_node,
    critic_node,
    evidence_extractor_node,
    evidence_reviewer_node,
    finalize_node,
    interaction_node,
    planner_node,
    research_node,
    social_listening_node,
    source_normalizer_node,
    template_node,
    trust_summary_node,
    writer_node,
)
from app.core.routing import route_for_ticket, select_review_ticket
from app.core.runtime.manifest import build_run_manifest
from app.core.runtime.review_tickets import (
    matching_ticket_claim_ids,
    resolve_review_ticket_improvements,
    start_review_ticket_rerun,
)
from app.core.runtime.tracing import trace_event
from app.models.schemas import AgentTraceEvent, GraphState, Task, WorkflowResult, now_iso


def _open_tickets(state: GraphState):
    return [ticket for ticket in state.review_tickets if ticket.status == "open"]


def route_after_critic(state: GraphState) -> str:
    if state.task.config.workflow_mode == "single_pass":
        return "evidence_reviewer_node"
    if not _open_tickets(state):
        return "evidence_reviewer_node"
    if state.loop_count >= state.max_loops or select_review_ticket(state.review_tickets) is None:
        return "review_loop_stop_node"
    return "review_router_node"


def _active_ticket(state: GraphState):
    return next(
        (ticket for ticket in state.review_tickets if ticket.ticket_id == state.active_review_ticket_id),
        None,
    )


def review_router_node(state: GraphState) -> GraphState:
    ticket = select_review_ticket(state.review_tickets)
    if ticket is None:
        state.active_review_ticket_id = ""
        state.active_review_route = ""
        trace_event(
            state,
            "ReviewRouter",
            "review_router",
            "review_routing_skipped",
            "No open Review Ticket is eligible for another rerun.",
        )
        return state

    state.active_review_ticket_id = ticket.ticket_id
    state.active_review_route = route_for_ticket(ticket)
    ticket.rerun_count += 1
    start_review_ticket_rerun(state, ticket)
    state.loop_count += 1
    is_fallback = state.active_review_route == "reviewer_fallback" and ticket.target_node != "EvidenceReviewer"
    trace_event(
        state,
        "ReviewRouter",
        "review_router",
        "review_ticket_selected",
        f"Selected {ticket.ticket_id} for {state.active_review_route} (rerun {ticket.rerun_count}/{ticket.max_reruns}).",
        [ticket.ticket_id],
        input_payload={
            "ticket_id": ticket.ticket_id,
            "target_node": ticket.target_node,
            "severity": ticket.severity,
            "before_evidence_ids": ticket.before_evidence_ids[:20],
            "before_claim_statuses": ticket.before_claim_statuses[:20],
        },
        output_payload={
            "route": state.active_review_route,
            "rerun_index": ticket.rerun_count,
            "fallback": is_fallback,
        },
    )
    return state


def route_after_review_router(state: GraphState) -> str:
    return state.active_review_route or "reviewer_fallback"


def _prepare_active_ticket(state: GraphState):
    ticket = _active_ticket(state)
    if ticket and ticket.status == "open":
        start_review_ticket_rerun(state, ticket)
    return ticket


def review_research_node(state: GraphState) -> GraphState:
    _prepare_active_ticket(state)
    state = research_node(state)
    state = source_normalizer_node(state)
    state = evidence_extractor_node(state)
    state = interaction_node(state)
    return analyst_node(state)


def review_social_node(state: GraphState) -> GraphState:
    _prepare_active_ticket(state)
    state = social_listening_node(state)
    state = source_normalizer_node(state)
    state = evidence_extractor_node(state)
    return analyst_node(state)


def review_interaction_node(state: GraphState) -> GraphState:
    _prepare_active_ticket(state)
    state = interaction_node(state)
    return analyst_node(state)


def review_analyst_node(state: GraphState) -> GraphState:
    _prepare_active_ticket(state)
    return analyst_node(state)


def review_fallback_node(state: GraphState) -> GraphState:
    ticket = _prepare_active_ticket(state)
    if ticket:
        trace_event(
            state,
            "ReviewRouter",
            "review_router",
            "review_route_fallback",
            f"Unknown target node {ticket.target_node!r}; routed safely to EvidenceReviewer.",
            [ticket.ticket_id],
            input_payload={"target_node": ticket.target_node},
            output_payload={"route": "EvidenceReviewer", "fallback": True},
        )
    return state


def review_resolution_node(state: GraphState) -> GraphState:
    ticket = _active_ticket(state)
    evidence_reviewer_node(state)
    resolve_review_ticket_improvements(state)
    if ticket and ticket.status == "rerun_started":
        if ticket.rerun_count >= ticket.max_reruns or state.loop_count >= state.max_loops:
            ticket.status = "open"
            ticket.resolution_summary = (
                "Rerun stopped because the Review Ticket reached its configured rerun or workflow loop limit."
            )
            result_event = "review_ticket_rerun_stopped"
        else:
            ticket.status = "open"
            ticket.resolution_summary = (
                "Rerun did not prove a claim improvement; the ticket remains open for the next deterministic review pass."
            )
            result_event = "review_ticket_rerun_unresolved"
        trace_event(
            state,
            "ReviewRouter",
            "review_router",
            result_event,
            ticket.resolution_summary,
            [ticket.ticket_id],
            input_payload={
                "rerun_index": ticket.rerun_count,
                "before_evidence_ids": ticket.before_evidence_ids[:20],
                "before_claim_statuses": ticket.before_claim_statuses[:20],
            },
            output_payload={
                "after_evidence_ids": ticket.added_evidence_ids[:20],
                "after_claim_statuses": ticket.after_claim_statuses[:20],
                "improved_claim_ids": ticket.improved_claim_ids[:20],
                "resolution": ticket.status,
            },
        )
    state.active_review_ticket_id = ""
    state.active_review_route = ""
    return state


def review_loop_stop_node(state: GraphState) -> GraphState:
    stopped = []
    for ticket in _open_tickets(state):
        ticket.resolution_summary = "Review rerun stopped by the configured loop or rerun limit."
        stopped.append(ticket.ticket_id)
    if stopped:
        trace_event(
            state,
            "ReviewRouter",
            "review_router",
            "review_rerun_stopped",
            f"Stopped {len(stopped)} open Review Ticket(s) at the configured limit.",
            stopped,
            output_payload={"stopped_ticket_ids": stopped, "loop_count": state.loop_count, "max_loops": state.max_loops},
        )
    return state


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("planner_node", planner_node)
    graph.add_node("template_node", template_node)
    graph.add_node("research_node", research_node)
    graph.add_node("social_listening_node", social_listening_node)
    graph.add_node("source_normalizer_node", source_normalizer_node)
    graph.add_node("evidence_extractor_node", evidence_extractor_node)
    graph.add_node("interaction_node", interaction_node)
    graph.add_node("analyst_node", analyst_node)
    graph.add_node("critic_node", critic_node)
    graph.add_node("trust_summary_node", trust_summary_node)
    graph.add_node("writer_node", writer_node)
    graph.add_node("evidence_reviewer_node", evidence_reviewer_node)
    graph.add_node("finalize_node", finalize_node)

    graph.add_node("review_router_node", review_router_node)
    graph.add_node("review_research_node", review_research_node)
    graph.add_node("review_social_node", review_social_node)
    graph.add_node("review_interaction_node", review_interaction_node)
    graph.add_node("review_analyst_node", review_analyst_node)
    graph.add_node("review_fallback_node", review_fallback_node)
    graph.add_node("review_resolution_node", review_resolution_node)
    graph.add_node("review_loop_stop_node", review_loop_stop_node)

    graph.add_edge(START, "planner_node")
    graph.add_edge("planner_node", "template_node")
    graph.add_edge("template_node", "research_node")
    graph.add_edge("research_node", "social_listening_node")
    graph.add_edge("social_listening_node", "source_normalizer_node")
    graph.add_edge("source_normalizer_node", "evidence_extractor_node")
    graph.add_edge("evidence_extractor_node", "interaction_node")
    graph.add_edge("interaction_node", "analyst_node")
    graph.add_edge("analyst_node", "critic_node")
    graph.add_conditional_edges(
        "critic_node",
        route_after_critic,
        {
            "review_router_node": "review_router_node",
            "review_loop_stop_node": "review_loop_stop_node",
            "evidence_reviewer_node": "evidence_reviewer_node",
        },
    )
    graph.add_conditional_edges(
        "review_router_node",
        route_after_review_router,
        {
            "research_rerun": "review_research_node",
            "social_rerun": "review_social_node",
            "interaction_rerun": "review_interaction_node",
            "analyst_rerun": "review_analyst_node",
            "reviewer_fallback": "review_fallback_node",
        },
    )
    graph.add_edge("review_research_node", "review_resolution_node")
    graph.add_edge("review_social_node", "review_resolution_node")
    graph.add_edge("review_interaction_node", "review_resolution_node")
    graph.add_edge("review_analyst_node", "review_resolution_node")
    graph.add_edge("review_fallback_node", "review_resolution_node")
    graph.add_edge("review_resolution_node", "critic_node")
    graph.add_edge("review_loop_stop_node", "evidence_reviewer_node")
    graph.add_edge("evidence_reviewer_node", "trust_summary_node")
    graph.add_edge("trust_summary_node", "writer_node")
    graph.add_edge("writer_node", "finalize_node")
    graph.add_edge("finalize_node", END)
    return graph.compile()


compiled_graph = build_graph()


def _refresh_runtime_latency(state: GraphState, started: float) -> None:
    elapsed_ms = max(1, int((time.perf_counter() - started) * 1000))
    if state.manifest is None:
        state.manifest = build_run_manifest(state)
    state.manifest.total_latency_ms = max(state.manifest.total_latency_ms, elapsed_ms)


def run_workflow(task: Task) -> WorkflowResult:
    started = time.perf_counter()
    initial = GraphState(task=task)
    final_state = compiled_graph.invoke(initial, config={"recursion_limit": 120})
    if isinstance(final_state, dict):
        final_state = GraphState.model_validate(final_state)
    _refresh_runtime_latency(final_state, started)
    return final_state.result()


def stream_workflow(task: Task) -> Iterator[dict]:
    started = time.perf_counter()
    initial = GraphState(task=task)
    seen_trace_events = 0
    final_state = initial
    yield {"event": "workflow_started", "data": {"task_id": task.task_id, "status": "running"}}
    for state_update in compiled_graph.stream(initial, stream_mode="values", config={"recursion_limit": 120}):
        final_state = GraphState.model_validate(state_update)
        new_events = final_state.trace[seen_trace_events:]
        for trace_event_item in new_events:
            yield {"event": "trace", "data": trace_event_item.model_dump(mode="json")}
        seen_trace_events = len(final_state.trace)
        yield {
            "event": "state",
            "data": {
                "task_id": task.task_id,
                "trace_count": len(final_state.trace),
                "source_count": len(final_state.sources),
                "evidence_count": len(final_state.evidence),
                "claim_count": len(final_state.claims),
                "ticket_count": len(final_state.review_tickets),
            },
        }
    _refresh_runtime_latency(final_state, started)
    yield {"event": "result", "data": final_state.result().model_dump(mode="json")}
    yield {"event": "workflow_completed", "data": {"task_id": task.task_id, "status": final_state.task.status}}


def _state_from_result(result: WorkflowResult) -> GraphState:
    return GraphState(
        task=result.task,
        brief=result.brief,
        template=result.template,
        search_plan=result.search_plan,
        tool_calls=result.tool_calls,
        sources=result.sources,
        evidence=result.evidence,
        claims=result.claims,
        review_tickets=result.review_tickets,
        trace=result.trace,
        trust_summary=result.trust_summary,
        report=result.report,
        social_posts=result.social_posts,
        social_insights=result.social_insights,
        skill_assignments=result.skill_assignments,
        manifest=result.manifest,
    )


def _run_manual_targeted_path(state: GraphState, ticket):
    state.active_review_ticket_id = ticket.ticket_id
    state.active_review_route = route_for_ticket(ticket)
    start_review_ticket_rerun(state, ticket)
    if state.active_review_route == "research_rerun":
        state = research_node(state)
        state = source_normalizer_node(state)
        state = evidence_extractor_node(state)
        state = interaction_node(state)
        state = analyst_node(state)
    elif state.active_review_route == "social_rerun":
        state = social_listening_node(state)
        state = source_normalizer_node(state)
        state = evidence_extractor_node(state)
        state = analyst_node(state)
    elif state.active_review_route == "interaction_rerun":
        state = interaction_node(state)
        state = analyst_node(state)
    elif state.active_review_route == "analyst_rerun":
        state = analyst_node(state)
    state = evidence_reviewer_node(state)
    resolve_review_ticket_improvements(state)
    state = trust_summary_node(state)
    state = writer_node(state)
    state.manifest = build_run_manifest(state)
    return state


def rerun_review_ticket(result: WorkflowResult, ticket_id: str) -> WorkflowResult:
    started = time.perf_counter()
    state = _state_from_result(result)
    ticket = next(ticket for ticket in state.review_tickets if ticket.ticket_id == ticket_id)
    was_resolved = ticket.status == "resolved" or bool(ticket.improved_claim_ids and ticket.added_evidence_ids)
    ticket.status = "open"
    state = _run_manual_targeted_path(state, ticket)
    if was_resolved and ticket.status == "rerun_started":
        revalidated = matching_ticket_claim_ids(state, ticket)
        if revalidated:
            ticket.improved_claim_ids = revalidated
            ticket.status = "resolved"
            ticket.resolution_summary = "Manual rerun revalidated the existing bound evidence and claim improvement."
            ticket.resolved_at = now_iso()
            trace_event(
                state,
                "ReviewTicketService",
                "review_ticket",
                "ticket_reopened_revalidated",
                ticket.resolution_summary,
                [ticket.ticket_id, *revalidated],
            )
    _refresh_runtime_latency(state, started)
    return state.result()


def apply_review_ticket_claim_decision(result: WorkflowResult, ticket_id: str, claim_status: str, summary: str) -> WorkflowResult:
    state = _state_from_result(result)
    ticket = next(ticket for ticket in state.review_tickets if ticket.ticket_id == ticket_id)
    affected_claims = [
        claim
        for claim in state.claims
        if (not ticket.product or claim.product == ticket.product)
        and (not ticket.missing_evidence_type or claim.claim_type == ticket.missing_evidence_type)
    ]
    for claim in affected_claims:
        claim.verified_status = claim_status
        claim.included_in_report = False
        claim.note = summary
    ticket.status = "resolved"
    ticket.resolution_summary = summary
    ticket.resolved_at = now_iso()
    state.trace.append(
        AgentTraceEvent(
            task_id=state.task.task_id,
            agent="ReviewTicketService",
            node="review_ticket",
            event_type=f"ticket_{claim_status}",
            summary=summary,
            related_ids=[ticket_id, *[claim.claim_id for claim in affected_claims]],
        )
    )
    state = trust_summary_node(state)
    state = writer_node(state)
    state.manifest = build_run_manifest(state)
    return state.result()
