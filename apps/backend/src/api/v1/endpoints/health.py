"""
Comprehensive Health Check Endpoints for Production Kubernetes Deployments

Provides:
- /health/readiness - K8s readiness probe (DB, Redis, critical services)
- /health/liveness - K8s liveness probe (process alive check)
- /health/detailed - Comprehensive system health with metrics
- Prometheus metrics for monitoring

Architecture:
- Async health checks for optimal performance
- Individual service checks with timeout protection
- Graceful degradation (service-specific failures)
- Detailed error reporting for debugging
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Prometheus metrics
try:
    from prometheus_client import Counter, Gauge, Histogram

    HEALTH_CHECK_COUNTER = Counter(
        "health_check_total", "Total health check requests", ["endpoint", "status"]
    )

    HEALTH_CHECK_DURATION = Histogram(
        "health_check_duration_seconds", "Health check duration", ["endpoint", "check_type"]
    )

    SERVICE_HEALTH_GAUGE = Gauge(
        "service_health_status", "Service health status (1=healthy, 0=unhealthy)", ["service"]
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

router = APIRouter()

# Track startup time for uptime calculation
STARTUP_TIME = time.time()


# === Pydantic Schemas ===


class ServiceHealthCheck(BaseModel):
    """Individual service health check result."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "response_time_ms": 45.2,
                "details": "Service is operational",
                "timestamp": "2024-10-25T10:30:00Z",
            }
        }
    )

    status: str = Field(..., description="healthy, degraded, or unhealthy")
    response_time_ms: float | None = Field(None, description="Response time in milliseconds")
    details: str = Field(..., description="Health check details")
    error: str | None = Field(None, description="Error message if unhealthy")
    timestamp: datetime = Field(description="Timestamp of the health check")

    @classmethod
    def create(
        cls,
        status: str,
        details: str,
        response_time_ms: float | None = None,
        error: str | None = None,
    ) -> "ServiceHealthCheck":
        """Factory method to create ServiceHealthCheck with automatic timestamp."""
        return cls(
            status=status,
            details=details,
            response_time_ms=response_time_ms,
            error=error,
            timestamp=datetime.now(timezone.utc),
        )


class ReadinessResponse(BaseModel):
    """Kubernetes readiness probe response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ready",
                "timestamp": "2024-10-25T10:30:00Z",
                "checks": {},
                "ready": True,
            }
        }
    )

    status: str = Field(..., description="ready or not_ready")
    timestamp: datetime = Field(description="Response timestamp")
    checks: dict[str, ServiceHealthCheck] = Field(..., description="Individual service checks")
    ready: bool = Field(..., description="Overall readiness status")
    details: str | None = Field(None, description="Additional details")

    @classmethod
    def create(
        cls,
        status: str,
        checks: dict[str, ServiceHealthCheck],
        ready: bool,
        details: str | None = None,
    ) -> "ReadinessResponse":
        """Factory method to create ReadinessResponse with automatic timestamp."""
        return cls(
            status=status,
            checks=checks,
            ready=ready,
            details=details,
            timestamp=datetime.now(timezone.utc),
        )


class LivenessResponse(BaseModel):
    """Kubernetes liveness probe response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "alive",
                "timestamp": "2024-10-25T10:30:00Z",
                "uptime_seconds": 3600.5,
                "pid": 12345,
            }
        }
    )

    status: str = Field(default="alive", description="Service liveness status")
    timestamp: datetime = Field(description="Response timestamp")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    pid: int = Field(..., description="Process ID")

    @classmethod
    def create(cls, uptime_seconds: float, pid: int, status: str = "alive") -> "LivenessResponse":
        """Factory method to create LivenessResponse with automatic timestamp."""
        return cls(
            status=status,
            uptime_seconds=uptime_seconds,
            pid=pid,
            timestamp=datetime.now(timezone.utc),
        )


class DetailedHealthResponse(BaseModel):
    """Comprehensive health check response."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2024-10-25T10:30:00Z",
                "uptime_seconds": 3600.5,
                "version": "2.0.0",
                "environment": "production",
                "services": {},
                "system": {},
                "configuration": {},
            }
        }
    )

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(description="Response timestamp")
    uptime_seconds: float = Field(..., description="Service uptime")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment name")
    services: dict[str, ServiceHealthCheck] = Field(..., description="Service health checks")
    system: dict[str, Any] = Field(..., description="System metrics")
    configuration: dict[str, Any] = Field(..., description="Configuration status")

    @classmethod
    def create(
        cls,
        status: str,
        uptime_seconds: float,
        version: str,
        environment: str,
        services: dict[str, ServiceHealthCheck],
        system: dict[str, Any],
        configuration: dict[str, Any],
    ) -> "DetailedHealthResponse":
        """Factory method to create DetailedHealthResponse with automatic timestamp."""
        return cls(
            status=status,
            uptime_seconds=uptime_seconds,
            version=version,
            environment=environment,
            services=services,
            system=system,
            configuration=configuration,
            timestamp=datetime.now(timezone.utc),
        )


# === Health Check Functions ===


async def check_database(db: AsyncSession) -> ServiceHealthCheck:
    """
    Check PostgreSQL database connectivity and performance.

    Tests:
    - Connection availability
    - Query execution
    - Response time
    """
    start_time = time.time()

    try:
        # Simple connectivity test with actual query
        await db.execute(text("SELECT 1 as health_check"))
        await db.execute(text("SELECT version()"))  # Get DB version

        response_time = (time.time() - start_time) * 1000

        return ServiceHealthCheck(
            status="healthy",
            response_time_ms=round(response_time, 2),
            details=f"Database connected and responsive (query time: {response_time:.2f}ms)",
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.exception(f"Database health check failed: {e}")

        return ServiceHealthCheck(
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            details="Database connection failed",
            error=str(e),
        )


async def check_redis(request: Request) -> ServiceHealthCheck:
    """
    Check Redis cache connectivity and performance.

    Tests:
    - Connection availability
    - PING response
    - Memory info
    - Response time
    """
    start_time = time.time()

    try:
        # Get Redis client from rate limiter or cache service
        redis_client = None

        # Try to get from rate limiter
        if hasattr(request.app.state, "rate_limiter"):
            rate_limiter = request.app.state.rate_limiter
            if hasattr(rate_limiter, "redis_client") and rate_limiter.redis_client:
                redis_client = rate_limiter.redis_client

        # Try to get from cache service
        if not redis_client and hasattr(request.app.state, "cache_service"):
            cache_service = request.app.state.cache_service
            if hasattr(cache_service, "_client") and cache_service._client:
                redis_client = cache_service._client

        if not redis_client:
            return ServiceHealthCheck(
                status="degraded",
                details="Redis not configured or not available (falling back to memory cache)",
            )

        # Ping test
        await asyncio.wait_for(redis_client.ping(), timeout=2.0)

        # Get memory info
        info = await redis_client.info("memory")
        used_memory_mb = info.get("used_memory", 0) / (1024 * 1024)

        response_time = (time.time() - start_time) * 1000

        return ServiceHealthCheck(
            status="healthy",
            response_time_ms=round(response_time, 2),
            details=f"Redis connected (memory: {used_memory_mb:.2f}MB, ping: {response_time:.2f}ms)",
        )

    except TimeoutError:
        response_time = (time.time() - start_time) * 1000
        logger.exception("Redis health check timed out")

        return ServiceHealthCheck(
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            details="Redis connection timeout",
            error="Timeout after 2 seconds",
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.exception(f"Redis health check failed: {e}")

        return ServiceHealthCheck(
            status="degraded",
            response_time_ms=round(response_time, 2),
            details="Redis connection failed (using memory cache fallback)",
            error=str(e),
        )


async def check_stripe() -> ServiceHealthCheck:
    """
    Check Stripe API connectivity (configuration only, no actual API call).

    Tests:
    - API key configuration
    - Webhook secret configuration
    """
    start_time = time.time()

    try:
        from core.config import get_settings

        settings = get_settings()

        # Check if Stripe is configured
        stripe_key = getattr(settings, "STRIPE_SECRET_KEY", None) or getattr(
            settings, "stripe_secret_key", None
        )
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None) or getattr(
            settings, "stripe_webhook_secret", None
        )

        if not stripe_key:
            return ServiceHealthCheck(
                status="unhealthy",
                details="Stripe API key not configured",
                error="STRIPE_SECRET_KEY environment variable not set",
            )

        # Validate key format (should start with sk_)
        if not stripe_key.startswith("sk_"):
            return ServiceHealthCheck(
                status="unhealthy",
                details="Stripe API key format invalid",
                error="API key should start with 'sk_'",
            )

        response_time = (time.time() - start_time) * 1000

        details = "Stripe API key configured"
        if webhook_secret:
            details += " (webhook secret configured)"

        return ServiceHealthCheck(
            status="healthy", response_time_ms=round(response_time, 2), details=details
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        logger.exception(f"Stripe health check failed: {e}")

        return ServiceHealthCheck(
            status="unhealthy",
            response_time_ms=round(response_time, 2),
            details="Stripe configuration check failed",
            error=str(e),
        )


def get_system_metrics() -> dict[str, Any]:
    """
    Get system performance metrics.

    Returns:
    - CPU usage
    - Memory usage
    - Disk usage
    - Process info
    """
    try:
        import psutil

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "used_gb": round(memory.used / (1024**3), 2),
            "used_percent": round(memory.percent, 2),
        }

        # Disk metrics
        disk = psutil.disk_usage("/")
        disk_info = {
            "total_gb": round(disk.total / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "used_percent": round(disk.percent, 2),
        }

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_info = {"count": psutil.cpu_count(), "usage_percent": round(cpu_percent, 2)}

        # Process metrics
        process = psutil.Process(os.getpid())
        process_info = {
            "pid": process.pid,
            "memory_mb": round(process.memory_info().rss / (1024**2), 2),
            "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
            "threads": process.num_threads(),
            "open_files": len(process.open_files()),
        }

        return {
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "process": process_info,
            "available": True,
        }

    except ImportError:
        return {"available": False, "error": "psutil package not installed"}
    except Exception as e:
        logger.exception(f"Failed to get system metrics: {e}")
        return {"available": False, "error": str(e)}


def get_configuration_status() -> dict[str, Any]:
    """Get application configuration status."""
    try:
        from core.config import get_settings

        settings = get_settings()

        return {
            "environment": getattr(settings, "ENVIRONMENT", "unknown"),
            "debug_mode": getattr(settings, "DEBUG", False),
            "log_level": getattr(settings, "LOG_LEVEL", "INFO"),
            "cors_enabled": bool(getattr(settings, "CORS_ORIGINS", [])),
            "rate_limiting_enabled": getattr(settings, "RATE_LIMIT_ENABLED", True),
            "database_url_configured": bool(getattr(settings, "DATABASE_URL", None)),
            "redis_url_configured": bool(getattr(settings, "REDIS_URL", None)),
            "stripe_configured": bool(
                getattr(settings, "STRIPE_SECRET_KEY", None)
                or getattr(settings, "stripe_secret_key", None)
            ),
            "email_configured": bool(
                getattr(settings, "SMTP_USER", None) or getattr(settings, "smtp_user", None)
            ),
        }
    except Exception as e:
        logger.exception(f"Failed to get configuration status: {e}")
        return {"error": str(e)}


# === Health Check Endpoints ===


@router.api_route(
    "/readiness",
    methods=["GET", "HEAD"],
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
)
async def readiness_probe(
    request: Request, db: AsyncSession = Depends(lambda: None)  # Will be injected properly
):
    """
    Kubernetes Readiness Probe

    Checks if the service is ready to accept traffic.
    Returns 200 if ready, 503 if not ready.

    Critical checks:
    - Database connectivity (MUST be healthy)
    - Redis connectivity (degraded OK, uses memory fallback)
    - Stripe configuration (degraded OK for non-payment endpoints)

    Use in k8s:
    ```yaml
    readinessProbe:
      httpGet:
        path: /api/v1/health/readiness
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    ```
    """
    start_time = time.time()

    try:
        # Import async session maker to avoid circular dependencies
        from core.database import get_db_context

        # Use an async session for DB checks
        async with get_db_context() as db:
            # Run health checks in parallel
            checks_results = await asyncio.gather(
                check_database(db), check_redis(request), check_stripe(), return_exceptions=True
            )

        # Parse results
        db_check, redis_check, stripe_check = checks_results

        # Handle exceptions
        if isinstance(db_check, Exception):
            db_check = ServiceHealthCheck(
                status="unhealthy", details="Database check exception", error=str(db_check)
            )

        if isinstance(redis_check, Exception):
            redis_check = ServiceHealthCheck(
                status="degraded", details="Redis check exception", error=str(redis_check)
            )

        if isinstance(stripe_check, Exception):
            stripe_check = ServiceHealthCheck(
                status="degraded", details="Stripe check exception", error=str(stripe_check)
            )

        checks = {"database": db_check, "redis": redis_check, "stripe": stripe_check}

        # Determine overall readiness
        # Database MUST be healthy, others can be degraded
        is_ready = db_check.status == "healthy"
        overall_status = "ready" if is_ready else "not_ready"

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            duration = time.time() - start_time
            HEALTH_CHECK_COUNTER.labels(endpoint="readiness", status=overall_status).inc()
            HEALTH_CHECK_DURATION.labels(endpoint="readiness", check_type="all").observe(duration)
            SERVICE_HEALTH_GAUGE.labels(service="database").set(
                1 if db_check.status == "healthy" else 0
            )
            SERVICE_HEALTH_GAUGE.labels(service="redis").set(
                1 if redis_check.status == "healthy" else 0
            )
            SERVICE_HEALTH_GAUGE.labels(service="stripe").set(
                1 if stripe_check.status == "healthy" else 0
            )

        response = ReadinessResponse(
            status=overall_status,
            checks=checks,
            ready=is_ready,
            details=(
                "Database is critical for readiness"
                if not is_ready
                else "All critical services ready"
            ),
        )

        # Return 503 if not ready
        if not is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response.dict()
            )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Readiness check failed: {e}")

        if PROMETHEUS_AVAILABLE:
            HEALTH_CHECK_COUNTER.labels(endpoint="readiness", status="error").inc()

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "error": str(e), "details": "Readiness check exception"},
        )


@router.api_route(
    "/liveness",
    methods=["GET", "HEAD"],
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
)
async def liveness_probe():
    """
    Kubernetes Liveness Probe

    Simple check to verify the process is alive and responsive.
    Should ALWAYS return 200 unless the process is completely hung.

    Use in k8s:
    ```yaml
    livenessProbe:
      httpGet:
        path: /api/v1/health/liveness
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 30
      timeoutSeconds: 5
      failureThreshold: 3
    ```
    """
    start_time = time.time()

    try:
        uptime = time.time() - STARTUP_TIME

        if PROMETHEUS_AVAILABLE:
            duration = time.time() - start_time
            HEALTH_CHECK_COUNTER.labels(endpoint="liveness", status="alive").inc()
            HEALTH_CHECK_DURATION.labels(endpoint="liveness", check_type="simple").observe(duration)

        return LivenessResponse(status="alive", uptime_seconds=round(uptime, 2), pid=os.getpid())

    except Exception as e:
        logger.exception(f"Liveness check failed: {e}")

        if PROMETHEUS_AVAILABLE:
            HEALTH_CHECK_COUNTER.labels(endpoint="liveness", status="error").inc()

        # Even on exception, return 200 unless completely hung
        return LivenessResponse(status="alive", uptime_seconds=0, pid=os.getpid())


@router.get("/detailed", response_model=DetailedHealthResponse, status_code=status.HTTP_200_OK)
async def detailed_health_check(request: Request):
    """
    Detailed Health Check with Comprehensive Metrics

    Provides:
    - All service health checks
    - System performance metrics
    - Configuration status
    - Detailed timing information

    Use for:
    - Monitoring dashboards
    - Debugging
    - Performance analysis
    - NOT for k8s probes (too heavy)
    """
    start_time = time.time()

    try:
        from core.config import get_settings
        from core.database import get_db_context

        settings = get_settings()

        # Get database session and run all health checks in parallel
        async with get_db_context() as db:
            checks_results = await asyncio.gather(
                check_database(db), check_redis(request), check_stripe(), return_exceptions=True
            )

        # Parse results
        db_check, redis_check, stripe_check = checks_results

        # Handle exceptions
        if isinstance(db_check, Exception):
            db_check = ServiceHealthCheck(
                status="unhealthy", details="Database check exception", error=str(db_check)
            )

        if isinstance(redis_check, Exception):
            redis_check = ServiceHealthCheck(
                status="degraded", details="Redis check exception", error=str(redis_check)
            )

        if isinstance(stripe_check, Exception):
            stripe_check = ServiceHealthCheck(
                status="degraded", details="Stripe check exception", error=str(stripe_check)
            )

        services = {"database": db_check, "redis": redis_check, "stripe": stripe_check}

        # Get system metrics
        system_metrics = get_system_metrics()

        # Get configuration status
        config_status = get_configuration_status()

        # Determine overall status
        critical_healthy = db_check.status == "healthy"
        overall_status = "healthy" if critical_healthy else "unhealthy"

        # Update Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            duration = time.time() - start_time
            HEALTH_CHECK_COUNTER.labels(endpoint="detailed", status=overall_status).inc()
            HEALTH_CHECK_DURATION.labels(endpoint="detailed", check_type="comprehensive").observe(
                duration
            )

        return DetailedHealthResponse(
            status=overall_status,
            uptime_seconds=round(time.time() - STARTUP_TIME, 2),
            version=getattr(settings, "API_VERSION", "1.0.0"),
            environment=getattr(settings, "ENVIRONMENT", "unknown"),
            services=services,
            system=system_metrics,
            configuration=config_status,
        )

    except Exception as e:
        logger.exception(f"Detailed health check failed: {e}")

        if PROMETHEUS_AVAILABLE:
            HEALTH_CHECK_COUNTER.labels(endpoint="detailed", status="error").inc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"status": "error", "error": str(e), "details": "Detailed health check failed"},
        )


@router.api_route("/", methods=["GET", "HEAD"], status_code=status.HTTP_200_OK)
async def basic_health_check():
    """
    Basic Health Check (Backward Compatibility)

    Simple alive check for basic monitoring.
    Use /readiness or /liveness for k8s probes.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": round(time.time() - STARTUP_TIME, 2),
        "service": "myhibachi-backend",
    }
