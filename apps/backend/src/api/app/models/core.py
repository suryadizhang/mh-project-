"""
Core database models for CRM system.
"""
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Use unified Base from models package
from api.app.models.declarative_base import Base


class Customer(Base):
    """Customer records with encrypted PII and station scoping."""

    __tablename__ = "customers"
    __table_args__ = {"schema": "core"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Station association for multi-tenant isolation
    station_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True)

    # Encrypted fields
    email_encrypted = Column(String(500), nullable=False)
    name_encrypted = Column(String(500), nullable=False)
    phone_encrypted = Column(String(500), nullable=False)

    # Metadata
    source = Column(String(50), nullable=False, default="website")
    first_booking_at = Column(DateTime(timezone=True), nullable=True)
    last_booking_at = Column(DateTime(timezone=True), nullable=True)
    total_bookings = Column(Integer, nullable=False, default=0)
    total_spent_cents = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    station = relationship("Station", foreign_keys=[station_id])  # Now works with unified Base!
    bookings = relationship("Booking", back_populates="customer")
    message_threads = relationship("MessageThread", back_populates="customer")
    # leads = relationship("Lead", back_populates="customer")  # Disabled - Lead.customer is commented out
    # social_threads = relationship("SocialThread", back_populates="customer")  # Disabled - no FK in SocialThread
    # newsletter_subscriptions = relationship("Subscriber", back_populates="customer")  # Disabled - check FK
    
    __table_args__ = (
        # Unique email within station (allow same email across different stations)
        Index("idx_customer_station_email", "station_id", "email_encrypted", unique=True),
        Index("idx_customer_station_created", "station_id", "created_at"),
        {"schema": "core"}
    )


class Booking(Base):
    """Booking records with station scoping."""

    __tablename__ = "bookings"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Station association for multi-tenant isolation
    station_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True)
    customer_id = Column(PostgresUUID(as_uuid=True), ForeignKey("core.customers.id"), nullable=False, index=True)

    # Booking details
    date = Column(DateTime(timezone=True), nullable=False)
    slot = Column(String(20), nullable=False)  # "11:00 AM", etc.
    total_guests = Column(Integer, nullable=False)

    # Pricing
    price_per_person_cents = Column(Integer, nullable=False)
    total_due_cents = Column(Integer, nullable=False)
    deposit_due_cents = Column(Integer, nullable=False, default=0)
    balance_due_cents = Column(Integer, nullable=False, default=0)

    # Status tracking
    status = Column(String(20), nullable=False, default="confirmed")  # confirmed, cancelled, completed
    payment_status = Column(String(20), nullable=False, default="pending")  # pending, deposit_paid, paid

    # Optional encrypted fields
    special_requests_encrypted = Column(String(1000), nullable=True)

    # Source tracking
    source = Column(String(50), nullable=False, default="website")
    ai_conversation_id = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    station = relationship("Station", foreign_keys=[station_id])  # Now works with unified Base!
    customer = relationship("Customer", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking")

    __table_args__ = (
        CheckConstraint("total_guests > 0", name="ck_bookings_check_party_adults_positive"),
        CheckConstraint("total_guests >= 0", name="ck_bookings_check_party_kids_non_negative"),
        CheckConstraint("deposit_due_cents >= 0", name="ck_bookings_check_deposit_non_negative"),
        CheckConstraint("total_due_cents >= deposit_due_cents", name="ck_bookings_check_total_gte_deposit"),
        Index("idx_booking_station_date", "station_id", "date", "slot"),
        Index("idx_booking_station_customer", "station_id", "customer_id"),
        {"schema": "core"},
    )


class Payment(Base):
    """Payment records."""

    __tablename__ = "payments"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    booking_id = Column(PostgresUUID(as_uuid=True), ForeignKey("core.bookings.id"), nullable=False, index=True)

    # Payment details
    amount_cents = Column(Integer, nullable=False)
    payment_method = Column(String(50), nullable=False)  # stripe, cash, check, etc.
    payment_reference = Column(String(100), nullable=True)  # Stripe payment ID, check number
    status = Column(String(20), nullable=False, default="completed")  # completed, pending, failed, refunded

    # Optional fields
    notes = Column(Text, nullable=True)

    # Processing info
    processed_by = Column(String(100), nullable=False)  # user_id or "system"
    processed_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    booking = relationship("Booking", back_populates="payments")

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="payment_amount_positive"),
        CheckConstraint(
            "status IN ('completed', 'pending', 'failed', 'refunded')",
            name="payment_status_valid"
        ),
        {"schema": "core"},
    )


class MessageThread(Base):
    """Message thread records with station scoping."""

    __tablename__ = "message_threads"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Station association for multi-tenant isolation
    station_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True)
    customer_id = Column(PostgresUUID(as_uuid=True), ForeignKey("core.customers.id"), nullable=True, index=True)

    # Contact info (encrypted)
    phone_number_encrypted = Column(String(500), nullable=False, index=True)

    # Thread metadata
    status = Column(String(20), nullable=False, default="active")  # active, closed, archived
    has_unread = Column(Boolean, nullable=False, default=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    # Context
    booking_id = Column(PostgresUUID(as_uuid=True), ForeignKey("core.bookings.id"), nullable=True)
    subject = Column(String(200), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    station = relationship("Station", foreign_keys=[station_id])  # Now works with unified Base!
    customer = relationship("Customer", back_populates="message_threads")
    messages = relationship("Message", back_populates="thread")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'closed', 'archived')",
            name="thread_status_valid"
        ),
        Index("idx_thread_station_phone", "station_id", "phone_number_encrypted"),
        Index("idx_thread_station_customer", "station_id", "customer_id"),
        {"schema": "core"},
    )


class Message(Base):
    """Individual message records."""

    __tablename__ = "messages"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    thread_id = Column(PostgresUUID(as_uuid=True), ForeignKey("core.message_threads.id"), nullable=False, index=True)

    # Message content (encrypted)
    content_encrypted = Column(String(2000), nullable=False)

    # Message metadata
    direction = Column(String(10), nullable=False)  # inbound, outbound
    status = Column(String(20), nullable=False, default="delivered")  # delivered, failed, pending

    # External references
    external_message_id = Column(String(100), nullable=True)
    source = Column(String(50), nullable=False, default="manual")  # ringcentral, manual, etc.

    # Timing
    sent_at = Column(DateTime(timezone=True), nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    # Who sent (for outbound messages)
    sent_by = Column(String(100), nullable=True)  # user_id or "system"

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Relationships
    thread = relationship("MessageThread", back_populates="messages")

    __table_args__ = (
        CheckConstraint(
            "direction IN ('inbound', 'outbound')",
            name="message_direction_valid"
        ),
        CheckConstraint(
            "status IN ('delivered', 'failed', 'pending')",
            name="message_status_valid"
        ),
        Index("idx_message_thread_sent", "thread_id", "sent_at"),
        {"schema": "core"},
    )


class Event(Base):
    """Event logging for system activities."""

    __tablename__ = "events"
    __table_args__ = {"schema": "core"}

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Event identification
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    
    # Event data
    data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_event_type_created", "event_type", "created_at"),
        Index("idx_entity_type_id", "entity_type", "entity_id"),
        {"schema": "core"}
    )


__all__ = [
    "Customer",
    "Booking",
    "Payment",
    "MessageThread",
    "Message",
    "Event"
]
