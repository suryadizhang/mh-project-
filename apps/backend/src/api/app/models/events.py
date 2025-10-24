"""
Database models for CQRS event sourcing and outbox patterns.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

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

# Use unified Base from models package
from api.app.models.declarative_base import Base


class DomainEvent(Base):
    """Domain events for event sourcing."""

    __tablename__ = "domain_events"
    __table_args__ = {"schema": "events"}

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
        id: Optional[str] = None,
        aggregate_id: str = None,
        aggregate_type: str = None,
        event_type: str = None,
        version: int = None,
        payload: dict[str, Any] = None,
        occurred_at: Optional[datetime] = None,
        hash_previous: str = None,
        hash_current: str = None,
        **kwargs
    ):
        self.id = id or uuid4()
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.event_type = event_type
        self.version = version
        self.payload = payload or {}
        self.occurred_at = occurred_at or datetime.utcnow()
        self.hash_previous = hash_previous
        self.hash_current = hash_current


class OutboxEntry(Base):
    """Outbox pattern for reliable event publishing."""

    __tablename__ = "outbox_entries"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(
        PostgresUUID(as_uuid=True),
        ForeignKey("events.domain_events.id"),
        nullable=False,
        index=True
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
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    next_attempt_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name="outbox_status_check"
        ),
        CheckConstraint("attempts >= 0", name="outbox_attempts_positive"),
        CheckConstraint("max_attempts > 0", name="outbox_max_attempts_positive"),
        {"schema": "events"},
    )

    def __init__(
        self,
        id: Optional[str] = None,
        event_id: str = None,
        target: str = None,
        payload: dict[str, Any] = None,
        status: str = "pending",
        attempts: int = 0,
        max_attempts: int = 3,
        next_attempt_at: Optional[datetime] = None,
        **kwargs
    ):
        self.id = id or uuid4()
        self.event_id = event_id
        self.target = target
        self.payload = payload or {}
        self.status = status
        self.attempts = attempts
        self.max_attempts = max_attempts
        self.next_attempt_at = next_attempt_at or datetime.utcnow()


class Snapshot(Base):
    """Aggregate snapshots for performance optimization."""

    __tablename__ = "snapshots"
    __table_args__ = {"schema": "events"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    aggregate_id = Column(PostgresUUID(as_uuid=True), nullable=False, unique=True)
    aggregate_type = Column(String(50), nullable=False)
    version = Column(Integer, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    def __init__(
        self,
        aggregate_id: str = None,
        aggregate_type: str = None,
        version: int = None,
        data: dict[str, Any] = None,
        **kwargs
    ):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = version
        self.data = data or {}


class ProjectionPosition(Base):
    """Track projection positions for event replay."""

    __tablename__ = "projection_positions"
    __table_args__ = {"schema": "events"}

    projection_name = Column(String(100), primary_key=True)
    last_event_id = Column(PostgresUUID(as_uuid=True), nullable=True)
    last_processed_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    def __init__(
        self,
        projection_name: str = None,
        last_event_id: Optional[str] = None,
        **kwargs
    ):
        self.projection_name = projection_name
        self.last_event_id = last_event_id


class IdempotencyKey(Base):
    """Idempotency tracking for commands."""

    __tablename__ = "idempotency_keys"

    key = Column(String(255), primary_key=True)
    command_type = Column(String(100), nullable=False)
    result = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="processing")  # processing, completed, failed
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'completed', 'failed')",
            name="idempotency_status_check"
        ),
        {"schema": "events"}
    )

    def __init__(
        self,
        key: str = None,
        command_type: str = None,
        expires_at: Optional[datetime] = None,
        **kwargs
    ):
        self.key = key
        self.command_type = command_type
        self.expires_at = expires_at or datetime.utcnow()


__all__ = [
    "DomainEvent",
    "OutboxEntry",
    "Snapshot",
    "ProjectionPosition",
    "IdempotencyKey"
]
