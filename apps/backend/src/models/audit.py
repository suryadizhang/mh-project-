from datetime import timezone

"""
Audit logging models
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, TIMESTAMP, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, INET
from sqlalchemy.orm import relationship
from models.base import Base


class AuditLog(Base):
    """
    Audit log for tracking all database changes.

    Business Requirements:
    - Track all changes to critical tables (bookings, payments, users)
    - Store old and new values for comparison
    - Track who made the change and when
    - Track IP address and user agent for security
    """

    __tablename__ = "audit_logs"

    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    table_name: str = Column(String(100), nullable=False, index=True)
    record_id: Optional[UUID] = Column(PGUUID(as_uuid=True), nullable=True, index=True)
    action: str = Column(String(20), nullable=False, index=True)  # INSERT, UPDATE, DELETE

    # Change tracking
    old_values: Optional[Dict[str, Any]] = Column(JSONB, nullable=True)
    new_values: Optional[Dict[str, Any]] = Column(JSONB, nullable=True)
    changed_fields: Optional[List[str]] = Column(ARRAY(Text), nullable=True)

    # User tracking
    user_id: Optional[UUID] = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_email: Optional[str] = Column(String(255), nullable=True)

    # Security tracking
    ip_address: Optional[str] = Column(INET, nullable=True)
    user_agent: Optional[str] = Column(Text, nullable=True)

    timestamp: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    user = relationship("models.user.User", foreign_keys=[user_id], back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.table_name} at {self.timestamp}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "table_name": self.table_name,
            "record_id": str(self.record_id) if self.record_id else None,
            "action": self.action,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "changed_fields": self.changed_fields,
            "user_id": str(self.user_id) if self.user_id else None,
            "user_email": self.user_email,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class SecurityAuditLog(Base):
    """
    Security audit log for high-value security events.

    Tracks:
    - Login attempts (success and failures)
    - Logout events
    - Permission changes
    - Password changes
    - 2FA setup/disable
    - IP verification events
    """

    __tablename__ = "security_audit_logs"

    id: UUID = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: str = Column(String(50), nullable=False, index=True)

    # User tracking
    user_id: Optional[UUID] = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    target_user_id: Optional[UUID] = Column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Event details
    description: str = Column(Text, nullable=False)
    event_metadata: Optional[Dict[str, Any]] = Column(JSONB, nullable=True)

    # Security context
    ip_address: Optional[str] = Column(INET, nullable=True)
    user_agent: Optional[str] = Column(Text, nullable=True)
    success: bool = Column(Boolean, default=True, index=True)
    failure_reason: Optional[str] = Column(Text, nullable=True)

    timestamp: datetime = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    # Relationships
    user = relationship(
        "models.user.User", foreign_keys=[user_id], back_populates="security_audit_logs"
    )
    target_user = relationship("models.user.User", foreign_keys=[target_user_id])

    def __repr__(self):
        return f"<SecurityAuditLog {self.event_type} at {self.timestamp}>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "event_type": self.event_type,
            "user_id": str(self.user_id) if self.user_id else None,
            "target_user_id": str(self.target_user_id) if self.target_user_id else None,
            "description": self.description,
            "metadata": self.event_metadata,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "success": self.success,
            "failure_reason": self.failure_reason,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
