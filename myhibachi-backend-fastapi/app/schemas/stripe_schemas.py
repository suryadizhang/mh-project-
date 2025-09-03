from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum


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
    name: Optional[str] = None
    phone: Optional[str] = None
    preferred_payment_method: PaymentMethod = PaymentMethod.ZELLE


class CustomerCreate(CustomerBase):
    user_id: str


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    preferred_payment_method: Optional[PaymentMethod] = None


class Customer(CustomerBase):
    id: str
    user_id: str
    stripe_customer_id: str
    total_spent: Decimal
    total_bookings: int
    zelle_savings: Decimal
    loyalty_tier: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Payment schemas
class LineItem(BaseModel):
    price_id: Optional[str] = None
    quantity: int = 1
    name: str
    amount: int  # in cents
    description: Optional[str] = None


class CreateCheckoutSession(BaseModel):
    booking_id: str
    line_items: List[LineItem]
    mode: str = "payment"
    allow_promo_codes: bool = False
    customer_email: Optional[str] = None
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CreatePaymentIntent(BaseModel):
    booking_id: str
    amount: int  # in cents
    currency: str = "usd"
    customer_email: Optional[str] = None
    payment_type: PaymentType = PaymentType.DEPOSIT
    description: Optional[str] = None
    metadata: Optional[Dict[str, str]] = {}


class PaymentBase(BaseModel):
    booking_id: Optional[str] = None
    amount: Decimal
    currency: str = "usd"
    method: PaymentMethod
    payment_type: PaymentType = PaymentType.DEPOSIT
    description: Optional[str] = None


class PaymentCreate(PaymentBase):
    user_id: str
    stripe_payment_intent_id: Optional[str] = None


class Payment(PaymentBase):
    id: str
    user_id: str
    stripe_payment_intent_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    status: PaymentStatus
    stripe_fee: Decimal
    net_amount: Optional[Decimal] = None
    metadata_json: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Invoice schemas
class InvoiceBase(BaseModel):
    booking_id: Optional[str] = None
    amount_due: Decimal
    currency: str = "usd"
    due_date: Optional[datetime] = None


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
    hosted_invoice_url: Optional[str] = None
    invoice_pdf_url: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Product and Price schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None


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
    recurring_interval: Optional[str] = None
    nickname: Optional[str] = None


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
    amount: Optional[Decimal] = None  # None means full refund
    reason: Optional[str] = None
    notes: Optional[str] = None


class Refund(BaseModel):
    id: str
    stripe_refund_id: str
    payment_id: str
    amount: Decimal
    currency: str
    status: str
    reason: Optional[str] = None
    requested_by: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Response schemas
class CheckoutSessionResponse(BaseModel):
    url: str
    session_id: str


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
    payment_methods: Dict[str, int]
    monthly_revenue: List[Dict[str, Any]]


class CustomerAnalytics(BaseModel):
    total_customers: int
    new_customers_this_month: int
    top_customers: List[Dict[str, Any]]
    payment_method_preferences: Dict[str, int]
    loyalty_distribution: Dict[str, int]


# Error schemas
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# Success schemas
class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
