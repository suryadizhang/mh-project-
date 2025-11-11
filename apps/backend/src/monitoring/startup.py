"""
Monitoring System Startup

Initializes and starts the complete monitoring system:
- ThresholdMonitor: Core monitoring engine
- MetricSubscriber: Real-time pub/sub listener
- MonitoringState: State machine management
- RuleEvaluator: Threshold checking

Usage in FastAPI app:

    from monitoring.startup import startup_monitoring, shutdown_monitoring
    
    @app.on_event("startup")
    async def startup():
        await startup_monitoring()
    
    @app.on_event("shutdown")
    async def shutdown():
        await shutdown_monitoring()

Or in lifespan context:

    from monitoring.startup import monitoring_lifespan
    
    app = FastAPI(lifespan=monitoring_lifespan)
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI

from core.database import SessionLocal
from core.config import settings
from .threshold_monitor import ThresholdMonitor, get_threshold_monitor
import redis

logger = logging.getLogger(__name__)

# Global monitor instance
_monitor_instance: Optional[ThresholdMonitor] = None


async def startup_monitoring() -> ThresholdMonitor:
    """
    Start the monitoring system.
    
    Call this during application startup to initialize monitoring.
    
    Returns:
        ThresholdMonitor instance
    """
    global _monitor_instance
    
    try:
        logger.info("Starting monitoring system...")
        
        # Get database session
        db = SessionLocal()
        
        # Get Redis client
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        # Create monitor
        _monitor_instance = get_threshold_monitor(db, redis_client)
        
        # Start monitoring
        await _monitor_instance.start()
        
        logger.info("Monitoring system started successfully")
        return _monitor_instance
    
    except Exception as e:
        logger.error(f"Failed to start monitoring system: {e}", exc_info=True)
        raise


async def shutdown_monitoring():
    """
    Stop the monitoring system.
    
    Call this during application shutdown to gracefully stop monitoring.
    """
    global _monitor_instance
    
    if _monitor_instance:
        try:
            logger.info("Stopping monitoring system...")
            await _monitor_instance.stop()
            _monitor_instance = None
            logger.info("Monitoring system stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping monitoring system: {e}", exc_info=True)


def get_monitor_instance() -> Optional[ThresholdMonitor]:
    """
    Get the current monitor instance.
    
    Returns:
        ThresholdMonitor instance or None if not started
    """
    return _monitor_instance


@asynccontextmanager
async def monitoring_lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Usage:
        from monitoring.startup import monitoring_lifespan
        
        app = FastAPI(lifespan=monitoring_lifespan)
    """
    # Startup
    logger.info("Application startup: initializing monitoring")
    await startup_monitoring()
    
    try:
        yield
    finally:
        # Shutdown
        logger.info("Application shutdown: stopping monitoring")
        await shutdown_monitoring()
