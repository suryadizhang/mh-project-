"""
Database models for CQRS event sourcing and outbox patterns.

Domain Events: Event sourcing with hash chain for audit integrity
Outbox Entries: Transactional outbox pattern for reliable event publishing
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from models.base import BaseModel as Base
from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func


class DomainEvent(Base):
    """
    Domain events for event sourcing.
    
    Uses hash chaining for audit integrity and tamper detection.
    Stored in 'events' schema for separation from business data.
    """

    __tablename__ = "domain_events"
    __table_args__ = {"schema": "events", "extend_existing": True}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    aggregate_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    aggregate_type = Column(String(50), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    payload = Column(JSON, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Hash chain for audit integrity
    hash_previous = Column(String(64), nullable=False)
    hash_current = Column(String(64), nullable=False, unique=True)

    def __init__(
        self,
        id: str | None = None,
        aggregate_id: str | None = None,
        aggregate_type: str | None = None,
        event_type: str | None = None,
        version: int | None = None,
        payload: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
        hash_previous: str | None = None,
        hash_current: str | None = None,
        **kwargs,
    ):
        self.id = id or uuid4()
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.event_type = event_type
        self.version = version
        self.payload = payload or {}
        self.occurred_at = occurred_at or datetime.now(timezone.utc)
        self.hash_previous = hash_previous
        self.hash_current = hash_current


class OutboxEntry(Base):
    """
    Outbox pattern for reliable event publishing.
    
    Ensures events are reliably published to external systems
    (RingCentral, Stripe, Email, etc.) using transactional outbox pattern.
    """

    __tablename__ = "outbox_entries"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')", 
            name="outbox_status_check"
        ),
        CheckConstraint("attempts >= 0", name="outbox_attempts_positive"),
        CheckConstraint("max_attempts > 0", name="outbox_max_attempts_positive"),
        {"schema": "events", "extend_existing": True},
    )

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("events.domain_events.id"),
        nullable=False,
        index=True,
    )
    target = Column(String(50), nullable=False, index=True)  # ringcentral, stripe, email, etc.
    payload = Column(JSON, nullable=False)
    status = Column(
        String(20), 
        nullable=False, 
        default="pending", 
        index=True
    )  # pending, processing, completed, failed
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(), 
        onupdate=func.now()
    )
    next_attempt_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def __init__(
        self,
        id: str | None = None,
        event_id: str | None = None,
        target: str | None = None,
        payload: dict[str, Any] | None = None,
        status: str = "pending",
        attempts: int = 0,
        max_attempts: int = 3,
        next_attempt_at: datetime | None = None,
        **kwargs,
    ):
        self.id = id or uuid4()
        self.event_id = event_id
        self.target = target
        self.payload = payload or {}
        self.status = status
        self.attempts = attempts
        self.max_attempts = max_attempts
        self.next_attempt_at = next_attempt_at or datetime.now(timezone.utc)
