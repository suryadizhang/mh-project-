"""
Audit Logs Router - Super Admin System Activity Viewer
=======================================================

Provides comprehensive audit log viewing for super admins.
Aggregates data from:
- audit_logs table (admin actions)
- security.security_events (security events)
- config_audit_log (configuration changes)

Endpoints:
- GET /admin/audit-logs - List all audit logs with filters
- GET /admin/audit-logs/stats - Get audit log statistics
- GET /admin/audit-logs/actions - Get list of action types
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.auth import require_roles
from core.config import UserRole

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


# Action category mapping for computed field
ACTION_CATEGORY_MAP = {
    # Authentication actions
    "LOGIN": "authentication",
    "LOGOUT": "authentication",
    "LOGIN_FAILED": "authentication",
    "PASSWORD_CHANGE": "authentication",
    "TOKEN_REFRESH": "authentication",
    "API_KEY_CREATED": "authentication",
    "API_KEY_REVOKED": "authentication",
    # Data change actions
    "CREATE": "data_change",
    "UPDATE": "data_change",
    "DELETE": "data_change",
    "SOFT_DELETE": "data_change",
    "RESTORE": "data_change",
    "BOOKING_CREATED": "data_change",
    "BOOKING_UPDATED": "data_change",
    "BOOKING_CANCELED": "data_change",
    "CUSTOMER_CREATED": "data_change",
    "CUSTOMER_UPDATED": "data_change",
    "CONFIG_CHANGE": "data_change",
    # Security actions
    "SECURITY_ALERT": "security",
    "SUSPICIOUS_ACTIVITY": "security",
    "ACCESS_DENIED": "security",
    "BRUTE_FORCE_DETECTED": "security",
    "IP_BLOCKED": "security",
    "RATE_LIMIT_EXCEEDED": "security",
    # System actions
    "SYSTEM_START": "system",
    "SYSTEM_STOP": "system",
    "CACHE_CLEAR": "system",
    "MIGRATION_RUN": "system",
    "BACKUP_CREATED": "system",
}

# Severity mapping for computed field
ACTION_SEVERITY_MAP = {
    # Critical severity
    "DELETE": "critical",
    "SOFT_DELETE": "critical",
    "SECURITY_ALERT": "critical",
    "BRUTE_FORCE_DETECTED": "critical",
    "IP_BLOCKED": "critical",
    # Warning severity
    "LOGIN_FAILED": "warning",
    "ACCESS_DENIED": "warning",
    "SUSPICIOUS_ACTIVITY": "warning",
    "RATE_LIMIT_EXCEEDED": "warning",
    "BOOKING_CANCELED": "warning",
    # Info severity (default)
    "LOGIN": "info",
    "LOGOUT": "info",
    "CREATE": "info",
    "UPDATE": "info",
    "RESTORE": "info",
    "CONFIG_CHANGE": "info",
}


def _get_action_category(action: str) -> str:
    """Get action category from action type."""
    return ACTION_CATEGORY_MAP.get(action.upper(), "system")


def _get_severity(action: str, success: Optional[bool] = True) -> str:
    """Get severity level from action type and success status."""
    if success is False:
        return "error"
    return ACTION_SEVERITY_MAP.get(action.upper(), "info")


def _generate_description(
    action: str,
    resource_type: Optional[str],
    resource_id: Optional[str],
    user_email: Optional[str],
) -> str:
    """Generate human-readable description from action and resource."""
    action_lower = action.lower().replace("_", " ")
    if resource_type and resource_id:
        return f"{action_lower.title()} {resource_type} ({resource_id[:8]}...)"
    elif resource_type:
        return f"{action_lower.title()} {resource_type}"
    elif user_email:
        return f"{action_lower.title()} by {user_email}"
    return action_lower.title()


class AuditLogEntry(BaseModel):
    """
    Single audit log entry.

    Provides both internal field names and frontend-expected aliases.
    Frontend expects: action_type, action_category, target_type, target_id, severity, description
    Backend stores: action, resource_type, resource_id
    """

    model_config = {"populate_by_name": True}

    id: str
    created_at: datetime

    # User info
    user_id: Optional[str] = None
    user_role: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    # Action fields - with frontend aliases
    action: str = Field(..., serialization_alias="action_type")
    resource_type: Optional[str] = Field(None, serialization_alias="target_type")
    resource_id: Optional[str] = Field(None, serialization_alias="target_id")
    resource_name: Optional[str] = None

    # Request info - frontend expects these
    request_method: Optional[str] = None
    request_path: Optional[str] = None
    status_code: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Additional context
    station_id: Optional[str] = None
    delete_reason: Optional[str] = None
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    metadata: Optional[dict] = None
    success: Optional[bool] = True
    error_message: Optional[str] = None
    source: str = "audit_logs"  # audit_logs, security_events, config_audit

    # Computed fields for frontend compatibility
    action_category: Optional[str] = None
    description: Optional[str] = None
    severity: str = "info"

    def model_post_init(self, __context):
        """Compute derived fields after initialization."""
        # Compute action_category if not provided
        if self.action_category is None:
            self.action_category = _get_action_category(self.action)

        # Compute severity if still default
        if self.severity == "info":
            self.severity = _get_severity(self.action, self.success)

        # Compute description if not provided
        if self.description is None:
            self.description = _generate_description(
                self.action, self.resource_type, self.resource_id, self.user_email
            )


class AuditLogListResponse(BaseModel):
    """
    Paginated audit log response.

    Frontend expects:
    - 'data' field containing the entries (serialized from 'entries')
    - 'total' for total count
    - 'page_size' for limit (serialized from 'limit')
    """

    model_config = {"populate_by_name": True}

    entries: list[AuditLogEntry] = Field(..., serialization_alias="data")
    total: int
    page: int
    limit: int = Field(..., serialization_alias="page_size")
    total_pages: int
    has_more: bool


class AuditLogStatsResponse(BaseModel):
    """
    Audit log statistics.

    Provides both internal field names and frontend-expected aliases.
    """

    model_config = {"populate_by_name": True}

    # Core stats - with frontend aliases
    total_entries: int = Field(..., serialization_alias="total_events")
    entries_today: int = Field(..., serialization_alias="events_today")
    entries_this_week: int = Field(..., serialization_alias="events_this_week")

    # Breakdown data
    actions_breakdown: dict[str, int]
    top_users: list[dict]
    top_resources: list[dict]

    # Additional stats for frontend
    security_events: int = 0
    authentication_events: int = 0
    data_change_events: int = 0
    system_events: int = 0
    unique_users: int = 0
    failed_actions: int = 0
    success_rate: float = 100.0


class ActionTypesResponse(BaseModel):
    """
    List of available action types for filtering.

    Provides both internal field names and frontend-expected aliases.
    """

    model_config = {"populate_by_name": True}

    # Field mappings for frontend
    actions: list[str] = Field(default_factory=list, serialization_alias="action_types")
    resource_types: list[str] = Field(default_factory=list, serialization_alias="target_types")

    # Additional filter options for frontend
    action_categories: list[str] = Field(
        default_factory=lambda: ["authentication", "data_change", "security", "system"]
    )
    severities: list[str] = Field(
        default_factory=lambda: ["info", "warning", "error", "critical"]
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/", response_model=AuditLogListResponse)
async def get_audit_logs(
    # Accept both 'action' and 'action_type' from frontend
    action: Optional[str] = Query(None, description="Filter by action type (VIEW, CREATE, UPDATE, DELETE, LOGIN, etc.)"),
    action_type: Optional[str] = Query(None, description="Alias for action (frontend compatibility)"),
    # Accept both 'resource_type' and 'target_type' from frontend
    resource_type: Optional[str] = Query(None, description="Filter by resource type (booking, customer, user, etc.)"),
    target_type: Optional[str] = Query(None, description="Alias for resource_type (frontend compatibility)"),
    # New action_category filter for frontend
    action_category: Optional[str] = Query(None, description="Filter by category (authentication, data_change, security, system)"),
    # New severity filter for frontend
    severity: Optional[str] = Query(None, description="Filter by severity (info, warning, error, critical)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    user_email: Optional[str] = Query(None, description="Filter by user email (partial match)"),
    station_id: Optional[str] = Query(None, description="Filter by station ID"),
    # Accept both 'start_date' and 'date_from' from frontend
    start_date: Optional[datetime] = Query(None, description="Filter by start date (ISO format)"),
    date_from: Optional[datetime] = Query(None, description="Alias for start_date (frontend compatibility)"),
    # Accept both 'end_date' and 'date_to' from frontend
    end_date: Optional[datetime] = Query(None, description="Filter by end date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="Alias for end_date (frontend compatibility)"),
    days: int = Query(7, ge=1, le=365, description="Number of days to look back (default: 7)"),
    search: Optional[str] = Query(None, description="Search in resource_name, user_name, user_email"),
    include_security: bool = Query(True, description="Include security events"),
    include_config: bool = Query(True, description="Include configuration changes"),
    page: int = Query(1, ge=1, description="Page number"),
    # Accept both 'limit' and 'page_size' from frontend
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    page_size: Optional[int] = Query(None, ge=1, le=200, description="Alias for limit (frontend compatibility)"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """
    Get comprehensive audit logs for super admin.

    Aggregates data from multiple sources:
    - Main audit_logs table
    - Security events (login, failed attempts, etc.)
    - Configuration change logs

    Supports frontend query params:
    - action_type (aliased to action)
    - target_type (aliased to resource_type)
    - action_category (new filter)
    - severity (new filter)
    - date_from / date_to (aliased to start_date / end_date)
    - page_size (aliased to limit)

    Requires SUPER_ADMIN role.
    """
    try:
        # Normalize filter params (accept both old and new names)
        effective_action = action_type or action
        effective_resource_type = target_type or resource_type
        effective_start_date = date_from or start_date
        effective_end_date = date_to or end_date
        effective_limit = page_size or limit

        # Calculate date range
        if not effective_start_date:
            effective_start_date = datetime.now(timezone.utc) - timedelta(days=days)
        if not effective_end_date:
            effective_end_date = datetime.now(timezone.utc)

        offset = (page - 1) * effective_limit
        entries = []
        total = 0

        # Build main audit_logs query
        conditions = ["created_at >= :start_date", "created_at <= :end_date"]
        params: dict[str, Any] = {
            "start_date": effective_start_date,
            "end_date": effective_end_date,
            "limit": effective_limit,
            "offset": offset,
        }

        if effective_action:
            conditions.append("action = :action")
            params["action"] = effective_action.upper()

        if effective_resource_type:
            conditions.append("resource_type = :resource_type")
            params["resource_type"] = effective_resource_type

        if user_id:
            conditions.append("user_id = :user_id")
            params["user_id"] = user_id

        if user_email:
            conditions.append("LOWER(user_email) LIKE :user_email")
            params["user_email"] = f"%{user_email.lower()}%"

        if station_id:
            conditions.append("station_id = :station_id")
            params["station_id"] = station_id

        if search:
            conditions.append(
                "(LOWER(resource_name) LIKE :search OR LOWER(user_name) LIKE :search OR LOWER(user_email) LIKE :search)"
            )
            params["search"] = f"%{search.lower()}%"

        # Filter by action_category (computed field - map to actual actions)
        if action_category:
            category_actions = [
                act for act, cat in ACTION_CATEGORY_MAP.items()
                if cat == action_category.lower()
            ]
            if category_actions:
                action_placeholders = ", ".join([f":cat_action_{i}" for i in range(len(category_actions))])
                conditions.append(f"action IN ({action_placeholders})")
                for i, act in enumerate(category_actions):
                    params[f"cat_action_{i}"] = act

        # Filter by severity (computed field - map to actual actions)
        if severity:
            severity_actions = [
                act for act, sev in ACTION_SEVERITY_MAP.items()
                if sev == severity.lower()
            ]
            if severity_actions:
                sev_placeholders = ", ".join([f":sev_action_{i}" for i in range(len(severity_actions))])
                conditions.append(f"action IN ({sev_placeholders})")
                for i, act in enumerate(severity_actions):
                    params[f"sev_action_{i}"] = act

        where_clause = " AND ".join(conditions)

        # Get total count
        count_query = text(f"""
            SELECT COUNT(*) as total
            FROM audit_logs
            WHERE {where_clause}
        """)
        count_result = await db.execute(count_query, params)
        total = count_result.scalar() or 0

        # Get paginated entries
        main_query = text(f"""
            SELECT
                id::text,
                created_at,
                user_id::text,
                user_role,
                user_name,
                user_email,
                action,
                resource_type,
                resource_id,
                resource_name,
                ip_address,
                user_agent,
                station_id::text,
                delete_reason,
                old_values,
                new_values,
                metadata,
                TRUE as success,
                NULL as error_message,
                'audit_logs' as source
            FROM audit_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)

        result = await db.execute(main_query, params)
        rows = result.fetchall()

        for row in rows:
            entries.append(AuditLogEntry(
                id=row.id,
                created_at=row.created_at,
                user_id=row.user_id,
                user_role=row.user_role,
                user_name=row.user_name,
                user_email=row.user_email,
                action=row.action,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                resource_name=row.resource_name,
                ip_address=row.ip_address,
                user_agent=row.user_agent,
                station_id=row.station_id,
                delete_reason=row.delete_reason,
                old_values=row.old_values,
                new_values=row.new_values,
                metadata=row.metadata,
                success=row.success,
                error_message=row.error_message,
                source=row.source,
            ))

        # Optionally include security events (only when not filtering by specific action/resource)
        if include_security and not effective_action and not effective_resource_type:
            try:
                security_query = text("""
                    SELECT
                        id::text,
                        created_at,
                        user_id::text,
                        NULL as user_role,
                        NULL as user_name,
                        email as user_email,
                        event_type as action,
                        'security' as resource_type,
                        NULL as resource_id,
                        severity as resource_name,
                        ip_address,
                        user_agent,
                        NULL as station_id,
                        NULL as delete_reason,
                        NULL as old_values,
                        details as new_values,
                        NULL as metadata,
                        is_resolved as success,
                        NULL as error_message,
                        'security_events' as source
                    FROM security.security_events
                    WHERE created_at >= :start_date AND created_at <= :end_date
                    ORDER BY created_at DESC
                    LIMIT 20
                """)
                sec_result = await db.execute(security_query, {
                    "start_date": effective_start_date,
                    "end_date": effective_end_date,
                })
                sec_rows = sec_result.fetchall()

                for row in sec_rows:
                    entries.append(AuditLogEntry(
                        id=row.id,
                        created_at=row.created_at,
                        user_id=row.user_id,
                        user_role=row.user_role,
                        user_name=row.user_name,
                        user_email=row.user_email,
                        action=row.action,
                        resource_type=row.resource_type,
                        resource_id=row.resource_id,
                        resource_name=row.resource_name,
                        ip_address=row.ip_address,
                        user_agent=row.user_agent,
                        station_id=row.station_id,
                        delete_reason=row.delete_reason,
                        old_values=row.old_values,
                        new_values=row.new_values,
                        metadata=row.metadata,
                        success=row.success,
                        error_message=row.error_message,
                        source=row.source,
                    ))
            except Exception as e:
                logger.warning(f"Could not fetch security events: {e}")

        # Optionally include config audit log
        if include_config and not effective_action and not effective_resource_type:
            try:
                config_query = text("""
                    SELECT
                        id::text,
                        changed_at as created_at,
                        changed_by::text as user_id,
                        NULL as user_role,
                        NULL as user_name,
                        NULL as user_email,
                        'CONFIG_CHANGE' as action,
                        'config' as resource_type,
                        key as resource_id,
                        category as resource_name,
                        NULL as ip_address,
                        NULL as user_agent,
                        NULL as station_id,
                        change_reason as delete_reason,
                        old_value as old_values,
                        new_value as new_values,
                        NULL as metadata,
                        TRUE as success,
                        NULL as error_message,
                        'config_audit' as source
                    FROM config_audit_log
                    WHERE changed_at >= :start_date AND changed_at <= :end_date
                    ORDER BY changed_at DESC
                    LIMIT 20
                """)
                config_result = await db.execute(config_query, {
                    "start_date": effective_start_date,
                    "end_date": effective_end_date,
                })
                config_rows = config_result.fetchall()

                for row in config_rows:
                    entries.append(AuditLogEntry(
                        id=row.id,
                        created_at=row.created_at,
                        user_id=row.user_id,
                        user_role=row.user_role,
                        user_name=row.user_name,
                        user_email=row.user_email,
                        action=row.action,
                        resource_type=row.resource_type,
                        resource_id=row.resource_id,
                        resource_name=row.resource_name,
                        ip_address=row.ip_address,
                        user_agent=row.user_agent,
                        station_id=row.station_id,
                        delete_reason=row.delete_reason,
                        old_values=row.old_values,
                        new_values=row.new_values,
                        metadata=row.metadata,
                        success=row.success,
                        error_message=row.error_message,
                        source=row.source,
                    ))
            except Exception as e:
                logger.warning(f"Could not fetch config audit log: {e}")

        # Sort all entries by created_at descending
        entries.sort(key=lambda x: x.created_at, reverse=True)

        # Limit to page size
        entries = entries[:effective_limit]

        total_pages = (total + effective_limit - 1) // effective_limit

        return AuditLogListResponse(
            entries=entries,
            total=total,
            page=page,
            limit=effective_limit,
            total_pages=total_pages,
            has_more=page < total_pages,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs",
        )


@router.get("/stats", response_model=AuditLogStatsResponse)
async def get_audit_stats(
    days: int = Query(7, ge=1, le=30, description="Number of days for stats"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """
    Get audit log statistics for dashboard.

    Provides:
    - Total entries (aliased as total_events for frontend)
    - Entries today (aliased as events_today)
    - Entries this week (aliased as events_this_week)
    - Action type breakdown
    - Top users by activity
    - Top resource types
    - Security events count
    - Authentication events count
    - Data change events count
    - Unique users count
    - Failed actions count
    - Success rate
    """
    try:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=days)

        # Total entries
        total_query = text("SELECT COUNT(*) FROM audit_logs")
        total_result = await db.execute(total_query)
        total_entries = total_result.scalar() or 0

        # Entries today
        today_query = text("SELECT COUNT(*) FROM audit_logs WHERE created_at >= :today")
        today_result = await db.execute(today_query, {"today": today_start})
        entries_today = today_result.scalar() or 0

        # Entries this week
        week_query = text("SELECT COUNT(*) FROM audit_logs WHERE created_at >= :week_start")
        week_result = await db.execute(week_query, {"week_start": week_start})
        entries_this_week = week_result.scalar() or 0

        # Actions breakdown
        actions_query = text("""
            SELECT action, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= :week_start
            GROUP BY action
            ORDER BY count DESC
            LIMIT 10
        """)
        actions_result = await db.execute(actions_query, {"week_start": week_start})
        actions_breakdown = {row.action: row.count for row in actions_result.fetchall()}

        # Top users
        users_query = text("""
            SELECT user_email, user_name, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= :week_start AND user_email IS NOT NULL
            GROUP BY user_email, user_name
            ORDER BY count DESC
            LIMIT 5
        """)
        users_result = await db.execute(users_query, {"week_start": week_start})
        top_users = [
            {"email": row.user_email, "name": row.user_name, "count": row.count}
            for row in users_result.fetchall()
        ]

        # Top resources
        resources_query = text("""
            SELECT resource_type, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= :week_start AND resource_type IS NOT NULL
            GROUP BY resource_type
            ORDER BY count DESC
            LIMIT 5
        """)
        resources_result = await db.execute(resources_query, {"week_start": week_start})
        top_resources = [
            {"type": row.resource_type, "count": row.count}
            for row in resources_result.fetchall()
        ]

        # === Additional stats for frontend compatibility ===

        # Unique users count
        unique_users_query = text("""
            SELECT COUNT(DISTINCT user_id) FROM audit_logs
            WHERE created_at >= :week_start AND user_id IS NOT NULL
        """)
        unique_users_result = await db.execute(unique_users_query, {"week_start": week_start})
        unique_users = unique_users_result.scalar() or 0

        # Failed actions count (success = false)
        failed_query = text("""
            SELECT COUNT(*) FROM audit_logs
            WHERE created_at >= :week_start AND success = false
        """)
        failed_result = await db.execute(failed_query, {"week_start": week_start})
        failed_actions = failed_result.scalar() or 0

        # Success rate calculation
        success_rate = 100.0
        if entries_this_week > 0:
            success_rate = round(((entries_this_week - failed_actions) / entries_this_week) * 100, 2)

        # Count events by category using the action type mappings
        # Security events (from security_events table or action patterns)
        security_events = 0
        try:
            sec_count_query = text("SELECT COUNT(*) FROM security.security_events WHERE created_at >= :week_start")
            sec_count_result = await db.execute(sec_count_query, {"week_start": week_start})
            security_events = sec_count_result.scalar() or 0
        except Exception:
            # Table might not exist
            pass

        # Count by action category from actions_breakdown
        authentication_events = 0
        data_change_events = 0
        system_events = 0

        for action, count in actions_breakdown.items():
            category = _get_action_category(action)
            if category == "authentication":
                authentication_events += count
            elif category == "data_change":
                data_change_events += count
            elif category == "security":
                security_events += count
            elif category == "system":
                system_events += count

        return AuditLogStatsResponse(
            total_entries=total_entries,
            entries_today=entries_today,
            entries_this_week=entries_this_week,
            actions_breakdown=actions_breakdown,
            top_users=top_users,
            top_resources=top_resources,
            security_events=security_events,
            authentication_events=authentication_events,
            data_change_events=data_change_events,
            system_events=system_events,
            unique_users=unique_users,
            failed_actions=failed_actions,
            success_rate=success_rate,
        )

    except Exception as e:
        logger.exception(f"Error fetching audit stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit statistics",
        )


@router.get("/actions", response_model=ActionTypesResponse)
async def get_action_types(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_roles([UserRole.SUPER_ADMIN])),
):
    """
    Get list of available action types and resource types for filtering.
    """
    try:
        # Get distinct actions
        actions_query = text("""
            SELECT DISTINCT action FROM audit_logs
            WHERE action IS NOT NULL
            ORDER BY action
        """)
        actions_result = await db.execute(actions_query)
        actions = [row.action for row in actions_result.fetchall()]

        # Get distinct resource types
        resources_query = text("""
            SELECT DISTINCT resource_type FROM audit_logs
            WHERE resource_type IS NOT NULL
            ORDER BY resource_type
        """)
        resources_result = await db.execute(resources_query)
        resource_types = [row.resource_type for row in resources_result.fetchall()]

        return ActionTypesResponse(
            actions=actions,
            resource_types=resource_types,
        )

    except Exception as e:
        logger.exception(f"Error fetching action types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve action types",
        )
