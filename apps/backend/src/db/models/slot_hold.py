"""
SQLAlchemy Model - Slot Holds
==============================

Temporary slot holds during agreement signing process.
2-hour timeout before slot is released if agreement not signed.

Table: core.slot_holds
Migration: database/migrations/008_legal_agreements_system.sql
           database/migrations/009_slot_holds_auto_cancel.sql

Workflow:
1. Customer requests booking → SlotHold created (status='pending')
2. 2 hours to sign agreement (1-hour warning)
3. After signing, 4 hours to pay deposit (1-hour warning)
4. After deposit → converted to Booking (status='converted')
5. Timeout → auto-cancel (status='expired' or 'cancelled')

Related:
- services/agreements/slot_hold_service.py
- workers/slot_hold_tasks.py
"""

import enum
from datetime import date, datetime, time
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base


class SlotHoldStatus(str, enum.Enum):
    """Status values for slot holds."""

    PENDING = "pending"  # Hold created, awaiting agreement
    SIGNED = "signed"  # Agreement signed, awaiting deposit
    CONVERTED = "converted"  # Deposit paid, converted to booking
    EXPIRED = "expired"  # Timed out (no action taken)
    CANCELLED = "cancelled"  # Manually cancelled


class SlotHold(Base):
    """
    Temporary slot holds during agreement signing.

    Holds a booking slot for 2 hours while customer signs the agreement,
    then 4 more hours to pay the deposit. Auto-expires if not completed.

    Schema: core.slot_holds
    """

    __tablename__ = "slot_holds"
    __table_args__ = (
        UniqueConstraint(
            "event_date",
            "slot_time",
            "station_id",
            "status",
            name="uq_slot_holds_slot_status",
        ),
        Index("idx_slot_holds_date_slot", "event_date", "slot_time", "station_id"),
        Index("idx_slot_holds_token", "signing_token"),
        Index(
            "idx_slot_holds_expires",
            "expires_at",
            postgresql_where="status = 'pending'",
        ),
        {"schema": "core"},
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )

    # Slot being held
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    slot_time: Mapped[time] = mapped_column(Time, nullable=False)
    station_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.stations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Customer details
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    guest_count: Mapped[int] = mapped_column(Integer, default=10)

    # Signing link
    signing_token: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), default=uuid4, unique=True
    )
    signing_link_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now() + func.cast("2 hours", Text),
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20), default=SlotHoldStatus.PENDING.value
    )
    converted_to_booking_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="SET NULL"),
        nullable=True,
    )

    # From migration 009: Agreement and deposit tracking
    agreement_signed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    signed_agreement_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.signed_agreements.id", ondelete="SET NULL"),
        nullable=True,
    )
    deposit_paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Warning tracking (for 1-hour warnings)
    signing_warning_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    payment_warning_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships (optional - add if needed)
    # station = relationship("Station", back_populates="slot_holds")
    # converted_booking = relationship("Booking", back_populates="slot_hold")
    # signed_agreement = relationship("SignedAgreement", back_populates="slot_hold")

    def __repr__(self) -> str:
        return (
            f"<SlotHold(id={self.id}, date={self.event_date}, "
            f"time={self.slot_time}, status={self.status})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if hold has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_pending(self) -> bool:
        """Check if hold is still pending."""
        return self.status == SlotHoldStatus.PENDING.value

    @property
    def is_signed(self) -> bool:
        """Check if agreement has been signed."""
        return self.agreement_signed_at is not None

    @property
    def is_paid(self) -> bool:
        """Check if deposit has been paid."""
        return self.deposit_paid_at is not None
