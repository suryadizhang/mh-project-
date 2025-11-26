"""
SQLAlchemy Models - Events Schema
==================================

Event Sourcing Pattern:
- Domain Events (event log)
- Inbox (inbound events from external systems)
- Outbox (outbound events to external systems)

All models use:
- UUID primary keys
- Timezone-aware datetime fields
- Schema qualification (__table_args__)
- JSONB for event payloads
- Type hints for IDE support
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..base_class import Base


# ==================== ENUMS ====================

import enum

class OutboxStatus(str, enum.Enum):
    """Outbox message status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"


# ==================== MODELS ====================

class DomainEvent(Base):
    """
    Domain event entity

    Immutable event log for event sourcing pattern.
    Records all significant domain events for audit and replay.
    """
    __tablename__ = "domain_events"
    __table_args__ = (
        Index("idx_domain_events_aggregate_id", "aggregate_id"),
        Index("idx_domain_events_event_type", "event_type"),
        Index("idx_domain_events_occurred_at", "occurred_at"),
        Index("idx_domain_events_aggregate_type_id", "aggregate_type", "aggregate_id"),
        {"schema": "events"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Event Identity
    event_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")

    # Aggregate Reference
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Booking", "Customer"
    aggregate_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    aggregate_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Event Data
    event_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Metadata (use event_metadata to avoid conflict with SQLAlchemy's metadata attribute)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    # Causation & Correlation (for event chains)
    causation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Event that caused this
    correlation_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Request/session ID

    # Actor (who triggered the event)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamp (immutable)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )


class Inbox(Base):
    """
    Inbox entity

    Inbound events from external systems (webhooks, integrations).
    Ensures exactly-once processing with idempotency.
    """
    __tablename__ = "inbox"
    __table_args__ = (
        Index("idx_inbox_message_id", "message_id"),
        Index("idx_inbox_source", "source"),
        Index("idx_inbox_processed", "is_processed"),
        Index("idx_inbox_received_at", "received_at"),
        {"schema": "events"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Message Identity (for idempotency)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    # Source
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., "stripe", "ringcentral"
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "webhook", "api"

    # Message Details
    message_type: Mapped[str] = mapped_column(String(255), nullable=False)
    message_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Processing Status
    is_processed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Metadata (use message_metadata to avoid conflict with SQLAlchemy's metadata attribute)
    headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    message_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)

    # Timestamps
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )


class Outbox(Base):
    """
    Outbox entity

    Outbound events to external systems (webhooks, notifications).
    Ensures reliable delivery with retry logic.
    """
    __tablename__ = "outbox"
    __table_args__ = (
        Index("idx_outbox_aggregate_id", "aggregate_id"),
        Index("idx_outbox_status", "status"),
        Index("idx_outbox_destination", "destination"),
        Index("idx_outbox_scheduled_at", "scheduled_at"),
        Index("idx_outbox_created_at", "created_at"),
        {"schema": "events"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Event Reference
    event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Reference to domain_events.id
    aggregate_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)

    # Destination
    destination: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., "webhook", "email", "sms"
    destination_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Payload
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    headers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Status
    status: Mapped[OutboxStatus] = mapped_column(
        SQLEnum(OutboxStatus, name="outbox_status", schema="public", create_type=False),
        nullable=False,
        server_default="pending",
        index=True
    )

    # Retry Logic
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Scheduling
    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    # Processing
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Response
    response_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )
