"""
Sample API Endpoints demonstrating the new architectural patterns
This file tests integration of DI container, repository pattern, and error handling
"""

from datetime import date, datetime
from typing import Any

# Import our new architectural components
from api.deps_enhanced import (
    PaginationParams,
    get_admin_booking_context,
    get_authenticated_booking_service,
    get_customer_service_context,
    get_pagination_params,
)
from core.exceptions import create_success_response, raise_not_found
from fastapi import APIRouter, Depends
from models.booking import BookingStatus
from models.customer import CustomerStatus
from pydantic import BaseModel, Field

# Create router
router = APIRouter(prefix="/test", tags=["Testing - New Architecture"])

# Pydantic models for request/response


class CreateBookingRequest(BaseModel):
    """Request model for creating a booking"""

    customer_id: int = Field(..., description="Customer ID")
    booking_datetime: datetime = Field(..., description="Booking date and time")
    party_size: int = Field(..., ge=1, le=20, description="Party size (1-20)")
    special_requests: str | None = Field(None, max_length=1000, description="Special requests")
    contact_phone: str | None = Field(None, max_length=20, description="Contact phone")
    contact_email: str | None = Field(None, max_length=255, description="Contact email")


class BookingResponse(BaseModel):
    """Response model for booking data"""

    id: int
    customer_id: int
    booking_datetime: datetime
    party_size: int
    status: str
    special_requests: str | None
    contact_phone: str | None
    contact_email: str | None
    created_at: datetime
    updated_at: datetime


class CreateCustomerRequest(BaseModel):
    """Request model for creating a customer"""

    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: str = Field(..., max_length=255, description="Email address")
    phone: str | None = Field(None, max_length=20, description="Phone number")
    dietary_preferences: list[str] | None = Field(None, description="Dietary preferences")
    email_notifications: bool = Field(True, description="Email notifications preference")
    sms_notifications: bool = Field(False, description="SMS notifications preference")


class CustomerResponse(BaseModel):
    """Response model for customer data"""

    id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    status: str
    loyalty_points: int
    total_visits: int
    total_spent: int
    created_at: datetime
    updated_at: datetime


# Booking Endpoints (testing repository pattern with business logic)


@router.post("/bookings", response_model=dict[str, Any])
async def create_booking(
    request: CreateBookingRequest, context=Depends(get_authenticated_booking_service)
) -> dict[str, Any]:
    """
    Create a new booking
    Tests: DI container, repository pattern, business validation, error handling
    """
    current_user, booking_repo = context

    try:
        # Use repository business logic method
        booking = booking_repo.create_booking(
            customer_id=request.customer_id,
            booking_datetime=request.booking_datetime,
            party_size=request.party_size,
            special_requests=request.special_requests,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email,
        )

        # Convert to response format
        booking_data = {
            "id": booking.id,
            "customer_id": booking.customer_id,
            "booking_datetime": booking.booking_datetime.isoformat(),
            "party_size": booking.party_size,
            "status": booking.status.value,
            "special_requests": booking.special_requests,
            "contact_phone": booking.contact_phone,
            "contact_email": booking.contact_email,
            "created_at": booking.created_at.isoformat(),
            "updated_at": booking.updated_at.isoformat(),
        }

        return create_success_response(data=booking_data, message="Booking created successfully")

    except Exception:
        # Our error handling middleware will catch and format this
        raise


@router.get("/bookings/{booking_id}", response_model=dict[str, Any])
async def get_booking(
    booking_id: int, context=Depends(get_authenticated_booking_service)
) -> dict[str, Any]:
    """
    Get a specific booking
    Tests: Repository pattern, error handling for not found
    """
    current_user, booking_repo = context

    booking = booking_repo.get_by_id(booking_id)

    if not booking:
        raise_not_found("Booking", str(booking_id))

    booking_data = {
        "id": booking.id,
        "customer_id": booking.customer_id,
        "booking_datetime": booking.booking_datetime.isoformat(),
        "party_size": booking.party_size,
        "status": booking.status.value,
        "special_requests": booking.special_requests,
        "contact_phone": booking.contact_phone,
        "contact_email": booking.contact_email,
        "created_at": booking.created_at.isoformat(),
        "updated_at": booking.updated_at.isoformat(),
    }

    return create_success_response(data=booking_data)


@router.put("/bookings/{booking_id}/confirm", response_model=dict[str, Any])
async def confirm_booking(
    booking_id: int, context=Depends(get_admin_booking_context)
) -> dict[str, Any]:
    """
    Confirm a pending booking
    Tests: Admin authentication, business logic validation, state transitions
    """
    admin_user, booking_repo, pagination = context

    # Use repository business logic method
    booking = booking_repo.confirm_booking(booking_id)

    booking_data = {
        "id": booking.id,
        "status": booking.status.value,
        "confirmed_at": booking.confirmed_at.isoformat() if booking.confirmed_at else None,
        "updated_at": booking.updated_at.isoformat(),
    }

    return create_success_response(data=booking_data, message="Booking confirmed successfully")


@router.get("/bookings", response_model=dict[str, Any])
async def list_bookings(
    status: BookingStatus | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    context=Depends(get_admin_booking_context),
) -> dict[str, Any]:
    """
    List bookings with filtering
    Tests: Repository pattern with filtering, pagination, admin authentication
    """
    admin_user, booking_repo, pagination = context

    # Build search criteria
    search_criteria = {}

    if status:
        search_criteria["status"] = status

    if start_date or end_date:
        date_range = {}
        if start_date:
            date_range["start_date"] = start_date
        if end_date:
            date_range["end_date"] = end_date
        search_criteria["date_range"] = date_range

    # Use repository search method
    bookings, total_count = booking_repo.search_bookings(
        search_criteria=search_criteria, page=pagination.page, page_size=pagination.per_page
    )

    # Convert to response format
    booking_list = []
    for booking in bookings:
        booking_data = {
            "id": booking.id,
            "customer_id": booking.customer_id,
            "booking_datetime": booking.booking_datetime.isoformat(),
            "party_size": booking.party_size,
            "status": booking.status.value,
            "special_requests": booking.special_requests,
            "created_at": booking.created_at.isoformat(),
        }
        booking_list.append(booking_data)

    return create_success_response(
        data=booking_list,
        meta={
            "total_count": total_count,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": (total_count + pagination.per_page - 1) // pagination.per_page,
        },
    )


# Customer Endpoints (testing customer repository and validation)


@router.post("/customers", response_model=dict[str, Any])
async def create_customer(
    request: CreateCustomerRequest, context=Depends(get_customer_service_context)
) -> dict[str, Any]:
    """
    Create a new customer
    Tests: Customer repository validation, duplicate detection, business logic
    """
    current_user, customer_repo, business_context = context

    # Use repository creation method with validation
    customer = customer_repo.create_customer(
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        phone=request.phone,
        dietary_preferences=request.dietary_preferences,
        email_notifications=request.email_notifications,
        sms_notifications=request.sms_notifications,
    )

    customer_data = {
        "id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email,
        "phone": customer.phone,
        "status": customer.status.value,
        "loyalty_points": customer.loyalty_points,
        "total_visits": customer.total_visits,
        "total_spent": customer.total_spent,
        "created_at": customer.created_at.isoformat(),
        "updated_at": customer.updated_at.isoformat(),
    }

    return create_success_response(data=customer_data, message="Customer created successfully")


@router.get("/customers/search", response_model=dict[str, Any])
async def search_customers(
    q: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    status: CustomerStatus | None = None,
    context=Depends(get_customer_service_context),
    pagination: PaginationParams = Depends(get_pagination_params),
) -> dict[str, Any]:
    """
    Search customers
    Tests: Repository search functionality, multiple search criteria
    """
    current_user, customer_repo, business_context = context

    # Build search criteria
    search_criteria = {}

    if q:  # General search term
        search_criteria["name"] = q

    if email:
        search_criteria["email"] = email

    if phone:
        search_criteria["phone"] = phone

    if status:
        search_criteria["status"] = status

    # Use repository search method
    customers, total_count = customer_repo.search_customers(
        search_criteria=search_criteria, page=pagination.page, page_size=pagination.per_page
    )

    # Convert to response format
    customer_list = []
    for customer in customers:
        customer_data = {
            "id": customer.id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
            "phone": customer.phone,
            "status": customer.status.value,
            "loyalty_points": customer.loyalty_points,
            "total_visits": customer.total_visits,
            "last_visit_date": (
                customer.last_visit_date.isoformat() if customer.last_visit_date else None
            ),
        }
        customer_list.append(customer_data)

    return create_success_response(
        data=customer_list,
        meta={
            "total_count": total_count,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_pages": (total_count + pagination.per_page - 1) // pagination.per_page,
            "search_criteria": search_criteria,
        },
    )


@router.get("/customers/{customer_id}/bookings", response_model=dict[str, Any])
async def get_customer_bookings(
    customer_id: int,
    include_cancelled: bool = False,
    limit: int | None = 50,
    context=Depends(get_customer_service_context),
) -> dict[str, Any]:
    """
    Get customer booking history
    Tests: Repository relationships, business logic methods
    """
    current_user, customer_repo, business_context = context

    # Verify customer exists
    customer = customer_repo.get_by_id(customer_id)
    if not customer:
        raise_not_found("Customer", str(customer_id))

    # Get booking history using customer repository method
    booking_history = customer_repo.get_customer_booking_history(
        customer_id=customer_id, limit=limit
    )

    return create_success_response(
        data=booking_history, message=f"Booking history for customer {customer.full_name}"
    )


# Analytics Endpoints (testing repository analytics methods)


@router.get("/analytics/bookings", response_model=dict[str, Any])
async def get_booking_analytics(
    start_date: date, end_date: date, context=Depends(get_admin_booking_context)
) -> dict[str, Any]:
    """
    Get booking analytics
    Tests: Repository analytics methods, admin authentication
    """
    admin_user, booking_repo, pagination = context

    # Use repository analytics method
    stats = booking_repo.get_booking_statistics(start_date, end_date)

    return create_success_response(
        data=stats, message=f"Booking statistics for {start_date} to {end_date}"
    )


@router.get("/analytics/customers", response_model=dict[str, Any])
async def get_customer_analytics(context=Depends(get_customer_service_context)) -> dict[str, Any]:
    """
    Get customer analytics
    Tests: Repository analytics, customer segmentation
    """
    current_user, customer_repo, business_context = context

    # Get overall statistics
    stats = customer_repo.get_customer_statistics()

    # Get customer segments
    segments = customer_repo.get_customer_segments()

    return create_success_response(
        data={"statistics": stats, "segments": segments}, message="Customer analytics"
    )


# Health Check Endpoint (testing DI container status)


@router.get("/health", response_model=dict[str, Any])
async def health_check(
    booking_context=Depends(get_authenticated_booking_service),
    customer_context=Depends(get_customer_service_context),
) -> dict[str, Any]:
    """
    Health check endpoint
    Tests: DI container resolution, service availability
    """
    try:
        # Unpack contexts returned by the composed dependencies
        current_user, booking_repo = booking_context
        _, customer_repo, _ = customer_context

        # Test database connectivity
        booking_count = len(booking_repo.get_all(limit=1))
        customer_count = len(customer_repo.get_all(limit=1))

        return create_success_response(
            data={
                "status": "healthy",
                "services": {
                    "booking_repository": "available",
                    "customer_repository": "available",
                    "database": "connected",
                },
                "sample_counts": {
                    "bookings_accessible": booking_count >= 0,
                    "customers_accessible": customer_count >= 0,
                },
            },
            message="All services are healthy",
        )

    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "HEALTH_CHECK_FAILED",
                "message": f"Health check failed: {e!s}",
                "timestamp": datetime.utcnow().isoformat(),
            },
        }
