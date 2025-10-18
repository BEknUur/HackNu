"""
Standalone FastAPI application for Gemini Live API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import router
from .config import config

app = FastAPI(
    title="Gemini Live API",
    description="Real-time audio and text interaction with Gemini using Live API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Gemini Live API Server",
        "model": config.model_name,
        "docs": "/docs",
        "health": "/api/gemini-live/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

