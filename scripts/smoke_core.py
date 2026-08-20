"""Core-only import smoke; it must not require the optional XHS package."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))


def main() -> int:
    from app.core.graph import compiled_graph
    from app.main import app
    from app.providers.xhs_mcp import XhsMcpClient

    print(
        json.dumps(
            {
                "status": "ok",
                "fastapi_title": app.title,
                "graph_compiled": compiled_graph is not None,
                "xhs_boundary": XhsMcpClient.__module__ == "app.providers.xhs_mcp",
                "xhs_transport": "http-jsonrpc",
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
