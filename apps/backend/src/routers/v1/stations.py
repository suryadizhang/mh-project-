"""
Public Stations API
===================

Public-facing station endpoints for listing and viewing stations.
This provides the /api/v1/stations routes expected by E2E tests.

For station management (create, update, delete), use /api/v1/admin/stations.

Endpoints:
    GET    /api/v1/stations           - List all active stations
    GET    /api/v1/stations/me        - Get current user's assigned station
    GET    /api/v1/stations/{id}      - Get station by ID
    POST   /api/v1/stations           - Create station (admin only, forwards to admin router)
"""

import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from core.security import decode_access_token
from db.models.identity import (
    Station,
    StationUser,
    User,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stations"])
security = HTTPBearer()


# =============================================================================
# Authentication Dependencies
# =============================================================================


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Get current user from JWT token.
    Validates token and fetches full User model from database.

    This is the industry-standard JWT authentication pattern used across all API endpoints.
    """
    from db.models.identity import UserStatus

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value.lower()}",
            )

        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user ID in token: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# Pydantic Schemas
# =============================================================================


class StationResponse(BaseModel):
    """Response model for station details."""

    id: UUID
    code: str
    name: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    status: str = "active"
    business_hours: Optional[dict[str, Any]] = None
    service_area_radius: Optional[int] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class StationListResponse(BaseModel):
    """Response for listing stations."""

    items: list[StationResponse]
    total: int


class StationCreateRequest(BaseModel):
    """Request model for creating a new station."""

    name: str = Field(..., min_length=1, max_length=100, description="Station name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Display name for UI")
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(..., min_length=2, max_length=2, description="2-letter state code")
    country: str = Field(default="US", min_length=2, max_length=2, description="Country code")
    timezone: str = Field(..., description="IANA timezone (e.g., America/Los_Angeles)")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    address: Optional[str] = Field(None, description="Street address")
    postal_code: Optional[str] = Field(None, max_length=20, description="ZIP/Postal code")
    status: str = Field(default="active", description="Station status")
    business_hours: Optional[dict[str, Any]] = Field(None, description="Operating hours JSON")
    service_area_radius: Optional[int] = Field(None, ge=0, description="Service radius in miles")
    max_concurrent_bookings: Optional[int] = Field(
        default=10, ge=1, description="Max concurrent bookings"
    )
    booking_lead_time_hours: Optional[int] = Field(
        default=24, ge=0, description="Minimum booking lead time"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "California Bay Area",
                "display_name": "MyHibachi - California Bay Area",
                "city": "Fremont",
                "state": "CA",
                "country": "US",
                "timezone": "America/Los_Angeles",
                "email": "bay-area@myhibachi.com",
            }
        }
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/", response_model=list[StationResponse])
async def list_stations(
    include_inactive: bool = Query(False, description="Include inactive stations"),
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> list[StationResponse]:
    """
    List all stations.

    By default, only shows active stations.
    Super admins can see all stations including inactive.
    Regular users can only see stations they're assigned to.

    **Authentication:** Requires valid JWT token (standard Bearer token auth).
    **Permissions:**
    - SUPER_ADMIN: Can view all stations, including inactive
    - Other roles: Can view active stations they're assigned to, or all active if no assignments
    """
    try:
        query = select(Station)

        # Filter by status unless super_admin requests inactive
        if not include_inactive or not current_user.is_super_admin:
            query = query.where(Station.status == "active")

        # Non-super_admin users only see their assigned stations
        if not current_user.is_super_admin:
            # Get user's assigned stations
            station_ids_result = await db.execute(
                select(StationUser.station_id).where(
                    and_(
                        StationUser.user_id == current_user.id,
                        StationUser.is_active,
                    )
                )
            )
            user_station_ids = [row[0] for row in station_ids_result.fetchall()]

            if user_station_ids:
                query = query.where(Station.id.in_(user_station_ids))
            else:
                # User has no station assignments - return all active (public view)
                pass

        query = query.order_by(Station.name)

        result = await db.execute(query)
        stations = result.scalars().all()

        return [
            StationResponse(
                id=s.id,
                code=s.code,
                name=s.name,
                display_name=s.display_name,
                email=s.email,
                phone=s.phone,
                address=s.address,
                city=s.city,
                state=s.state,
                postal_code=s.postal_code,
                country=s.country,
                timezone=s.timezone,
                status=s.status or "active",
                business_hours=s.business_hours,
                service_area_radius=s.service_area_radius,
                is_active=s.status == "active",
            )
            for s in stations
        ]

    except Exception as e:
        logger.error(f"Error listing stations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve stations",
        )


@router.get("/me", response_model=Optional[StationResponse])
async def get_my_station(
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> Optional[StationResponse]:
    """
    Get the current user's assigned station.

    Returns the first active station assignment for the user.

    **Authentication:** Requires valid JWT token.
    **Returns:** First active station user is assigned to, or None if no assignments.
    """
    try:
        result = await db.execute(
            select(Station)
            .join(StationUser, StationUser.station_id == Station.id)
            .where(
                and_(
                    StationUser.user_id == current_user.id,
                    StationUser.is_active,
                    Station.status == "active",
                )
            )
            .limit(1)
        )
        station = result.scalar_one_or_none()

        if not station:
            return None

        return StationResponse(
            id=station.id,
            code=station.code,
            name=station.name,
            display_name=station.display_name,
            email=station.email,
            phone=station.phone,
            address=station.address,
            city=station.city,
            state=station.state,
            postal_code=station.postal_code,
            country=station.country,
            timezone=station.timezone,
            status=station.status or "active",
            business_hours=station.business_hours,
            service_area_radius=station.service_area_radius,
            is_active=station.status == "active",
        )

    except Exception as e:
        logger.error(f"Error getting user's station: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve station",
        )


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(
    station_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> StationResponse:
    """
    Get a specific station by ID.

    **Authentication:** Requires valid JWT token.
    **Permissions:** All authenticated users can view station details.
    """
    try:
        result = await db.execute(select(Station).where(Station.id == station_id))
        station = result.scalar_one_or_none()

        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station not found",
            )

        # Check access for non-super_admin
        if not current_user.is_super_admin:
            # Check if user is assigned to this station
            assignment = await db.execute(
                select(StationUser).where(
                    and_(
                        StationUser.user_id == current_user.user_id,
                        StationUser.station_id == station_id,
                        StationUser.is_active,
                    )
                )
            )
            # Allow viewing even without assignment (public station info)
            # But log if they're not assigned
            if not assignment.scalar_one_or_none():
                logger.debug(f"User {current_user.user_id} viewing unassigned station {station_id}")

        return StationResponse(
            id=station.id,
            code=station.code,
            name=station.name,
            display_name=station.display_name,
            email=station.email,
            phone=station.phone,
            address=station.address,
            city=station.city,
            state=station.state,
            postal_code=station.postal_code,
            country=station.country,
            timezone=station.timezone,
            status=station.status or "active",
            business_hours=station.business_hours,
            service_area_radius=station.service_area_radius,
            is_active=station.status == "active",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting station: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve station",
        )


@router.post("/", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(
    request: StationCreateRequest,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_session),
) -> StationResponse:
    """
    Create a new station.

    Only super_admin can create stations.
    Station code is auto-generated based on location.

    **Authentication:** Requires valid JWT token with SUPER_ADMIN role.
    **Permissions:** SUPER_ADMIN only.
    """
    # Only super_admin can create
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create stations",
        )

    try:
        from utils.station_code_generator import generate_station_code

        # Auto-generate unique station code
        station_code = await generate_station_code(
            db=db,
            city=request.city,
            state=request.state,
            country=request.country,
        )

        logger.info(f"Generated station code: {station_code} for {request.city}, {request.state}")

        # Create station
        station = Station(
            code=station_code,
            name=request.name,
            display_name=request.display_name,
            email=request.email,
            phone=request.phone,
            address=request.address,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            country=request.country,
            timezone=request.timezone,
            status=request.status or "active",
            business_hours=request.business_hours,
            service_area_radius=request.service_area_radius,
            max_concurrent_bookings=request.max_concurrent_bookings or 10,
            booking_lead_time_hours=request.booking_lead_time_hours or 24,
        )

        db.add(station)
        await db.commit()
        await db.refresh(station)

        # Audit logging: Log station creation
        try:
            logger.info(
                "Audit: Station created",
                extra={
                    "action": "create_station",
                    "performed_by": str(current_user.id),
                    "performed_by_email": current_user.email,
                    "resource_type": "station",
                    "resource_id": str(station.id),
                    "details": {
                        "station_name": station.name,
                        "station_code": station_code,
                        "city": request.city,
                        "state": request.state,
                    },
                },
            )
        except Exception as audit_error:
            logger.warning(f"Audit logging failed for station creation: {audit_error}")

        logger.info(f"Created station: {station_code} (ID: {station.id})")

        return StationResponse(
            id=station.id,
            code=station_code,
            name=station.name,
            display_name=station.display_name,
            email=station.email,
            phone=station.phone,
            address=station.address,
            city=station.city,
            state=station.state,
            postal_code=station.postal_code,
            country=station.country,
            timezone=station.timezone,
            status=station.status or "active",
            business_hours=station.business_hours,
            service_area_radius=station.service_area_radius,
            is_active=True,
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating station: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create station: {str(e)}",
        )
