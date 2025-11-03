"""
Unified Inbox endpoints
Handles SMS, Instagram, Facebook, email communications in one place
Admin users get 100-200 requests/minute vs 20 for public
"""

from datetime import datetime
from enum import Enum
import logging
from typing import Any

from api.deps import AdminUser, get_current_admin_user
from core.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
from pydantic import BaseModel, Field


class MessageChannel(str, Enum):
    SMS = "sms"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class MessageDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class ThreadStatus(str, Enum):
    OPEN = "open"
    PENDING = "pending"
    CLOSED = "closed"
    ARCHIVED = "archived"


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    channel: MessageChannel
    direction: MessageDirection
    thread_id: int
    from_number: str | None = None
    to_number: str | None = None
    from_email: str | None = None
    to_email: str | None = None
    social_user_id: str | None = None
    social_username: str | None = None
    attachments: list[str] | None = []
    metadata: dict[str, Any] | None = {}


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: int
    status: MessageStatus
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    assigned_to: str | None = None
    ai_suggested_reply: str | None = None

    class Config:
        from_attributes = True


class ThreadBase(BaseModel):
    channel: MessageChannel
    status: ThreadStatus = ThreadStatus.OPEN
    customer_identifier: str = Field(..., description="Phone, email, or social username")
    customer_name: str | None = None
    subject: str | None = None
    tags: list[str] | None = []
    priority: int = Field(1, ge=1, le=5, description="1=Low, 5=Urgent")


class ThreadCreate(ThreadBase):
    pass


class ThreadUpdate(BaseModel):
    status: ThreadStatus | None = None
    customer_name: str | None = None
    subject: str | None = None
    tags: list[str] | None = None
    priority: int | None = Field(None, ge=1, le=5)
    assigned_to: str | None = None


class ThreadResponse(ThreadBase):
    id: int
    message_count: int = 0
    unread_count: int = 0
    last_message_at: datetime | None = None
    last_message_preview: str | None = None
    created_at: datetime
    updated_at: datetime
    assigned_to: str | None = None
    customer_id: int | None = None
    lead_id: int | None = None

    class Config:
        from_attributes = True


class ThreadWithMessages(ThreadResponse):
    messages: list[MessageResponse] = []


class InboxStats(BaseModel):
    total_threads: int = 0
    open_threads: int = 0
    pending_threads: int = 0
    unread_messages: int = 0
    avg_response_time_minutes: float = 0.0
    channels: dict[str, int] = {}


# Mock data storage (replace with actual database operations)
mock_threads = [
    {
        "id": 1,
        "channel": "sms",
        "status": "open",
        "customer_identifier": "+19165551234",
        "customer_name": "John Smith",
        "subject": "Hibachi Booking Inquiry",
        "priority": 3,
        "message_count": 5,
        "unread_count": 1,
        "last_message_at": datetime.now(),
        "last_message_preview": "What time would work best for the hibachi setup?",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "assigned_to": "admin@myhibachichef.com",
        "customer_id": 1,
        "lead_id": None,
        "tags": ["booking", "inquiry"],
    },
    {
        "id": 2,
        "channel": "instagram",
        "status": "pending",
        "customer_identifier": "@foodlover_sarah",
        "customer_name": "Sarah Johnson",
        "subject": "Birthday Party Request",
        "priority": 2,
        "message_count": 3,
        "unread_count": 2,
        "last_message_at": datetime.now(),
        "last_message_preview": "Can you do hibachi for 8 people next weekend?",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "assigned_to": None,
        "customer_id": 2,
        "lead_id": 2,
        "tags": ["birthday", "instagram"],
    },
    {
        "id": 3,
        "channel": "facebook",
        "status": "open",
        "customer_identifier": "mike.davis.fb",
        "customer_name": "Mike Davis",
        "subject": "Corporate Event Quote",
        "priority": 4,
        "message_count": 8,
        "unread_count": 0,
        "last_message_at": datetime.now(),
        "last_message_preview": "The quote looks good, let's proceed with the booking",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "assigned_to": "owner@myhibachichef.com",
        "customer_id": None,
        "lead_id": 1,
        "tags": ["corporate", "quote", "high-value"],
    },
]

mock_messages = [
    {
        "id": 1,
        "content": "Hi! I'm interested in booking a hibachi chef for my anniversary party.",
        "channel": "sms",
        "direction": "inbound",
        "thread_id": 1,
        "from_number": "+19165551234",
        "to_number": "+19167408768",
        "status": "read",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "sent_at": datetime.now(),
        "delivered_at": datetime.now(),
        "read_at": datetime.now(),
        "attachments": [],
        "metadata": {"ringcentral_id": "msg_123"},
    },
    {
        "id": 2,
        "content": "That sounds wonderful! I'd be happy to help you celebrate. How many guests will you be having?",
        "channel": "sms",
        "direction": "outbound",
        "thread_id": 1,
        "from_number": "+19167408768",
        "to_number": "+19165551234",
        "status": "delivered",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "sent_at": datetime.now(),
        "delivered_at": datetime.now(),
        "attachments": [],
        "metadata": {"ringcentral_id": "msg_124"},
    },
    {
        "id": 3,
        "content": "We're planning for 8 people on October 20th. What time would work best?",
        "channel": "sms",
        "direction": "inbound",
        "thread_id": 1,
        "from_number": "+19165551234",
        "to_number": "+19167408768",
        "status": "delivered",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "sent_at": datetime.now(),
        "delivered_at": datetime.now(),
        "attachments": [],
        "metadata": {"ringcentral_id": "msg_125"},
        "ai_suggested_reply": "For 8 guests, I recommend starting around 6:00 PM or 7:00 PM. This gives enough time for setup and a leisurely dining experience. What time preference do you have?",
    },
]


@router.get("/threads", response_model=list[ThreadResponse])
async def list_threads(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    channel: MessageChannel | None = Query(None, description="Filter by channel"),
    status: ThreadStatus | None = Query(None, description="Filter by status"),
    assigned_to: str | None = Query(None, description="Filter by assigned user"),
    unread_only: bool = Query(False, description="Show only threads with unread messages"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    List conversation threads with pagination and filters
    Admin rate limit: 100 requests/minute
    """
    try:
        # Apply filters to mock data
        filtered_threads = mock_threads.copy()

        if channel:
            filtered_threads = [t for t in filtered_threads if t["channel"] == channel]

        if status:
            filtered_threads = [t for t in filtered_threads if t["status"] == status]

        if assigned_to:
            filtered_threads = [t for t in filtered_threads if t.get("assigned_to") == assigned_to]

        if unread_only:
            filtered_threads = [t for t in filtered_threads if t["unread_count"] > 0]

        # Sort by last message time (most recent first)
        filtered_threads.sort(key=lambda t: t["last_message_at"] or t["created_at"], reverse=True)

        # Apply pagination
        total = len(filtered_threads)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        threads_page = filtered_threads[start_idx:end_idx]

        logger.info(
            f"Admin {current_admin.email} listed threads - page {page}, found {total} total"
        )

        return [ThreadResponse(**t) for t in threads_page]

    except Exception as e:
        logger.exception(f"Error listing threads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve threads"
        )


@router.get("/threads/{thread_id}", response_model=ThreadWithMessages)
async def get_thread(
    thread_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    Get specific thread with all messages
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find thread in mock data
        thread = next((t for t in mock_threads if t["id"] == thread_id), None)

        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Thread {thread_id} not found"
            )

        # Get messages for this thread
        thread_messages = [m for m in mock_messages if m["thread_id"] == thread_id]
        thread_messages.sort(key=lambda m: m["created_at"])

        # Mark messages as read
        for msg in mock_messages:
            if msg["thread_id"] == thread_id and msg["direction"] == "inbound":
                msg["status"] = "read"
                msg["read_at"] = datetime.now()

        # Update thread unread count
        thread["unread_count"] = 0
        thread["updated_at"] = datetime.now()

        logger.info(f"Admin {current_admin.email} retrieved thread {thread_id}")

        return ThreadWithMessages(
            **thread, messages=[MessageResponse(**m) for m in thread_messages]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve thread"
        )


@router.post(
    "/threads/{thread_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    thread_id: int,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    Send message in thread
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find thread
        thread = next((t for t in mock_threads if t["id"] == thread_id), None)

        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Thread {thread_id} not found"
            )

        # Create new message
        new_id = max([m["id"] for m in mock_messages], default=0) + 1
        new_message = {
            "id": new_id,
            **message.dict(),
            "thread_id": thread_id,
            "direction": "outbound",
            "status": "sent",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "sent_at": datetime.now(),
            "delivered_at": datetime.now(),
            "assigned_to": current_admin.email,
        }

        # Set appropriate from/to based on channel and thread
        if message.channel == "sms":
            new_message["from_number"] = "+19167408768"  # Business number
            new_message["to_number"] = thread["customer_identifier"]
        elif message.channel in ["instagram", "facebook"]:
            new_message["social_username"] = "myhibachichef"
            new_message["social_user_id"] = thread["customer_identifier"]

        mock_messages.append(new_message)

        # Update thread
        thread["message_count"] += 1
        thread["last_message_at"] = datetime.now()
        thread["last_message_preview"] = message.content[:50] + (
            "..." if len(message.content) > 50 else ""
        )
        thread["updated_at"] = datetime.now()

        logger.info(
            f"Admin {current_admin.email} sent message in thread {thread_id} via {message.channel}"
        )

        # DOCUMENTED: External message sending not implemented in mock endpoint
        # Production implementation should:
        # 1. Route to RingCentral API for SMS
        # 2. Route to Meta Business API for WhatsApp/Instagram/Facebook
        # 3. Route to email service for email
        # 4. Handle webhook responses and delivery status
        # Integration point: Create MessageSenderService with channel-specific adapters

        return MessageResponse(**new_message)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error sending message in thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send message"
        )


@router.put("/threads/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: int,
    thread_update: ThreadUpdate,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    Update thread properties (status, assignment, etc.)
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find and update thread
        thread_idx = next((i for i, t in enumerate(mock_threads) if t["id"] == thread_id), None)

        if thread_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Thread {thread_id} not found"
            )

        # Update fields
        update_data = thread_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now()

        mock_threads[thread_idx].update(update_data)

        logger.info(f"Admin {current_admin.email} updated thread {thread_id}")
        return ThreadResponse(**mock_threads[thread_idx])

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update thread"
        )


@router.get("/stats", response_model=InboxStats)
async def get_inbox_stats(
    db: AsyncSession = Depends(get_db), current_admin: AdminUser = Depends(get_current_admin_user)
):
    """
    Get inbox statistics
    Admin rate limit: 100 requests/minute
    """
    try:
        # Calculate stats from mock data
        stats = InboxStats()

        stats.total_threads = len(mock_threads)
        stats.open_threads = len([t for t in mock_threads if t["status"] == "open"])
        stats.pending_threads = len([t for t in mock_threads if t["status"] == "pending"])
        stats.unread_messages = sum(t["unread_count"] for t in mock_threads)

        # Channel breakdown
        for thread in mock_threads:
            channel = thread["channel"]
            stats.channels[channel] = stats.channels.get(channel, 0) + 1

        # Mock average response time
        stats.avg_response_time_minutes = 15.5

        logger.info(f"Admin {current_admin.email} retrieved inbox stats")
        return stats

    except Exception as e:
        logger.exception(f"Error getting inbox stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve inbox stats",
        )


@router.post("/threads/{thread_id}/ai-reply")
async def generate_ai_reply(
    thread_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    Generate AI-suggested reply for thread
    Admin rate limit: 100 requests/minute (but AI endpoint is 10/min)
    """
    try:
        # Find thread
        thread = next((t for t in mock_threads if t["id"] == thread_id), None)

        if not thread:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Thread {thread_id} not found"
            )

        # Get recent messages for context
        thread_messages = [m for m in mock_messages if m["thread_id"] == thread_id]
        thread_messages.sort(key=lambda m: m["created_at"], reverse=True)

        # Mock AI reply generation (replace with actual AI service call)
        ai_replies = [
            "Thank you for your interest! I'd be happy to help with your hibachi event. Let me get some details to provide you with an accurate quote.",
            "That sounds like a wonderful celebration! For 8 guests, I recommend our Premium Hibachi Experience. When were you thinking of having this event?",
            "I appreciate you reaching out! Our hibachi experiences are perfect for special occasions. What date did you have in mind?",
        ]

        import random

        ai_reply = random.choice(ai_replies)

        logger.info(f"Admin {current_admin.email} generated AI reply for thread {thread_id}")

        return {
            "suggested_reply": ai_reply,
            "confidence": 85,
            "context_messages": len(thread_messages),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating AI reply for thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate AI reply"
        )


@router.post("/threads/{thread_id}/assign")
async def assign_thread(
    thread_id: int,
    assigned_to: str = Query(..., description="Email of admin to assign to"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin_user),
):
    """
    Assign thread to admin user
    Admin rate limit: 100 requests/minute
    """
    try:
        # Find thread
        thread_idx = next((i for i, t in enumerate(mock_threads) if t["id"] == thread_id), None)

        if thread_idx is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Thread {thread_id} not found"
            )

        # Update assignment
        mock_threads[thread_idx]["assigned_to"] = assigned_to
        mock_threads[thread_idx]["updated_at"] = datetime.now()

        logger.info(f"Admin {current_admin.email} assigned thread {thread_id} to {assigned_to}")

        return {"message": f"Thread {thread_id} assigned to {assigned_to}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error assigning thread {thread_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to assign thread"
        )
