"""
SQLAlchemy Model - System Events
==================================

System event tracking for analytics, auditing, and debugging.
Used by EventService for centralized event tracking.

Migrated from: models.system_event (OLD)
Location: db.models.system_event (NEW)
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..base_class import Base


class SystemEvent(Base):
    """
    System event tracking for analytics and audit trails.

    Stores events from all services including:
    - User actions (login, profile updates, etc.)
    - Business events (lead created, booking confirmed, etc.)
    - System events (errors, warnings, etc.)
    - Audit trail for compliance

    Indexed for efficient querying by:
    - entity_type + entity_id (get all events for a specific entity)
    - user_id (get all events for a user)
    - service + action (analytics by service/action)
    - timestamp (chronological queries)
    - severity (error tracking)
    """

    __tablename__ = "system_events"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)

    # Event identification
    service: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Service that logged the event (e.g., 'LeadService', 'BookingService')",
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Action performed (e.g., 'lead_created', 'booking_confirmed')",
    )

    # Entity reference (what was acted upon)
    entity_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Type of entity (e.g., 'lead', 'booking', 'user')",
    )
    entity_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="ID of the entity"
    )

    # User reference (who performed the action)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, index=True, comment="User who triggered the event"
    )

    # Event data (using JSONB for PostgreSQL optimization)
    event_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Additional JSON data about the event",
    )

    # Event severity
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="info",
        server_default="info",
        index=True,
        comment="Event severity: debug, info, warning, error, critical",
    )

    # Timestamps (timezone-aware)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="When the event occurred",
    )

    # Composite indexes for common queries
    __table_args__ = (
        # Get all events for a specific entity
        Index("ix_system_events_entity_lookup", "entity_type", "entity_id", "timestamp"),
        # Get all events for a specific user
        Index("ix_system_events_user_timeline", "user_id", "timestamp"),
        # Analytics: events by service and action
        Index("ix_system_events_service_action", "service", "action", "timestamp"),
        # Error tracking: get errors by severity
        Index("ix_system_events_severity_time", "severity", "timestamp"),
        # Audit trail: chronological events
        Index("ix_system_events_chronological", "timestamp", "service"),
    )

    def __repr__(self) -> str:
        return (
            f"<SystemEvent(id={self.id}, service='{self.service}', "
            f"action='{self.action}', entity_type='{self.entity_type}', "
            f"entity_id={self.entity_id}, timestamp={self.timestamp})>"
        )

    def to_dict(self) -> dict:
        """Convert event to dictionary for API responses."""
        return {
            "id": self.id,
            "service": self.service,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "user_id": self.user_id,
            "metadata": self.event_data,  # Keep 'metadata' key for API compatibility
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
