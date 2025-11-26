"""
SQLAlchemy Models - Feedback & Marketing Schemas
=================================================

Feedback Schema:
- Customer Reviews
- Discount Coupons
- Review Escalations

Marketing Schema:
- QR Codes
- QR Scans

All models use:
- UUID primary keys
- Timezone-aware datetime fields
- Schema qualification (__table_args__)
- Proper foreign key relationships
- Type hints for IDE support
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, Numeric,
    ForeignKey, Index, CheckConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from ..base_class import Base


# ==================== ENUMS ====================

import enum

class ReviewRating(str, enum.Enum):
    """Review rating levels"""
    ONE_STAR = "1"
    TWO_STAR = "2"
    THREE_STAR = "3"
    FOUR_STAR = "4"
    FIVE_STAR = "5"


class ReviewStatus(str, enum.Enum):
    """Review moderation status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class CouponStatus(str, enum.Enum):
    """Coupon lifecycle status"""
    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"


class QRCodeType(str, enum.Enum):
    """QR code types"""
    MENU = "menu"
    BOOKING = "booking"
    REVIEW = "review"
    PROMOTION = "promotion"
    EVENT = "event"


# ==================== FEEDBACK SCHEMA ====================

class CustomerReview(Base):
    """
    Customer review entity

    Tracks customer reviews with rating, sentiment analysis,
    and moderation workflow.
    """
    __tablename__ = "customer_reviews"
    __table_args__ = (
        Index("idx_customer_reviews_booking_id", "booking_id"),
        Index("idx_customer_reviews_customer_id", "customer_id"),
        Index("idx_customer_reviews_rating", "rating"),
        Index("idx_customer_reviews_status", "status"),
        Index("idx_customer_reviews_created_at", "created_at"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="check_rating_range"),
        {"schema": "feedback"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    booking_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.bookings.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("core.customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Review Details
    rating: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1-5
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Sentiment Analysis (from AI)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)  # -1.0 to 1.0
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # positive/neutral/negative

    # Moderation
    status: Mapped[ReviewStatus] = mapped_column(
        SQLEnum(ReviewStatus, name="review_status", schema="feedback", create_type=False),
        nullable=False,
        server_default="pending",
        index=True
    )
    moderation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moderated_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True
    )
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Public Display
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    display_on_website: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    escalations: Mapped[list["ReviewEscalation"]] = relationship("ReviewEscalation", back_populates="review")


class DiscountCoupon(Base):
    """
    Discount coupon entity

    Promotional codes for discounts and special offers.
    """
    __tablename__ = "discount_coupons"
    __table_args__ = (
        Index("idx_discount_coupons_code", "code"),
        Index("idx_discount_coupons_status", "status"),
        Index("idx_discount_coupons_valid_from", "valid_from"),
        Index("idx_discount_coupons_valid_until", "valid_until"),
        CheckConstraint("discount_percentage >= 0 AND discount_percentage <= 100", name="check_discount_percentage"),
        CheckConstraint("discount_amount >= 0", name="check_discount_amount"),
        CheckConstraint("max_uses > 0", name="check_max_uses_positive"),
        {"schema": "feedback"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Coupon Details
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Discount Type (either percentage OR fixed amount)
    discount_percentage: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    discount_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # cents

    # Validity
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Usage Limits
    max_uses: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    current_uses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Restrictions
    min_booking_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # cents
    max_discount_amount: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # cents

    # Status
    status: Mapped[CouponStatus] = mapped_column(
        SQLEnum(CouponStatus, name="coupon_status", schema="feedback", create_type=False),
        nullable=False,
        server_default="active",
        index=True
    )

    # Metadata
    coupon_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )


class ReviewEscalation(Base):
    """
    Review escalation entity

    Tracks negative reviews that require management attention.
    """
    __tablename__ = "review_escalations"
    __table_args__ = (
        Index("idx_review_escalations_review_id", "review_id"),
        Index("idx_review_escalations_assigned_to_id", "assigned_to_id"),
        Index("idx_review_escalations_is_resolved", "is_resolved"),
        {"schema": "feedback"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    review_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("feedback.customer_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    assigned_to_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("public.users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Escalation Details
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")  # low/medium/high

    # Resolution
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    review: Mapped["CustomerReview"] = relationship("CustomerReview", back_populates="escalations")


# ==================== MARKETING SCHEMA ====================

class QRCode(Base):
    """
    QR code entity

    Dynamic QR codes for menus, bookings, reviews, and promotions.
    """
    __tablename__ = "qr_codes"
    __table_args__ = (
        Index("idx_qr_codes_code", "code"),
        Index("idx_qr_codes_type", "type"),
        Index("idx_qr_codes_active", "is_active"),
        {"schema": "marketing"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # QR Details
    code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    type: Mapped[QRCodeType] = mapped_column(
        SQLEnum(QRCodeType, name="qr_code_type", schema="marketing", create_type=False),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Target URL
    target_url: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Tracking
    scan_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    # Metadata
    qr_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    scans: Mapped[list["QRScan"]] = relationship("QRScan", back_populates="qr_code", cascade="all, delete-orphan")


class QRScan(Base):
    """
    QR scan entity

    Tracks individual QR code scans for analytics.
    """
    __tablename__ = "qr_scans"
    __table_args__ = (
        Index("idx_qr_scans_qr_code_id", "qr_code_id"),
        Index("idx_qr_scans_scanned_at", "scanned_at"),
        {"schema": "marketing"}
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    qr_code_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("marketing.qr_codes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Scan Details
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Location (if available)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    scan_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Timestamp
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    # Relationships
    qr_code: Mapped["QRCode"] = relationship("QRCode", back_populates="scans")
