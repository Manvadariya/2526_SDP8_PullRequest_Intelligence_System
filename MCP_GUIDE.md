# MCP + Ollama Integration Guide

## Quick Start

### 1. Prerequisites

```bash
# Ollama must be running
ollama serve

# Verify model is available
ollama list
# Should show: qwen2.5-coder:3b-instruct-q4_K_M
```

### 2. Configure `.env`

```env
# LLM Provider — "ollama" (local) or "openrouter" (cloud)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=qwen2.5-coder:3b-instruct-q4_K_M

# Review Mode
# "legacy"     → Original scripted pipeline
# "mcp_guided" → AI agent with fixed tool steps (best for 3B model)
# "mcp_auto"   → AI agent decides tool order (best for larger models)
REVIEW_MODE=mcp_guided
```

### 3. Start the Backend

```bash
cd backend/src/webhooks
python main.py
```

You'll see:
```
🚀 Starting PR Review Bot on http://0.0.0.0:8000
   Provider: ollama | Mode: mcp_guided
   Health:   GET  http://localhost:8000/health
   Webhook:  POST http://localhost:8000/webhook/pr
   Jobs:     GET  http://localhost:8000/api/jobs
   Review:   POST http://localhost:8000/api/review
   Chat:     POST http://localhost:8000/api/chat
   Config:   GET  http://localhost:8000/api/config
   Ollama:   GET  http://localhost:8000/api/ollama/status
```

---

## API Endpoints Reference

### GET `/api/config`
Returns current system configuration.

```bash
curl http://localhost:8000/api/config
```

```json
{
  "llm_provider": "ollama",
  "review_mode": "mcp_guided",
  "model": "qwen2.5-coder:3b-instruct-q4_K_M",
  "ollama_base_url": "http://localhost:11434/v1",
  "docker_checks_enabled": false
}
```

---

### GET `/api/ollama/status`
Check if Ollama is running and list available models.

```bash
curl http://localhost:8000/api/ollama/status
```

```json
{
  "status": "running",
  "models": [
    {"name": "qwen2.5-coder:3b-instruct-q4_K_M", "size": 2097152000}
  ],
  "active_model": "qwen2.5-coder:3b-instruct-q4_K_M"
}
```

---

### GET `/api/jobs`
List all review jobs (most recent first).

```bash
curl http://localhost:8000/api/jobs
```

```json
[
  {
    "id": 1,
    "repo_full_name": "owner/repo",
    "pr_number": 42,
    "commit_sha": "abc123",
    "status": "success",
    "created_at": "2026-03-01T06:00:00"
  }
]
```

---

### GET `/api/jobs/{id}`
Get a specific job with its review results.

```bash
curl http://localhost:8000/api/jobs/1
```

```json
{
  "job": { "id": 1, "status": "success", ... },
  "results": [
    {
      "agent_name": "mcp_reviewer",
      "output_json": "{\"mode\": \"guided\", \"verdict\": \"APPROVE\", \"tool_calls_made\": 8}"
    }
  ]
}
```

---

### POST `/api/review`
Manually trigger a PR review (without GitHub webhook).

```bash
curl -X POST http://localhost:8000/api/review \
  -H "Content-Type: application/json" \
  -d '{"repo": "owner/repo", "pr_number": 42}'
```

```json
{
  "status": "Review queued",
  "job_id": 5,
  "review_mode": "mcp_guided",
  "llm_provider": "ollama"
}
```

---

### POST `/api/chat`
Send a message to the AI agent (stateless chat).

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain what async/await does in Python"}'
```

```json
{
  "response": "async/await in Python is used for...",
  "model": "qwen2.5-coder:3b-instruct-q4_K_M",
  "provider": "ollama"
}
```

With context:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Is this code safe?",
    "context": "def login(user, pwd):\n    query = f\"SELECT * FROM users WHERE name={user}\""
  }'
```

---

## Frontend Integration (React)

### Connecting from React

```javascript
const API_BASE = 'http://localhost:8000';

// Fetch system config
const config = await fetch(`${API_BASE}/api/config`).then(r => r.json());

// List all jobs
const jobs = await fetch(`${API_BASE}/api/jobs`).then(r => r.json());

// Get specific job with results
const jobDetail = await fetch(`${API_BASE}/api/jobs/${jobId}`).then(r => r.json());

// Trigger a manual review
const review = await fetch(`${API_BASE}/api/review`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ repo: 'owner/repo', pr_number: 42 })
}).then(r => r.json());

// Chat with AI
const chat = await fetch(`${API_BASE}/api/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Review this code...', context: codeSnippet })
}).then(r => r.json());

// Check Ollama status
const ollama = await fetch(`${API_BASE}/api/ollama/status`).then(r => r.json());
```

---

## Architecture Overview

```
                    Frontend (React :5173)
                         │
                    ┌────┴────┐
                    │ REST API │ ← /api/* endpoints
                    │ :8000   │
                    └────┬────┘
                         │
            ┌────────────┼────────────┐
            │            │            │
       ┌────┴───┐  ┌────┴───┐  ┌────┴────┐
       │ Legacy │  │ Guided │  │  Auto   │
       │Pipeline│  │ Agent  │  │  Agent  │
       └────┬───┘  └────┬───┘  └────┬────┘
            │            │            │
            │       ┌────┴────────────┘
            │       │
            │  ┌────┴──────────────┐
            │  │ MCP Server (9 tools) │
            │  └────┬──────────────┘
            │       │
       ┌────┴───────┴────┐
       │   Ollama / OR   │  ← LLM Provider
       └─────────────────┘
```

---

## Switching Modes

| Mode | In `.env` | Best For |
|------|-----------|----------|
| Legacy Pipeline | `REVIEW_MODE=legacy` | Production with OpenRouter |
| Guided Agent | `REVIEW_MODE=mcp_guided` | Local Ollama (3B model) |
| Autonomous Agent | `REVIEW_MODE=mcp_auto` | Large models (32B+) |

Switch providers:
```env
# Use local Ollama
LLM_PROVIDER=ollama

# Use OpenRouter (cloud)
LLM_PROVIDER=openrouter
```

> **Note**: Changing `.env` requires a server restart.

---

## MCP Tools Available

The MCP agent has access to 9 tools:

| Tool | Description |
|------|-------------|
| `get_pr_diff` | Fetch PR diff from GitHub |
| `get_pr_metadata` | Get PR title, author, description |
| `read_file` | Read a file from the cloned repo |
| `list_changed_files` | Parse diff into file list |
| `run_linter` | Run flake8/eslint/checkstyle |
| `scan_security` | Run Bandit security scan |
| `get_custom_rules` | Load .pr-reviewer.yml rules |
| `post_review` | Post review to GitHub PR |
| `set_commit_status` | Set GitHub commit status |
