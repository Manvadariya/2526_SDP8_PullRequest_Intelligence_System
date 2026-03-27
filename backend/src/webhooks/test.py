from groq import Groq

# Add your Groq API key
client = Groq(
    api_key="..."
)

response = client.chat.completions.create(
    model="openai/gpt-oss-120b",   # free Groq model
    messages=[
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Explain ensemble learning in simple terms."}
    ],
    temperature=0.7,
    max_tokens=512
)

print(response.choices[0].message.content)