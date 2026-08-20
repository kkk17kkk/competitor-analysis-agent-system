# Runtime and dependency setup

EvidenceGraph recommends Python 3.12. The repository keeps the application
runtime independent from the optional Xiaohongshu MCP service:

| Profile | Install | Purpose | CI |
| --- | --- | --- | --- |
| Core | `requirements-core.txt` | FastAPI, LangGraph, providers, SQLite | Required |
| Dev | `requirements-dev.txt` | Core plus pytest and HTTP test client | Required for tests |
| XHS | `requirements-xhs.txt` | Core plus `xiaohongshu-mcp-server==0.1.1` | Optional/manual |

The core process communicates with XHS through HTTP JSON-RPC at
`XHS_MCP_URL`. It does not import `xhs_mcp`. If autostart is enabled, the
core process launches the external bridge with `XHS_MCP_AUTOSTART_PYTHON`;
that executable should belong to the dedicated Python 3.12 XHS environment.

## Core setup

From the repository root:

```bash
python3.12 -m venv .venv-core
. .venv-core/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-core.txt
python scripts/smoke_core.py

# Test-only dependencies are intentionally separate from the runtime profile.
python -m pip install -r requirements-dev.txt
cd backend
python -m pytest tests -q
cd ..
python scripts/eval_workflow.py
python scripts/export_demo_report.py
```

PowerShell equivalent:

```powershell
py -3.12 -m venv .venv-core
.\.venv-core\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-core.txt
python scripts/smoke_core.py
python -m pip install -r requirements-dev.txt
Push-Location backend
python -m pytest tests -q
Pop-Location
python scripts/eval_workflow.py
python scripts/export_demo_report.py
```

The mock benchmark sets mock providers explicitly and needs no credentials.
The report is a local fixture artifact, not live market research.

## Optional live LLM/search smoke

Live checks are opt-in. They skip cleanly when credentials are absent, and
`--require-live` turns a manual smoke into a fail-closed check:

```bash
DEEPSEEK_API_KEY=... \
ANYSEARCH_API_KEY=... \
python scripts/smoke_live_providers.py --require-live
```

For DuckDuckGo, use `--search-provider duckduckgo`; it does not need an API
key, but it does require network access:

```bash
python scripts/smoke_live_providers.py --check search --search-provider duckduckgo --require-live
```

Do not put provider keys in CI logs, reports, frontend code, or committed
files.

## Optional XHS MCP service

Create a separate environment for the service and install the XHS profile
there. This step is not part of core CI:

```bash
python3.12 -m venv .venv-xhs
. .venv-xhs/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-xhs.txt
python -m playwright install chromium
```

Start or smoke the external bridge:

```bash
export XHS_MCP_URL=http://127.0.0.1:18060/mcp
export XHS_MCP_AUTOSTART_PYTHON="$PWD/.venv-xhs/bin/python"
python scripts/smoke_xhs_mcp.py --autostart
```

After completing the QR login in the browser, run the manual acceptance
check:

```bash
python scripts/smoke_xhs_mcp.py --autostart --require-login --require-search --keyword 飞书
```

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv-xhs
.\.venv-xhs\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-xhs.txt
python -m playwright install chromium
$env:XHS_MCP_URL = "http://127.0.0.1:18060/mcp"
$env:XHS_MCP_AUTOSTART_PYTHON = "$PWD\.venv-xhs\Scripts\python.exe"
python scripts/smoke_xhs_mcp.py --autostart --require-login --require-search --keyword 飞书
```

XHS health, login, and search are manual live-integration checks. CI only
tests the HTTP client, parsing, error handling, and the no-XHS core import
boundary; CI does not require an XHS package, browser, credentials, or login.

## Verification boundary

| Check | Expected environment | Status semantics |
| --- | --- | --- |
| Core install/import | Python 3.12, core profile | Required and CI-safe |
| Full pytest | Python 3.12, dev profile | Required and CI-safe |
| Mock benchmark/report | Python 3.12, dev profile | Required and deterministic |
| DeepSeek/search smoke | Credentials or network | Optional manual live check |
| XHS startup/login/search | XHS profile, browser, login | Optional manual live check |
