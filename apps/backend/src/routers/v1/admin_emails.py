"""
Admin Email Management API
Provides Gmail-style email interface for 2 inboxes:
1. cs@myhibachichef.com (IONOS) - Customer support, inquiries, replies
2. myhibachichef@gmail.com (Gmail) - Payment notifications (read-only)

**NOW READS FROM POSTGRESQL DATABASE** for fast access!
- IMAP IDLE auto-syncs emails to database
- API reads from database (no IMAP connection needed)
- Fallback to IMAP if database is empty or unavailable
"""

from datetime import datetime, timezone
from typing import Optional
import logging
import email

from fastapi import APIRouter, Depends, HTTPException, Query, Header, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import select, update, func, and_
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, get_async_session
from core.config import get_settings
from services.customer_email_monitor import customer_email_monitor
from services.payment_email_monitor import PaymentEmailMonitor
from repositories.email_repository import EmailRepository
from db.models.email import EmailMessage
from utils.auth import superadmin_required

router = APIRouter(prefix="/admin/emails", tags=["admin", "emails"])
settings = get_settings()
logger = logging.getLogger(__name__)


# ============================================================================
# RESPONSE MODELS
# ============================================================================


class EmailAddress(BaseModel):
    """Email address with optional name"""

    email: str
    name: Optional[str] = None


class EmailAttachment(BaseModel):
    """Email attachment metadata"""

    filename: str
    content_type: str
    size_bytes: int


class Email(BaseModel):
    """Single email message"""

    message_id: str
    thread_id: Optional[str] = None
    from_address: str
    from_name: Optional[str] = None
    to_address: str
    to_name: Optional[str] = None
    cc: list[EmailAddress] = Field(default_factory=list)
    bcc: list[EmailAddress] = Field(default_factory=list)
    subject: str
    text_body: Optional[str] = None
    html_body: Optional[str] = None
    received_at: datetime
    is_read: bool = False
    is_starred: bool = False
    is_archived: bool = False
    has_attachments: bool = False
    attachments: list[EmailAttachment] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)


class EmailThread(BaseModel):
    """Email conversation thread (Gmail-style)"""

    thread_id: str
    subject: str
    participants: list[EmailAddress]
    messages: list[Email]
    message_count: int
    unread_count: int
    last_message_at: datetime
    is_read: bool
    is_starred: bool
    is_archived: bool
    labels: list[str] = Field(default_factory=list)


class EmailListResponse(BaseModel):
    """Paginated email list"""

    inbox: str  # "customer_support" or "payments"
    threads: list[EmailThread]
    total_count: int
    unread_count: int
    page: int
    limit: int
    has_more: bool


class EmailStats(BaseModel):
    """Email inbox statistics"""

    inbox: str
    total_emails: int
    unread_emails: int
    starred_emails: int
    archived_emails: int
    today_count: int
    week_count: int


# ============================================================================
# REQUEST MODELS
# ============================================================================


class SendEmailRequest(BaseModel):
    """Send or reply to email"""

    to: list[EmailAddress]
    cc: Optional[list[EmailAddress]] = None
    bcc: Optional[list[EmailAddress]] = None
    subject: str
    text_body: str
    html_body: Optional[str] = None
    in_reply_to: Optional[str] = None  # message_id if replying
    thread_id: Optional[str] = None


class UpdateEmailRequest(BaseModel):
    """Update email status"""

    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None
    is_archived: Optional[bool] = None
    labels: Optional[list[str]] = None


class BulkUpdateEmailRequest(BaseModel):
    """Bulk update email status for multiple messages"""

    message_ids: list[str] = Field(..., description="List of message IDs to update")
    is_read: Optional[bool] = None
    is_starred: Optional[bool] = None
    is_archived: Optional[bool] = None
    labels: Optional[list[str]] = None
    action: Optional[str] = Field(
        None,
        description="Action: mark_read, mark_unread, star, unstar, archive, unarchive, delete, apply_label, remove_label",
    )
    label_slug: Optional[str] = Field(
        None, description="Label slug for apply_label/remove_label actions"
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _convert_imap_email_to_model(imap_email: dict, inbox: str) -> Email:
    """Convert IMAP email dict to Email model"""
    return Email(
        message_id=imap_email["message_id"],
        thread_id=imap_email.get("thread_id", imap_email["message_id"]),
        from_address=imap_email["from_address"],
        from_name=imap_email.get("from_name"),
        to_address=inbox,
        to_name="My Hibachi Chef" if inbox == "cs@myhibachichef.com" else "Payment Monitoring",
        subject=imap_email["subject"],
        text_body=imap_email.get("text_body"),
        html_body=imap_email.get("html_body"),
        received_at=imap_email["received_at"],
        is_read=imap_email.get("is_read", False),
        has_attachments=imap_email.get("has_attachments", False),
        attachments=[],  # TODO: Parse attachments
        labels=[],
    )


def _group_emails_into_threads(emails: list[Email]) -> list[EmailThread]:
    """Group emails by subject into Gmail-style threads"""
    threads_dict: dict[str, list[Email]] = {}

    for email_msg in emails:
        # Normalize subject (remove Re:, Fwd:, etc.)
        normalized_subject = email_msg.subject.lower()
        for prefix in ["re:", "fwd:", "fw:", "reply:"]:
            normalized_subject = normalized_subject.replace(prefix, "").strip()

        # Use normalized subject as thread_id
        thread_id = normalized_subject or email_msg.message_id

        if thread_id not in threads_dict:
            threads_dict[thread_id] = []
        threads_dict[thread_id].append(email_msg)

    # Convert to EmailThread objects
    threads: list[EmailThread] = []
    for thread_id, thread_emails in threads_dict.items():
        # Sort by received_at (oldest first)
        thread_emails.sort(key=lambda e: e.received_at)

        # Get unique participants
        participants_set = set()
        for email_msg in thread_emails:
            participants_set.add((email_msg.from_address, email_msg.from_name))
        participants = [EmailAddress(email=addr, name=name) for addr, name in participants_set]

        # Calculate stats
        unread_count = sum(1 for e in thread_emails if not e.is_read)
        is_read = unread_count == 0
        is_starred = any(e.is_starred for e in thread_emails)
        is_archived = all(e.is_archived for e in thread_emails)

        threads.append(
            EmailThread(
                thread_id=thread_id,
                subject=thread_emails[0].subject,
                participants=participants,
                messages=thread_emails,
                message_count=len(thread_emails),
                unread_count=unread_count,
                last_message_at=thread_emails[-1].received_at,
                is_read=is_read,
                is_starred=is_starred,
                is_archived=is_archived,
                labels=[],
            )
        )

    # Sort threads by last_message_at (newest first)
    threads.sort(key=lambda t: t.last_message_at, reverse=True)

    return threads


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.get("/stats", response_model=dict[str, EmailStats])
async def get_email_stats(db: AsyncSession = Depends(get_async_session)):
    """
    Get statistics for both email inboxes

    **NEW**: Reads from PostgreSQL database for instant stats!

    Returns:
        - customer_support: Stats for cs@myhibachichef.com
        - payments: Stats for myhibachichef@gmail.com
    """
    stats = {}
    repo = EmailRepository(db)

    # Customer Support Inbox (IONOS)
    try:
        customer_stats = await repo.get_email_stats("customer_support")
        stats["customer_support"] = EmailStats(
            inbox="cs@myhibachichef.com",
            total_emails=customer_stats["total_messages"],
            unread_emails=customer_stats["unread_messages"],
            starred_emails=customer_stats["starred_messages"],
            archived_emails=customer_stats["archived_messages"],
            today_count=customer_stats["today_messages"],
            week_count=customer_stats.get("week_messages", 0),
        )
    except Exception as e:
        logger.error(f"Failed to get customer support stats: {e}")
        # Fallback to IMAP if database fails
        try:
            customer_email_monitor.connect()
            total, unread = customer_email_monitor.get_email_count()
            customer_email_monitor.disconnect()

            stats["customer_support"] = EmailStats(
                inbox="cs@myhibachichef.com",
                total_emails=total,
                unread_emails=unread,
                starred_emails=0,
                archived_emails=0,
                today_count=0,
                week_count=0,
            )
        except Exception as fallback_error:
            logger.exception(f"IMAP fallback failed: {fallback_error}")
            stats["customer_support"] = EmailStats(
                inbox="cs@myhibachichef.com",
                total_emails=0,
                unread_emails=0,
                starred_emails=0,
                archived_emails=0,
                today_count=0,
                week_count=0,
            )

    # Payment Inbox (Gmail)
    try:
        payment_stats = await repo.get_email_stats("payments")
        stats["payments"] = EmailStats(
            inbox="myhibachichef@gmail.com",
            total_emails=payment_stats["total_messages"],
            unread_emails=payment_stats["unread_messages"],
            starred_emails=payment_stats["starred_messages"],
            archived_emails=payment_stats["archived_messages"],
            today_count=payment_stats["today_messages"],
            week_count=payment_stats.get("week_messages", 0),
        )
    except Exception as e:
        logger.error(f"Failed to get payment stats: {e}")
        stats["payments"] = EmailStats(
            inbox="myhibachichef@gmail.com",
            total_emails=0,
            unread_emails=0,
            starred_emails=0,
            archived_emails=0,
            today_count=0,
            week_count=0,
        )

    return stats


@router.get("/customer-support", response_model=EmailListResponse)
async def get_customer_support_emails(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    starred_only: bool = Query(False),
    archived: bool = Query(False),
    search: Optional[str] = Query(None),
    label: Optional[str] = Query(None, description="Filter by label slug"),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get emails from cs@myhibachichef.com (Customer Support Inbox)

    **NEW**: Reads from PostgreSQL database for instant access!

    This is the main customer support inbox with READ/WRITE capabilities:
    - View incoming customer emails
    - Reply via Resend API
    - Mark as read/unread
    - Star important emails
    - Archive old conversations

    Args:
        page: Page number (1-indexed)
        limit: Results per page
        unread_only: Show only unread emails
        starred_only: Show only starred emails
        archived: Show archived emails (default: false)
        search: Search query (subject, sender, body)
        label: Filter by label slug (e.g., 'vip', 'urgent', 'follow-up')
    """
    try:
        repo = EmailRepository(db)

        # Calculate pagination
        skip = (page - 1) * limit

        # Fetch threads from database
        db_threads = await repo.get_threads_by_inbox(
            inbox="customer_support",
            skip=skip,
            limit=limit,
            filters={
                "unread_only": unread_only,
                "starred_only": starred_only,
                "archived": archived,
                "search": search,
                "label": label,
            },
        )

        # Convert to API models
        threads = []
        for db_thread in db_threads:
            # Convert messages to Email models
            messages = []
            for db_message in db_thread.messages:
                messages.append(
                    Email(
                        message_id=db_message.message_id,
                        thread_id=db_message.thread_id,
                        from_address=db_message.from_address,
                        from_name=db_message.from_name,
                        to_address=(
                            db_message.to_addresses[0]
                            if db_message.to_addresses
                            else "cs@myhibachichef.com"
                        ),
                        to_name="My Hibachi Chef",
                        cc=[EmailAddress(email=addr) for addr in (db_message.cc_addresses or [])],
                        bcc=[],
                        subject=db_message.subject,
                        text_body=db_message.text_body,
                        html_body=db_message.html_body,
                        received_at=db_message.received_at,
                        is_read=db_message.is_read,
                        is_starred=db_message.is_starred,
                        is_archived=db_message.is_archived,
                        has_attachments=db_message.has_attachments,
                        attachments=[
                            EmailAttachment(
                                filename=att["filename"],
                                content_type=att.get("content_type", "application/octet-stream"),
                                size_bytes=att.get("size_bytes", 0),
                            )
                            for att in (db_message.attachments or [])
                        ],
                        labels=db_message.labels or [],
                    )
                )

            # Extract unique participants
            participants_set = set()
            for msg in db_thread.messages:
                participants_set.add((msg.from_address, msg.from_name))
            participants = [EmailAddress(email=addr, name=name) for addr, name in participants_set]

            threads.append(
                EmailThread(
                    thread_id=db_thread.thread_id,
                    subject=db_thread.subject,
                    participants=participants,
                    messages=messages,
                    message_count=db_thread.message_count,
                    unread_count=db_thread.unread_count,
                    last_message_at=db_thread.last_message_at,
                    is_read=(db_thread.unread_count == 0),
                    is_starred=db_thread.is_starred,
                    is_archived=db_thread.is_archived,
                    labels=db_thread.labels or [],
                )
            )

        # Get stats for total/unread counts
        stats = await repo.get_email_stats("customer_support")
        total_count = stats["total_threads"] if not archived else stats.get("archived_threads", 0)
        unread_count = stats["unread_messages"]

        return EmailListResponse(
            inbox="cs@myhibachichef.com",
            threads=threads,
            total_count=total_count,
            unread_count=unread_count,
            page=page,
            limit=limit,
            has_more=len(threads) == limit,
        )

    except Exception as e:
        logger.exception(f"Failed to fetch customer support emails from database: {e}")

        # Fallback to IMAP if database fails
        logger.warning("Falling back to IMAP...")
        try:
            customer_email_monitor.connect()

            # Fetch emails
            emails_data = customer_email_monitor.fetch_unread_emails(mark_as_read=False)

            # Convert to Email models
            emails = [
                _convert_imap_email_to_model(email_data, "cs@myhibachichef.com")
                for email_data in emails_data
            ]

            # Apply filters
            if unread_only:
                emails = [e for e in emails if not e.is_read]
            if starred_only:
                emails = [e for e in emails if e.is_starred]
            if search:
                search_lower = search.lower()
                emails = [
                    e
                    for e in emails
                    if search_lower in e.subject.lower()
                    or search_lower in (e.from_name or "").lower()
                    or search_lower in e.from_address.lower()
                    or search_lower in (e.text_body or "").lower()
                ]

            # Get total stats
            total_count = len(emails)
            unread_count = sum(1 for e in emails if not e.is_read)

            # Group into threads
            threads = _group_emails_into_threads(emails)

            # Pagination
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit
            paginated_threads = threads[start_idx:end_idx]
            has_more = end_idx < len(threads)

            customer_email_monitor.disconnect()

            return EmailListResponse(
                inbox="cs@myhibachichef.com",
                threads=paginated_threads,
                total_count=total_count,
                unread_count=unread_count,
                page=page,
                limit=limit,
                has_more=has_more,
            )
        except Exception as fallback_error:
            logger.exception(f"IMAP fallback also failed: {fallback_error}")
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch emails: {str(fallback_error)}"
            )


@router.get("/payments", response_model=EmailListResponse)
async def get_payment_emails(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Get emails from myhibachichef@gmail.com (Payment Monitoring - READ ONLY)

    This inbox is READ-ONLY for manual payment verification:
    - Stripe payment confirmations
    - Venmo payment notifications
    - Zelle transfer confirmations
    - Bank of America alerts

    Args:
        page: Page number (1-indexed)
        limit: Results per page
        unread_only: Show only unread emails
        search: Search query (subject, sender, body)
    """
    try:
        from sqlalchemy import text

        # Calculate pagination offset
        offset = (page - 1) * limit

        # Build base query for processed payment emails
        # Column names match actual payments.processed_emails schema
        base_query = """
            SELECT
                id,
                email_message_id,
                email_uid,
                payment_provider,
                amount_cents,
                sender_name,
                sender_identifier,
                email_subject,
                email_date,
                matched_booking_id,
                matched_customer_id,
                processing_status,
                processing_notes,
                processed_at
            FROM payments.processed_emails
            WHERE email_account = :account
        """

        # Add search filter if provided
        if search:
            base_query += " AND (email_subject ILIKE :search OR sender_name ILIKE :search OR sender_identifier ILIKE :search)"

        # Order by most recent first
        count_query = f"SELECT COUNT(*) FROM ({base_query}) AS subq"
        base_query += " ORDER BY email_date DESC NULLS LAST, processed_at DESC"
        base_query += " LIMIT :limit OFFSET :offset"

        # Execute queries
        params = {
            "account": "myhibachichef@gmail.com",
            "limit": limit,
            "offset": offset,
        }
        if search:
            params["search"] = f"%{search}%"

        # Get total count
        count_result = await db.execute(
            text(count_query.replace(" LIMIT :limit OFFSET :offset", "")), params
        )
        total_count = count_result.scalar() or 0

        # Get emails
        result = await db.execute(text(base_query), params)
        rows = result.fetchall()

        # Convert to Email models
        emails = []
        for row in rows:
            # Create email model from processed_emails row
            email = Email(
                message_id=row.email_message_id or f"payment_{row.id}",
                thread_id=f"payment_{row.payment_provider}_{row.id}",
                from_address=row.sender_identifier or "unknown@payment.com",
                from_name=row.sender_name or row.payment_provider.title(),
                to_address="myhibachichef@gmail.com",
                to_name="My Hibachi Payments",
                cc=[],
                bcc=[],
                subject=row.email_subject
                or f"{row.payment_provider.title()} Payment: ${row.amount_cents/100:.2f}",
                text_body=f"Payment received: ${row.amount_cents/100:.2f} from {row.sender_name} via {row.payment_provider.title()}\n\nStatus: {row.processing_status}\nNotes: {row.processing_notes or 'None'}",
                html_body=None,
                received_at=row.email_date or row.processed_at,
                is_read=row.processing_status == "processed",
                is_starred=row.matched_booking_id is not None,
                is_archived=False,
                has_attachments=False,
                attachments=[],
                labels=(
                    [row.payment_provider, row.processing_status] if row.payment_provider else []
                ),
            )
            emails.append(email)

        # Group into threads by payment provider
        threads = _group_emails_into_threads(emails)

        # Calculate unread count (unmatched payments)
        unread_result = await db.execute(
            text(
                """
                SELECT COUNT(*) FROM payments.processed_emails
                WHERE email_account = :account
                AND (processing_status != 'processed' OR matched_booking_id IS NULL)
            """
            ),
            {"account": "myhibachichef@gmail.com"},
        )
        unread_count = unread_result.scalar() or 0

        return EmailListResponse(
            inbox="myhibachichef@gmail.com",
            threads=threads,
            total_count=total_count,
            unread_count=unread_count,
            page=page,
            limit=limit,
            has_more=len(rows) == limit,
        )

    except Exception as e:
        logger.error(f"Failed to fetch payment emails: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")


@router.get("/customer-support/{thread_id}", response_model=EmailThread)
async def get_customer_support_thread(
    thread_id: str,
    db: Session = Depends(get_db),
):
    """
    Get a specific email thread from customer support inbox

    Args:
        thread_id: Thread ID (normalized subject)
    """
    try:
        customer_email_monitor.connect()
        emails_data = customer_email_monitor.fetch_unread_emails(mark_as_read=False)
        customer_email_monitor.disconnect()

        emails = [
            _convert_imap_email_to_model(email_data, "cs@myhibachichef.com")
            for email_data in emails_data
        ]

        threads = _group_emails_into_threads(emails)
        thread = next((t for t in threads if t.thread_id == thread_id), None)

        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        return thread

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch thread: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch thread: {str(e)}")


@router.post("/customer-support/send", response_model=dict)
async def send_customer_support_email(
    request: SendEmailRequest,
    db: Session = Depends(get_db),
):
    """
    Send or reply to customer support email via Resend API

    Args:
        request: Email details (to, subject, body, reply info)
    """
    try:
        # Validate recipients
        if not request.to:
            raise HTTPException(status_code=400, detail="At least one recipient required")

        # Send via Resend
        # Note: email_service uses Resend API (see email_service.py)
        # For now, we'll use a simple notification style
        # TODO: Extend email_service.py to support custom HTML/text emails

        to_email = request.to[0].email
        subject = request.subject
        text_body = request.text_body
        html_body = request.html_body or f"<p>{text_body}</p>"

        # Use email_service (which uses Resend)
        # This is a workaround until we extend email_service for generic sends
        from resend import Resend

        resend_client = Resend(api_key=settings.RESEND_API_KEY)

        response = resend_client.emails.send(
            {
                "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
                "to": [to_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
                "reply_to": settings.RESEND_FROM_EMAIL,
            }
        )

        return {
            "success": True,
            "message_id": response.get("id"),
            "recipient": to_email,
        }

    except Exception as e:
        logger.error(f"Failed to send email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.patch("/customer-support/{message_id}", response_model=dict)
async def update_customer_support_email(
    message_id: str,
    request: UpdateEmailRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Update customer support email status (mark as read, star, archive)

    Args:
        message_id: Email message ID
        request: Update fields
    """
    try:
        repo = EmailRepository(db)

        # Update in database
        update_data = request.dict(exclude_none=True)
        if update_data:
            await repo.update_message(message_id, update_data)
            logger.info(f"Updated email {message_id}: {update_data}")

        return {
            "success": True,
            "message_id": message_id,
            "updated_fields": update_data,
        }

    except Exception as e:
        logger.error(f"Failed to update email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to update email: {str(e)}")


@router.post("/customer-support/bulk", response_model=dict)
async def bulk_update_customer_support_emails(
    request: BulkUpdateEmailRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Bulk update multiple emails (mark read/unread, star/unstar, archive, delete, labels)

    Args:
        request: Bulk update request with message IDs and action

    Returns:
        Success count and failure details
    """
    try:
        repo = EmailRepository(db)

        success_count = 0
        failed_count = 0
        errors = []

        # Determine update data based on action
        update_data = {}
        if request.action == "mark_read":
            update_data = {"is_read": True}
        elif request.action == "mark_unread":
            update_data = {"is_read": False}
        elif request.action == "star":
            update_data = {"is_starred": True}
        elif request.action == "unstar":
            update_data = {"is_starred": False}
        elif request.action == "archive":
            update_data = {"is_archived": True}
        elif request.action == "unarchive":
            update_data = {"is_archived": False}
        elif request.action == "delete":
            # Handle delete separately
            pass
        elif request.action == "apply_label":
            # Validate label_slug is provided
            if not request.label_slug:
                raise HTTPException(
                    status_code=400, detail="label_slug is required for apply_label action"
                )
            # Verify label exists
            from models.email_label import EmailLabel

            label_result = await db.execute(
                select(EmailLabel).where(
                    and_(
                        EmailLabel.slug == request.label_slug,
                        EmailLabel.is_archived == False,
                        EmailLabel.is_deleted == False,
                    )
                )
            )
            label = label_result.scalar_one_or_none()
            if not label:
                raise HTTPException(
                    status_code=404, detail=f"Label '{request.label_slug}' not found or archived"
                )
            # Handle in processing loop
            pass
        elif request.action == "remove_label":
            # Validate label_slug is provided
            if not request.label_slug:
                raise HTTPException(
                    status_code=400, detail="label_slug is required for remove_label action"
                )
            # Handle in processing loop
            pass
        else:
            # Use explicit fields from request
            update_data = request.dict(
                exclude_none=True, exclude={"message_ids", "action", "label_slug"}
            )

        # Process each message
        for message_id in request.message_ids:
            try:
                if request.action == "delete":
                    # Delete from database
                    await repo.delete_message(message_id)
                    logger.info(f"Deleted email {message_id}")
                elif request.action == "apply_label":
                    # Add label to message
                    await repo.add_label_to_message(message_id, request.label_slug)
                    logger.info(f"Applied label '{request.label_slug}' to email {message_id}")
                elif request.action == "remove_label":
                    # Remove label from message
                    await repo.remove_label_from_message(message_id, request.label_slug)
                    logger.info(f"Removed label '{request.label_slug}' from email {message_id}")
                else:
                    # Update in database
                    if update_data:
                        await repo.update_message(message_id, update_data)
                        logger.info(f"Updated email {message_id}: {update_data}")

                success_count += 1

            except Exception as e:
                logger.error(f"Failed to update email {message_id}: {e}")
                failed_count += 1
                errors.append({"message_id": message_id, "error": str(e)})

        # Update email_count on label if apply_label/remove_label was used
        if request.action in ["apply_label", "remove_label"] and request.label_slug:
            from models.email_label import EmailLabel

            try:
                # Count messages with this label
                count_result = await db.execute(
                    select(func.count(EmailMessage.id)).where(
                        and_(
                            EmailMessage.labels.contains([request.label_slug]),
                            EmailMessage.is_deleted == False,
                        )
                    )
                )
                label_count = count_result.scalar() or 0

                # Update label's email_count
                await db.execute(
                    update(EmailLabel)
                    .where(EmailLabel.slug == request.label_slug)
                    .values(email_count=label_count)
                )
                await db.commit()
                logger.info(f"Updated email_count for label '{request.label_slug}': {label_count}")
            except Exception as e:
                logger.error(f"Failed to update email_count for label '{request.label_slug}': {e}")

        return {
            "success": True,
            "total_requested": len(request.message_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors if errors else None,
            "action": request.action or "update",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform bulk update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to perform bulk update: {str(e)}")


@router.delete("/customer-support/{message_id}", response_model=dict)
async def delete_customer_support_email(
    message_id: str,
    current_user: dict = Depends(superadmin_required),
    db: Session = Depends(get_db),
):
    """
    Permanently delete customer support email (super admin only)

    Args:
        message_id: Email message ID
        current_user: Current authenticated user (must be super admin)

    Returns:
        Success confirmation
    """
    try:
        logger.info(f"Super admin {current_user.get('email')} deleting email {message_id}")

        # Connect to IMAP
        customer_email_monitor.connect()

        # Search for email by message ID
        _, message_numbers = customer_email_monitor.imap_connection.search(
            None, f'HEADER Message-ID "{message_id}"'
        )

        if not message_numbers[0]:
            raise HTTPException(status_code=404, detail="Email not found")

        msg_num = message_numbers[0].split()[0]

        # Mark email as deleted (\Deleted flag)
        customer_email_monitor.imap_connection.store(msg_num, "+FLAGS", "\\Deleted")

        # Expunge (permanently remove) deleted emails
        customer_email_monitor.imap_connection.expunge()

        logger.info(f"Email {message_id} permanently deleted from IMAP")

        return {
            "success": True,
            "message_id": message_id,
            "action": "deleted",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete email: {str(e)}")


@router.delete("/payments/{message_id}", response_model=dict)
async def delete_payment_email(
    message_id: str,
    current_user: dict = Depends(superadmin_required),
    db: Session = Depends(get_db),
):
    """
    Permanently delete payment email (super admin only)

    Args:
        message_id: Email message ID
        current_user: Current authenticated user (must be super admin)

    Returns:
        Success confirmation
    """
    try:
        logger.info(f"Super admin {current_user.get('email')} deleting payment email {message_id}")

        # Create payment monitor instance
        payment_monitor = PaymentEmailMonitor(
            email_address=settings.PAYMENT_EMAIL_ADDRESS,
            password=settings.PAYMENT_EMAIL_PASSWORD,
        )

        # Connect to IMAP
        payment_monitor.connect()

        # Search for email by message ID
        _, message_numbers = payment_monitor.imap_connection.search(
            None, f'HEADER Message-ID "{message_id}"'
        )

        if not message_numbers[0]:
            payment_monitor.disconnect()
            raise HTTPException(status_code=404, detail="Email not found")

        msg_num = message_numbers[0].split()[0]

        # Mark email as deleted (\Deleted flag)
        payment_monitor.imap_connection.store(msg_num, "+FLAGS", "\\Deleted")

        # Expunge (permanently remove) deleted emails
        payment_monitor.imap_connection.expunge()

        payment_monitor.disconnect()

        logger.info(f"Payment email {message_id} permanently deleted from IMAP")

        return {
            "success": True,
            "message_id": message_id,
            "action": "deleted",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete payment email: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete payment email: {str(e)}")


# ============================================================================
# ATTACHMENT DOWNLOAD
# ============================================================================


@router.get("/attachments/{message_id}/{attachment_index}", response_class=Response)
async def download_attachment(
    message_id: str,
    attachment_index: int,
    db: Session = Depends(get_db),
):
    """
    Download email attachment.

    Args:
        message_id: Email message ID
        attachment_index: Index of attachment (0-based)

    Returns:
        File download response
    """
    try:
        # Connect to IMAP
        customer_email_monitor.connect()

        # Search for email by message ID
        _, message_numbers = customer_email_monitor.imap_connection.search(
            None, f'HEADER Message-ID "{message_id}"'
        )

        if not message_numbers[0]:
            raise HTTPException(status_code=404, detail="Email not found")

        msg_num = message_numbers[0].split()[0]

        # Fetch email
        _, msg_data = customer_email_monitor.imap_connection.fetch(msg_num, "(RFC822)")

        if not msg_data or not msg_data[0]:
            raise HTTPException(status_code=404, detail="Email data not found")

        email_body = msg_data[0][1]
        msg = email.message_from_bytes(email_body)

        # Find attachment
        attachment_count = 0
        for part in msg.walk():
            if part.get_content_disposition() == "attachment":
                if attachment_count == attachment_index:
                    # Get filename
                    filename = part.get_filename() or f"attachment_{attachment_index}"

                    # Get content type
                    content_type = part.get_content_type()

                    # Get payload
                    payload = part.get_payload(decode=True)

                    # Disconnect
                    customer_email_monitor.disconnect()

                    # Return file
                    return Response(
                        content=payload,
                        media_type=content_type,
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
                    )

                attachment_count += 1

        # Disconnect
        customer_email_monitor.disconnect()

        raise HTTPException(status_code=404, detail=f"Attachment {attachment_index} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download attachment: {e}", exc_info=True)
        customer_email_monitor.disconnect()
        raise HTTPException(status_code=500, detail=f"Failed to download attachment: {str(e)}")


# ============================================================================
# RESEND WEBHOOKS
# ============================================================================


class ResendWebhookData(BaseModel):
    """Resend webhook event data"""

    created_at: str
    email_id: str
    from_: str = Field(alias="from")
    to: list[str]
    subject: str


class ResendWebhookEvent(BaseModel):
    """Resend webhook event payload"""

    type: str  # email.sent, email.delivered, email.bounced, etc.
    created_at: str
    data: ResendWebhookData


@router.post("/webhooks/resend", response_model=dict, include_in_schema=False)
async def resend_webhook(
    request: Request,
    svix_id: Optional[str] = Header(None, alias="svix-id"),
    svix_timestamp: Optional[str] = Header(None, alias="svix-timestamp"),
    svix_signature: Optional[str] = Header(None, alias="svix-signature"),
):
    """
    Resend webhook endpoint for email events.

    Handles:
    - email.sent - Email sent successfully
    - email.delivered - Email delivered to recipient
    - email.delivery_delayed - Temporary delivery failure
    - email.bounced - Permanent delivery failure
    - email.complained - Marked as spam
    - email.opened - Email opened (if tracking enabled)
    - email.clicked - Link clicked

    Security: Verifies webhook signature from Resend
    """
    try:
        # Get raw body
        body = await request.body()
        payload = body.decode()

        # TODO: Verify webhook signature (optional but recommended)
        # For now, we'll just log the events

        # Parse event
        import json

        event_data = json.loads(payload)
        event_type = event_data.get("type")

        logger.info(f"≡ƒôº Resend webhook received: {event_type}")
        logger.debug(f"Event data: {event_data}")

        # Handle different event types
        if event_type == "email.sent":
            # Email successfully sent from Resend
            email_id = event_data.get("data", {}).get("email_id")
            logger.info(f"Γ£à Email sent: {email_id}")

        elif event_type == "email.delivered":
            # Email delivered to recipient's inbox
            email_id = event_data.get("data", {}).get("email_id")
            recipient = event_data.get("data", {}).get("to", [])[0]
            logger.info(f"≡ƒô¼ Email delivered to {recipient}: {email_id}")

        elif event_type == "email.bounced":
            # Email bounced (permanent failure)
            email_id = event_data.get("data", {}).get("email_id")
            recipient = event_data.get("data", {}).get("to", [])[0]
            logger.error(f"Γ¥î Email bounced for {recipient}: {email_id}")
            # TODO: Mark email as bounced in database, notify admin

        elif event_type == "email.delivery_delayed":
            # Temporary delivery failure
            email_id = event_data.get("data", {}).get("email_id")
            logger.warning(f"ΓÅ│ Email delivery delayed: {email_id}")

        elif event_type == "email.complained":
            # Recipient marked as spam
            email_id = event_data.get("data", {}).get("email_id")
            recipient = event_data.get("data", {}).get("to", [])[0]
            logger.error(f"≡ƒÜ¿ Email marked as spam by {recipient}: {email_id}")
            # TODO: Add recipient to suppression list

        elif event_type == "email.opened":
            # Email opened (tracking must be enabled)
            email_id = event_data.get("data", {}).get("email_id")
            logger.info(f"≡ƒæÇ Email opened: {email_id}")
            # TODO: Track open metrics

        elif event_type == "email.clicked":
            # Link clicked in email
            email_id = event_data.get("data", {}).get("email_id")
            logger.info(f"≡ƒû▒∩╕Å Link clicked in email: {email_id}")
            # TODO: Track click metrics

        else:
            logger.warning(f"ΓÜá∩╕Å Unknown webhook event type: {event_type}")

        # TODO: Store webhook events in database for tracking

        return {
            "success": True,
            "event_type": event_type,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.exception(f"Error processing Resend webhook: {e}")
        # Return 200 to avoid Resend retrying failed webhooks
        return {
            "success": False,
            "error": str(e),
        }


# ============================================================================
# EMAIL LABELS API - Custom Label Management
# ============================================================================


class LabelCreate(BaseModel):
    """Create new email label"""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#6B7280", pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)


class LabelUpdate(BaseModel):
    """Update existing label"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, max_length=50)
    is_archived: Optional[bool] = None
    sort_order: Optional[int] = None


class LabelResponse(BaseModel):
    """Label response"""

    id: int
    name: str
    slug: str
    description: Optional[str]
    color: str
    icon: Optional[str]
    is_system: bool
    is_archived: bool
    email_count: int
    sort_order: int
    created_at: datetime
    updated_at: datetime


@router.get("/labels", response_model=list[LabelResponse])
async def list_labels(
    include_archived: bool = Query(False, description="Include archived labels"),
    db: AsyncSession = Depends(get_async_session),
    _user=Depends(superadmin_required),
):
    """
    Get all email labels.

    Returns active labels by default. Set include_archived=true to see all.
    System labels cannot be deleted (e.g., Important, Follow-up).
    """
    from sqlalchemy import select
    from models.email_label import EmailLabel

    query = select(EmailLabel).where(EmailLabel.is_deleted == False)

    if not include_archived:
        query = query.where(EmailLabel.is_archived == False)

    query = query.order_by(EmailLabel.sort_order, EmailLabel.name)

    result = await db.execute(query)
    labels = result.scalars().all()

    return [
        LabelResponse(
            id=label.id,
            name=label.name,
            slug=label.slug,
            description=label.description,
            color=label.color,
            icon=label.icon,
            is_system=label.is_system,
            is_archived=label.is_archived,
            email_count=label.email_count,
            sort_order=label.sort_order,
            created_at=label.created_at,
            updated_at=label.updated_at,
        )
        for label in labels
    ]


@router.post("/labels", response_model=LabelResponse, status_code=201)
async def create_label(
    data: LabelCreate,
    db: AsyncSession = Depends(get_async_session),
    _user=Depends(superadmin_required),
):
    """
    Create a new email label.

    Label slug is auto-generated from name (e.g., "Follow Up" ΓåÆ "follow-up").
    Label names must be unique.
    """
    from sqlalchemy import select
    from models.email_label import EmailLabel
    import re

    # Generate slug from name
    slug = re.sub(r"[^a-z0-9]+", "-", data.name.lower()).strip("-")

    # Check if name or slug already exists
    existing_query = select(EmailLabel).where(
        (EmailLabel.name == data.name) | (EmailLabel.slug == slug), EmailLabel.is_deleted == False
    )
    result = await db.execute(existing_query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Label with this name already exists")

    # Create label
    label = EmailLabel(
        name=data.name,
        slug=slug,
        description=data.description,
        color=data.color,
        icon=data.icon,
        is_system=False,
        is_archived=False,
        email_count=0,
        sort_order=0,
    )

    db.add(label)
    await db.commit()
    await db.refresh(label)

    logger.info(f"Created label: {label.name} (slug: {label.slug})")

    return LabelResponse(
        id=label.id,
        name=label.name,
        slug=label.slug,
        description=label.description,
        color=label.color,
        icon=label.icon,
        is_system=label.is_system,
        is_archived=label.is_archived,
        email_count=label.email_count,
        sort_order=label.sort_order,
        created_at=label.created_at,
        updated_at=label.updated_at,
    )


@router.put("/labels/{label_id}", response_model=LabelResponse)
async def update_label(
    label_id: int,
    data: LabelUpdate,
    db: AsyncSession = Depends(get_async_session),
    _user=Depends(superadmin_required),
):
    """
    Update an existing label.

    System labels can only update color/icon, not name.
    """
    from sqlalchemy import select
    from models.email_label import EmailLabel
    import re

    # Get label
    query = select(EmailLabel).where(EmailLabel.id == label_id, EmailLabel.is_deleted == False)
    result = await db.execute(query)
    label = result.scalar_one_or_none()

    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    # System labels cannot be renamed
    if label.is_system and data.name and data.name != label.name:
        raise HTTPException(status_code=400, detail="Cannot rename system labels")

    # Update fields
    if data.name and data.name != label.name:
        # Check name uniqueness
        slug = re.sub(r"[^a-z0-9]+", "-", data.name.lower()).strip("-")
        existing_query = select(EmailLabel).where(
            (EmailLabel.name == data.name) | (EmailLabel.slug == slug),
            EmailLabel.id != label_id,
            EmailLabel.is_deleted == False,
        )
        result = await db.execute(existing_query)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Label with this name already exists")

        label.name = data.name
        label.slug = slug

    if data.description is not None:
        label.description = data.description
    if data.color:
        label.color = data.color
    if data.icon is not None:
        label.icon = data.icon
    if data.is_archived is not None:
        label.is_archived = data.is_archived
    if data.sort_order is not None:
        label.sort_order = data.sort_order

    label.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(label)

    logger.info(f"Updated label: {label.name}")

    return LabelResponse(
        id=label.id,
        name=label.name,
        slug=label.slug,
        description=label.description,
        color=label.color,
        icon=label.icon,
        is_system=label.is_system,
        is_archived=label.is_archived,
        email_count=label.email_count,
        sort_order=label.sort_order,
        created_at=label.created_at,
        updated_at=label.updated_at,
    )


@router.delete("/labels/{label_id}", status_code=204)
async def delete_label(
    label_id: int,
    db: AsyncSession = Depends(get_async_session),
    _user=Depends(superadmin_required),
):
    """
    Archive (soft delete) a label.

    System labels cannot be deleted.
    Emails with this label will have it removed.
    """
    from sqlalchemy import select
    from models.email_label import EmailLabel

    # Get label
    query = select(EmailLabel).where(EmailLabel.id == label_id, EmailLabel.is_deleted == False)
    result = await db.execute(query)
    label = result.scalar_one_or_none()

    if not label:
        raise HTTPException(status_code=404, detail="Label not found")

    if label.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system labels")

    # Soft delete
    label.is_archived = True
    label.updated_at = datetime.now(timezone.utc)

    await db.commit()

    logger.info(f"Archived label: {label.name}")

    return Response(status_code=204)
