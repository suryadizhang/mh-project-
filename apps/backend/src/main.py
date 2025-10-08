"""
FastAPI Main Application
Unified API with operational and AI endpoints
"""
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from core.config import get_settings
from core.rate_limiting import rate_limit_middleware

settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # TODO: Initialize database connection
    # TODO: Initialize Redis connection
    # TODO: Initialize external service connections
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    # TODO: Close database connections
    # TODO: Close Redis connections

app = FastAPI(
    title=settings.APP_NAME,
    description="Unified API for operational and AI functions",
    version=settings.API_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log request details and processing time"""
    start_time = time.time()
    
    # Log request
    logger.info(f"{request.method} {request.url.path} - {request.client.host if request.client else 'unknown'}")
    
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    
    # Log response
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    
    return response

# Rate Limiting Middleware
@app.middleware("http")
async def apply_rate_limiting(request: Request, call_next):
    """Apply tiered rate limiting based on user role"""
    # TODO: Extract user from JWT token if present
    user = None  # This will be implemented when auth is added
    return await rate_limit_middleware(request, call_next, user)

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "service": "unified-api",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": int(time.time())
    }

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root endpoint with basic information"""
    return {
        "message": f"{settings.APP_NAME} API",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "health": "/health",
        "endpoints": {
            "operational": "/v1/",
            "ai": "/v1/ai/",
            "webhooks": "/webhooks/",
            "websockets": "/ws/"
        }
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The endpoint {request.url.path} was not found",
            "suggestion": "Check the API documentation at /docs"
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": id(request)
        }
    )

# TODO: Include routers when implemented
# from api.v1.api import api_router
# from api.webhooks.router import webhook_router
# from api.websockets.inbox_ws import ws_router

# app.include_router(api_router, prefix="/v1", tags=["API v1"])
# app.include_router(webhook_router, prefix="/webhooks", tags=["Webhooks"])
# app.include_router(ws_router, prefix="/ws", tags=["WebSockets"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )