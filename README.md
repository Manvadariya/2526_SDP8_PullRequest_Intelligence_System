# AgenticPR - Pull Request Intelligence System 🤖

AgenticPR is an AI-powered pull request intelligence platform that ingests PR events, runs staged analysis and review agents, and delivers actionable findings through a web dashboard and SCM comments.

## What This Project Contains ✨

- 🌐 Frontend web app built with React + Vite + Tailwind.
- ⚙️ Backend API built with FastAPI.
- 🔄 Async worker pipeline for queued PR processing (fetch -> analyze -> review -> publish).
- 🔐 Integrations for GitHub and Bitbucket OAuth.
- 🗄️ PostgreSQL for persistent data.
- 🚀 Redis for queueing and worker coordination.
- 🧠 Qdrant for vector-based retrieval context.
- 🐳 Dockerized local and production-style orchestration.

## Current Architecture 🏗️

### Frontend (AgenticPR) 🎨

- React 19, Vite 7, Tailwind 4.
- React Router for public and protected routes.
- TanStack React Query for API caching.
- Markdown and code rendering support for review output.

Main user flows in the UI include:

- Landing/authentication.
- Repository activation and management.
- PR/job history and detailed review pages.
- Repo-level views: overview, issues, metrics, reports, settings.
- Scan detail and PR visualization pages.

### Backend (backend/src/webhooks) 🔧

- FastAPI app with CORS and modular routers.
- Auth router for GitHub/Bitbucket OAuth + JWT user sessions.
- API router for jobs, reviews, chat, repository stats, repo activation, and SCM proxy endpoints.
- Webhook ingestion endpoints with signature verification and deduplication/supersede logic.

### Worker System ⚡

The queue-driven pipeline is split into stages:

1. fetch
2. analyze
3. review
4. publish

Workers read from Redis queues and update job status through lifecycle states such as queued, fetching, analyzing, reviewing, publishing, completed, failed, and superseded.

### Data and Services 🧱

- PostgreSQL: jobs, users, agent results, review lifecycle entities.
- Redis: queue/stream transport and concurrency control.
- Qdrant: semantic context storage and retrieval for review context enrichment.

## Tech Stack 🛠️

### Frontend 📱

- react
- react-router-dom
- @tanstack/react-query
- tailwindcss
- lucide-react
- react-markdown + rehype/remark tooling

### Backend 🧩

- fastapi
- uvicorn
- sqlmodel + sqlalchemy async
- asyncpg + psycopg2-binary
- redis
- qdrant-client
- tree-sitter + tree-sitter-languages
- httpx
- openai, groq, google-genai
- python-dotenv

### Analysis and Checks ✅

- flake8 (+ flake8-json)
- bandit
- eslint
- cppcheck (in checks container)

## Repository Structure 📁

```text
2526_SDP8_PullRequest_Intelligence_System/
	AgenticPR/                 # React frontend
	backend/                   # FastAPI, workers, checks
		src/webhooks/            # API app, auth, models, workers, tests
		src/MCP/                 # MCP-related logic
	docker-compose.yml         # Full local stack
	docker-compose.prod.yml    # Production-style stack
	DEPLOY_TO_RENDER.md        # Render deployment runbook
```

## Key Backend Endpoints 🔌

### Core ❤️

- GET /health
- GET /webhook/pr
- POST /webhook/pr

### Auth 🔐

- GET /auth/github
- POST /auth/callback
- GET /auth/bitbucket
- POST /auth/bitbucket/callback
- GET /auth/me

### API (prefix /api) 📡

- GET /api/jobs
- GET /api/jobs/{job_id}
- GET /api/config
- POST /api/review
- POST /api/webhook
- POST /api/chat
- GET /api/ollama/status
- GET /api/repos/{owner}/{repo}/stats
- GET /api/activated-repos
- POST /api/activated-repos
- DELETE /api/activated-repos/{repo_full_name}
- GET /api/user/repos
- GET /api/user/repos/{owner}/{repo}/pulls
- GET /api/user/repos/{owner}/{repo}/pulls/{number}
- GET /api/user/repos/{owner}/{repo}/pulls/{number}/comments
- GET /api/repos/{owner}/{repo}/pr/{number}/review-data

## Running The Project 🚀

### Prerequisites 📋

- Docker and Docker Compose (recommended path).
- Node.js 20+ and npm (for frontend local mode).
- Python 3.11+ and pip (for backend local mode).
- PostgreSQL, Redis, and Qdrant available if running without compose.

### Option 1: Full Stack with Docker (Recommended) 🐳

From repository root:

```bash
docker-compose up --build
```

This starts:

- frontend
- api
- workers
- postgres
- redis
- qdrant

Default ports:

- Frontend: 5173
- API: 8000
- Postgres: 5432
- Redis: 6379
- Qdrant: 6333

### Option 2: Local Development (Without Full Compose) 💻

### 1) Frontend

```bash
cd AgenticPR
npm install
npm run dev
```

### 2) Backend API

```bash
cd backend/src/webhooks
pip install -r ../../requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Workers (separate terminal)

```bash
cd backend/src/webhooks
python run_workers.py
```

Run specific stages only:

```bash
python run_workers.py --workers fetch,review
```

## Environment Configuration ⚙️

Use environment variables for provider credentials, OAuth, and infrastructure URLs.

Important variables include:

- LLM_PROVIDER
- OPENROUTER_API_KEY
- GROQ_API_KEY
- GEMINI_API_KEY
- GITHUB_TOKEN
- GITHUB_CLIENT_ID
- GITHUB_CLIENT_SECRET
- WEBHOOK_SECRET
- BITBUCKET_CLIENT_ID
- BITBUCKET_CLIENT_SECRET
- JWT_SECRET
- DATABASE_URL
- REDIS_URL
- QDRANT_URL
- FRONTEND_URL
- ALLOW_ORIGINS

Reference template:

- backend/src/webhooks/.env.example

## LLM Provider Support 🧠

Current backend configuration supports:

- Groq
- Gemini (Google)
- OpenRouter
- Ollama (local)

Provider and model can be selected through environment configuration.

## Testing and Validation 🧪

Backend contains multiple integration and system tests under backend/src/webhooks, including:

- test_end_to_end.py
- test_full_review.py
- test_incremental.py
- test_inline_review.py
- test_vector_store.py
- test_mcp_server.py
- test_infra.py

There is also an isolated checks container flow:

- backend/run_checks.sh
- backend/Dockerfile.checks

## Deployment 🌍

Deployment guides and assets are included for:

- Render deployment runbook (DEPLOY_TO_RENDER.md)
- Docker compose production stack (docker-compose.prod.yml)
- DockerHub script (deploy-to-dockerhub.ps1)

## Development History 📚

### Lab 1 - December 8, 2025 🧪
-  Project initialization with React + Vite
-  Frontend scaffolding with Tailwind CSS
-  Created main sections (Hero, Planning, Issue Tracking)
-  Built responsive navbar and footer

### Lab 2 - December 15, 2025 🧪
-  GitHub API integration
-  PR diff fetching and parsing
-  Backend webhook setup 
-  Initial PR analysis logic

### Lab 3 - December 22, 2025 🧪
-  GitHub Official MCP implementation
-  Multi-LLM provider support 
-  Enhanced analysis agents 
-  Dashboard improvements

### Lab 4 - January 5, 2026 🧪
- Update LLMService and Orchestrator for improved error handling and cleanup processes.


### LAB 5 - January 12, 2026 🧪
- Added Better PR Summarization with better formatting and context.
- Improved Issue Detection with more comprehensive checks and balances.

### LAB 6 - January 19, 2026 🧪
- Enhance ReviewerAgent with robust JSON prompt 
- Added multi-file review capabilities


### LAB 7 - February 13, 2026 🧪
- Implemented Inline Commenting System for more contextual feedback

### LAB 8 - February 16, 2026 🧪
- updated frontend landing page, implemented RAG and context awareness to llm, and updated more sofasticated code review blocks

### Lab 9 - March 2, 2026 🧪
- Implement GitHub & Bitbucket OAuth 2.0 and connect full pipeline
- Add OAuth 2.0 flow for GitHub and Bitbucket
- Connect frontend and backend APIs
- Set up local AI integration
- Add MCP for complete pipeline support

### Lab 10 - March 9, 2026 🧪
- Implemented logging for the ReviewPlanner and VectorStore processes, including error handling and connection status.
- Done Other minor bug fixes and improvements to the review process.


---