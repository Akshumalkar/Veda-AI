import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured")

client = Groq(
    api_key=GROQ_API_KEY
)

# Use a vision-capable model with better JSON reliability.
MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "meta-llama/llama-4-scout-17b-16e-instruct",
)

print(
    f"Groq client initialized. Model: {MODEL_NAME}"
)
