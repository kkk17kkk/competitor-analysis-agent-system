"""Optional HTTP XHS MCP health/login/search smoke check.

This script never imports ``xhs_mcp``. The service and its Python 3.12
environment are outside the core application process.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def _health_url(mcp_url: str) -> str:
    parsed = urlparse(mcp_url)
    return urlunparse((parsed.scheme, parsed.netloc, "/health", "", "", ""))


def _health(mcp_url: str) -> dict[str, object]:
    request = Request(_health_url(mcp_url), headers={"Accept": "application/json"}, method="GET")
    with urlopen(request, timeout=3) as response:
        body = json.loads(response.read().decode("utf-8"))
    return {"status": "passed", "http_status": getattr(response, "status", 200), "body": body}


def _is_logged_in(value: object) -> bool:
    if isinstance(value, dict):
        for key in ("logged_in", "login", "is_logged_in", "isLogin"):
            if value.get(key) is True:
                return True
        text = json.dumps(value, ensure_ascii=False).casefold()
    else:
        text = str(value).casefold()
    negative = ("not logged", "未登录", "请登录", "login required", "需要登录", "没有权限")
    positive = ("logged in", "已登录", "登录成功", "cookies saved")
    return any(term in text for term in positive) and not any(term in text for term in negative)


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional XHS MCP service smoke check.")
    parser.add_argument("--url", default=os.getenv("XHS_MCP_URL", "http://127.0.0.1:18060/mcp"))
    parser.add_argument("--keyword", default="飞书")
    parser.add_argument("--autostart", action="store_true", help="allow the core client to start the external bridge")
    parser.add_argument("--require-health", action="store_true")
    parser.add_argument("--require-login", action="store_true")
    parser.add_argument("--require-search", action="store_true")
    args = parser.parse_args()
    if not args.autostart:
        os.environ["XHS_MCP_AUTOSTART"] = "false"

    from app.providers.errors import ProviderRequestError
    from app.providers.xhs_mcp import XhsMcpClient

    client = XhsMcpClient(args.url)
    result: dict[str, object] = {"mcp_url": args.url, "transport": "http-jsonrpc"}
    failures = []
    health_error: Exception | None = None
    try:
        result["health"] = _health(args.url)
    except (OSError, URLError, ValueError) as exc:
        health_error = exc
        result["health"] = {"status": "skipped", "reason": str(exc)}
        if args.require_health and not args.autostart:
            failures.append(f"health: {exc}")

    try:
        login = client.check_login_status()
        logged_in = _is_logged_in(login)
        result["login"] = {"status": "passed" if logged_in else "login_required", "logged_in": logged_in}
        if health_error is not None and args.autostart:
            try:
                result["health"] = _health(args.url)
            except (OSError, URLError, ValueError) as exc:
                result["health"] = {"status": "skipped", "reason": str(exc)}
                if args.require_health:
                    failures.append(f"health: {exc}")
        if args.require_login and not logged_in:
            failures.append("login: XHS MCP is reachable but no logged-in account is available")
        if logged_in or args.require_search:
            search = client.search_feeds(args.keyword, filters={"limit": 3})
            result["search"] = {"status": "passed", "result_shape": sorted(search.keys())}
    except ProviderRequestError as exc:
        result["mcp"] = {"status": "skipped", "reason": str(exc)}
        if args.require_health or args.require_login or args.require_search:
            failures.append(f"mcp: {exc}")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
