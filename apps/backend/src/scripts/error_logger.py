"""
Email Backfill Error Logger

Integrates with the existing ErrorLog system in middleware/structured_logging.py
to provide comprehensive error tracking and notification for email backfill operations.

Features:
- Database error logging (error_logs table)
- Severity classification (CRITICAL, ERROR, WARNING, INFO)
- Correlation ID tracking
- Automatic error aggregation
- Fallback mechanisms for critical failures

Created: November 2025
Author: My Hibachi Chef Development Team
"""

from datetime import datetime, timezone
import logging
import traceback
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from middleware.structured_logging import ErrorLog

logger = logging.getLogger(__name__)


class EmailBackfillErrorLogger:
    """
    Error logging utility for email backfill operations.

    Integrates with the existing ErrorLog model to track all errors
    during email synchronization and backfill operations.
    """

    def __init__(self, db: AsyncSession, operation_id: str | None = None):
        """
        Initialize error logger.

        Args:
            db: Database session for logging errors
            operation_id: Unique identifier for this backfill operation (correlation ID)
        """
        self.db = db
        self.operation_id = operation_id or str(uuid.uuid4())
        self.error_count = 0
        self.warning_count = 0
        self.critical_count = 0

    async def log_error(
        self,
        error: Exception,
        context: dict[str, Any] | None = None,
        severity: str = "ERROR",
        email_id: str | None = None,
        inbox: str | None = None,
    ) -> None:
        """
        Log error to database using ErrorLog model.

        Args:
            error: The exception that occurred
            context: Additional context information
            severity: ERROR, WARNING, or CRITICAL
            email_id: IMAP email ID being processed
            inbox: Inbox name (customer_support or payments)
        """
        try:
            # Build error context
            error_context = {
                "operation": "email_backfill",
                "inbox": inbox,
                "email_id": email_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **(context or {}),
            }

            # Create ErrorLog entry
            error_log = ErrorLog(
                correlation_id=self.operation_id,
                timestamp=datetime.now(timezone.utc),
                method="BACKFILL",
                path=f"/scripts/backfill_emails/{inbox or 'unknown'}",
                client_ip="127.0.0.1",  # Local script execution
                user_id=None,  # System operation
                user_role="SYSTEM",
                error_type=type(error).__name__,
                error_message=str(error),
                error_traceback=traceback.format_exc(),
                status_code=500,  # Internal error
                request_body=str(error_context),
                request_headers=None,
                user_agent="EmailBackfillScript/1.0",
                response_time_ms=None,
                level=severity.upper(),
                resolved=0,  # Unresolved
            )

            self.db.add(error_log)
            await self.db.commit()

            # Update counters
            if severity == "CRITICAL":
                self.critical_count += 1
            elif severity == "ERROR":
                self.error_count += 1
            elif severity == "WARNING":
                self.warning_count += 1

            # Log to standard logger
            log_message = f"📝 Logged {severity}: {type(error).__name__} - {str(error)}"
            if email_id:
                log_message += f" (Email ID: {email_id})"

            if severity == "CRITICAL":
                logger.critical(log_message)
            elif severity == "ERROR":
                logger.error(log_message)
            else:
                logger.warning(log_message)

        except Exception as log_error:
            # Fallback: If database logging fails, use standard logger
            logger.error(
                f"❌ FALLBACK: Failed to log error to database: {log_error}",
                exc_info=True,
            )
            logger.error(f"❌ Original error: {error}", exc_info=True)

    async def log_batch_error(
        self,
        batch_number: int,
        batch_size: int,
        error: Exception,
        emails_processed: int,
    ) -> None:
        """
        Log batch processing error.

        Args:
            batch_number: Batch number that failed
            batch_size: Size of the batch
            error: The exception that occurred
            emails_processed: Number of emails successfully processed in batch
        """
        await self.log_error(
            error=error,
            context={
                "batch_number": batch_number,
                "batch_size": batch_size,
                "emails_processed": emails_processed,
                "completion_percentage": (emails_processed / batch_size * 100) if batch_size > 0 else 0,
            },
            severity="ERROR",
        )

    async def log_critical_failure(
        self,
        operation: str,
        error: Exception,
        recovery_attempted: bool = False,
    ) -> None:
        """
        Log critical failure that stops the backfill operation.

        Args:
            operation: Operation that failed critically
            error: The exception that occurred
            recovery_attempted: Whether automatic recovery was attempted
        """
        await self.log_error(
            error=error,
            context={
                "critical_operation": operation,
                "recovery_attempted": recovery_attempted,
                "requires_manual_intervention": True,
            },
            severity="CRITICAL",
        )

    async def log_imap_connection_error(
        self,
        inbox: str,
        error: Exception,
        retry_attempt: int | None = None,
    ) -> None:
        """
        Log IMAP connection error.

        Args:
            inbox: Inbox that failed to connect
            error: Connection error
            retry_attempt: Retry attempt number (if applicable)
        """
        await self.log_error(
            error=error,
            context={
                "connection_type": "IMAP",
                "retry_attempt": retry_attempt,
            },
            severity="ERROR",
            inbox=inbox,
        )

    async def log_database_error(
        self,
        operation: str,
        error: Exception,
        email_id: str | None = None,
    ) -> None:
        """
        Log database operation error.

        Args:
            operation: Database operation that failed
            error: Database error
            email_id: Email ID being processed (if applicable)
        """
        await self.log_error(
            error=error,
            context={
                "database_operation": operation,
            },
            severity="ERROR",
            email_id=email_id,
        )

    async def log_duplicate_email(
        self,
        email_id: str,
        message_id: str,
        inbox: str,
    ) -> None:
        """
        Log duplicate email detection (INFO level).

        Args:
            email_id: IMAP email ID
            message_id: Email message ID
            inbox: Inbox name
        """
        try:
            logger.info(f"ℹ️  Duplicate email detected: {message_id} (Email ID: {email_id})")
            # Don't log duplicates to ErrorLog - they're expected behavior
        except Exception as e:
            logger.error(f"Error logging duplicate: {e}")

    def get_error_summary(self) -> dict[str, Any]:
        """
        Get summary of errors logged during this operation.

        Returns:
            Dictionary with error counts by severity and operation ID
        """
        return {
            "critical": self.critical_count,
            "errors": self.error_count,
            "warnings": self.warning_count,
            "total": self.critical_count + self.error_count + self.warning_count,
            "operation_id": self.operation_id,
        }

    def should_abort_operation(self, threshold_percentage: float = 50.0) -> bool:
        """
        Determine if operation should be aborted based on error rate.

        Args:
            threshold_percentage: Maximum acceptable error percentage

        Returns:
            True if operation should be aborted
        """
        # Abort if critical errors occur
        if self.critical_count > 0:
            logger.critical(
                f"🛑 ABORT: Critical errors detected ({self.critical_count})"
            )
            return True

        # Could implement error rate threshold checking here
        # For now, only abort on critical errors
        return False
