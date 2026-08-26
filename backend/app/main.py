from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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