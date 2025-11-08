"""
Structured Logging Middleware with Request Tracking and Admin Dashboard Integration

Features:
- Correlation ID tracking across requests
- Request/response logging with timing
- Error log aggregation for admin dashboard
- Security event logging
- Performance monitoring
- Database-backed error logs for admin viewing

Created: October 30, 2025
Author: My Hibachi Chef Development Team
"""

from datetime import datetime, timezone
import json
import logging
import time
import traceback
import uuid

from core.database import (
    Base,
    get_db,
)  # Phase 2C: Updated from api.app.database
from fastapi import Request
import asyncio
from sqlalchemy import Column, DateTime, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# Error Log Model for Admin Dashboard
class ErrorLog(Base):
    """Store error logs for admin dashboard viewing"""

    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    correlation_id = Column(String(36), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Request information
    method = Column(String(10))
    path = Column(String(512))
    client_ip = Column(String(45))
    user_id = Column(Integer, index=True, nullable=True)
    user_role = Column(String(50), nullable=True)

    # Error details
    error_type = Column(String(100))
    error_message = Column(Text)
    error_traceback = Column(Text, nullable=True)
    status_code = Column(Integer)

    # Additional context
    request_body = Column(Text, nullable=True)
    request_headers = Column(Text, nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)

    # Severity level
    level = Column(String(20), default="ERROR", index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL

    # Resolution tracking
    resolved = Column(Integer, default=0)  # 0 = unresolved, 1 = resolved
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)
    resolution_notes = Column(Text, nullable=True)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured logging with correlation IDs and error tracking
    """

    def __init__(
        self,
        app,
        log_request_body: bool = False,
        log_response_body: bool = False,
        sensitive_headers: list | None = None,
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.sensitive_headers = sensitive_headers or [
            "authorization",
            "cookie",
            "x-api-key",
            "x-csrf-token",
        ]

    def _sanitize_headers(self, headers: dict) -> dict:
        """Remove sensitive headers from logs"""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized

    async def _log_error_to_database(
        self,
        correlation_id: str,
        request: Request,
        error: Exception,
        status_code: int,
        response_time_ms: int,
        request_body: str | None = None,
    ):
        """Log error to database for admin dashboard"""
        try:
            # If the event loop is closed (test teardown), skip DB logging to avoid RuntimeError
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("Event loop is closed; skipping DB error log")
                return

            # Get database session
            async for db in get_db():
                # Extract user info from request state
                user_id = getattr(request.state, "user_id", None)
                user_role = getattr(request.state, "role", None)

                # Get client IP
                client_ip = request.client.host if request.client else "unknown"
                if "x-forwarded-for" in request.headers:
                    client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

                # Create error log entry
                error_log = ErrorLog(
                    correlation_id=correlation_id,
                    method=request.method,
                    path=str(request.url.path),
                    client_ip=client_ip,
                    user_id=user_id,
                    user_role=user_role,
                    error_type=type(error).__name__,
                    error_message=str(error),
                    error_traceback=traceback.format_exc(),
                    status_code=status_code,
                    request_body=(request_body if self.log_request_body else None),
                    request_headers=json.dumps(self._sanitize_headers(dict(request.headers))),
                    user_agent=request.headers.get("user-agent"),
                    response_time_ms=response_time_ms,
                    level="ERROR" if status_code >= 500 else "WARNING",
                    resolved=0,
                )

                db.add(error_log)
                await db.commit()

                logger.info(f"📝 Error logged to database with correlation ID: {correlation_id}")
                break  # Exit generator after first iteration

        except Exception as e:
            # If DB logging fails, write to standard logger but do not re-raise
            logger.error(f"❌ Failed to log error to database: {e}", exc_info=True)

    async def dispatch(self, request: Request, call_next):
        """Process request with structured logging"""

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        # Start timing
        start_time = time.time()

        # Get client info
        client_ip = request.client.host if request.client else "unknown"
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()

        # Read request body if needed
        request_body = None
        if self.log_request_body and request.method in [
            "POST",
            "PUT",
            "PATCH",
        ]:
            try:
                body_bytes = await request.body()
                request_body = body_bytes.decode("utf-8")

                # Re-populate request body for downstream handlers
                async def receive():
                    return {"type": "http.request", "body": body_bytes}

                request._receive = receive

            except Exception as e:
                logger.warning(f"⚠️ Could not read request body: {e}")

        # Log request start
        logger.info(
            f"→ {request.method} {request.url.path} "
            f"[{correlation_id}] "
            f"from {client_ip} "
            f"user={getattr(request.state, 'user_id', 'anonymous')}"
        )

        # Process request
        response = None
        error = None
        status_code = 200

        try:
            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            error = e
            status_code = 500

            # Log exception
            logger.error(
                f"❌ Exception in {request.method} {request.url.path} [{correlation_id}]: {e!s}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "user_id": getattr(request.state, "user_id", None),
                    "error_type": type(e).__name__,
                },
            )

            # Re-raise to let FastAPI handle it
            raise

        finally:
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)

            # Determine log level based on status code
            if status_code >= 500:
                log_level = logging.ERROR
                emoji = "❌"
            elif status_code >= 400:
                log_level = logging.WARNING
                emoji = "⚠️"
            elif status_code >= 300:
                log_level = logging.INFO
                emoji = "↪️"
            else:
                log_level = logging.INFO
                emoji = "✅"

            # Log response
            logger.log(
                log_level,
                f"{emoji} {request.method} {request.url.path} "
                f"[{correlation_id}] "
                f"→ {status_code} "
                f"in {response_time_ms}ms "
                f"user={getattr(request.state, 'user_id', 'anonymous')}",
            )

            # Log to database if error occurred
            if error or status_code >= 400:
                await self._log_error_to_database(
                    correlation_id=correlation_id,
                    request=request,
                    error=error or Exception(f"HTTP {status_code}"),
                    status_code=status_code,
                    response_time_ms=response_time_ms,
                    request_body=request_body,
                )

        # Add correlation ID header to response
        if response:
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Response-Time-Ms"] = str(response_time_ms)

        return response


# Helper function for manually logging to admin dashboard
async def log_to_admin_dashboard(
    level: str,
    message: str,
    error_type: str | None = None,
    error_traceback: str | None = None,
    user_id: int | None = None,
    additional_context: dict | None = None,
    db: AsyncSession | None = None,
):
    """
    Manually log an event to the admin dashboard

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        error_type: Type of error if applicable
        error_traceback: Stack trace if applicable
        user_id: User ID if applicable
        additional_context: Additional context as dict
        db: Database session (optional)
    """
    try:
        # Create database session if not provided
        if db is None:
            async for session in get_db():
                db = session
                break

        error_log = ErrorLog(
            correlation_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            method=None,
            path=None,
            client_ip=None,
            user_id=user_id,
            error_type=error_type,
            error_message=message,
            error_traceback=error_traceback,
            status_code=None,
            request_body=(json.dumps(additional_context) if additional_context else None),
            level=level,
            resolved=0,
        )

        db.add(error_log)
        await db.commit()

        logger.info(f"📝 Manual log entry created with level {level}")

    except Exception as e:
        logger.error(f"❌ Failed to create manual log entry: {e}", exc_info=True)


# Helper function to get error logs for admin dashboard
async def get_error_logs(
    db: AsyncSession,
    level: str | None = None,
    user_id: int | None = None,
    resolved: bool | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    Retrieve error logs for admin dashboard

    Args:
        db: Database session
        level: Filter by log level
        user_id: Filter by user ID
        resolved: Filter by resolution status
        limit: Number of logs to return
        offset: Pagination offset

    Returns:
        List of error log entries
    """
    query = select(ErrorLog).order_by(ErrorLog.timestamp.desc())

    if level:
        query = query.where(ErrorLog.level == level)

    if user_id:
        query = query.where(ErrorLog.user_id == user_id)

    if resolved is not None:
        query = query.where(ErrorLog.resolved == (1 if resolved else 0))

    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return result.scalars().all()


# Helper function to resolve error log
async def resolve_error_log(
    db: AsyncSession,
    error_log_id: int,
    resolved_by: int,
    resolution_notes: str | None = None,
):
    """
    Mark an error log as resolved

    Args:
        db: Database session
        error_log_id: ID of the error log
        resolved_by: User ID of the person resolving
        resolution_notes: Optional notes about the resolution
    """
    result = await db.execute(select(ErrorLog).where(ErrorLog.id == error_log_id))
    error_log = result.scalar_one_or_none()

    if error_log:
        error_log.resolved = 1
        error_log.resolved_at = datetime.now(timezone.utc)
        error_log.resolved_by = resolved_by
        error_log.resolution_notes = resolution_notes

        await db.commit()
        logger.info(f"✅ Error log {error_log_id} marked as resolved by user {resolved_by}")
        return True

    return False
