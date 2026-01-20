"""
Stripe Router Schemas
=====================

Pydantic models for Stripe API requests and responses.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoyaltyTier(str, Enum):
    """Customer loyalty tier based on total spending."""

    NEW = "new"
    SILVER = "silver"
    GOLD = "gold"
    VIP = "vip"


class CheckoutSessionRequest(BaseModel):
    """Request model for creating a checkout session."""

    booking_id: Optional[UUID] = None
    amount: int = Field(..., ge=100, description="Amount in cents, minimum $1.00")
    currency: str = Field(default="usd", pattern="^[a-z]{3}$")
    description: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None
    customer_email: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class CheckoutSessionResponse(BaseModel):
    """Response model for checkout session creation."""

    session_id: str
    checkout_url: str
    expires_at: Optional[datetime] = None


class PaymentIntentRequest(BaseModel):
    """Request model for creating a payment intent."""

    amount: int = Field(..., ge=100, description="Amount in cents")
    currency: str = Field(default="usd")
    booking_id: Optional[UUID] = None
    customer_email: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None


class PaymentIntentResponse(BaseModel):
    """Response model for payment intent creation."""

    client_secret: str
    payment_intent_id: str
    amount: int
    currency: str
    status: str


class RefundRequest(BaseModel):
    """Request model for creating a refund."""

    payment_intent_id: str
    amount: Optional[int] = Field(
        default=None, ge=1, description="Partial refund amount in cents"
    )
    reason: Optional[str] = None


class RefundResponse(BaseModel):
    """Response model for refund creation."""

    refund_id: str
    amount: int
    status: str
    payment_intent_id: str


class PaymentListResponse(BaseModel):
    """Response model for paginated payment list."""

    payments: List[Dict[str, Any]]
    total: int
    has_more: bool
    next_cursor: Optional[str] = None


class InvoiceListResponse(BaseModel):
    """Response model for paginated invoice list."""

    invoices: List[Dict[str, Any]]
    total: int
    has_more: bool
    next_cursor: Optional[str] = None


class PaymentAnalyticsResponse(BaseModel):
    """Response model for payment analytics (admin only)."""

    total_revenue: Decimal
    total_payments: int
    successful_payments: int
    failed_payments: int
    average_transaction: Decimal
    revenue_by_method: Dict[str, Decimal]
    daily_revenue: List[Dict[str, Any]]


class CustomerDashboardResponse(BaseModel):
    """Response model for customer payment dashboard."""

    total_spent: Decimal
    payment_count: int
    last_payment_date: Optional[datetime] = None
    preferred_payment_method: Optional[str] = None
    loyalty_tier: LoyaltyTier
    savings_from_zelle: Decimal
    recent_payments: List[Dict[str, Any]]


class PortalSessionRequest(BaseModel):
    """Request model for creating a customer portal session."""

    return_url: Optional[str] = None


class PortalSessionResponse(BaseModel):
    """Response model for customer portal session."""

    portal_url: str
    expires_at: Optional[datetime] = None


class WebhookEventResponse(BaseModel):
    """Response model for webhook event processing."""

    received: bool
    event_id: Optional[str] = None
    event_type: Optional[str] = None
    processed: bool = False
    message: Optional[str] = None


# ============================================================================
# Customer Lookup & Balance Schemas
# ============================================================================


class CustomerLookupRequest(BaseModel):
    """Request model for customer lookup by phone or email."""

    phone: Optional[str] = Field(default=None, description="Customer phone number")
    email: Optional[str] = Field(default=None, description="Customer email address")

    class Config:
        json_schema_extra = {
            "example": {"phone": "+19167408768", "email": "customer@example.com"}
        }


class BookingBalanceInfo(BaseModel):
    """Booking balance information."""

    booking_id: UUID
    event_date: Optional[datetime] = None
    total_due_cents: int
    deposit_paid_cents: int
    balance_due_cents: int
    travel_fee_cents: int
    status: str


class TaxBreakdownResponse(BaseModel):
    """Tax calculation breakdown."""

    taxable_amount_cents: int
    tax_amount_cents: int
    travel_fee_cents: int
    tip_cents: int
    subtotal_cents: int
    total_cents: int
    tax_rate: float


class SuggestedTips(BaseModel):
    """Suggested tip amounts."""

    tip_20_percent: int
    tip_25_percent: int
    tip_30_percent: int
    tip_35_percent: int


class CustomerBalanceResponse(BaseModel):
    """Response model for customer balance lookup."""

    customer_id: UUID
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

    # Active bookings with balances
    bookings: List[BookingBalanceInfo]

    # Totals
    total_balance_due_cents: int
    total_travel_fee_cents: int

    # Tax calculation (on balance without travel fee)
    tax_breakdown: TaxBreakdownResponse

    # Suggested tips (on taxable amount)
    suggested_tips: SuggestedTips

    # Loyalty info
    loyalty_tier: LoyaltyTier
    total_spent_cents: int


class PaymentWithTipRequest(BaseModel):
    """Request model for payment with optional tip."""

    booking_id: UUID
    tip_cents: int = Field(default=0, ge=0, description="Tip amount in cents")
    payment_method: str = Field(default="stripe", pattern="^(stripe|venmo|zelle|cash)$")

    class Config:
        json_schema_extra = {
            "example": {
                "booking_id": "123e4567-e89b-12d3-a456-426614174000",
                "tip_cents": 10000,
                "payment_method": "stripe",
            }
        }
