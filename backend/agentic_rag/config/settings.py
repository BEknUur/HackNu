"""
Configuration settings for the Agentic RAG system.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Get the agentic_rag module root directory
MODULE_ROOT = Path(__file__).parent.parent.resolve()

# Load environment variables from the main backend .env (one level up from agentic_rag)
BACKEND_ROOT = MODULE_ROOT.parent
load_dotenv(BACKEND_ROOT / '.env')


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_assignment=False  # Allow setting computed fields
    )
    
    # API Keys
    google_api_key: str = "your_google_api_key_here"
    tavily_api_key: str = "your_tavily_api_key_here"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Database - Use the same PostgreSQL database as main backend
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/hacknu")
    
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    max_iterations: int = 5
    
    # LLM Settings
    llm_model: str = "gemini-2.0-flash-exp"
    llm_temperature: float = 0.3
    embedding_model: str = "models/embedding-001"
    
    # Paths - Absolute paths, always relative to agentic_rag module (not configurable via .env)
    documents_path: str = str(MODULE_ROOT / "data" / "documents")
    vector_store_path: str = str(MODULE_ROOT / "data" / "vector_store")
    
    # Vector Search Settings
    top_k_results: int = 3
    
    # API Settings
    api_v1_prefix: str = "/api/rag"
    cors_origins: list[str] = ["*"]


# Global settings instance
settings = Settings()

# Debug: Print paths on import (can be removed in production)
if settings.app_env == "development":
    print(f"📁 Module root: {MODULE_ROOT}")
    print(f"📁 Documents path: {settings.documents_path}")
    print(f"📁 Vector store path: {settings.vector_store_path}")
