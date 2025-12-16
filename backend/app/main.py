"""ClearSky Text-to-SQL API - Main FastAPI Application."""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, schema, history, config, feedback
from app.services.s3_config_loader import get_config_loader, get_chatbot_config
from app.utils.logging_utils import setup_logging

# Setup logging
log_level = os.environ.get("LOG_LEVEL", "INFO")
setup_logging(level=log_level, json_format=os.environ.get("JSON_LOGS", "false").lower() == "true")

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Starting ClearSky Text-to-SQL API...")
    
    try:
        # Load configurations from S3
        config_loader = get_config_loader()
        config_loader.load_chatbot_config()
        config_loader.load_vector_store_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.warning(f"Failed to load configuration from S3: {e}")
        logger.warning("Using default configuration")
    
    chatbot_config = get_chatbot_config()
    logger.info(f"Application: {chatbot_config.app_name} v{chatbot_config.version}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ClearSky Text-to-SQL API...")


# Create FastAPI app
app = FastAPI(
    title="ClearSky Text-to-SQL API",
    description="Enterprise natural language to SQL query interface powered by AWS Bedrock and Athena",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api")
app.include_router(schema.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    config = get_chatbot_config()
    return {
        "name": config.app_name,
        "version": config.version,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)
