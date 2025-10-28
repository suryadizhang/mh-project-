"""
Comprehensive health check endpoints for MyHibachi Backend.
Provides detailed system status, database connectivity, and external service checks.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from api.app.database import get_db
from api.app.schemas.health import HealthResponse, ReadinessResponse
from core.config import get_settings

settings = get_settings()
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Track startup time for uptime calculation
startup_time = time.time()


async def check_database_connectivity() -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        start_time = time.time()
        
        # Get database session
        db = next(get_db())
        
        # Simple connectivity test
        result = db.execute("SELECT 1")
        
        # Performance test
        query_time = time.time() - start_time
        db.close()
        
        return {
            "status": "healthy",
            "response_time_ms": round(query_time * 1000, 2),
            "details": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "response_time_ms": None,
            "error": str(e),
            "details": "Database connection failed"
        }


def get_system_info() -> Dict[str, Any]:
    """Get basic system information."""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_used_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_used_percent": round((disk.used / disk.total) * 100, 2)
        }
    except ImportError:
        return {"details": "System metrics require psutil package"}
    except Exception as e:
        return {"error": str(e), "details": "System metrics unavailable"}


@router.get("/", response_model=HealthResponse)
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
            environment=settings.environment,
            version="1.2.0",
            timestamp=datetime.utcnow(),
            uptime_seconds=round(time.time() - startup_time, 2),
            database_status=db_check["status"],
            database_response_time_ms=db_check.get("response_time_ms"),
            checks={
                "database": db_check,
                "stripe_configured": bool(getattr(settings, 'stripe_secret_key', None)),
                "email_configured": bool(getattr(settings, 'smtp_user', None)),
                "environment": settings.environment
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Checks if the service is ready to accept traffic.
    """
    try:
        checks = {
            "database": False,
            "stripe": False,
            "email": False
        }
        
        # Database connectivity check
        db_check = await check_database_connectivity()
        checks["database"] = db_check["status"] == "healthy"
        
        # Stripe configuration check
        checks["stripe"] = bool(getattr(settings, 'stripe_secret_key', None))
        
        # Email configuration check  
        checks["email"] = bool(getattr(settings, 'smtp_user', None))
        
        # Overall readiness - database is critical
        is_ready = checks["database"]
        status = "ready" if is_ready else "not ready"
        
        return ReadinessResponse(
            status=status,
            service="myhibachi-backend-fastapi",
            environment=settings.environment,
            checks=checks,
            database_connected=checks["database"],
            stripe_configured=checks["stripe"],
            email_configured=checks["email"],
            timestamp=datetime.utcnow(),
            ready=is_ready
        )
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Readiness check failed: {str(e)}")


@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Simple check to verify the service is alive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "myhibachi-backend-fastapi",
        "uptime_seconds": round(time.time() - startup_time, 2)
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
            "stripe_configured": bool(getattr(settings, 'stripe_secret_key', None)),
            "email_configured": bool(getattr(settings, 'smtp_user', None)),
            "debug_mode": getattr(settings, 'debug', False),
            "environment": settings.environment,
            "log_level": getattr(settings, 'log_level', 'info')
        }
        
        # Overall status
        overall_status = "healthy" if db_check["status"] == "healthy" else "unhealthy"
        
        return {
            "status": overall_status,
            "service": "myhibachi-backend-fastapi",
            "version": "1.2.0",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": round(time.time() - startup_time, 2),
            "environment": settings.environment,
            "database": db_check,
            "system": system_info,
            "configuration": config_status,
            "features": {
                "rate_limiting": getattr(settings, 'rate_limit_enabled', True),
                "metrics": getattr(settings, 'enable_metrics', False),
                "cors_enabled": bool(getattr(settings, 'cors_origins', [])),
            }
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Detailed health check failed: {str(e)}")