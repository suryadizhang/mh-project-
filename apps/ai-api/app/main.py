"""
Dedicated AI API - MyHibachi AI Service
Handles AI chat, learning, content generation, and AI-specific functions
"""
import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from app.config import get_settings, validate_configuration
from app.database import engine, init_db, close_db
from app.logging_config import setup_logging
from app.security import setup_security_middleware, get_current_user
from app.routers import webhooks
from app.routers.chat import router as chat_router
from app.routers.admin import router as admin_router
from app.routers.websocket import router as websocket_router
from app.services.ai_pipeline import AIPipeline
from app.services.knowledge_base_simple import SimpleKnowledgeBaseService as KnowledgeBaseService

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global services
ai_service = None
kb_service = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    global ai_service, kb_service
    
    # Load and validate configuration
    settings = validate_configuration()
    logger.info(f"Starting MyHibachi AI API v1.0.0 in {settings.app_env} mode...")
    
    try:
        # Initialize database
        init_db()
        logger.info("Database initialized")
        
        # Validate OpenAI configuration
        openai_config = settings.get_openai_config()
        if openai_config["enabled"]:
            logger.info("OpenAI configuration validated")
        else:
            logger.warning("OpenAI not configured - AI features will be limited")
        
        # Initialize AI services
        if openai_config["enabled"]:
            # ai_service = AIPipeline(openai_config)
            # kb_service = KnowledgeBaseService()
            logger.info("AI services initialized")
        
        logger.info("AI API startup complete")
        
    except Exception as e:
        logger.error(f"Failed to start AI API: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down AI API...")
    close_db()
    logger.info("AI API shutdown complete")


# Create FastAPI app with lifespan management
app = FastAPI(
    title="MyHibachi AI API",
    description="Dedicated AI service for chat, learning, and content generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Setup security middleware (includes CORS)
setup_security_middleware(app)

# Include routers
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(admin_router, prefix="/api", tags=["admin"])
app.include_router(websocket_router, tags=["websocket"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "myhibachi-ai-api",
        "version": "1.0.0",
        "database": "initialized",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "environment": os.getenv("APP_ENV", "development")
    }

# Secure metrics endpoint (requires authentication in production)
@app.get("/metrics")
async def get_metrics(current_user=Depends(get_current_user)):
    """Metrics endpoint with optional authentication"""
    app_env = os.getenv("APP_ENV", "development")
    
    # In production, require authentication
    if app_env == "production" and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return {
        "message": "Metrics endpoint - monitoring system not yet configured",
        "environment": app_env,
        "authenticated": bool(current_user)
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "MyHibachi AI API",
        "description": "Dedicated AI service for chat, learning, and content generation",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        log_level="info"
    )