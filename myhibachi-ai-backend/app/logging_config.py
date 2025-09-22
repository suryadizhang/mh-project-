"""
Comprehensive Logging Configuration for MyHibachi AI Backend
Structured logging with performance metrics and monitoring
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Optional

import structlog
from structlog.typing import FilteringBoundLogger


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_logs: bool = False,
) -> FilteringBoundLogger:
    """
    Set up comprehensive structured logging for the application

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        json_logs: Whether to use JSON format for logs

    Returns:
        Configured structlog logger
    """

    # Clear any existing configuration
    structlog.reset_defaults()

    # Configure standard library logging first
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Set up processors for structured logging
    processors = [
        # Add timestamp
        structlog.processors.TimeStamper(fmt="ISO", utc=True),
        # Add log level
        structlog.stdlib.add_log_level,
        # Add logger name
        structlog.stdlib.add_logger_name,
        # Stack info processor
        structlog.processors.StackInfoRenderer(),
        # Exception info processor
        structlog.dev.set_exc_info,
        # Add call site info in development
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]

    if json_logs:
        # Production: JSON formatting for structured logs
        processors.extend(
            [
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ]
        )
    else:
        # Development: Pretty colored output
        processors.extend(
            [
                structlog.processors.dict_tracebacks,
                structlog.dev.ConsoleRenderer(colors=True),
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Create and configure file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, mode="a")
        file_handler.setLevel(getattr(logging, log_level.upper()))

        if json_logs:
            file_formatter = logging.Formatter("%(message)s")
        else:
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        file_handler.setFormatter(file_formatter)

        # Add file handler to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)

    # Return configured logger
    return structlog.get_logger("myhibachi_ai")


# Performance monitoring utilities
class PerformanceLogger:
    """Context manager for timing operations and logging performance metrics"""

    def __init__(
        self, logger: FilteringBoundLogger, operation: str, **context
    ):
        self.logger = logger
        self.operation = operation
        self.context = context
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.debug(
            "Operation started", operation=self.operation, **self.context
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type:
            self.logger.error(
                "Operation failed",
                operation=self.operation,
                duration_seconds=duration,
                error_type=exc_type.__name__,
                error_message=str(exc_val),
                **self.context,
            )
        else:
            log_level = "warning" if duration > 5.0 else "info"
            getattr(self.logger, log_level)(
                "Operation completed",
                operation=self.operation,
                duration_seconds=duration,
                **self.context,
            )


# Request/Response logging middleware
class RequestLogger:
    """Utility for logging HTTP requests and responses"""

    def __init__(self, logger: FilteringBoundLogger):
        self.logger = logger

    def log_request(
        self, method: str, url: str, headers: dict[str, Any] = None, **context
    ):
        """Log incoming HTTP request"""
        self.logger.info(
            "HTTP request received",
            method=method,
            url=str(url),
            user_agent=headers.get("user-agent") if headers else None,
            **context,
        )

    def log_response(self, status_code: int, duration: float, **context):
        """Log HTTP response"""
        log_level = "error" if status_code >= 400 else "info"
        getattr(self.logger, log_level)(
            "HTTP response sent",
            status_code=status_code,
            duration_seconds=duration,
            **context,
        )


# WebSocket logging utilities
class WebSocketLogger:
    """Utility for logging WebSocket events"""

    def __init__(self, logger: FilteringBoundLogger):
        self.logger = logger

    def log_connection(self, client_id: str, conversation_id: str):
        """Log WebSocket connection"""
        self.logger.info(
            "WebSocket connection established",
            client_id=client_id,
            conversation_id=conversation_id,
        )

    def log_disconnection(
        self, client_id: str, conversation_id: str, reason: str = None
    ):
        """Log WebSocket disconnection"""
        self.logger.info(
            "WebSocket connection closed",
            client_id=client_id,
            conversation_id=conversation_id,
            reason=reason,
        )

    def log_message(self, client_id: str, message_type: str, **context):
        """Log WebSocket message"""
        self.logger.debug(
            "WebSocket message processed",
            client_id=client_id,
            message_type=message_type,
            **context,
        )


# AI/ML specific logging
class AILogger:
    """Utility for logging AI pipeline operations"""

    def __init__(self, logger: FilteringBoundLogger):
        self.logger = logger

    def log_model_usage(
        self, model: str, tokens_used: int, cost: float = None, **context
    ):
        """Log AI model usage for cost tracking"""
        self.logger.info(
            "AI model invoked",
            model=model,
            tokens_used=tokens_used,
            estimated_cost=cost,
            **context,
        )

    def log_knowledge_base_search(
        self, query: str, results_count: int, search_time: float, **context
    ):
        """Log knowledge base search operations"""
        self.logger.debug(
            "Knowledge base search performed",
            query_length=len(query),
            results_count=results_count,
            search_time_seconds=search_time,
            **context,
        )

    def log_confidence_score(
        self, score: float, threshold: float, action: str, **context
    ):
        """Log confidence scoring and escalation decisions"""
        self.logger.info(
            "AI confidence evaluation",
            confidence_score=score,
            threshold=threshold,
            action=action,
            **context,
        )


# Database logging utilities
class DatabaseLogger:
    """Utility for logging database operations"""

    def __init__(self, logger: FilteringBoundLogger):
        self.logger = logger

    def log_query(
        self, operation: str, table: str, duration: float, **context
    ):
        """Log database query performance"""
        log_level = "warning" if duration > 1.0 else "debug"
        getattr(self.logger, log_level)(
            "Database query executed",
            operation=operation,
            table=table,
            duration_seconds=duration,
            **context,
        )

    def log_connection_pool(self, active: int, idle: int, total: int):
        """Log database connection pool status"""
        self.logger.debug(
            "Database connection pool status",
            active_connections=active,
            idle_connections=idle,
            total_connections=total,
        )


# Security logging
class SecurityLogger:
    """Utility for logging security-related events"""

    def __init__(self, logger: FilteringBoundLogger):
        self.logger = logger

    def log_authentication(
        self, success: bool, user_id: str = None, ip: str = None, **context
    ):
        """Log authentication attempts"""
        log_level = "info" if success else "warning"
        getattr(self.logger, log_level)(
            "Authentication attempt",
            success=success,
            user_id=user_id,
            ip_address=ip,
            **context,
        )

    def log_rate_limit(
        self, client_id: str, endpoint: str, limit_reached: bool, **context
    ):
        """Log rate limiting events"""
        if limit_reached:
            self.logger.warning(
                "Rate limit exceeded",
                client_id=client_id,
                endpoint=endpoint,
                **context,
            )


# Export main logger setup function and utilities
__all__ = [
    "setup_logging",
    "PerformanceLogger",
    "RequestLogger",
    "WebSocketLogger",
    "AILogger",
    "DatabaseLogger",
    "SecurityLogger",
]
