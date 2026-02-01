"""
Comprehensive health check endpoints for MyHibachi Backend.
Provides detailed system status, database connectivity, and external service checks.
"""

import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from core.config import get_settings
from core.database import get_db_context
from schemas.health import HealthResponse, ReadinessResponse

settings = get_settings()
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Track startup time for uptime calculation
startup_time = time.time()


async def check_database_connectivity() -> dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        start_time = time.time()

        # Get database session
        async with get_db_context() as db:
            # Simple connectivity test
            await db.execute(text("SELECT 1"))

            # Performance test
            query_time = time.time() - start_time

        return {
            "status": "healthy",
            "response_time_ms": round(query_time * 1000, 2),
            "details": "Database connection successful",
        }
    except Exception as e:
        logger.exception(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "error": str(e),
            "details": "Database connection failed",
        }


def get_system_info() -> dict[str, Any]:
    """Get basic system information."""
    try:
        import psutil

        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_used_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_used_percent": round((disk.used / disk.total) * 100, 2),
        }
    except ImportError:
        return {"details": "System metrics require psutil package"}
    except Exception as e:
        return {"error": str(e), "details": "System metrics unavailable"}


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint.
    Returns overall service health status with comprehensive checks.
    """
    try:
        # Database connectivity check
        db_check = await check_database_connectivity()

        overall_status = "healthy" if db_check["status"] == "healthy" else "unhealthy"

        return HealthResponse(
            status=overall_status,
            service="myhibachi-backend-fastapi",
            environment=getattr(settings, "ENVIRONMENT", "development"),
            version="1.2.0",
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=round(time.time() - startup_time, 2),
            database_status=db_check["status"],
            database_response_time_ms=db_check.get("response_time_ms"),
            checks={
                "database": db_check,
                "stripe_configured": bool(getattr(settings, "stripe_secret_key", None)),
                "email_configured": bool(getattr(settings, "smtp_user", None)),
                "environment": getattr(settings, "ENVIRONMENT", "development"),
            },
        )
    except Exception as e:
        logger.exception(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {e!s}")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Checks if the service is ready to accept traffic.
    """
    try:
        checks = {"database": False, "stripe": False, "email": False}

        # Database connectivity check
        db_check = await check_database_connectivity()
        checks["database"] = db_check["status"] == "healthy"

        # Stripe configuration check
        checks["stripe"] = bool(getattr(settings, "stripe_secret_key", None))

        # Email configuration check
        checks["email"] = bool(getattr(settings, "smtp_user", None))

        # Overall readiness - database is critical
        is_ready = checks["database"]
        status = "ready" if is_ready else "not ready"

        return ReadinessResponse(
            status=status,
            service="myhibachi-backend-fastapi",
            environment=getattr(settings, "ENVIRONMENT", "development"),
            checks=checks,
            database_connected=checks["database"],
            stripe_configured=checks["stripe"],
            email_configured=checks["email"],
            timestamp=datetime.now(timezone.utc),
            ready=is_ready,
        )
    except Exception as e:
        logger.exception(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {e!s}")


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Simple check to verify the service is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "myhibachi-backend-fastapi",
        "uptime_seconds": round(time.time() - startup_time, 2),
    }


@router.get("/email-monitors")
async def email_monitors_health():
    """
    Health check for email monitoring systems (Gmail + IONOS).

    Returns status of both email monitors including:
    - Last check timestamp
    - Last successful check
    - Consecutive failure count
    - Last error message (if any)

    Used by admin dashboard to display email monitor status.
    Part of Batch 1: Full Redundancy email monitoring system.
    """
    import os
    from datetime import timezone

    try:
        # Try to get status from Celery task
        # Import here to avoid circular imports at module level
        from workers.email_monitoring_tasks import (
            EMAIL_MONITOR_STATUS,
            get_monitor_health,
            validate_email_credentials,
        )

        # Get current credentials status
        creds = validate_email_credentials()

        # Get monitor status from the shared state
        health = get_monitor_health.delay().get(timeout=5)

        # Determine overall health
        gmail_healthy = (
            health["gmail"]["consecutive_failures"] == 0 and creds["gmail"]["valid"]
        )
        ionos_healthy = (
            health["ionos"]["consecutive_failures"] == 0 and creds["ionos"]["valid"]
        )

        overall_status = "healthy" if (gmail_healthy and ionos_healthy) else "degraded"
        if (
            health["gmail"]["consecutive_failures"] >= 3
            or health["ionos"]["consecutive_failures"] >= 3
        ):
            overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "monitors": {
                "gmail": {
                    **health["gmail"],
                    "credentials_valid": creds["gmail"]["valid"],
                    "credentials_missing": creds["gmail"]["missing"],
                    "healthy": gmail_healthy,
                    "description": "Payment email notifications (myhibachichef@gmail.com)",
                },
                "ionos": {
                    **health["ionos"],
                    "credentials_valid": creds["ionos"]["valid"],
                    "credentials_missing": creds["ionos"]["missing"],
                    "healthy": ionos_healthy,
                    "description": "Customer support emails (cs@myhibachichef.com)",
                },
            },
            "configuration": {
                "gmail_user_set": bool(os.getenv("GMAIL_USER")),
                "gmail_password_set": bool(os.getenv("GMAIL_APP_PASSWORD")),
                "ionos_password_set": bool(os.getenv("SMTP_PASSWORD")),
            },
        }

    except Exception as e:
        # Celery task failed or not available - return what we can
        import os

        logger.warning(f"Email monitor health check degraded: {e}")

        return {
            "status": "unknown",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": f"Could not retrieve monitor status: {str(e)}",
            "configuration": {
                "gmail_user_set": bool(os.getenv("GMAIL_USER")),
                "gmail_password_set": bool(os.getenv("GMAIL_APP_PASSWORD")),
                "ionos_password_set": bool(os.getenv("SMTP_PASSWORD")),
            },
            "hint": "Celery worker may not be running. Check with: celery -A workers.celery_config status",
        }


@router.get("/detailed")
async def detailed_health_check():
    """
    Detailed health check with comprehensive system information.
    Includes database, system metrics, and configuration status.
    """
    try:
        # Run database check
        db_check = await check_database_connectivity()

        # Get system information
        system_info = get_system_info()

        # Configuration checks
        config_status = {
            "stripe_configured": bool(getattr(settings, "stripe_secret_key", None)),
            "email_configured": bool(getattr(settings, "smtp_user", None)),
            "debug_mode": getattr(settings, "debug", False),
            "environment": getattr(settings, "ENVIRONMENT", "development"),
            "log_level": getattr(settings, "log_level", "info"),
        }

        # Overall status
        overall_status = "healthy" if db_check["status"] == "healthy" else "unhealthy"

        return {
            "status": overall_status,
            "service": "myhibachi-backend-fastapi",
            "version": "1.2.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": round(time.time() - startup_time, 2),
            "environment": getattr(settings, "ENVIRONMENT", "development"),
            "database": db_check,
            "system": system_info,
            "configuration": config_status,
            "features": {
                "rate_limiting": getattr(settings, "rate_limit_enabled", True),
                "metrics": getattr(settings, "enable_metrics", False),
                "cors_enabled": bool(getattr(settings, "cors_origins", [])),
            },
        }
    except Exception as e:
        logger.exception(f"Detailed health check failed: {e}")
        raise HTTPException(
            status_code=503, detail=f"Detailed health check failed: {e!s}"
        )
