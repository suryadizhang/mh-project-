"""
Security Audit Logger
=====================

Security event logging with database persistence and file backup.

This module handles security-specific events (authentication, authorization,
data access, security incidents) and writes them to:
1. security.security_events table (PRIMARY - for UI/queries)
2. Python logging (SECONDARY - for file backup/debugging)

For business action audit trails (CRUD operations), see:
    services/audit_service.py

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ==============================================================================
# Security Event Types (for consistency)
# ==============================================================================

class SecurityEventType:
    """Standard security event types for the security_events table."""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET_REQUEST = "password_reset_request"
    PASSWORD_RESET_COMPLETE = "password_reset_complete"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKED = "token_revoked"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_CHALLENGE = "mfa_challenge"

    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_ESCALATION = "permission_escalation"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"

    # Security incidents
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    SESSION_HIJACK_ATTEMPT = "session_hijack_attempt"
    IP_BLOCKED = "ip_blocked"

    # Data access events
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    BULK_DATA_EXPORT = "bulk_data_export"
    PII_ACCESS = "pii_access"


class SecuritySeverity:
    """Security event severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ==============================================================================
# Security Audit Logger Class
# ==============================================================================

class SecurityAuditLogger:
    """
    Security event logger with database persistence.

    Writes to security.security_events table AND Python logging.

    Usage (async with database):
        from core.security.audit import security_audit_logger

        await security_audit_logger.log_authentication_async(
            db=session,
            user_id=user.id,
            email=user.email,
            action="login_success",
            success=True,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            details={"method": "password"}
        )

    Usage (sync fallback - logs only, no DB):
        security_audit_logger.log_authentication(
            user_id=str(user.id),
            action="login_success",
            success=True,
            ip_address="127.0.0.1",
        )
    """

    def __init__(self, log_name: str = "security.audit"):
        """Initialize the security audit logger."""
        self.file_logger = logging.getLogger(log_name)

    # ==========================================================================
    # ASYNC METHODS (with database persistence) - PREFERRED
    # ==========================================================================

    async def log_authentication_async(
        self,
        db: AsyncSession,
        action: str,
        success: bool,
        ip_address: str,
        user_id: Optional[UUID] = None,
        email: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> Optional[UUID]:
        """
        Log authentication event to database and file.

        Args:
            db: Database session
            action: Event type (login_success, login_failure, logout, etc.)
            success: Whether the authentication succeeded
            ip_address: Client IP address
            user_id: User ID (may be None for failed attempts)
            email: User email (for failed attempts where user_id unknown)
            user_agent: Browser/client user agent
            details: Additional event details

        Returns:
            UUID of created security event, or None on error
        """
        event_type = action if success else f"{action}"
        severity = SecuritySeverity.LOW if success else SecuritySeverity.MEDIUM

        # Failed login attempts should be higher severity
        if not success and "login" in action.lower():
            severity = SecuritySeverity.MEDIUM

        event_details = {
            "success": success,
            "action": action,
            **(details or {}),
        }

        return await self._write_to_database(
            db=db,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            details=event_details,
        )

    async def log_authorization_async(
        self,
        db: AsyncSession,
        user_id: UUID,
        resource: str,
        action: str,
        allowed: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Optional[UUID]:
        """
        Log authorization decision to database and file.

        Args:
            db: Database session
            user_id: User who attempted the action
            resource: Resource being accessed
            action: Action being attempted
            allowed: Whether access was granted
            ip_address: Client IP address
            user_agent: Browser/client user agent
            reason: Reason for denial (if denied)

        Returns:
            UUID of created security event, or None on error
        """
        event_type = SecurityEventType.ACCESS_GRANTED if allowed else SecurityEventType.ACCESS_DENIED
        severity = SecuritySeverity.LOW if allowed else SecuritySeverity.MEDIUM

        details = {
            "resource": resource,
            "action": action,
            "allowed": allowed,
        }
        if reason:
            details["reason"] = reason

        return await self._write_to_database(
            db=db,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )

    async def log_data_access_async(
        self,
        db: AsyncSession,
        user_id: UUID,
        resource_type: str,
        resource_id: str,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        fields: Optional[list[str]] = None,
        is_sensitive: bool = False,
    ) -> Optional[UUID]:
        """
        Log data access event to database and file.

        Args:
            db: Database session
            user_id: User accessing the data
            resource_type: Type of resource (booking, customer, etc.)
            resource_id: ID of the resource
            action: Access action (read, export, etc.)
            ip_address: Client IP address
            user_agent: Browser/client user agent
            fields: Specific fields accessed
            is_sensitive: Whether this is sensitive data (PII, etc.)

        Returns:
            UUID of created security event, or None on error
        """
        event_type = SecurityEventType.SENSITIVE_DATA_ACCESS if is_sensitive else "data_access"
        severity = SecuritySeverity.MEDIUM if is_sensitive else SecuritySeverity.LOW

        details = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
        }
        if fields:
            details["fields"] = fields

        return await self._write_to_database(
            db=db,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )

    async def log_security_event_async(
        self,
        db: AsyncSession,
        event_type: str,
        severity: str,
        description: str,
        user_id: Optional[UUID] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> Optional[UUID]:
        """
        Log general security event to database and file.

        Args:
            db: Database session
            event_type: Type of security event (use SecurityEventType constants)
            severity: Severity level (use SecuritySeverity constants)
            description: Human-readable description
            user_id: Related user ID (if applicable)
            email: Related email (if applicable)
            ip_address: Client IP address
            user_agent: Browser/client user agent
            details: Additional event details

        Returns:
            UUID of created security event, or None on error
        """
        event_details = {
            "description": description,
            **(details or {}),
        }

        return await self._write_to_database(
            db=db,
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            details=event_details,
        )

    async def _write_to_database(
        self,
        db: AsyncSession,
        event_type: str,
        severity: str,
        user_id: Optional[UUID] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> Optional[UUID]:
        """
        Write security event to database and log to file.

        Returns:
            UUID of created event, or None on error
        """
        # Always log to file as backup
        file_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "severity": severity,
            "user_id": str(user_id) if user_id else None,
            "email": email,
            "ip_address": ip_address,
            "details": details,
        }

        if severity in [SecuritySeverity.CRITICAL, SecuritySeverity.HIGH]:
            self.file_logger.warning(json.dumps(file_event))
        else:
            self.file_logger.info(json.dumps(file_event))

        # Write to database
        try:
            result = await db.execute(
                text("""
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
                        :details::jsonb,
                        :severity
                    )
                    RETURNING id
                """),
                {
                    "event_type": event_type,
                    "user_id": str(user_id) if user_id else None,
                    "email": email,
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "details": json.dumps(details) if details else "{}",
                    "severity": severity,
                },
            )
            row = result.fetchone()
            await db.commit()

            if row:
                logger.debug(f"Security event logged: {event_type} (id={row[0]})")
                return row[0]
            return None

        except Exception as e:
            logger.error(f"Failed to write security event to database: {e}")
            # Event is still logged to file, so don't raise
            return None

    # ==========================================================================
    # SYNC METHODS (file logging only - for backwards compatibility)
    # ==========================================================================

    def log_authentication(
        self,
        user_id: str | None,
        action: str,
        success: bool,
        ip_address: str,
        details: dict | None = None,
    ):
        """
        Log authentication events (SYNC - file only).

        For database persistence, use log_authentication_async().
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "authentication",
            "user_id": user_id,
            "action": action,
            "success": success,
            "ip_address": ip_address,
            "details": details or {},
        }
        self.file_logger.info(json.dumps(event))

    def log_authorization(
        self,
        user_id: str,
        resource: str,
        action: str,
        allowed: bool,
        reason: str | None = None,
    ):
        """
        Log authorization decisions (SYNC - file only).

        For database persistence, use log_authorization_async().
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "authorization",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "allowed": allowed,
            "reason": reason,
        }
        self.file_logger.info(json.dumps(event))

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        fields: list[str] | None = None,
    ):
        """
        Log data access events (SYNC - file only).

        For database persistence, use log_data_access_async().
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "data_access",
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "fields": fields,
        }
        self.file_logger.info(json.dumps(event))

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        details: dict[str, Any] | None = None,
    ):
        """
        Log general security events (SYNC - file only).

        For database persistence, use log_security_event_async().
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "security_event",
            "event_type": event_type,
            "severity": severity,
            "description": description,
            "details": details or {},
        }
        if severity in ["critical", "high"]:
            self.file_logger.warning(json.dumps(event))
        else:
            self.file_logger.info(json.dumps(event))


# ==============================================================================
# Global Instances
# ==============================================================================

# New preferred name
security_audit_logger = SecurityAuditLogger()

# Legacy alias for backwards compatibility
audit_logger = security_audit_logger


# ==============================================================================
# Exports
# ==============================================================================

__all__ = [
    # Classes
    "SecurityAuditLogger",
    "SecurityEventType",
    "SecuritySeverity",
    # Instances
    "security_audit_logger",
    "audit_logger",  # Legacy alias
    # Legacy class name alias
    "AuditLogger",
]

# Legacy class alias for backwards compatibility
AuditLogger = SecurityAuditLogger
