"""
REST API routes for Gemini Live API integration.
"""

import os
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pathlib import Path

from .utils import GeminiLiveClient, AudioProcessor
from .config import config


router = APIRouter(prefix="/api/gemini-live", tags=["Gemini Live"])


# Ensure directories exist
Path(config.upload_dir).mkdir(exist_ok=True)


# Response Models
class HealthResponse(BaseModel):
    status: str
    model: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    """
    return HealthResponse(
        status="healthy",
        model=config.model_name
    )


@router.post("/stream-audio")
async def stream_audio(
    audio_file: UploadFile = File(...),
    system_instruction: Optional[str] = Form(None)
):
    """
    Process audio file and stream audio response in real-time.
    
    Args:
        audio_file: Audio file to process
        system_instruction: Optional custom system instruction
    
    Returns:
        Streaming audio response in real-time
    """
    if audio_file.size and audio_file.size > config.max_file_size:
        raise HTTPException(status_code=413, detail="File too large")
    
    try:
        # Save uploaded file
        upload_path = Path(config.upload_dir) / f"input_{audio_file.filename}"
        with open(upload_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
        
        # Process audio
        audio_bytes = AudioProcessor.load_audio_file(str(upload_path))
        
        # Initialize client
        instruction = system_instruction or config.system_instruction
        client = GeminiLiveClient(
            api_key=config.google_api_key,
            model=config.model_name,
            system_instruction=instruction
        )
        
        # Stream audio response
        async def audio_stream_generator():
            try:
                async for audio_data in client.process_audio_stream(audio_bytes):
                    yield audio_data
            finally:
                # Clean up upload file after streaming
                if upload_path.exists():
                    upload_path.unlink()
        
        return StreamingResponse(
            audio_stream_generator(),
            media_type="audio/pcm",
            headers={
                "X-Sample-Rate": str(config.output_sample_rate),
                "X-Channels": "1",
                "X-Bit-Depth": "16"
            }
        )
    
    except Exception as e:
        # Clean up on error
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

