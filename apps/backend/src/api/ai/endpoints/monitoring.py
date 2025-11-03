"""
Performance Monitoring and Metrics Collection for MyHibachi AI Backend
Real-time metrics, health checks, and system resource monitoring
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
from typing import Any

from fastapi import Request
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Info,
    start_http_server,
)
import psutil
import structlog

logger = structlog.get_logger(__name__)


# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)

AI_MODEL_REQUESTS = Counter(
    "ai_model_requests_total", "Total AI model requests", ["model", "success"]
)

AI_MODEL_TOKENS = Counter("ai_model_tokens_total", "Total AI model tokens used", ["model"])

AI_RESPONSE_TIME = Histogram("ai_response_duration_seconds", "AI model response time", ["model"])

WEBSOCKET_CONNECTIONS = Gauge("websocket_connections_active", "Active WebSocket connections")

DATABASE_QUERY_DURATION = Histogram(
    "database_query_duration_seconds",
    "Database query duration",
    ["operation", "table"],
)

KNOWLEDGE_BASE_SEARCHES = Counter(
    "knowledge_base_searches_total",
    "Total knowledge base searches",
    ["success"],
)

SYSTEM_INFO = Info("myhibachi_ai_system_info", "System information")

# System resource metrics
CPU_USAGE = Gauge("system_cpu_usage_percent", "CPU usage percentage")
MEMORY_USAGE = Gauge("system_memory_usage_bytes", "Memory usage in bytes")
MEMORY_USAGE_PERCENT = Gauge("system_memory_usage_percent", "Memory usage percentage")
DISK_USAGE = Gauge("system_disk_usage_percent", "Disk usage percentage")


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""

    request_count: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    ai_requests: int = 0
    ai_tokens_used: int = 0
    websocket_connections: int = 0
    database_queries: int = 0
    knowledge_base_searches: int = 0
    system_cpu: float = 0.0
    system_memory: float = 0.0
    system_disk: float = 0.0
    uptime_seconds: float = 0.0
    last_updated: datetime = None

    def __post_init__(self):
        """Set timestamp after initialization."""
        if self.last_updated is None:
            self.last_updated = datetime.utcnow()


class PerformanceMonitor:
    """Comprehensive performance monitoring system"""

    def __init__(self):
        self.start_time = time.time()
        self.metrics_history: deque = deque(maxlen=1440)  # 24 hours of minute data
        self.response_times: deque = deque(maxlen=1000)
        self.error_counts: dict[str, int] = defaultdict(int)
        self.ai_usage_stats: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "requests": 0,
                "tokens": 0,
                "total_time": 0.0,
                "errors": 0,
            }
        )
        self.websocket_connections_count = 0

        # Start system resource monitoring
        self._monitor_system_resources()

        logger.info("Performance monitoring system initialized")

    def _monitor_system_resources(self):
        """Monitor system resources and update metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)

            # Memory usage
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)
            MEMORY_USAGE_PERCENT.set(memory.percent)

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            DISK_USAGE.set(disk_percent)

            # System info
            SYSTEM_INFO.info(
                {
                    "version": "1.0.0",
                    "python_version": psutil.sys.version.split()[0],
                    "platform": psutil.sys.platform,
                    "cpu_count": str(psutil.cpu_count()),
                    "memory_total": str(memory.total),
                }
            )

        except Exception as e:
            logger.exception("Failed to collect system metrics", error=str(e))

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

        self.response_times.append(duration)

        if status_code >= 400:
            self.error_counts[f"{method}_{endpoint}"] += 1

        logger.debug(
            "Request recorded",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration=duration,
        )

    def record_ai_request(self, model: str, tokens: int, duration: float, success: bool = True):
        """Record AI model usage metrics"""
        AI_MODEL_REQUESTS.labels(model=model, success=str(success)).inc()
        AI_MODEL_TOKENS.labels(model=model).inc(tokens)
        AI_RESPONSE_TIME.labels(model=model).observe(duration)

        # Update internal stats
        stats = self.ai_usage_stats[model]
        stats["requests"] += 1
        stats["tokens"] += tokens
        stats["total_time"] += duration
        if not success:
            stats["errors"] += 1

        logger.info(
            "AI request recorded",
            model=model,
            tokens=tokens,
            duration=duration,
            success=success,
        )

    def record_websocket_connection(self, connected: bool):
        """Record WebSocket connection changes"""
        if connected:
            self.websocket_connections_count += 1
        else:
            self.websocket_connections_count = max(0, self.websocket_connections_count - 1)

        WEBSOCKET_CONNECTIONS.set(self.websocket_connections_count)

        logger.debug(
            "WebSocket connection recorded",
            connected=connected,
            total_connections=self.websocket_connections_count,
        )

    def record_database_query(self, operation: str, table: str, duration: float):
        """Record database query metrics"""
        DATABASE_QUERY_DURATION.labels(operation=operation, table=table).observe(duration)

        logger.debug(
            "Database query recorded",
            operation=operation,
            table=table,
            duration=duration,
        )

    def record_knowledge_base_search(self, success: bool, duration: float):
        """Record knowledge base search metrics"""
        KNOWLEDGE_BASE_SEARCHES.labels(success=str(success)).inc()

        logger.debug(
            "Knowledge base search recorded",
            success=success,
            duration=duration,
        )

    def get_current_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        uptime = time.time() - self.start_time

        # Calculate average response time
        avg_response_time = (
            sum(self.response_times) / len(self.response_times) if self.response_times else 0.0
        )

        # Calculate error rate
        total_errors = sum(self.error_counts.values())
        total_requests = len(self.response_times)
        error_rate = (total_errors / total_requests) if total_requests > 0 else 0.0

        # Get system resources
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
        except (OSError, AttributeError, ZeroDivisionError) as e:
            logger.warning(f"Failed to get system resources: {e}")
            cpu_percent = memory.percent = disk_percent = 0.0

        return PerformanceMetrics(
            request_count=total_requests,
            avg_response_time=avg_response_time,
            error_rate=error_rate,
            ai_requests=sum(stats["requests"] for stats in self.ai_usage_stats.values()),
            ai_tokens_used=sum(stats["tokens"] for stats in self.ai_usage_stats.values()),
            websocket_connections=self.websocket_connections_count,
            system_cpu=cpu_percent,
            system_memory=memory.percent,
            system_disk=disk_percent,
            uptime_seconds=uptime,
        )

    def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive health status"""
        metrics = self.get_current_metrics()

        # Determine health status based on metrics
        health_issues = []

        if metrics.error_rate > 0.05:  # More than 5% error rate
            health_issues.append(f"High error rate: {metrics.error_rate:.2%}")

        if metrics.avg_response_time > 2.0:  # More than 2 seconds average
            health_issues.append(f"Slow response time: {metrics.avg_response_time:.2f}s")

        if metrics.system_cpu > 80:
            health_issues.append(f"High CPU usage: {metrics.system_cpu:.1f}%")

        if metrics.system_memory > 85:
            health_issues.append(f"High memory usage: {metrics.system_memory:.1f}%")

        if metrics.system_disk > 90:
            health_issues.append(f"High disk usage: {metrics.system_disk:.1f}%")

        status = "unhealthy" if health_issues else "healthy"

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": metrics.uptime_seconds,
            "uptime_human": str(timedelta(seconds=int(metrics.uptime_seconds))),
            "metrics": {
                "requests_total": metrics.request_count,
                "avg_response_time": metrics.avg_response_time,
                "error_rate": metrics.error_rate,
                "ai_requests": metrics.ai_requests,
                "ai_tokens_used": metrics.ai_tokens_used,
                "websocket_connections": metrics.websocket_connections,
                "system": {
                    "cpu_percent": metrics.system_cpu,
                    "memory_percent": metrics.system_memory,
                    "disk_percent": metrics.system_disk,
                },
            },
            "issues": health_issues,
            "ai_usage": dict(self.ai_usage_stats),
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Middleware for automatic request monitoring
class PerformanceMiddleware:
    """FastAPI middleware for automatic performance monitoring"""

    def __init__(self):
        self.monitor = performance_monitor

    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        # Get endpoint info
        method = request.method
        endpoint = str(request.url.path)

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        self.monitor.record_request(method, endpoint, response.status_code, duration)

        return response


def start_metrics_server(port: int = 8000):
    """Start Prometheus metrics server"""
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
        logger.info(f"Metrics available at http://localhost:{port}/metrics")
    except Exception as e:
        logger.exception(f"Failed to start metrics server: {e}")


# Export main components
__all__ = [
    "PerformanceMetrics",
    "PerformanceMiddleware",
    "PerformanceMonitor",
    "performance_monitor",
    "start_metrics_server",
]
