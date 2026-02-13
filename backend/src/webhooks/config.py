import os
from dotenv import load_dotenv

load_dotenv(override=True)

class Config:
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    A4F_API_KEY = os.getenv("A4F_API_KEY")
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")  # Optional for Phase 1 MVP
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    MODEL = os.getenv("MODEL", "meta-llama/llama-3.1-405b-instruct:free")
    
    # Defaults
    LINT_TIMEOUT = 30
    STATIC_TIMEOUT = 60
    
    # Model config
    LLM_BASE_URL = "https://api.a4f.co/v1"
    LLM_MODEL = "provider-5/gpt-oss-20b"

    # Docker config
    ENABLE_DOCKER_CHECKS = os.getenv("ENABLE_DOCKER_CHECKS", "False").lower() == "true"
    DOCKER_IMAGE = os.getenv("DOCKER_CHECK_IMAGE", "pr-checks:latest")
    DOCKER_TIMEOUT = int(os.getenv("DOCKER_TIMEOUT", "300"))
    
    # Persistent Docker Service
    DOCKER_EXECUTABLE_PATH = os.getenv("DOCKER_EXECUTABLE_PATH", "docker")
    DOCKER_CONTAINER_NAME = "sapient-pr-checks-worker"
    # Shared workspace on host (e.g. D:\project\sdp\...\backend\src\webhooks\ai_review_workspace)
    WORKSPACE_MOUNT_PATH = os.path.join(os.getcwd(), "ai_review_workspace")

config = Config()