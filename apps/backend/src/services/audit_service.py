"""
Audit Service - Centralized Audit Logging Implementation

Enterprise-grade audit service for tracking all system changes and security events.
Supports SOC2/HIPAA/GDPR compliance with immutable logs and retention policies.

Tables Used:
- audit_logs: General action audit trail (VIEW, CREATE, UPDATE, DELETE)
- security.security_events: Security-specific events (login, logout, failures)

Usage:
    from services.audit_service import get_audit_service, AuditService

    # In FastAPI endpoint with dependency injection
    audit_service = get_audit_service(db)
    await audit_service.log_action(
        action="UPDATE",
        resource_type="booking",
        resource_id=str(booking.id),
        user_id=str(current_user.id),
        details={"status": "confirmed"}
    )

    # Log data changes (INSERT/UPDATE/DELETE)
    await audit_service.log_change(
        table_name="bookings",
        record_id=booking.id,
        action="INSERT",
        new_values=booking_dict,
        user_id=customer_id
    )

    # Log security events
    await audit_service.log_security_event(
        event_type="NEW_IP_DETECTED",
        description="New IP address detected",
        user_id=user.id,
        success=True,
        ip_address="1.2.3.4"
    )
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AuditService:
    """
    Centralized Audit Service for enterprise compliance.

    Provides:
    - log_action(): General action logging
    - log_change(): Data change tracking (INSERT/UPDATE/DELETE)
    - log_security_event(): Security event logging
    - get_audit_trail(): Query audit logs
    """

    # Valid actions for log_action
    VALID_ACTIONS = {"VIEW", "CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "ACCESS"}

    # Valid change actions for log_change
    VALID_CHANGE_ACTIONS = {"INSERT", "UPDATE", "DELETE"}

    def __init__(self, db: Optional[AsyncSession] = None):
        """Initialize audit service with database session."""
        self.db = db

    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str = None,
        user_id: str = None,
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Optional[UUID]:
        """
        Log an audit action to the audit_logs table.

        Args:
            action: Action type (VIEW, CREATE, UPDATE, DELETE, etc.)
            resource_type: Type of resource (booking, customer, lead, etc.)
            resource_id: ID of affected resource
            user_id: ID of user performing action
            details: Additional context as dict
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            UUID of created audit log entry, or None on failure
        """
        if not self.db:
            logger.warning("AuditService.log_action: No database session available")
            return None

        # Validate action
        if action not in self.VALID_ACTIONS:
            logger.warning(f"Invalid audit action '{action}', logging anyway")

        try:
            query = text("""
                INSERT INTO audit_logs (
                    user_id,
                    user_role,
                    user_name,
                    user_email,
                    action,
                    resource_type,
                    resource_id,
                    resource_name,
                    ip_address,
                    user_agent,
                    metadata
                ) VALUES (
                    :user_id,
                    :user_role,
                    :user_name,
                    :user_email,
                    :action,
                    :resource_type,
                    :resource_id,
                    :resource_name,
                    :ip_address,
                    :user_agent,
                    CAST(:metadata AS jsonb)
                )
                RETURNING id
            """)

            result = await self.db.execute(
                query,
                {
                    "user_id": str(user_id) if user_id else None,
                    "user_role": details.get("user_role", "unknown") if details else "unknown",
                    "user_name": details.get("user_name", "System") if details else "System",
                    "user_email": details.get("user_email") if details else None,
                    "action": action.upper(),
                    "resource_type": resource_type,
                    "resource_id": str(resource_id) if resource_id else None,
                    "resource_name": details.get("resource_name") if details else None,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "metadata": json.dumps(details) if details else "{}",
                },
            )

            audit_log_id = result.scalar_one()
            logger.debug(f"Audit log created: {action} {resource_type}/{resource_id}")
            return audit_log_id

        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")
            return None

    async def log_change(
        self,
        table_name: str,
        record_id: Any,
        action: str,
        old_values: dict = None,
        new_values: dict = None,
        user_id: Any = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> Optional[UUID]:
        """
        Log a data change (INSERT, UPDATE, DELETE) to audit trail.

        Args:
            table_name: Database table name (bookings, customers, etc.)
            record_id: ID of the record being changed
            action: Change type (INSERT, UPDATE, DELETE)
            old_values: Previous state (for UPDATE/DELETE)
            new_values: New state (for INSERT/UPDATE)
            user_id: ID of user making the change
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            UUID of created audit log entry, or None on failure
        """
        if not self.db:
            logger.warning("AuditService.log_change: No database session available")
            return None

        # Validate action
        if action.upper() not in self.VALID_CHANGE_ACTIONS:
            logger.warning(f"Invalid change action '{action}', expected INSERT/UPDATE/DELETE")

        try:
            # Serialize values if they're not already JSON-serializable
            def safe_serialize(obj):
                if obj is None:
                    return None
                if isinstance(obj, (dict, list)):
                    return json.dumps(obj, default=str)
                return json.dumps({"value": obj}, default=str)

            query = text("""
                INSERT INTO audit_logs (
                    user_id,
                    user_role,
                    user_name,
                    action,
                    resource_type,
                    resource_id,
                    old_values,
                    new_values,
                    ip_address,
                    user_agent,
                    metadata
                ) VALUES (
                    :user_id,
                    'system',
                    'System',
                    :action,
                    :table_name,
                    :record_id,
                    CAST(:old_values AS jsonb),
                    CAST(:new_values AS jsonb),
                    :ip_address,
                    :user_agent,
                    CAST(:metadata AS jsonb)
                )
                RETURNING id
            """)

            result = await self.db.execute(
                query,
                {
                    "user_id": str(user_id) if user_id else None,
                    "action": action.upper(),
                    "table_name": table_name,
                    "record_id": str(record_id) if record_id else None,
                    "old_values": safe_serialize(old_values),
                    "new_values": safe_serialize(new_values),
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "metadata": json.dumps({
                        "change_type": action.upper(),
                        "table": table_name,
                        "logged_at": datetime.now(timezone.utc).isoformat(),
                    }),
                },
            )

            audit_log_id = result.scalar_one()
            logger.debug(f"Change logged: {action} on {table_name}/{record_id}")
            return audit_log_id

        except Exception as e:
            logger.error(f"Failed to log change: {e}")
            return None

    async def log_security_event(
        self,
        event_type: str,
        description: str = None,
        user_id: Any = None,
        email: str = None,
        success: bool = True,
        failure_reason: str = None,
        metadata: dict = None,
        ip_address: str = None,
        user_agent: str = None,
        severity: str = "low",
    ) -> Optional[UUID]:
        """
        Log a security event to security.security_events table.

        Args:
            event_type: Type of security event (LOGIN_SUCCESS, LOGIN_FAILED, etc.)
            description: Human-readable description
            user_id: ID of user involved (if applicable)
            email: Email address involved (for failed logins)
            success: Whether the action succeeded
            failure_reason: Reason for failure (if success=False)
            metadata: Additional context as dict
            ip_address: Client IP address
            user_agent: Client user agent
            severity: Event severity (low, medium, high, critical)

        Returns:
            UUID of created security event, or None on failure
        """
        if not self.db:
            logger.warning("AuditService.log_security_event: No database session available")
            return None

        try:
            # Build details dict
            details = metadata.copy() if metadata else {}
            if description:
                details["description"] = description
            if success is not None:
                details["success"] = success
            if failure_reason:
                details["failure_reason"] = failure_reason

            query = text("""
                INSERT INTO security.security_events (
                    event_type,
                    user_id,
                    email,
                    ip_address,
                    user_agent,
                    details,
                    severity
                ) VALUES (
                    :event_type,
                    :user_id,
                    :email,
                    :ip_address,
                    :user_agent,
                    CAST(:details AS jsonb),
                    :severity
                )
                RETURNING id
            """)

            result = await self.db.execute(
                query,
                {
                    "event_type": event_type.upper(),
                    "user_id": str(user_id) if user_id else None,
                    "email": email,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "details": json.dumps(details) if details else "{}",
                    "severity": severity,
                },
            )

            event_id = result.scalar_one()
            logger.debug(f"Security event logged: {event_type} (severity={severity})")
            return event_id

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return None

    async def get_audit_trail(
        self,
        resource_type: str = None,
        resource_id: str = None,
        user_id: str = None,
        action: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Retrieve audit trail entries with optional filters.

        Args:
            resource_type: Filter by resource type
            resource_id: Filter by specific resource ID
            user_id: Filter by user who performed action
            action: Filter by action type
            limit: Maximum entries to return (default 100)
            offset: Pagination offset

        Returns:
            List of audit log entries as dicts
        """
        if not self.db:
            logger.warning("AuditService.get_audit_trail: No database session available")
            return []

        try:
            # Build dynamic query with filters
            conditions = []
            params = {"limit": limit, "offset": offset}

            if resource_type:
                conditions.append("resource_type = :resource_type")
                params["resource_type"] = resource_type
            if resource_id:
                conditions.append("resource_id = :resource_id")
                params["resource_id"] = str(resource_id)
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = str(user_id)
            if action:
                conditions.append("action = :action")
                params["action"] = action.upper()

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = text(f"""
                SELECT
                    id,
                    user_id,
                    user_role,
                    user_name,
                    user_email,
                    action,
                    resource_type,
                    resource_id,
                    resource_name,
                    ip_address,
                    old_values,
                    new_values,
                    metadata,
                    created_at
                FROM audit_logs
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(query, params)
            rows = result.fetchall()

            # Convert to list of dicts
            return [
                {
                    "id": str(row.id),
                    "user_id": row.user_id,
                    "user_role": row.user_role,
                    "user_name": row.user_name,
                    "user_email": row.user_email,
                    "action": row.action,
                    "resource_type": row.resource_type,
                    "resource_id": row.resource_id,
                    "resource_name": row.resource_name,
                    "ip_address": row.ip_address,
                    "old_values": row.old_values,
                    "new_values": row.new_values,
                    "metadata": row.metadata,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
            return []

    async def get_security_events(
        self,
        event_type: str = None,
        user_id: str = None,
        email: str = None,
        ip_address: str = None,
        severity: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Retrieve security events with optional filters.

        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            email: Filter by email
            ip_address: Filter by IP address
            severity: Filter by severity level
            limit: Maximum entries to return
            offset: Pagination offset

        Returns:
            List of security events as dicts
        """
        if not self.db:
            logger.warning("AuditService.get_security_events: No database session available")
            return []

        try:
            conditions = []
            params = {"limit": limit, "offset": offset}

            if event_type:
                conditions.append("event_type = :event_type")
                params["event_type"] = event_type.upper()
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = str(user_id)
            if email:
                conditions.append("email = :email")
                params["email"] = email
            if ip_address:
                conditions.append("ip_address = :ip_address")
                params["ip_address"] = ip_address
            if severity:
                conditions.append("severity = :severity")
                params["severity"] = severity

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = text(f"""
                SELECT
                    id,
                    event_type,
                    user_id,
                    email,
                    ip_address,
                    user_agent,
                    details,
                    severity,
                    created_at
                FROM security.security_events
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """)

            result = await self.db.execute(query, params)
            rows = result.fetchall()

            return [
                {
                    "id": str(row.id),
                    "event_type": row.event_type,
                    "user_id": row.user_id,
                    "email": row.email,
                    "ip_address": row.ip_address,
                    "user_agent": row.user_agent,
                    "details": row.details,
                    "severity": row.severity,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []


def get_audit_service(db: AsyncSession = None) -> AuditService:
    """
    Dependency injection function for FastAPI endpoints.

    Returns an AuditService instance with database session.

    Usage in FastAPI:
        @router.get("/bookings")
        async def get_bookings(
            db: AsyncSession = Depends(get_db),
            audit: AuditService = Depends(get_audit_service)
        ):
            ...
    """
    return AuditService(db)
