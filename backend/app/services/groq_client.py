import os

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# API KEY
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError(
        "GROQ_API_KEY is not configured"
    )


# ============================================================
# CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

# Qwen 3.6 27B is currently a Groq vision-capable model.
#
# It supports:
# - text input
# - image input
# - JSON mode
# - OCR / visual understanding
#
# Keep the model configurable through Render environment
# variables so we do not have to modify source code every
# time the model needs to change.
#
# Source:
# Groq Vision documentation
#
# Default:
# qwen/qwen3.6-27b
# ============================================================

MODEL_NAME = os.getenv(
    "GROQ_MODEL",
    "qwen/qwen3.6-27b",
).strip()


# ============================================================
# OPTIONAL CONFIGURATION
# ============================================================

# Maximum output tokens for question extraction.
#
# This is intentionally kept small because the output is
# structured JSON and we don't need thousands of tokens.
#
# Can be overridden in Render:
#
# GROQ_MAX_COMPLETION_TOKENS=1200
# ============================================================

try:
    MAX_COMPLETION_TOKENS = int(
        os.getenv(
            "GROQ_MAX_COMPLETION_TOKENS",
            "1200",
        )
    )
except ValueError:
    MAX_COMPLETION_TOKENS = 1200


if MAX_COMPLETION_TOKENS < 256:
    MAX_COMPLETION_TOKENS = 256


# ============================================================
# LOGGING
# ============================================================

print(
    "Groq client initialized."
)

print(
    f"Groq model: {MODEL_NAME}"
)

print(
    f"Groq max completion tokens: "
    f"{MAX_COMPLETION_TOKENS}"
)
