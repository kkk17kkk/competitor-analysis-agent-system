from __future__ import annotations

import atexit
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import ProxyHandler, Request, build_opener, urlopen
from uuid import uuid4

from app.providers.errors import ProviderRequestError


DEFAULT_XHS_MCP_URL = "http://localhost:18060/mcp"
_AUTO_START_LOCK = threading.Lock()
_AUTO_STARTED_PROCESS: subprocess.Popen[str] | None = None


class XhsMcpClient:
    """HTTP JSON-RPC client for an external Xiaohongshu MCP service."""

    provider_name = "XhsMcpProvider"

    def __init__(self, base_url: str | None = None, timeout: float = 15.0):
        self.base_url = (base_url or os.getenv("XHS_MCP_URL") or DEFAULT_XHS_MCP_URL).strip()
        self.timeout = timeout
        self.session_id = ""

    def check_login_status(self) -> dict[str, Any]:
        return self.call_tool("check_login_status", {})

    def get_login_qrcode(self) -> dict[str, Any]:
        return self.call_tool("get_login_qrcode", {})

    def check_qrcode_status(self, qr_id: str, code: str) -> dict[str, Any]:
        return self.call_tool("check_qrcode_status", {"qr_id": qr_id, "code": code})

    def search_feeds(self, keyword: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"keyword": keyword}
        if filters:
            payload["filters"] = filters
            if filters.get("limit") or filters.get("max_results"):
                payload["limit"] = filters.get("limit") or filters.get("max_results")
        return self.call_tool("search_feeds", payload)

    def get_feed_detail(self, feed_id: str, xsec_token: str, load_all_comments: bool = False) -> dict[str, Any]:
        return self.call_tool(
            "get_feed_detail",
            {"feed_id": feed_id, "xsec_token": xsec_token, "load_all_comments": load_all_comments},
        )

    def get_feed_comments(self, feed_id: str, limit: int = 30, cursor: str = "", xsec_token: str = "") -> dict[str, Any]:
        return self.call_tool(
            "get_feed_comments",
            {"feed_id": feed_id, "limit": limit, "cursor": cursor, "xsec_token": xsec_token},
        )

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._jsonrpc("tools/call", {"name": name, "arguments": arguments})
        except ProviderRequestError as direct_error:
            if _should_auto_start_mcp(self.base_url, direct_error):
                _ensure_local_mcp_server(self.base_url)
                try:
                    response = self._jsonrpc("tools/call", {"name": name, "arguments": arguments})
                except ProviderRequestError as auto_started_error:
                    direct_error = ProviderRequestError(
                        f"{direct_error} Auto-started external xiaohongshu-mcp bridge, but the request still failed: {auto_started_error}"
                    )
                else:
                    result = response.get("result")
                    if isinstance(result, dict) and result.get("isError"):
                        raise ProviderRequestError(_stringify_mcp_content(result) or f"{name} returned an MCP error.")
                    return _normalize_mcp_result(result)
            self._initialize()
            try:
                response = self._jsonrpc("tools/call", {"name": name, "arguments": arguments})
            except ProviderRequestError as initialized_error:
                raise ProviderRequestError(f"{direct_error} Retried after MCP initialize: {initialized_error}") from initialized_error
        result = response.get("result")
        if isinstance(result, dict) and result.get("isError"):
            raise ProviderRequestError(_stringify_mcp_content(result) or f"{name} returned an MCP error.")
        return _normalize_mcp_result(result)

    def _initialize(self) -> None:
        try:
            self._jsonrpc(
                "initialize",
                {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "competitor-analysis-agent-system", "version": "0.1.0"},
                },
                allow_empty_params=True,
            )
        except ProviderRequestError:
            self._jsonrpc("initialize", {}, allow_empty_params=True)
        try:
            self._jsonrpc("notifications/initialized", {}, notification=True, allow_empty_params=True)
        except ProviderRequestError:
            pass

    def _jsonrpc(
        self,
        method: str,
        params: dict[str, Any],
        *,
        notification: bool = False,
        allow_empty_params: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if not notification:
            payload["id"] = f"xhs_{uuid4().hex[:10]}"
        if params or allow_empty_params:
            payload["params"] = params
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        request = Request(self.base_url, data=body, headers=headers, method="POST")
        try:
            with _open_url(request, self.base_url, self.timeout) as response:
                self.session_id = response.headers.get("mcp-session-id") or response.headers.get("Mcp-Session-Id") or self.session_id
                raw = response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise ProviderRequestError(
                f"Cannot connect to xiaohongshu-mcp at {self.base_url}: HTTP Error {exc.code}: {detail or exc.reason}"
            ) from exc
        except URLError as exc:
            raise ProviderRequestError(f"Cannot connect to xiaohongshu-mcp at {self.base_url}: {exc}") from exc
        except TimeoutError as exc:
            raise ProviderRequestError(f"Timed out connecting to xiaohongshu-mcp at {self.base_url}.") from exc

        if notification and not raw.strip():
            return {}
        payload = _parse_json_or_sse(raw)
        if not isinstance(payload, dict):
            raise ProviderRequestError("xiaohongshu-mcp returned a non-object response.")
        if payload.get("error"):
            raise ProviderRequestError(str(payload["error"]))
        return payload


def _is_default_local_mcp_url(base_url: str) -> bool:
    parsed = urlparse(base_url)
    return (
        parsed.scheme == "http"
        and parsed.hostname in {"localhost", "127.0.0.1"}
        and (parsed.port or 80) == 18060
        and parsed.path.rstrip("/") == "/mcp"
    )


def _open_url(request: Request, base_url: str, timeout: float):
    if _is_default_local_mcp_url(base_url):
        return build_opener(ProxyHandler({})).open(request, timeout=timeout)
    return urlopen(request, timeout=timeout)


def _should_auto_start_mcp(base_url: str, exc: ProviderRequestError) -> bool:
    if os.getenv("XHS_MCP_AUTOSTART", "false").strip().lower() in {"0", "false", "no"}:
        return False
    if not _is_default_local_mcp_url(base_url):
        return False
    message = str(exc)
    refused_markers = ("Connection refused", "Errno 61", "Errno 111", "WinError 10061", "10061")
    if not any(marker in message for marker in refused_markers):
        return False
    if "10061" in message:
        return True
    return _is_local_port_closed(base_url)


def _ensure_local_mcp_server(base_url: str) -> None:
    global _AUTO_STARTED_PROCESS

    with _AUTO_START_LOCK:
        if _healthcheck_ok(_health_url_for_mcp(base_url)):
            return
        if _AUTO_STARTED_PROCESS is not None and _AUTO_STARTED_PROCESS.poll() is None:
            _wait_for_local_mcp_ready(base_url, _AUTO_STARTED_PROCESS)
            return

        env = dict(os.environ)
        env.setdefault("PYTHONUNBUFFERED", "1")
        _AUTO_STARTED_PROCESS = subprocess.Popen(
            [_xhs_autostart_python(), str(_xhs_bridge_script_path())],
            cwd=str(_xhs_repo_root()),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
            start_new_session=True,
        )
        _wait_for_local_mcp_ready(base_url, _AUTO_STARTED_PROCESS)


def _xhs_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _xhs_bridge_script_path() -> Path:
    return _xhs_repo_root() / "scripts" / "run_xhs_mcp_bridge.py"


def _xhs_autostart_python() -> str:
    configured = os.getenv("XHS_MCP_AUTOSTART_PYTHON", "").strip()
    return configured or sys.executable


def _is_local_port_closed(base_url: str) -> bool:
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 80
    try:
        with socket.create_connection((host, port), timeout=0.35):
            return False
    except ConnectionRefusedError:
        return True
    except socket.timeout:
        return False
    except OSError as exc:
        if exc.errno in {61, 111, 10061}:
            return True
        return False


def _wait_for_local_mcp_ready(base_url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.time() + float(os.getenv("XHS_MCP_AUTOSTART_TIMEOUT", "15"))
    health_url = _health_url_for_mcp(base_url)
    while time.time() < deadline:
        if process.poll() is not None:
            raise ProviderRequestError("Auto-started external xiaohongshu-mcp bridge exited before becoming ready.")
        if _healthcheck_ok(health_url):
            return
        time.sleep(0.25)
    raise ProviderRequestError(f"Auto-started external xiaohongshu-mcp bridge did not become ready before timeout: {health_url}")


def _health_url_for_mcp(base_url: str) -> str:
    parsed = urlparse(base_url)
    return urlunparse((parsed.scheme, parsed.netloc, "/health", "", "", ""))


def _healthcheck_ok(url: str) -> bool:
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=0.5) as response:
            return 200 <= getattr(response, "status", 200) < 300
    except Exception:
        return False


def _xhs_browser_headless() -> bool:
    configured = os.getenv("XHS_MCP_BROWSER_HEADLESS", "").strip().lower()
    if configured:
        return configured in {"1", "true", "yes", "on"}
    if os.getenv("CI", "").strip().lower() in {"1", "true", "yes", "on"}:
        return True
    return sys.platform.startswith("linux") and not (os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY"))


def _parse_json_or_sse(raw: str) -> Any:
    text = raw.strip()
    if not text:
        return {}
    if text.startswith("{"):
        return json.loads(text)
    data_lines = [line.removeprefix("data:").strip() for line in text.splitlines() if line.startswith("data:")]
    for line in reversed(data_lines):
        if line and line != "[DONE]":
            return json.loads(line)
    return json.loads(text)


def _normalize_mcp_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        parsed = _parse_embedded_content(result.get("content"))
        if parsed is not None:
            return parsed if isinstance(parsed, dict) else {"items": parsed}
        return result
    if isinstance(result, list):
        return {"items": result}
    return {"value": result}


def _parse_embedded_content(content: Any) -> Any:
    if isinstance(content, list):
        texts = [
            str(item.get("text") or "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        texts.extend(str(item) for item in content if isinstance(item, str))
        for text in texts:
            parsed = _try_json(text)
            if parsed is not None:
                return parsed
        if texts:
            return {"message": "\n".join(texts)}
    if isinstance(content, str):
        return _try_json(content) or {"message": content}
    return None


def _try_json(text: str) -> Any:
    value = text.strip()
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def _stringify_mcp_content(result: dict[str, Any]) -> str:
    parsed = _parse_embedded_content(result.get("content"))
    if isinstance(parsed, dict):
        return str(parsed.get("message") or parsed.get("error") or "")
    if parsed:
        return str(parsed)
    return ""


def _cleanup_auto_started_process() -> None:
    process = _AUTO_STARTED_PROCESS
    if process is None or process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=3)
    except Exception:
        pass


atexit.register(_cleanup_auto_started_process)
