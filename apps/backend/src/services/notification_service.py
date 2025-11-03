"""
Notification Service - Compatibility Alias

This module provides backward compatibility for imports that reference
the old NotificationService name. It redirects to UnifiedNotificationService.

Created: October 30, 2025
Reason: Fix import errors in payment_matcher_service.py and payment_email_scheduler.py
"""

from .unified_notification_service import (
    UnifiedNotificationService as NotificationService,
)
from .unified_notification_service import (
    get_notification_service,
    notify_booking_edit,
    notify_cancellation,
    notify_complaint,
    notify_new_booking,
    notify_payment,
    notify_review,
)

__all__ = [
    "NotificationService",
    "get_notification_service",
    "notify_booking_edit",
    "notify_cancellation",
    "notify_complaint",
    "notify_new_booking",
    "notify_payment",
    "notify_review",
]
