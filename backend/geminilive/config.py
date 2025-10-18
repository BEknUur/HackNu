"""
Configuration settings for Gemini Live API.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class GeminiLiveConfig(BaseSettings):
    """
    Configuration for Gemini Live API integration.
    """
    
    # API Configuration
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    
    # Model Configuration
    model_name: str = Field(
        default="gemini-2.5-flash-native-audio-preview-09-2025",
        env="GEMINI_MODEL_NAME"
    )
    
    # Audio Configuration
    input_sample_rate: int = Field(default=16000, env="INPUT_SAMPLE_RATE")
    output_sample_rate: int = Field(default=24000, env="OUTPUT_SAMPLE_RATE")
    
    # Response Configuration
    system_instruction: str = Field(
        default="You are a helpful assistant and answer in a friendly tone.",
        env="SYSTEM_INSTRUCTION"
    )
    
    # File Storage
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    output_dir: str = Field(default="outputs", env="OUTPUT_DIR")
    
    # Limits
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10 MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Create global config instance
config = GeminiLiveConfig()

