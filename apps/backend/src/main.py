"""
FastAPI Main Application - Enhanced with Dependency Injection
Unified API with operational and AI endpoints, enterprise architecture patterns
"""

# ==============================================
# STARTUP DEBUG LOGGING - Confirm module loaded
# This file write happens at module import time
# ==============================================
import os as _os_debug
import time as _time_debug

_startup_debug_file = _os_debug.path.join(
    _os_debug.path.dirname(__file__), "STARTUP_DEBUG.log"
)
with open(_startup_debug_file, "w") as _f:
    _f.write(f"MAIN.PY LOADED AT: {_time_debug.strftime('%Y-%m-%d %H:%M:%S')}\n")
    _f.write("This file proves the server loaded the latest main.py code\n")
# ==============================================

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager

# Import Sentry for error tracking and performance monitoring
import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Import Prometheus for metrics
from prometheus_client import make_wsgi_app
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Import SlowAPI for secondary rate limiting layer
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.wsgi import WSGIMiddleware

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
from core.security_middleware import RequestSizeLimiter, SecurityHeadersMiddleware

# Import our new architectural components
from core.service_registry import create_service_container

# Import sd-notify for enterprise systemd integration
# This enables proper watchdog support and service readiness signaling
try:
    import sdnotify

    SDNOTIFY_AVAILABLE = True
except ImportError:
    SDNOTIFY_AVAILABLE = False


# Custom operation ID generator to avoid duplicates when routers are mounted at multiple prefixes
# Industry standard approach for FastAPI multi-mount scenarios
from fastapi.routing import APIRoute


def generate_unique_operation_id(route: APIRoute, prefix: str = "") -> str:
    """
    Generate a unique operation ID for a route, incorporating the prefix.

    This is necessary when the same router is mounted at multiple prefixes
    (e.g., /api/leads and /api/v1/public/leads) to avoid duplicate operation IDs.

    Args:
        route: The FastAPI route
        prefix: The URL prefix where this router is mounted

    Returns:
        A unique operation ID string
    """
    # Clean the prefix for use in operation ID
    clean_prefix = prefix.strip("/").replace("/", "_").replace("-", "_")
    operation_id = route.name
    if clean_prefix:
        return f"{clean_prefix}_{operation_id}"
    return operation_id


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
        profiles_sample_rate=getattr(settings, "sentry_profiles_sample_rate", 1.0),
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
    logger.debug("Sentry DSN not configured - monitoring disabled (OK for development)")

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

    # Initialize Google Secret Manager (Phase 1A: GSM Integration)
    try:
        logger.info("🔐 Initializing Google Secret Manager...")
        gsm_status = await settings.initialize_gsm()

        if gsm_status.get("status") == "success":
            logger.info(
                f"✅ GSM initialized: {gsm_status.get('secrets_from_gsm', 0)} secrets from GSM, "
                f"{gsm_status.get('secrets_from_env', 0)} from environment"
            )
        elif gsm_status.get("status") == "env_only":
            logger.info(
                "✅ GSM not available - using environment variables only (OK for dev)"
            )
        else:
            logger.warning(
                f"⚠️ GSM initialization failed - using environment variables: "
                f"{gsm_status.get('error', 'unknown')}"
            )
    except Exception as e:
        logger.warning(
            f"⚠️ GSM initialization error: {e} - using environment variables"
        )

    # ============================================================
    # Email Credential Validation (Batch 1 - Full Redundancy)
    # Validates email credentials on startup to catch configuration
    # issues EARLY before email monitors fail silently
    # ============================================================
    email_config_issues = []

    # Gmail credentials (payment email notifications)
    gmail_user = os.getenv("GMAIL_USER")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_user:
        email_config_issues.append(
            "GMAIL_USER is missing - payment email monitor will fail"
        )
    if not gmail_app_password:
        email_config_issues.append(
            "GMAIL_APP_PASSWORD is missing - payment email monitor will fail"
        )

    # IONOS credentials (customer support email)
    ionos_password = os.getenv("SMTP_PASSWORD")
    if not ionos_password:
        email_config_issues.append(
            "SMTP_PASSWORD is missing - IONOS email monitor will fail"
        )

    # Log validation results
    if email_config_issues:
        for issue in email_config_issues:
            logger.warning(f"⚠️ EMAIL CONFIG: {issue}")
        logger.warning(
            "⚠️ EMAIL MONITORS MAY NOT FUNCTION CORRECTLY - "
            f"Found {len(email_config_issues)} configuration issue(s). "
            "Check .env file and restart after fixing."
        )
    else:
        logger.info(
            "✅ Email credentials validated: Gmail (payment) + IONOS (support) ready"
        )

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
        logger.warning("⚠️ Cache service connection timeout - continuing without cache")
        app.state.cache = None
    except Exception as e:
        logger.warning(f"⚠️ Cache service unavailable: {e} - continuing without cache")
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
        from services.payment_email_scheduler import start_payment_email_scheduler

        # Start in background - don't wait for first email check
        start_payment_email_scheduler()
        logger.info("✅ Payment email monitoring scheduler started")
    except ImportError as e:
        logger.warning(
            f"⚠️ Payment email scheduler not available (missing dependencies): {e}"
        )
    except Exception as e:
        logger.warning(f"⚠️ Payment email scheduler not available: {e}")

    # Start email notification scheduler (WhatsApp alerts for new emails)
    try:
        from tasks.email_notification_task import start_email_notification_task

        # Start in background - checks for new emails every 60s
        asyncio.create_task(start_email_notification_task())
        logger.info("✅ Email notification scheduler started (WhatsApp alerts enabled)")
    except ImportError as e:
        logger.warning(
            f"⚠️ Email notification scheduler not available (missing dependencies): {e}"
        )
    except Exception as e:
        logger.warning(f"⚠️ Email notification scheduler not available: {e}")

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
        logger.warning(f"⚠️ AI Orchestrator not available (missing dependencies): {e}")
        app.state.orchestrator = None
    except Exception as e:
        logger.warning(f"⚠️ AI Orchestrator initialization failed: {e}")
        app.state.orchestrator = None

    # Initialize outbox processor workers (CQRS + Event Sourcing) - NEW location
    if getattr(settings, "WORKERS_ENABLED", False):
        try:
            from workers.outbox_processors import create_outbox_processor_manager

            worker_configs = getattr(settings, "get_worker_configs", lambda: {})()
            worker_manager = create_outbox_processor_manager(worker_configs)
            await worker_manager.start_all()
            app.state.worker_manager = worker_manager
            logger.info(
                "✅ Outbox processor workers started from NEW location (CQRS + Event Sourcing)"
            )
        except ImportError as e:
            logger.warning(f"⚠️ Outbox processors not available: {e}")
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

    # Notify systemd that service is ready (enterprise-standard)
    # This enables proper watchdog support and prevents premature service kills
    if SDNOTIFY_AVAILABLE:
        try:
            notifier = sdnotify.SystemdNotifier()
            notifier.notify("READY=1")
            notifier.notify("STATUS=Application ready and accepting requests")
            logger.info("✅ Notified systemd: service ready")

            # Start watchdog ping task if WatchdogSec is configured
            # This keeps the service alive by sending periodic WATCHDOG=1 signals
            watchdog_usec = os.environ.get("WATCHDOG_USEC")
            if watchdog_usec:
                watchdog_interval = (
                    int(watchdog_usec) / 1_000_000 / 2
                )  # Half the timeout

                async def watchdog_ping():
                    """Send periodic watchdog pings to systemd."""
                    while True:
                        try:
                            notifier.notify("WATCHDOG=1")
                            await asyncio.sleep(watchdog_interval)
                        except Exception:
                            break

                # Start watchdog task in background
                asyncio.create_task(watchdog_ping())
                logger.info(
                    f"✅ Systemd watchdog ping enabled (interval: {watchdog_interval:.1f}s)"
                )
        except Exception as e:
            logger.warning(f"⚠️ sd-notify failed: {e} (non-fatal, continuing)")

    yield

    # Shutdown
    logger.info("🛑 Starting graceful shutdown...")

    # Notify systemd of stopping state
    if SDNOTIFY_AVAILABLE:
        try:
            notifier = sdnotify.SystemdNotifier()
            notifier.notify("STOPPING=1")
            notifier.notify("STATUS=Graceful shutdown in progress")
        except Exception:
            pass  # Non-fatal during shutdown

    # Stop real-time voice call sessions
    try:
        from services.realtime_voice.call_session import call_session_manager

        active_sessions = list(call_session_manager.active_sessions.values())
        if active_sessions:
            logger.info(
                f"📞 Gracefully closing {len(active_sessions)} active voice calls..."
            )

            for session in active_sessions:
                try:
                    # Stop STT bridge
                    if session.stt_bridge and session.stt_bridge.is_running:
                        session.stt_bridge.stop()
                        logger.info(f"✅ Stopped STT bridge for call {session.call_id}")

                    # Close WebSocket
                    if session.websocket:
                        try:
                            await session.websocket.close(
                                code=1001, reason="Server shutdown"
                            )
                            logger.info(
                                f"✅ Closed WebSocket for call {session.call_id}"
                            )
                        except Exception as ws_error:
                            logger.debug(f"WebSocket already closed: {ws_error}")

                    # Mark session ended and save logs
                    session.mark_ended()
                    logger.info(
                        f"✅ Call {session.call_id} ended gracefully | "
                        f"duration={session.get_duration():.1f}s | "
                        f"transcripts={session.transcripts_count} | "
                        f"turns={session.turn_count}"
                    )

                except Exception as session_error:
                    logger.error(
                        f"Error closing session {session.call_id}: {session_error}"
                    )

            # Final cleanup
            await call_session_manager.cleanup_all_sessions()

            stats = call_session_manager.get_stats()
            logger.info(
                f"📊 Voice AI final stats | "
                f"total_calls={stats['total_calls']} | "
                f"completed={stats['completed_calls']} | "
                f"failed={stats['failed_calls']} | "
                f"success_rate={stats['success_rate']:.2%}"
            )
        else:
            logger.info("✅ No active voice calls to close")

    except ImportError:
        logger.debug("Real-time voice module not imported")
    except Exception as e:
        logger.error(f"Error during voice call shutdown: {e}")

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
        from services.payment_email_scheduler import stop_payment_email_scheduler

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


# ============================================================================
# ASGI debug middleware temporarily disabled - was causing RuntimeError
# See: asgi_exception.log for previous logs
logger.info("⚠️ ASGI exception logger middleware DISABLED (was causing RuntimeError)")

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

    # FILE-BASED DEBUG LOGGING - Write exception to file for debugging
    import traceback

    debug_file = os.path.join(os.path.dirname(__file__), "exception_debug.log")
    with open(debug_file, "a") as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"EXCEPTION at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Request: {request.method} {request.url}\n")
        f.write(f"Exception: {type(exc).__name__}: {exc}\n")
        f.write(f"Traceback:\n{traceback.format_exc()}\n")
        f.write(f"{'='*60}\n")

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


logger.info("✅ Custom exception handlers registered (with Sentry integration)")

# ============================================================================
# MIDDLEWARE REGISTRATION ORDER (CRITICAL!)
# ============================================================================
# Starlette/FastAPI middleware runs in REVERSE order of registration:
# - FIRST registered = runs LAST for incoming requests
# - LAST registered = runs FIRST for incoming requests
#
# For CORS to work, CORSMiddleware must be registered LAST so it can
# intercept OPTIONS preflight requests BEFORE any other middleware
# potentially rejects them (like RateLimitMiddleware returning 405).
#
# Current registration order (bottom = runs first for incoming requests):
# 1. RequestIDMiddleware (registered first → runs LAST)
# 2. StructuredLoggingMiddleware
# 3. SecurityHeadersMiddleware
# 4. RequestSizeLimiter
# 5. GZipMiddleware
# 6. CachingMiddleware
# 7. RateLimitMiddleware
# 8. CORSMiddleware (registered LAST → runs FIRST for OPTIONS handling)
#
# FIX 2025-01-30: CORS must be registered LAST to run FIRST!
# ============================================================================

# Request ID Middleware (runs last for incoming, first for outgoing)
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
logger.info("✅ Security headers middleware registered (HSTS, CSP, X-Frame-Options)")

# Request Size Limiter (PREVENT DOS ATTACKS)
app.add_middleware(RequestSizeLimiter, max_size=10 * 1024 * 1024)  # 10 MB limit
logger.info("✅ Request size limiter registered (10 MB maximum)")

# GZip Compression Middleware (PERFORMANCE)
app.add_middleware(GZipMiddleware, minimum_size=500)  # Compress responses > 500 bytes
logger.info("✅ GZip compression middleware registered (min size: 500 bytes)")

# Caching Middleware (PERFORMANCE - Cache-Control headers)
# NOTE: Must be registered BEFORE CORS so CORS runs FIRST
try:
    from middleware.caching import CachingMiddleware

    app.add_middleware(CachingMiddleware, enable_etag=True)
    logger.info("✅ Caching middleware registered (Cache-Control headers + ETag)")
except ImportError:
    logger.warning("⚠️ Caching middleware not available")

# Login Rate Limiting Middleware (SECURITY - Brute Force Protection)
# This provides login-specific protection: 3 failed attempts = 1-hour lockout
# NOTE: Must be registered BEFORE CORS so CORS runs FIRST
try:
    from middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware, redis_url=settings.redis_url)
    logger.info(
        "✅ Login rate limit middleware registered (3 attempts, 1-hour lockout)"
    )
except ImportError as e:
    logger.warning(f"⚠️ Login rate limit middleware not available: {e}")
except Exception as e:
    logger.error(f"❌ Failed to register login rate limit middleware: {e}")

# Audit Logging Middleware (SECURITY - Log all admin actions)
# Must be registered BEFORE CORS so it runs AFTER request processing
try:
    from middleware.audit_middleware import AuditMiddleware

    app.add_middleware(AuditMiddleware)
    logger.info(
        "✅ Audit middleware registered - logging all admin POST/PUT/PATCH/DELETE actions"
    )
except ImportError as e:
    logger.warning(f"⚠️ Audit middleware not available: {e}")
except Exception as e:
    logger.error(f"❌ Failed to register audit middleware: {e}")

# CORS Middleware (MUST BE REGISTERED LAST to run FIRST!)
# ============================================================================
# CRITICAL: In Starlette/FastAPI, middleware runs in REVERSE order:
# - LAST registered = runs FIRST for incoming requests
# - CORS must intercept OPTIONS preflight BEFORE any other middleware
#   (like RateLimitMiddleware) can reject the request with 405/401
#
# FIX APPLIED 2025-01-30: Moved CORS to be registered LAST to fix:
# - OPTIONS returning 405 instead of 200/204 with CORS headers
# - Missing Access-Control-Allow-Origin on error responses
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
        "OPTIONS",
    ],  # Explicit OPTIONS
    allow_headers=["*"],
)
logger.info(
    f"✅ CORS middleware registered LAST (runs FIRST) for origins: {settings.cors_origins_list}"
)


# OLD General Rate Limiting Middleware - DISABLED
# This was causing conflicts with the new RateLimitMiddleware (login protection).
# The new RateLimitMiddleware from middleware/rate_limit.py handles login brute-force
# protection (3 attempts = 1-hour lockout). The old tier-based rate limiting is
# disabled for now. If needed, it can be integrated into the new middleware.
# app.state.rate_limiter is still initialized for health check diagnostics.
#
# @app.middleware("http")
# async def rate_limiting_middleware(request: Request, call_next):
#     """Rate limiting middleware wrapper - DISABLED to avoid conflict"""
#     ...
# See git history for full implementation if needed.


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
        "docs": ("/docs" if settings.DEBUG else "Documentation disabled in production"),
    }


@app.get("/health", tags=["Health"])
async def health_check(request: Request):
    """Health check endpoint for load balancers"""
    # Check DI container status
    di_status = (
        "available"
        if hasattr(request.app.state, "container") and request.app.state.container
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
            booking_repo_available = container.is_registered("booking_repository")
            customer_repo_available = container.is_registered("customer_repository")
            db_session_available = container.is_registered("database_session")

            health_data["services"] = {
                "booking_repository": (
                    "available" if booking_repo_available else "not_registered"
                ),
                "customer_repository": (
                    "available" if customer_repo_available else "not_registered"
                ),
                "database_session": (
                    "available" if db_session_available else "not_registered"
                ),
            }
        except Exception as e:
            health_data["services"] = {"error": f"Service resolution failed: {e!s}"}

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
    from api.v1.endpoints.user_management import router as user_management_router

    app.include_router(user_management_router, tags=["User Management"])
    logger.info("✅ User Management endpoints included")
except ImportError as e:
    logger.warning(f"User Management endpoints not available: {e}")

# Include Role Management endpoints (Super Admin)
try:
    from api.v1.endpoints.role_management import router as role_management_router

    app.include_router(role_management_router, tags=["Role Management"])
    logger.info("✅ Role Management endpoints included")
except ImportError as e:
    logger.warning(f"Role Management endpoints not available: {e}")

# Include Payment Calculator endpoints (for fee calculations)
try:
    from api.v1.endpoints.payment_calculator import router as payment_calculator_router

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
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings-v1"])

# Include PUBLIC booking endpoints (no auth required - for customer website)
try:
    from routers.v1.public_bookings import router as public_bookings_router

    app.include_router(
        public_bookings_router,
        prefix="/api/v1/public/bookings",
        tags=["public-bookings"],
    )
    logger.info("✅ Public booking endpoints included (no auth - customer website)")
except ImportError as e:
    logger.warning(f"Public booking endpoints not available: {e}")

# Include PUBLIC quote endpoints (no auth required - for customer website)
try:
    from routers.v1.public_quote import router as public_quote_router

    app.include_router(
        public_quote_router,
        prefix="/api/v1/public/quote",
        tags=["public-quote"],
    )
    logger.info("✅ Public quote endpoints included (no auth - customer website)")
except ImportError as e:
    logger.warning(f"Public quote endpoints not available: {e}")

# Include PUBLIC config endpoints (no auth required - for customer website SSoT)
# These endpoints serve dynamic business config to frontend hooks (useConfig, usePolicies)
try:
    from routers.v1.public_config import router as public_config_router

    app.include_router(public_config_router, prefix="/api/v1", tags=["public-config"])
    logger.info(
        "✅ Public config endpoints included (no auth - SSoT for customer website)"
    )
except ImportError as e:
    logger.warning(f"Public config endpoints not available: {e}")

# Include PUBLIC contact form endpoint (no auth required - website contact form)
try:
    from routers.v1.contact import router as contact_router

    app.include_router(contact_router, prefix="/api/v1/contact", tags=["contact"])
    logger.info("✅ Contact form endpoint included (no auth - website contact)")
except ImportError as e:
    logger.warning(f"Contact form endpoint not available: {e}")

# Include v1 API router (pricing, menu items, addon items)
try:
    from api.v1.api import api_router as v1_api_router

    app.include_router(v1_api_router, prefix="/api/v1")
    logger.info("✅ V1 API endpoints included (pricing, menu items, addon items)")
except ImportError as e:
    logger.warning(f"V1 API endpoints not available: {e}")

# Include Booking Reminders endpoints (Sprint 1 - Feature Flag: BOOKING_REMINDERS)
try:
    from routers.v1.booking_reminders import router as booking_reminders_router

    app.include_router(
        booking_reminders_router, prefix="/api/v1", tags=["booking-reminders"]
    )
except ImportError:
    pass

# Include Smart Scheduling endpoints (Phase 1 - Travel-optimized chef assignment)
try:
    from routers.v1.scheduling import router as scheduling_router

    app.include_router(scheduling_router, prefix="/api/v1", tags=["scheduling"])
    logger.info(
        "✅ Smart Scheduling endpoints included (availability, chef assignment)"
    )
except ImportError as e:
    logger.warning(f"Smart Scheduling endpoints not available: {e}")

# Include Chef Portal endpoints (Chef self-service availability + Station Manager oversight)
try:
    from routers.v1.chef_portal import router as chef_portal_router

    app.include_router(chef_portal_router, prefix="/api/v1", tags=["chef-portal"])
    logger.info(
        "✅ Chef Portal endpoints included (chef availability, time-off requests)"
    )
except ImportError as e:
    logger.warning(f"Chef Portal endpoints not available: {e}")

# Include Chef Pay endpoints (Chef earnings calculation + Station Manager/Admin oversight)
try:
    from routers.v1.chef_pay import router as chef_pay_router

    app.include_router(chef_pay_router, prefix="/api/v1", tags=["chef-pay"])
    logger.info(
        "✅ Chef Pay endpoints included (earnings calculation, pay rate management)"
    )
except ImportError as e:
    logger.warning(f"Chef Pay endpoints not available: {e}")

# Include Customer Preferences endpoints (Chef request tracking + Allergen capture)
try:
    from routers.v1.customer_preferences import router as customer_preferences_router

    app.include_router(
        customer_preferences_router, prefix="/api/v1", tags=["customer-preferences"]
    )
    logger.info(
        "✅ Customer Preferences endpoints included (chef request, allergen disclosure)"
    )
except ImportError as e:
    logger.warning(f"Customer Preferences endpoints not available: {e}")

# Include Legal Agreements endpoints (Batch 1.x - Liability waiver, allergen disclosure)
try:
    from routers.v1.agreements import router as agreements_router

    app.include_router(agreements_router, prefix="/api/v1", tags=["agreements"])
    logger.info(
        "✅ Legal Agreements endpoints included (liability waiver, allergen disclosure, slot holds)"
    )
except ImportError as e:
    logger.warning(f"Legal Agreements endpoints not available: {e}")

# Include Address Management endpoints (Enterprise geocoding with caching)
try:
    from routers.v1.addresses import router as addresses_router

    app.include_router(addresses_router, prefix="/api/v1", tags=["addresses"])
    logger.info("✅ Address Management endpoints included (geocoding, saved addresses)")
except ImportError as e:
    logger.warning(f"Address Management endpoints not available: {e}")

# Include Knowledge Sync endpoints (Admin/Superadmin)
try:
    from routers.v1.knowledge_sync import router as knowledge_sync_router

    app.include_router(knowledge_sync_router, tags=["Knowledge Sync"])
    logger.info("✅ Knowledge Sync endpoints included")
except ImportError as e:
    logger.warning(f"Knowledge Sync endpoints not available: {e}")

# Stripe router from NEW location
# Tables created in migration 017_stripe_tables.sql
try:
    from routers.v1.stripe import router as stripe_router

    app.include_router(stripe_router, prefix="/api/v1/stripe", tags=["stripe"])

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
        customer_id: str = None,
        email: str = None,
        request: Request = None,
    ):
        """Compatibility endpoint - uses Stripe customer_id or email"""
        from routers.v1.stripe import get_customer_dashboard_by_stripe_id

        return await get_customer_dashboard_by_stripe_id(
            customer_id=customer_id, email=email
        )

    app.include_router(customer_compat_router, prefix="/api")
    logger.info(
        "✅ Stripe router included from NEW location with customer compatibility endpoints"
    )
except ImportError as e_stripe:
    logger.error(f"❌ Stripe router not available: {e_stripe}")

# CRM Router - Admin Panel Integration Layer (re-enabled for admin frontend sync)
try:
    from routers.v1.crm import router as crm_router

    app.include_router(crm_router, prefix="/api/crm", tags=["crm", "admin"])
    logger.info("✅ CRM router included (Admin Panel Integration Layer)")
except ImportError as e:
    logger.error(f"❌ CRM router not available: {e}")

# Station Management and Authentication (Multi-tenant RBAC) - NEW location
try:
    from routers.v1.station_admin import router as station_admin_router
    from routers.v1.station_auth import router as station_auth_router

    app.include_router(
        station_auth_router, prefix="/api/station", tags=["station-auth"]
    )
    app.include_router(
        station_admin_router,
        prefix="/api/v1/admin/stations",
        tags=["station-admin"],
    )
    logger.info(
        "✅ Station Management and Auth endpoints included from NEW location (Multi-tenant RBAC)"
    )
except ImportError as e:
    logger.error(f"❌ Station Auth endpoints not available: {e}")

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
    logger.error(f"❌ Enhanced Booking Admin endpoints not available: {e}")

# Payment Analytics (separate router for /api/payments/analytics) - NEW location
try:
    from routers.v1.payments import router as payments_router

    app.include_router(
        payments_router, prefix="/api/payments", tags=["payment-analytics"]
    )
    logger.info("✅ Payment Analytics endpoints included from NEW location")
except ImportError as e:
    logger.error(f"❌ Payment Analytics endpoints not available: {e}")

# Real-time Voice WebSocket endpoints - NEW location
try:
    from routers.v1.realtime_voice import router as realtime_voice_router

    app.include_router(realtime_voice_router, tags=["Voice - Real-time"])
    logger.info("✅ Real-time Voice WebSocket endpoints included")
except ImportError as e:
    logger.error(f"❌ Real-time Voice endpoints not available: {e}")

# QR Code Tracking System - DELETED (Nov 22, 2025)
# Not needed for hibachi catering business model
# Files removed: routers/v1/qr_tracking.py, services/qr_tracking_service.py

# Admin Dynamic Config (SSoT for pricing, policies, business rules)
try:
    from routers.v1.admin.config import router as admin_config_router

    app.include_router(
        admin_config_router,
        prefix="/api",
        tags=["admin", "config", "ssot"],
    )
    logger.info("✅ Admin Config endpoints included (dynamic variables SSoT)")
except ImportError as e:
    logger.error(f"❌ Admin Config endpoints not available: {e}")

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
    logger.error(f"❌ Admin Error Logs endpoints not available: {e}")

# Admin Audit Logs (comprehensive system activity logging for super admins)
try:
    from routers.v1.admin.audit_logs import router as audit_logs_router

    app.include_router(
        audit_logs_router,
        prefix="/api/v1/admin/audit-logs",
        tags=["admin", "audit-logs", "superadmin"],
    )
    logger.info("✅ Admin Audit Logs endpoints included")
except ImportError as e:
    logger.error(f"❌ Admin Audit Logs endpoints not available: {e}")

# Staff Invitations (role-based invitation system)
try:
    from routers.v1.admin.invitations import router as invitations_router

    app.include_router(
        invitations_router,
        prefix="/api/v1/admin/invitations",
        tags=["admin", "invitations", "staff"],
    )
    logger.info("✅ Staff Invitations endpoints included")
except ImportError as e:
    logger.error(f"❌ Staff Invitations endpoints not available: {e}")

# Notification Groups Admin - NEW location
try:
    from routers.v1.admin.notification_groups import (
        router as notification_groups_router,
    )

    app.include_router(
        notification_groups_router,
        prefix="/api/v1/admin/notification-groups",
        tags=["admin", "notifications"],
    )
    logger.info("✅ Notification Groups Admin included from NEW location")
except ImportError as e:
    logger.error(f"❌ Notification Groups endpoints not available: {e}")

# Admin Analytics (comprehensive) - NEW location
try:
    from routers.v1.admin_analytics import router as admin_analytics_router

    app.include_router(
        admin_analytics_router, prefix="/api", tags=["admin", "analytics"]
    )
    logger.info("✅ Admin Analytics endpoints included from NEW location")
except ImportError as e:
    logger.error(f"❌ Admin Analytics endpoints not available: {e}")

# VPS Security Monitoring (fail2ban/firewalld status, banned IPs) - NEW
try:
    from routers.v1.vps_security import router as vps_security_router

    app.include_router(
        vps_security_router, prefix="/api/admin", tags=["admin", "vps-security"]
    )
    logger.info("✅ VPS Security Monitoring endpoints included (fail2ban/firewalld)")
except ImportError as e:
    logger.error(f"❌ VPS Security Monitoring endpoints not available: {e}")

# Admin Email Management (Gmail-style interface for 2 inboxes) - NEW
try:
    from routers.v1.admin_emails import router as admin_emails_router

    app.include_router(admin_emails_router, prefix="/api/v1", tags=["admin", "emails"])
    logger.info("✅ Admin Email Management endpoints included (cs@ + gmail)")
except ImportError as e:
    logger.error(f"❌ Admin Email Management endpoints not available: {e}")

# Customer Review System (from legacy - comprehensive) - NEW location
try:
    from routers.v1.reviews import router as reviews_router

    app.include_router(
        reviews_router, prefix="/api/v1/reviews", tags=["reviews", "feedback"]
    )
    logger.info(
        "✅ Customer Review System included from NEW location (legacy comprehensive version)"
    )
except ImportError as e:
    logger.error(f"❌ Customer Review System endpoints not available: {e}")

# Monitoring Alert Rules API (Admin only - dynamic rule management) - DISABLED (broken import)
# try:
#     from routers.v1.monitoring_rules import router as monitoring_rules_router
#     app.include_router(monitoring_rules_router, prefix="/api/v1", tags=["monitoring"])
#     logger.info("✅ Monitoring Alert Rules API included (admin rule management)")
# except ImportError as e:
#     logger.error(f"❌ Monitoring Alert Rules API not available: {e}")

# Knowledge Sync API (Superadmin only - dynamic menu/FAQ/terms sync)
try:
    from api.v1.knowledge_sync.router import router as knowledge_sync_router

    app.include_router(
        knowledge_sync_router,
        prefix="/api/v1/knowledge",
        tags=["knowledge-sync"],
    )
    logger.info("✅ Knowledge Sync API included (menu/FAQ/terms auto-sync)")
except ImportError as e:
    logger.error(f"❌ Knowledge Sync API not available: {e}")

# Try to include additional routers if available - NEW locations
try:
    from routers.v1.campaigns import router as campaigns_router
    from routers.v1.conversations import router as conversations_router
    from routers.v1.leads import router as leads_router
    from routers.v1.newsletter import analytics_router as newsletter_analytics_router
    from routers.v1.newsletter import router as newsletter_router
    from routers.v1.referrals import router as referrals_router
    from routers.v1.ringcentral_webhooks import router as ringcentral_router

    app.include_router(leads_router, prefix="/api/leads", tags=["leads"])
    # Use generate_unique_id_function for second mount to avoid duplicate operation IDs
    app.include_router(
        leads_router,
        prefix="/api/v1/public/leads",
        tags=["leads-public"],
        generate_unique_id_function=lambda route: generate_unique_operation_id(
            route, "public_leads"
        ),
    )  # Public endpoint
    app.include_router(newsletter_router, prefix="/api/newsletter", tags=["newsletter"])
    app.include_router(
        newsletter_analytics_router,
        prefix="/api",
        tags=["newsletter-analytics"],
    )
    app.include_router(ringcentral_router, prefix="/api/ringcentral", tags=["sms"])
    app.include_router(conversations_router, prefix="/api/v1", tags=["conversations"])
    app.include_router(referrals_router, prefix="/api/v1", tags=["referrals"])
    app.include_router(campaigns_router, prefix="/api/v1", tags=["campaigns"])
    logger.info(
        "✅ All CRM routers included (leads, newsletter, campaigns, referrals, SMS, conversations)"
    )
except ImportError as e:
    logger.error(f"❌ Some additional routers not available: {e}")

# Station Management endpoints - Multi-tenant RBAC (already included above, removing duplicate)
# OLD duplicate: from api.app.routers.station_admin import router as station_admin_router
# This was duplicate of lines 671-677 above - now removed

# AI Chat endpoints from moved AI API
# NOTE: Removed duplicate mount - ai_chat_router was conflicting with chat.router from api/v1/api.py
# Both were mounting at /api/v1/ai/chat causing duplicate operation ID warnings.
# The chat.router from api/v1/endpoints/ai/chat.py is already included via v1_api_router.
# If the real AI chat implementation is needed, consider using a different prefix like /api/v2/ai/chat
# or removing the mock implementation from api/v1/endpoints/ai/chat.py


# AI WebSocket endpoints (real-time chat)
try:
    from api.ai.endpoints.routers.websocket import router as ai_websocket_router

    app.include_router(ai_websocket_router, prefix="/api/v1", tags=["ai-websocket"])
    logger.info("✅ AI WebSocket endpoints included (/api/v1/ws/chat)")
except ImportError as e:
    logger.warning(f"AI WebSocket endpoints not available: {e}")


# NLP Monitoring endpoints
try:
    from api.ai.endpoints.routers.nlp_monitoring import router as nlp_monitoring_router

    app.include_router(
        nlp_monitoring_router, prefix="/api/v1/ai", tags=["nlp-monitoring"]
    )
    logger.info("✅ NLP Monitoring endpoints included")
except ImportError as e:
    logger.warning(f"NLP Monitoring endpoints not available: {e}")


# Escalation System - Customer Support Handoff
try:
    from api.v1.escalations.endpoints import router as escalations_router

    app.include_router(
        escalations_router, prefix="/api/v1/escalations", tags=["escalations"]
    )
    logger.info("✅ Escalation endpoints included (AI to human handoff)")
except ImportError as e:
    logger.warning(f"Escalation endpoints not available: {e}")

# Meta Webhooks - WhatsApp, Instagram, Facebook Messenger
try:
    from routers.v1.webhooks.meta_webhook_refactored import (
        router as meta_webhook_router,
    )

    app.include_router(
        meta_webhook_router,
        prefix="/api/v1",  # Router has /webhooks/meta prefix
        tags=["webhooks", "meta", "whatsapp"],
    )
    logger.info("✅ Meta webhook receiver included (WhatsApp, Instagram, FB Messenger)")
except ImportError as e:
    logger.warning(f"Meta webhook endpoints not available: {e}")

# RingCentral Webhooks - SMS, Call, Recording Events
try:
    from api.v1.webhooks.ringcentral import router as rc_webhook_router

    app.include_router(
        rc_webhook_router,
        prefix="/api/v1",  # Already has /webhooks/ringcentral in router definition
        tags=["webhooks"],
    )
    logger.info("✅ RingCentral webhook receiver included")
except ImportError as e:
    logger.warning(f"RingCentral webhook endpoints not available: {e}")

# RingCentral Voice Webhooks - Voice AI with Deepgram
try:
    from routers.v1.ringcentral_voice_webhooks import router as rc_voice_router

    app.include_router(
        rc_voice_router,
        prefix="/api/v1/webhooks",
        tags=["voice-ai", "webhooks"],
    )
    logger.info("✅ RingCentral Voice AI webhooks included (Deepgram STT + TTS)")
except ImportError as e:
    logger.warning(f"Voice AI endpoints not available: {e}")

# Call Recordings API - Access recordings and AI transcripts
try:
    from routers.v1.recordings import router as recordings_router

    app.include_router(
        recordings_router,
        prefix="/api/v1",  # Already has /recordings prefix in router
        tags=["recordings", "voice-ai"],
    )
    logger.info("✅ Call recordings API included (RingCentral AI transcripts)")
except ImportError as e:
    logger.warning(f"Recordings API not available: {e}")

# Escalation WebSocket - Real-time Updates
try:
    from api.v1.websockets.escalations import router as escalation_ws_router

    app.include_router(
        escalation_ws_router,
        prefix="/api/v1",  # Already has /ws/escalations in router definition
        tags=["websocket"],
    )
    logger.info("✅ Escalation WebSocket included (real-time updates)")
except ImportError as e:
    logger.warning(f"Escalation WebSocket not available: {e}")


# Compliance WebSocket - Real-time Updates
try:
    from api.v1.websockets.compliance import router as compliance_ws_router

    app.include_router(
        compliance_ws_router,
        tags=["websocket"],
    )
    logger.info("✅ Compliance WebSocket included (real-time updates)")
except ImportError as e:
    logger.warning(f"Compliance WebSocket not available: {e}")


# Unified Inbox endpoints - Week 2 Feature
try:
    from api.v1.inbox.endpoints import router as inbox_router

    # DEBUG: Log router details
    logger.info(f"🔍 DEBUG: Inbox router prefix: {inbox_router.prefix}")
    logger.info(f"🔍 DEBUG: Inbox router routes count: {len(inbox_router.routes)}")
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
    from routers.v1.health_checks import router as comprehensive_health_router

    app.include_router(
        comprehensive_health_router,
        prefix="/api/health",
        tags=["Health Monitoring"],
    )
    logger.info(
        "✅ Comprehensive health monitoring endpoints included from NEW location"
    )
except ImportError as e:
    logger.error(f"❌ Comprehensive health check endpoints not available: {e}")

# Admin Analytics endpoints - Composite service
try:
    from api.v1.endpoints.analytics import router as analytics_router

    app.include_router(
        analytics_router,
        prefix="/api/v1/admin/analytics",
        tags=["Admin Analytics"],
    )
    logger.info("✅ Admin Analytics endpoints included (6 composite endpoints)")
except ImportError as e:
    logger.warning(f"Admin Analytics endpoints not available: {e}")

# Payment Email Notification endpoints - Auto payment confirmation
try:
    from routes.payment_email_routes import router as payment_email_router

    app.include_router(payment_email_router, tags=["Payment Email Notifications"])
    logger.info("✅ Payment Email Notification endpoints included")
except ImportError as e:
    logger.warning(f"Payment Email Notification endpoints not available: {e}")

# Development Role Switching - SUPER_ADMIN can test as other roles
if settings.DEV_MODE:
    try:
        from api.v1.endpoints.dev_role_switch import router as role_switch_router

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
    from api.v1.endpoints.multi_channel_ai import router as multi_channel_router

    app.include_router(
        multi_channel_router,
        prefix="/api/v1/ai/multi-channel",
        tags=["AI Multi-Channel Communication"],
    )
    logger.info(
        "✅ Multi-Channel AI Communication endpoints included (email, SMS, Instagram, Facebook, phone)"
    )
except ImportError as e:
    logger.warning(f"Multi-Channel AI Communication endpoints not available: {e}")

# Admin Email Review Dashboard - Review and approve AI-generated email responses
try:
    from api.admin.email_review import router as email_review_router

    app.include_router(
        email_review_router,
        prefix="/api/v1/admin/emails",
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
