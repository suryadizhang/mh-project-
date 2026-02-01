"""
Email Monitoring Celery Tasks
=============================

Schedules both email monitoring systems:
1. Gmail (payment notifications) - myhibachichef@gmail.com
2. IONOS (customer support) - cs@myhibachichef.com

OPTION C: Full Redundancy Implementation
- Startup validation for credentials
- Health status tracking
- Automatic failover
- Error alerting

See: docs/04-DEPLOYMENT/LEGAL_PROTECTION_IMPLEMENTATION.md
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from celery import shared_task

from core.config import get_settings
from core.database import SessionLocal

logger = logging.getLogger(__name__)

# Health status tracking (in-memory, resets on worker restart)
# For persistent tracking, use Redis or database
EMAIL_MONITOR_STATUS = {
    "gmail": {
        "last_check": None,
        "last_success": None,
        "last_error": None,
        "error_message": None,
        "consecutive_failures": 0,
        "total_checks": 0,
        "total_emails_processed": 0,
    },
    "ionos": {
        "last_check": None,
        "last_success": None,
        "last_error": None,
        "error_message": None,
        "consecutive_failures": 0,
        "total_checks": 0,
        "total_emails_processed": 0,
    },
}


def validate_email_credentials() -> dict[str, bool]:
    """
    Validate that all required email credentials are configured.

    Returns:
        Dict with validation status for each email system

    Raises:
        ValueError if critical credentials are missing (fail-fast mode)
    """
    settings = get_settings()

    validation = {
        "gmail_valid": False,
        "ionos_valid": False,
        "gmail_errors": [],
        "ionos_errors": [],
    }

    # Gmail validation
    gmail_user = getattr(settings, "GMAIL_USER", None)
    gmail_password = getattr(settings, "GMAIL_APP_PASSWORD", None)

    if not gmail_user:
        validation["gmail_errors"].append("GMAIL_USER not configured in .env")
    if not gmail_password:
        validation["gmail_errors"].append("GMAIL_APP_PASSWORD not configured in .env")

    validation["gmail_valid"] = len(validation["gmail_errors"]) == 0

    # IONOS validation
    smtp_password = getattr(settings, "SMTP_PASSWORD", None)
    smtp_user = getattr(settings, "SMTP_USER", "cs@myhibachichef.com")

    if not smtp_password:
        validation["ionos_errors"].append("SMTP_PASSWORD not configured in .env")

    validation["ionos_valid"] = len(validation["ionos_errors"]) == 0

    # Log validation results
    if not validation["gmail_valid"]:
        logger.error(f"❌ Gmail validation failed: {validation['gmail_errors']}")
    else:
        logger.info(f"✅ Gmail credentials validated for {gmail_user}")

    if not validation["ionos_valid"]:
        logger.error(f"❌ IONOS validation failed: {validation['ionos_errors']}")
    else:
        logger.info(f"✅ IONOS credentials validated for {smtp_user}")

    return validation


def get_email_monitor_status() -> dict:
    """Get current health status for all email monitors."""
    return {
        "gmail": EMAIL_MONITOR_STATUS["gmail"].copy(),
        "ionos": EMAIL_MONITOR_STATUS["ionos"].copy(),
        "validation": validate_email_credentials(),
    }


@shared_task(name="workers.email_monitoring_tasks.check_gmail_emails")
def check_gmail_emails() -> dict[str, Any]:
    """
    Check Gmail for new payment notifications.

    Uses imapclient for IMAP IDLE with fallback to polling.
    Processes new payment notifications and matches to pending bookings.

    Returns:
        Dict with check results
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)

    EMAIL_MONITOR_STATUS["gmail"]["last_check"] = now.isoformat()
    EMAIL_MONITOR_STATUS["gmail"]["total_checks"] += 1

    result = {
        "success": False,
        "emails_found": 0,
        "payments_matched": 0,
        "error": None,
    }

    try:
        # Validate credentials first
        gmail_user = getattr(settings, "GMAIL_USER", None)
        gmail_password = getattr(settings, "GMAIL_APP_PASSWORD", None)

        if not gmail_user or not gmail_password:
            error_msg = "Gmail credentials not configured (GMAIL_USER or GMAIL_APP_PASSWORD missing)"
            logger.error(f"❌ {error_msg}")
            EMAIL_MONITOR_STATUS["gmail"]["last_error"] = now.isoformat()
            EMAIL_MONITOR_STATUS["gmail"]["error_message"] = error_msg
            EMAIL_MONITOR_STATUS["gmail"]["consecutive_failures"] += 1
            result["error"] = error_msg
            return result

        # Import here to avoid circular imports
        from services.email_service import EmailService
        from services.notification_service import NotificationService
        from services.payment_email_monitor import PaymentEmailMonitor
        from services.payment_matcher_service import check_payment_emails_task

        db = SessionLocal()

        try:
            email_monitor = PaymentEmailMonitor(
                email_address=gmail_user,
                app_password=gmail_password,
                db_session=db,
            )

            email_service = EmailService()
            notify_service = NotificationService()

            # Run the check
            results = asyncio.run(
                check_payment_emails_task(
                    db=db,
                    email_monitor=email_monitor,
                    email_service=email_service,
                    notify_service=notify_service,
                )
            )

            result["success"] = True
            result["emails_found"] = results.get("emails_checked", 0)
            result["payments_matched"] = results.get("payments_confirmed", 0)

            EMAIL_MONITOR_STATUS["gmail"]["last_success"] = now.isoformat()
            EMAIL_MONITOR_STATUS["gmail"]["consecutive_failures"] = 0
            EMAIL_MONITOR_STATUS["gmail"]["total_emails_processed"] += result[
                "emails_found"
            ]
            EMAIL_MONITOR_STATUS["gmail"]["error_message"] = None

            logger.info(
                f"✅ Gmail check complete: {result['emails_found']} emails, {result['payments_matched']} payments matched"
            )

        finally:
            db.close()

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"❌ Gmail check failed: {error_msg}")

        EMAIL_MONITOR_STATUS["gmail"]["last_error"] = now.isoformat()
        EMAIL_MONITOR_STATUS["gmail"]["error_message"] = error_msg
        EMAIL_MONITOR_STATUS["gmail"]["consecutive_failures"] += 1
        result["error"] = error_msg

        # Alert if too many consecutive failures
        if EMAIL_MONITOR_STATUS["gmail"]["consecutive_failures"] >= 3:
            logger.critical(
                f"🚨 CRITICAL: Gmail monitor has failed {EMAIL_MONITOR_STATUS['gmail']['consecutive_failures']} times consecutively!"
            )

    return result


@shared_task(name="workers.email_monitoring_tasks.check_ionos_emails")
def check_ionos_emails() -> dict[str, Any]:
    """
    Check IONOS inbox for new customer support emails.

    Monitors cs@myhibachichef.com for:
    - New customer inquiries
    - Support requests
    - Booking-related questions
    - Replies to outbound emails

    Returns:
        Dict with check results
    """
    settings = get_settings()
    now = datetime.now(timezone.utc)

    EMAIL_MONITOR_STATUS["ionos"]["last_check"] = now.isoformat()
    EMAIL_MONITOR_STATUS["ionos"]["total_checks"] += 1

    result = {
        "success": False,
        "emails_found": 0,
        "emails_processed": 0,
        "error": None,
    }

    try:
        # Validate credentials
        smtp_password = getattr(settings, "SMTP_PASSWORD", None)
        smtp_user = getattr(settings, "SMTP_USER", "cs@myhibachichef.com")

        if not smtp_password:
            error_msg = "IONOS credentials not configured (SMTP_PASSWORD missing)"
            logger.error(f"❌ {error_msg}")
            EMAIL_MONITOR_STATUS["ionos"]["last_error"] = now.isoformat()
            EMAIL_MONITOR_STATUS["ionos"]["error_message"] = error_msg
            EMAIL_MONITOR_STATUS["ionos"]["consecutive_failures"] += 1
            result["error"] = error_msg
            return result

        # Import here to avoid circular imports
        from services.customer_email_monitor import CustomerEmailMonitor

        monitor = CustomerEmailMonitor(
            email_address=smtp_user,
            password=smtp_password,
            imap_server=getattr(settings, "IMAP_SERVER", "imap.ionos.com"),
            imap_port=int(getattr(settings, "IMAP_PORT", 993)),
        )

        # Connect and check for emails
        if not monitor.connect():
            error_msg = "Failed to connect to IONOS IMAP server"
            EMAIL_MONITOR_STATUS["ionos"]["last_error"] = now.isoformat()
            EMAIL_MONITOR_STATUS["ionos"]["error_message"] = error_msg
            EMAIL_MONITOR_STATUS["ionos"]["consecutive_failures"] += 1
            result["error"] = error_msg
            return result

        try:
            # Check for unread emails
            emails = monitor.fetch_unread_emails()
            result["emails_found"] = len(emails)

            # Process each email (create leads, link to bookings, etc.)
            for email_data in emails:
                try:
                    processed = process_customer_email(email_data)
                    if processed:
                        result["emails_processed"] += 1
                except Exception as e:
                    logger.error(f"Error processing customer email: {e}")

            result["success"] = True

            EMAIL_MONITOR_STATUS["ionos"]["last_success"] = now.isoformat()
            EMAIL_MONITOR_STATUS["ionos"]["consecutive_failures"] = 0
            EMAIL_MONITOR_STATUS["ionos"]["total_emails_processed"] += result[
                "emails_processed"
            ]
            EMAIL_MONITOR_STATUS["ionos"]["error_message"] = None

            logger.info(
                f"✅ IONOS check complete: {result['emails_found']} emails, {result['emails_processed']} processed"
            )

        finally:
            monitor.disconnect()

    except Exception as e:
        error_msg = str(e)
        logger.exception(f"❌ IONOS check failed: {error_msg}")

        EMAIL_MONITOR_STATUS["ionos"]["last_error"] = now.isoformat()
        EMAIL_MONITOR_STATUS["ionos"]["error_message"] = error_msg
        EMAIL_MONITOR_STATUS["ionos"]["consecutive_failures"] += 1
        result["error"] = error_msg

        # Alert if too many consecutive failures
        if EMAIL_MONITOR_STATUS["ionos"]["consecutive_failures"] >= 3:
            logger.critical(
                f"🚨 CRITICAL: IONOS monitor has failed {EMAIL_MONITOR_STATUS['ionos']['consecutive_failures']} times consecutively!"
            )

    return result


def process_customer_email(email_data: dict) -> bool:
    """
    Process a customer email from IONOS inbox.

    Actions:
    - Create lead if from new customer
    - Link to existing booking if identifiable
    - Create support ticket/thread
    - Notify admin for urgent emails

    Args:
        email_data: Parsed email data from CustomerEmailMonitor

    Returns:
        True if successfully processed
    """
    try:
        from_addr = email_data.get("from", "")
        subject = email_data.get("subject", "")
        body = email_data.get("text_body", "")

        logger.info(f"📧 Processing customer email from {from_addr}: {subject[:50]}...")

        # TODO: Implement full processing logic in Batch 4
        # For now, just log and return success
        # Future implementation:
        # 1. Check if from_addr matches existing customer
        # 2. Check if subject contains booking reference
        # 3. Create or update support thread
        # 4. Auto-respond if auto-reply enabled
        # 5. Notify admin for urgent keywords

        return True

    except Exception as e:
        logger.error(f"Error processing email: {e}")
        return False


@shared_task(name="workers.email_monitoring_tasks.check_all_email_monitors")
def check_all_email_monitors() -> dict:
    """
    Combined task to check all email monitors.
    Useful for a single beat schedule entry.
    """
    gmail_result = check_gmail_emails()
    ionos_result = check_ionos_emails()

    return {
        "gmail": gmail_result,
        "ionos": ionos_result,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@shared_task(name="workers.email_monitoring_tasks.get_monitor_health")
def get_monitor_health() -> dict:
    """
    Get health status for all email monitors.
    Can be called via API or Celery to check status.
    """
    return get_email_monitor_status()
