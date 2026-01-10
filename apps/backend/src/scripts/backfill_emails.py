"""
Email Backfill Script - One-Time Historical Sync

Syncs existing emails from IMAP to PostgreSQL database.
Should be run once after initial deployment to populate the database with historical emails.

Features:
- Syncs all existing emails from IMAP to database
- Supports both customer_support and payments inboxes
- Deduplication (skips emails already in database)
- Progress tracking and error handling
- Configurable batch size and limit
- Dry-run mode for testing

Usage:
    # Sync customer support inbox (default: all emails)
    python -m src.scripts.backfill_emails --inbox customer_support

    # Sync payments inbox with limit
    python -m src.scripts.backfill_emails --inbox payments --limit 1000

    # Dry run (preview without syncing)
    python -m src.scripts.backfill_emails --inbox customer_support --dry-run

    # Sync with custom batch size
    python -m src.scripts.backfill_emails --inbox customer_support --batch-size 50

Requirements:
- Database migration 20251124_add_email_storage must be applied
- IMAP credentials configured in .env
- Backend server should be stopped during backfill (to avoid conflicts)
"""

import asyncio
import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
import email

from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path for imports
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from core.database import get_db_context
from core.config import get_settings
from services.customer_email_monitor import CustomerEmailMonitor
from services.payment_email_monitor import PaymentEmailMonitor
from services.email_sync_service import EmailSyncService
from repositories.email_repository import EmailRepository
from scripts.error_logger import EmailBackfillErrorLogger

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
settings = get_settings()


class EmailBackfillService:
    """Service to backfill emails from IMAP to database"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = EmailRepository(db)
        self.sync_service = EmailSyncService(self.repository)
        self.error_logger = EmailBackfillErrorLogger(db)  # Enterprise error logging

        # Statistics
        self.stats = {
            "total_fetched": 0,
            "total_synced": 0,
            "total_skipped": 0,
            "total_errors": 0,
            "total_retries": 0,
            "start_time": datetime.now(timezone.utc),
        }

        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    async def backfill_inbox(
        self, inbox: str, limit: Optional[int] = None, batch_size: int = 100, dry_run: bool = False
    ) -> Dict:
        """
        Backfill emails from IMAP to database.

        Args:
            inbox: 'customer_support' or 'payments'
            limit: Maximum number of emails to sync (None = all)
            batch_size: Number of emails to process per batch
            dry_run: If True, only preview without syncing

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info(f"🚀 Starting email backfill for inbox: {inbox}")
        logger.info(f"   Limit: {limit or 'ALL'}")
        logger.info(f"   Batch size: {batch_size}")
        logger.info(f"   Dry run: {dry_run}")
        logger.info("=" * 80)

        # Get IMAP monitor for inbox
        monitor = None
        try:
            monitor = self._get_imap_monitor(inbox)
            if not monitor:
                error = ValueError(f"Failed to get IMAP monitor for inbox: {inbox}")
                await self.error_logger.log_critical_failure(
                    operation="get_imap_monitor",
                    error=error,
                )
                logger.error(f"❌ {error}")
                return self.stats
        except Exception as e:
            await self.error_logger.log_critical_failure(
                operation="get_imap_monitor",
                error=e,
            )
            logger.exception(f"❌ Failed to initialize IMAP monitor: {e}")
            return self.stats

        # Connect to IMAP with retry logic
        logger.info("📡 Connecting to IMAP server...")
        connected = False
        for attempt in range(self.max_retries):
            try:
                if monitor.connect():
                    connected = True
                    logger.info("✅ Connected to IMAP server")
                    break
                else:
                    raise ConnectionError("IMAP connection returned False")
            except Exception as e:
                self.stats["total_retries"] += 1
                await self.error_logger.log_imap_connection_error(
                    inbox=inbox,
                    error=e,
                    retry_attempt=attempt + 1,
                )
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"⚠️  IMAP connection attempt {attempt + 1}/{self.max_retries} failed. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    await self.error_logger.log_critical_failure(
                        operation="imap_connection",
                        error=e,
                        recovery_attempted=True,
                    )
                    logger.error(f"❌ Failed to connect to IMAP after {self.max_retries} attempts")
                    return self.stats

        if not connected:
            error = ConnectionError("IMAP connection failed after all retries")
            await self.error_logger.log_critical_failure(
                operation="imap_connection",
                error=error,
                recovery_attempted=True,
            )
            return self.stats

        try:
            # Fetch all email IDs from IMAP
            email_ids = self._fetch_all_email_ids(monitor, limit)
            self.stats["total_fetched"] = len(email_ids)

            logger.info(f"📬 Found {len(email_ids)} total emails in IMAP")

            if dry_run:
                logger.info("🔍 DRY RUN MODE - No emails will be synced")
                logger.info(f"   Would process: {len(email_ids)} emails")
                return self.stats

            # Process in batches
            for i in range(0, len(email_ids), batch_size):
                batch_ids = email_ids[i : i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(email_ids) + batch_size - 1) // batch_size

                logger.info("")
                logger.info(
                    f"📦 Processing batch {batch_num}/{total_batches} ({len(batch_ids)} emails)"
                )

                # Process batch with error tracking
                try:
                    await self._process_batch(monitor, batch_ids, inbox, batch_num)
                except Exception as batch_error:
                    await self.error_logger.log_batch_error(
                        batch_number=batch_num,
                        batch_size=len(batch_ids),
                        error=batch_error,
                        emails_processed=self.stats["total_synced"],
                    )
                    logger.error(f"❌ Batch {batch_num} failed: {batch_error}")

                    # Check if we should abort operation
                    if self.error_logger.should_abort_operation():
                        logger.critical("🛑 ABORTING: Too many errors detected")
                        break

                    # Continue with next batch (graceful degradation)
                    logger.info("⏭️  Continuing with next batch...")
                    continue

            # Log final statistics
            self._log_final_stats()

        except Exception as e:
            await self.error_logger.log_critical_failure(
                operation="backfill_inbox",
                error=e,
            )
            logger.exception(f"❌ Backfill failed: {e}")
            self.stats["total_errors"] += 1

        finally:
            # Disconnect from IMAP
            monitor.disconnect()
            logger.info("🔌 Disconnected from IMAP server")

        return self.stats

    def _get_imap_monitor(self, inbox: str):
        """Get IMAP monitor for inbox"""
        if inbox == "customer_support":
            return CustomerEmailMonitor(
                email_address="cs@myhibachichef.com",
                password=settings.SMTP_PASSWORD,
                imap_server="imap.ionos.com",
                imap_port=993,
            )
        elif inbox == "payments":
            # Get Gmail credentials from settings (GSM)
            gmail_user = getattr(settings, "GMAIL_USER", "myhibachichef@gmail.com")
            gmail_password = getattr(settings, "GMAIL_APP_PASSWORD", "")

            if not gmail_password:
                logger.error("❌ GMAIL_APP_PASSWORD not set in settings")
                return None

            return PaymentEmailMonitor(email_address=gmail_user, app_password=gmail_password)
        else:
            logger.error(f"❌ Unknown inbox: {inbox}")
            return None

    def _fetch_all_email_ids(self, monitor, limit: Optional[int] = None) -> List[bytes]:
        """Fetch all email IDs from IMAP inbox"""
        try:
            # Select inbox
            monitor.imap_connection.select("INBOX")

            # Search for ALL emails (not just unread)
            _, message_numbers = monitor.imap_connection.search(None, "ALL")
            email_ids = message_numbers[0].split()

            # Apply limit if specified
            if limit and len(email_ids) > limit:
                email_ids = email_ids[-limit:]  # Get most recent emails

            return email_ids

        except Exception as e:
            logger.exception(f"❌ Failed to fetch email IDs: {e}")
            return []

    async def _process_batch(self, monitor, email_ids: List[bytes], inbox: str, batch_num: int = 1):
        """
        Process a batch of emails with comprehensive error handling.

        Args:
            monitor: IMAP monitor instance
            email_ids: List of email IDs to process
            inbox: Inbox name
            batch_num: Batch number (for error logging)
        """
        batch_success = 0
        batch_errors = 0

        for idx, email_id in enumerate(email_ids, 1):
            try:
                # Fetch email from IMAP with retry logic
                email_data = None
                for attempt in range(self.max_retries):
                    try:
                        email_data = self._fetch_email_data(monitor, email_id, inbox)
                        if email_data:
                            break
                    except Exception as fetch_error:
                        self.stats["total_retries"] += 1
                        if attempt < self.max_retries - 1:
                            logger.warning(
                                f"   ⚠️  [{idx}/{len(email_ids)}] Fetch attempt {attempt + 1} failed, retrying..."
                            )
                            time.sleep(self.retry_delay)
                        else:
                            await self.error_logger.log_error(
                                error=fetch_error,
                                context={
                                    "operation": "fetch_email_data",
                                    "batch": batch_num,
                                    "email_index": idx,
                                },
                                severity="ERROR",
                                email_id=str(email_id),
                                inbox=inbox,
                            )
                            logger.error(
                                f"   ❌ [{idx}/{len(email_ids)}] Failed to fetch email {email_id} after {self.max_retries} attempts"
                            )

                if not email_data:
                    self.stats["total_errors"] += 1
                    batch_errors += 1
                    continue

                # Check if already exists in database
                existing = await self.repository.get_message_by_message_id(email_data["message_id"])

                if existing:
                    await self.error_logger.log_duplicate_email(
                        email_id=str(email_id),
                        message_id=email_data["message_id"],
                        inbox=inbox,
                    )
                    logger.debug(
                        f"   ⏭️  [{idx}/{len(email_ids)}] Skipped (already exists): {email_data['subject'][:50]}"
                    )
                    self.stats["total_skipped"] += 1
                    continue

                # Sync to database with retry logic
                result = None
                for attempt in range(self.max_retries):
                    try:
                        result = await self.sync_service.sync_email_from_idle(email_data)
                        if result.get("success"):
                            logger.info(
                                f"   ✅ [{idx}/{len(email_ids)}] Synced ({result['action']}): "
                                f"{email_data['subject'][:50]}"
                            )
                            self.stats["total_synced"] += 1
                            batch_success += 1
                            break
                        else:
                            raise Exception(result.get("error", "Unknown sync error"))
                    except Exception as sync_error:
                        self.stats["total_retries"] += 1
                        if attempt < self.max_retries - 1:
                            logger.warning(
                                f"   ⚠️  [{idx}/{len(email_ids)}] Sync attempt {attempt + 1} failed, retrying..."
                            )
                            time.sleep(self.retry_delay)
                        else:
                            await self.error_logger.log_database_error(
                                operation="sync_email",
                                error=sync_error,
                                email_id=str(email_id),
                            )
                            logger.error(f"   ❌ [{idx}/{len(email_ids)}] Failed: {sync_error}")
                            self.stats["total_errors"] += 1
                            batch_errors += 1

            except Exception as e:
                await self.error_logger.log_error(
                    error=e,
                    context={
                        "operation": "process_email",
                        "batch": batch_num,
                        "email_index": idx,
                    },
                    severity="ERROR",
                    email_id=str(email_id),
                    inbox=inbox,
                )
                logger.exception(
                    f"   ❌ [{idx}/{len(email_ids)}] Error processing email {email_id}: {e}"
                )
                self.stats["total_errors"] += 1
                batch_errors += 1

        # Log batch summary
        logger.info(f"📊 Batch {batch_num} complete: {batch_success} synced, {batch_errors} errors")

    def _fetch_email_data(self, monitor, email_id: bytes, inbox: str) -> Optional[Dict]:
        """Fetch email data from IMAP"""
        try:
            # Fetch email
            _, msg_data = monitor.imap_connection.fetch(email_id, "(RFC822)")
            email_body = msg_data[0][1]
            msg = email.message_from_bytes(email_body)

            # Extract fields
            from_header = monitor._decode_header_value(msg.get("From", ""))
            subject = monitor._decode_header_value(msg.get("Subject", ""))
            message_id = msg.get("Message-ID", "")
            date_str = msg.get("Date", "")

            # Parse sender
            from_address = from_header
            from_name = None
            if "<" in from_header and ">" in from_header:
                from_name = from_header.split("<")[0].strip().strip('"')
                from_address = from_header.split("<")[1].split(">")[0].strip()

            # Parse date
            try:
                from email.utils import parsedate_to_datetime

                received_at = parsedate_to_datetime(date_str)
                if received_at.tzinfo is None:
                    received_at = received_at.replace(tzinfo=timezone.utc)
            except Exception:
                received_at = datetime.now(timezone.utc)

            # Extract body
            text_body, html_body = monitor._extract_email_body(msg)

            # Parse to/cc addresses
            to_addresses = []
            to_header = msg.get("To", "")
            if to_header:
                to_addresses = [addr.strip() for addr in to_header.split(",")]

            cc_addresses = []
            cc_header = msg.get("Cc", "")
            if cc_header:
                cc_addresses = [addr.strip() for addr in cc_header.split(",")]

            # Check attachments
            has_attachments = False
            attachments = []
            for part in msg.walk():
                if part.get_content_maintype() == "multipart":
                    continue
                if part.get("Content-Disposition") is None:
                    continue

                has_attachments = True
                filename = part.get_filename()
                if filename:
                    attachments.append(
                        {
                            "filename": filename,
                            "content_type": part.get_content_type(),
                            "size_bytes": len(part.get_payload(decode=True) or b""),
                        }
                    )

            return {
                "message_id": message_id,
                "from_address": from_address,
                "from_name": from_name,
                "to_addresses": to_addresses,
                "cc_addresses": cc_addresses,
                "subject": subject,
                "text_body": text_body,
                "html_body": html_body,
                "received_at": received_at,
                "inbox": inbox,
                "has_attachments": has_attachments,
                "attachments": attachments,
            }

        except Exception as e:
            logger.exception(f"❌ Failed to parse email: {e}")
            return None

    def _log_final_stats(self):
        """Log final backfill statistics with error summary"""
        elapsed = (datetime.now(timezone.utc) - self.stats["start_time"]).total_seconds()

        # Get error summary from error logger
        error_summary = self.error_logger.get_error_summary()

        logger.info("")
        logger.info("=" * 80)
        logger.info("📊 BACKFILL COMPLETE")
        logger.info("=" * 80)
        logger.info(f"   Total fetched: {self.stats['total_fetched']}")
        logger.info(f"   Total synced:  {self.stats['total_synced']} ✅")
        logger.info(f"   Total skipped: {self.stats['total_skipped']} ⏭️")
        logger.info(f"   Total errors:  {self.stats['total_errors']} ❌")
        logger.info(f"   Total retries: {self.stats['total_retries']} 🔄")
        logger.info(f"   Elapsed time:  {elapsed:.1f}s")

        if self.stats["total_fetched"] > 0:
            success_rate = (self.stats["total_synced"] / self.stats["total_fetched"]) * 100
            logger.info(f"   Success rate:  {success_rate:.1f}%")

        # Log error breakdown
        if error_summary["total"] > 0:
            logger.info("")
            logger.info("📝 ERROR SUMMARY (logged to database):")
            logger.info(f"   Critical: {error_summary['critical']} 🔴")
            logger.info(f"   Errors:   {error_summary['errors']} 🟠")
            logger.info(f"   Warnings: {error_summary['warnings']} 🟡")
            logger.info(f"   Operation ID: {error_summary['operation_id']}")
            logger.info("   View in admin dashboard under Error Logs")

        logger.info("=" * 80)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Backfill emails from IMAP to PostgreSQL database")
    parser.add_argument(
        "--inbox",
        type=str,
        choices=["customer_support", "payments"],
        required=True,
        help="Inbox to backfill (customer_support or payments)",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Maximum number of emails to sync (default: all)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of emails to process per batch (default: 100)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without syncing to database"
    )

    args = parser.parse_args()

    # Get database session
    async with get_db_context() as db:
        try:
            # Create backfill service
            backfill_service = EmailBackfillService(db)

            # Run backfill
            stats = await backfill_service.backfill_inbox(
                inbox=args.inbox, limit=args.limit, batch_size=args.batch_size, dry_run=args.dry_run
            )

            # Exit with appropriate code
            if stats["total_errors"] > 0:
                logger.warning(f"⚠️  Backfill completed with {stats['total_errors']} errors")
                sys.exit(1)
            else:
                logger.info("✅ Backfill completed successfully")
                sys.exit(0)

        except Exception as e:
            logger.exception(f"❌ Fatal error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
