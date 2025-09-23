import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import prometheus_client
from prometheus_client import make_wsgi_app
from starlette.middleware.wsgi import WSGIMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import auth, bookings, stripe, health
from app.utils.stripe_setup import setup_stripe_products

# Import security middleware
try:
    from app.middleware.security import (
        SecurityHeadersMiddleware,
        InputValidationMiddleware,
        MetricsMiddleware,
        RequestLoggingMiddleware,
        RateLimitByIPMiddleware
    )
    SECURITY_MIDDLEWARE_AVAILABLE = True
except ImportError:
    SECURITY_MIDDLEWARE_AVAILABLE = False
    logging.warning("Security middleware not available - using basic setup")

# Configure comprehensive logging with security context
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(request_id)s]" if hasattr(logging, 'request_id') else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log") if settings.environment == "production" else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Set up enhanced rate limiter with configurable limits
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{getattr(settings, 'rate_limit_requests', 100)}/minute"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting My Hibachi FastAPI Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Security: Enhanced security middleware {'enabled' if SECURITY_MIDDLEWARE_AVAILABLE else 'disabled'}")
    logger.info(f"Metrics: {'enabled' if getattr(settings, 'enable_metrics', False) else 'disabled'}")

    # Create database tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

    # Setup Stripe products and prices (only in development/staging)
    if settings.environment in ["development", "staging"] and hasattr(settings, 'stripe_secret_key') and settings.stripe_secret_key:
        try:
            await setup_stripe_products()
            logger.info("✅ Stripe products initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Stripe setup failed: {e}")

    # Initialize metrics collection
    if getattr(settings, 'enable_metrics', False):
        try:
            # Ensure prometheus multiproc directory exists
            metrics_dir = getattr(settings, 'prometheus_multiproc_dir', '/tmp/prometheus_multiproc_dir')
            os.makedirs(metrics_dir, exist_ok=True)
            logger.info("✅ Metrics collection initialized")
        except Exception as e:
            logger.warning(f"⚠️ Metrics setup failed: {e}")

    logger.info("🎉 Application startup complete")
    
    yield

    # Shutdown
    logger.info("🛑 Shutting down My Hibachi API...")
    logger.info("✅ Shutdown complete")


# Create FastAPI app with enhanced security
app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade FastAPI backend for My Hibachi with comprehensive booking, payment, security, and monitoring features",
    version="1.2.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan,
    # Security configurations
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
    } if settings.debug else None
)

# Add security middleware in correct order (last added = first executed)
if SECURITY_MIDDLEWARE_AVAILABLE:
    # Request logging (should be first)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Input validation
    app.add_middleware(InputValidationMiddleware)
    
    # Metrics collection
    if getattr(settings, 'enable_metrics', False):
        app.add_middleware(MetricsMiddleware)
    
    # Rate limiting (additional layer beyond slowapi)
    if getattr(settings, 'rate_limit_enabled', True):
        app.add_middleware(
            RateLimitByIPMiddleware,
            requests_per_minute=getattr(settings, 'rate_limit_requests', 100)
        )

# CORS middleware (should be after security middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-API-Version"],
)

# Rate limiting middleware integration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add Prometheus metrics endpoint
if getattr(settings, 'enable_metrics', False):
    metrics_app = make_wsgi_app()
    app.mount("/metrics", WSGIMiddleware(metrics_app))

# Global exception handlers with enhanced error tracking
# Global exception handlers with enhanced error tracking
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}", extra={"request_id": request_id})
    
    # Don't expose internal errors in production
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Please try again later."},
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc) if settings.debug else "Error details hidden in production"
            },
        )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404, 
        content={"detail": "The requested resource was not found"}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.warning(f"Validation error for {request.method} {request.url}: {exc.errors()}", extra={"request_id": request_id})
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors() if settings.debug else "Invalid request data"
        },
    )


# Include routers with comprehensive API structure
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(stripe.router, prefix="/api/stripe", tags=["stripe"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(bookings.router, prefix="/api/booking", tags=["booking"])

# Legacy API compatibility (for existing frontend)
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings-legacy"])


@app.get("/")
async def root():
    """Health check endpoint compatible with source backend."""
    return {
        "message": "My hibachi", 
        "environment": settings.environment,
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "app_name": settings.app_name,
        "database": "connected",
        "stripe": "configured" if settings.stripe_secret_key else "not configured",
        "email": "configured" if settings.smtp_user else "not configured",
        "rate_limiting": "enabled" if settings.rate_limit_enabled else "disabled",
    }


@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    # Add any readiness checks here (database connectivity, etc.)
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
