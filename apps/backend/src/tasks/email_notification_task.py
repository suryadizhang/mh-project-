"""
Email Notification Background Task - IMAP IDLE Push Notifications + Database Sync

Uses IMAP IDLE protocol for real-time email monitoring instead of polling.
Sends WhatsApp alerts instantly when new emails arrive.
**NOW SYNCS EMAILS TO POSTGRESQL DATABASE!**

Architecture:
- IMAP IDLE for customer support (cs@myhibachichef.com)
- IMAP IDLE for payment monitoring (myhibachichef@gmail.com)
- Push notifications via server EXISTS events
- **Database sync for all incoming emails** ✨
- Automatic fallback to polling if IDLE not supported

Integration:
1. Add to main.py startup event
2. Runs IMAP IDLE monitors in separate async tasks
3. Instant notifications (no 60-second delay)
4. **Emails stored in PostgreSQL for fast access**
5. Graceful shutdown on app termination

Usage in main.py:
    from tasks.email_notification_task import start_email_notification_task

    @app.on_event("startup")
    async def startup():
        # Start IMAP IDLE monitors
        asyncio.create_task(start_email_notification_task())
"""

import asyncio
import logging
from typing import Any, Dict

from services.email_idle_monitor import (
    create_customer_support_monitor,
    create_payment_monitor,
)
from services.email_notification_service import get_email_notification_service
from core.database import get_async_session

logger = logging.getLogger(__name__)


async def start_email_notification_task():
    """
    Start IMAP IDLE email notification monitors.

    This creates two IMAP IDLE monitors:
    1. Customer Support (cs@myhibachichef.com) - IONOS
    2. Payment Monitoring (myhibachichef@gmail.com) - Gmail

    Both use push notifications for instant email alerts.
    **NEW: All emails are synced to PostgreSQL database!** ✨
    """
    logger.info("🚀 Starting IMAP IDLE email notification monitors...")

    service = get_email_notification_service()

    # Log startup info
    logger.info(f"   - Notification hours: {service.notification_start_hour}:00 - {service.notification_end_hour}:00")
    logger.info(f"   - Admin phones: {len(service.admin_phones)}")
    logger.info(f"   - Enabled: {service.enabled}")
    logger.info("   - Mode: IMAP IDLE (push notifications)")
    logger.info("   - Database sync: ENABLED ✨")

    # Create callback function for new emails
    async def on_new_email(email_data: Dict[str, Any]):
        """
        Callback when new email arrives via IMAP IDLE.

        Now includes database sync for fast email access!
        """
        # Create database session for this email
        async for db in get_async_session():
            try:
                await service.handle_new_email(email_data, db=db)
            except Exception as e:
                logger.exception(f"❌ Failed to handle new email: {e}")
            finally:
                # Session automatically closed by async generator
                break

    try:
        # Create IMAP IDLE monitors
        customer_monitor = create_customer_support_monitor(
            on_new_email_callback=on_new_email
        )

        payment_monitor = create_payment_monitor(
            on_new_email_callback=on_new_email
        )

        # Start both monitors concurrently
        logger.info("📧 Starting customer support IMAP IDLE monitor...")
        logger.info("💳 Starting payment monitoring IMAP IDLE monitor...")

        await asyncio.gather(
            customer_monitor.start(),
            payment_monitor.start(),
            return_exceptions=True,
        )

    except Exception as e:
        logger.exception(f"❌ Email notification monitors crashed: {e}")
        # Restart after delay
        await asyncio.sleep(60)
        logger.info("🔄 Restarting email notification monitors...")
        await start_email_notification_task()


if __name__ == "__main__":
    # Test email notification task
    asyncio.run(start_email_notification_task())
