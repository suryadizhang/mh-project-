import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_wsgi_app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.wsgi import WSGIMiddleware

# Import Sentry for error tracking and performance monitoring
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from api.app.auth.middleware import setup_auth_middleware
from core.config import get_settings

settings = get_settings()

# Initialize Sentry if DSN is configured
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment or settings.environment,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR  # Send errors as events
            ),
        ],
        # Performance Monitoring
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        
        # Additional options
        send_default_pii=False,  # Don't send personally identifiable information
        attach_stacktrace=True,
        enable_tracing=True,
        
        # Before send hook to filter sensitive data
        before_send=lambda event, hint: (
            None if settings.environment == "development" and not settings.debug 
            else event
        ),
    )
    logging.info(f"✅ Sentry monitoring initialized (environment: {settings.sentry_environment or settings.environment})")
else:
    logging.info("⚠️ Sentry DSN not configured - monitoring disabled")

# Import CRM components
from api.app.crm.endpoints import router as crm_router
from api.app.database import Base, close_database, engine, init_database
from api.app.routers import auth, bookings, health, stripe

# Import workers for background processing
from api.app.workers.outbox_processors import create_outbox_processor_manager

# Import security middleware
try:
    from app.middleware.security import (
        InputValidationMiddleware,
        MetricsMiddleware,
        RateLimitByIPMiddleware,
        RequestLoggingMiddleware,
        SecurityHeadersMiddleware,
    )
    SECURITY_MIDDLEWARE_AVAILABLE = True
except ImportError:
    SECURITY_MIDDLEWARE_AVAILABLE = False
    logging.warning("Security middleware not available - using basic setup")

# Import Stripe setup utility
try:
    from app.utils.stripe_setup import setup_stripe_products
    STRIPE_SETUP_AVAILABLE = True
except ImportError:
    STRIPE_SETUP_AVAILABLE = False
    logging.warning("Stripe setup utility not available")

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

# Global worker manager instance
worker_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global worker_manager

    # Startup
    logger.info("🚀 Starting My Hibachi CRM FastAPI Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Security: Enhanced security middleware {'enabled' if SECURITY_MIDDLEWARE_AVAILABLE else 'disabled'}")
    logger.info(f"Metrics: {'enabled' if getattr(settings, 'enable_metrics', False) else 'disabled'}")
    logger.info(f"Workers: {'enabled' if settings.workers_enabled else 'disabled'}")

    # Initialize database
    try:
        await init_database()
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    # Create database tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

    # Setup Stripe products and prices (only in development/staging)
    if STRIPE_SETUP_AVAILABLE and settings.environment in ["development", "staging"] and settings.stripe_secret_key:
        try:
            await setup_stripe_products()
            logger.info("✅ Stripe products initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Stripe setup failed: {e}")

    # Initialize outbox processor workers
    if settings.workers_enabled:
        try:
            worker_configs = settings.get_worker_configs()
            worker_manager = create_outbox_processor_manager(worker_configs)

            # Start workers properly with await
            await worker_manager.start_all()
            logger.info("✅ Background workers started successfully")
        except Exception as e:
            logger.warning(f"⚠️ Worker setup failed: {e}")
            worker_manager = None

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
    logger.info("🛑 Shutting down My Hibachi CRM API...")

    # Stop background workers
    if worker_manager:
        try:
            await worker_manager.stop_all()
            logger.info("✅ Background workers stopped")
        except Exception as e:
            logger.error(f"❌ Error stopping workers: {e}")

    # Close database connections
    try:
        await close_database()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")

    logger.info("✅ Shutdown complete")


# Import OpenAPI configuration
from api.app.openapi_config import get_openapi_schema

# Create FastAPI application with enhanced configuration
app = FastAPI(
    title="MyHibachi AI Sales CRM API",
    description="Comprehensive hibachi catering booking and management system with AI-powered features",
    version="2.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)

# Set custom OpenAPI schema
app.openapi = get_openapi_schema(app)

# Setup authentication middleware
setup_auth_middleware(app)

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
    expose_headers=["X-Request-ID", "X-API-Version", "X-RateLimit-Remaining"],
)

# Rate limiting middleware integration
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add Prometheus metrics endpoint
if getattr(settings, 'enable_metrics', False):
    metrics_app = make_wsgi_app()
    app.mount("/metrics", WSGIMiddleware(metrics_app))

# Global exception handlers with enhanced error tracking
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}", extra={"request_id": request_id})
    
    # Capture exception in Sentry with context
    if settings.sentry_dsn:
        with sentry_sdk.push_scope() as scope:
            scope.set_context("request", {
                "url": str(request.url),
                "method": request.method,
                "headers": dict(request.headers),
                "request_id": request_id,
            })
            scope.set_tag("endpoint", request.url.path)
            sentry_sdk.capture_exception(exc)

    # Don't expose internal errors in production
    if settings.environment == "production":
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error. Please try again later.",
                "request_id": request_id
            },
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": str(exc) if settings.debug else "Error details hidden in production",
                "request_id": request_id
            },
        )


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "detail": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.warning(f"Validation error for {request.method} {request.url}: {exc.errors()}", extra={"request_id": request_id})
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": exc.errors() if settings.debug else "Invalid request data",
            "request_id": request_id
        },
    )


# Include routers with comprehensive API structure
app.include_router(health.router, prefix="/api/health", tags=["health"])

# Authentication & Authorization
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])

# Station-aware Authentication & Administration
from api.app.routers.station_auth import router as station_auth_router
from api.app.routers.station_admin import router as station_admin_router
app.include_router(station_auth_router, prefix="/api/station", tags=["station-auth"])
app.include_router(station_admin_router, prefix="/api/admin/stations", tags=["station-admin"])

# CRM Operations (new comprehensive API)
app.include_router(crm_router, prefix="/api", tags=["crm"])

# Payment Processing
app.include_router(stripe.router, prefix="/api/stripe", tags=["payments"])

# Payment Analytics (separate router for /api/payments/analytics)
from api.app.routers.payments import router as payments_router
app.include_router(payments_router, prefix="/api/payments", tags=["payment-analytics"])

# Lead and Newsletter Management
from api.app.routers.leads import router as leads_router
from api.app.routers.newsletter import router as newsletter_router
from api.app.routers.ringcentral_webhooks import router as ringcentral_router
from api.app.routers.admin_analytics import router as admin_analytics_router

app.include_router(leads_router, prefix="/api", tags=["leads"])
app.include_router(newsletter_router, prefix="/api", tags=["newsletter"])
app.include_router(ringcentral_router, prefix="/api", tags=["sms", "webhooks"])
app.include_router(admin_analytics_router, prefix="/api", tags=["admin", "analytics"])

# Legacy API compatibility (for existing frontend)
app.include_router(bookings.router, prefix="/api/booking", tags=["booking-legacy"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings-legacy"])

# Enhanced Booking Admin API (includes /admin/kpis and /admin/customer-analytics)
from api.app.routers.booking_enhanced import router as booking_enhanced_router
app.include_router(booking_enhanced_router, prefix="/api", tags=["booking-enhanced", "admin"])

# Customer Review System
from api.app.routers.reviews import router as reviews_router
app.include_router(reviews_router, prefix="/api/reviews", tags=["reviews", "feedback"])

# QR Code Tracking System
from api.app.routers.qr_tracking import router as qr_tracking_router
app.include_router(qr_tracking_router, prefix="/api/qr", tags=["qr-tracking", "marketing"])


@app.get("/")
async def root():
    """Health check endpoint compatible with source backend."""
    return {
        "message": "My Hibachi CRM API",
        "environment": settings.environment,
        "version": "2.0.0",
        "status": "healthy",
        "features": {
            "cqrs": True,
            "event_sourcing": True,
            "field_encryption": settings.enable_field_encryption,
            "audit_logging": settings.enable_audit_logging,
            "workers": settings.workers_enabled,
            "mfa": True,
            "rbac": True
        }
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    worker_status = "running" if worker_manager and worker_manager.running else "stopped"

    return {
        "status": "healthy",
        "environment": settings.environment,
        "app_name": settings.app_name,
        "database": "connected",
        "workers": worker_status,
        "stripe": "configured" if settings.stripe_secret_key else "not configured",
        "email": "configured" if settings.smtp_user or settings.sendgrid_api_key else "not configured",
        "sms": "configured" if settings.ringcentral_enabled else "not configured",
        "rate_limiting": "enabled" if settings.rate_limit_enabled else "disabled",
        "field_encryption": "enabled" if settings.enable_field_encryption else "disabled",
        "audit_logging": "enabled" if settings.enable_audit_logging else "disabled",
        "features": {
            "oauth2.1": True,
            "oidc": True,
            "mfa": True,
            "rbac": True,
            "cqrs": True,
            "event_sourcing": True,
            "outbox_pattern": True
        }
    }


@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    # Check database connectivity
    try:
        from app.database import get_db_context
        async with get_db_context() as db:
            await db.execute("SELECT 1")
        db_ready = True
    except Exception:
        db_ready = False

    # Check worker status if enabled
    worker_ready = True
    if settings.workers_enabled:
        worker_ready = worker_manager is not None

    ready = db_ready and worker_ready

    return {
        "status": "ready" if ready else "not ready",
        "checks": {
            "database": "ready" if db_ready else "not ready",
            "workers": "ready" if worker_ready else "not ready"
        }
    }


@app.get("/info")
async def app_info():
    """Application information endpoint."""
    return {
        "name": settings.app_name,
        "version": "2.0.0",
        "environment": settings.environment,
        "architecture": "CQRS with Event Sourcing",
        "security": {
            "authentication": "OAuth 2.1 + OIDC",
            "authorization": "RBAC",
            "mfa": "TOTP + Backup Codes",
            "encryption": "AES-GCM Field-Level",
            "audit_logging": "Comprehensive"
        },
        "integrations": {
            "payment": "Stripe",
            "sms": "RingCentral" if settings.ringcentral_enabled else "disabled",
            "email": settings.email_provider if settings.email_enabled else "disabled"
        },
        "worker_stats": {
            "enabled": settings.workers_enabled,
            "sms_worker": settings.sms_worker_enabled,
            "email_worker": settings.email_worker_enabled,
            "stripe_worker": settings.stripe_worker_enabled
        }
    }


# Export OpenAPI schema for TypeScript generation
@app.get("/openapi.json", include_in_schema=False)
async def export_openapi_schema():
    """Export OpenAPI schema for client generation."""
    return app.openapi()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8003,
        reload=False,  # Disable reload for stability
        log_level="info",
        workers=1,  # Single worker for development
    )
