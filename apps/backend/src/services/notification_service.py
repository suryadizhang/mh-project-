"""
Notification Service - Compatibility Alias

This module provides backward compatibility for imports that reference
the old NotificationService name. It redirects to UnifiedNotificationService.

Created: October 30, 2025
Reason: Fix import errors in payment_matcher_service.py and payment_email_scheduler.py
"""

from .unified_notification_service import UnifiedNotificationService as NotificationService
from .unified_notification_service import (
    notify_new_booking,
    notify_booking_edit,
    notify_cancellation,
    notify_payment,
    notify_review,
    notify_complaint,
    get_notification_service
)

__all__ = [
    "NotificationService",
    "notify_new_booking",
    "notify_booking_edit",
    "notify_cancellation",
    "notify_payment",
    "notify_review",
    "notify_complaint",
    "get_notification_service"
]
