# import os
# from openai import OpenAI

# class OpenAIService:
#     def __init__(self):
#         token = os.environ.get("HF_TOKEN")
#         endpoint = "https://router.huggingface.co/v1"
        
#         # CHANGED: Use Qwen 2.5 72B (Supports tools/function calling much better)
#         #self.model = "Qwen/Qwen2.5-72B-Instruct" 
#         self.model = "Qwen/Qwen3-VL-8B-Instruct:novita" 

#         if not token:
#             raise ValueError("HF_TOKEN environment variable is required.")

#         self.client = OpenAI(
#             base_url=endpoint,
#             api_key=token,
#         )

#     def chat(self, messages: list, tools: list = None):
#         params = {
#             "messages": messages,
#             "model": self.model,
#             "max_tokens": 1024, 
#         }

#         # Only add tools if the model supports them (Qwen does)
#         if tools:
#             params["tools"] = tools
#             params["tool_choice"] = "auto"

#         response = self.client.chat.completions.create(**params)
#         return response.choices[0].message


import os
from openai import OpenAI

class OpenAIService:
    def __init__(self):
        # 1. Get OpenRouter Key
        token = os.environ.get("OPENROUTER_API_KEY")
        
        # 2. OpenRouter Endpoint
        endpoint = "https://openrouter.ai/api/v1"
        
        # 3. Choose a Model
        # "google/gemini-2.0-flash-exp:free" is excellent for tools and currently free.
        # You can also try "meta-llama/llama-3.1-70b-instruct:free"
        self.model = "nvidia/nemotron-3-nano-30b-a3b:free"

        if not token:
            raise ValueError("OPENROUTER_API_KEY environment variable is required.")

        # 4. Initialize Client with OpenRouter headers
        self.client = OpenAI(
            base_url=endpoint,
            api_key=token,
            default_headers={
                "HTTP-Referer": "http://localhost:8000",  # Optional: Your site URL
                "X-Title": "MCP-CLI-Agent",              # Optional: App name
            }
        )

    def chat(self, messages: list, tools: list = None):
        params = {
            "messages": messages,
            "model": self.model,
        }

        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        # OpenRouter uses standard OpenAI-compatible completions
        response = self.client.chat.completions.create(**params)
        return response.choices[0].message