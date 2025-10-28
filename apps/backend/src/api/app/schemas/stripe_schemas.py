from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr


class PaymentMethod(str, Enum):
    STRIPE = "stripe"
    ZELLE = "zelle"
    VENMO = "venmo"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class PaymentType(str, Enum):
    DEPOSIT = "deposit"
    BALANCE = "balance"
    FULL = "full"
    ADDON = "addon"
    GRATUITY = "gratuity"


# Base schemas
class CustomerBase(BaseModel):
    email: EmailStr
    name: str | None = None
    phone: str | None = None
    preferred_payment_method: PaymentMethod = PaymentMethod.ZELLE


class CustomerCreate(CustomerBase):
    user_id: str


class CustomerUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    preferred_payment_method: PaymentMethod | None = None


class Customer(CustomerBase):
    id: str
    user_id: str
    stripe_customer_id: str
    total_spent: Decimal
    total_bookings: int
    zelle_savings: Decimal
    loyalty_tier: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# Payment schemas
class LineItem(BaseModel):
    price_id: str | None = None
    quantity: int = 1
    name: str
    amount: int  # in cents
    description: str | None = None


class CreateCheckoutSession(BaseModel):
    booking_id: str
    line_items: list[LineItem]
    mode: str = "payment"
    allow_promo_codes: bool = False
    customer_email: str | None = None
    success_url: str | None = None
    cancel_url: str | None = None


class CreatePaymentIntent(BaseModel):
    booking_id: str
    amount: int  # in cents
    currency: str = "usd"
    customer_email: str | None = None
    payment_type: PaymentType = PaymentType.DEPOSIT
    description: str | None = None
    metadata: dict[str, str] | None = {}


class PaymentBase(BaseModel):
    booking_id: str | None = None
    amount: Decimal
    currency: str = "usd"
    method: PaymentMethod
    payment_type: PaymentType = PaymentType.DEPOSIT
    description: str | None = None


class PaymentCreate(PaymentBase):
    user_id: str
    stripe_payment_intent_id: str | None = None


class Payment(PaymentBase):
    id: str
    user_id: str
    stripe_payment_intent_id: str | None = None
    stripe_customer_id: str | None = None
    status: PaymentStatus
    stripe_fee: Decimal
    net_amount: Decimal | None = None
    metadata_json: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# Invoice schemas
class InvoiceBase(BaseModel):
    booking_id: str | None = None
    amount_due: Decimal
    currency: str = "usd"
    due_date: datetime | None = None


class InvoiceCreate(InvoiceBase):
    user_id: str
    stripe_customer_id: str


class Invoice(InvoiceBase):
    id: str
    user_id: str
    stripe_invoice_id: str
    stripe_customer_id: str
    amount_paid: Decimal
    status: str
    hosted_invoice_url: str | None = None
    invoice_pdf_url: str | None = None
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# Product and Price schemas
class ProductBase(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None


class Product(ProductBase):
    id: str
    stripe_product_id: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PriceBase(BaseModel):
    unit_amount: int  # cents
    currency: str = "usd"
    recurring_interval: str | None = None
    nickname: str | None = None


class Price(PriceBase):
    id: str
    stripe_price_id: str
    product_id: str
    stripe_product_id: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Refund schemas
class RefundCreate(BaseModel):
    payment_id: str
    amount: Decimal | None = None  # None means full refund
    reason: str | None = None
    notes: str | None = None


class Refund(BaseModel):
    id: str
    stripe_refund_id: str
    payment_id: str
    amount: Decimal
    currency: str
    status: str
    reason: str | None = None
    requested_by: str | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# Response schemas
class CheckoutSessionResponse(BaseModel):
    url: str
    session_id: str


class CheckoutSessionVerifyRequest(BaseModel):
    session_id: str


class CheckoutSessionVerifyResponse(BaseModel):
    success: bool
    session_id: str
    payment_status: str  # unpaid, paid, no_payment_required
    payment_intent: str | None = None
    amount_total: int | None = None  # in cents
    currency: str | None = None
    customer_email: str | None = None
    booking_id: str | None = None
    metadata: dict[str, str] | None = None


class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str


class CustomerPortalResponse(BaseModel):
    url: str


class WebhookResponse(BaseModel):
    received: bool
    event_type: str
    event_id: str
    processed: bool = True


# Analytics schemas
class PaymentAnalytics(BaseModel):
    total_payments: int
    total_amount: Decimal
    avg_payment: Decimal
    payment_methods: dict[str, int]
    monthly_revenue: list[dict[str, Any]]


class CustomerAnalytics(BaseModel):
    total_customers: int
    new_customers_this_month: int
    top_customers: list[dict[str, Any]]
    payment_method_preferences: dict[str, int]
    loyalty_distribution: dict[str, int]


# Error schemas
class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    code: str | None = None


# Success schemas
class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] | None = None
