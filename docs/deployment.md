# 部署说明

## 本地开发

后端：

推荐直接使用本机 `dev` conda 环境；它已经包含后端依赖，避免重新创建 `.venv` 时因为 PyPI SSL/网络失败卡住。

```bash
cd backend
conda activate dev
uvicorn app.main:app --reload --port 8000
```

如果新终端已经自动进入 `(dev)`，可以省略 `conda activate dev`。依赖检查：

```bash
python -c "import fastapi, langgraph; print('backend deps ok')"
```

前端：

```bash
cd frontend
npm install
npm run dev
```

打开：

```text
http://localhost:5173
```

健康检查：

```bash
curl http://localhost:8000/health
```

## Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

服务地址：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`

## API Key 与密钥文件

演示模式可以使用 mock providers，不需要真实 API Key。真实分析模式需要配置搜索与 LLM Provider。

后续接入真实 provider 时，在根目录 `.env` 中配置：

```env
USE_MOCK_SEARCH=false
USE_MOCK_LLM=false
SEARCH_PROVIDER=duckduckgo
LLM_PROVIDER=deepseek
ANYSEARCH_API_KEY=
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com/chat/completions
DEEPSEEK_MODEL=deepseek-chat
SEED_API_KEY=
SEED_BASE_URL=
SEED_MODEL=
DATABASE_URL=sqlite:///./data/app.db
```

不要把 AnySearch 或 Seed API Key 放到前端。前端只需要：

```env
VITE_API_BASE=http://localhost:8000
```

已忽略的本地密钥/工具状态文件包括：

- `.env`
- `.env.local`
- `backend/.env`
- `frontend/.env.local`
- `*.key`
- `*.pem`
- `*.secret`
- `secrets/`
- `.agents/`
- `.codex/`

## Provider 状态

当前已实现：

- `MockSearchProvider` / `MockLLMProvider`：用于一键 Demo 的预跑场景。
- `AnySearchProvider`：读取 `ANYSEARCH_API_KEY`、`ANYSEARCH_BASE_URL` 和 `ANYSEARCH_MAX_RESULTS`。
- `DuckDuckGoSearchProvider`：可作为无搜索 API Key 的公开网页搜索路径。
- `DeepSeekLLMProvider`：OpenAI-compatible Chat Completions。
- `SeedLLMProvider`：可作为主 LLM 或轻量 LLM Provider。
- Provider factory：根据 `.env` 或前端设置页保存的配置选择 Demo / live provider。

本地 Demo 可在前端点击“一键运行 Demo”直接体验。需要使用真实 Provider 时，请配置搜索和 LLM Key，并关闭 `USE_MOCK_SEARCH`、`USE_MOCK_LLM`、`ALLOW_PROVIDER_FALLBACK` 和 `ALLOW_EMPTY_SEARCH_FALLBACK`。

## 服务器部署

Linux 服务器已安装 Docker 时：

```bash
git clone <repo-url>
cd competitor-analysis-agent-system
cp .env.example .env
docker compose up -d --build
```

如需公网访问，建议在前面放 Nginx 或 Caddy：

- 前端容器端口：`5173`
- 后端容器端口：`8000`

生产部署仍需额外补充 HTTPS、认证、日志、监控和 secret 管理。首个 demo 未包含生产加固。
