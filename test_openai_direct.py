#!/usr/bin/env python3
"""
Test OpenAI API directly to verify it's working
"""
import openai

# Get the OpenAI key from backend .env
with open("apps/backend/.env") as f:
    for line in f:
        if line.startswith("OPENAI_API_KEY="):
            api_key = line.strip().split("=", 1)[1]
            break

openai.api_key = api_key

print(f"🔑 Using API key: {api_key[:20]}...")
print("📡 Testing OpenAI API connection...")

try:
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello World' and nothing else."},
        ],
        max_tokens=10,
        timeout=10,
    )

    print("\n✅ SUCCESS!")
    print(f"Response: {response.choices[0].message.content}")
    print(f"Model: {response.model}")
    print(f"Tokens: {response.usage.total_tokens}")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback

    traceback.print_exc()
