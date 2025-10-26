"""
CRM-specific commands, queries, and events for booking operations.
"""
from datetime import date as Date
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator, ConfigDict

from api.app.cqrs.base import Command, Event, Query

# ==================== COMMANDS ====================

class CreateBookingCommand(Command):
    """Create a new hibachi booking."""

    customer_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    customer_name: str = Field(..., min_length=2, max_length=100)
    customer_phone: str = Field(..., pattern=r'^\+?[\d\s\-\(\)]+$')

    # Booking details
    date: Date
    slot: str  # "11:00 AM", "1:00 PM", etc.
    total_guests: int = Field(..., ge=1, le=50)
    special_requests: Optional[str] = Field(None, max_length=500)

    # Pricing
    price_per_person_cents: int = Field(..., ge=0)
    total_due_cents: int = Field(..., ge=0)
    deposit_due_cents: int = Field(..., ge=0)

    # Source tracking
    source: str = Field(default="website")  # ai, website, phone, etc.
    ai_conversation_id: Optional[str] = None

    # Idempotency
    idempotency_key: Optional[str] = None

    @field_validator('total_due_cents')
    @classmethod
    def validate_total_matches_calculation(cls, v, info):
        """Validate total matches price per person * guests."""
        values = info.data
        if 'price_per_person_cents' in values and 'total_guests' in values:
            expected = values['price_per_person_cents'] * values['total_guests']
            if v != expected:
                raise ValueError(f'Total due ({v}) must equal price per person ({values["price_per_person_cents"]}) × guests ({values["total_guests"]}) = {expected}')
        return v

    @field_validator('deposit_due_cents')
    @classmethod
    def validate_deposit_reasonable(cls, v, info):
        """Validate deposit is reasonable percentage of total."""
        values = info.data
        if 'total_due_cents' in values:
            if v < 0 or v > values['total_due_cents']:
                raise ValueError(f'Deposit ({v}) must be between 0 and total due ({values["total_due_cents"]})')
        return v


class UpdateBookingCommand(Command):
    """Update an existing booking."""

    booking_id: UUID

    # Fields that can be updated
    customer_name: Optional[str] = Field(None, min_length=2, max_length=100)
    customer_phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')
    date: Optional[Date] = None
    slot: Optional[str] = None
    total_guests: Optional[int] = Field(None, ge=1, le=50)
    special_requests: Optional[str] = Field(None, max_length=500)

    # Updated by
    updated_by: str  # user_id or "system"
    update_reason: str = Field(..., max_length=200)

    # Idempotency
    idempotency_key: Optional[str] = None


class CancelBookingCommand(Command):
    """Cancel a booking."""

    booking_id: UUID
    cancellation_reason: str = Field(..., max_length=200)
    cancelled_by: str  # user_id or "customer"
    refund_amount_cents: int = Field(0, ge=0)

    # Idempotency
    idempotency_key: Optional[str] = None


class RecordPaymentCommand(Command):
    """Record a payment for a booking."""

    booking_id: UUID
    amount_cents: int = Field(..., gt=0)
    payment_method: str  # stripe, cash, check, etc.
    payment_reference: Optional[str] = None  # Stripe payment ID, check number, etc.
    notes: Optional[str] = Field(None, max_length=200)

    # Who processed
    processed_by: str  # user_id or "system"

    # Idempotency
    idempotency_key: Optional[str] = None


class CreateMessageThreadCommand(Command):
    """Create a new message thread with a customer."""

    customer_id: Optional[UUID] = None  # If known customer
    phone_number: str = Field(..., pattern=r'^\+?[\d\s\-\(\)]+$')
    initial_message: str = Field(..., min_length=1, max_length=1000)
    source: str = Field(default="ringcentral")  # ringcentral, manual, etc.

    # If part of booking conversation
    booking_id: Optional[UUID] = None

    # Idempotency
    idempotency_key: Optional[str] = None


class SendMessageCommand(Command):
    """Send a message in an existing thread."""

    thread_id: UUID
    content: str = Field(..., min_length=1, max_length=1000)
    sent_by: str  # user_id or "system"

    # Optional integration details
    external_message_id: Optional[str] = None

    # Idempotency
    idempotency_key: Optional[str] = None


class ReceiveMessageCommand(Command):
    """Record a message received from a customer."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "phone_number": "+19167408768",
            "content": "I'd like to book a hibachi chef",
            "received_at": "2024-10-25T10:30:00Z",
            "external_message_id": "msg_12345",
            "source": "ringcentral"
        }
    })

    thread_id: Optional[UUID] = None  # If known thread
    phone_number: str = Field(..., pattern=r'^\+?[\d\s\-\(\)]+$')
    content: str = Field(..., min_length=1, max_length=1000)
    received_at: datetime = Field(description="When the message was received")

    # Integration details
    external_message_id: str  # RingCentral message ID
    source: str = Field(default="ringcentral")

    # Idempotency
    idempotency_key: Optional[str] = None

    @classmethod
    def create(
        cls,
        phone_number: str,
        content: str,
        external_message_id: str,
        thread_id: Optional[UUID] = None,
        source: str = "ringcentral",
        idempotency_key: Optional[str] = None
    ) -> "ReceiveMessageCommand":
        """Factory method to create ReceiveMessageCommand with automatic timestamp."""
        return cls(
            thread_id=thread_id,
            phone_number=phone_number,
            content=content,
            received_at=datetime.now(timezone.utc),
            external_message_id=external_message_id,
            source=source,
            idempotency_key=idempotency_key
        )


# ==================== QUERIES ====================

class GetBookingQuery(Query):
    """Get a specific booking by ID."""

    booking_id: UUID
    include_payments: bool = True
    include_messages: bool = True


class GetBookingsQuery(Query):
    """Get bookings with filtering and pagination."""

    # Filters
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    date_from: Optional[Date] = None
    date_to: Optional[Date] = None
    status: Optional[str] = None  # confirmed, cancelled, etc.
    source: Optional[str] = None

    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    # Sorting
    sort_by: str = Field("date", pattern=r'^(date|created_at|updated_at|customer_name)$')
    sort_order: str = Field("asc", pattern=r'^(asc|desc)$')


class GetCustomer360Query(Query):
    """Get comprehensive customer view."""

    customer_id: Optional[UUID] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

    # What to include
    include_bookings: bool = True
    include_payments: bool = True
    include_messages: bool = True

    @field_validator('customer_id')
    @classmethod
    def validate_one_identifier(cls, v, info):
        """Ensure exactly one identifier is provided."""
        values = info.data
        identifiers = [v, values.get('customer_email'), values.get('customer_phone')]
        provided = [x for x in identifiers if x is not None]
        if len(provided) != 1:
            raise ValueError('Exactly one of customer_id, customer_email, or customer_phone must be provided')
        return v


class GetMessageThreadQuery(Query):
    """Get message thread with history."""

    thread_id: UUID
    include_customer_details: bool = True
    include_booking_context: bool = True
    limit: int = Field(50, ge=1, le=200)


class GetMessageThreadsQuery(Query):
    """Get message threads with filtering."""

    # Filters
    customer_id: Optional[UUID] = None
    phone_number: Optional[str] = None
    has_unread: Optional[bool] = None

    # Date range
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class GetAvailabilitySlotsQuery(Query):
    """Get available time slots for a date."""

    date: Date
    party_size: int = Field(..., ge=1, le=50)
    duration_minutes: int = Field(180, ge=60, le=480)  # Default 3 hours


class GetDashboardStatsQuery(Query):
    """Get dashboard statistics."""

    date_from: Optional[Date] = None
    date_to: Optional[Date] = None

    # What stats to include
    include_bookings: bool = True
    include_revenue: bool = True
    include_messages: bool = True


# ==================== EVENTS ====================

class BookingCreated(Event):
    """Booking was created."""

    customer_email: str
    customer_name: str
    customer_phone: str
    date: Date
    slot: str
    total_guests: int
    total_due_cents: int
    deposit_due_cents: int
    source: str
    special_requests: Optional[str] = None
    ai_conversation_id: Optional[str] = None

    aggregate_type: Literal["Booking"] = "Booking"
    event_type: Literal["BookingCreated"] = "BookingCreated"


class BookingUpdated(Event):
    """Booking was updated."""

    changes: dict[str, Any]
    updated_by: str
    update_reason: str

    aggregate_type: Literal["Booking"] = "Booking"
    event_type: Literal["BookingUpdated"] = "BookingUpdated"


class BookingCancelled(Event):
    """Booking was cancelled."""

    cancellation_reason: str
    cancelled_by: str
    refund_amount_cents: int

    aggregate_type: Literal["Booking"] = "Booking"
    event_type: Literal["BookingCancelled"] = "BookingCancelled"


class PaymentRecorded(Event):
    """Payment was recorded for a booking."""

    booking_id: UUID
    amount_cents: int
    payment_method: str
    payment_reference: Optional[str] = None
    processed_by: str
    notes: Optional[str] = None

    aggregate_type: Literal["Payment"] = "Payment"
    event_type: Literal["PaymentRecorded"] = "PaymentRecorded"


class MessageThreadCreated(Event):
    """Message thread was created."""

    customer_id: Optional[UUID] = None
    phone_number: str
    initial_message: str
    source: str
    booking_id: Optional[UUID] = None

    aggregate_type: Literal["MessageThread"] = "MessageThread"
    event_type: Literal["MessageThreadCreated"] = "MessageThreadCreated"


class MessageSent(Event):
    """Message was sent to customer."""

    thread_id: UUID
    content: str
    sent_by: str
    external_message_id: Optional[str] = None

    aggregate_type: Literal["MessageThread"] = "MessageThread"
    event_type: Literal["MessageSent"] = "MessageSent"


class MessageReceived(Event):
    """Message was received from customer."""

    thread_id: UUID
    phone_number: str
    content: str
    received_at: datetime
    external_message_id: str
    source: str

    aggregate_type: Literal["MessageThread"] = "MessageThread"
    event_type: Literal["MessageReceived"] = "MessageReceived"


class CustomerCreated(Event):
    """Customer record was created."""

    email: str
    name: str
    phone: str
    source: str

    aggregate_type: Literal["Customer"] = "Customer"
    event_type: Literal["CustomerCreated"] = "CustomerCreated"


class CustomerUpdated(Event):
    """Customer information was updated."""

    changes: dict[str, Any]
    updated_by: str

    aggregate_type: Literal["Customer"] = "Customer"
    event_type: Literal["CustomerUpdated"] = "CustomerUpdated"


__all__ = [
    # Commands
    "CreateBookingCommand",
    "UpdateBookingCommand",
    "CancelBookingCommand",
    "RecordPaymentCommand",
    "CreateMessageThreadCommand",
    "SendMessageCommand",
    "ReceiveMessageCommand",

    # Queries
    "GetBookingQuery",
    "GetBookingsQuery",
    "GetCustomer360Query",
    "GetMessageThreadQuery",
    "GetMessageThreadsQuery",
    "GetAvailabilitySlotsQuery",
    "GetDashboardStatsQuery",

    # Events
    "BookingCreated",
    "BookingUpdated",
    "BookingCancelled",
    "PaymentRecorded",
    "MessageThreadCreated",
    "MessageSent",
    "MessageReceived",
    "CustomerCreated",
    "CustomerUpdated"
]
