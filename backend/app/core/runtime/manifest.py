from __future__ import annotations

import os

from app.models.schemas import GraphState, RunManifest, now_iso


GRAPH_VERSION = "evidencegraph-adaptive-routing-v1"


def build_run_manifest(state: GraphState, *, completed_at: str | None = None) -> RunManifest:
    provider_events = [event for event in state.trace if event.provider]
    search_provider = next(
        (event.provider for event in provider_events if event.node == "research"),
        "",
    )
    llm_provider = next(
        (
            event.provider
            for event in provider_events
            if event.node in {"analyst", "critic", "writer"}
        ),
        "",
    )
    enabled_skills = sorted(
        {
            event.skill_name
            for event in state.trace
            if event.skill_name
        }
        | {
            str(assignment.get("skill_id") or "")
            for assignment in state.skill_assignments
            if assignment.get("skill_id")
        }
    )
    total_tokens = sum(event.token_count or 0 for event in provider_events)
    if not total_tokens:
        total_tokens = sum(call.token_count or 0 for call in state.tool_calls)
    # Provider trace events carry token metadata, while tool calls are the
    # authoritative timing records for both search and LLM execution.
    total_latency_ms = sum(call.latency_ms or 0 for call in state.tool_calls)
    fixture_mode = bool(state.trust_summary.fixture_mode) if state.trust_summary else any(
        call.provider_mode.startswith("mock") for call in state.tool_calls
    )
    return RunManifest(
        run_id=state.run_id,
        task_id=state.task.task_id,
        workflow_mode=state.task.config.workflow_mode,
        graph_version=GRAPH_VERSION,
        app_version=os.getenv("APP_VERSION", ""),
        search_provider=search_provider,
        llm_provider=llm_provider,
        llm_model=os.getenv("DEEPSEEK_MODEL", "") if llm_provider == "DeepSeekLLMProvider" else "",
        fixture_mode=fixture_mode,
        enabled_skills=enabled_skills,
        started_at=state.started_at,
        completed_at=completed_at or state.completed_at or now_iso(),
        total_tokens=total_tokens,
        total_latency_ms=total_latency_ms,
        total_tool_calls=len(state.tool_calls),
        total_reruns=sum(ticket.rerun_count for ticket in state.review_tickets),
        total_loops=state.loop_count,
    )
