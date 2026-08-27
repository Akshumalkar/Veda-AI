import os

from dotenv import load_dotenv
from groq import Groq


# ============================================================
# LOAD ENVIRONMENT
# ============================================================

load_dotenv()


GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)


if not GROQ_API_KEY:

    raise RuntimeError(
        "GROQ_API_KEY is missing."
    )


# ============================================================
# GROQ CLIENT
# ============================================================

client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

# IMPORTANT:
# Use only models that are available to your Groq API account.

VISION_MODEL = os.getenv(
    "GROQ_VISION_MODEL",
    "qwen/qwen3.6-27b",
)

TEXT_MODEL = os.getenv(
    "GROQ_TEXT_MODEL",
    "qwen/qwen3.6-27b",
)


print("Groq client initialized.")
print(
    f"Vision model: {VISION_MODEL}"
)
print(
    f"Text model: {TEXT_MODEL}"
)


# ============================================================
# VISION REQUEST
# ============================================================

def call_vision(
    messages,
    temperature: float = 0,
    max_tokens: int = 2500,
    response_format=None,
):
    """
    Send a vision request to Groq.

    Used for:
    - Question extraction
    - Answer sheet extraction
    - Image analysis
    """

    print(
        "\n========== GROQ VISION REQUEST =========="
    )

    print(
        f"Using model: {VISION_MODEL}"
    )

    request_kwargs = {
        "model": VISION_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if response_format:

        request_kwargs[
            "response_format"
        ] = response_format

    response = (
        client.chat.completions.create(
            **request_kwargs
        )
    )

    return response


# ============================================================
# TEXT REQUEST
# ============================================================

def call_text(
    messages,
    temperature: float = 0.1,
    max_tokens: int = 3000,
    response_format=None,
):
    """
    Send a text request to Groq.

    Used for:
    - Answer grading
    - Feedback generation
    - Text analysis
    """

    print(
        "\n========== GROQ TEXT REQUEST =========="
    )

    print(
        f"Using model: {TEXT_MODEL}"
    )

    request_kwargs = {
        "model": TEXT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if response_format:

        request_kwargs[
            "response_format"
        ] = response_format

    response = (
        client.chat.completions.create(
            **request_kwargs
        )
    )

    return response
