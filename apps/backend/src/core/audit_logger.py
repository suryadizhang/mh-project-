"""
Comprehensive Audit Logging Service for Admin Actions

This service logs all administrative actions (VIEW, CREATE, UPDATE, DELETE) with full context:
- WHO: user_id, role, name, email
- WHAT: action, resource_type, resource_id
- WHEN: timestamp
- WHERE: IP address, user_agent, station_id
- WHY: delete_reason (mandatory for DELETE)
- DETAILS: old_values, new_values (JSON)

Usage:
    from core.audit_logger import audit_logger

    # Log a delete action
    await audit_logger.log_delete(
        session=db,
        user=current_user,
        resource_type="booking",
        resource_id=booking_id,
        resource_name=f"{booking.customer_name} - {booking.booking_date}",
        delete_reason=request.delete_reason,
        old_values=booking.to_dict(),
        ip_address=request.client.host,
        station_id=booking.station_id
    )
"""

from datetime import datetime
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Enterprise-grade audit logging service.
    Tracks all admin actions with full context for compliance (GDPR, SOC 2).
    """

    VALID_ACTIONS = {"VIEW", "CREATE", "UPDATE", "DELETE"}
    MIN_DELETE_REASON_LENGTH = 10
    MAX_DELETE_REASON_LENGTH = 500

    @staticmethod
    async def log(
        session: AsyncSession,
        user: dict[str, Any],
        action: str,
        resource_type: str,
        resource_id: str,
        resource_name: str | None = None,
        delete_reason: str | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        station_id: UUID | None = None,
    ) -> UUID:
        """
        Log an admin action to audit_logs table.

        Args:
            session: AsyncSession - Database session
            user: Dict - Current user (must have: id, role, name/email)
            action: str - One of: VIEW, CREATE, UPDATE, DELETE
            resource_type: str - Type of resource (booking, customer, lead, etc)
            resource_id: str - ID of affected resource
            resource_name: Optional[str] - Friendly name for UI display
            delete_reason: Optional[str] - Reason for deletion (REQUIRED for DELETE actions)
            old_values: Optional[Dict] - State before change
            new_values: Optional[Dict] - State after change
            metadata: Optional[Dict] - Additional context
            ip_address: Optional[str] - Request IP address
            user_agent: Optional[str] - Browser/device info
            station_id: Optional[UUID] - Station context

        Returns:
            UUID: ID of created audit log entry

        Raises:
            ValueError: If validation fails (invalid action, missing delete reason, etc)
        """

        # Validate action
        if action not in AuditLogger.VALID_ACTIONS:
            raise ValueError(
                f"Invalid action '{action}'. Must be one of: {AuditLogger.VALID_ACTIONS}"
            )

        # Validate DELETE actions have reason
        if action == "DELETE":
            if not delete_reason:
                raise ValueError("Delete actions require a reason")

            if len(delete_reason) < AuditLogger.MIN_DELETE_REASON_LENGTH:
                raise ValueError(
                    f"Delete reason must be at least {AuditLogger.MIN_DELETE_REASON_LENGTH} characters"
                )

            if len(delete_reason) > AuditLogger.MAX_DELETE_REASON_LENGTH:
                raise ValueError(
                    f"Delete reason must be at most {AuditLogger.MAX_DELETE_REASON_LENGTH} characters"
                )

        # Extract user information
        user_id = user.get("id") or user.get("user_id")
        user_role = user.get("role")
        user_name = user.get("name") or user.get("full_name") or user.get("email", "Unknown")
        user_email = user.get("email", "unknown@unknown.com")

        if not user_id:
            raise ValueError("User must have an 'id' field")

        if not user_role:
            raise ValueError("User must have a 'role' field")

        # Prepare metadata
        if metadata is None:
            metadata = {}

        # Add timestamp to metadata
        metadata["logged_at"] = datetime.utcnow().isoformat()

        # Insert audit log
        query = text(
            """
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
                station_id,
                delete_reason,
                old_values,
                new_values,
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
                :station_id,
                :delete_reason,
                :old_values::jsonb,
                :new_values::jsonb,
                :metadata::jsonb
            )
            RETURNING id
        """
        )

        result = await session.execute(
            query,
            {
                "user_id": str(user_id),
                "user_role": user_role,
                "user_name": user_name,
                "user_email": user_email,
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
                "resource_name": resource_name,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "station_id": str(station_id) if station_id else None,
                "delete_reason": delete_reason,
                "old_values": old_values,
                "new_values": new_values,
                "metadata": metadata,
            },
        )

        audit_log_id = result.scalar_one()

        # Commit is handled by caller
        # await session.commit()

        logger.info(
            f"Audit log created: {action} {resource_type}/{resource_id} by {user_name} ({user_role})",
            extra={
                "audit_log_id": str(audit_log_id),
                "user_id": str(user_id),
                "action": action,
                "resource_type": resource_type,
                "resource_id": str(resource_id),
            },
        )

        return audit_log_id

    @staticmethod
    async def log_view(
        session: AsyncSession, user: dict, resource_type: str, resource_id: str, **kwargs
    ) -> UUID:
        """
        Log a VIEW action (user viewed sensitive data).

        Example:
            await audit_logger.log_view(
                session=db,
                user=current_user,
                resource_type="customer",
                resource_id=customer_id,
                resource_name=customer.full_name,
                metadata={"view_type": "profile_page"}
            )
        """
        return await AuditLogger.log(session, user, "VIEW", resource_type, resource_id, **kwargs)

    @staticmethod
    async def log_create(
        session: AsyncSession,
        user: dict,
        resource_type: str,
        resource_id: str,
        new_values: dict,
        **kwargs,
    ) -> UUID:
        """
        Log a CREATE action (user created new resource).

        Example:
            await audit_logger.log_create(
                session=db,
                user=current_user,
                resource_type="booking",
                resource_id=booking.id,
                resource_name=f"{booking.customer_name} - {booking.booking_date}",
                new_values={
                    "customer_name": booking.customer_name,
                    "booking_date": str(booking.booking_date),
                    "total_amount": float(booking.total_amount)
                },
                station_id=booking.station_id
            )
        """
        return await AuditLogger.log(
            session, user, "CREATE", resource_type, resource_id, new_values=new_values, **kwargs
        )

    @staticmethod
    async def log_update(
        session: AsyncSession,
        user: dict,
        resource_type: str,
        resource_id: str,
        old_values: dict,
        new_values: dict,
        **kwargs,
    ) -> UUID:
        """
        Log an UPDATE action (user modified existing resource).

        Example:
            await audit_logger.log_update(
                session=db,
                user=current_user,
                resource_type="customer",
                resource_id=customer.id,
                resource_name=customer.full_name,
                old_values={"email": "old@example.com", "phone": "555-0100"},
                new_values={"email": "new@example.com", "phone": "555-0199"},
                metadata={"reason": "Customer requested update"}
            )
        """
        return await AuditLogger.log(
            session,
            user,
            "UPDATE",
            resource_type,
            resource_id,
            old_values=old_values,
            new_values=new_values,
            **kwargs,
        )

    @staticmethod
    async def log_delete(
        session: AsyncSession,
        user: dict,
        resource_type: str,
        resource_id: str,
        delete_reason: str,
        old_values: dict,
        **kwargs,
    ) -> UUID:
        """
        Log a DELETE action (user deleted resource).

        DELETE actions REQUIRE a reason (min 10 characters).

        Example:
            await audit_logger.log_delete(
                session=db,
                user=current_user,
                resource_type="booking",
                resource_id=booking.id,
                resource_name=f"{booking.customer_name} - {booking.booking_date}",
                delete_reason="Customer requested cancellation due to weather concerns",
                old_values={
                    "customer_name": booking.customer_name,
                    "booking_date": str(booking.booking_date),
                    "status": booking.status,
                    "total_amount": float(booking.total_amount)
                },
                station_id=booking.station_id,
                metadata={"refund_processed": True, "refund_amount": 450.00}
            )
        """
        return await AuditLogger.log(
            session,
            user,
            "DELETE",
            resource_type,
            resource_id,
            delete_reason=delete_reason,
            old_values=old_values,
            **kwargs,
        )

    @staticmethod
    async def get_logs(
        session: AsyncSession,
        user_id: UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        station_id: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """
        Query audit logs with filters.

        Args:
            session: Database session
            user_id: Filter by user
            action: Filter by action type
            resource_type: Filter by resource type
            resource_id: Filter by specific resource
            station_id: Filter by station
            start_date: Filter by date range (start)
            end_date: Filter by date range (end)
            limit: Max results
            offset: Pagination offset

        Returns:
            List of audit log dictionaries
        """

        # Build dynamic query
        conditions = []
        params = {}

        if user_id:
            conditions.append("user_id = :user_id")
            params["user_id"] = str(user_id)

        if action:
            conditions.append("action = :action")
            params["action"] = action

        if resource_type:
            conditions.append("resource_type = :resource_type")
            params["resource_type"] = resource_type

        if resource_id:
            conditions.append("resource_id = :resource_id")
            params["resource_id"] = resource_id

        if station_id:
            conditions.append("station_id = :station_id")
            params["station_id"] = str(station_id)

        if start_date:
            conditions.append("created_at >= :start_date")
            params["start_date"] = start_date

        if end_date:
            conditions.append("created_at <= :end_date")
            params["end_date"] = end_date

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = text(
            f"""
            SELECT
                id,
                created_at,
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
                station_id,
                delete_reason,
                old_values,
                new_values,
                metadata
            FROM audit_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        )

        params["limit"] = limit
        params["offset"] = offset

        result = await session.execute(query, params)
        rows = result.fetchall()

        return [dict(row._mapping) for row in rows]


# Singleton instance
audit_logger = AuditLogger()
