from app.services.gemini_client import client

MODEL = "gemini-3.6-flash"

print(f"Testing model: {MODEL}")

response = client.models.generate_content(
    model=MODEL,
    contents="Reply with exactly: Gemini test successful"
)

print("Response:")
print(response.text)