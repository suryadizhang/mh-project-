"""
Shared Enums Module
===================

Centralized enum definitions for the My Hibachi database models.

IMPORTANT: All enums used across multiple model files MUST be defined here
to prevent inconsistencies and maintain Single Source of Truth (SSoT).

Industry Standards Applied:
- Payment statuses use Stripe terminology (SUCCEEDED not COMPLETED)
- Enum values are lowercase strings for database compatibility
- All enums inherit from (str, Enum) for JSON serialization

Migration Note:
- If migrating from COMPLETED to SUCCEEDED, run:
  UPDATE core.payments SET status = 'succeeded' WHERE status = 'completed';
  See: database/migrations/XXX_consolidate_payment_status.sql

Usage:
    from db.models.enums import PaymentStatus, SocialPlatform, SocialThreadStatus

Created: 2025-01-30
"""

from db.models.enums.payment import (
    InvoiceStatus,
    PaymentStatus,
    PaymentType,
    RefundStatus,
    WebhookEventStatus,
)
from db.models.enums.social import SocialPlatform, SocialThreadStatus

__all__ = [
    # Payment enums
    "PaymentStatus",
    "PaymentType",
    "InvoiceStatus",
    "RefundStatus",
    "WebhookEventStatus",
    # Social enums
    "SocialPlatform",
    "SocialThreadStatus",
]
