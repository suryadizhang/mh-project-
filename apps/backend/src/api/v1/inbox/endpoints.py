"""
Unified Inbox API Endpoints
RESTful API for unified messaging system
"""

from datetime import UTC, datetime
import logging
from uuid import UUID

from api.app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import (
    Message,
    MessageChannel,
    MessageStatus,
    TCPAOptStatus,
    Thread,
)
from .router import MessageRouter
from .schemas import (
    BulkMessageRequest,
    BulkMessageResponse,
    MessageResponse,
    MessageStatsResponse,
    SendMessageRequest,
    TCPAStatusResponse,
    TCPAUpdateRequest,
    ThreadCreateRequest,
    ThreadResponse,
    ThreadWithMessagesResponse,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/v1/inbox", tags=["Unified Inbox"])


# Message endpoints
@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(request: SendMessageRequest, db: AsyncSession = Depends(get_db)):
    """Send a message through unified inbox system"""
    try:
        message_router = MessageRouter(db)
        result = await message_router.route_message(request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Send message failed: {e!s}")
        raise HTTPException(status_code=500, detail="Message sending failed")


@router.get("/messages", response_model=list[MessageResponse])
async def get_messages(
    channel: MessageChannel | None = None,
    contact_id: UUID | None = None,
    thread_id: UUID | None = None,
    status: MessageStatus | None = None,
    phone_number: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get messages with filtering and pagination"""
    try:
        query = select(Message).options(selectinload(Message.thread))

        # Apply filters
        conditions = []
        if channel:
            conditions.append(Message.channel == channel)
        if contact_id:
            conditions.append(Message.contact_id == contact_id)
        if thread_id:
            conditions.append(Message.thread_id == thread_id)
        if status:
            conditions.append(Message.status == status)
        if phone_number:
            conditions.append(Message.phone_number == phone_number)

        if conditions:
            query = query.where(and_(*conditions))

        # Apply pagination and ordering
        query = query.order_by(desc(Message.created_at))
        query = query.offset((page - 1) * limit).limit(limit)

        result = await db.execute(query)
        messages = result.scalars().all()

        return [MessageResponse.from_orm(msg) for msg in messages]

    except Exception as e:
        logger.exception(f"Get messages failed: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to retrieve messages")


@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(message_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get specific message by ID"""
    message = await db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return MessageResponse.from_orm(message)


@router.patch("/messages/{message_id}/status")
async def update_message_status(
    message_id: UUID, new_status: MessageStatus, db: AsyncSession = Depends(get_db)
):
    """Update message status (read, replied, etc.)"""
    message = await db.get(Message, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    old_status = message.status
    message.status = new_status

    # Update status timestamps
    now = datetime.now(UTC)
    if new_status == MessageStatus.READ and not message.read_at:
        message.read_at = now
    elif new_status == MessageStatus.DELIVERED and not message.delivered_at:
        message.delivered_at = now

    await db.commit()

    # Notify WebSocket clients of status change
    message_router = MessageRouter(db)
    await message_router._notify_websocket_clients(message, "status_updated")

    return {"status": "updated", "old_status": old_status, "new_status": new_status}


# Thread endpoints
@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(request: ThreadCreateRequest, db: AsyncSession = Depends(get_db)):
    """Create a new message thread"""
    try:
        thread = Thread(
            channel=request.channel,
            subject=request.subject,
            contact_id=request.contact_id,
            booking_id=request.booking_id,
            metadata=request.metadata,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        db.add(thread)
        await db.commit()
        await db.refresh(thread)

        return ThreadResponse.from_orm(thread)

    except Exception as e:
        logger.exception(f"Create thread failed: {e!s}")
        raise HTTPException(status_code=500, detail="Thread creation failed")


@router.get("/threads", response_model=list[ThreadResponse])
async def get_threads(
    channel: MessageChannel | None = None,
    contact_id: UUID | None = None,
    is_active: bool = True,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get threads with filtering and pagination"""
    try:
        query = select(Thread)

        # Apply filters
        conditions = [Thread.is_active == is_active]
        if channel:
            conditions.append(Thread.channel == channel)
        if contact_id:
            conditions.append(Thread.contact_id == contact_id)

        query = query.where(and_(*conditions))

        # Apply pagination and ordering
        query = query.order_by(desc(Thread.updated_at))
        query = query.offset((page - 1) * limit).limit(limit)

        result = await db.execute(query)
        threads = result.scalars().all()

        # Get message counts for each thread
        response_threads = []
        for thread in threads:
            # Count messages in thread
            count_query = select(func.count(Message.id)).where(Message.thread_id == thread.id)
            count_result = await db.execute(count_query)
            message_count = count_result.scalar()

            # Count unread messages
            unread_query = select(func.count(Message.id)).where(
                and_(Message.thread_id == thread.id, Message.status != MessageStatus.READ)
            )
            unread_result = await db.execute(unread_query)
            unread_count = unread_result.scalar()

            thread_response = ThreadResponse.from_orm(thread)
            thread_response.message_count = message_count
            thread_response.unread_count = unread_count

            response_threads.append(thread_response)

        return response_threads

    except Exception as e:
        logger.exception(f"Get threads failed: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to retrieve threads")


@router.get("/threads/{thread_id}", response_model=ThreadWithMessagesResponse)
async def get_thread_with_messages(
    thread_id: UUID,
    include_messages: bool = True,
    message_limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get thread with message history"""
    thread = await db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    thread_response = ThreadWithMessagesResponse.from_orm(thread)

    if include_messages:
        # Get messages for thread
        query = select(Message).where(Message.thread_id == thread_id)
        query = query.order_by(Message.created_at).limit(message_limit)

        result = await db.execute(query)
        messages = result.scalars().all()

        thread_response.messages = [MessageResponse.from_orm(msg) for msg in messages]

    return thread_response


@router.patch("/threads/{thread_id}")
async def update_thread(
    thread_id: UUID,
    is_active: bool | None = None,
    is_archived: bool | None = None,
    subject: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Update thread properties"""
    thread = await db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    if is_active is not None:
        thread.is_active = is_active
    if is_archived is not None:
        thread.is_archived = is_archived
    if subject is not None:
        thread.subject = subject

    thread.updated_at = datetime.now(UTC)

    await db.commit()

    return {"status": "updated"}


# TCPA endpoints
@router.get("/tcpa/{phone_number}", response_model=list[TCPAStatusResponse])
async def get_tcpa_status(phone_number: str, db: AsyncSession = Depends(get_db)):
    """Get TCPA opt status for phone number"""
    query = select(TCPAOptStatus).where(TCPAOptStatus.phone_number == phone_number)
    result = await db.execute(query)
    statuses = result.scalars().all()

    return [TCPAStatusResponse.from_orm(status) for status in statuses]


@router.post("/tcpa", response_model=TCPAStatusResponse, status_code=status.HTTP_201_CREATED)
async def update_tcpa_status(request: TCPAUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Update TCPA opt status"""
    try:
        # Check for existing record
        query = select(TCPAOptStatus).where(
            and_(
                TCPAOptStatus.phone_number == request.phone_number,
                TCPAOptStatus.channel == request.channel,
            )
        )
        result = await db.execute(query)
        tcpa_record = result.scalar_one_or_none()

        now = datetime.now(UTC)

        if tcpa_record:
            tcpa_record.status = request.status
            tcpa_record.opt_in_method = request.opt_in_method
            tcpa_record.opt_in_source = request.opt_in_source
            tcpa_record.updated_at = now
        else:
            tcpa_record = TCPAOptStatus(
                phone_number=request.phone_number,
                channel=request.channel,
                status=request.status,
                opt_in_method=request.opt_in_method,
                opt_in_source=request.opt_in_source,
                created_at=now,
                updated_at=now,
            )
            db.add(tcpa_record)

        await db.commit()
        await db.refresh(tcpa_record)

        return TCPAStatusResponse.from_orm(tcpa_record)

    except Exception as e:
        logger.exception(f"TCPA update failed: {e!s}")
        raise HTTPException(status_code=500, detail="TCPA status update failed")


# Statistics endpoints
@router.get("/stats", response_model=MessageStatsResponse)
async def get_message_stats(
    channel: MessageChannel | None = None,
    days: int = Query(7, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get message statistics"""
    try:
        # Base query conditions
        conditions = []
        if channel:
            conditions.append(Message.channel == channel)

        # Total messages
        total_query = select(func.count(Message.id))
        if conditions:
            total_query = total_query.where(and_(*conditions))
        total_result = await db.execute(total_query)
        total_messages = total_result.scalar()

        # Total threads
        thread_query = select(func.count(Thread.id))
        if channel:
            thread_query = thread_query.where(Thread.channel == channel)
        thread_result = await db.execute(thread_query)
        total_threads = thread_result.scalar()

        # Channel stats
        channel_query = select(Message.channel, func.count(Message.id)).group_by(Message.channel)
        channel_result = await db.execute(channel_query)
        channel_stats = {row[0]: row[1] for row in channel_result}

        # Status stats
        status_query = select(Message.status, func.count(Message.id)).group_by(Message.status)
        if conditions:
            status_query = status_query.where(and_(*conditions))
        status_result = await db.execute(status_query)
        status_stats = {row[0]: row[1] for row in status_result}

        # Direction stats
        direction_query = select(Message.direction, func.count(Message.id)).group_by(
            Message.direction
        )
        if conditions:
            direction_query = direction_query.where(and_(*conditions))
        direction_result = await db.execute(direction_query)
        direction_stats = {row[0]: row[1] for row in direction_result}

        # Recent activity (last 24 hours)
        last_24h = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

        recent_msg_query = select(func.count(Message.id)).where(Message.created_at >= last_24h)
        if conditions:
            recent_msg_query = recent_msg_query.where(and_(*conditions))
        recent_msg_result = await db.execute(recent_msg_query)
        messages_last_24h = recent_msg_result.scalar()

        recent_thread_query = select(func.count(Thread.id)).where(Thread.created_at >= last_24h)
        if channel:
            recent_thread_query = recent_thread_query.where(Thread.channel == channel)
        recent_thread_result = await db.execute(recent_thread_query)
        threads_last_24h = recent_thread_result.scalar()

        return MessageStatsResponse(
            total_messages=total_messages,
            total_threads=total_threads,
            channel_stats=channel_stats,
            status_stats=status_stats,
            direction_stats=direction_stats,
            messages_last_24h=messages_last_24h,
            threads_last_24h=threads_last_24h,
        )

    except Exception as e:
        logger.exception(f"Get stats failed: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


# Bulk operations
@router.post("/messages/bulk", response_model=BulkMessageResponse)
async def send_bulk_messages(request: BulkMessageRequest, db: AsyncSession = Depends(get_db)):
    """Send multiple messages in batch"""
    try:
        message_router = MessageRouter(db)
        results = []
        successful = 0
        failed = 0

        for msg_request in request.messages:
            try:
                result = await message_router.route_message(msg_request)
                results.append(
                    {"success": True, "message_id": str(result.id), "status": result.status}
                )
                successful += 1
            except Exception as e:
                results.append({"success": False, "error": str(e)})
                failed += 1

        return BulkMessageResponse(
            batch_id=uuid4(),
            total_messages=len(request.messages),
            successful=successful,
            failed=failed,
            results=results,
        )

    except Exception as e:
        logger.exception(f"Bulk send failed: {e!s}")
        raise HTTPException(status_code=500, detail="Bulk message sending failed")


# Health check
@router.get("/health")
async def inbox_health_check(db: AsyncSession = Depends(get_db)):
    """Health check for unified inbox system"""
    try:
        # Test database connection
        await db.execute(select(1))

        # Get basic stats
        msg_count = await db.execute(select(func.count(Message.id)))
        thread_count = await db.execute(select(func.count(Thread.id)))

        return {
            "status": "healthy",
            "message_count": msg_count.scalar(),
            "thread_count": thread_count.scalar(),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.exception(f"Health check failed: {e!s}")
        raise HTTPException(status_code=503, detail="Inbox system unhealthy")
