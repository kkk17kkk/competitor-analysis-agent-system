import pytest

from app.core.graph import (
    review_fallback_node,
    review_router_node,
    route_after_critic,
    route_after_review_router,
    run_workflow,
)
from app.core.routing import eligible_review_tickets, route_for_target, select_review_ticket
from app.models.schemas import GraphState, ReviewTicket, Task, TaskConfig


@pytest.fixture(autouse=True)
def use_mock_providers(monkeypatch):
    monkeypatch.setenv("USE_MOCK_SEARCH", "true")
    monkeypatch.setenv("USE_MOCK_LLM", "true")


def _task(**config):
    return Task(
        config=TaskConfig(
            domain="ai_tools",
            target_product="Cursor",
            competitors=["TRAE"],
            analysis_goals=["positioning"],
            **config,
        )
    )


def _ticket(task, *, target="ResearchAgent", severity="medium", rerun_count=0, created_at="2026-01-01T00:00:00+00:00"):
    return ReviewTicket(
        task_id=task.task_id,
        reviewer="CriticAgent",
        target_node=target,
        reason="A focused evidence check is required.",
        required_action="Collect and review the missing evidence.",
        severity=severity,
        rerun_count=rerun_count,
        created_at=created_at,
    )


def test_ticket_priority_is_severity_then_creation_order():
    task = _task()
    older_high = _ticket(task, severity="high", created_at="2026-01-01T00:00:00+00:00")
    newer_critical = _ticket(task, severity="critical", created_at="2026-01-02T00:00:00+00:00")
    selected = select_review_ticket([older_high, newer_critical])
    assert selected is newer_critical


def test_ticket_priority_tie_preserves_creation_order():
    task = _task()
    first = _ticket(task, severity="high", created_at="2026-01-01T00:00:00+00:00")
    second = _ticket(task, severity="high", created_at="2026-01-01T00:00:00+00:00")
    first.ticket_id, second.ticket_id = "rt_a", "rt_b"
    assert select_review_ticket([second, first]) is second


def test_all_supported_targets_have_explicit_routes_and_unknown_falls_back():
    assert route_for_target("ResearchAgent") == "research_rerun"
    assert route_for_target("SocialListeningAgent") == "social_rerun"
    assert route_for_target("InteractionAgent") == "interaction_rerun"
    assert route_for_target("AnalystAgent") == "analyst_rerun"
    assert route_for_target("EvidenceReviewer") == "reviewer_fallback"
    assert route_for_target("UnexpectedAgent") == "reviewer_fallback"


def test_max_rerun_ticket_is_not_eligible():
    task = _task()
    ticket = _ticket(task, rerun_count=2)
    assert eligible_review_tickets([ticket]) == []


def test_router_records_unknown_target_fallback():
    task = _task()
    ticket = _ticket(task, target="UnexpectedAgent", severity="critical")
    state = GraphState(task=task, review_tickets=[ticket])
    review_router_node(state)
    assert route_after_review_router(state) == "reviewer_fallback"
    review_fallback_node(state)
    assert any(event.event_type == "review_route_fallback" for event in state.trace)


def test_single_pass_does_not_enter_targeted_rerun():
    task = _task(workflow_mode="single_pass")
    state = GraphState(task=task, review_tickets=[_ticket(task)])
    assert route_after_critic(state) == "evidence_reviewer_node"


def test_adaptive_mock_workflow_records_selected_route_and_manifest():
    result = run_workflow(_task())
    assert result.manifest is not None
    assert result.manifest.workflow_mode == "adaptive_review"
    assert result.manifest.total_tool_calls == len(result.tool_calls)
    assert result.manifest.total_tokens >= 0
    assert any(event.event_type == "review_ticket_selected" for event in result.trace)


def test_single_pass_mock_workflow_preserves_tickets_without_rerun_trace():
    result = run_workflow(_task(workflow_mode="single_pass"))
    assert result.manifest is not None
    assert result.manifest.workflow_mode == "single_pass"
    assert not any(event.event_type == "review_ticket_selected" for event in result.trace)


def test_manifest_endpoints_return_persisted_runtime_manifest(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from app.api import routes
    from app.main import app
    from app.storage.sqlite import SQLiteStore

    store = SQLiteStore(str(tmp_path / "manifest.db"))
    monkeypatch.setattr(routes, "store", store)
    task = store.create_task(_task(workflow_mode="single_pass"))
    result = run_workflow(task)
    store.save_result(result)

    client = TestClient(app)
    direct = client.get(f"/api/tasks/{task.task_id}/manifest")
    envelope = client.get(f"/api/v1/tasks/{task.task_id}/manifest")

    assert direct.status_code == 200
    assert direct.json()["run_id"] == result.manifest.run_id
    assert direct.json()["workflow_mode"] == "single_pass"
    assert envelope.status_code == 200
    assert envelope.json()["data"]["graph_version"] == result.manifest.graph_version
