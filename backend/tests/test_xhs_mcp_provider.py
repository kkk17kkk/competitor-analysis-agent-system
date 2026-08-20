from __future__ import annotations

import socket
from pathlib import Path

import pytest

from app.providers.errors import ProviderRequestError
from app.providers.xhs_mcp import DEFAULT_XHS_MCP_URL, XhsMcpClient


def test_core_xhs_provider_is_http_only():
    source = Path(__file__).resolve().parents[1] / "app" / "providers" / "xhs_mcp.py"
    text = source.read_text(encoding="utf-8")
    assert "from xhs_mcp import" not in text
    assert "_should_use_local_tool_fallback" not in text


def test_should_auto_start_only_when_default_local_port_is_closed(monkeypatch):
    from app.providers import xhs_mcp

    monkeypatch.setenv("XHS_MCP_AUTOSTART", "true")
    monkeypatch.setattr(xhs_mcp, "_is_local_port_closed", lambda base_url: True)

    assert xhs_mcp._should_auto_start_mcp(
        DEFAULT_XHS_MCP_URL,
        ProviderRequestError("Cannot connect to xiaohongshu-mcp at http://localhost:18060/mcp: <urlopen error [Errno 61] Connection refused>"),
    )
    assert not xhs_mcp._should_auto_start_mcp(
        "http://example.com/mcp",
        ProviderRequestError("Cannot connect to xiaohongshu-mcp at http://example.com/mcp: <urlopen error [Errno 61] Connection refused>"),
    )
    assert not xhs_mcp._should_auto_start_mcp(
        DEFAULT_XHS_MCP_URL,
        ProviderRequestError("Timed out connecting to xiaohongshu-mcp at http://localhost:18060/mcp."),
    )
    monkeypatch.setattr(xhs_mcp, "_is_local_port_closed", lambda base_url: False)
    assert xhs_mcp._should_auto_start_mcp(
        DEFAULT_XHS_MCP_URL,
        ProviderRequestError("Cannot connect to xiaohongshu-mcp at http://localhost:18060/mcp: <urlopen error [WinError 10061] connection refused>"),
    )


def test_external_xhs_autostart_is_opt_in(monkeypatch):
    from app.providers import xhs_mcp

    monkeypatch.delenv("XHS_MCP_AUTOSTART", raising=False)
    monkeypatch.setattr(xhs_mcp, "_is_local_port_closed", lambda base_url: True)
    assert not xhs_mcp._should_auto_start_mcp(
        DEFAULT_XHS_MCP_URL,
        ProviderRequestError("Cannot connect to xiaohongshu-mcp at http://localhost:18060/mcp: Connection refused"),
    )


def test_autostart_python_can_target_dedicated_xhs_environment(monkeypatch):
    from app.providers import xhs_mcp

    monkeypatch.setenv("XHS_MCP_AUTOSTART_PYTHON", r"D:\xhs\.venv\Scripts\python.exe")
    assert xhs_mcp._xhs_autostart_python() == r"D:\xhs\.venv\Scripts\python.exe"


def test_is_local_port_closed_treats_timeout_as_not_closed(monkeypatch):
    from app.providers import xhs_mcp

    def fake_create_connection(*_args, **_kwargs):
        raise socket.timeout()

    monkeypatch.setattr(socket, "create_connection", fake_create_connection)
    assert xhs_mcp._is_local_port_closed(DEFAULT_XHS_MCP_URL) is False


def test_call_tool_auto_starts_bridge_and_retries(monkeypatch):
    from app.providers import xhs_mcp

    monkeypatch.setenv("XHS_MCP_AUTOSTART", "true")
    client = XhsMcpClient()
    calls: list[str] = []

    def fake_jsonrpc(method, params, **_kwargs):
        calls.append(method)
        if len(calls) == 1:
            raise ProviderRequestError("Cannot connect to xiaohongshu-mcp at http://localhost:18060/mcp: <urlopen error [Errno 61] Connection refused>")
        return {"result": {"content": [{"type": "text", "text": "{\"logged_in\": true}"}]}}

    started: list[str] = []

    monkeypatch.setattr(client, "_jsonrpc", fake_jsonrpc)
    monkeypatch.setattr(xhs_mcp, "_ensure_local_mcp_server", lambda base_url: started.append(base_url))
    monkeypatch.setattr(xhs_mcp, "_is_local_port_closed", lambda base_url: True)

    result = client.check_login_status()

    assert started == [DEFAULT_XHS_MCP_URL]
    assert result["logged_in"] is True
    assert calls == ["tools/call", "tools/call"]
