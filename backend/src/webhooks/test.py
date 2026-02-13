import requests
import json

response = requests.post(
  url="https://openrouter.ai/api/v1/chat/completions",
  headers={
    "Authorization": "Bearer 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",
  },
  data=json.dumps({
    "model": "stepfun/step-3.5-flash:free",
    "messages": [
      {
        "role": "user",
        "content": "What is the meaning of life?"
      }
    ]
  }),
  timeout=30
)

print(response.status_code)
print(response.text)
