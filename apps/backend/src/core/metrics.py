"""
API Monitoring & Metrics - Prometheus Integration
Track request metrics, cache performance, query times, and business KPIs

IMPORTANT: This is the SINGLE SOURCE OF TRUTH for the metrics registry.
All other modules MUST import metrics from here, never create their own.
"""

from collections.abc import Callable
from datetime import datetime, timezone
import logging
import time

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

logger = logging.getLogger(__name__)

# ============================================================================
# SINGLE METRICS REGISTRY - All metrics MUST use this registry
# ============================================================================
registry = CollectorRegistry()

# Guard to prevent double registration during test imports
_METRICS_REGISTERED = False

def _register_metrics():
    """
    Register all metrics exactly once.
    This prevents duplicate registration errors during test imports.
    """
    global _METRICS_REGISTERED
    
    if _METRICS_REGISTERED:
        logger.debug("Metrics already registered, skipping")
        return
    
    logger.info("Registering Prometheus metrics...")
    _METRICS_REGISTERED = True


# ============================================================================
# CORE METRICS - Registered at module import
# ============================================================================

# Request metrics
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
    registry=registry,
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

request_size = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    registry=registry,
)

response_size = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    registry=registry,
)

# Cache metrics
cache_hits = Counter(
    "cache_hits_total", "Total cache hits", ["cache_key_prefix"], registry=registry
)

cache_misses = Counter(
    "cache_misses_total", "Total cache misses", ["cache_key_prefix"], registry=registry
)

cache_errors = Counter("cache_errors_total", "Total cache errors", ["operation"], registry=registry)

cache_operation_duration = Histogram(
    "cache_operation_duration_seconds", "Cache operation latency", ["operation"], registry=registry
)

# Database metrics
db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query latency",
    ["operation", "model"],
    registry=registry,
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

db_query_count = Counter(
    "db_queries_total", "Total database queries", ["operation", "model"], registry=registry
)

db_connection_errors = Counter(
    "db_connection_errors_total", "Total database connection errors", [], registry=registry
)

# Business metrics
bookings_created = Counter(
    "bookings_created_total", "Total bookings created", ["status"], registry=registry
)

payments_processed = Counter(
    "payments_processed_total",
    "Total payments processed",
    ["status", "provider"],
    registry=registry,
)

payment_amount = Histogram(
    "payment_amount_dollars",
    "Payment amounts in dollars",
    ["status"],
    registry=registry,
    buckets=(10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
)

messages_sent = Counter(
    "messages_sent_total", "Total messages sent", ["channel", "status"], registry=registry
)

# System metrics
active_connections = Gauge(
    "active_connections", "Number of active connections", [], registry=registry
)

security_violations = Counter(
    "security_violations_total",
    "Security violations detected",
    ["violation_type"],
    registry=registry,
)

rate_limit_exceeded = Counter(
    "rate_limit_exceeded_total",
    "Total rate limit exceeded events",
    ["tier", "limit_type"],
    registry=registry,
)

idempotency_replays = Counter(
    "idempotency_replays_total", "Total idempotent request replays", ["endpoint"], registry=registry
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect request metrics"""

    def __init__(self, app):
        super().__init__(app)
        self.active_requests = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for each request"""

        # Skip metrics collection for metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        # Track active connections
        self.active_requests += 1
        active_connections.set(self.active_requests)

        # Get request size
        request_body_size = int(request.headers.get("content-length", 0))

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Get endpoint pattern (remove IDs for better grouping)
            endpoint = self._normalize_endpoint(request.url.path)

            # Record metrics
            request_count.labels(
                method=request.method, endpoint=endpoint, status=response.status_code
            ).inc()

            request_duration.labels(method=request.method, endpoint=endpoint).observe(duration)

            request_size.labels(method=request.method, endpoint=endpoint).observe(request_body_size)

            # Try to get response size
            if hasattr(response, "body"):
                response_body_size = len(response.body)
                response_size.labels(method=request.method, endpoint=endpoint).observe(
                    response_body_size
                )

            # Add custom headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

            return response

        except Exception as e:
            logger.exception(f"Error in metrics middleware: {e}")
            raise

        finally:
            # Decrement active connections
            self.active_requests -= 1
            active_connections.set(self.active_requests)

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for better metric grouping"""
        # Replace UUIDs and numeric IDs with placeholders
        import re

        # Replace UUIDs
        path = re.sub(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "{uuid}", path
        )

        # Replace numeric IDs
        path = re.sub(r"/\d+/", "/{id}/", path)
        path = re.sub(r"/\d+$", "/{id}", path)

        return path


class MetricsCollector:
    """Helper class for collecting custom metrics"""

    @staticmethod
    def record_cache_hit(key_prefix: str):
        """Record a cache hit"""
        cache_hits.labels(cache_key_prefix=key_prefix).inc()

    @staticmethod
    def record_cache_miss(key_prefix: str):
        """Record a cache miss"""
        cache_misses.labels(cache_key_prefix=key_prefix).inc()

    @staticmethod
    def record_cache_error(operation: str):
        """Record a cache error"""
        cache_errors.labels(operation=operation).inc()

    @staticmethod
    def record_cache_operation(operation: str, duration: float):
        """Record cache operation duration"""
        cache_operation_duration.labels(operation=operation).observe(duration)

    @staticmethod
    def record_db_query(operation: str, model: str, duration: float):
        """Record database query"""
        db_query_count.labels(operation=operation, model=model).inc()
        db_query_duration.labels(operation=operation, model=model).observe(duration)

    @staticmethod
    def record_db_error():
        """Record database connection error"""
        db_connection_errors.inc()

    @staticmethod
    def record_booking_created(status: str):
        """Record booking creation"""
        bookings_created.labels(status=status).inc()

    @staticmethod
    def record_payment(status: str, provider: str, amount: float):
        """Record payment processed"""
        payments_processed.labels(status=status, provider=provider).inc()
        payment_amount.labels(status=status).observe(amount)

    @staticmethod
    def record_message_sent(channel: str, status: str):
        """Record message sent"""
        messages_sent.labels(channel=channel, status=status).inc()

    @staticmethod
    def record_rate_limit_exceeded(tier: str, limit_type: str):
        """Record rate limit exceeded"""
        rate_limit_exceeded.labels(tier=tier, limit_type=limit_type).inc()

    @staticmethod
    def record_idempotency_replay(endpoint: str):
        """Record idempotent request replay"""
        idempotency_replays.labels(endpoint=endpoint).inc()


# Decorator for automatic query timing
def track_query_time(operation: str, model_name: str):
    """
    Decorator to automatically track database query time

    Example:
        @track_query_time("select", "Booking")
        async def get_bookings(self):
            return await self.repository.find_all()
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                MetricsCollector.record_db_query(operation, model_name, duration)
                return result
            except Exception:
                MetricsCollector.record_db_error()
                raise

        return wrapper

    return decorator


# Decorator for cache metrics
def track_cache_operation(operation: str):
    """
    Decorator to track cache operations

    Example:
        @track_cache_operation("get")
        async def get_from_cache(self, key):
            return await self.redis.get(key)
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                MetricsCollector.record_cache_operation(operation, duration)
                return result
            except Exception:
                MetricsCollector.record_cache_error(operation)
                raise

        return wrapper

    return decorator


async def metrics_endpoint(request: Request) -> StarletteResponse:
    """
    Prometheus metrics endpoint

    Add to FastAPI:
        @app.get("/metrics")
        async def metrics(request: Request):
            return await metrics_endpoint(request)
    """
    metrics_data = generate_latest(registry)
    return StarletteResponse(
        content=metrics_data, media_type=CONTENT_TYPE_LATEST, headers={"Cache-Control": "no-cache"}
    )


class HealthCheckMetrics:
    """Health check with metrics"""

    @staticmethod
    async def get_health_with_metrics(app) -> dict:
        """
        Get comprehensive health status with metrics

        Returns:
            Health status with key metrics
        """
        # Get cache hit rate
        try:
            total_cache_ops = cache_hits._value.get() + cache_misses._value.get()
            cache_hit_rate = (
                (cache_hits._value.get() / total_cache_ops * 100) if total_cache_ops > 0 else 0
            )
        except (AttributeError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"Failed to calculate cache hit rate: {e}")
            cache_hit_rate = 0

        # Get average response time (approximate)
        try:
            avg_response_time = request_duration._sum.get() / request_duration._count.get()
        except (AttributeError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"Failed to calculate average response time: {e}")
            avg_response_time = 0

        # Get active connections from gauge
        try:
            active_conns = active_connections._value.get()
        except (AttributeError, TypeError) as e:
            logger.warning(f"Failed to get active connections: {e}")
            active_conns = 0

        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics": {
                "total_requests": (
                    request_count._value.get() if hasattr(request_count, "_value") else 0
                ),
                "active_connections": active_conns,
                "cache_hit_rate_percent": round(cache_hit_rate, 2),
                "avg_response_time_seconds": round(avg_response_time, 3),
                "total_cache_hits": cache_hits._value.get() if hasattr(cache_hits, "_value") else 0,
                "total_cache_misses": (
                    cache_misses._value.get() if hasattr(cache_misses, "_value") else 0
                ),
                "total_db_queries": (
                    db_query_count._value.get() if hasattr(db_query_count, "_value") else 0
                ),
            },
        }


# ============================================================================
# PUBLIC API - Import these from other modules
# ============================================================================
__all__ = [
    # Registry (REQUIRED for all custom metrics)
    "registry",
    
    # Core HTTP metrics
    "request_count",
    "request_duration",
    "request_size",
    "response_size",
    
    # Cache metrics
    "cache_hits",
    "cache_misses",
    "cache_errors",
    "cache_operation_duration",
    
    # Database metrics
    "db_query_duration",
    "db_query_count",
    "db_connection_errors",
    
    # Business metrics
    "bookings_created",
    "payments_processed",
    "payment_amount",
    "messages_sent",
    
    # System metrics
    "active_connections",
    "security_violations",
    "rate_limit_exceeded",
    "idempotency_replays",
    
    # Middleware & utilities
    "MetricsMiddleware",
    "MetricsCollector",
    "HealthCheckMetrics",
    "metrics_endpoint",
    "track_cache_operation",
]
