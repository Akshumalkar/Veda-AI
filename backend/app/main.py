from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routes.assessment import router


app = FastAPI(
    title="AI Assessment Analyzer",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "AI Assessment Analyzer backend is running",
    }


@app.get("/debug")
def debug():
    from app.services.groq_client import MODEL_NAME, GROQ_API_KEY, client
    key = GROQ_API_KEY or ""
    key_status = "missing" if not key else ("placeholder" if key == "gsk_placeholder" else f"set ({key[:8]}...)")

    # Text test
    try:
        test = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=10,
        )
        groq_text_test = "success: " + test.choices[0].message.content
    except Exception as e:
        groq_text_test = f"failed: {str(e)}"

    # Vision test with a tiny 1x1 white PNG
    tiny_png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    try:
        vtest = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "What color is this pixel? 2 words max."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{tiny_png_b64}"}}
                ]
            }],
            max_tokens=10,
        )
        groq_vision_test = "success: " + vtest.choices[0].message.content
    except Exception as e:
        groq_vision_test = f"failed: {str(e)}"

    return {
        "groq_api_key": key_status,
        "groq_model": MODEL_NAME,
        "groq_text_test": groq_text_test,
        "groq_vision_test": groq_vision_test,
    }