"""
SQLAlchemy Models - Stripe/Payment Schema
==========================================

Payment-related entities for Stripe integration:
- StripeCustomer: Stripe customer mapping
- StripePayment: Payment transactions
- Invoice: Invoice records
- Refund: Refund records
- WebhookEvent: Stripe webhook event log

All models use:
- UUID primary keys
- Timezone-aware datetime fields
- Proper foreign key relationships
- Type hints for IDE support
"""

import enum
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

# Import enums from shared module (SSoT)
from db.models.enums import (
    InvoiceStatus,
    PaymentStatus,
    RefundStatus,
    WebhookEventStatus,
)

# ==================== MODELS ====================


class StripeCustomer(Base):
    """
    Maps internal customers to Stripe customer IDs.
    Enables payment method storage and subscription management.
    """

    __tablename__ = "stripe_customers"
    __table_args__ = (
        Index("ix_stripe_customers_customer_id", "customer_id"),
        Index("ix_stripe_customers_stripe_id", "stripe_customer_id"),
        {"schema": "core"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.customers.id", ondelete="CASCADE"),
        nullable=False,
    )
    stripe_customer_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    default_payment_method: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    customer = relationship("Customer", back_populates="stripe_customer")
    payments = relationship("StripePayment", back_populates="stripe_customer")
    invoices = relationship("Invoice", back_populates="stripe_customer")

    def __repr__(self) -> str:
        return f"<StripeCustomer {self.stripe_customer_id}>"


class StripePayment(Base):
    """
    Records individual payment transactions.
    Tracks payment intents and their statuses.
    """

    __tablename__ = "stripe_payments"
    __table_args__ = (
        Index("ix_stripe_payments_customer", "stripe_customer_id"),
        Index("ix_stripe_payments_booking", "booking_id"),
        Index("ix_stripe_payments_intent", "payment_intent_id"),
        Index("ix_stripe_payments_status", "status"),
        {"schema": "core"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    stripe_customer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.stripe_customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    booking_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_intent_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus, name="payment_status", create_type=True),
        default=PaymentStatus.PENDING,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Stripe-specific fields
    charge_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    failure_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    failure_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    stripe_customer = relationship("StripeCustomer", back_populates="payments")
    booking = relationship("Booking", back_populates="stripe_payments")
    refunds = relationship("Refund", back_populates="payment")

    def __repr__(self) -> str:
        return f"<StripePayment {self.payment_intent_id} {self.status.value}>"


class Invoice(Base):
    """
    Invoice records for bookings.
    Synced with Stripe invoices.
    """

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_customer", "stripe_customer_id"),
        Index("ix_invoices_booking", "booking_id"),
        Index("ix_invoices_stripe", "stripe_invoice_id"),
        Index("ix_invoices_status", "status"),
        {"schema": "core"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    stripe_customer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.stripe_customers.id", ondelete="SET NULL"),
        nullable=True,
    )
    booking_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="SET NULL"),
        nullable=True,
    )
    stripe_invoice_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(
        SQLEnum(InvoiceStatus, name="invoice_status", create_type=True),
        default=InvoiceStatus.DRAFT,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    line_items: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hosted_invoice_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    # Relationships
    stripe_customer = relationship("StripeCustomer", back_populates="invoices")
    booking = relationship("Booking", back_populates="invoices")

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} {self.status.value}>"


class Refund(Base):
    """
    Refund records for payments.
    Synced with Stripe refunds.
    """

    __tablename__ = "refunds"
    __table_args__ = (
        Index("ix_refunds_payment", "payment_id"),
        Index("ix_refunds_stripe", "stripe_refund_id"),
        Index("ix_refunds_status", "status"),
        {"schema": "core"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    payment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.stripe_payments.id", ondelete="CASCADE"),
        nullable=False,
    )
    stripe_refund_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="usd", nullable=False)
    status: Mapped[RefundStatus] = mapped_column(
        SQLEnum(RefundStatus, name="refund_status", create_type=True),
        default=RefundStatus.PENDING,
        nullable=False,
    )
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stripe_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    refunded_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    payment = relationship("StripePayment", back_populates="refunds")

    def __repr__(self) -> str:
        return f"<Refund {self.stripe_refund_id} {self.status.value}>"


class WebhookEvent(Base):
    """
    Log of Stripe webhook events for auditing and replay.
    """

    __tablename__ = "webhook_events"
    __table_args__ = (
        Index("ix_webhook_events_stripe_id", "stripe_event_id"),
        Index("ix_webhook_events_type", "event_type"),
        Index("ix_webhook_events_status", "status"),
        Index("ix_webhook_events_created", "created_at"),
        {"schema": "core"},
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    stripe_event_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[WebhookEventStatus] = mapped_column(
        SQLEnum(WebhookEventStatus, name="webhook_event_status", create_type=True),
        default=WebhookEventStatus.RECEIVED,
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<WebhookEvent {self.stripe_event_id} {self.event_type}>"
