"""
Main FastAPI application for Agentic RAG.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from config.settings import settings
from utils.logger import logger
import uvicorn


# Create FastAPI app
app = FastAPI(
    title="Agentic RAG Multi-Agent System",
    version="1.0.0",
    description=(
        "A sophisticated multi-agent RAG system using LangGraph and Google Gemini. "
        "Features a supervisor agent that coordinates specialized agents for "
        "local knowledge, web search, and cloud resources."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("=" * 60)
    logger.info("Starting Agentic RAG Multi-Agent System")
    logger.info("=" * 60)
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"LLM Model: {settings.llm_model}")
    logger.info(f"API Prefix: {settings.api_v1_prefix}")
    
    # Initialize the agent graph
    try:
        from graph.agent_graph import get_agent_graph
        logger.info("Initializing multi-agent graph...")
        get_agent_graph()
        logger.info("✓ Multi-agent graph initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize agent graph: {e}")
        import traceback
        traceback.print_exc()
    
    # Initialize vector store
    try:
        from tools.vector_search import vector_search_manager
        logger.info("Initializing vector store...")
        vector_search_manager.initialize()
        logger.info("✓ Vector store initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize vector store: {e}")
        import traceback
        traceback.print_exc()
    
    logger.info("=" * 60)
    logger.info("System Ready!")
    logger.info("=" * 60)
    logger.info(f"API Documentation: http://localhost:8000/docs")
    logger.info(f"Query Endpoint: http://localhost:8000{settings.api_v1_prefix}/query")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Agentic RAG system...")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Agentic RAG Multi-Agent System",
        "version": "1.0.0",
        "status": "running",
        "description": "Multi-agent supervisor system with LangGraph & Gemini",
        "endpoints": {
            "docs": "/docs",
            "api": settings.api_v1_prefix,
            "query": f"{settings.api_v1_prefix}/query",
            "health": f"{settings.api_v1_prefix}/health"
        }
    }


# Include API router
app.include_router(router)


if __name__ == "__main__":
    """Run the application."""
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
