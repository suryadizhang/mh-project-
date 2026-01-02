"""
Audit Logger
============

Security event logging for audit trails.

See: .github/instructions/22-QUALITY_CONTROL.instructions.md for modularization standards
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit trail for security events"""

    def __init__(self, log_name: str = "security.audit"):
        self.audit_logger = logging.getLogger(log_name)

    def log_authentication(
        self,
        user_id: str | None,
        action: str,
        success: bool,
        ip_address: str,
        details: dict | None = None,
    ):
        """Log authentication events"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "authentication",
            "user_id": user_id,
            "action": action,
            "success": success,
            "ip_address": ip_address,
            "details": details or {},
        }
        self.audit_logger.info(json.dumps(event))

    def log_authorization(
        self,
        user_id: str,
        resource: str,
        action: str,
        allowed: bool,
        reason: str | None = None,
    ):
        """Log authorization decisions"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "authorization",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "allowed": allowed,
            "reason": reason,
        }
        self.audit_logger.info(json.dumps(event))

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        fields: list[str] | None = None,
    ):
        """Log data access events"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "data_access",
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            "fields": fields,
        }
        self.audit_logger.info(json.dumps(event))

    def log_security_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        details: dict[str, Any] | None = None,
    ):
        """Log general security events"""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "security_event",
            "event_type": event_type,
            "severity": severity,
            "description": description,
            "details": details or {},
        }
        if severity in ["critical", "high"]:
            self.audit_logger.warning(json.dumps(event))
        else:
            self.audit_logger.info(json.dumps(event))


# Global audit logger instance
audit_logger = AuditLogger()


__all__ = [
    "AuditLogger",
    "audit_logger",
]
