from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)

response = client.chat.completions.create(
    model="qwen/qwen3.8-27b",
    messages=[
        {
            "role": "system",
            "content": "You are an AI assessment assistant."
        },
        {
            "role": "user",
            "content": "Reply exactly: Groq Qwen model is working."
        }
    ],
    temperature=0
)

content = response.choices[0].message.content
if "<think>" in content and "</think>" in content:
    content = content.split("</think>")[-1].strip()

print(content)