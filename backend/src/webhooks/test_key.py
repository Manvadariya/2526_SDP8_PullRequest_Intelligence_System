import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("OPENROUTER_API_KEY")
print(f"Key loaded: {key[:10]}...{key[-5:] if key else 'None'}")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=key,
    default_headers={
        "HTTP-Referer": "https://test.com",
        "X-Title": "Test Script"
    }
)

try:
    print("Sending test request...")
    response = client.chat.completions.create(
        model="qwen/qwen-2.5-coder-32b-instruct",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print("Success!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Error: {e}")
