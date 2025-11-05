"""
Base classes for CQRS Command and Query patterns with event sourcing.
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
import hashlib
import json
from typing import Any
from uuid import UUID, uuid4

from api.app.models.events import DomainEvent, OutboxEntry
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class Command(BaseModel):
    """Base class for all commands."""

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)


class Query(BaseModel):
    """Base class for all queries."""

    model_config = ConfigDict(arbitrary_types_allowed=True, use_enum_values=True)


class Event(BaseModel):
    """Base class for domain events."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        json_schema_extra={
            "example": {
                "aggregate_id": "550e8400-e29b-41d4-a716-446655440000",
                "aggregate_type": "Booking",
                "event_type": "BookingCreated",
                "version": 1,
                "occurred_at": "2024-10-25T10:30:00Z",
            }
        },
    )

    aggregate_id: UUID
    aggregate_type: str
    event_type: str
    version: int = 1
    occurred_at: datetime = Field(description="When the event occurred")

    @classmethod
    def create(
        cls, aggregate_id: UUID, aggregate_type: str, event_type: str, version: int = 1
    ) -> "Event":
        """Factory method to create Event with automatic timestamp."""
        return cls(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            event_type=event_type,
            version=version,
            occurred_at=datetime.now(UTC),
        )


class CommandResult(BaseModel):
    """Result of command execution."""

    success: bool
    data: dict[str, Any] | None = None
    events: list[Event] = Field(default_factory=list)
    error: str | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class QueryResult(BaseModel):
    """Result of query execution."""

    success: bool
    data: dict[str, Any] | list[dict[str, Any]] | None = None
    error: str | None = None
    total_count: int | None = None

    model_config = ConfigDict(arbitrary_types_allowed=True)


class CommandHandler(ABC):
    """Base class for command handlers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def handle(self, command: Command) -> CommandResult:
        """Handle the command and return result."""


class QueryHandler(ABC):
    """Base class for query handlers."""

    def __init__(self, session: AsyncSession):
        self.session = session

    @abstractmethod
    async def handle(self, query: Query) -> QueryResult:
        """Handle the query and return result."""


class EventStore:
    """Event store for persisting and retrieving domain events."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self._last_hash: str | None = None

    async def append_events(
        self, events: list[Event], expected_version: int | None = None
    ) -> list[DomainEvent]:
        """
        Append events to the event store with hash chaining for audit trail.

        Args:
            events: List of events to append
            expected_version: Expected version for optimistic concurrency control

        Returns:
            List of persisted DomainEvent records
        """
        if not events:
            return []

        # Get the last hash for chaining
        if self._last_hash is None:
            last_event_stmt = (
                select(DomainEvent.hash_current).order_by(DomainEvent.created_at.desc()).limit(1)
            )
            result = await self.session.execute(last_event_stmt)
            self._last_hash = result.scalar() or "genesis"

        persisted_events = []

        for event in events:
            # Create event record
            event_dict = event.dict()

            # Calculate hash for audit chain
            event_content = json.dumps(
                {
                    "aggregate_id": str(event.aggregate_id),
                    "aggregate_type": event.aggregate_type,
                    "event_type": event.event_type,
                    "payload": event_dict,
                    "version": event.version,
                    "occurred_at": event.occurred_at.isoformat(),
                    "previous_hash": self._last_hash,
                },
                sort_keys=True,
            )

            current_hash = hashlib.sha256(event_content.encode()).hexdigest()

            domain_event = DomainEvent(
                id=uuid4(),
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                event_type=event.event_type,
                payload=event_dict,
                version=event.version,
                occurred_at=event.occurred_at,
                hash_previous=self._last_hash,
                hash_current=current_hash,
            )

            self.session.add(domain_event)
            persisted_events.append(domain_event)

            # Update hash for next event
            self._last_hash = current_hash

        await self.session.flush()
        return persisted_events

    async def get_events(
        self, aggregate_id: UUID, from_version: int = 0, to_version: int | None = None
    ) -> list[DomainEvent]:
        """Get events for an aggregate."""
        stmt = (
            select(DomainEvent)
            .where(DomainEvent.aggregate_id == aggregate_id)
            .where(DomainEvent.version > from_version)
        )

        if to_version is not None:
            stmt = stmt.where(DomainEvent.version <= to_version)

        stmt = stmt.order_by(DomainEvent.version.asc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_all_events(
        self,
        event_types: list[str] | None = None,
        from_timestamp: datetime | None = None,
        limit: int = 1000,
    ) -> list[DomainEvent]:
        """Get all events for projection rebuilding."""
        stmt = select(DomainEvent)

        if event_types:
            stmt = stmt.where(DomainEvent.event_type.in_(event_types))

        if from_timestamp:
            stmt = stmt.where(DomainEvent.occurred_at >= from_timestamp)

        stmt = stmt.order_by(DomainEvent.occurred_at.asc()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class OutboxProcessor:
    """Processor for reliable event publishing via outbox pattern."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_outbox_entries(
        self, events: list[DomainEvent], targets: list[str]
    ) -> list[OutboxEntry]:
        """Create outbox entries for reliable delivery."""
        outbox_entries = []

        for event in events:
            for target in targets:
                entry = OutboxEntry(
                    id=uuid4(),
                    event_id=event.id,
                    target=target,
                    payload=self._build_outbox_payload(event, target),
                    attempts=0,
                    max_attempts=3,
                    next_attempt_at=datetime.now(UTC),
                    status="pending",
                )

                self.session.add(entry)
                outbox_entries.append(entry)

        await self.session.flush()
        return outbox_entries

    def _build_outbox_payload(self, event: DomainEvent, target: str) -> dict[str, Any]:
        """Build payload for specific target."""
        base_payload = {
            "event_id": str(event.id),
            "event_type": event.event_type,
            "aggregate_id": str(event.aggregate_id),
            "aggregate_type": event.aggregate_type,
            "occurred_at": event.occurred_at.isoformat(),
            "payload": event.payload,
        }

        # Customize payload based on target
        if target == "ringcentral":
            return self._build_ringcentral_payload(base_payload, event)
        elif target == "stripe":
            return self._build_stripe_payload(base_payload, event)
        elif target == "email":
            return self._build_email_payload(base_payload, event)
        elif target == "projection":
            return base_payload
        else:
            return base_payload

    def _build_ringcentral_payload(self, base: dict, event: DomainEvent) -> dict[str, Any]:
        """Build RingCentral-specific payload."""
        if event.event_type == "MessageReceived":
            return {
                **base,
                "phone_number": event.payload.get("phone_number"),
                "message": event.payload.get("content"),
                "thread_id": event.payload.get("thread_id"),
            }
        elif event.event_type == "MessageSent":
            return {
                **base,
                "phone_number": event.payload.get("phone_number"),
                "message": event.payload.get("content"),
            }
        return base

    def _build_stripe_payload(self, base: dict, event: DomainEvent) -> dict[str, Any]:
        """Build Stripe-specific payload."""
        if event.event_type == "BookingCreated":
            return {
                **base,
                "customer_email": event.payload.get("customer_email"),
                "booking_id": str(event.aggregate_id),
                "amount_cents": event.payload.get("deposit_due_cents"),
                "description": f"Hibachi booking deposit for {event.payload.get('date')} at {event.payload.get('slot')}",
            }
        return base

    def _build_email_payload(self, base: dict, event: DomainEvent) -> dict[str, Any]:
        """Build email-specific payload."""
        if event.event_type == "BookingCreated":
            return {
                **base,
                "to_email": event.payload.get("customer_email"),
                "template": "booking_confirmation",
                "variables": {
                    "customer_name": event.payload.get("customer_name"),
                    "booking_date": event.payload.get("date"),
                    "booking_slot": event.payload.get("slot"),
                    "total_guests": event.payload.get("total_guests"),
                    "total_amount": event.payload.get("total_due_cents"),
                },
            }
        return base

    async def get_pending_entries(
        self, target: str | None = None, limit: int = 100
    ) -> list[OutboxEntry]:
        """Get pending outbox entries for processing."""
        stmt = (
            select(OutboxEntry)
            .where(OutboxEntry.status == "pending")
            .where(OutboxEntry.next_attempt_at <= datetime.now(UTC))
        )

        if target:
            stmt = stmt.where(OutboxEntry.target == target)

        stmt = stmt.order_by(OutboxEntry.created_at.asc()).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class AggregateRoot(ABC):
    """Base class for aggregate roots in DDD."""

    def __init__(self, aggregate_id: UUID):
        self.id = aggregate_id
        self.version = 0
        self._uncommitted_events: list[Event] = []

    def add_event(self, event: Event):
        """Add an event to the uncommitted events list."""
        event.aggregate_id = self.id
        event.version = self.version + len(self._uncommitted_events) + 1
        self._uncommitted_events.append(event)

    def get_uncommitted_events(self) -> list[Event]:
        """Get uncommitted events."""
        return self._uncommitted_events.copy()

    def mark_events_as_committed(self):
        """Mark all uncommitted events as committed."""
        self.version += len(self._uncommitted_events)
        self._uncommitted_events.clear()

    @classmethod
    @abstractmethod
    def from_events(cls, events: list[Event]) -> "AggregateRoot":
        """Reconstruct aggregate from events."""


class CommandBus:
    """Command bus for routing commands to handlers."""

    def __init__(self):
        self._handlers: dict[type[Command], type[CommandHandler]] = {}

    def register_handler(self, command_type: type[Command], handler_type: type[CommandHandler]):
        """Register a command handler."""
        self._handlers[command_type] = handler_type

    async def execute(self, command: Command, session: AsyncSession) -> CommandResult:
        """Execute a command."""
        command_type = type(command)

        if command_type not in self._handlers:
            return CommandResult(
                success=False, error=f"No handler registered for command: {command_type.__name__}"
            )

        handler_type = self._handlers[command_type]
        handler = handler_type(session)

        try:
            result = await handler.handle(command)
            return result
        except Exception as e:
            return CommandResult(success=False, error=str(e))


class QueryBus:
    """Query bus for routing queries to handlers."""

    def __init__(self):
        self._handlers: dict[type[Query], type[QueryHandler]] = {}

    def register_handler(self, query_type: type[Query], handler_type: type[QueryHandler]):
        """Register a query handler."""
        self._handlers[query_type] = handler_type

    async def execute(self, query: Query, session: AsyncSession) -> QueryResult:
        """Execute a query."""
        query_type = type(query)

        if query_type not in self._handlers:
            return QueryResult(
                success=False, error=f"No handler registered for query: {query_type.__name__}"
            )

        handler_type = self._handlers[query_type]
        handler = handler_type(session)

        try:
            result = await handler.handle(query)
            return result
        except Exception as e:
            return QueryResult(success=False, error=str(e))


# Global instances
command_bus = CommandBus()
query_bus = QueryBus()


def register_command_handler(command_type: type[Command]):
    """Decorator to register command handlers."""

    def decorator(handler_class: type[CommandHandler]):
        command_bus.register_handler(command_type, handler_class)
        return handler_class

    return decorator


def register_query_handler(query_type: type[Query]):
    """Decorator to register query handlers."""

    def decorator(handler_class: type[QueryHandler]):
        query_bus.register_handler(query_type, handler_class)
        return handler_class

    return decorator
