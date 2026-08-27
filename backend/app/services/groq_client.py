import os

from dotenv import load_dotenv
from groq import Groq


# Load environment variables
load_dotenv()


# =========================================================
# GROQ API KEY
# =========================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not configured"
    )


# =========================================================
# GROQ CLIENT
# =========================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# =========================================================
# MODEL
# =========================================================
#
# Use GROQ_MODEL from environment if available.
#
# Otherwise use a smaller vision-capable model.
#
# IMPORTANT:
# Do NOT use qwen/qwen3.6-27b here because your
# Render logs show that its daily token quota was exhausted.
#

MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "meta-llama/llama-4-scout-17b-16e-instruct"
)


print(
    f"Groq client initialized. Model: {MODEL_NAME}"
)
