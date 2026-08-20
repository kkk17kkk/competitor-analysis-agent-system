# EvidenceGraph
### 证据优先、可追溯、可复核的竞品分析 Agent 工作台

EvidenceGraph 面向产品经理、增长团队和竞品研究场景。用户输入目标产品、竞品和分析重点后，系统会自动完成公开信息采集、证据抽取、结论生成、复核打回、舆情整理和结构化报告输出。


![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=111)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Workflow-5F7DF2?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-111111?style=flat-square)

[🚀 在线体验 Demo](https://competitor-analysis-agent-system-two.vercel.app) · [本地运行](http://localhost:5173)

> 真实分析请在本地或私有部署中配置 key 和 Provider。
---

## ✨ 项目亮点

| 亮点 | 说明 |
| --- | --- |
| 🔎 证据优先 | Claim 必须绑定 Evidence；无支撑结论会被标记、降级或移出最终报告。 |
| 🧭 可观测 Trace | 记录节点、Agent、Provider、Prompt 摘要、token、latency、request id 和运行事件。 |
| 🔁 复核闭环 | Critic 生成 Review Ticket，Research 可按缺口补采，Reviewer 再做证据门禁。 |
| 🧩 Skill Layer | 支持导入 GitHub `SKILL.md`，把竞品分析、用户画像、定价、SWOT 方法论注入 Prompt。 |
| 📣 舆情采集 | 通过外部 `xiaohongshu-mcp` HTTP MCP 服务接入小红书搜索、笔记与评论样本；它是可选集成，不属于 core 安装。 |
| 🧪 可复核交付 | 前端提供证据、结论、报告、trace、工单与可信度摘要，方便评审或产品团队逐项检查。 |

---

## 🖥️ Demo 展示

打开 [🚀 在线 Demo](https://competitor-analysis-agent-system-two.vercel.app)，点击页面左侧 **一键运行 Demo**，即可生成 AI 编程工具竞品分析报告；本地开发时也可以使用 `http://localhost:5173`。

Demo 场景：

| 目标产品 | 竞品 | 输出内容 |
| --- | --- | --- |
| Cursor | GitHub Copilot、Windsurf、TRAE | 检索计划、来源、证据、结构化结论、复核工单、可信度摘要、最终报告 |


---

## 🧠 架构与 Agent

EvidenceGraph 不是把 Agent 简单串成流水线，而是围绕“证据是否足够支撑结论”组织运行时。

```text
┌──────────────────────────────────────────────────────────────┐
│ React 工作台                                                   │
│ 输入任务 · Demo 运行 · 报告浏览 · 证据复核 · Agent Trace        │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│ FastAPI API                                                    │
│ Task / Stream / Report / Evidence / Review Ticket / Settings  │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│ LangGraph Agent Workflow                                      │
│ Planner → Research → Evidence → Analyst → Critic → Reviewer   │
│           ↑                         │              │           │
│           └──── Review Ticket 补采 ─┴── Trust Summary → Writer │
└───────────────────────────────┬──────────────────────────────┘
                                │
┌───────────────────────────────▼──────────────────────────────┐
│ Skill & Provider Layer                                        │
│ AnySearch / DuckDuckGo · DeepSeek · optional XHS HTTP MCP    │
│ PM Skills · Prompt Composer · SQLite Store                    │
└──────────────────────────────────────────────────────────────┘
```

### Agent / 节点职责

| 模块 | 职责 |
| --- | --- |
| PlannerAgent | 将用户输入整理为结构化分析 brief。 |
| ResearchAgent | 生成检索计划，调用搜索 Provider，并处理复核补采。 |
| SocialListeningAgent | 整理小红书等社媒舆情样本，纳入证据池。 |
| SourceNormalizer | 识别官方、第三方、社媒来源，过滤低相关内容。 |
| EvidenceExtractor | 从来源中抽取 Evidence，生成可引用证据记录。 |
| InteractionAgent | 整理交互路径和产品体验证据。 |
| AnalystAgent | 基于 Evidence 输出 Feature、Pricing、Persona、SWOT 等 Claim。 |
| CriticAgent | 查找证据缺口、矛盾和高风险推断，生成 Review Ticket。 |
| EvidenceReviewer | 执行证据门禁，降级 unsupported / uncertain 结论。 |
| TrustSummary | 计算证据绑定率、官方来源占比、未解决工单和 Provider 模式。 |
| WriterAgent | 生成结构化 Markdown 报告。 |

---

## 🛠️ 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | React 19、Vite、lucide-react、Server-Sent Events |
| 后端 | FastAPI、Pydantic v2、Uvicorn、SQLite |
| Agent Runtime | LangGraph StateGraph、自研 Agent 节点、Review Ticket 闭环 |
| 搜索 | AnySearch、DuckDuckGo |
| LLM | DeepSeek OpenAI-compatible API |
| 舆情 | 可选的外部 xiaohongshu-mcp-server（HTTP MCP 边界） |
| 测试与交付 | pytest、Playwright、Docker Compose |

---

## 🚀 快速开始

### 1. 创建 Python 3.12 环境并安装

Python 3.12 是推荐项目运行时。Core 安装不会拉取 XHS 包；测试依赖单独放在 dev profile。

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/smoke_core.py
```

依赖 profile：

| Profile | 文件 | 用途 |
| --- | --- | --- |
| Core | `requirements-core.txt` | FastAPI、LangGraph、Provider、SQLite runtime |
| Dev | `requirements-dev.txt` | Core + pytest/httpx，用于测试和本地 benchmark |
| XHS | `requirements-xhs.txt` | 独立 Python 3.12 XHS MCP 服务环境 |

完整安装和 smoke 说明见 [`docs/runtime-setup.md`](docs/runtime-setup.md)。

### 2. 启动后端

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

健康检查：

```bash
curl http://localhost:8000/health
```

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开：

```text
http://localhost:5173
```

---

## 🔐 Provider 配置

推荐在根目录 `.env` 或后端设置页配置 Provider。API Key 只保存在本地或服务端环境，不进入前端代码。

```env
DATABASE_URL=sqlite:///./data/app.db
PUBLIC_DEMO_MODE=false

SEARCH_PROVIDER=anysearch
ANYSEARCH_API_KEY=your_anysearch_key
ANYSEARCH_BASE_URL=https://api.anysearch.com/v1/search
ANYSEARCH_MAX_RESULTS=15

LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_BASE_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-chat
LIGHTWEIGHT_LLM_PROVIDER=deepseek

ALLOW_PROVIDER_FALLBACK=false
ALLOW_EMPTY_SEARCH_FALLBACK=false
```

DeepSeek 用作当前可配置的真实 LLM Provider；AnySearch / DuckDuckGo 用作搜索 Provider。XHS 由独立的 `xiaohongshu-mcp-server` Python 3.12 环境通过 HTTP MCP 提供服务。

```env
XHS_MCP_URL=http://localhost:18060/mcp
XHS_MCP_AUTOSTART=false
# 仅在本机启用外部 bridge autostart 时设置：
# XHS_MCP_AUTOSTART_PYTHON=/path/to/.venv-xhs/bin/python
```

---

## 📚 API 文档

启动后端后访问：

```text
http://localhost:8000/docs
```

核心接口：

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `GET` | `/api/v1/provider-status` | Provider 就绪状态 |
| `GET` / `PUT` | `/api/v1/settings` | 读取 / 保存 Provider 设置 |
| `GET` | `/api/tasks` | 历史任务列表 |
| `POST` | `/api/v1/tasks` | 创建分析任务 |
| `POST` | `/api/tasks/{task_id}/run` | 运行工作流 |
| `GET` | `/api/v1/tasks/{task_id}/run/stream` | SSE 运行流 |
| `GET` | `/api/tasks/{task_id}/trace` | Agent Trace |
| `GET` | `/api/tasks/{task_id}/manifest` | Run Manifest / reproducibility metadata |
| `GET` | `/api/tasks/{task_id}/evidence` | Evidence 列表 |
| `GET` | `/api/tasks/{task_id}/claims` | Claim 列表 |
| `GET` | `/api/v1/tasks/{task_id}/review-tickets` | 复核工单 |
| `GET` | `/api/v1/tasks/{task_id}/report` | 最终报告 |
| `POST` | `/api/v1/review-tickets/{ticket_id}/rerun` | 按工单补采 |
| `GET` | `/api/v1/skills/catalog` | Skill Catalog |
| `POST` | `/api/v1/skills/import-github` | 导入 GitHub Skill |
| `POST` | `/api/v1/social/xhs/login-qrcode` | 小红书扫码登录 |

---

## 📁 项目结构

```text
competitor-analysis-agent-system/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # LangGraph graph and Agent nodes
│   │   │   ├── routing.py       # deterministic Review-Ticket routing
│   │   │   └── runtime/         # tracing, ticket lifecycle, run manifest
│   │   ├── fixtures/     # Demo scenario data
│   │   ├── models/       # Pydantic schemas
│   │   ├── providers/    # Search / LLM / XHS providers
│   │   ├── skills/       # PM Skill registry and prompt composer
│   │   ├── storage/      # SQLite persistence
│   │   └── templates/    # Report templates
│   └── tests/
├── frontend/
│   └── src/
│       ├── api/          # API client and SSE stream
│       ├── main.jsx      # React workspace
│       └── styles/       # Product UI styles
├── docs/
│   └── runtime-setup.md   # Core/dev/XHS setup and smoke boundaries
├── requirements-core.txt
├── requirements-dev.txt
├── requirements-xhs.txt
└── docker-compose.yml
```

### Example Report

The portfolio-oriented demo report is generated from the same deterministic mock workflow:

- [Markdown report](examples/demo-report.md)
- [Standalone HTML report](examples/demo-report.html)

Regenerate both artifacts with:

```bash
python scripts/export_demo_report.py
```

The backend also includes a small regression comparison between `single_pass` and `adaptive_review`:

```bash
python scripts/eval_workflow.py
```

Results are written to `eval/results/latest.json` and `eval/results/latest.md`. Live providers are optional; mock mode is the CI-safe default for this harness.

Optional smoke checks:

```bash
python scripts/smoke_live_providers.py
python scripts/smoke_xhs_mcp.py
```

These commands skip when live credentials or XHS login are unavailable. Use `--require-live`, `--require-login`, or `--require-search` only for a manually configured live environment. XHS startup/login/search is not a CI requirement.

---

## 🧪 测试

```bash
cd frontend
npm run build
```

```bash
cd backend
python -m pytest tests -q
```

Core import and optional live checks:

```bash
python scripts/smoke_core.py
python scripts/smoke_live_providers.py --require-live
python scripts/smoke_xhs_mcp.py --autostart --require-login --require-search
```

The first two workflow checks are CI-safe when run without the optional flags. The live provider and XHS commands are manual verification paths and require their respective credentials, network access, browser, and (for XHS) login session.

