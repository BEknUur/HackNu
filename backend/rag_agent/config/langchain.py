"""
LangChain Configuration Module

This module provides flexible configuration for LangChain components,
supporting multiple LLM providers and easy extension with new tools.
"""

from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, Field
import os


class LLMProviderConfig(BaseModel):
    """Base configuration for LLM providers."""
    name: str
    model: str
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    api_key: Optional[str] = None
    
    class Config:
        extra = "allow"


class GoogleConfig(LLMProviderConfig):
    """Google Gemini configuration."""
    name: str = "google"
    model: str = "gemini-2.5-flash"
    google_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY"))


class LLMFactory:
    """Factory for creating LLM instances from configuration."""
    
    _providers: Dict[str, Type[LLMProviderConfig]] = {
        "google": GoogleConfig,
    }
    
    @classmethod
    def register_provider(cls, name: str, config_class: Type[LLMProviderConfig]):
        """Register a new LLM provider."""
        cls._providers[name] = config_class
    
    @classmethod
    def create_llm(cls, provider: str, **kwargs) -> Any:
        """Create an LLM instance from provider configuration."""
        if provider not in cls._providers:
            raise ValueError(f"Unknown provider: {provider}. Available: {list(cls._providers.keys())}")
        
        config_class = cls._providers[provider]
        config = config_class(**kwargs)
        
        if provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=config.model,
                google_api_key=config.google_api_key,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens
            )
        else:
            raise ValueError(f"LLM creation not implemented for provider: {provider}")


class ToolConfig(BaseModel):
    """Configuration for tools."""
    name: str
    description: str
    enabled: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"


class LangChainConfig(BaseModel):
    """Main LangChain configuration."""
    
    # Default LLM provider
    default_provider: str = "google"
    
    # Provider configurations
    providers: Dict[str, LLMProviderConfig] = Field(default_factory=dict)
    
    # Tool configurations
    tools: Dict[str, ToolConfig] = Field(default_factory=dict)
    
    # Embedding configuration
    embedding_provider: str = "google"
    embedding_model: str = "models/embedding-001"
    
    # Vector store configuration
    vector_store_type: str = "chroma"
    vector_store_path: str = "data/vector_store"
    top_k_results: int = 3
    
    def get_llm(self, provider: Optional[str] = None) -> Any:
        """Get configured LLM instance."""
        provider = provider or self.default_provider
        
        if provider in self.providers:
            config = self.providers[provider]
            return LLMFactory.create_llm(provider, **config.dict())
        else:
            # Use default configuration
            return LLMFactory.create_llm(provider)
    
    def get_embedding(self):
        """Get configured embedding instance."""
        if self.embedding_provider == "google":
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            return GoogleGenerativeAIEmbeddings(
                model=self.embedding_model,
                google_api_key=os.getenv("GOOGLE_API_KEY")
            )
        else:
            raise ValueError(f"Embedding provider not supported: {self.embedding_provider}")
    
    def add_tool(self, name: str, description: str, enabled: bool = True, **parameters):
        """Add a new tool configuration."""
        self.tools[name] = ToolConfig(
            name=name,
            description=description,
            enabled=enabled,
            parameters=parameters
        )
    
    def get_enabled_tools(self) -> List[str]:
        """Get list of enabled tool names."""
        return [name for name, config in self.tools.items() if config.enabled]


# Global configuration instance
langchain_config = LangChainConfig()

# Register default providers
langchain_config.providers["google"] = GoogleConfig()

# Register default tools
langchain_config.add_tool(
    "vector_search",
    "Search through local knowledge base using vector similarity",
    enabled=True
)

langchain_config.add_tool(
    "web_search", 
    "Search the web for current information using Tavily API",
    enabled=True,
    api_key=os.getenv("TAVILY_API_KEY")
)