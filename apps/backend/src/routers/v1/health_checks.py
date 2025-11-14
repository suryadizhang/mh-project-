"""
Comprehensive Health Check Endpoints

Features:
- Liveness probe (is app running?)
- Readiness probe (is app ready to serve traffic?)
- Detailed health checks for all dependencies
- Component-level health status
- Performance metrics

Created: October 30, 2025
Author: My Hibachi Chef Development Team
"""

import asyncio
from datetime import datetime, timezone
import logging
import time

from core.database import get_db
from core.config import get_settings
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from redis import asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Phase 2A: Twilio is optional dependency - handle import gracefully
try:
    from twilio.rest import Client as TwilioClient

    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None  # type: ignore

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


class ComponentHealth(BaseModel):
    """Health status of a single component"""

    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str | None = None
    response_time_ms: int | None = None
    details: dict | None = None


class HealthResponse(BaseModel):
    """Overall health check response"""

    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    version: str
    environment: str
    uptime_seconds: int | None = None
    components: list[ComponentHealth]
    overall_response_time_ms: int


# Track application start time for uptime calculation
APP_START_TIME = time.time()


async def check_database_health(db: AsyncSession) -> ComponentHealth:
    """Check PostgreSQL database health"""
    start_time = time.time()

    try:
        # Execute simple query
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        response_time_ms = int((time.time() - start_time) * 1000)

        # Try to get pool status, but don't fail if not available
        pool_details = {}
        try:
            engine = db.get_bind()
            if hasattr(engine, "pool"):
                pool = engine.pool
                pool_details = {
                    "pool_size": pool.size(),
                    "pool_checked_in": pool.checkedin(),
                    "pool_checked_out": pool.size() - pool.checkedin(),
                }
        except Exception as pool_error:
            logger.debug(f"Could not get pool status: {pool_error}")
            pool_details = {"pool_info": "unavailable"}

        return ComponentHealth(
            name="database",
            status="healthy",
            message="Database connection successful",
            response_time_ms=response_time_ms,
            details=pool_details,
        )

    except Exception as e:
        logger.exception(f"❌ Database health check failed: {e}")
        return ComponentHealth(
            name="database",
            status="unhealthy",
            message=f"Database connection failed: {e!s}",
            response_time_ms=int((time.time() - start_time) * 1000),
        )


async def check_redis_health() -> ComponentHealth:
    """Check Redis cache health"""
    start_time = time.time()

    try:
        redis = await aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)

        # Test write/read
        test_key = "health_check_test"
        test_value = f"test_{int(time.time())}"

        await redis.set(test_key, test_value, ex=10)  # 10 second expiry
        result = await redis.get(test_key)

        await redis.delete(test_key)
        await redis.close()

        response_time_ms = int((time.time() - start_time) * 1000)

        if result == test_value:
            return ComponentHealth(
                name="redis",
                status="healthy",
                message="Redis connection successful",
                response_time_ms=response_time_ms,
                details={"read_write_test": "passed"},
            )
        else:
            return ComponentHealth(
                name="redis",
                status="degraded",
                message="Redis read/write test mismatch",
                response_time_ms=response_time_ms,
            )

    except Exception as e:
        logger.exception(f"❌ Redis health check failed: {e}")
        return ComponentHealth(
            name="redis",
            status="unhealthy",
            message=f"Redis connection failed: {e!s}",
            response_time_ms=int((time.time() - start_time) * 1000),
        )


async def check_twilio_health() -> ComponentHealth:
    """Check Twilio service health"""
    start_time = time.time()

    try:
        # Phase 2A: Check if Twilio is available
        if not TWILIO_AVAILABLE:
            return ComponentHealth(
                name="twilio",
                status="degraded",
                message="Twilio library not installed",
                response_time_ms=0,
            )

        if not settings.twilio_account_sid or not settings.twilio_auth_token:
            return ComponentHealth(
                name="twilio",
                status="degraded",
                message="Twilio credentials not configured",
                response_time_ms=0,
            )

        client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)

        # Check account status
        account = client.api.accounts(settings.twilio_account_sid).fetch()

        response_time_ms = int((time.time() - start_time) * 1000)

        return ComponentHealth(
            name="twilio",
            status="healthy",
            message="Twilio connection successful",
            response_time_ms=response_time_ms,
            details={
                "account_status": account.status,
                "account_sid": settings.twilio_account_sid[:10] + "...",
            },
        )

    except Exception as e:
        logger.exception(f"❌ Twilio health check failed: {e}")
        return ComponentHealth(
            name="twilio",
            status="unhealthy",
            message=f"Twilio connection failed: {e!s}",
            response_time_ms=int((time.time() - start_time) * 1000),
        )


async def check_stripe_health() -> ComponentHealth:
    """Check Stripe API health"""
    start_time = time.time()

    try:
        if not settings.stripe_secret_key:
            return ComponentHealth(
                name="stripe",
                status="degraded",
                message="Stripe API key not configured",
                response_time_ms=0,
            )

        import stripe

        stripe.api_key = settings.stripe_secret_key

        # Test API with a simple call
        _ = stripe.Account.retrieve()

        response_time_ms = int((time.time() - start_time) * 1000)

        return ComponentHealth(
            name="stripe",
            status="healthy",
            message="Stripe API connection successful",
            response_time_ms=response_time_ms,
        )

    except Exception as e:
        logger.exception(f"❌ Stripe health check failed: {e}")
        return ComponentHealth(
            name="stripe",
            status="unhealthy",
            message=f"Stripe API connection failed: {e!s}",
            response_time_ms=int((time.time() - start_time) * 1000),
        )


async def check_openai_health() -> ComponentHealth:
    """Check OpenAI API key health"""
    start_time = time.time()

    try:
        if not settings.openai_api_key:
            return ComponentHealth(
                name="openai",
                status="degraded",
                message="OpenAI API key not configured",
                response_time_ms=0,
            )

        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        # Determine key type
        key_prefix = settings.openai_api_key[:20] + "..."
        if settings.openai_api_key.startswith("sk-proj-"):
            key_type = "project"
        elif settings.openai_api_key.startswith("sk-svcacct-"):
            key_type = "service_account"
        else:
            key_type = "unknown"

        # Test API with a simple call
        models = client.models.list()
        models_count = len(models.data)

        response_time_ms = int((time.time() - start_time) * 1000)

        # Warn if using service account key
        warning = None
        if key_type == "service_account":
            warning = "Using SERVICE ACCOUNT key - consider switching to PROJECT key for stability"

        return ComponentHealth(
            name="openai",
            status="healthy",
            message="OpenAI API key is valid",
            response_time_ms=response_time_ms,
            details={
                "key_prefix": key_prefix,
                "key_type": key_type,
                "models_available": models_count,
                "warning": warning,
            },
        )

    except Exception as e:
        logger.exception(f"❌ OpenAI health check failed: {e}")
        error_msg = str(e)

        # Provide helpful error message
        if "401" in error_msg or "Incorrect API key" in error_msg:
            message = "OpenAI API key is INVALID or EXPIRED! Update .env file immediately."
        else:
            message = f"OpenAI API connection failed: {error_msg}"

        return ComponentHealth(
            name="openai",
            status="unhealthy",
            message=message,
            response_time_ms=int((time.time() - start_time) * 1000),
        )


async def check_email_health() -> ComponentHealth:
    """Check email service health (Gmail IMAP)"""
    start_time = time.time()

    try:
        if not settings.gmail_user or not settings.gmail_app_password:
            return ComponentHealth(
                name="email",
                status="degraded",
                message="Gmail credentials not configured",
                response_time_ms=0,
            )

        import imaplib
        import ssl

        # Connect to Gmail IMAP
        context = ssl.create_default_context()
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993, ssl_context=context)
        mail.login(settings.gmail_user, settings.gmail_app_password)
        mail.select("INBOX")
        mail.logout()

        response_time_ms = int((time.time() - start_time) * 1000)

        return ComponentHealth(
            name="email",
            status="healthy",
            message="Gmail IMAP connection successful",
            response_time_ms=response_time_ms,
            details={"email": settings.gmail_user[:5] + "***"},
        )

    except Exception as e:
        logger.exception(f"❌ Email health check failed: {e}")
        return ComponentHealth(
            name="email",
            status="unhealthy",
            message=f"Gmail IMAP connection failed: {e!s}",
            response_time_ms=int((time.time() - start_time) * 1000),
        )


@router.get("/live", response_model=dict, status_code=status.HTTP_200_OK)
async def liveness_probe():
    """
    Liveness probe - Kubernetes uses this to know if the app is running

    Returns 200 if the application process is running
    This should be lightweight and fast
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "Application is running",
    }


@router.get("/ready", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """
    Readiness probe - Kubernetes uses this to know if the app can serve traffic

    Checks all critical dependencies:
    - Database connection
    - Redis cache
    - External services (Twilio, Stripe, Email)

    Returns 200 if all critical services are healthy
    Returns 503 if any critical service is unhealthy
    """
    start_time = time.time()

    # Run all health checks in parallel
    results = await asyncio.gather(
        check_database_health(db),
        check_redis_health(),
        check_openai_health(),
        check_twilio_health(),
        check_stripe_health(),
        check_email_health(),
        return_exceptions=True,
    )

    # Process results
    components = []
    for result in results:
        if isinstance(result, Exception):
            components.append(
                ComponentHealth(
                    name="unknown", status="unhealthy", message=f"Health check failed: {result!s}"
                )
            )
        else:
            components.append(result)

    # Determine overall status
    unhealthy_count = sum(1 for c in components if c.status == "unhealthy")
    degraded_count = sum(1 for c in components if c.status == "degraded")

    if unhealthy_count > 0:
        # Critical services are down - database or redis
        critical_unhealthy = any(
            c.name in ["database", "redis"] and c.status == "unhealthy" for c in components
        )

        if critical_unhealthy:
            overall_status = "unhealthy"
        else:
            # Non-critical services are down
            overall_status = "degraded"
    elif degraded_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    overall_response_time_ms = int((time.time() - start_time) * 1000)
    uptime_seconds = int(time.time() - APP_START_TIME)

    response = HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=getattr(settings, "API_VERSION", "1.0.0"),
        environment=getattr(settings, "ENVIRONMENT", "development"),
        uptime_seconds=uptime_seconds,
        components=components,
        overall_response_time_ms=overall_response_time_ms,
    )

    # Return appropriate status code
    if overall_status == "unhealthy":
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response.dict())

    return response


@router.get("/", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Comprehensive health check endpoint

    Same as /ready but more detailed
    """
    return await readiness_probe(db)


@router.get("/startup", response_model=dict)
async def startup_probe(db: AsyncSession = Depends(get_db)):
    """
    Startup probe - Kubernetes uses this during container startup

    Returns 200 only when the application is fully initialized
    This can be slower than liveness/readiness probes
    """
    try:
        # Check if database is accessible
        await db.execute(text("SELECT 1"))

        # Check if migrations are applied (optional)
        # Could check for specific tables or schema version

        return {
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Application is fully initialized and ready to serve traffic",
            "uptime_seconds": int(time.time() - APP_START_TIME),
        }

    except Exception as e:
        logger.exception(f"❌ Startup check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "message": f"Application is still initializing: {e!s}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
