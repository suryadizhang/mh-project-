"""
Example Endpoint Refactoring
Demonstrates enterprise patterns: Service Layer + DTOs + Caching + DI

This shows the transformation from a typical endpoint to an enterprise-grade endpoint.
"""

from datetime import date
from uuid import UUID

# Service and Repository imports
from api.app.services.booking_service import BookingService
from core.cache import CacheService
from core.container import DependencyInjectionContainer

# Core imports
from core.dtos import (
    ApiResponse,
    PaginatedResponse,
    create_paginated_response,
    create_success_response,
)
from core.exceptions import (
    BusinessLogicException,
    ConflictException,
    NotFoundException,
)
from fastapi import APIRouter, Depends, Query, status

# Models and Schemas
# Note: These schemas need to be created based on your actual booking model
# from api.v1.bookings.schemas import (
#     BookingResponse,
#     BookingCreate,
#     BookingUpdate,
#     BookingListFilters
# )
from pydantic import BaseModel
from repositories.booking_repository import BookingRepository
from sqlalchemy.orm import Session


# Placeholder schemas (replace with your actual schemas)
class BookingResponse(BaseModel):
    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    customer_id: UUID
    event_date: date
    event_time: str
    party_size: int


router = APIRouter(prefix="/api/v1/bookings", tags=["bookings"])


# ============================================================================
# DEPENDENCY PROVIDERS
# ============================================================================


async def get_db() -> Session:
    """Database session dependency"""
    # Implementation from your existing code


async def get_container() -> DependencyInjectionContainer:
    """Get DI container from app state"""
    # Implementation from your existing code


async def get_cache() -> CacheService:
    """Get cache service from app state"""
    # Implementation from your existing code


async def get_booking_service(
    db: Session = Depends(get_db), cache: CacheService = Depends(get_cache)
) -> BookingService:
    """
    Provide BookingService with dependencies

    This is a factory function that creates a BookingService instance
    with all required dependencies injected.
    """
    repository = BookingRepository(session=db)
    return BookingService(repository=repository, cache=cache)


# ============================================================================
# ❌ BEFORE: Old Pattern (NOT RECOMMENDED)
# ============================================================================

# This is what your endpoints might look like currently:
# - Mixed concerns (routing + business logic + data access)
# - No caching
# - Inconsistent responses
# - Hard to test

"""
@router.get("/bookings/old")
async def get_bookings_old(
    db: Session = Depends(get_db),
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    customer_id: Optional[str] = None
):
    # Business logic mixed with data access
    query = db.query(Booking)

    # Filtering logic in endpoint
    if status:
        query = query.filter(Booking.status == status)
    if customer_id:
        query = query.filter(Booking.customer_id == customer_id)

    # Pagination logic in endpoint
    total = query.count()
    bookings = query.offset((page - 1) * per_page).limit(per_page).all()

    # Manual response construction
    return {
        "items": [booking.dict() for booking in bookings],
        "total": total,
        "page": page,
        "per_page": per_page
    }

@router.post("/bookings/old")
async def create_booking_old(
    data: BookingCreate,
    db: Session = Depends(get_db)
):
    # Validation logic in endpoint
    if data.event_date < date.today():
        return JSONResponse(
            status_code=400,
            content={"error": "Cannot book events in the past"}
        )

    # Data access logic in endpoint
    booking = Booking(**data.dict())
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Inconsistent response format
    return {"booking": booking.dict()}
"""


# ============================================================================
# ✅ AFTER: Enterprise Pattern (RECOMMENDED)
# ============================================================================


@router.get(
    "",
    response_model=PaginatedResponse[BookingResponse],
    summary="List bookings with pagination",
    description="Get a paginated list of bookings with optional filtering",
)
async def list_bookings(
    service: BookingService = Depends(get_booking_service),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str | None = Query(None, description="Filter by status"),
    customer_id: UUID | None = Query(None, description="Filter by customer"),
    start_date: date | None = Query(None, description="Start of date range"),
    end_date: date | None = Query(None, description="End of date range"),
) -> dict:
    """
    ✅ Endpoint concerns ONLY:
    - Request validation (via Pydantic)
    - Dependency injection
    - Response formatting

    ✅ Business logic in SERVICE layer
    ✅ Data access in REPOSITORY layer
    ✅ Consistent response via DTOs
    """
    # Delegate to service layer
    result = await service.get_bookings_paginated(
        page=page,
        per_page=per_page,
        status=status,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
    )

    # Return standardized response
    return create_paginated_response(
        items=[BookingResponse.from_orm(b) for b in result.items],
        total_items=result.total_count,
        page=page,
        per_page=per_page,
        message="Bookings retrieved successfully",
    )


@router.get(
    "/stats",
    response_model=ApiResponse[dict],
    summary="Get booking statistics",
    description="Get cached dashboard statistics (cached for 5 minutes)",
)
async def get_booking_stats(
    service: BookingService = Depends(get_booking_service),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
) -> dict:
    """
    ✅ Demonstrates caching:
    - Service layer handles caching automatically
    - Expensive queries are cached
    - No caching logic in endpoint
    """
    stats = await service.get_dashboard_stats(start_date=start_date, end_date=end_date)

    return create_success_response(data=stats, message="Statistics retrieved successfully")


@router.get(
    "/{booking_id}",
    response_model=ApiResponse[BookingResponse],
    summary="Get booking by ID",
    responses={404: {"description": "Booking not found"}},
)
async def get_booking(
    booking_id: UUID, service: BookingService = Depends(get_booking_service)
) -> dict:
    """
    ✅ Demonstrates error handling:
    - Service raises typed exceptions
    - Middleware handles conversion to HTTP responses
    - Consistent error responses
    """
    try:
        booking = await service.get_booking_by_id(booking_id)

        return create_success_response(
            data=BookingResponse.from_orm(booking), message="Booking retrieved successfully"
        )
    except NotFoundException:
        # Middleware will convert this to proper HTTP response
        raise


@router.post(
    "",
    response_model=ApiResponse[BookingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new booking",
    responses={
        201: {"description": "Booking created successfully"},
        400: {"description": "Invalid booking data"},
        409: {"description": "Time slot not available"},
    },
)
async def create_booking(
    data: BookingCreate, service: BookingService = Depends(get_booking_service)
) -> dict:
    """
    ✅ Demonstrates:
    - Validation via Pydantic (automatic)
    - Business rules in service layer
    - Cache invalidation (automatic)
    - Typed exceptions for errors
    """
    try:
        booking = await service.create_booking(
            customer_id=data.customer_id,
            event_date=data.event_date,
            event_time=data.event_time,
            party_size=data.party_size,
            **data.dict(exclude={"customer_id", "event_date", "event_time", "party_size"}),
        )

        return create_success_response(
            data=BookingResponse.from_orm(booking), message="Booking created successfully"
        )
    except (BusinessLogicException, ConflictException):
        # Middleware will convert to appropriate HTTP response
        raise


@router.put(
    "/{booking_id}/confirm",
    response_model=ApiResponse[BookingResponse],
    summary="Confirm a pending booking",
    responses={
        404: {"description": "Booking not found"},
        400: {"description": "Booking cannot be confirmed"},
    },
)
async def confirm_booking(
    booking_id: UUID, service: BookingService = Depends(get_booking_service)
) -> dict:
    """
    ✅ Demonstrates state transitions:
    - Business rules enforced in service
    - Optimistic concurrency handling
    - Cache invalidation
    """
    try:
        booking = await service.confirm_booking(booking_id)

        return create_success_response(
            data=BookingResponse.from_orm(booking), message="Booking confirmed successfully"
        )
    except (NotFoundException, BusinessLogicException):
        raise


@router.delete(
    "/{booking_id}",
    response_model=ApiResponse[dict],
    summary="Cancel a booking",
    responses={
        404: {"description": "Booking not found"},
        400: {"description": "Booking cannot be cancelled"},
    },
)
async def cancel_booking(
    booking_id: UUID,
    reason: str | None = Query(None, description="Cancellation reason"),
    service: BookingService = Depends(get_booking_service),
) -> dict:
    """
    ✅ Demonstrates:
    - Business rule validation (24-hour policy)
    - Audit trail (reason tracking)
    - Cache invalidation
    """
    try:
        booking = await service.cancel_booking(booking_id=booking_id, reason=reason)

        return create_success_response(
            data={"id": str(booking.id), "status": booking.status},
            message="Booking cancelled successfully",
        )
    except (NotFoundException, BusinessLogicException):
        raise


# ============================================================================
# BENEFITS OF THE NEW PATTERN
# ============================================================================

"""
✅ SEPARATION OF CONCERNS:
   - Endpoints: Routing, validation, response formatting
   - Service: Business logic, orchestration
   - Repository: Data access, queries
   - Models: Data structure

✅ TESTABILITY:
   - Service can be unit tested with mock repository
   - Repository can be tested with test database
   - Endpoints can be integration tested

✅ MAINTAINABILITY:
   - Business logic changes don't affect endpoints
   - Data access changes don't affect service
   - Easy to understand and modify

✅ PERFORMANCE:
   - Caching handled in service layer
   - N+1 queries prevented in repository
   - Expensive operations are cached automatically

✅ CONSISTENCY:
   - All responses follow same format
   - All errors handled consistently
   - All endpoints follow same patterns

✅ SECURITY:
   - Input validation via Pydantic
   - Authorization can be added to service layer
   - Audit logging in one place

✅ SCALABILITY:
   - Easy to add new endpoints
   - Easy to add new business logic
   - Easy to optimize hot paths
"""


# ============================================================================
# MIGRATION STRATEGY
# ============================================================================

"""
How to refactor your existing endpoints:

1. Create service class (e.g., BookingService)
2. Move business logic from endpoint to service
3. Update endpoint to use service
4. Add caching decorators to service methods
5. Use standardized DTOs for responses
6. Run tests to ensure no regression

Example migration order:
1. Start with GET endpoints (read-only, safer)
2. Move to POST/PUT endpoints (more complex)
3. Update all endpoints in one domain at a time
4. Keep old endpoints for backward compatibility
5. Deprecate old endpoints after migration

Estimated time per endpoint: 30-60 minutes
Total time for 20 endpoints: 1-2 weeks
"""
