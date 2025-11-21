"""
Audit Service - Track all database changes and security events
"""

from datetime import datetime
import logging
from typing import Any
from uuid import UUID

from models.audit import AuditLog, SecurityAuditLog
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AuditService:
    """
    Service for logging database changes and security events.

    Usage:
        audit_service = AuditService(db)
        await audit_service.log_change(
            table_name="bookings",
            record_id=booking_id,
            action="UPDATE",
            old_values=old_booking_dict,
            new_values=new_booking_dict,
            user_id=current_user_id,
            ip_address=request.client.host
        )
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_change(
        self,
        table_name: str,
        record_id: UUID,
        action: str,  # INSERT, UPDATE, DELETE
        old_values: dict[str, Any] | None = None,
        new_values: dict[str, Any] | None = None,
        user_id: UUID | None = None,
        user_email: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        """
        Log a database change.

        Args:
            table_name: Name of the table (e.g., "bookings", "payments")
            record_id: ID of the record that changed
            action: INSERT, UPDATE, or DELETE
            old_values: Dict of old field values (for UPDATE/DELETE)
            new_values: Dict of new field values (for INSERT/UPDATE)
            user_id: ID of user who made the change
            user_email: Email of user who made the change
            ip_address: IP address of the request
            user_agent: User agent string

        Returns:
            Created AuditLog instance
        """

        try:
            # Detect changed fields
            changed_fields = []
            if old_values and new_values:
                changed_fields = [
                    field
                    for field in new_values.keys()
                    if old_values.get(field) != new_values.get(field)
                ]

            # Create audit log entry
            audit_log = AuditLog(
                table_name=table_name,
                record_id=record_id,
                action=action,
                old_values=old_values,
                new_values=new_values,
                changed_fields=changed_fields,
                user_id=user_id,
                user_email=user_email,
                ip_address=ip_address,
                user_agent=user_agent,
            )

            self.db.add(audit_log)
            await self.db.flush()

            logger.info(
                f"Audit log created: {action} on {table_name} (record {record_id})",
                extra={
                    "table": table_name,
                    "action": action,
                    "user_id": str(user_id) if user_id else None,
                    "changed_fields": changed_fields,
                },
            )

            return audit_log

        except Exception as e:
            logger.exception(f"Failed to create audit log: {e}")
            # Don't fail the main operation if audit logging fails
            raise

    async def log_security_event(
        self,
        event_type: str,
        description: str,
        user_id: UUID | None = None,
        target_user_id: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True,
        failure_reason: str | None = None,
    ) -> SecurityAuditLog:
        """
        Log a security event.

        Args:
            event_type: Type of event (LOGIN, LOGOUT, PERMISSION_CHANGE, etc.)
            description: Human-readable description
            user_id: User who performed the action
            target_user_id: User affected by the action (for permission changes)
            metadata: Additional context data
            ip_address: IP address
            user_agent: User agent string
            success: Whether the event succeeded
            failure_reason: Reason for failure if success=False

        Returns:
            Created SecurityAuditLog instance
        """

        try:
            security_log = SecurityAuditLog(
                event_type=event_type,
                description=description,
                user_id=user_id,
                target_user_id=target_user_id,
                event_metadata=metadata,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                failure_reason=failure_reason,
            )

            self.db.add(security_log)
            await self.db.flush()

            logger.info(
                f"Security event logged: {event_type}",
                extra={
                    "event_type": event_type,
                    "user_id": str(user_id) if user_id else None,
                    "success": success,
                },
            )

            return security_log

        except Exception as e:
            logger.exception(f"Failed to create security audit log: {e}")
            raise

    async def get_audit_logs(
        self,
        table_name: str | None = None,
        record_id: UUID | None = None,
        user_id: UUID | None = None,
        action: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """
        Query audit logs with filters.

        Args:
            table_name: Filter by table name
            record_id: Filter by record ID
            user_id: Filter by user who made change
            action: Filter by action type (INSERT, UPDATE, DELETE)
            limit: Max results to return
            offset: Pagination offset

        Returns:
            List of AuditLog instances
        """

        query = select(AuditLog)

        # Apply filters
        conditions = []
        if table_name:
            conditions.append(AuditLog.table_name == table_name)
        if record_id:
            conditions.append(AuditLog.record_id == record_id)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if action:
            conditions.append(AuditLog.action == action)

        if conditions:
            query = query.where(and_(*conditions))

        # Order by timestamp DESC
        query = query.order_by(desc(AuditLog.timestamp))

        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_security_logs(
        self,
        event_type: str | None = None,
        user_id: UUID | None = None,
        success: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SecurityAuditLog]:
        """
        Query security audit logs with filters.

        Args:
            event_type: Filter by event type
            user_id: Filter by user
            success: Filter by success status
            limit: Max results
            offset: Pagination offset

        Returns:
            List of SecurityAuditLog instances
        """

        query = select(SecurityAuditLog)

        # Apply filters
        conditions = []
        if event_type:
            conditions.append(SecurityAuditLog.event_type == event_type)
        if user_id:
            conditions.append(SecurityAuditLog.user_id == user_id)
        if success is not None:
            conditions.append(SecurityAuditLog.success == success)

        if conditions:
            query = query.where(and_(*conditions))

        # Order by timestamp DESC
        query = query.order_by(desc(SecurityAuditLog.timestamp))

        # Pagination
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_record_history(
        self, table_name: str, record_id: UUID
    ) -> list[AuditLog]:
        """
        Get full change history for a specific record.

        Args:
            table_name: Table name
            record_id: Record ID

        Returns:
            List of all changes to this record, ordered chronologically
        """

        query = (
            select(AuditLog)
            .where(
                and_(
                    AuditLog.table_name == table_name,
                    AuditLog.record_id == record_id,
                )
            )
            .order_by(AuditLog.timestamp)
        )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_failed_login_attempts(
        self,
        user_id: UUID | None = None,
        ip_address: str | None = None,
        hours: int = 24,
    ) -> list[SecurityAuditLog]:
        """
        Get failed login attempts in the last N hours.

        Args:
            user_id: Filter by user ID
            ip_address: Filter by IP address
            hours: Time window (default 24 hours)

        Returns:
            List of failed login attempts
        """

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        query = select(SecurityAuditLog).where(
            and_(
                SecurityAuditLog.event_type == "LOGIN",
                SecurityAuditLog.success == False,
                SecurityAuditLog.timestamp >= cutoff_time,
            )
        )

        if user_id:
            query = query.where(SecurityAuditLog.user_id == user_id)
        if ip_address:
            query = query.where(SecurityAuditLog.ip_address == ip_address)

        query = query.order_by(desc(SecurityAuditLog.timestamp))

        result = await self.db.execute(query)
        return result.scalars().all()


# Helper function for easy access
def get_audit_service(db: AsyncSession) -> AuditService:
    """Get AuditService instance."""
    return AuditService(db)
