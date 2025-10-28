"""
FastAPI Main Application - Enhanced with Dependency Injection
Unified API with operational and AI endpoints, enterprise architecture patterns
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from core.middleware import RequestIDMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import time
import logging
import os

from core.config import get_settings
from core.rate_limiting import RateLimiter

# Import our new architectural components
from core.service_registry import create_service_container, ContainerMiddleware
from core.exceptions import (
    app_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler,
    AppException
)

# Configure settings
settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler with dependency injection setup"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize Cache Service
    try:
        from core.cache import CacheService
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        cache_service = CacheService(redis_url)
        await cache_service.connect()
        app.state.cache = cache_service
        logger.info("✅ Cache service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize cache service: {e}")
        app.state.cache = None
    
    # Initialize dependency injection container
    try:
        # Get database URL from environment or settings
        database_url = os.getenv("DATABASE_URL", "sqlite:///./myhibachi.db")
        
        # Create application configuration
        app_config = {
            "database_url": database_url,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "app_name": settings.APP_NAME,
            "business_info": {
                "name": "MyHibachi Restaurant",
                "timezone": "America/Los_Angeles",
                "operating_hours": {
                    "monday": {"open": "11:00", "close": "22:00"},
                    "tuesday": {"open": "11:00", "close": "22:00"},
                    "wednesday": {"open": "11:00", "close": "22:00"},
                    "thursday": {"open": "11:00", "close": "22:00"},
                    "friday": {"open": "11:00", "close": "23:00"},
                    "saturday": {"open": "11:00", "close": "23:00"},
                    "sunday": {"open": "11:00", "close": "22:00"}
                }
            }
        }
        
        # Create and configure DI container
        container = create_service_container(database_url, app_config)
        
        # Register cache service in container
        if app.state.cache:
            container.register_value("cache_service", app.state.cache)
        
        app.state.container = container
        logger.info("✅ Dependency injection container initialized")
        
        # Note: ContainerMiddleware must be added before app starts (see below)
        # We'll store container in app.state for dependency injection via Depends()
        
    except Exception as e:
        logger.error(f"Failed to initialize dependency injection: {e}")
        # Continue startup without DI for backwards compatibility
        app.state.container = None
    
    # Initialize rate limiter
    rate_limiter = RateLimiter()
    await rate_limiter._init_redis()
    app.state.rate_limiter = rate_limiter
    logger.info("✅ Rate limiter initialized")
    
    yield
    
    # Shutdown
    # Close cache service
    if hasattr(app.state, 'cache') and app.state.cache:
        await app.state.cache.disconnect()
        logger.info("✅ Cache service closed")
    
    if hasattr(app.state, 'rate_limiter'):
        if hasattr(app.state.rate_limiter, 'redis_client') and app.state.rate_limiter.redis_client:
            await app.state.rate_limiter.redis_client.close()
        logger.info("✅ Rate limiter closed")
    
    # Cleanup DI container if needed
    if hasattr(app.state, 'container') and app.state.container:
        try:
            # The DI container itself doesn't need cleanup
            # Database sessions are managed per-request and closed automatically
            logger.info("✅ Dependency injection container cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up DI container: {e}")
    
    logger.info("Shutting down application")

app = FastAPI(
    title=settings.APP_NAME,
    description="Unified API with enterprise architecture patterns - DI, Repository Pattern, Error Handling",
    version=settings.API_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Error Handling - Register our custom exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)
logger.info("✅ Custom exception handlers registered")

# Request ID Middleware (must be first to trace all requests)
app.add_middleware(RequestIDMiddleware)
logger.info("✅ Request ID middleware registered for distributed tracing")

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
        "status": "healthy - enterprise architecture patterns implemented!",
        "architecture": {
            "dependency_injection": "✅ Implemented",
            "repository_pattern": "✅ Implemented", 
            "error_handling": "✅ Centralized",
            "rate_limiting": "✅ Active"
        },
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production"
    }

@app.get("/health", tags=["Health"])
async def health_check(request: Request):
    """Health check endpoint for load balancers"""
    # Check DI container status
    di_status = "available" if hasattr(request.app.state, 'container') and request.app.state.container else "not_available"
    
    health_data = {
        "status": "healthy",
        "service": "unified-api",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "architecture": {
            "dependency_injection": di_status,
            "repository_pattern": "implemented",
            "error_handling": "centralized",
            "rate_limiting": "active"
        },
        "timestamp": int(time.time())
    }
    
    # If DI container is available, test service resolution
    if di_status == "available":
        try:
            container = request.app.state.container
            # Test key service resolutions
            booking_repo_available = container.is_registered("booking_repository")
            customer_repo_available = container.is_registered("customer_repository")
            db_session_available = container.is_registered("database_session")
            
            health_data["services"] = {
                "booking_repository": "available" if booking_repo_available else "not_registered",
                "customer_repository": "available" if customer_repo_available else "not_registered", 
                "database_session": "available" if db_session_available else "not_registered"
            }
        except Exception as e:
            health_data["services"] = {"error": f"Service resolution failed: {str(e)}"}
    
    return health_data

# Include routers from moved working API structure
from api.app.routers import health, auth, bookings, stripe
from api.app.crm.endpoints import router as crm_router

# Include our new test endpoints for architectural patterns
try:
    from api.test_endpoints import router as test_router
    app.include_router(test_router, tags=["Architecture Testing"])
    logger.info("✅ New architecture test endpoints included")
except ImportError as e:
    logger.warning(f"Test endpoints not available: {e}")

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

# Include public lead capture endpoints (no auth required)
try:
    from api.v1.endpoints.public_leads import router as public_leads_router
    app.include_router(public_leads_router, prefix="/api/v1/public", tags=["Public Lead Capture"])
    logger.info("✅ Public lead capture endpoints included")
except ImportError as e:
    logger.warning(f"Public lead endpoints not available: {e}")

# AI Chat endpoints from moved AI API
try:
    from api.ai.endpoints.routers.chat import router as ai_chat_router
    app.include_router(ai_chat_router, prefix="/api/v1/ai", tags=["ai-chat"])
    logger.info("✅ AI Chat endpoints included")
except ImportError as e:
    logger.warning(f"AI Chat endpoints not available: {e}")

# Customer Review Blog System (Production-grade with video support)
try:
    from api.v1.customer_reviews import router as customer_reviews_router
    app.include_router(customer_reviews_router, tags=["customer-reviews"])
    logger.info("✅ Customer Review Blog endpoints included (image + video support)")
except ImportError as e:
    logger.warning(f"Customer Review Blog endpoints not available: {e}")

# Admin Review Moderation System (Approval workflow)
try:
    from api.admin.review_moderation import router as admin_moderation_router
    app.include_router(admin_moderation_router, tags=["admin-review-moderation"])
    logger.info("✅ Admin Review Moderation endpoints included (approve/reject/bulk)")
except ImportError as e:
    logger.warning(f"Admin Review Moderation endpoints not available: {e}")
    
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

# Enhanced Health Check endpoints for production K8s
try:
    from api.v1.endpoints.health import router as v1_health_router
    app.include_router(v1_health_router, prefix="/api/v1/health", tags=["Health Checks"])
    logger.info("✅ Enhanced health check endpoints included (K8s ready)")
except ImportError as e:
    logger.warning(f"Enhanced health check endpoints not available: {e}")

# Admin Analytics endpoints - Composite service
try:
    from api.v1.endpoints.analytics import router as analytics_router
    app.include_router(analytics_router, prefix="/api/admin/analytics", tags=["Admin Analytics"])
    logger.info("✅ Admin Analytics endpoints included (6 composite endpoints)")
except ImportError as e:
    logger.warning(f"Admin Analytics endpoints not available: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info"
    )