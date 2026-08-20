from __future__ import annotations

import json

from app.models.schemas import AgentTraceEvent, GraphState


def trace_event(
    state: GraphState,
    agent: str,
    node: str,
    event_type: str,
    summary: str,
    related_ids: list[str] | None = None,
    *,
    input_summary: str = "",
    output_summary: str = "",
    prompt_name: str = "",
    prompt: str = "",
    input_payload: dict | None = None,
    output_payload: dict | None = None,
    token_count: int | None = None,
    latency_ms: int | None = None,
    provider: str = "",
    provider_request_id: str = "",
    skill_fields: dict[str, str] | None = None,
) -> None:
    skill_fields = skill_fields or {}
    state.trace.append(
        AgentTraceEvent(
            task_id=state.task.task_id,
            agent=agent,
            node=node,
            event_type=event_type,
            summary=summary,
            input_summary=input_summary,
            output_summary=output_summary,
            prompt_name=prompt_name,
            prompt=prompt,
            input_payload=input_payload or {},
            output_payload=output_payload or {},
            token_count=token_count,
            latency_ms=latency_ms,
            provider=provider,
            provider_request_id=provider_request_id,
            skill_name=skill_fields.get("skill_name", ""),
            skill_repo=skill_fields.get("skill_repo", ""),
            skill_path=skill_fields.get("skill_path", ""),
            skill_hash=skill_fields.get("skill_hash", ""),
            skill_license=skill_fields.get("skill_license", ""),
            related_ids=related_ids or [],
        )
    )


def estimate_tokens(*payloads: object) -> int:
    text = " ".join(json.dumps(payload, ensure_ascii=False, default=str) for payload in payloads)
    return max(1, len(text) // 4)


def provider_meta(response: object) -> dict:
    if isinstance(response, dict):
        meta = response.get("__provider_meta")
        if isinstance(meta, dict):
            return meta
    return {}


def provider_request_id(response: object, provider_name: str) -> str:
    if provider_name.startswith("Mock"):
        return "fixture"
    return str(provider_meta(response).get("request_id") or "")


def provider_token_count(response: object, fallback: int) -> int:
    usage = provider_meta(response).get("usage")
    if isinstance(usage, dict):
        total = usage.get("total_tokens")
        if isinstance(total, int):
            return total
    return fallback
