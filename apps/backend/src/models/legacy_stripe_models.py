import uuid

# Use unified Base from models package
from models.legacy_declarative_base import (
    Base,
)  # Phase 2C: Updated from api.app.models.declarative_base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class StripeCustomer(Base):
    """Legacy Stripe customer model from public schema (linking users to Stripe customers)."""

    __tablename__ = "customers"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, unique=True, index=True)
    email = Column(String, nullable=False, unique=True, index=True)
    stripe_customer_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String)
    phone = Column(String)
    preferred_payment_method = Column(String, default="zelle")

    # Analytics fields
    total_spent = Column(Numeric(10, 2), default=0)
    total_bookings = Column(Integer, default=0)
    zelle_savings = Column(Numeric(10, 2), default=0)
    loyalty_tier = Column(String, default="bronze")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    payments = relationship("StripePayment", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")


class StripePayment(Base):
    """Legacy Stripe payment records for public.stripe_payments table."""

    __tablename__ = "stripe_payments"  # Changed from "payments" to avoid conflict with core.Payment
    __table_args__ = {"schema": "public", "extend_existing": True}  # Use public schema for legacy Stripe model

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    booking_id = Column(String, index=True)
    stripe_payment_intent_id = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String, ForeignKey("customers.stripe_customer_id"))

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="usd")
    status = Column(String, nullable=False, index=True)
    method = Column(String, nullable=False)  # stripe, zelle, venmo

    # Metadata
    payment_type = Column(String)  # deposit, balance, full, addon
    description = Column(Text)
    metadata_json = Column(Text)

    # Fees and savings
    stripe_fee = Column(Numeric(10, 2), default=0)
    net_amount = Column(Numeric(10, 2))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("StripeCustomer", back_populates="payments")
    refunds = relationship("Refund", back_populates="payment")


class Invoice(Base):
    """Invoice records for balance collection."""

    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    booking_id = Column(String, index=True)
    stripe_invoice_id = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String, ForeignKey("customers.stripe_customer_id"))

    # Invoice details
    amount_due = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=0)
    currency = Column(String, default="usd")
    status = Column(String, nullable=False, index=True)

    # URLs
    hosted_invoice_url = Column(String)
    invoice_pdf_url = Column(String)

    # Dates
    due_date = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    customer = relationship("StripeCustomer", back_populates="invoices")


class Product(Base):
    """Stripe products mirror."""

    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stripe_product_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    active = Column(Boolean, default=True)

    # Metadata
    category = Column(String)  # menu, addon, fee, gratuity

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    prices = relationship("Price", back_populates="product")


class Price(Base):
    """Stripe prices mirror."""

    __tablename__ = "prices"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stripe_price_id = Column(String, unique=True, nullable=False, index=True)
    product_id = Column(String, ForeignKey("products.id"))
    stripe_product_id = Column(String, nullable=False)

    # Price details
    unit_amount = Column(Integer, nullable=False)  # cents
    currency = Column(String, default="usd")
    active = Column(Boolean, default=True)

    # Subscription details (nullable for one-time prices)
    recurring_interval = Column(String)  # month, year, etc.
    recurring_interval_count = Column(Integer)

    # Metadata
    nickname = Column(String)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="prices")


class WebhookEvent(Base):
    """Webhook event audit log."""

    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False, index=True)
    stripe_event_id = Column(String, unique=True, nullable=False, index=True)

    # Event data
    payload_json = Column(Text, nullable=False)
    processed = Column(Boolean, default=False)

    # Processing details
    processing_error = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True))


class Refund(Base):
    """Refund records."""

    __tablename__ = "refunds"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stripe_refund_id = Column(String, unique=True, nullable=False, index=True)
    payment_id = Column(String, ForeignKey("public.stripe_payments.id"))

    # Refund details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="usd")
    status = Column(String, nullable=False)
    reason = Column(String)

    # Admin details
    requested_by = Column(String)  # admin user id
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    payment = relationship("StripePayment", back_populates="refunds")


class Dispute(Base):
    """Dispute records."""

    __tablename__ = "disputes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    stripe_dispute_id = Column(String, unique=True, nullable=False, index=True)
    payment_id = Column(String, ForeignKey("public.stripe_payments.id"))

    # Dispute details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="usd")
    status = Column(String, nullable=False)
    reason = Column(String)

    # Dispute evidence
    evidence_details = Column(Text)
    evidence_due_by = Column(DateTime(timezone=True))

    # Resolution
    resolved_at = Column(DateTime(timezone=True))
    resolution = Column(String)  # won, lost, warning_closed, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Create indexes for better performance
Index("idx_payments_user_booking", StripePayment.user_id, StripePayment.booking_id)
Index("idx_payments_status_method", StripePayment.status, StripePayment.method)
Index("idx_invoices_user_booking", Invoice.user_id, Invoice.booking_id)
Index(
    "idx_webhook_events_type_processed",
    WebhookEvent.type,
    WebhookEvent.processed,
)
