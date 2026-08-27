from app.services.groq_client import client, MODEL_NAME


response = client.chat.completions.create(
    model=MODEL_NAME,
    messages=[
        {
            "role": "user",
            "content": "Reply with exactly: Groq client working"
        }
    ],
    temperature=0,
)


content = response.choices[0].message.content
if "<think>" in content and "</think>" in content:
    content = content.split("</think>")[-1].strip()

print(content)