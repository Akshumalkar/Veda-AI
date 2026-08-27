import os

from dotenv import load_dotenv
from groq import Groq


# Load environment variables
load_dotenv()


# Get Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is missing. "
        "Please add it to the backend .env file."
    )


# Create Groq client
client = Groq(
    api_key=GROQ_API_KEY
)


# Default text model
MODEL_NAME = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")