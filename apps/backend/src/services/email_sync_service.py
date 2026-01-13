"""
Email Sync Service - Synchronize IMAP emails to PostgreSQL database
Integrates with existing IMAP IDLE monitors for real-time sync
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import hashlib
import re

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.email_repository import EmailRepository

# Fixed: Use standard logging instead of missing core.logging_config
import logging

logger = logging.getLogger(__name__)


class EmailSyncService:
    """
    Service for syncing emails from IMAP to PostgreSQL database.

    Works with existing IMAP IDLE monitors - when a new email arrives
    via IMAP IDLE callback, this service saves it to the database.
    """

    def __init__(self, repository: EmailRepository):
        """Initialize sync service with repository"""
        self.repository = repository

    def _generate_thread_id(
        self,
        subject: str,
        from_address: str,
        to_addresses: Optional[List[str]] = None
    ) -> str:
        """
        Generate thread ID for grouping related emails.

        Strategy:
        1. Normalize subject (remove Re:, Fwd:, etc.)
        2. Hash normalized subject + participants
        3. Use hash as thread_id

        This groups emails with same subject and participants into threads.
        """
        # Normalize subject (remove Re:, Fwd:, etc.)
        normalized_subject = subject.lower().strip()
        normalized_subject = re.sub(r'^(re|fwd|fw):\s*', '', normalized_subject)
        normalized_subject = re.sub(r'\s+', ' ', normalized_subject)

        # Get unique participants
        participants = [from_address.lower()]
        if to_addresses:
            participants.extend([addr.lower() for addr in to_addresses])
        participants = sorted(set(participants))

        # Generate hash
        thread_key = f"{normalized_subject}|{','.join(participants)}"
        thread_hash = hashlib.md5(thread_key.encode()).hexdigest()[:16]

        return f"thread_{thread_hash}"

    async def sync_email_from_idle(
        self,
        email_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync email to database when received from IMAP IDLE callback.

        This is called automatically when a new email arrives via IMAP IDLE.

        Args:
            email_data: Email data from IMAP IDLE monitor:
                {
                    'message_id': str,
                    'from_address': str,
                    'from_name': str,
                    'subject': str,
                    'text_body': str,
                    'html_body': str,
                    'received_at': datetime,
                    'inbox': 'customer_support' | 'payments',
                    'to_addresses': List[str] (optional),
                    'cc_addresses': List[str] (optional),
                    'has_attachments': bool (optional),
                    'attachments': List[Dict] (optional),
                }

        Returns:
            Sync result with message and thread info
        """
        try:
            message_id = email_data.get("message_id")
            inbox = email_data.get("inbox", "customer_support")

            logger.info(f"📥 Syncing email to DB: {message_id} ({inbox})")

            # Check if message already exists
            existing_message = await self.repository.get_message_by_message_id(message_id)
            if existing_message:
                logger.debug(f"Message {message_id} already in database")
                return {
                    "success": True,
                    "action": "exists",
                    "message_id": message_id,
                }

            # Generate thread ID
            subject = email_data.get("subject", "")
            from_address = email_data.get("from_address", "")
            to_addresses = email_data.get("to_addresses")

            thread_id = self._generate_thread_id(subject, from_address, to_addresses)

            # Ensure thread exists
            thread = await self.repository.get_or_create_thread(
                thread_id=thread_id,
                inbox=inbox,
                subject=subject
            )

            # Prepare message data for database
            message_data = {
                "message_id": message_id,
                "thread_id": thread_id,
                "inbox": inbox,
                "folder": "INBOX",

                # Headers
                "subject": subject,
                "from_address": from_address,
                "from_name": email_data.get("from_name"),
                "to_addresses": to_addresses,
                "cc_addresses": email_data.get("cc_addresses"),
                "bcc_addresses": email_data.get("bcc_addresses"),
                "reply_to": email_data.get("reply_to"),

                # Content
                "text_body": email_data.get("text_body"),
                "html_body": email_data.get("html_body"),

                # Metadata
                "received_at": email_data.get("received_at", datetime.now(timezone.utc)),
                "sent_at": email_data.get("sent_at"),

                # Flags (new emails are unread by default)
                "is_read": False,
                "is_starred": False,
                "is_archived": False,
                "is_spam": False,
                "is_draft": False,
                "is_sent": False,

                # Attachments
                "has_attachments": email_data.get("has_attachments", False),
                "attachments": email_data.get("attachments"),

                # Sync metadata
                "last_synced_at": datetime.now(timezone.utc),
            }

            # Create message
            message = await self.repository.create_message(message_data)

            # Update thread counts
            await self.repository.update_thread_counts(thread_id)

            # Update thread participants
            participants = []
            if from_address:
                participants.append({
                    "email": from_address,
                    "name": email_data.get("from_name")
                })
            if to_addresses:
                for addr in to_addresses:
                    if addr not in [p["email"] for p in participants]:
                        participants.append({"email": addr, "name": None})

            await self.repository.update_thread(thread_id, {
                "participants": participants
            })

            # Record successful sync
            await self.repository.record_sync_success(
                inbox=inbox,
                messages_synced=1
            )

            logger.info(f"✅ Email synced to DB: {message_id} → thread {thread_id}")

            return {
                "success": True,
                "action": "created",
                "message_id": message_id,
                "thread_id": thread_id,
                "message_db_id": message.id,
            }

        except Exception as e:
            logger.exception(f"❌ Failed to sync email to DB: {e}")

            # Record sync error
            try:
                await self.repository.record_sync_error(
                    inbox=inbox,
                    error_message=str(e)
                )
            except Exception as err:
                logger.error(f"Failed to record sync error: {err}")

            return {
                "success": False,
                "error": str(e),
                "message_id": email_data.get("message_id"),
            }

    async def update_message_flags(
        self,
        message_id: str,
        is_read: Optional[bool] = None,
        is_starred: Optional[bool] = None,
        is_archived: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update message flags (read, starred, archived).

        Used when user marks email as read/unread, stars it, or archives it.
        """
        try:
            update_data = {}
            if is_read is not None:
                update_data["is_read"] = is_read
            if is_starred is not None:
                update_data["is_starred"] = is_starred
            if is_archived is not None:
                update_data["is_archived"] = is_archived

            message = await self.repository.update_message(message_id, update_data)

            if not message:
                return {"success": False, "error": "Message not found"}

            # Update thread counts if read status changed
            if is_read is not None and message.thread_id:
                await self.repository.update_thread_counts(message.thread_id)

            logger.info(f"✅ Updated message flags: {message_id}")

            return {
                "success": True,
                "message_id": message_id,
                "updated_fields": list(update_data.keys())
            }

        except Exception as e:
            logger.exception(f"❌ Failed to update message flags: {e}")
            return {"success": False, "error": str(e)}

    async def delete_message_from_db(
        self,
        message_id: str,
        soft_delete: bool = True
    ) -> Dict[str, Any]:
        """
        Delete message from database.

        Args:
            message_id: Message ID
            soft_delete: If True, mark as deleted. If False, hard delete.
        """
        try:
            # Get message to get thread_id before deletion
            message = await self.repository.get_message_by_message_id(message_id)
            if not message:
                return {"success": False, "error": "Message not found"}

            thread_id = message.thread_id

            # Delete message
            deleted = await self.repository.delete_message(message_id, soft_delete)

            if not deleted:
                return {"success": False, "error": "Delete failed"}

            # Update thread counts
            if thread_id:
                await self.repository.update_thread_counts(thread_id)

            logger.info(f"✅ Deleted message from DB: {message_id} (soft={soft_delete})")

            return {
                "success": True,
                "message_id": message_id,
                "soft_delete": soft_delete
            }

        except Exception as e:
            logger.exception(f"❌ Failed to delete message: {e}")
            return {"success": False, "error": str(e)}

    async def bulk_update_flags(
        self,
        message_ids: List[str],
        is_read: Optional[bool] = None,
        is_starred: Optional[bool] = None,
        is_archived: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Bulk update flags for multiple messages.

        Useful for "mark all as read", "archive all", etc.
        """
        try:
            update_data = {}
            if is_read is not None:
                update_data["is_read"] = is_read
            if is_starred is not None:
                update_data["is_starred"] = is_starred
            if is_archived is not None:
                update_data["is_archived"] = is_archived

            count = await self.repository.bulk_update_messages(
                message_ids=message_ids,
                update_data=update_data
            )

            logger.info(f"✅ Bulk updated {count} messages")

            return {
                "success": True,
                "updated_count": count,
                "updated_fields": list(update_data.keys())
            }

        except Exception as e:
            logger.exception(f"❌ Failed to bulk update: {e}")
            return {"success": False, "error": str(e)}


async def get_email_sync_service(session: AsyncSession) -> EmailSyncService:
    """Dependency injection for email sync service"""
    repository = EmailRepository(session)
    return EmailSyncService(repository)
