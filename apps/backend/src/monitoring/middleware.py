"""
Monitoring Middleware - Activity Detection & Metric Tracking

Integrates with FastAPI to:
1. Detect API activity and wake/sleep monitoring
2. Track response times for performance monitoring
3. Track errors for error rate monitoring
4. Log activity patterns for baseline learning
"""

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from monitoring.activity_classifier import get_activity_classifier
from monitoring.metric_collector import track_response_time, track_error, push_metric_update
from monitoring.monitoring_state import get_monitoring_state

logger = logging.getLogger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for activity detection and metric tracking
    
    Features:
    - Smart activity classification (wake/sleep trigger)
    - Response time tracking
    - Error rate tracking  
    - Request rate tracking
    - Pattern learning
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.classifier = get_activity_classifier()
        self.state_machine = get_monitoring_state()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with activity detection and metric tracking
        
        Flow:
        1. Check if should wake monitoring
        2. Track request start time
        3. Process request
        4. Track response time and status
        5. Update activity timestamp if woke
        """
        
        # ====================================================================
        # Step 1: Activity Classification
        # ====================================================================
        
        should_wake, reason = self.classifier.should_wake(request)
        
        if should_wake:
            logger.info(f"🔫 WAKE: {request.method} {request.url.path} - Reason: {reason}")
            
            # Wake monitoring system
            self._trigger_wake()
            
            # Log wake event for pattern analysis
            self.classifier.log_wake_event(request, reason)
        else:
            logger.debug(f"😴 IDLE: {request.method} {request.url.path} - Reason: {reason}")
        
        # ====================================================================
        # Step 2: Start timing
        # ====================================================================
        
        start_time = time.time()
        
        # ====================================================================
        # Step 3: Process request
        # ====================================================================
        
        response = None
        error_occurred = False
        
        try:
            response = await call_next(request)
            
        except Exception as e:
            logger.error(f"Error processing request {request.url.path}: {e}")
            error_occurred = True
            raise
        
        # ====================================================================
        # Step 4: Track metrics
        # ====================================================================
        
        # Calculate response time
        duration_ms = (time.time() - start_time) * 1000
        
        # Track response time
        track_response_time(duration_ms)
        
        # Track errors (5xx responses)
        if error_occurred or (response and response.status_code >= 500):
            track_error()
        
        # Add custom headers for debugging
        if response:
            response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
            response.headers["X-Monitor-Wake"] = "true" if should_wake else "false"
            response.headers["X-Monitor-Reason"] = reason
        
        return response
    
    def _trigger_wake(self):
        """
        Trigger monitoring system wake up using the state machine
        
        Delegates to MonitoringState which handles:
        - State transitions
        - Activity timestamp updates
        - State history tracking
        """
        try:
            # Use state machine to handle wake logic
            state_changed = self.state_machine.wake(reason="api_activity")
            
            if state_changed:
                logger.info("🔔 Monitoring state: IDLE → ACTIVE")
            
        except Exception as e:
            logger.error(f"Error triggering wake: {e}")


# ============================================================================
# EXCEPTION HANDLER FOR ERROR TRACKING
# ============================================================================

async def monitoring_exception_handler(request: Request, exc: Exception):
    """
    Exception handler that tracks errors
    
    Register in FastAPI:
    app.add_exception_handler(Exception, monitoring_exception_handler)
    """
    logger.error(f"Unhandled exception on {request.url.path}: {exc}")
    
    # Track error
    track_error()
    
    # Push error count metric
    try:
        import redis
        from core.config import settings
        
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        error_count = redis_client.incr("metrics:total_errors")
        push_metric_update("total_errors", float(error_count))
        
    except Exception as e:
        logger.error(f"Error tracking exception: {e}")
    
    # Re-raise for default handling
    raise exc
