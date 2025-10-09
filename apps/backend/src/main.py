"""
FastAPI Main Application - Simplified for Reorganization
Unified API with operational and AI endpoints
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from core.config import get_settings
from core.rate_limiting import RateLimiter

# Configure settings
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
    
    # Initialize rate limiter
    rate_limiter = RateLimiter()
    await rate_limiter._init_redis()
    app.state.rate_limiter = rate_limiter
    logger.info("✅ Rate limiter initialized")
    
    yield
    
    # Shutdown
    if hasattr(app.state, 'rate_limiter'):
        if hasattr(app.state.rate_limiter, 'redis_client') and app.state.rate_limiter.redis_client:
            await app.state.rate_limiter.redis_client.close()
        logger.info("✅ Rate limiter closed")
    logger.info("Shutting down application")

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

# Rate Limiting Middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware wrapper"""
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    if hasattr(app.state, 'rate_limiter'):
        try:
            result = await app.state.rate_limiter.check_and_update(request)
            
            if not result["allowed"]:
                # Rate limit exceeded
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Rate limit exceeded",
                        "tier": result["tier"],
                        "limit": result["limit_type"],
                        "limit_value": result["limit"],
                        "current": result["current"],
                        "retry_after_seconds": result["reset_seconds"]
                    },
                    headers={"Retry-After": str(result["reset_seconds"])}
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            response.headers["X-RateLimit-Tier"] = result["tier"]
            response.headers["X-RateLimit-Remaining-Minute"] = str(result["minute_remaining"])
            response.headers["X-RateLimit-Remaining-Hour"] = str(result["hour_remaining"])
            response.headers["X-RateLimit-Reset-Minute"] = str(result["minute_reset"])
            response.headers["X-RateLimit-Reset-Hour"] = str(result["hour_reset"])
            response.headers["X-RateLimit-Backend"] = "redis" if app.state.rate_limiter.redis_available else "memory"
            
            return response
            
        except Exception as e:
            # If rate limiting fails, allow request but log error
            logger.warning(f"Rate limiting error: {e}")
            response = await call_next(request)
            response.headers["X-RateLimit-Tier"] = "fallback"
            return response
    else:
        # Fallback if rate limiter not initialized
        return await call_next(request)

# Root endpoints
@app.get("/")
async def root():
    """API root endpoint with basic information"""
    return {
        "message": f"{settings.APP_NAME} API",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "healthy - unified backend reorganization complete!",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "service": "unified-api",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "reorganization": "complete",
        "timestamp": int(time.time())
    }

# Include routers from moved working API structure
from api.app.routers import health, auth, bookings, stripe
from api.app.crm.endpoints import router as crm_router

# Include the core working routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])
app.include_router(stripe.router, prefix="/api/stripe", tags=["payments"])
app.include_router(crm_router, prefix="/api/crm", tags=["crm"])

# Try to include additional routers if available
try:
    from api.app.routers.leads import router as leads_router
    from api.app.routers.newsletter import router as newsletter_router
    from api.app.routers.ringcentral_webhooks import router as ringcentral_router
    
    app.include_router(leads_router, prefix="/api/leads", tags=["leads"])
    app.include_router(newsletter_router, prefix="/api/newsletter", tags=["newsletter"])
    app.include_router(ringcentral_router, prefix="/api/ringcentral", tags=["sms"])
    logger.info("✅ Additional CRM routers included")
except ImportError as e:
    logger.warning(f"Some additional routers not available: {e}")

# AI Chat endpoints from moved AI API
try:
    from api.ai.endpoints.routers.chat import router as ai_chat_router
    app.include_router(ai_chat_router, prefix="/api/v1/ai", tags=["ai-chat"])
    logger.info("✅ AI Chat endpoints included")
except ImportError as e:
    logger.warning(f"AI Chat endpoints not available: {e}")
    
    # Add a placeholder AI endpoint
    @app.post("/api/v1/ai/chat", tags=["ai-chat"])
    async def ai_chat_placeholder():
        return {
            "status": "success",
            "message": "AI chat endpoint - moved from apps/ai-api",
            "note": "Full implementation pending import path fixes"
        }

# Unified Inbox endpoints - Week 2 Feature
try:
    from api.v1.inbox.endpoints import router as inbox_router
    app.include_router(inbox_router, tags=["unified-inbox"])
    logger.info("✅ Unified Inbox endpoints included")
except ImportError as e:
    logger.warning(f"Unified Inbox endpoints not available: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )