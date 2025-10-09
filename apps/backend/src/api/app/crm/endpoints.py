"""
CRM API endpoints using CQRS pattern with proper authentication and validation.
"""
from datetime import date as date_type
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.middleware import (
    AuthenticatedUser,
    audit_log_action,
    get_current_active_user,
    rate_limit,
    require_any_permission,
    require_permission,
)
from api.app.auth.models import Permission
from api.app.cqrs.base import CommandResult, QueryResult, command_bus, query_bus
from api.app.cqrs.crm_operations import *
from api.app.database import get_db_session

router = APIRouter(prefix="/crm", tags=["CRM Operations"])


# Request/Response Models
class CreateBookingRequest(BaseModel):
    """Create booking request model."""
    customer_email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    customer_name: str = Field(..., min_length=2, max_length=100)
    customer_phone: str = Field(..., pattern=r'^\+?[\d\s\-\(\)]+$')

    date: date_type
    slot: str = Field(..., pattern=r'^(9|10|11):00 (AM|PM)$|^(12|1|2|3|4|5|6|7|8):00 (AM|PM)$')
    total_guests: int = Field(..., ge=1, le=50)
    special_requests: Optional[str] = Field(None, max_length=500)

    price_per_person_cents: int = Field(..., ge=0)
    total_due_cents: int = Field(..., ge=0)
    deposit_due_cents: int = Field(..., ge=0)

    source: str = Field("website", max_length=50)
    ai_conversation_id: Optional[str] = Field(None, max_length=100)


class UpdateBookingRequest(BaseModel):
    """Update booking request model."""
    customer_name: Optional[str] = Field(None, min_length=2, max_length=100)
    customer_phone: Optional[str] = Field(None, pattern=r'^\+?[\d\s\-\(\)]+$')
    date: Optional[date_type] = None
    slot: Optional[str] = Field(None, pattern=r'^(9|10|11):00 (AM|PM)$|^(12|1|2|3|4|5|6|7|8):00 (AM|PM)$')
    total_guests: Optional[int] = Field(None, ge=1, le=50)
    special_requests: Optional[str] = Field(None, max_length=500)

    update_reason: str = Field(..., max_length=200)


class RecordPaymentRequest(BaseModel):
    """Record payment request model."""
    amount_cents: int = Field(..., gt=0)
    payment_method: str = Field(..., pattern=r'^(stripe|cash|check|card|other)$')
    payment_reference: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=200)


class CancelBookingRequest(BaseModel):
    """Cancel booking request model."""
    cancellation_reason: str = Field(..., max_length=200)
    refund_amount_cents: int = Field(0, ge=0)


class SendMessageRequest(BaseModel):
    """Send message request model."""
    content: str = Field(..., min_length=1, max_length=1000)


class BookingResponse(BaseModel):
    """Booking response model."""
    booking_id: str
    customer: dict[str, Any]
    date: date_type
    slot: str
    total_guests: int
    status: str
    payment_status: str
    total_due_cents: int
    balance_due_cents: int
    special_requests: Optional[str] = None
    source: str
    created_at: str
    updated_at: str


class ApiResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    total_count: Optional[int] = None


def handle_command_result(result: CommandResult) -> ApiResponse:
    """Convert CommandResult to API response."""
    return ApiResponse(
        success=result.success,
        data=result.data,
        error=result.error
    )


def handle_query_result(result: QueryResult) -> ApiResponse:
    """Convert QueryResult to API response."""
    return ApiResponse(
        success=result.success,
        data=result.data,
        error=result.error,
        total_count=result.total_count
    )


@router.post("/bookings", response_model=ApiResponse)
@require_permission(Permission.BOOKING_CREATE)
@rate_limit(max_requests=10, window_seconds=60, per_user=True)
async def create_booking(
    request: CreateBookingRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new hibachi booking."""

    try:
        # Create command with idempotency key
        command = CreateBookingCommand(
            customer_email=request.customer_email,
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            date=request.date,
            slot=request.slot,
            total_guests=request.total_guests,
            special_requests=request.special_requests,
            price_per_person_cents=request.price_per_person_cents,
            total_due_cents=request.total_due_cents,
            deposit_due_cents=request.deposit_due_cents,
            source=request.source,
            ai_conversation_id=request.ai_conversation_id,
            idempotency_key=f"booking_{current_user.id}_{hash(str(request.dict()))}"
        )

        # Execute command
        result = await command_bus.execute(command, db)

        # Audit log
        await audit_log_action(
            "CREATE_BOOKING",
            current_user,
            db,
            resource_type="booking",
            resource_id=result.data.get('booking_id') if result.success else None,
            details={
                "customer_email": request.customer_email,
                "date": str(request.date),
                "slot": request.slot,
                "total_guests": request.total_guests,
                "total_due_cents": request.total_due_cents
            },
            success=result.success,
            error_message=result.error
        )

        return handle_command_result(result)

    except Exception as e:
        await audit_log_action(
            "CREATE_BOOKING",
            current_user,
            db,
            details={"error": "Unexpected error", "exception": str(e)},
            success=False,
            error_message="Internal server error"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the booking"
        )


@router.get("/bookings/{booking_id}", response_model=ApiResponse)
@require_permission(Permission.BOOKING_READ)
async def get_booking(
    booking_id: UUID,
    include_payments: bool = Query(True, description="Include payment history"),
    include_messages: bool = Query(True, description="Include message threads"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get booking details by ID."""

    try:
        query = GetBookingQuery(
            booking_id=booking_id,
            include_payments=include_payments,
            include_messages=include_messages
        )

        result = await query_bus.execute(query, db)

        await audit_log_action(
            "VIEW_BOOKING",
            current_user,
            db,
            resource_type="booking",
            resource_id=str(booking_id),
            details={"include_payments": include_payments, "include_messages": include_messages},
            success=result.success,
            error_message=result.error
        )

        return handle_query_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the booking"
        )


@router.get("/bookings", response_model=ApiResponse)
@require_permission(Permission.BOOKING_READ)
async def get_bookings(
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    customer_phone: Optional[str] = Query(None, description="Filter by customer phone"),
    date_from: Optional[date_type] = Query(None, description="Filter bookings from date"),
    date_to: Optional[date_type] = Query(None, description="Filter bookings to date"),
    status: Optional[str] = Query(None, pattern=r'^(confirmed|cancelled|completed|pending)$'),
    source: Optional[str] = Query(None, description="Filter by booking source"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("date", pattern=r'^(date|created_at|updated_at|customer_name)$'),
    sort_order: str = Query("asc", pattern=r'^(asc|desc)$'),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get bookings with filtering and pagination."""

    try:
        query = GetBookingsQuery(
            customer_email=customer_email,
            customer_phone=customer_phone,
            date_from=date_from,
            date_to=date_to,
            status=status,
            source=source,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )

        result = await query_bus.execute(query, db)

        await audit_log_action(
            "LIST_BOOKINGS",
            current_user,
            db,
            details={
                "filters": {
                    "customer_email": customer_email,
                    "date_from": str(date_from) if date_from else None,
                    "date_to": str(date_to) if date_to else None,
                    "status": status
                },
                "pagination": {"page": page, "page_size": page_size}
            },
            success=result.success,
            error_message=result.error
        )

        return handle_query_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving bookings"
        )


@router.put("/bookings/{booking_id}", response_model=ApiResponse)
@require_permission(Permission.BOOKING_UPDATE)
async def update_booking(
    booking_id: UUID,
    request: UpdateBookingRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update an existing booking."""

    try:
        command = UpdateBookingCommand(
            booking_id=booking_id,
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            date=request.date,
            slot=request.slot,
            total_guests=request.total_guests,
            special_requests=request.special_requests,
            updated_by=str(current_user.id),
            update_reason=request.update_reason,
            idempotency_key=f"update_booking_{booking_id}_{current_user.id}_{hash(str(request.dict()))}"
        )

        result = await command_bus.execute(command, db)

        await audit_log_action(
            "UPDATE_BOOKING",
            current_user,
            db,
            resource_type="booking",
            resource_id=str(booking_id),
            details={
                "changes": request.dict(exclude_unset=True),
                "update_reason": request.update_reason
            },
            success=result.success,
            error_message=result.error
        )

        return handle_command_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the booking"
        )


@router.delete("/bookings/{booking_id}", response_model=ApiResponse)
@require_permission(Permission.BOOKING_CANCEL)
async def cancel_booking(
    booking_id: UUID,
    request: CancelBookingRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Cancel a booking."""

    try:
        command = CancelBookingCommand(
            booking_id=booking_id,
            cancellation_reason=request.cancellation_reason,
            cancelled_by=str(current_user.id),
            refund_amount_cents=request.refund_amount_cents,
            idempotency_key=f"cancel_booking_{booking_id}_{current_user.id}"
        )

        result = await command_bus.execute(command, db)

        await audit_log_action(
            "CANCEL_BOOKING",
            current_user,
            db,
            resource_type="booking",
            resource_id=str(booking_id),
            details={
                "cancellation_reason": request.cancellation_reason,
                "refund_amount_cents": request.refund_amount_cents
            },
            success=result.success,
            error_message=result.error
        )

        return handle_command_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while cancelling the booking"
        )


@router.post("/bookings/{booking_id}/payments", response_model=ApiResponse)
@require_permission(Permission.PAYMENT_RECORD)
async def record_payment(
    booking_id: UUID,
    request: RecordPaymentRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Record a payment for a booking."""

    try:
        command = RecordPaymentCommand(
            booking_id=booking_id,
            amount_cents=request.amount_cents,
            payment_method=request.payment_method,
            payment_reference=request.payment_reference,
            notes=request.notes,
            processed_by=str(current_user.id),
            idempotency_key=f"payment_{booking_id}_{current_user.id}_{hash(str(request.dict()))}"
        )

        result = await command_bus.execute(command, db)

        await audit_log_action(
            "RECORD_PAYMENT",
            current_user,
            db,
            resource_type="payment",
            resource_id=result.data.get('payment_id') if result.success else None,
            details={
                "booking_id": str(booking_id),
                "amount_cents": request.amount_cents,
                "payment_method": request.payment_method,
                "payment_reference": request.payment_reference
            },
            success=result.success,
            error_message=result.error
        )

        return handle_command_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while recording the payment"
        )


@router.get("/customers", response_model=ApiResponse)
@require_permission(Permission.CUSTOMER_READ)
async def get_customer_360(
    customer_id: Optional[UUID] = Query(None, description="Customer ID"),
    customer_email: Optional[str] = Query(None, description="Customer email"),
    customer_phone: Optional[str] = Query(None, description="Customer phone"),
    include_bookings: bool = Query(True, description="Include booking history"),
    include_payments: bool = Query(True, description="Include payment history"),
    include_messages: bool = Query(True, description="Include message threads"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get comprehensive customer view."""

    try:
        query = GetCustomer360Query(
            customer_id=customer_id,
            customer_email=customer_email,
            customer_phone=customer_phone,
            include_bookings=include_bookings,
            include_payments=include_payments,
            include_messages=include_messages
        )

        result = await query_bus.execute(query, db)

        identifier = customer_id or customer_email or customer_phone
        await audit_log_action(
            "VIEW_CUSTOMER_360",
            current_user,
            db,
            resource_type="customer",
            resource_id=str(customer_id) if customer_id else None,
            details={
                "identifier": str(identifier),
                "includes": {
                    "bookings": include_bookings,
                    "payments": include_payments,
                    "messages": include_messages
                }
            },
            success=result.success,
            error_message=result.error
        )

        return handle_query_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving customer information"
        )


@router.get("/messages/threads", response_model=ApiResponse)
@require_permission(Permission.MESSAGE_READ)
async def get_message_threads(
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    phone_number: Optional[str] = Query(None, description="Filter by phone number"),
    has_unread: Optional[bool] = Query(None, description="Filter by unread status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get message threads with filtering."""

    try:
        query = GetMessageThreadsQuery(
            customer_id=customer_id,
            phone_number=phone_number,
            has_unread=has_unread,
            page=page,
            page_size=page_size
        )

        result = await query_bus.execute(query, db)

        await audit_log_action(
            "LIST_MESSAGE_THREADS",
            current_user,
            db,
            details={
                "filters": {
                    "customer_id": str(customer_id) if customer_id else None,
                    "phone_number": phone_number,
                    "has_unread": has_unread
                },
                "pagination": {"page": page, "page_size": page_size}
            },
            success=result.success,
            error_message=result.error
        )

        return handle_query_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving message threads"
        )


@router.get("/messages/threads/{thread_id}", response_model=ApiResponse)
@require_permission(Permission.MESSAGE_READ)
async def get_message_thread(
    thread_id: UUID,
    include_customer_details: bool = Query(True, description="Include customer details"),
    include_booking_context: bool = Query(True, description="Include booking context"),
    limit: int = Query(50, ge=1, le=200, description="Number of messages to retrieve"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get message thread with history."""

    try:
        query = GetMessageThreadQuery(
            thread_id=thread_id,
            include_customer_details=include_customer_details,
            include_booking_context=include_booking_context,
            limit=limit
        )

        result = await query_bus.execute(query, db)

        await audit_log_action(
            "VIEW_MESSAGE_THREAD",
            current_user,
            db,
            resource_type="message_thread",
            resource_id=str(thread_id),
            details={
                "include_customer_details": include_customer_details,
                "include_booking_context": include_booking_context,
                "limit": limit
            },
            success=result.success,
            error_message=result.error
        )

        return handle_query_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the message thread"
        )


@router.post("/messages/threads/{thread_id}/send", response_model=ApiResponse)
@require_permission(Permission.MESSAGE_SEND)
@rate_limit(max_requests=30, window_seconds=60, per_user=True)  # 30 messages per minute
async def send_message(
    thread_id: UUID,
    request: SendMessageRequest,
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Send a message in an existing thread."""

    try:
        command = SendMessageCommand(
            thread_id=thread_id,
            content=request.content,
            sent_by=str(current_user.id),
            idempotency_key=f"send_message_{thread_id}_{current_user.id}_{hash(request.content)}"
        )

        result = await command_bus.execute(command, db)

        await audit_log_action(
            "SEND_MESSAGE",
            current_user,
            db,
            resource_type="message",
            resource_id=result.data.get('message_id') if result.success else None,
            details={
                "thread_id": str(thread_id),
                "content_length": len(request.content)
            },
            success=result.success,
            error_message=result.error
        )

        return handle_command_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending the message"
        )


@router.get("/availability", response_model=ApiResponse)
async def get_availability_slots(
    date: date_type = Query(..., description="Date to check availability"),
    party_size: int = Query(..., ge=1, le=50, description="Number of guests"),
    duration_minutes: int = Query(180, ge=60, le=480, description="Event duration in minutes"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get available time slots for a date."""

    try:
        query = GetAvailabilitySlotsQuery(
            date=date,
            party_size=party_size,
            duration_minutes=duration_minutes
        )

        result = await query_bus.execute(query, db)

        return handle_query_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while checking availability"
        )


@router.get("/dashboard/stats", response_model=ApiResponse)
@require_any_permission([Permission.REPORTS_VIEW, Permission.BOOKING_READ])
async def get_dashboard_stats(
    date_from: Optional[date_type] = Query(None, description="Stats from date"),
    date_to: Optional[date_type] = Query(None, description="Stats to date"),
    include_bookings: bool = Query(True, description="Include booking statistics"),
    include_revenue: bool = Query(True, description="Include revenue statistics"),
    include_messages: bool = Query(True, description="Include message statistics"),
    current_user: AuthenticatedUser = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get dashboard statistics."""

    try:
        query = GetDashboardStatsQuery(
            date_from=date_from,
            date_to=date_to,
            include_bookings=include_bookings,
            include_revenue=include_revenue,
            include_messages=include_messages
        )

        result = await query_bus.execute(query, db)

        await audit_log_action(
            "VIEW_DASHBOARD_STATS",
            current_user,
            db,
            details={
                "date_range": {
                    "from": str(date_from) if date_from else None,
                    "to": str(date_to) if date_to else None
                },
                "includes": {
                    "bookings": include_bookings,
                    "revenue": include_revenue,
                    "messages": include_messages
                }
            },
            success=result.success,
            error_message=result.error
        )

        return handle_query_result(result)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving dashboard statistics"
        )


__all__ = ["router"]
