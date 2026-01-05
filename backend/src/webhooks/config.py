import os
from dotenv import load_dotenv

load_dotenv()

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

config = Config()