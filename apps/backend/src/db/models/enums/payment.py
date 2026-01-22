"""
Payment Enums (Shared)
======================

Centralized payment-related enum definitions.

Industry Standard:
- Uses Stripe terminology (SUCCEEDED instead of COMPLETED)
- Includes CANCELLED status for payment cancellations
- All values are lowercase for database compatibility

CRITICAL: Always use SUCCEEDED for successful payments.
The value "completed" is deprecated and should be migrated.

See: database/migrations/XXX_consolidate_payment_status.sql
"""

from enum import Enum


class PaymentStatus(str, Enum):
    """
    Payment status workflow - Stripe-aligned.

    Values:
        PENDING: Payment initiated, awaiting processing
        PROCESSING: Payment is being processed
        SUCCEEDED: Payment completed successfully (Stripe standard)
        FAILED: Payment failed
        CANCELLED: Payment was cancelled before completion
        REFUNDED: Full refund issued
        PARTIALLY_REFUNDED: Partial refund issued

    Note: "completed" is DEPRECATED. Use "succeeded" for new payments.
    Migration required for existing "completed" records.
    """

    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentType(str, Enum):
    """
    Payment types for booking transactions.

    Values:
        DEPOSIT: Initial deposit to secure booking
        FULL_PAYMENT: Complete payment for service
        PARTIAL_PAYMENT: Partial payment toward balance
        REFUND: Refund transaction
        BALANCE: Remaining balance payment
        ADJUSTMENT: Price adjustment (positive or negative)
    """

    DEPOSIT = "deposit"
    FULL_PAYMENT = "full_payment"
    PARTIAL_PAYMENT = "partial_payment"
    REFUND = "refund"
    BALANCE = "balance"
    ADJUSTMENT = "adjustment"


class InvoiceStatus(str, Enum):
    """
    Invoice status workflow - Stripe-aligned.

    Values:
        DRAFT: Invoice created but not finalized
        OPEN: Invoice sent, awaiting payment
        PAID: Invoice fully paid
        UNCOLLECTIBLE: Invoice marked as uncollectible
        VOID: Invoice voided/cancelled
    """

    DRAFT = "draft"
    OPEN = "open"
    PAID = "paid"
    UNCOLLECTIBLE = "uncollectible"
    VOID = "void"


class RefundStatus(str, Enum):
    """
    Refund status workflow - Stripe-aligned.

    Values:
        PENDING: Refund initiated, awaiting processing
        SUCCEEDED: Refund completed successfully
        FAILED: Refund failed
        CANCELLED: Refund was cancelled
    """

    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WebhookEventStatus(str, Enum):
    """
    Webhook event processing status.

    Values:
        RECEIVED: Event received from payment provider
        PROCESSING: Event is being processed
        PROCESSED: Event successfully processed
        FAILED: Event processing failed
        SKIPPED: Event skipped (duplicate or irrelevant)
    """

    RECEIVED = "received"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    SKIPPED = "skipped"
