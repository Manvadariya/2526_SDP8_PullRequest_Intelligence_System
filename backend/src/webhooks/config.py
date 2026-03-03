import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    A4F_API_KEY = os.getenv("A4F_API_KEY")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")  # Optional for Phase 1 MVP
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    MODEL = os.getenv("MODEL", "meta-llama/llama-3.1-405b-instruct:free")
    
    # LLM Provider Toggle: "openrouter" or "ollama"
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b-instruct-q4_K_M")
    
    # Review Mode: "legacy" (scripted pipeline), "mcp_auto" (autonomous agent), "mcp_guided" (guided agent)
    REVIEW_MODE = os.getenv("REVIEW_MODE", "legacy")
    
    # Defaults
    LINT_TIMEOUT = 30
    STATIC_TIMEOUT = 60
    
    # Model config
    LLM_BASE_URL = "https://api.a4f.co/v1"
    LLM_MODEL = "provider-5/gpt-oss-20b"

    # Docker config
    # USER REQUEST: Disable Docker-based checks ("cloning to docker")
    ENABLE_DOCKER_CHECKS = False 
    DOCKER_IMAGE = os.getenv("DOCKER_CHECK_IMAGE", "pr-checks:latest")
    
    # Infrastructure Config (Defaults for Docker Services)
    # QDRANT at localhost:6333
    # REDIS at localhost:6379
    # POSTGRES at localhost:5432 (database.py handles connection string)
    DOCKER_TIMEOUT = int(os.getenv("DOCKER_TIMEOUT", "300"))
    
    # Persistent Docker Service
    DOCKER_EXECUTABLE_PATH = os.getenv("DOCKER_EXECUTABLE_PATH", "docker")
    DOCKER_CONTAINER_NAME = "sapient-pr-checks-worker"
    # Shared workspace on host (e.g. D:\project\sdp\...\backend\src\webhooks\ai_review_workspace)
    WORKSPACE_MOUNT_PATH = os.path.join(os.getcwd(), "ai_review_workspace")

config = Config()