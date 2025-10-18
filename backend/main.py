from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from geminilive import router as gemini_router

app = FastAPI(
    title="HackNU API - Gemini Live",
    version="1.0.0",
    description="Real-time audio streaming with Gemini Live API"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "HackNU - Gemini Live API",
        "docs": "/docs",
        "health": "/api/gemini-live/health"
    }

# Include Gemini Live API routes
app.include_router(gemini_router)

