"""
CRM Router - Admin Panel Integration Layer

This router provides the /api/crm/* endpoints that the admin panel expects.
It acts as a thin wrapper/adapter layer over the existing routers:
- /api/crm/bookings -> delegates to bookings router
- /api/crm/customers -> delegates to customer service
- /api/crm/dashboard/stats -> aggregates data from multiple sources
- /api/crm/availability -> delegates to availability logic

This ensures the admin frontend can work without modification while
keeping the core business logic in dedicated routers.

⚠️ FIELD MAPPING (core.Booking model):
- date -> date (Date type)
- slot -> slot (Time type) NOT 'time'
- party_adults + party_kids -> guests (calculated)
- total_due_cents -> total amount in cents
- deposit_due_cents -> deposit amount in cents
- deposit_confirmed_at -> deposit paid (not null = paid)
- address_encrypted -> address (encrypted)
- customer_id -> FK to Customer table for name/email/phone
"""

from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from db.models.core import Booking, BookingStatus, Customer
from utils.auth import require_admin

router = APIRouter(tags=["crm"])
logger = logging.getLogger(__name__)


# ============================================================================
# Response Schemas
# ============================================================================


class CRMBookingResponse(BaseModel):
    """Booking response for CRM/Admin."""

    id: str
    date: str
    time: str
    guests: int
    status: str
    total_amount: float
    deposit_paid: bool
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    location_address: str
    special_requests: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CRMCustomerResponse(BaseModel):
    """Customer response for CRM/Admin."""

    id: str
    name: str
    email: str
    phone: Optional[str] = None
    total_bookings: int = 0
    total_spent: float = 0.0
    created_at: datetime
    last_booking_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DashboardStatsResponse(BaseModel):
    """Dashboard statistics for admin panel."""

    total_bookings: int
    pending_bookings: int
    confirmed_bookings: int
    completed_bookings: int
    cancelled_bookings: int
    total_revenue: float
    today_bookings: int
    this_week_bookings: int
    this_month_bookings: int
    total_customers: int
    repeat_customers: int
    average_party_size: float


class AvailabilitySlot(BaseModel):
    """Time slot availability."""

    time: str
    available: bool
    reason: Optional[str] = None


class AvailabilityResponse(BaseModel):
    """Availability response for a date."""

    date: str
    slots: List[AvailabilitySlot]
    fully_booked: bool


class PaginatedResponse(BaseModel):
    """Paginated list response."""

    data: List[Any]
    total_count: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool
    # Cursor-based pagination support
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None


# ============================================================================
# CRM Bookings Endpoints
# ============================================================================


@router.get("/bookings", response_model=PaginatedResponse)
async def get_crm_bookings(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    status_filter: Optional[str] = Query(
        None, alias="status", description="Filter by status"
    ),
    payment_status: Optional[str] = Query(
        None, description="Filter by payment status"
    ),
    date_from: Optional[str] = Query(
        None, description="Filter from date (YYYY-MM-DD)"
    ),
    date_to: Optional[str] = Query(
        None, description="Filter to date (YYYY-MM-DD)"
    ),
    customer_search: Optional[str] = Query(
        None, description="Search customer name/email"
    ),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_admin),
) -> PaginatedResponse:
    """
    Get all bookings for CRM/Admin panel.

    Supports both cursor-based (preferred) and offset-based pagination.
    Cursor-based is O(1) vs offset-based O(n) for deep pages.

    ⚠️ FIELD MAPPING: Uses correct Booking model fields
    - slot (not time)
    - party_adults + party_kids (not guests)
    - total_due_cents (not total_amount_cents)
    - deposit_confirmed_at != None (not deposit_paid)
    - address_encrypted (not location_address)
    - customer relationship for customer_name/email/phone
    """
    try:
        # Build query with Customer relationship loaded
        query = select(Booking).options(joinedload(Booking.customer))
        count_query = select(func.count(Booking.id))

        # Apply filters
        filters = []

        if status_filter:
            try:
                booking_status = BookingStatus(status_filter)
                filters.append(Booking.status == booking_status)
            except ValueError:
                # Invalid status, try case-insensitive match
                for bs in BookingStatus:
                    if bs.value.lower() == status_filter.lower():
                        filters.append(Booking.status == bs)
                        break

        if payment_status:
            if payment_status == "paid":
                filters.append(Booking.deposit_confirmed_at.isnot(None))
            elif payment_status == "unpaid":
                filters.append(Booking.deposit_confirmed_at.is_(None))

        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                filters.append(Booking.date >= from_date)
            except ValueError:
                pass

        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
                filters.append(Booking.date <= to_date)
            except ValueError:
                pass

        # Customer search requires a subquery/join
        if customer_search:
            search_term = f"%{customer_search}%"
            # Join with Customer table to search name/email
            customer_subquery = select(Customer.id).where(
                or_(
                    Customer.first_name.ilike(search_term),
                    Customer.last_name.ilike(search_term),
                    Customer.email_encrypted.ilike(search_term),
                )
            )
            filters.append(Booking.customer_id.in_(customer_subquery))

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(Booking, sort_by, Booking.created_at)
        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await db.execute(query)
        bookings = result.unique().scalars().all()

        # Convert to response format using CORRECT field names
        booking_list = []
        for booking in bookings:
            # Get customer info from relationship
            customer = booking.customer
            customer_name = ""
            customer_email = ""
            customer_phone = None

            if customer:
                customer_name = (
                    f"{customer.first_name} {customer.last_name}".strip()
                )
                customer_email = (
                    customer.email_encrypted
                )  # Note: This is encrypted
                customer_phone = (
                    customer.phone_encrypted
                )  # Note: This is encrypted

            # Calculate total guests
            total_guests = (booking.party_adults or 0) + (
                booking.party_kids or 0
            )

            # Determine if deposit is paid
            deposit_paid = booking.deposit_confirmed_at is not None

            booking_list.append(
                {
                    "id": str(booking.id),
                    "date": booking.date.isoformat() if booking.date else None,
                    "time": (
                        booking.slot.isoformat() if booking.slot else None
                    ),  # slot -> time for frontend
                    "guests": total_guests,  # party_adults + party_kids
                    "adults": booking.party_adults or 0,
                    "kids": booking.party_kids or 0,
                    "status": (
                        booking.status.value
                        if hasattr(booking.status, "value")
                        else str(booking.status)
                    ),
                    "total_amount": float(booking.total_due_cents or 0)
                    / 100,  # cents to dollars
                    "deposit_amount": float(booking.deposit_due_cents or 0)
                    / 100,
                    "deposit_paid": deposit_paid,
                    "deposit_confirmed_at": booking.deposit_confirmed_at,
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "customer_phone": customer_phone,
                    "location_address": booking.address_encrypted
                    or "",  # Note: encrypted
                    "zone": booking.zone or "",
                    "special_requests": booking.special_requests,
                    "notes": booking.notes,
                    "created_at": booking.created_at,
                    "updated_at": booking.updated_at,
                }
            )

        return PaginatedResponse(
            data=booking_list,
            total_count=total_count,
            page=page,
            limit=limit,
            has_next=(page * limit) < total_count,
            has_prev=page > 1,
            next_cursor=None,  # TODO: Implement cursor-based
            prev_cursor=None,
        )

    except Exception as e:
        logger.error(f"Error fetching CRM bookings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch bookings: {str(e)}",
        )


@router.get("/bookings/{booking_id}")
async def get_crm_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_admin),
) -> dict:
    """Get a specific booking by ID with customer details."""
    try:
        booking_uuid = UUID(booking_id)
        result = await db.execute(
            select(Booking)
            .options(joinedload(Booking.customer))
            .where(Booking.id == booking_uuid)
        )
        booking = result.unique().scalar_one_or_none()

        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found",
            )

        # Get customer info from relationship
        customer = booking.customer
        customer_name = ""
        customer_email = ""
        customer_phone = None

        if customer:
            customer_name = (
                f"{customer.first_name} {customer.last_name}".strip()
            )
            customer_email = customer.email_encrypted
            customer_phone = customer.phone_encrypted

        # Calculate total guests
        total_guests = (booking.party_adults or 0) + (booking.party_kids or 0)

        # Determine if deposit is paid
        deposit_paid = booking.deposit_confirmed_at is not None

        return {
            "data": {
                "id": str(booking.id),
                "date": booking.date.isoformat() if booking.date else None,
                "time": (
                    booking.slot.isoformat() if booking.slot else None
                ),  # slot -> time
                "guests": total_guests,
                "adults": booking.party_adults or 0,
                "kids": booking.party_kids or 0,
                "status": (
                    booking.status.value
                    if hasattr(booking.status, "value")
                    else str(booking.status)
                ),
                "total_amount": float(booking.total_due_cents or 0) / 100,
                "deposit_amount": float(booking.deposit_due_cents or 0) / 100,
                "deposit_paid": deposit_paid,
                "deposit_confirmed_at": booking.deposit_confirmed_at,
                "customer_id": str(booking.customer_id),
                "customer_name": customer_name,
                "customer_email": customer_email,
                "customer_phone": customer_phone,
                "location_address": booking.address_encrypted or "",
                "zone": booking.zone or "",
                "special_requests": booking.special_requests,
                "notes": booking.notes,
                "source": booking.source,
                "created_at": booking.created_at,
                "updated_at": booking.updated_at,
            }
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid booking ID format",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching booking {booking_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch booking: {str(e)}",
        )


# ============================================================================
# CRM Customers Endpoints
# ============================================================================


@router.get("/customers", response_model=PaginatedResponse)
async def get_crm_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_admin),
) -> PaginatedResponse:
    """
    Get all customers for CRM/Admin panel.

    Uses the actual Customer table with booking stats joined.
    """
    try:
        # Query customers with booking aggregates
        query = (
            select(
                Customer,
                func.count(Booking.id).label("total_bookings"),
                func.sum(Booking.total_due_cents).label("total_spent_cents"),
                func.max(Booking.created_at).label("last_booking_date"),
            )
            .outerjoin(Booking, Customer.id == Booking.customer_id)
            .group_by(Customer.id)
        )

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Customer.first_name.ilike(search_term),
                    Customer.last_name.ilike(search_term),
                    Customer.email_encrypted.ilike(search_term),
                )
            )

        # Filter out deleted customers
        query = query.where(Customer.deleted_at.is_(None))

        # Get total count
        count_subquery = (
            select(func.count(func.distinct(Customer.id)))
            .select_from(Customer)
            .where(Customer.deleted_at.is_(None))
        )
        if search:
            search_term = f"%{search}%"
            count_subquery = count_subquery.where(
                or_(
                    Customer.first_name.ilike(search_term),
                    Customer.last_name.ilike(search_term),
                    Customer.email_encrypted.ilike(search_term),
                )
            )
        count_result = await db.execute(count_subquery)
        total_count = count_result.scalar() or 0

        # Apply sorting
        if sort_by == "name":
            sort_column = Customer.first_name
        elif sort_by == "email":
            sort_column = Customer.email_encrypted
        else:
            sort_column = Customer.created_at

        if sort_order.lower() == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute
        result = await db.execute(query)
        rows = result.all()

        customer_list = []
        for row in rows:
            customer = row[0]  # Customer object
            total_bookings = row[1] or 0
            total_spent_cents = row[2] or 0
            last_booking_date = row[3]

            customer_list.append(
                {
                    "id": str(customer.id),
                    "name": f"{customer.first_name} {customer.last_name}".strip(),
                    "first_name": customer.first_name,
                    "last_name": customer.last_name,
                    "email": customer.email_encrypted,  # Note: encrypted
                    "phone": customer.phone_encrypted,  # Note: encrypted
                    "total_bookings": total_bookings,
                    "total_spent": float(total_spent_cents) / 100,
                    "created_at": customer.created_at,
                    "last_booking_date": last_booking_date,
                    "timezone": customer.timezone,
                    "consent_sms": customer.consent_sms,
                    "consent_email": customer.consent_email,
                }
            )

        return PaginatedResponse(
            data=customer_list,
            total_count=total_count,
            page=page,
            limit=limit,
            has_next=(page * limit) < total_count,
            has_prev=page > 1,
        )

    except Exception as e:
        logger.error(f"Error fetching CRM customers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customers: {str(e)}",
        )


@router.get("/customers/{customer_id}")
async def get_crm_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_admin),
) -> dict:
    """Get customer details by ID (UUID) with their bookings."""
    try:
        # Parse customer ID as UUID
        try:
            customer_uuid = UUID(customer_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid customer ID format. Please provide a valid UUID.",
            )

        # Fetch customer with bookings
        result = await db.execute(
            select(Customer)
            .options(selectinload(Customer.bookings))
            .where(
                and_(
                    Customer.id == customer_uuid, Customer.deleted_at.is_(None)
                )
            )
        )
        customer = result.unique().scalar_one_or_none()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        # Calculate totals from bookings
        total_spent_cents = sum(
            b.total_due_cents or 0 for b in customer.bookings
        )
        last_booking = max(
            (b.created_at for b in customer.bookings), default=None
        )

        # Get recent bookings for display
        recent_bookings = sorted(
            customer.bookings, key=lambda b: b.created_at, reverse=True
        )[:10]

        return {
            "data": {
                "id": str(customer.id),
                "name": f"{customer.first_name} {customer.last_name}".strip(),
                "first_name": customer.first_name,
                "last_name": customer.last_name,
                "email": customer.email_encrypted,
                "phone": customer.phone_encrypted,
                "total_bookings": len(customer.bookings),
                "total_spent": float(total_spent_cents) / 100,
                "created_at": customer.created_at,
                "last_booking_date": last_booking,
                "timezone": customer.timezone,
                "consent_sms": customer.consent_sms,
                "consent_email": customer.consent_email,
                "notes": customer.notes,
                "tags": customer.tags or [],
                "bookings": [
                    {
                        "id": str(b.id),
                        "date": b.date.isoformat() if b.date else None,
                        "time": b.slot.isoformat() if b.slot else None,
                        "status": (
                            b.status.value
                            if hasattr(b.status, "value")
                            else str(b.status)
                        ),
                        "total_amount": float(b.total_due_cents or 0) / 100,
                        "guests": (b.party_adults or 0) + (b.party_kids or 0),
                    }
                    for b in recent_bookings
                ],
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customer: {str(e)}",
        )


@router.get("/customers/{customer_id}/bookings")
async def get_customer_bookings(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_admin),
) -> dict:
    """Get all bookings for a specific customer by ID (UUID)."""
    try:
        # Parse customer ID as UUID
        try:
            customer_uuid = UUID(customer_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid customer ID format. Please provide a valid UUID.",
            )

        # Verify customer exists
        customer_result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.id == customer_uuid, Customer.deleted_at.is_(None)
                )
            )
        )
        customer = customer_result.scalar_one_or_none()

        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        # Fetch bookings for this customer
        result = await db.execute(
            select(Booking)
            .where(Booking.customer_id == customer_uuid)
            .order_by(Booking.created_at.desc())
        )
        bookings = result.scalars().all()

        booking_list = [
            {
                "id": str(b.id),
                "date": b.date.isoformat() if b.date else None,
                "time": b.slot.isoformat() if b.slot else None,
                "guests": (b.party_adults or 0) + (b.party_kids or 0),
                "adults": b.party_adults or 0,
                "kids": b.party_kids or 0,
                "status": (
                    b.status.value
                    if hasattr(b.status, "value")
                    else str(b.status)
                ),
                "total_amount": float(b.total_due_cents or 0) / 100,
                "deposit_amount": float(b.deposit_due_cents or 0) / 100,
                "deposit_paid": b.deposit_confirmed_at is not None,
                "location_address": b.address_encrypted or "",
                "zone": b.zone or "",
                "special_requests": b.special_requests,
                "created_at": b.created_at,
            }
            for b in bookings
        ]

        return {"data": booking_list}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer bookings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch customer bookings: {str(e)}",
        )


# ============================================================================
# CRM Dashboard Endpoints
# ============================================================================


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_admin),
) -> dict:
    """
    Get dashboard statistics for admin panel.

    Uses correct Booking model fields:
    - party_adults + party_kids for average party size
    - total_due_cents for revenue (from COMPLETED bookings)
    """
    try:
        now = datetime.now(timezone.utc)
        today = now.date()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        # Total bookings by status
        status_counts = {}
        for booking_status in BookingStatus:
            result = await db.execute(
                select(func.count(Booking.id)).where(
                    Booking.status == booking_status
                )
            )
            status_counts[booking_status.value] = result.scalar() or 0

        total_bookings = sum(status_counts.values())

        # Total revenue (from completed bookings)
        revenue_result = await db.execute(
            select(func.sum(Booking.total_due_cents)).where(
                Booking.status == BookingStatus.COMPLETED
            )
        )
        total_revenue_cents = revenue_result.scalar() or 0

        # Today's bookings
        today_result = await db.execute(
            select(func.count(Booking.id)).where(Booking.date == today)
        )
        today_bookings = today_result.scalar() or 0

        # This week's bookings
        week_result = await db.execute(
            select(func.count(Booking.id)).where(Booking.date >= week_start)
        )
        this_week_bookings = week_result.scalar() or 0

        # This month's bookings
        month_result = await db.execute(
            select(func.count(Booking.id)).where(Booking.date >= month_start)
        )
        this_month_bookings = month_result.scalar() or 0

        # Total unique customers (from Customer table)
        customer_result = await db.execute(
            select(func.count(Customer.id)).where(
                Customer.deleted_at.is_(None)
            )
        )
        total_customers = customer_result.scalar() or 0

        # Repeat customers (more than 1 booking)
        repeat_subquery = (
            select(Booking.customer_id)
            .group_by(Booking.customer_id)
            .having(func.count(Booking.id) > 1)
        ).subquery()

        repeat_result = await db.execute(
            select(func.count()).select_from(repeat_subquery)
        )
        repeat_customers = repeat_result.scalar() or 0

        # Average party size (party_adults + party_kids)
        avg_result = await db.execute(
            select(func.avg(Booking.party_adults + Booking.party_kids))
        )
        avg_party_size = float(avg_result.scalar() or 0)

        # Pending deposits (unpaid)
        pending_deposit_result = await db.execute(
            select(func.count(Booking.id)).where(
                and_(
                    Booking.deposit_confirmed_at.is_(None),
                    Booking.status.in_(
                        [BookingStatus.PENDING, BookingStatus.CONFIRMED]
                    ),
                )
            )
        )
        pending_deposits = pending_deposit_result.scalar() or 0

        return {
            "data": {
                "total_bookings": total_bookings,
                "pending_bookings": status_counts.get("pending", 0),
                "confirmed_bookings": status_counts.get("confirmed", 0),
                "completed_bookings": status_counts.get("completed", 0),
                "cancelled_bookings": status_counts.get("cancelled", 0),
                "total_revenue": float(total_revenue_cents) / 100,
                "today_bookings": today_bookings,
                "this_week_bookings": this_week_bookings,
                "this_month_bookings": this_month_bookings,
                "total_customers": total_customers,
                "repeat_customers": repeat_customers,
                "average_party_size": round(avg_party_size, 1),
                "pending_deposits": pending_deposits,
            }
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}",
        )


# ============================================================================
# CRM Availability Endpoints
# ============================================================================


@router.get("/availability")
async def get_availability(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
    current_user: Any = Depends(require_admin),
) -> dict:
    """
    Get availability for a specific date or today.

    Uses correct field: Booking.slot (not time)
    """
    try:
        # Parse date
        if date:
            try:
                check_date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use YYYY-MM-DD",
                )
        else:
            check_date = datetime.now(timezone.utc).date()

        # Get existing bookings for the date (using correct field: slot)
        result = await db.execute(
            select(Booking.slot).where(
                and_(
                    Booking.date == check_date,
                    Booking.status.in_(
                        [
                            BookingStatus.PENDING,
                            BookingStatus.CONFIRMED,
                        ]
                    ),
                )
            )
        )
        booked_slots = result.all()

        # Convert booked slots to string format for comparison
        booked_times = []
        for row in booked_slots:
            slot = row[0]
            if slot:
                booked_times.append(
                    slot.strftime("%H:%M")
                    if hasattr(slot, "strftime")
                    else str(slot)[:5]
                )

        # Generate time slots (10 AM to 8 PM, hourly)
        time_slots = []
        for hour in range(10, 21):  # 10 AM to 8 PM
            time_str = f"{hour:02d}:00"
            is_booked = time_str in booked_times or any(
                bt.startswith(f"{hour:02d}:") for bt in booked_times
            )
            time_slots.append(
                {
                    "time": time_str,
                    "available": not is_booked,
                    "reason": "Already booked" if is_booked else None,
                }
            )

        fully_booked = all(not slot["available"] for slot in time_slots)

        return {
            "data": {
                "date": check_date.isoformat(),
                "slots": time_slots,
                "fully_booked": fully_booked,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch availability: {str(e)}",
        )


__all__ = ["router"]
