"""
Email Repository - Database operations for email storage
Handles CRUD operations for EmailMessage, EmailThread, and EmailSyncStatus models
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, desc, func, update, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging

# MIGRATED: from models.email → db.models.email
from db.models.email import EmailMessage, EmailThread, EmailSyncStatus

logger = logging.getLogger(__name__)


class EmailRepository:
    """Repository for email database operations"""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session"""
        self.session = session

    # ========================================================================
    # EmailMessage Operations
    # ========================================================================

    async def get_message_by_message_id(self, message_id: str) -> Optional[EmailMessage]:
        """Get email message by Message-ID header"""
        result = await self.session.execute(
            select(EmailMessage).where(
                and_(EmailMessage.message_id == message_id, EmailMessage.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()

    async def get_messages_by_inbox(
        self,
        inbox: str,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
        starred_only: bool = False,
        archived: bool = False,
    ) -> List[EmailMessage]:
        """Get messages for specific inbox with filters"""
        query = select(EmailMessage).where(
            and_(
                EmailMessage.inbox == inbox,
                EmailMessage.is_deleted == False,
                EmailMessage.is_archived == archived,
            )
        )

        if unread_only:
            query = query.where(EmailMessage.is_read == False)

        if starred_only:
            query = query.where(EmailMessage.is_starred == True)

        query = query.order_by(desc(EmailMessage.received_at))
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_messages_by_thread(self, thread_id: str) -> List[EmailMessage]:
        """Get all messages in a thread"""
        result = await self.session.execute(
            select(EmailMessage)
            .where(and_(EmailMessage.thread_id == thread_id, EmailMessage.is_deleted == False))
            .order_by(EmailMessage.received_at)
        )
        return list(result.scalars().all())

    async def create_message(self, message_data: Dict[str, Any]) -> EmailMessage:
        """Create new email message"""
        # Check if message already exists
        existing = await self.get_message_by_message_id(message_data.get("message_id"))
        if existing:
            logger.debug(f"Message {message_data.get('message_id')} already exists")
            return existing

        message = EmailMessage(**message_data)
        self.session.add(message)
        await self.session.commit()
        await self.session.refresh(message)

        logger.info(f"✅ Created message: {message.message_id}")
        return message

    async def update_message(
        self, message_id: str, update_data: Dict[str, Any]
    ) -> Optional[EmailMessage]:
        """Update email message"""
        message = await self.get_message_by_message_id(message_id)
        if not message:
            return None

        for key, value in update_data.items():
            if hasattr(message, key):
                setattr(message, key, value)

        message.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(message)

        return message

    async def delete_message(self, message_id: str, soft_delete: bool = True) -> bool:
        """Delete email message (soft or hard delete)"""
        message = await self.get_message_by_message_id(message_id)
        if not message:
            return False

        if soft_delete:
            message.is_deleted = True
            message.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
        else:
            await self.session.delete(message)
            await self.session.commit()

        return True

    async def bulk_update_messages(
        self, message_ids: List[str], update_data: Dict[str, Any]
    ) -> int:
        """Bulk update multiple messages"""
        result = await self.session.execute(
            update(EmailMessage)
            .where(EmailMessage.message_id.in_(message_ids))
            .values(**update_data, updated_at=datetime.now(timezone.utc))
        )
        await self.session.commit()
        return result.rowcount

    # ========================================================================
    # EmailThread Operations
    # ========================================================================

    async def get_thread_by_thread_id(self, thread_id: str) -> Optional[EmailThread]:
        """Get email thread by thread_id"""
        result = await self.session.execute(
            select(EmailThread)
            .where(and_(EmailThread.thread_id == thread_id, EmailThread.is_deleted == False))
            .options(selectinload(EmailThread.messages))
        )
        return result.scalar_one_or_none()

    async def get_threads_by_inbox(
        self,
        inbox: str,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
        starred_only: bool = False,
        archived: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[EmailThread]:
        """Get threads for specific inbox with filters"""
        # Use filters dict if provided (newer calling pattern)
        if filters:
            unread_only = filters.get("unread_only", unread_only)
            starred_only = filters.get("starred_only", starred_only)
            archived = filters.get("archived", archived)
            search_query = filters.get("search")
            label_filter = filters.get("label")
        else:
            search_query = None
            label_filter = None

        query = select(EmailThread).where(
            and_(
                EmailThread.inbox == inbox,
                EmailThread.is_deleted == False,
                EmailThread.is_archived == archived,
            )
        )

        if unread_only:
            query = query.where(EmailThread.unread_count > 0)

        if starred_only:
            query = query.where(EmailThread.is_starred == True)

        # Filter by label (threads with messages containing this label)
        if label_filter:
            query = query.where(EmailThread.labels.contains([label_filter]))

        # Search filter (subject, participants)
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.where(
                or_(
                    EmailThread.subject.ilike(search_pattern),
                    EmailThread.participants.cast(String).ilike(search_pattern),
                )
            )

        query = query.order_by(desc(EmailThread.last_message_at))
        query = query.offset(skip).limit(limit)
        query = query.options(selectinload(EmailThread.messages))

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create_thread(self, thread_data: Dict[str, Any]) -> EmailThread:
        """Create new email thread"""
        # Check if thread already exists
        existing = await self.get_thread_by_thread_id(thread_data.get("thread_id"))
        if existing:
            logger.debug(f"Thread {thread_data.get('thread_id')} already exists")
            return existing

        thread = EmailThread(**thread_data)
        self.session.add(thread)
        await self.session.commit()
        await self.session.refresh(thread)

        logger.info(f"✅ Created thread: {thread.thread_id}")
        return thread

    async def update_thread(
        self, thread_id: str, update_data: Dict[str, Any]
    ) -> Optional[EmailThread]:
        """Update email thread"""
        thread = await self.get_thread_by_thread_id(thread_id)
        if not thread:
            return None

        for key, value in update_data.items():
            if hasattr(thread, key):
                setattr(thread, key, value)

        thread.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(thread)

        return thread

    async def update_thread_counts(self, thread_id: str) -> Optional[EmailThread]:
        """Recalculate and update thread counts"""
        # Get all messages in thread
        messages = await self.get_messages_by_thread(thread_id)
        if not messages:
            return None

        # Calculate counts
        message_count = len(messages)
        unread_count = sum(1 for m in messages if not m.is_read)
        has_attachments = any(m.has_attachments for m in messages)

        # Get first and last message times
        first_message_at = min(m.received_at for m in messages)
        last_message_at = max(m.received_at for m in messages)

        # All read?
        is_read = unread_count == 0

        # Update thread
        return await self.update_thread(
            thread_id,
            {
                "message_count": message_count,
                "unread_count": unread_count,
                "has_attachments": has_attachments,
                "first_message_at": first_message_at,
                "last_message_at": last_message_at,
                "is_read": is_read,
            },
        )

    async def get_or_create_thread(
        self, thread_id: str, inbox: str, subject: Optional[str] = None
    ) -> EmailThread:
        """Get existing thread or create new one"""
        thread = await self.get_thread_by_thread_id(thread_id)
        if thread:
            return thread

        # Create new thread
        thread_data = {
            "thread_id": thread_id,
            "inbox": inbox,
            "subject": subject,
            "message_count": 0,
            "unread_count": 0,
        }
        return await self.create_thread(thread_data)

    # ========================================================================
    # EmailSyncStatus Operations
    # ========================================================================

    async def get_sync_status(self, inbox: str) -> Optional[EmailSyncStatus]:
        """Get sync status for inbox"""
        result = await self.session.execute(
            select(EmailSyncStatus).where(
                and_(EmailSyncStatus.inbox == inbox, EmailSyncStatus.is_deleted == False)
            )
        )
        return result.scalar_one_or_none()

    async def update_sync_status(
        self, inbox: str, update_data: Dict[str, Any]
    ) -> Optional[EmailSyncStatus]:
        """Update sync status"""
        status = await self.get_sync_status(inbox)
        if not status:
            # Create if doesn't exist
            status = EmailSyncStatus(inbox=inbox, **update_data)
            self.session.add(status)
        else:
            for key, value in update_data.items():
                if hasattr(status, key):
                    setattr(status, key, value)

        status.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(status)

        return status

    async def record_sync_success(
        self, inbox: str, messages_synced: int, last_uid: Optional[int] = None
    ) -> EmailSyncStatus:
        """Record successful sync"""
        status = await self.get_sync_status(inbox)
        if not status:
            status = EmailSyncStatus(inbox=inbox)
            self.session.add(status)

        status.last_sync_at = datetime.now(timezone.utc)
        if last_uid:
            status.last_sync_uid = last_uid
        status.total_messages_synced += messages_synced
        status.is_syncing = False
        status.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(status)

        return status

    async def record_sync_error(self, inbox: str, error_message: str) -> EmailSyncStatus:
        """Record sync error"""
        status = await self.get_sync_status(inbox)
        if not status:
            status = EmailSyncStatus(inbox=inbox)
            self.session.add(status)

        status.sync_errors += 1
        status.last_error = error_message
        status.last_error_at = datetime.now(timezone.utc)
        status.is_syncing = False
        status.updated_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(status)

        return status

    # ========================================================================
    # Statistics and Analytics
    # ========================================================================

    async def get_email_stats(self, inbox: str) -> Dict[str, Any]:
        """Get email statistics for inbox"""
        # Total count
        total_result = await self.session.execute(
            select(func.count(EmailMessage.id)).where(
                and_(
                    EmailMessage.inbox == inbox,
                    EmailMessage.is_deleted == False,
                    EmailMessage.is_archived == False,
                )
            )
        )
        total_count = total_result.scalar() or 0

        # Unread count
        unread_result = await self.session.execute(
            select(func.count(EmailMessage.id)).where(
                and_(
                    EmailMessage.inbox == inbox,
                    EmailMessage.is_deleted == False,
                    EmailMessage.is_archived == False,
                    EmailMessage.is_read == False,
                )
            )
        )
        unread_count = unread_result.scalar() or 0

        # Starred count
        starred_result = await self.session.execute(
            select(func.count(EmailMessage.id)).where(
                and_(
                    EmailMessage.inbox == inbox,
                    EmailMessage.is_deleted == False,
                    EmailMessage.is_starred == True,
                )
            )
        )
        starred_count = starred_result.scalar() or 0

        # Archived count
        archived_result = await self.session.execute(
            select(func.count(EmailMessage.id)).where(
                and_(
                    EmailMessage.inbox == inbox,
                    EmailMessage.is_deleted == False,
                    EmailMessage.is_archived == True,
                )
            )
        )
        archived_count = archived_result.scalar() or 0

        # Today's count
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_result = await self.session.execute(
            select(func.count(EmailMessage.id)).where(
                and_(
                    EmailMessage.inbox == inbox,
                    EmailMessage.is_deleted == False,
                    EmailMessage.received_at >= today_start,
                )
            )
        )
        today_count = today_result.scalar() or 0

        # Week's count
        week_start = today_start - timedelta(days=7)
        week_result = await self.session.execute(
            select(func.count(EmailMessage.id)).where(
                and_(
                    EmailMessage.inbox == inbox,
                    EmailMessage.is_deleted == False,
                    EmailMessage.received_at >= week_start,
                )
            )
        )
        week_count = week_result.scalar() or 0

        # Thread counts (using email_threads table)
        total_threads_result = await self.session.execute(
            select(func.count(EmailThread.id)).where(
                and_(
                    EmailThread.inbox == inbox,
                    EmailThread.is_deleted == False,
                    EmailThread.is_archived == False,
                )
            )
        )
        total_threads = total_threads_result.scalar() or 0

        archived_threads_result = await self.session.execute(
            select(func.count(EmailThread.id)).where(
                and_(
                    EmailThread.inbox == inbox,
                    EmailThread.is_deleted == False,
                    EmailThread.is_archived == True,
                )
            )
        )
        archived_threads = archived_threads_result.scalar() or 0

        # Return keys matching what admin_emails.py expects
        return {
            "inbox": inbox,
            # Message-level stats (for /stats endpoint)
            "total_messages": total_count,
            "unread_messages": unread_count,
            "starred_messages": starred_count,
            "archived_messages": archived_count,
            "today_messages": today_count,
            "week_messages": week_count,
            # Thread-level stats (for /customer-support endpoint)
            "total_threads": total_threads,
            "archived_threads": archived_threads,
            # Backward compatibility aliases
            "total_emails": total_count,
            "unread_emails": unread_count,
            "starred_emails": starred_count,
            "archived_emails": archived_count,
            "today_count": today_count,
        }

    # ========================================================================
    # Label Operations
    # ========================================================================

    async def add_label_to_message(
        self, message_id: str, label_slug: str
    ) -> Optional[EmailMessage]:
        """
        Add a label to an email message (idempotent - won't duplicate)

        Args:
            message_id: Email message ID
            label_slug: Label slug to add

        Returns:
            Updated EmailMessage or None if not found
        """
        message = await self.get_message_by_message_id(message_id)
        if not message:
            logger.warning(f"Message {message_id} not found for label addition")
            return None

        # Get current labels (handle None case)
        current_labels = message.labels or []

        # Add label if not already present (idempotent)
        if label_slug not in current_labels:
            current_labels.append(label_slug)
            message.labels = current_labels
            message.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(message)
            logger.info(f"Added label '{label_slug}' to message {message_id}")
        else:
            logger.debug(f"Label '{label_slug}' already on message {message_id}")

        return message

    async def remove_label_from_message(
        self, message_id: str, label_slug: str
    ) -> Optional[EmailMessage]:
        """
        Remove a label from an email message (idempotent - won't error if not present)

        Args:
            message_id: Email message ID
            label_slug: Label slug to remove

        Returns:
            Updated EmailMessage or None if not found
        """
        message = await self.get_message_by_message_id(message_id)
        if not message:
            logger.warning(f"Message {message_id} not found for label removal")
            return None

        # Get current labels (handle None case)
        current_labels = message.labels or []

        # Remove label if present (idempotent)
        if label_slug in current_labels:
            current_labels.remove(label_slug)
            message.labels = current_labels
            message.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            await self.session.refresh(message)
            logger.info(f"Removed label '{label_slug}' from message {message_id}")
        else:
            logger.debug(f"Label '{label_slug}' not on message {message_id}")

        return message

    async def bulk_add_label_to_messages(self, message_ids: List[str], label_slug: str) -> int:
        """
        Bulk add a label to multiple messages

        Args:
            message_ids: List of message IDs
            label_slug: Label slug to add

        Returns:
            Number of messages updated
        """
        updated_count = 0
        for message_id in message_ids:
            result = await self.add_label_to_message(message_id, label_slug)
            if result:
                updated_count += 1

        return updated_count

    async def bulk_remove_label_from_messages(self, message_ids: List[str], label_slug: str) -> int:
        """
        Bulk remove a label from multiple messages

        Args:
            message_ids: List of message IDs
            label_slug: Label slug to remove

        Returns:
            Number of messages updated
        """
        updated_count = 0
        for message_id in message_ids:
            result = await self.remove_label_from_message(message_id, label_slug)
            if result:
                updated_count += 1

        return updated_count


async def get_email_repository(session: AsyncSession) -> EmailRepository:
    """Dependency injection for email repository"""
    return EmailRepository(session)
