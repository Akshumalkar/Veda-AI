import os
import time
from typing import Any, Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


# ============================================================
# GROQ CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured")


client = Groq(
    api_key=GROQ_API_KEY,
)


# ============================================================
# MODEL CONFIGURATION
# ============================================================

# Vision-capable model for PDF/image question extraction.
#
# You can override this from Render Environment Variables:
#
# GROQ_VISION_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
#
# The fallback list is used automatically if a model is unavailable.
#
VISION_MODELS = [
    os.getenv(
        "GROQ_VISION_MODEL",
        "meta-llama/llama-4-scout-17b-16e-instruct",
    ),
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]


# Text model used for grading / text-only operations.
#
# Keep this separate from the vision model.
TEXT_MODEL = os.getenv(
    "GROQ_TEXT_MODEL",
    "qwen/qwen3.6-27b",
)


# Backward-compatible model name.
#
# Existing files importing:
#
# from app.services.groq_client import client, MODEL_NAME
#
# will continue working.
MODEL_NAME = VISION_MODELS[0]


# ============================================================
# ERROR HELPERS
# ============================================================

def is_rate_limit_error(error: Exception) -> bool:
    """
    Detect Groq 429 / rate-limit errors.
    """

    message = str(error).lower()

    return (
        "429" in message
        or "rate_limit" in message
        or "rate limit" in message
        or "rate_limit_exceeded" in message
        or "tokens per day" in message
        or "tokens per minute" in message
        or "tpd" in message
        or "tpm" in message
    )


def is_model_not_found_error(error: Exception) -> bool:
    """
    Detect unavailable / invalid model errors.
    """

    message = str(error).lower()

    return (
        "model_not_found" in message
        or "model" in message and "does not exist" in message
        or "do not have access" in message
        or "not found" in message
    )


def get_retry_seconds(
    error: Exception,
    default: int = 5,
) -> int:
    """
    Try to extract the retry duration from Groq's
    rate-limit error message.

    Example:

    Please try again in 23m47.76s
    """

    message = str(error)

    import re

    match = re.search(
        r"try again in\s+"
        r"(?:(\d+)h)?"
        r"(?:(\d+)m)?"
        r"(?:(\d+(?:\.\d+)?)s)?",
        message,
        flags=re.IGNORECASE,
    )

    if not match:
        return default

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = float(match.group(3) or 0)

    total_seconds = (
        hours * 3600
        + minutes * 60
        + seconds
    )

    return max(
        1,
        int(total_seconds),
    )


# ============================================================
# VISION MODEL SELECTION
# ============================================================

def get_vision_models():
    """
    Return configured vision models without duplicates.
    """

    models = []

    for model in VISION_MODELS:
        if model and model not in models:
            models.append(model)

    return models


def get_available_vision_model() -> str:
    """
    Return the preferred vision model.

    This function does not make an API request.
    Actual fallback happens in call_vision().
    """

    models = get_vision_models()

    if not models:
        raise RuntimeError(
            "No Groq vision model is configured."
        )

    return models[0]


# ============================================================
# VISION API CALL
# ============================================================

def call_vision(
    messages: Any,
    temperature: float = 0,
    max_tokens: int = 2000,
    response_format: Optional[dict] = None,
):
    """
    Call a Groq vision model with automatic model fallback.

    Behaviour:

    1. Try the configured vision model.
    2. If model is unavailable -> try next model.
    3. If rate limited -> immediately raise a clean
       rate-limit error instead of repeatedly retrying.
    4. Never waste tokens repeatedly calling a model
       that has exhausted its daily quota.
    """

    models = get_vision_models()

    if not models:
        raise RuntimeError(
            "No Groq vision models are configured."
        )

    last_error = None

    for model_index, model in enumerate(models):

        print(
            f"Groq vision model attempt "
            f"{model_index + 1}/{len(models)}: {model}"
        )

        try:

            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }

            if response_format is not None:
                kwargs["response_format"] = response_format

            response = client.chat.completions.create(
                **kwargs
            )

            print(
                f"Groq vision model selected: {model}"
            )

            return response

        except Exception as error:

            last_error = error

            print(
                f"Groq vision model failed: {model}"
            )

            print(
                f"Error: {error}"
            )

            # ------------------------------------------------
            # 429
            # ------------------------------------------------

            if is_rate_limit_error(error):

                retry_seconds = get_retry_seconds(
                    error
                )

                print(
                    "Groq rate limit detected."
                )

                print(
                    f"Groq requested retry after "
                    f"{retry_seconds} seconds."
                )

                # IMPORTANT:
                #
                # Do NOT sleep for 20+ minutes on Render.
                #
                # A web request should return an error quickly.
                #
                raise RuntimeError(
                    "Groq rate limit exceeded. "
                    f"Please try again in approximately "
                    f"{retry_seconds} seconds."
                ) from error

            # ------------------------------------------------
            # Model unavailable
            # ------------------------------------------------

            if is_model_not_found_error(error):

                print(
                    f"Vision model '{model}' is unavailable."
                )

                if model_index < len(models) - 1:

                    print(
                        "Trying the next available "
                        "vision model..."
                    )

                    continue

                raise RuntimeError(
                    "No configured Groq vision model "
                    "is currently available."
                ) from error

            # ------------------------------------------------
            # Other error
            # ------------------------------------------------

            raise

    if last_error:
        raise last_error

    raise RuntimeError(
        "Groq vision request failed."
    )


# ============================================================
# TEXT API CALL
# ============================================================

def call_text(
    messages: Any,
    temperature: float = 0,
    max_tokens: int = 1000,
    response_format: Optional[dict] = None,
):
    """
    Call the configured text model.

    Used for grading and other text-only operations.
    """

    kwargs = {
        "model": TEXT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    if response_format is not None:
        kwargs["response_format"] = response_format

    try:

        response = client.chat.completions.create(
            **kwargs
        )

        return response

    except Exception as error:

        if is_rate_limit_error(error):

            retry_seconds = get_retry_seconds(
                error
            )

            raise RuntimeError(
                "Groq text model rate limit exceeded. "
                f"Please try again in approximately "
                f"{retry_seconds} seconds."
            ) from error

        raise


# ============================================================
# STARTUP INFORMATION
# ============================================================

print(
    "Groq client initialized."
)

print(
    "Preferred vision model:",
    get_available_vision_model(),
)

print(
    "Text model:",
    TEXT_MODEL,
)
