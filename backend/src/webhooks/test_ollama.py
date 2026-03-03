"""Quick test script to verify Ollama integration via LLMService."""
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

from config import config
from core.llm import LLMService

print("=" * 50)
print("Testing Ollama Integration")
print("=" * 50)
print(f"Provider: {config.LLM_PROVIDER}")
print(f"Ollama URL: {config.OLLAMA_BASE_URL}")
print(f"Ollama Model: {config.OLLAMA_MODEL}")
print()

# Test 1: Basic LLMService init
print("[Test 1] Initializing LLMService...")
llm = LLMService()
print(f"   OK - Provider: {llm._provider} | Model: {llm.model}")
print()

# Test 2: Simple chat completion
print("[Test 2] Simple chat completion...")
try:
    response = llm.client.chat.completions.create(
        model=llm.model,
        messages=[{"role": "user", "content": "What is a pull request? Answer in 1 sentence."}]
    )
    print(f"   OK - Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"   FAIL - Error: {e}")
print()

# Test 3: generate_summary (the main function used by reviewers)
print("[Test 3] generate_summary with sample diff...")
sample_diff = """
diff --git a/app.py b/app.py
--- a/app.py
+++ b/app.py
@@ -1,5 +1,7 @@
+import logging
 from flask import Flask
 
 app = Flask(__name__)
+logging.basicConfig(level=logging.DEBUG)
 
 @app.route('/')
"""
result = llm.generate_summary(sample_diff, "Add logging to Flask app")
print(f"   Result: {result}")
print()

print("=" * 50)
print("All tests completed!")
print("=" * 50)
