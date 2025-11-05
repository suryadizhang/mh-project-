"""
Background Service for Payment Email Monitoring

Uses IMAP IDLE for real-time email notifications (push-based) with imapclient library.
Falls back to polling every 5 minutes as a safety net.
Processes new notifications and updates payment/booking status.
Cleans up old processed notifications after 2+ days (if read).
"""

import asyncio
from datetime import datetime, timedelta
import logging
from threading import Thread
import time

import schedule
from sqlalchemy import and_

# Use imapclient for more reliable IMAP IDLE support
try:
    from imapclient import IMAPClient

    IMAP_CLIENT_AVAILABLE = True
except ImportError:
    import imaplib

    IMAP_CLIENT_AVAILABLE = False
    logging.warning("imapclient not installed - IMAP IDLE will use fallback mode")

from core.config import get_settings
from core.database import SessionLocal
from services.payment_email_monitor import PaymentEmailMonitor

settings = get_settings()
import builtins
import contextlib

from services.email_service import EmailService
from services.notification_service import NotificationService
from services.payment_matcher_service import check_payment_emails_task

logger = logging.getLogger(__name__)


class PaymentEmailScheduler:
    """Background service for payment email monitoring with IMAP IDLE"""

    def __init__(self, check_interval_minutes: int = 5, use_imap_idle: bool = True):
        """
        Initialize email monitoring service

        Args:
            check_interval_minutes: Fallback polling interval (default: 5 minutes)
            use_imap_idle: Use IMAP IDLE for real-time push notifications (default: True with imapclient)
        """
        self.check_interval_minutes = check_interval_minutes
        self.use_imap_idle = use_imap_idle
        self.is_running = False
        self.thread: Thread | None = None
        self.idle_thread: Thread | None = None
        self.last_run: datetime | None = None
        self.run_count = 0
        self.error_count = 0
        self.idle_connection: imaplib.IMAP4_SSL | None = None

    def check_emails_job(self):
        """Job that runs on schedule to check emails"""
        try:
            logger.info(f"🔍 Starting scheduled payment email check (run #{self.run_count + 1})")

            # Create database session
            db = SessionLocal()

            try:
                # Initialize services
                email_monitor = PaymentEmailMonitor(
                    email_address=settings.GMAIL_USER,
                    app_password=settings.GMAIL_APP_PASSWORD,
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

                # Update stats
                self.last_run = datetime.utcnow()
                self.run_count += 1

                # Log results
                if results["payments_confirmed"] > 0:
                    logger.info(
                        f"✅ Email check complete: "
                        f"{results['payments_confirmed']} payment(s) confirmed, "
                        f"{results['emails_found']} email(s) found"
                    )
                else:
                    logger.info(
                        f"✅ Email check complete: No new payments to confirm "
                        f"({results['emails_found']} email(s) found)"
                    )

                # Log errors
                if results["errors"]:
                    self.error_count += len(results["errors"])
                    logger.warning(f"⚠️ {len(results['errors'])} error(s) during email check")
                    for error in results["errors"]:
                        logger.error(f"  - {error}")

            finally:
                db.close()

        except Exception as e:
            logger.exception(f"❌ Error in scheduled email check: {e}")
            self.error_count += 1

    def cleanup_old_notifications_job(self):
        """
        Clean up old processed payment notifications with smart retention policy:

        READ Notifications:
        - Must be at least 2 days old
        - Must be processed (CONFIRMED or IGNORED status)

        UNREAD Notifications:
        - Must be at least 14 days old (2 weeks)
        - Deleted regardless of status to prevent flooding
        - Admin has 2 weeks to review before auto-cleanup

        Runs daily at 2 AM.
        """
        try:
            logger.info("🧹 Starting old notification cleanup job...")

            # Create database session
            db = SessionLocal()

            try:
                # Import models here to avoid circular imports
                from models.payment_notification import (
                    PaymentNotification,
                    PaymentNotificationStatus,
                )

                # Calculate cutoff dates
                cutoff_date_read = datetime.utcnow() - timedelta(days=2)  # 2 days for read
                cutoff_date_unread = datetime.utcnow() - timedelta(days=14)  # 14 days for unread

                # Find old READ processed notifications (2+ days old)
                old_read_notifications = (
                    db.query(PaymentNotification)
                    .filter(
                        and_(
                            PaymentNotification.created_at < cutoff_date_read,
                            PaymentNotification.is_processed,
                            PaymentNotification.is_read,
                            PaymentNotification.status.in_(
                                [
                                    PaymentNotificationStatus.CONFIRMED,
                                    PaymentNotificationStatus.IGNORED,
                                ]
                            ),
                        )
                    )
                    .all()
                )

                # Find old UNREAD notifications (14+ days old) - prevent flooding
                old_unread_notifications = (
                    db.query(PaymentNotification)
                    .filter(
                        and_(
                            PaymentNotification.created_at < cutoff_date_unread,
                            not PaymentNotification.is_read,
                        )
                    )
                    .all()
                )

                total_to_delete = len(old_read_notifications) + len(old_unread_notifications)

                if total_to_delete == 0:
                    logger.info("✅ No old notifications to clean up")
                    return

                # Count by type for logging
                read_count = len(old_read_notifications)
                unread_count = len(old_unread_notifications)

                # Delete old READ notifications
                for notif in old_read_notifications:
                    db.delete(notif)

                # Delete old UNREAD notifications (prevent flooding)
                for notif in old_unread_notifications:
                    db.delete(notif)

                db.commit()

                logger.info(
                    f"✅ Cleanup complete: Deleted {total_to_delete} notification(s) "
                    f"[{read_count} READ (2+ days), {unread_count} UNREAD (14+ days)]"
                )

            except Exception as e:
                db.rollback()
                logger.exception(f"Error during cleanup: {e}")
                raise

            finally:
                db.close()

        except Exception as e:
            logger.exception(f"❌ Error in cleanup job: {e}")
            self.error_count += 1

    def imap_idle_monitor(self):
        """
        Monitor for new emails using IMAP IDLE (push notifications) with imapclient library.
        Only checks when emails actually arrive - no polling!
        Reconnects automatically if connection drops.
        More reliable than raw imaplib with proper SSL handling.
        """
        logger.info("📧 Starting IMAP IDLE monitor for real-time email notifications...")

        while self.is_running:
            try:
                if IMAP_CLIENT_AVAILABLE:
                    # Use imapclient for robust IMAP IDLE
                    with IMAPClient(host="imap.gmail.com", ssl=True, port=993) as client:
                        # Login
                        client.login(
                            settings.GMAIL_USER,
                            settings.GMAIL_APP_PASSWORD_IMAP or settings.GMAIL_APP_PASSWORD,
                        )

                        # Select inbox
                        client.select_folder("INBOX")

                        logger.info(
                            "✅ IMAP IDLE connected (imapclient) - waiting for new emails (real-time push mode)"
                        )

                        while self.is_running:
                            # Start IDLE mode - server will push when email arrives
                            client.idle()
                            logger.debug("📬 IDLE mode activated - listening for new emails...")

                            # Wait for notification (timeout after 28 minutes, server max is 29-30)
                            responses = client.idle_check(timeout=28 * 60)

                            if responses:
                                # Check if it's a new message notification
                                for response in responses:
                                    if b"EXISTS" in response or b"RECENT" in response:
                                        logger.info(
                                            "📬 New email detected via IMAP IDLE - processing immediately..."
                                        )

                                        # Exit IDLE mode to process
                                        client.idle_done()

                                        # Process new emails
                                        self.check_emails_job()

                                        # Break inner loop to re-enter IDLE
                                        break
                                else:
                                    # No new email, continue IDLE
                                    client.idle_done()
                                    continue

                                # If we broke out, re-enter IDLE in next iteration
                                continue
                            else:
                                # Timeout - exit IDLE and reconnect (keepalive)
                                logger.debug(
                                    "IMAP IDLE timeout (28 min) - reconnecting for keepalive..."
                                )
                                client.idle_done()
                                break  # Break to reconnect

                else:
                    # Fallback to raw imaplib (less reliable)
                    logger.warning(
                        "Using fallback imaplib for IMAP IDLE - consider installing imapclient"
                    )
                    import imaplib
                    import ssl

                    ssl_context = ssl.create_default_context()
                    self.idle_connection = imaplib.IMAP4_SSL(
                        host="imap.gmail.com", port=993, ssl_context=ssl_context
                    )

                    # Login
                    self.idle_connection.login(
                        settings.GMAIL_USER,
                        settings.GMAIL_APP_PASSWORD_IMAP or settings.GMAIL_APP_PASSWORD,
                    )

                    # Select inbox
                    status, messages = self.idle_connection.select("INBOX")
                    if status != "OK":
                        raise Exception(f"Failed to select INBOX: {status}")

                    logger.info(
                        "✅ IMAP IDLE connected (fallback) - waiting for new emails (push mode)"
                    )

                    # Simple IDLE loop for fallback
                    while self.is_running:
                        try:
                            tag = self.idle_connection._new_tag().decode()
                            self.idle_connection.send(f"{tag} IDLE\r\n".encode())

                            resp = self.idle_connection.readline()
                            if b"+" not in resp:
                                logger.warning(f"Unexpected IDLE response: {resp}")
                                break

                            # Wait for notifications (25-minute timeout)
                            self.idle_connection.sock.settimeout(25 * 60)

                            try:
                                line = self.idle_connection.readline()

                                if b"EXISTS" in line:
                                    logger.info(
                                        "📬 New email detected via IMAP IDLE (fallback) - processing..."
                                    )

                                    # Exit IDLE mode
                                    self.idle_connection.send(b"DONE\r\n")
                                    while True:
                                        resp = self.idle_connection.readline()
                                        if tag.encode() in resp:
                                            break

                                    # Process emails
                                    self.check_emails_job()
                                    break  # Re-enter IDLE

                            except TimeoutError:
                                logger.debug("IMAP IDLE timeout - reconnecting...")
                                self.idle_connection.send(b"DONE\r\n")
                                with contextlib.suppress(builtins.BaseException):
                                    self.idle_connection.logout()
                                break
                        except Exception as e:
                            logger.exception(f"IMAP IDLE error in loop: {e}")
                            break

            except Exception as e:
                logger.exception(f"❌ IMAP IDLE connection error: {e}")
                if hasattr(self, "idle_connection") and self.idle_connection:
                    with contextlib.suppress(builtins.BaseException):
                        self.idle_connection.logout()
                    self.idle_connection = None

                # Wait before reconnecting
                if self.is_running:
                    logger.info("⏳ Reconnecting IMAP IDLE in 60 seconds...")
                    time.sleep(60)

        logger.info("📧 IMAP IDLE monitor stopped")

    def run_scheduler(self):
        """Run the scheduler loop (blocking) - IMAP IDLE + fallback polling + cleanup"""
        if self.use_imap_idle:
            mode = "imapclient" if IMAP_CLIENT_AVAILABLE else "imaplib fallback"
            logger.info(
                f"🚀 Payment email service started: "
                f"Real-time push notifications (IMAP IDLE with {mode}) + "
                f"fallback polling every {self.check_interval_minutes} minutes"
            )
        else:
            logger.info(
                f"🚀 Payment email service started: "
                f"Polling every {self.check_interval_minutes} minute(s) "
                f"(IMAP IDLE disabled)"
            )

        # Schedule email checking job (fallback polling)
        schedule.every(self.check_interval_minutes).minutes.do(self.check_emails_job)

        # Schedule cleanup job (daily at 2 AM)
        schedule.every().day.at("02:00").do(self.cleanup_old_notifications_job)

        # Log scheduled jobs
        logger.info("📅 Scheduled jobs:")
        if self.use_imap_idle:
            logger.info("  - Real-time email monitoring: IMAP IDLE (push notifications)")
            logger.info(f"  - Fallback email check: Every {self.check_interval_minutes} minute(s)")
        else:
            logger.info(f"  - Email check: Every {self.check_interval_minutes} minute(s)")
        logger.info("  - Cleanup: Daily at 2:00 AM (READ: 2+ days, UNREAD: 14+ days)")

        # Run scheduler loop
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)

        logger.info("Payment email scheduler stopped")

    def start(self):
        """Start the email monitoring service in background threads"""
        if self.is_running:
            logger.warning("Email monitoring service is already running")
            return

        self.is_running = True

        # Start scheduler thread (for fallback polling + cleanup)
        self.thread = Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()

        # Start IMAP IDLE thread if enabled (for real-time push notifications)
        if self.use_imap_idle:
            self.idle_thread = Thread(target=self.imap_idle_monitor, daemon=True)
            self.idle_thread.start()
            logger.info(
                "✅ Payment email service started: Real-time push (IMAP IDLE) + fallback polling"
            )
        else:
            logger.info(
                f"✅ Payment email service started: Polling every {self.check_interval_minutes} minutes"
            )

    def stop(self):
        """Stop the email monitoring service"""
        if not self.is_running:
            logger.warning("Email monitoring service is not running")
            return

        self.is_running = False

        # Close IMAP connection
        if self.idle_connection:
            try:
                self.idle_connection.send(b"DONE\r\n")
                self.idle_connection.logout()
            except (OSError, Exception) as e:
                # If logout fails, connection is likely already closed
                logger.debug(f"IMAP logout error (expected during shutdown): {e}")
                pass

        # Wait for threads to finish
        if self.thread:
            self.thread.join(timeout=5)

        if self.idle_thread:
            self.idle_thread.join(timeout=5)

        logger.info("Payment email service stopped")

    def get_status(self) -> dict:
        """Get email monitoring service status"""
        return {
            "is_running": self.is_running,
            "mode": "IMAP IDLE (real-time push)" if self.use_imap_idle else "Polling",
            "imap_idle_enabled": self.use_imap_idle,
            "imap_idle_connected": self.idle_connection is not None,
            "fallback_polling_interval_minutes": self.check_interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "next_scheduled_run": schedule.next_run().isoformat() if self.is_running else None,
        }


# Global scheduler instance
_scheduler: PaymentEmailScheduler | None = None


def get_scheduler() -> PaymentEmailScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler

    if _scheduler is None:
        # Get settings from environment or use defaults
        check_interval = getattr(
            settings, "PAYMENT_EMAIL_CHECK_INTERVAL_MINUTES", 30
        )  # 30-min fallback
        use_imap_idle = getattr(
            settings, "PAYMENT_EMAIL_USE_IMAP_IDLE", True
        )  # Real-time push enabled
        _scheduler = PaymentEmailScheduler(
            check_interval_minutes=check_interval, use_imap_idle=use_imap_idle
        )

    return _scheduler


def start_payment_email_scheduler():
    """Start the payment email monitoring scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_payment_email_scheduler():
    """Stop the payment email monitoring scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()


# FastAPI lifespan events
async def on_startup():
    """Called when FastAPI app starts"""
    try:
        # Check if email monitoring is configured
        if not settings.GMAIL_USER or not settings.GMAIL_APP_PASSWORD:
            logger.warning(
                "⚠️ Gmail credentials not configured - " "payment email monitoring disabled"
            )
            return

        # Start scheduler
        start_payment_email_scheduler()
        logger.info("✅ Payment email monitoring scheduler started")

    except Exception as e:
        logger.exception(f"Failed to start payment email scheduler: {e}")


async def on_shutdown():
    """Called when FastAPI app stops"""
    try:
        stop_payment_email_scheduler()
        logger.info("✅ Payment email monitoring scheduler stopped")
    except Exception as e:
        logger.exception(f"Error stopping payment email scheduler: {e}")


# Add to FastAPI app
def setup_payment_email_scheduler(app):
    """
    Setup payment email scheduler with FastAPI app

    Usage in main.py:
        from services.payment_email_scheduler import setup_payment_email_scheduler

        setup_payment_email_scheduler(app)
    """

    @app.on_event("startup")
    async def startup_event():
        await on_startup()

    @app.on_event("shutdown")
    async def shutdown_event():
        await on_shutdown()

    logger.info("✅ Payment email scheduler configured")
