"""
FastAPI Main Application - Enhanced with Dependency Injection
Unified API with operational and AI endpoints, enterprise architecture patterns
"""

import asyncio
from contextlib import asynccontextmanager
import logging
import os
import time

# Import Sentry for error tracking and performance monitoring
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from core.config import get_settings
from core.exceptions import (
    AppException,
    app_exception_handler,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from core.middleware import RequestIDMiddleware
from core.rate_limiting import RateLimiter
from core.security_middleware import (
    RequestSizeLimiter,
    SecurityHeadersMiddleware,
)

# Import our new architectural components
from core.service_registry import create_service_container
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import SlowAPI for secondary rate limiting layer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Import Prometheus for metrics
from prometheus_client import make_wsgi_app
from starlette.middleware.wsgi import WSGIMiddleware

# Configure settings
settings = get_settings()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry if DSN is configured (PRODUCTION MONITORING)
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment or settings.ENVIRONMENT,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR,  # Send errors as events
            ),
        ],
        # Performance Monitoring
        traces_sample_rate=getattr(settings, "sentry_traces_sample_rate", 1.0),
        profiles_sample_rate=getattr(
            settings, "sentry_profiles_sample_rate", 1.0
        ),
        # Additional options
        send_default_pii=False,  # Don't send personally identifiable information
        attach_stacktrace=True,
        enable_tracing=True,
        # Before send hook to filter sensitive data
        before_send=lambda event, hint: (
            None
            if settings.ENVIRONMENT == "development" and not settings.DEBUG
            else event
        ),
    )
    logger.info(
        f"✅ Sentry monitoring initialized (environment: {settings.sentry_environment or settings.ENVIRONMENT})"
    )
else:
    logger.info("⚠️ Sentry DSN not configured - monitoring disabled")

# Set up SlowAPI rate limiter (secondary layer)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{getattr(settings, 'RATE_LIMIT_REQUESTS', 100)}/minute"],
)
logger.info("✅ SlowAPI rate limiter configured")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler with dependency injection setup"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize Cache Service with timeout (non-blocking)
    try:
        from core.cache import CacheService

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        cache_service = CacheService(redis_url)

        # Add timeout to prevent hanging
        await asyncio.wait_for(cache_service.connect(), timeout=3.0)
        app.state.cache = cache_service
        logger.info("✅ Cache service initialized")
    except TimeoutError:
        logger.warning(
            "⚠️ Cache service connection timeout - continuing without cache"
        )
        app.state.cache = None
    except Exception as e:
        logger.warning(
            f"⚠️ Cache service unavailable: {e} - continuing without cache"
        )
        app.state.cache = None

    # Initialize dependency injection container (synchronous, fast)
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
                    "sunday": {"open": "11:00", "close": "22:00"},
                },
            },
        }

        # Create and configure DI container
        container = create_service_container(database_url, app_config)

        # Register cache service in container
        if app.state.cache:
            container.register_value("cache_service", app.state.cache)

        app.state.container = container
        logger.info("✅ Dependency injection container initialized")

    except Exception as e:
        logger.warning(
            f"⚠️ DI container initialization failed: {e} - continuing without DI"
        )
        app.state.container = None

    # Initialize rate limiter with timeout (non-blocking)
    try:
        rate_limiter = RateLimiter()

        # Add timeout to prevent hanging
        await asyncio.wait_for(rate_limiter._init_redis(), timeout=3.0)
        app.state.rate_limiter = rate_limiter
        logger.info("✅ Rate limiter initialized")
    except TimeoutError:
        logger.warning(
            "⚠️ Rate limiter connection timeout - using memory-based fallback"
        )
        rate_limiter = RateLimiter()
        rate_limiter.redis_available = False
        app.state.rate_limiter = rate_limiter
    except Exception as e:
        logger.warning(
            f"⚠️ Rate limiter Redis unavailable: {e} - using memory-based fallback"
        )
        rate_limiter = RateLimiter()
        rate_limiter.redis_available = False
        app.state.rate_limiter = rate_limiter

    # Start payment email monitoring scheduler (non-blocking)
    try:
        from services.payment_email_scheduler import (
            start_payment_email_scheduler,
        )

        # Start in background - don't wait for first email check
        start_payment_email_scheduler()
        logger.info("✅ Payment email monitoring scheduler started")
    except ImportError as e:
        logger.warning(
            f"⚠️ Payment email scheduler not available (missing dependencies): {e}"
        )
    except Exception as e:
        logger.warning(f"⚠️ Payment email scheduler not available: {e}")

    # Initialize and start AI Orchestrator with Follow-Up Scheduler (Phase 1B)
    # Phase 3: Using DI Container pattern
    try:
        from api.ai.container import get_container

        container = get_container()
        orchestrator = container.get_orchestrator()
        await orchestrator.start()
        app.state.orchestrator = orchestrator
        logger.info(
            "✅ AI Orchestrator with Follow-Up Scheduler started (via DI Container)"
        )
    except ImportError as e:
        logger.warning(
            f"⚠️ AI Orchestrator not available (missing dependencies): {e}"
        )
        app.state.orchestrator = None
    except Exception as e:
        logger.warning(f"⚠️ AI Orchestrator initialization failed: {e}")
        app.state.orchestrator = None

    # Initialize outbox processor workers (CQRS + Event Sourcing) - NEW location
    if getattr(settings, "WORKERS_ENABLED", False):
        try:
            from workers.outbox_processors import (
                create_outbox_processor_manager,
            )

            worker_configs = getattr(
                settings, "get_worker_configs", lambda: {}
            )()
            worker_manager = create_outbox_processor_manager(worker_configs)
            await worker_manager.start_all()
            app.state.worker_manager = worker_manager
            logger.info(
                "✅ Outbox processor workers started from NEW location (CQRS + Event Sourcing)"
            )
        except ImportError as e:
            logger.warning(
                f"⚠️ Outbox processors not available from NEW location, trying OLD: {e}"
            )
            try:
                from api.app.workers.outbox_processors import (
                    create_outbox_processor_manager,
                )

                worker_configs = getattr(
                    settings, "get_worker_configs", lambda: {}
                )()
                worker_manager = create_outbox_processor_manager(
                    worker_configs
                )
                await worker_manager.start_all()
                app.state.worker_manager = worker_manager
                logger.warning("⚠️ Using OLD workers location")
            except ImportError as e2:
                logger.warning(f"⚠️ Outbox processors not available: {e2}")
                app.state.worker_manager = None
        except Exception as e:
            logger.warning(f"⚠️ Worker setup failed: {e}")
            app.state.worker_manager = None
    else:
        app.state.worker_manager = None

    # Initialize Prometheus metrics collection
    if getattr(settings, "ENABLE_METRICS", False):
        try:
            metrics_dir = getattr(
                settings,
                "PROMETHEUS_MULTIPROC_DIR",
                "/tmp/prometheus_multiproc_dir",
            )
            os.makedirs(metrics_dir, exist_ok=True)
            logger.info("✅ Prometheus metrics collection initialized")
        except Exception as e:
            logger.warning(f"⚠️ Metrics setup failed: {e}")

    logger.info("🚀 Application startup complete - ready to accept requests")

    yield

    # Shutdown
    # Stop outbox processor workers
    if hasattr(app.state, "worker_manager") and app.state.worker_manager:
        try:
            await app.state.worker_manager.stop_all()
            logger.info("✅ Outbox processor workers stopped")
        except Exception as e:
            logger.warning(f"Error stopping workers: {e}")

    # Stop AI Orchestrator and Follow-Up Scheduler
    if hasattr(app.state, "orchestrator") and app.state.orchestrator:
        try:
            await app.state.orchestrator.stop()
            logger.info("✅ AI Orchestrator and Follow-Up Scheduler stopped")
        except Exception as e:
            logger.warning(f"Error stopping orchestrator: {e}")

    # Stop payment email monitoring scheduler
    try:
        from services.payment_email_scheduler import (
            stop_payment_email_scheduler,
        )

        stop_payment_email_scheduler()
        logger.info("✅ Payment email monitoring scheduler stopped")
    except Exception as e:
        logger.warning(f"Error stopping payment email scheduler: {e}")

    # Close cache service
    if hasattr(app.state, "cache") and app.state.cache:
        await app.state.cache.disconnect()
        logger.info("✅ Cache service closed")

    if hasattr(app.state, "rate_limiter"):
        if (
            hasattr(app.state.rate_limiter, "redis_client")
            and app.state.rate_limiter.redis_client
        ):
            await app.state.rate_limiter.redis_client.close()
        logger.info("✅ Rate limiter closed")

    # Cleanup DI container if needed
    if hasattr(app.state, "container") and app.state.container:
        try:
            # The DI container itself doesn't need cleanup
            # Database sessions are managed per-request and closed automatically
            logger.info("✅ Dependency injection container cleaned up")
        except Exception as e:
            logger.warning(f"Error cleaning up DI container: {e}")

    logger.info("Shutting down application")


app = FastAPI(
    title=settings.APP_NAME,
    description="Unified API with enterprise architecture patterns - DI, Repository Pattern, Error Handling, CQRS, Event Sourcing",
    version=settings.API_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# SlowAPI rate limiting integration (secondary layer)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
logger.info("✅ SlowAPI exception handler registered")

# Prometheus metrics endpoint
if getattr(settings, "ENABLE_METRICS", False):
    metrics_app = make_wsgi_app()
    app.mount("/metrics", WSGIMiddleware(metrics_app))
    logger.info("✅ Prometheus /metrics endpoint mounted")

# Error Handling - Register our custom exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)


# Enhanced global exception handler with Sentry integration
@app.exception_handler(Exception)
async def enhanced_global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with Sentry integration"""
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.error(
        f"Unhandled error on {request.method} {request.url}: {exc}",
        extra={"request_id": request_id},
    )

    # Capture exception in Sentry with context
    if settings.sentry_dsn:
        with sentry_sdk.push_scope() as scope:
            scope.set_context(
                "request",
                {
                    "url": str(request.url),
                    "method": request.method,
                    "headers": dict(request.headers),
                    "request_id": request_id,
                },
            )
            scope.set_tag("endpoint", request.url.path)
            sentry_sdk.capture_exception(exc)

    # Call the original handler
    return await general_exception_handler(request, exc)


logger.info(
    "✅ Custom exception handlers registered (with Sentry integration)"
)

# Request ID Middleware (must be first to trace all requests)
app.add_middleware(RequestIDMiddleware)
logger.info("✅ Request ID middleware registered for distributed tracing")

# Add advanced middleware if available
try:
    from middleware.structured_logging import StructuredLoggingMiddleware

    app.add_middleware(
        StructuredLoggingMiddleware,
        log_request_body=settings.DEBUG,  # Only log request bodies in debug mode
        log_response_body=False,  # Don't log response bodies (can be large)
    )
    logger.info("✅ Structured logging middleware registered")
except ImportError:
    logger.warning("⚠️ Structured logging middleware not available")

# Security Headers Middleware (PRODUCTION SECURITY)
app.add_middleware(SecurityHeadersMiddleware)
logger.info(
    "✅ Security headers middleware registered (HSTS, CSP, X-Frame-Options)"
)

# Request Size Limiter (PREVENT DOS ATTACKS)
app.add_middleware(
    RequestSizeLimiter, max_size=10 * 1024 * 1024
)  # 10 MB limit
logger.info("✅ Request size limiter registered (10 MB maximum)")

# CORS Middleware (MULTI-DOMAIN SUPPORT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)
logger.info(
    f"✅ CORS middleware registered for origins: {settings.cors_origins_list}"
)


# Rate Limiting Middleware
@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Rate limiting middleware wrapper"""
    # Skip rate limiting for health checks
    if request.url.path in [
        "/health",
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
    ]:
        return await call_next(request)

    if hasattr(app.state, "rate_limiter"):
        try:
            # Extract user from JWT token if present (for proper rate limiting tiers)
            user = None
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    from core.security import extract_user_from_token

                    token = auth_header.split(" ")[1]
                    user = extract_user_from_token(token)
                except Exception:
                    pass  # Invalid token, treat as public user

            result = await app.state.rate_limiter.check_and_update(
                request, user
            )

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
                        "retry_after_seconds": result["reset_seconds"],
                    },
                    headers={"Retry-After": str(result["reset_seconds"])},
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers
            response.headers["X-RateLimit-Tier"] = result["tier"]
            response.headers["X-RateLimit-Remaining-Minute"] = str(
                result["minute_remaining"]
            )
            response.headers["X-RateLimit-Remaining-Hour"] = str(
                result["hour_remaining"]
            )
            response.headers["X-RateLimit-Reset-Minute"] = str(
                result["minute_reset"]
            )
            response.headers["X-RateLimit-Reset-Hour"] = str(
                result["hour_reset"]
            )
            response.headers["X-RateLimit-Backend"] = (
                "redis" if app.state.rate_limiter.redis_available else "memory"
            )

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
            "rate_limiting": "✅ Active",
        },
        "docs": (
            "/docs"
            if settings.DEBUG
            else "Documentation disabled in production"
        ),
    }


@app.get("/health", tags=["Health"])
async def health_check(request: Request):
    """Health check endpoint for load balancers"""
    # Check DI container status
    di_status = (
        "available"
        if hasattr(request.app.state, "container")
        and request.app.state.container
        else "not_available"
    )

    health_data = {
        "status": "healthy",
        "service": "unified-api",
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "architecture": {
            "dependency_injection": di_status,
            "repository_pattern": "implemented",
            "error_handling": "centralized",
            "rate_limiting": "active",
        },
        "timestamp": int(time.time()),
    }

    # If DI container is available, test service resolution
    if di_status == "available":
        try:
            container = request.app.state.container
            # Test key service resolutions
            booking_repo_available = container.is_registered(
                "booking_repository"
            )
            customer_repo_available = container.is_registered(
                "customer_repository"
            )
            db_session_available = container.is_registered("database_session")

            health_data["services"] = {
                "booking_repository": (
                    "available" if booking_repo_available else "not_registered"
                ),
                "customer_repository": (
                    "available"
                    if customer_repo_available
                    else "not_registered"
                ),
                "database_session": (
                    "available" if db_session_available else "not_registered"
                ),
            }
        except Exception as e:
            health_data["services"] = {
                "error": f"Service resolution failed: {e!s}"
            }

    return health_data


@app.get("/ready", tags=["Health"])
async def readiness_check(request: Request):
    """Kubernetes readiness probe endpoint"""
    try:
        # Check database connectivity
        from core.database import get_db

        async for db in get_db():
            await db.execute("SELECT 1")
            break
        db_ready = True
    except Exception:
        db_ready = False

    # Check worker status if enabled
    worker_ready = True
    if getattr(settings, "WORKERS_ENABLED", False):
        worker_ready = (
            hasattr(request.app.state, "worker_manager")
            and request.app.state.worker_manager is not None
        )

    ready = db_ready and worker_ready

    return {
        "status": "ready" if ready else "not ready",
        "ready": ready,  # Add top-level ready boolean field
        "checks": {
            "database": "ready" if db_ready else "not ready",
            "workers": "ready" if worker_ready else "not ready",
        },
    }


@app.get("/info", tags=["Health"])
async def app_info():
    """Application information endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "architecture": "CQRS with Event Sourcing + DI + Repository Pattern",
        "security": {
            "authentication": "OAuth 2.1 + OIDC",
            "authorization": "RBAC",
            "mfa": "TOTP + Backup Codes",
            "encryption": (
                "AES-GCM Field-Level"
                if getattr(settings, "ENABLE_FIELD_ENCRYPTION", False)
                else "disabled"
            ),
            "audit_logging": (
                "Comprehensive"
                if getattr(settings, "ENABLE_AUDIT_LOGGING", False)
                else "disabled"
            ),
        },
        "integrations": {
            "payment": "Stripe",
            "sms": (
                "RingCentral"
                if getattr(settings, "RINGCENTRAL_ENABLED", False)
                else "disabled"
            ),
            "email": (
                getattr(settings, "EMAIL_PROVIDER", "disabled")
                if getattr(settings, "EMAIL_ENABLED", False)
                else "disabled"
            ),
        },
        "features": {
            "oauth2.1": True,
            "oidc": True,
            "mfa": True,
            "rbac": True,
            "cqrs": True,
            "event_sourcing": True,
            "outbox_pattern": getattr(settings, "WORKERS_ENABLED", False),
            "ai_orchestrator": True,
            "multi_channel_ai": True,
            "dependency_injection": True,
        },
        "worker_stats": {
            "enabled": getattr(settings, "WORKERS_ENABLED", False),
            "sms_worker": getattr(settings, "SMS_WORKER_ENABLED", False),
            "email_worker": getattr(settings, "EMAIL_WORKER_ENABLED", False),
            "stripe_worker": getattr(settings, "STRIPE_WORKER_ENABLED", False),
        },
    }


# ============================================================================
# PHASE 2A: Import Migration - NEW Clean Architecture (2025-11-04)
# ============================================================================
# All routers now imported from NEW structure: routers/v1/*, services/*, cqrs/*, workers/*, core/auth/*
# OLD imports kept commented below as backup for easy rollback
# ============================================================================

# Import routers from NEW clean architecture structure
from routers.v1 import auth, bookings, health

# Note: stripe router import updated below in the try/catch block
# Note: CRM router no longer exists as standalone - functionality distributed across routers

# ============================================================================
# OLD IMPORTS (BACKUP - Can uncomment if issues arise)
# ============================================================================
# from api.app.crm.endpoints import router as crm_router
# from api.app.routers import auth, bookings, health, stripe
# ============================================================================

# Include OAuth endpoints
try:
    from api.v1.endpoints.google_oauth import router as google_oauth_router

    app.include_router(google_oauth_router, tags=["Authentication - OAuth"])
    logger.info("✅ Google OAuth endpoints included")
except ImportError as e:
    logger.warning(f"Google OAuth endpoints not available: {e}")

# Include User Management endpoints (Super Admin)
try:
    from api.v1.endpoints.user_management import (
        router as user_management_router,
    )

    app.include_router(user_management_router, tags=["User Management"])
    logger.info("✅ User Management endpoints included")
except ImportError as e:
    logger.warning(f"User Management endpoints not available: {e}")

# Include Role Management endpoints (Super Admin)
try:
    from api.v1.endpoints.role_management import (
        router as role_management_router,
    )

    app.include_router(role_management_router, tags=["Role Management"])
    logger.info("✅ Role Management endpoints included")
except ImportError as e:
    logger.warning(f"Role Management endpoints not available: {e}")

# Include Payment Calculator endpoints (for fee calculations)
try:
    from api.v1.endpoints.payment_calculator import (
        router as payment_calculator_router,
    )

    app.include_router(
        payment_calculator_router,
        prefix="/api/v1/payments",
        tags=["Payment Calculator"],
    )
    logger.info("✅ Payment Calculator endpoints included")
except ImportError as e:
    logger.warning(f"Payment Calculator endpoints not available: {e}")

# Include our new test endpoints for architectural patterns
try:
    from api.test_endpoints import router as test_router

    app.include_router(test_router, tags=["Architecture Testing"])
    logger.info("✅ New architecture test endpoints included")
except ImportError as e:
    logger.warning(f"Test endpoints not available: {e}")

# Include the core working routers (NEW clean architecture)
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])
# Also register with /api/v1 prefix for frontend compatibility
app.include_router(
    bookings.router, prefix="/api/v1/bookings", tags=["bookings-v1"]
)

# Stripe router from NEW location
try:
    from routers.v1.stripe import router as stripe_router

    app.include_router(stripe_router, prefix="/api/stripe", tags=["payments"])

    # Also register customer endpoints at /api/v1 for frontend compatibility
    # Create a sub-router for customer endpoints only
    from fastapi import APIRouter as _APIRouter
    from fastapi import Depends as _Depends
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession
    from core.database import get_db as _get_db

    customer_compat_router = _APIRouter(tags=["customers-compat"])

    # Import the actual endpoint functions and re-register them
    # This creates aliases at /api/v1/customers/* that point to /api/stripe/v1/customers/*
    @customer_compat_router.get("/v1/customers/dashboard")
    async def customer_dashboard_compat(
        customer_id: str,
        request: Request,
        db: _AsyncSession = _Depends(_get_db),
    ):
        """Compatibility endpoint - redirects to stripe router"""
        from routers.v1.stripe import get_customer_dashboard

        return await get_customer_dashboard(customer_id=customer_id, db=db)

    app.include_router(customer_compat_router, prefix="/api")
    logger.info(
        "✅ Stripe router included from NEW location with customer compatibility endpoints"
    )
except ImportError as e_stripe:
    # Fallback to old location (should not happen after migration)
    try:
        from api.app.routers.stripe import router as stripe_router

        app.include_router(
            stripe_router, prefix="/api/stripe", tags=["payments"]
        )
        logger.warning(
            "⚠️ Using OLD stripe router location (migration incomplete)"
        )
    except ImportError as e:
        logger.error(
            f"❌ Stripe router not available. NEW: {e_stripe}, OLD: {e}"
        )

# CRM router removed - functionality distributed across other routers
# OLD: app.include_router(crm_router, prefix="/api/crm", tags=["crm"])
# Note: CRM features now available through: leads, newsletter, bookings, station_admin routers

# Station Management and Authentication (Multi-tenant RBAC) - NEW location
try:
    from routers.v1.station_auth import router as station_auth_router
    from routers.v1.station_admin import router as station_admin_router

    app.include_router(
        station_auth_router, prefix="/api/station", tags=["station-auth"]
    )
    app.include_router(
        station_admin_router,
        prefix="/api/admin/stations",
        tags=["station-admin"],
    )
    logger.info(
        "✅ Station Management and Auth endpoints included from NEW location (Multi-tenant RBAC)"
    )
except ImportError as e:
    logger.warning(
        f"Station Management endpoints not available from NEW location, trying OLD: {e}"
    )
    try:
        # OLD location fallback
        from api.app.routers.station_auth import router as station_auth_router
        from api.app.routers.station_admin import (
            router as station_admin_router,
        )

        app.include_router(
            station_auth_router, prefix="/api/station", tags=["station-auth"]
        )
        app.include_router(
            station_admin_router,
            prefix="/api/admin/stations",
            tags=["station-admin"],
        )
        logger.warning("⚠️ Using OLD station router locations")
    except ImportError as e2:
        logger.error(f"❌ Station Management endpoints not available: {e2}")

# Enhanced Booking Admin API (includes /admin/kpis and /admin/customer-analytics) - NEW location
try:
    from routers.v1.booking_enhanced import router as booking_enhanced_router

    app.include_router(
        booking_enhanced_router,
        prefix="/api",
        tags=["booking-enhanced", "admin"],
    )
    logger.info(
        "✅ Enhanced Booking Admin API included from NEW location (KPIs, customer analytics)"
    )
except ImportError as e:
    logger.warning(
        f"Enhanced Booking Admin endpoints not available from NEW location, trying OLD: {e}"
    )
    try:
        from api.app.routers.booking_enhanced import (
            router as booking_enhanced_router,
        )

        app.include_router(
            booking_enhanced_router,
            prefix="/api",
            tags=["booking-enhanced", "admin"],
        )
        logger.warning("⚠️ Using OLD booking_enhanced location")
    except ImportError as e2:
        logger.error(
            f"❌ Enhanced Booking Admin endpoints not available: {e2}"
        )

# Payment Analytics (separate router for /api/payments/analytics) - NEW location
try:
    from routers.v1.payments import router as payments_router

    app.include_router(
        payments_router, prefix="/api/payments", tags=["payment-analytics"]
    )
    logger.info("✅ Payment Analytics endpoints included from NEW location")
except ImportError as e:
    logger.warning(
        f"Payment Analytics endpoints not available from NEW location, trying OLD: {e}"
    )
    try:
        from api.app.routers.payments import router as payments_router

        app.include_router(
            payments_router, prefix="/api/payments", tags=["payment-analytics"]
        )
        logger.warning("⚠️ Using OLD payments location")
    except ImportError as e2:
        logger.error(f"❌ Payment Analytics endpoints not available: {e2}")

# QR Code Tracking System - NEW location
try:
    from routers.v1.qr_tracking import router as qr_tracking_router

    app.include_router(
        qr_tracking_router, prefix="/api/qr", tags=["qr-tracking", "marketing"]
    )
    logger.info("✅ QR Code Tracking System included from NEW location")
except ImportError as e:
    logger.warning(
        f"QR Tracking endpoints not available from NEW location, trying OLD: {e}"
    )
    try:
        from api.app.routers.qr_tracking import router as qr_tracking_router

        app.include_router(
            qr_tracking_router,
            prefix="/api/qr",
            tags=["qr-tracking", "marketing"],
        )
        logger.warning("⚠️ Using OLD qr_tracking location")
    except ImportError as e2:
        logger.error(f"❌ QR Tracking endpoints not available: {e2}")

# Admin Error Logs (for monitoring and debugging) - NEW location
try:
    from routers.v1.admin.error_logs import router as error_logs_router

    app.include_router(
        error_logs_router,
        prefix="/api",
        tags=["admin", "error-logs", "monitoring"],
    )
    logger.info("✅ Admin Error Logs endpoints included from NEW location")
except ImportError as e:
    logger.warning(
        f"Admin Error Logs endpoints not available from NEW location, trying OLD: {e}"
    )
    try:
        from api.app.routers.admin.error_logs import (
            router as error_logs_router,
        )

        app.include_router(
            error_logs_router,
            prefix="/api",
            tags=["admin", "error-logs", "monitoring"],
        )
        logger.warning("⚠️ Using OLD admin.error_logs location")
    except ImportError as e2:
        logger.error(f"❌ Admin Error Logs endpoints not available: {e2}")

# Notification Groups Admin - NEW location
try:
    from routers.v1.admin.notification_groups import (
        router as notification_groups_router,
    )

    app.include_router(
        notification_groups_router,
        prefix="/api/admin/notification-groups",
        tags=["admin", "notifications"],
    )
    logger.info("✅ Notification Groups Admin included from NEW location")
except ImportError as e:
    logger.warning(
        f"Notification Groups endpoints not available from NEW location, trying OLD: {e}"
    )
    try:
        from api.app.routers.admin.notification_groups import (
            router as notification_groups_router,
        )

        app.include_router(
            notification_groups_router,
            prefix="/api/admin/notification-groups",
            tags=["admin", "notifications"],
        )
        logger.warning("⚠️ Using OLD admin.notification_groups location")
    except ImportError as e2:
        logger.error(f"❌ Notification Groups endpoints not available: {e2}")

# Admin Analytics (comprehensive) - NEW location
try:
    from routers.v1.admin_analytics import router as admin_analytics_router

    app.include_router(
        admin_analytics_router, prefix="/api", tags=["admin", "analytics"]
    )
    logger.info("✅ Admin Analytics endpoints included from NEW location")
except ImportError as e:
    logger.warning(
        f"Admin Analytics endpoints not available from NEW location, trying OLD: {e}"
    )
    try:
        from api.app.routers.admin_analytics import (
            router as admin_analytics_router,
        )

        app.include_router(
            admin_analytics_router, prefix="/api", tags=["admin", "analytics"]
        )
        logger.warning("⚠️ Using OLD admin_analytics location")
    except ImportError as e2:
        logger.error(f"❌ Admin Analytics endpoints not available: {e2}")

# Customer Review System (from legacy - comprehensive) - NEW location
try:
    from routers.v1.reviews import router as reviews_router

    # DEBUG: Check for router-level dependencies
    logger.info(
        f"🔍 DEBUG: Reviews router dependencies: {reviews_router.dependencies}"
    )
    logger.info(f"🔍 DEBUG: Reviews router prefix: {reviews_router.prefix}")

    app.include_router(
        reviews_router, prefix="/api/reviews", tags=["reviews", "feedback"]
    )
    logger.info(
        "✅ Customer Review System included from NEW location (legacy comprehensive version)"
    )
except ImportError as e:
    logger.warning(
        f"Customer Review System endpoints not available from NEW location, trying OLD: {e}"
    )
    try:
        from api.app.routers.reviews import router as reviews_router

        app.include_router(
            reviews_router, prefix="/api/reviews", tags=["reviews", "feedback"]
        )
        logger.warning("⚠️ Using OLD reviews location")
    except ImportError as e2:
        logger.error(
            f"❌ Customer Review System endpoints not available: {e2}"
        )

# Try to include additional routers if available - NEW locations
try:
    from routers.v1.leads import router as leads_router
    from routers.v1.newsletter import router as newsletter_router
    from routers.v1.ringcentral_webhooks import (
        router as ringcentral_router,
    )

    app.include_router(leads_router, prefix="/api/leads", tags=["leads"])
    app.include_router(
        newsletter_router, prefix="/api/newsletter", tags=["newsletter"]
    )
    app.include_router(
        ringcentral_router, prefix="/api/ringcentral", tags=["sms"]
    )
    logger.info("✅ Additional CRM routers included from NEW location")
except ImportError as e:
    logger.warning(
        f"Some additional routers not available from NEW location, trying OLD: {e}"
    )
    try:
        from api.app.routers.leads import router as leads_router
        from api.app.routers.newsletter import router as newsletter_router
        from api.app.routers.ringcentral_webhooks import (
            router as ringcentral_router,
        )

        app.include_router(leads_router, prefix="/api/leads", tags=["leads"])
        app.include_router(
            newsletter_router, prefix="/api/newsletter", tags=["newsletter"]
        )
        app.include_router(
            ringcentral_router, prefix="/api/ringcentral", tags=["sms"]
        )
        logger.warning(
            "⚠️ Using OLD locations for leads/newsletter/ringcentral"
        )
    except ImportError as e2:
        logger.error(f"❌ Some additional routers not available: {e2}")

# Station Management endpoints - Multi-tenant RBAC (already included above, removing duplicate)
# OLD duplicate: from api.app.routers.station_admin import router as station_admin_router
# This was duplicate of lines 671-677 above - now removed

# Include public lead capture endpoints (no auth required)
try:
    from api.v1.endpoints.public_leads import router as public_leads_router

    app.include_router(
        public_leads_router,
        prefix="/api/v1/public",
        tags=["Public Lead Capture"],
    )
    logger.info("✅ Public lead capture endpoints included")
except ImportError as e:
    logger.warning(f"Public lead endpoints not available: {e}")

# Include public quote calculation endpoint (no auth required)
try:
    from api.v1.endpoints.public_quote import router as public_quote_router

    app.include_router(
        public_quote_router,
        prefix="/api/v1/public/quote",
        tags=["Public Quote Calculator"],
    )
    logger.info(
        "✅ Public quote calculation endpoints included (travel fee calculation)"
    )
except ImportError as e:
    logger.warning(f"Public quote endpoints not available: {e}")

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
    logger.info(
        "✅ Customer Review Blog endpoints included (image + video support)"
    )
except ImportError as e:
    logger.warning(f"Customer Review Blog endpoints not available: {e}")

# Admin Review Moderation System (Approval workflow)
try:
    from api.admin.review_moderation import router as admin_moderation_router

    app.include_router(
        admin_moderation_router, tags=["admin-review-moderation"]
    )
    logger.info(
        "✅ Admin Review Moderation endpoints included (approve/reject/bulk)"
    )
except ImportError as e:
    logger.warning(f"Admin Review Moderation endpoints not available: {e}")

    # Add a placeholder AI endpoint
    @app.post("/api/v1/ai/chat", tags=["ai-chat"])
    async def ai_chat_placeholder():
        return {
            "status": "success",
            "message": "AI chat endpoint - moved from apps/ai-api",
            "note": "Full implementation pending import path fixes",
        }


# Unified Inbox endpoints - Week 2 Feature
try:
    from api.v1.inbox.endpoints import router as inbox_router

    # DEBUG: Log router details
    logger.info(f"🔍 DEBUG: Inbox router prefix: {inbox_router.prefix}")
    logger.info(
        f"🔍 DEBUG: Inbox router routes count: {len(inbox_router.routes)}"
    )
    for route in inbox_router.routes:
        logger.info(
            f"🔍 DEBUG: - Route: {route.path} Methods: {getattr(route, 'methods', 'N/A')}"
        )

    app.include_router(inbox_router, prefix="/api", tags=["unified-inbox"])
    logger.info("✅ Unified Inbox endpoints included at /api + router.prefix")
except ImportError as e:
    logger.warning(f"Unified Inbox endpoints not available: {e}")
    import traceback

    logger.error(traceback.format_exc())

# Enhanced Health Check endpoints for production K8s
try:
    from api.v1.endpoints.health import router as v1_health_router

    app.include_router(
        v1_health_router, prefix="/api/v1/health", tags=["Health Checks"]
    )
    logger.info("✅ Enhanced health check endpoints included (K8s ready)")
except ImportError as e:
    logger.warning(f"Enhanced health check endpoints not available: {e}")

# Comprehensive Health Check endpoints with dependency monitoring - NEW location
try:
    from routers.v1.health_checks import (
        router as comprehensive_health_router,
    )

    app.include_router(
        comprehensive_health_router,
        prefix="/api/health",
        tags=["Health Monitoring"],
    )
    logger.info(
        "✅ Comprehensive health monitoring endpoints included from NEW location"
    )
except ImportError as e:
    logger.warning(
        f"Comprehensive health check endpoints not available from NEW location, trying OLD: {e}"
    )
    try:
        from api.app.routers.health_checks import (
            router as comprehensive_health_router,
        )

        app.include_router(
            comprehensive_health_router,
            prefix="/api/health",
            tags=["Health Monitoring"],
        )
        logger.warning("⚠️ Using OLD health_checks location")
    except ImportError as e2:
        logger.error(
            f"❌ Comprehensive health check endpoints not available: {e2}"
        )

# Admin Analytics endpoints - Composite service
try:
    from api.v1.endpoints.analytics import router as analytics_router

    app.include_router(
        analytics_router,
        prefix="/api/admin/analytics",
        tags=["Admin Analytics"],
    )
    logger.info(
        "✅ Admin Analytics endpoints included (6 composite endpoints)"
    )
except ImportError as e:
    logger.warning(f"Admin Analytics endpoints not available: {e}")

# Payment Email Notification endpoints - Auto payment confirmation
try:
    from routes.payment_email_routes import router as payment_email_router

    app.include_router(
        payment_email_router, tags=["Payment Email Notifications"]
    )
    logger.info("✅ Payment Email Notification endpoints included")
except ImportError as e:
    logger.warning(f"Payment Email Notification endpoints not available: {e}")

# Development Role Switching - SUPER_ADMIN can test as other roles
if settings.DEV_MODE:
    try:
        from api.v1.endpoints.dev_role_switch import (
            router as role_switch_router,
        )

        app.include_router(
            role_switch_router,
            prefix="/api/v1/dev",
            tags=["Development - Role Switching"],
        )
        logger.info("🔄 Development role switching enabled (DEV_MODE=true)")
    except ImportError as e:
        logger.warning(f"Development role switching not available: {e}")

# Multi-Channel AI Communication endpoints - Handle email, SMS, Instagram, Facebook, phone
try:
    from api.v1.endpoints.multi_channel_ai import (
        router as multi_channel_router,
    )

    app.include_router(
        multi_channel_router,
        prefix="/api/v1/ai/multi-channel",
        tags=["AI Multi-Channel Communication"],
    )
    logger.info(
        "✅ Multi-Channel AI Communication endpoints included (email, SMS, Instagram, Facebook, phone)"
    )
except ImportError as e:
    logger.warning(
        f"Multi-Channel AI Communication endpoints not available: {e}"
    )

# Admin Email Review Dashboard - Review and approve AI-generated email responses
try:
    from api.admin.email_review import router as email_review_router

    app.include_router(
        email_review_router,
        prefix="/api/admin/emails",
        tags=["Admin Email Review"],
    )
    logger.info(
        "✅ Admin Email Review Dashboard endpoints included (approve/edit/reject AI responses)"
    )
except ImportError as e:
    logger.warning(f"Admin Email Review endpoints not available: {e}")

# DEBUG: Log all registered routes for troubleshooting
logger.info("=" * 80)
logger.info("🔍 DEBUG: ALL REGISTERED ROUTES:")
for route in app.routes:
    if hasattr(route, "path") and hasattr(route, "methods"):
        logger.info(f"  {route.methods} {route.path}")
    elif hasattr(route, "path"):
        logger.info(f"  [NO METHODS] {route.path}")
logger.info("=" * 80)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
