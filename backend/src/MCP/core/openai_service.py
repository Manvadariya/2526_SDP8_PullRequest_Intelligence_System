# ============================================================
# OpenAIService — Dual Provider Setup (OpenRouter + Ollama)
# ============================================================
# Toggle via .env:  LLM_PROVIDER=openrouter  OR  LLM_PROVIDER=ollama
# Both setups use the OpenAI-compatible Python SDK.
# ============================================================

# --- OPTION A: HuggingFace (Legacy, kept for reference) ---
# import os
# from openai import OpenAI
#
# class OpenAIService:
#     def __init__(self):
#         token = os.environ.get("HF_TOKEN")
#         endpoint = "https://router.huggingface.co/v1"
#         self.model = "Qwen/Qwen2.5-72B-Instruct"
#
#         if not token:
#             raise ValueError("HF_TOKEN environment variable is required.")
#
#         self.client = OpenAI(
#             base_url=endpoint,
#             api_key=token,
#         )
#
#     def chat(self, messages: list, tools: list = None):
#         params = {
#             "messages": messages,
#             "model": self.model,
#             "max_tokens": 1024,
#         }
#         if tools:
#             params["tools"] = tools
#             params["tool_choice"] = "auto"
#
#         response = self.client.chat.completions.create(**params)
#         return response.choices[0].message

# --- OPTION B: OpenRouter Only (Legacy, kept for reference) ---
# import os
# from openai import OpenAI
#
# class OpenAIService:
#     def __init__(self):
#         token = os.environ.get("OPENROUTER_API_KEY")
#         endpoint = "https://openrouter.ai/api/v1"
#         self.model = "nvidia/nemotron-3-nano-30b-a3b:free"
#
#         if not token:
#             raise ValueError("OPENROUTER_API_KEY environment variable is required.")
#
#         self.client = OpenAI(
#             base_url=endpoint,
#             api_key=token,
#             default_headers={
#                 "HTTP-Referer": "http://localhost:8000",
#                 "X-Title": "MCP-CLI-Agent",
#             }
#         )
#
#     def chat(self, messages: list, tools: list = None):
#         params = {
#             "messages": messages,
#             "model": self.model,
#         }
#         if tools:
#             params["tools"] = tools
#             params["tool_choice"] = "auto"
#
#         response = self.client.chat.completions.create(**params)
#         return response.choices[0].message


# --- ACTIVE: Dual Provider (OpenRouter + Ollama) ---
# Controlled by LLM_PROVIDER env var

import os
from openai import OpenAI

class OpenAIService:
    def __init__(self):
        provider = os.environ.get("LLM_PROVIDER", "openrouter")

        if provider == "ollama":
            # --- Ollama (Local) ---
            # Requires: ollama serve + ollama pull qwen2.5-coder:3b-instruct-q4_K_M
            self.client = OpenAI(
                base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
                api_key="ollama",  # Ollama doesn't need a real key
            )
            self.model = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:3b-instruct-q4_K_M")
            self._provider = "ollama"

        else:
            # --- OpenRouter (Cloud, default) ---
            token = os.environ.get("OPENROUTER_API_KEY")
            endpoint = "https://openrouter.ai/api/v1"
            self.model = "nvidia/nemotron-3-nano-30b-a3b:free"

            if not token:
                raise ValueError("OPENROUTER_API_KEY environment variable is required when using OpenRouter.")

            self.client = OpenAI(
                base_url=endpoint,
                api_key=token,
                default_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "MCP-CLI-Agent",
                }
            )
            self._provider = "openrouter"

        print(f"🤖 OpenAIService initialized with provider: {self._provider} | model: {self.model}")

    def chat(self, messages: list, tools: list = None):
        params = {
            "messages": messages,
            "model": self.model,
        }

        if tools:
            params["tools"] = tools
            # tool_choice works reliably on OpenRouter; Ollama may handle it too
            params["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**params)
        return response.choices[0].message