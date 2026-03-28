import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    # ─── SCM Tokens ─────────────────────────────────────────────
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    A4F_API_KEY = os.getenv("A4F_API_KEY")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
    
    # ─── LLM Providers ──────────────────────────────────────────
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    MODEL = os.getenv("MODEL", "meta-llama/llama-3.1-405b-instruct:free")
    
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    
    # Groq (Primary LLM)
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    # ─── Timeouts and Limits ────────────────────────────────────
    LINT_TIMEOUT = 30
    STATIC_TIMEOUT = 60
    
    # Model config (legacy)
    LLM_BASE_URL = "https://api.a4f.co/v1"
    LLM_MODEL = "provider-5/gpt-oss-20b"

    # ─── Docker ─────────────────────────────────────────────────
    ENABLE_DOCKER_CHECKS = os.getenv("ENABLE_DOCKER_CHECKS", "false").lower() == "true"
    DOCKER_IMAGE = os.getenv("DOCKER_CHECK_IMAGE", "pr-checks:latest")
    DOCKER_TIMEOUT = int(os.getenv("DOCKER_TIMEOUT", "300"))
    DOCKER_EXECUTABLE_PATH = os.getenv("DOCKER_EXECUTABLE_PATH", "docker")
    DOCKER_CONTAINER_NAME = "sapient-pr-checks-worker"
    WORKSPACE_MOUNT_PATH = os.path.join(os.getcwd(), "ai_review_workspace")
    
    # ─── Infrastructure ─────────────────────────────────────────
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    
    # ─── Worker Configuration ───────────────────────────────────
    WORKER_CONCURRENCY_FETCH = int(os.getenv("WORKER_CONCURRENCY_FETCH", "4"))
    WORKER_CONCURRENCY_ANALYZE = int(os.getenv("WORKER_CONCURRENCY_ANALYZE", "2"))
    WORKER_CONCURRENCY_REVIEW = int(os.getenv("WORKER_CONCURRENCY_REVIEW", "3"))
    WORKER_CONCURRENCY_PUBLISH = int(os.getenv("WORKER_CONCURRENCY_PUBLISH", "6"))
    
    # Per-repo concurrency cap
    MAX_CONCURRENT_PER_REPO = int(os.getenv("MAX_CONCURRENT_PER_REPO", "2"))
    
    # ─── Rate Limiting ──────────────────────────────────────────
    LLM_RPM_LIMIT = int(os.getenv("LLM_RPM_LIMIT", "30"))  # requests per minute
    GITHUB_API_BUFFER = int(os.getenv("GITHUB_API_BUFFER", "100"))  # remaining calls before backoff
    
    # ─── Environment ────────────────────────────────────────────
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")
    PRODUCTION = os.getenv("PRODUCTION", "").lower() in ("true", "1", "yes")
    DEV_MODE = os.getenv("DEV_MODE", "").lower() in ("true", "1", "yes")

config = Config()