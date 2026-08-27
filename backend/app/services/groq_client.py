import os

from dotenv import load_dotenv
from groq import Groq


# Load environment variables
load_dotenv()


# Get Groq API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


# Create Groq client
client = Groq(
    api_key=GROQ_API_KEY or "gsk_placeholder"
)


# Default text model
MODEL_NAME = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")