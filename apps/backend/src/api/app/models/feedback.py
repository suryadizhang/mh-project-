"""
Feedback models for customer reviews and discount coupons.
"""
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Optional
import secrets
import string

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.app.models.declarative_base import Base


class CustomerReview(Base):
    """Customer review records with station scoping."""

    __tablename__ = "customer_reviews"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Station and customer associations
    station_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True)
    booking_id = Column(PostgresUUID(as_uuid=True), ForeignKey("core.bookings.id"), nullable=False, index=True)
    customer_id = Column(PostgresUUID(as_uuid=True), ForeignKey("core.customers.id"), nullable=False, index=True)
    
    # Review data
    rating = Column(
        Enum('great', 'good', 'okay', 'could_be_better', name='review_rating', schema='feedback'),
        nullable=False
    )
    status = Column(
        Enum('pending', 'submitted', 'escalated', 'resolved', 'archived', name='review_status', schema='feedback'),
        nullable=False,
        default='pending'
    )
    
    # For negative reviews
    complaint_text = Column(Text, nullable=True)
    improvement_suggestions = Column(Text, nullable=True)
    
    # External review tracking
    left_yelp_review = Column(Boolean, nullable=False, default=False)
    left_google_review = Column(Boolean, nullable=False, default=False)
    external_review_date = Column(DateTime(timezone=True), nullable=True)
    
    # SMS tracking
    sms_sent_at = Column(DateTime(timezone=True), nullable=True)
    sms_message_id = Column(String(100), nullable=True)
    review_link = Column(String(500), nullable=True)
    
    # Follow-up tracking
    admin_notified_at = Column(DateTime(timezone=True), nullable=True)
    ai_escalated_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Coupon issued
    coupon_issued = Column(Boolean, nullable=False, default=False)
    coupon_id = Column(PostgresUUID(as_uuid=True), ForeignKey("feedback.discount_coupons.id"), nullable=True)
    
    # Metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    extra_metadata = Column('metadata', JSONB, nullable=True)  # Renamed to avoid SQLAlchemy conflict
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    station = relationship("Station", foreign_keys=[station_id])
    booking = relationship("Booking", foreign_keys=[booking_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    coupon = relationship("DiscountCoupon", foreign_keys=[coupon_id], post_update=True)
    escalations = relationship("ReviewEscalation", back_populates="review", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "(rating IN ('great', 'good') AND complaint_text IS NULL) OR "
            "(rating IN ('okay', 'could_be_better') AND complaint_text IS NOT NULL)",
            name='check_complaint_required_for_negative'
        ),
        Index("ix_feedback_reviews_station_customer", "station_id", "customer_id"),
        Index("ix_feedback_reviews_booking", "booking_id"),
        Index("ix_feedback_reviews_rating", "rating"),
        Index("ix_feedback_reviews_status", "status"),
        Index("ix_feedback_reviews_created", "created_at"),
        {"schema": "feedback"}
    )

    @property
    def is_positive(self) -> bool:
        """Check if review is positive."""
        return self.rating in ('great', 'good')

    @property
    def is_negative(self) -> bool:
        """Check if review is negative."""
        return self.rating in ('okay', 'could_be_better')

    @property
    def needs_escalation(self) -> bool:
        """Check if review needs escalation."""
        return self.is_negative and self.status == 'submitted'


class DiscountCoupon(Base):
    """Discount coupon records with station scoping."""

    __tablename__ = "discount_coupons"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Station and customer associations
    station_id = Column(PostgresUUID(as_uuid=True), ForeignKey("identity.stations.id"), nullable=False, index=True)
    customer_id = Column(PostgresUUID(as_uuid=True), ForeignKey("core.customers.id"), nullable=False, index=True)
    review_id = Column(PostgresUUID(as_uuid=True), ForeignKey("feedback.customer_reviews.id"), nullable=True)
    
    # Coupon details
    coupon_code = Column(String(50), nullable=False, unique=True)
    discount_type = Column(String(20), nullable=False)  # 'percentage', 'fixed_amount'
    discount_value = Column(Integer, nullable=False)  # e.g., 10 for 10%, or 1000 for $10.00
    description = Column(Text, nullable=True)
    
    # Usage constraints
    minimum_order_cents = Column(Integer, nullable=False, default=0)
    max_uses = Column(Integer, nullable=False, default=1)
    times_used = Column(Integer, nullable=False, default=0)
    
    # Status and validity
    status = Column(
        Enum('active', 'used', 'expired', 'cancelled', name='coupon_status', schema='feedback'),
        nullable=False,
        default='active'
    )
    valid_from = Column(DateTime(timezone=True), nullable=False, default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=False)
    
    # Usage tracking
    used_at = Column(DateTime(timezone=True), nullable=True)
    used_in_booking_id = Column(PostgresUUID(as_uuid=True), ForeignKey("core.bookings.id"), nullable=True)
    
    # Issue reason
    issue_reason = Column(String(100), nullable=False)  # 'negative_review', 'complaint_resolution', 'promotion'
    issued_by = Column(PostgresUUID(as_uuid=True), nullable=True)  # admin user or NULL for auto-issued
    
    # Metadata
    extra_metadata = Column('metadata', JSONB, nullable=True)  # Renamed to avoid SQLAlchemy conflict
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    station = relationship("Station", foreign_keys=[station_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    review = relationship("CustomerReview", foreign_keys=[review_id], post_update=True)
    used_in_booking = relationship("Booking", foreign_keys=[used_in_booking_id])

    __table_args__ = (
        CheckConstraint('discount_value > 0', name='check_discount_positive'),
        CheckConstraint('minimum_order_cents >= 0', name='check_min_order_non_negative'),
        CheckConstraint('max_uses > 0', name='check_max_uses_positive'),
        CheckConstraint('times_used >= 0', name='check_times_used_non_negative'),
        CheckConstraint('times_used <= max_uses', name='check_times_used_within_limit'),
        CheckConstraint('valid_until > valid_from', name='check_valid_date_range'),
        CheckConstraint(
            "discount_type IN ('percentage', 'fixed_amount')",
            name='check_discount_type_valid'
        ),
        CheckConstraint(
            "(discount_type = 'percentage' AND discount_value <= 100) OR discount_type = 'fixed_amount'",
            name='check_percentage_max_100'
        ),
        Index("ix_feedback_coupons_station_customer", "station_id", "customer_id"),
        Index("ix_feedback_coupons_code", "coupon_code", unique=True),
        Index("ix_feedback_coupons_status", "status"),
        Index("ix_feedback_coupons_valid_until", "valid_until"),
        Index("ix_feedback_coupons_review", "review_id"),
        {"schema": "feedback"}
    )

    @classmethod
    def generate_coupon_code(cls, prefix: str = "MH") -> str:
        """Generate a unique coupon code."""
        # Format: MH-XXXXXXXX (8 random alphanumeric characters)
        chars = string.ascii_uppercase + string.digits
        random_part = ''.join(secrets.choice(chars) for _ in range(8))
        return f"{prefix}-{random_part}"

    @property
    def is_valid(self) -> bool:
        """Check if coupon is currently valid."""
        now = datetime.now()
        return (
            self.status == 'active' and
            self.valid_from <= now <= self.valid_until and
            self.times_used < self.max_uses
        )

    @property
    def is_expired(self) -> bool:
        """Check if coupon is expired."""
        return datetime.now() > self.valid_until

    def mark_used(self, booking_id: Optional[str] = None) -> None:
        """Mark coupon as used."""
        self.times_used += 1
        if self.times_used >= self.max_uses:
            self.status = 'used'
            self.used_at = datetime.now()
        if booking_id:
            self.used_in_booking_id = booking_id

    @property
    def discount_display(self) -> str:
        """Get human-readable discount value."""
        if self.discount_type == 'percentage':
            return f"{self.discount_value}%"
        else:  # fixed_amount
            return f"${self.discount_value / 100:.2f}"


class ReviewEscalation(Base):
    """Review escalation tracking records."""

    __tablename__ = "review_escalations"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    review_id = Column(PostgresUUID(as_uuid=True), ForeignKey("feedback.customer_reviews.id"), nullable=False)
    
    # Escalation details
    escalation_type = Column(String(50), nullable=False)  # 'admin_notification', 'ai_agent', 'manual'
    priority = Column(String(20), nullable=False, default='medium')  # 'low', 'medium', 'high', 'urgent'
    assigned_to = Column(PostgresUUID(as_uuid=True), nullable=True)
    
    # Content
    escalation_reason = Column(Text, nullable=False)
    action_taken = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default='open')  # 'open', 'in_progress', 'resolved', 'closed'
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    review = relationship("CustomerReview", back_populates="escalations")

    __table_args__ = (
        Index("ix_feedback_escalations_review", "review_id"),
        Index("ix_feedback_escalations_status", "status"),
        Index("ix_feedback_escalations_priority", "priority"),
        {"schema": "feedback"}
    )

    @property
    def is_open(self) -> bool:
        """Check if escalation is still open."""
        return self.status in ('open', 'in_progress')

    @property
    def response_time_hours(self) -> Optional[float]:
        """Calculate response time in hours."""
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
            return delta.total_seconds() / 3600
        return None


__all__ = [
    "CustomerReview",
    "DiscountCoupon",
    "ReviewEscalation"
]
