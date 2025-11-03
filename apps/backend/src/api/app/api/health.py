from datetime import datetime

from api.app.core.logging import get_logger
from api.app.database import get_db
from fastapi import APIRouter, Depends, HTTPException
import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/health", tags=["Health Check"])
logger = get_logger(__name__)


@router.get("/")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "MyHibachi API",
        "version": "1.0.0",
    }


@router.get("/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with database and system metrics"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "MyHibachi API",
        "version": "1.0.0",
        "checks": {},
    }

    # Database check
    try:
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()
        health_data["checks"]["database"] = {"status": "healthy", "response_time_ms": "< 100"}
    except Exception as e:
        health_data["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_data["status"] = "unhealthy"

    # Memory check
    memory = psutil.virtual_memory()
    health_data["checks"]["memory"] = {
        "status": "healthy" if memory.percent < 90 else "warning",
        "usage_percent": memory.percent,
        "available_gb": round(memory.available / (1024**3), 2),
    }

    # Disk check
    disk = psutil.disk_usage("/")
    health_data["checks"]["disk"] = {
        "status": "healthy" if disk.percent < 90 else "warning",
        "usage_percent": disk.percent,
        "free_gb": round(disk.free / (1024**3), 2),
    }

    # CPU check
    cpu_percent = psutil.cpu_percent(interval=1)
    health_data["checks"]["cpu"] = {
        "status": "healthy" if cpu_percent < 80 else "warning",
        "usage_percent": cpu_percent,
    }

    return health_data


@router.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics endpoint"""

    # System metrics
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu_percent = psutil.cpu_percent()

    metrics = []

    # Memory metrics
    metrics.append(f"memory_usage_bytes {memory.used}")
    metrics.append(f"memory_total_bytes {memory.total}")
    metrics.append(f"memory_usage_percent {memory.percent}")

    # Disk metrics
    metrics.append(f"disk_usage_bytes {disk.used}")
    metrics.append(f"disk_total_bytes {disk.total}")
    metrics.append(f"disk_usage_percent {disk.percent}")

    # CPU metrics
    metrics.append(f"cpu_usage_percent {cpu_percent}")

    # Process metrics
    process = psutil.Process()
    metrics.append(f"process_memory_bytes {process.memory_info().rss}")
    metrics.append(f"process_cpu_percent {process.cpu_percent()}")

    return "\n".join(metrics)


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Kubernetes-style readiness probe"""
    try:
        # Check database connection
        result = await db.execute(text("SELECT 1"))
        await result.fetchone()

        # Check if we can write (optional)
        # await db.execute(text("CREATE TEMP TABLE readiness_test (id INT)"))
        # await db.execute(text("DROP TABLE readiness_test"))

        return {"status": "ready"}
    except Exception as e:
        logger.exception(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")


@router.get("/live")
async def liveness_check():
    """Kubernetes-style liveness probe"""
    # Simple check to see if the application is responsive
    try:
        # Basic application state check
        return {"status": "alive"}
    except Exception as e:
        logger.exception(f"Liveness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not alive")
