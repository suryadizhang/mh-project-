"""
Stripe Router Package
=====================

Modularized Stripe payment router (previously a single 1343-line file).
This package provides complete Stripe payment integration for My Hibachi.

Package Structure:
- schemas.py      - Pydantic request/response models
- utils.py        - Helper functions (loyalty tiers, savings calculation)
- checkout.py     - Checkout session endpoints
- payment_intents.py - Payment intent endpoints
- refunds.py      - Refund endpoints (admin permissions)
- payments.py     - Payment listing endpoints
- invoices.py     - Invoice listing endpoints
- analytics.py    - Payment analytics (admin)
- dashboard.py    - Customer dashboard endpoints
- webhooks.py     - Stripe webhook handling (consolidated)

Consolidation Notes (Batch 1):
- Merged 3 duplicate webhook endpoints into single /webhook
- Correctly uses 3% Stripe fee rate (was incorrectly 8%)
- Removed Plaid/ACH/Cash/Check - kept Stripe (card), Zelle (FREE), Venmo

Usage:
    from routers.v1.stripe import router

    # In main.py:
    app.include_router(router, prefix="/api/v1/stripe", tags=["stripe"])
"""

from fastapi import APIRouter

from .analytics import router as analytics_router

# Import sub-routers
from .checkout import router as checkout_router
from .customer_lookup import router as customer_lookup_router

# Import legacy compatibility function for main.py
from .dashboard import get_customer_dashboard_by_stripe_id
from .dashboard import router as dashboard_router
from .invoices import router as invoices_router
from .payment_intents import router as payment_intents_router
from .payments import router as payments_router
from .refunds import router as refunds_router

# Import schemas for external use
from .schemas import (  # Customer lookup schemas
    BookingBalanceInfo,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerBalanceResponse,
    CustomerDashboardResponse,
    CustomerLookupRequest,
    InvoiceListResponse,
    LoyaltyTier,
    PaymentAnalyticsResponse,
    PaymentIntentRequest,
    PaymentIntentResponse,
    PaymentListResponse,
    PaymentWithTipRequest,
    PortalSessionRequest,
    PortalSessionResponse,
    RefundRequest,
    RefundResponse,
    SuggestedTips,
    TaxBreakdownResponse,
    WebhookEventResponse,
)

# Import utilities for external use
from .utils import (
    DEFAULT_TAX_RATE,
    LOYALTY_THRESHOLDS,
    STRIPE_FEE_RATE,
    calculate_suggested_tips,
    calculate_tax_breakdown,
    calculate_zelle_savings,
    determine_loyalty_status,
    format_invoice_for_response,
    format_payment_for_response,
)
from .webhooks import router as webhooks_router

# Create main router
router = APIRouter()

# Include all sub-routers
# Note: Sub-routers define their own paths, these are relative to /api/v1/stripe
router.include_router(checkout_router)  # /checkout/session
router.include_router(payment_intents_router)  # /payment-intent, /confirm-payment, etc.
router.include_router(refunds_router)  # /refund
router.include_router(payments_router)  # /payments, /payments/{id}, /admin/payments
router.include_router(invoices_router)  # /invoices, /invoices/{id}, /admin/invoices
router.include_router(analytics_router)  # /analytics, /analytics/daily
router.include_router(dashboard_router)  # /dashboard, /customer-portal, /loyalty-status
router.include_router(webhooks_router)  # /webhook
router.include_router(customer_lookup_router)  # /lookup, /calculate-total, /suggested-tips

# Export for external imports
__all__ = [
    # Main router
    "router",
    # Legacy compatibility
    "get_customer_dashboard_by_stripe_id",
    # Schemas
    "LoyaltyTier",
    "CheckoutSessionRequest",
    "CheckoutSessionResponse",
    "PaymentIntentRequest",
    "PaymentIntentResponse",
    "RefundRequest",
    "RefundResponse",
    "PaymentListResponse",
    "InvoiceListResponse",
    "PaymentAnalyticsResponse",
    "CustomerDashboardResponse",
    "PortalSessionRequest",
    "PortalSessionResponse",
    "WebhookEventResponse",
    # Customer lookup schemas
    "CustomerLookupRequest",
    "CustomerBalanceResponse",
    "BookingBalanceInfo",
    "TaxBreakdownResponse",
    "SuggestedTips",
    "PaymentWithTipRequest",
    # Utilities
    "LOYALTY_THRESHOLDS",
    "STRIPE_FEE_RATE",
    "DEFAULT_TAX_RATE",
    "determine_loyalty_status",
    "calculate_zelle_savings",
    "format_payment_for_response",
    "format_invoice_for_response",
    "calculate_tax_breakdown",
    "calculate_suggested_tips",
]
