"""
Station Administration API
Comprehensive endpoints for managing stations, users, roles, and permissions.
"""

from datetime import datetime, timezone, timedelta
import logging
from typing import Any

from core.auth.station_middleware import (
    AuthenticatedUser,
    require_station_permission,
)
from core.auth.station_middleware import (
    audit_log_action as log_station_activity,
)

# Phase 1.1: Use canonical db.models.identity instead of deprecated station_models
from db.models.identity import (
    Station,
    StationAuditLog,
    StationUser,
)
from core.database import get_db_session
from utils.station_code_generator import (
    generate_station_code,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(tags=["station-admin"])


# Add a simple test endpoint without authentication
@router.get("/test", response_model=dict[str, Any])
async def test_endpoint(
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """Simple test endpoint to verify router is working."""
    try:
        # Test database connection
        result = await db.execute(select(func.count(Station.id)))
        station_count = result.scalar_one()

        return {
            "status": "success",
            "message": "Station Management API is operational",
            "station_count": station_count,
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {e}", exc_info=True)
        return {"status": "error", "message": str(e), "station_count": 0}


# Pydantic models for station management
class StationCreateRequest(BaseModel):
    """Request model for creating a new station (code is auto-generated)."""

    name: str = Field(..., min_length=1, max_length=100, description="Station name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Display name for UI")

    # Location (required for code generation)
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(
        ...,
        min_length=2,
        max_length=2,
        description="2-letter state code (e.g., CA, TX)",
    )
    country: str = Field(default="US", min_length=2, max_length=2, description="Country code")
    timezone: str = Field(..., description="IANA timezone (e.g., America/Los_Angeles)")

    # Optional contact & location details
    email: str | None = Field(None, description="Contact email")
    phone: str | None = Field(None, max_length=50, description="Contact phone")
    address: str | None = Field(None, description="Street address")
    postal_code: str | None = Field(None, max_length=20, description="ZIP/Postal code")

    # Business settings
    status: str | None = Field(default="active", description="Station status")
    settings: dict[str, Any] | None = Field(
        default_factory=dict, description="Station settings JSON"
    )
    business_hours: dict[str, Any] | None = Field(None, description="Operating hours JSON")
    service_area_radius: int | None = Field(None, ge=0, description="Service radius in miles")
    max_concurrent_bookings: int | None = Field(
        default=10, ge=1, description="Max concurrent bookings"
    )
    booking_lead_time_hours: int | None = Field(
        default=24, ge=0, description="Minimum booking lead time"
    )
    branding_config: dict[str, Any] | None = Field(None, description="Branding configuration JSON")

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
                "phone": "+1-510-555-0100",
                "address": "123 Mission Blvd",
                "postal_code": "94539",
                "status": "active",
                "business_hours": {
                    "monday": {"open": "10:00", "close": "22:00"},
                    "tuesday": {"open": "10:00", "close": "22:00"},
                    "wednesday": {"open": "10:00", "close": "22:00"},
                    "thursday": {"open": "10:00", "close": "22:00"},
                    "friday": {"open": "10:00", "close": "23:00"},
                    "saturday": {"open": "09:00", "close": "23:00"},
                    "sunday": {"open": "09:00", "close": "22:00"},
                },
                "max_concurrent_bookings": 15,
                "booking_lead_time_hours": 24,
            }
        }
    )


class StationUpdateRequest(BaseModel):
    """Request model for updating an existing station."""

    name: str | None = Field(None, min_length=1, max_length=100)
    display_name: str | None = Field(None, min_length=1, max_length=200)
    email: str | None = Field(None)
    phone: str | None = Field(None, max_length=50)
    address: str | None = Field(None)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=2)
    postal_code: str | None = Field(None, max_length=20)
    country: str | None = Field(None, max_length=2)
    timezone: str | None = Field(None)
    status: str | None = Field(
        None,
        description="Station status: active, inactive, suspended, maintenance",
    )
    settings: dict[str, Any] | None = Field(None)
    business_hours: dict[str, Any] | None = Field(None)
    service_area_radius: int | None = Field(None, ge=0, description="Service radius in miles")
    escalation_radius_miles: int | None = Field(
        None, ge=0, description="Distance beyond which bookings require human escalation"
    )
    max_concurrent_bookings: int | None = Field(None, ge=1)
    booking_lead_time_hours: int | None = Field(None, ge=0)
    branding_config: dict[str, Any] | None = Field(None)


class StationResponse(BaseModel):
    """Response model for station information."""

    id: str  # UUID as string
    code: str
    name: str
    display_name: str
    email: str | None
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    country: str
    timezone: str
    status: str
    settings: dict[str, Any]
    business_hours: dict[str, Any] | None
    service_area_radius: int | None
    escalation_radius_miles: int | None
    max_concurrent_bookings: int
    booking_lead_time_hours: int
    branding_config: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    # Geocoding fields
    lat: float | None = None
    lng: float | None = None
    geocoded_at: datetime | None = None
    geocode_status: str | None = None
    is_geocoded: bool = False
    full_address: str | None = None

    # Statistics (populated optionally)
    user_count: int | None = None
    active_booking_count: int | None = None
    total_booking_count: int | None = None
    last_activity: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserStationAssignmentRequest(BaseModel):
    """Request model for assigning users to stations."""

    user_id: int = Field(..., description="User ID to assign")
    role: str = Field(
        ...,
        description="Role to assign",
        pattern="^(super_admin|admin|station_admin|customer_support)$",
    )
    permissions: list[str] | None = Field(None, description="Additional permissions")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": 123,
                "role": "station_admin",
                "permissions": ["manage_bookings", "view_analytics"],
            }
        }
    )


class StationUserResponse(BaseModel):
    """Response model for station user information."""

    id: int
    user_id: int
    station_id: int
    role: str
    permissions: list[str]
    assigned_at: datetime
    assigned_by: int
    is_active: bool

    # User details (if requested)
    user_email: str | None = None
    user_name: str | None = None
    last_login: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    """Response model for audit log entries."""

    id: int
    station_id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: str | None
    details: dict[str, Any]
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime

    # User details
    user_email: str | None = None
    user_role: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Station management endpoints


def _build_station_response(station: Station) -> StationResponse:
    """Build StationResponse with computed properties from Station model."""
    return StationResponse(
        id=str(station.id),
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
        status=station.status,
        settings=station.settings or {},
        business_hours=station.business_hours,
        service_area_radius=station.service_area_radius,
        escalation_radius_miles=station.escalation_radius_miles,
        max_concurrent_bookings=station.max_concurrent_bookings,
        booking_lead_time_hours=station.booking_lead_time_hours,
        branding_config=station.branding_config,
        created_at=station.created_at,
        updated_at=station.updated_at,
        # Geocoding fields
        lat=float(station.lat) if station.lat is not None else None,
        lng=float(station.lng) if station.lng is not None else None,
        geocoded_at=station.geocoded_at,
        geocode_status=station.geocode_status,
        is_geocoded=station.is_geocoded,  # Property
        full_address=station.full_address,  # Property
    )


# NO-AUTH TESTING ENDPOINT (Remove in production)
@router.get("/list-no-auth")
async def list_stations_no_auth(
    db: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    """List all stations WITHOUT authentication (testing only - REMOVE IN PRODUCTION)."""
    try:
        # Build async query
        query = select(Station)

        # Execute
        result = await db.execute(query)
        stations = result.scalars().all()

        # Build simple response with geocoding fields
        response = []
        for station in stations:
            response.append(
                {
                    "id": str(station.id),
                    "code": station.code,
                    "name": station.name,
                    "display_name": station.display_name,
                    "city": station.city,
                    "state": station.state,
                    "status": station.status,
                    # Geocoding fields
                    "lat": float(station.lat) if station.lat is not None else None,
                    "lng": float(station.lng) if station.lng is not None else None,
                    "geocode_status": station.geocode_status,
                    "is_geocoded": station.is_geocoded,
                    "service_area_radius": station.service_area_radius,
                    "escalation_radius_miles": station.escalation_radius_miles,
                }
            )

        logger.info(f"Listed {len(response)} stations (no auth)")
        return {"count": len(response), "stations": response}

    except Exception as e:
        logger.error(f"Error listing stations: {e}", exc_info=True)
        return {"error": str(e), "count": 0, "stations": []}


@router.get("/", response_model=list[StationResponse])
async def list_stations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    active_only: bool = Query(True, description="Only return active stations"),
    include_stats: bool = Query(False, description="Include user and booking statistics"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_stations")),
    db: AsyncSession = Depends(get_db_session),
) -> list[StationResponse]:
    """
    List all stations with optional filtering and statistics.

    Requires 'view_stations' permission.
    Super admins see all stations, others see only their assigned stations.
    """
    try:
        # Build async query using select()
        query = select(Station)

        # Apply station scoping unless super admin
        if not current_user.is_super_admin:
            query = query.where(Station.id == current_user.station_id)

        # Apply filters
        if active_only:
            query = query.where(Station.is_active)

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute async query
        result = await db.execute(query)
        stations = result.scalars().all()

        # Build response with optional statistics
        response = []
        for station in stations:
            # Use helper function to include computed properties
            station_data = _build_station_response(station)

            if include_stats:
                # Count users (async)
                user_count_result = await db.execute(
                    select(func.count(StationUser.id)).where(
                        and_(
                            StationUser.station_id == station.id,
                            StationUser.is_active,
                        )
                    )
                )
                user_count = user_count_result.scalar_one()

                # Get last activity (async)
                last_activity_result = await db.execute(
                    select(StationAuditLog.timestamp)
                    .where(StationAuditLog.station_id == station.id)
                    .order_by(desc(StationAuditLog.timestamp))
                    .limit(1)
                )
                last_activity = last_activity_result.scalar_one_or_none()

                station_data.user_count = user_count
                station_data.last_activity = last_activity

            response.append(station_data)

        await log_station_activity(
            action="view_stations",
            auth_user=current_user,
            db=db,
            resource_type="station",
            details={"count": len(response), "include_stats": include_stats},
        )

        return response

    except Exception as e:
        logger.error(f"Error listing stations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve stations",
        )


@router.post("/", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(
    request: StationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_stations")),
    db: AsyncSession = Depends(get_db_session),
) -> StationResponse:
    """
    Create a new station with auto-generated code.

    Station codes follow format: STATION-{STATE}-{CITY}-{###}
    Example: STATION-CA-BAY-001, STATION-TX-AUSTIN-002

    Requires 'manage_stations' permission.
    Only super admins can create stations.
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create stations",
        )

    try:
        # Auto-generate unique station code
        station_code = await generate_station_code(
            db=db,
            city=request.city,
            state=request.state,
            country=request.country,
        )

        logger.info(f"Generated station code: {station_code} for {request.city}, {request.state}")

        # Create station with all fields from new schema
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
            settings=request.settings or {},
            business_hours=request.business_hours,
            service_area_radius=request.service_area_radius,
            max_concurrent_bookings=request.max_concurrent_bookings or 10,
            booking_lead_time_hours=request.booking_lead_time_hours or 24,
            branding_config=request.branding_config,
        )

        db.add(station)
        await db.commit()
        await db.refresh(station)

        # Auto-create notification group for this station
        try:
            from services.station_notification_sync import (
                sync_station_with_notification_group,
            )

            station_location = (
                f"{station.city}, {station.state}"
                if station.city and station.state
                else station.name
            )
            await sync_station_with_notification_group(
                db=db,
                station_id=station.id,
                station_name=station.name,
                station_location=station_location,
                is_active=True,
                created_by=current_user.id,
            )
            logger.info(f"✅ Auto-created notification group for station: {station.name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create notification group for station: {e}")
            # Don't fail station creation if notification group fails

        await log_station_activity(
            action="create_station",
            auth_user=current_user,
            db=db,
            resource_type="station",
            resource_id=str(station.id),
            details={
                "station_name": station.name,
                "station_code": station_code,
                "city": request.city,
                "state": request.state,
            },
        )

        logger.info(f"Created station: {station_code} (ID: {station.id})")

        return StationResponse.model_validate(station)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating station: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create station: {e!s}",
        )


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(
    station_id: str,
    include_stats: bool = Query(False, description="Include detailed statistics"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_stations")),
    db: AsyncSession = Depends(get_db_session),
) -> StationResponse:
    """
    Get detailed information about a specific station.

    Requires 'view_stations' permission.
    Users can only view their assigned station unless they're super admin.
    """
    from uuid import UUID as PyUUID

    try:
        # Parse station_id (can be UUID string)
        try:
            uuid_station_id = PyUUID(station_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid station ID format",
            )

        # Check station access
        if not current_user.is_super_admin and uuid_station_id != current_user.station_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this station",
            )

        # Async query
        result = await db.execute(select(Station).where(Station.id == uuid_station_id))
        station = result.scalar_one_or_none()

        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station not found",
            )

        # Use helper function to include computed properties
        response = _build_station_response(station)

        if include_stats:
            # Detailed statistics (async)
            user_count_result = await db.execute(
                select(func.count(StationUser.id)).where(
                    and_(
                        StationUser.station_id == uuid_station_id,
                        StationUser.is_active,
                    )
                )
            )
            user_count = user_count_result.scalar_one()

            last_activity_result = await db.execute(
                select(StationAuditLog.timestamp)
                .where(StationAuditLog.station_id == uuid_station_id)
                .order_by(desc(StationAuditLog.timestamp))
                .limit(1)
            )
            last_activity = last_activity_result.scalar_one_or_none()

            response.user_count = user_count
            response.last_activity = last_activity

        await log_station_activity(
            action="view_station",
            auth_user=current_user,
            db=db,
            resource_type="station",
            resource_id=str(station_id),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting station {station_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve station",
        )


@router.put("/{station_id}", response_model=StationResponse)
async def update_station(
    station_id: str,
    request: StationUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_stations")),
    db: AsyncSession = Depends(get_db_session),
) -> StationResponse:
    """
    Update an existing station.

    Requires 'manage_stations' permission.
    Station admins can only update their own station.
    Super admins can update any station.
    """
    try:
        # Check station access
        if not current_user.is_super_admin and str(station_id) != str(current_user.station_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this station",
            )

        # Fetch station
        result = await db.execute(select(Station).where(Station.id == station_id))
        station = result.scalar_one_or_none()

        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station not found",
            )

        # Track changes for audit
        changes = {}

        # Update fields from new schema
        if request.name is not None:
            changes["name"] = {"old": station.name, "new": request.name}
            station.name = request.name

        if request.display_name is not None:
            changes["display_name"] = {
                "old": station.display_name,
                "new": request.display_name,
            }
            station.display_name = request.display_name

        if request.email is not None:
            changes["email"] = {"old": station.email, "new": request.email}
            station.email = request.email

        if request.phone is not None:
            changes["phone"] = {"old": station.phone, "new": request.phone}
            station.phone = request.phone

        if request.address is not None:
            changes["address"] = {
                "old": station.address,
                "new": request.address,
            }
            station.address = request.address

        if request.city is not None:
            changes["city"] = {"old": station.city, "new": request.city}
            station.city = request.city

        if request.state is not None:
            changes["state"] = {"old": station.state, "new": request.state}
            station.state = request.state

        if request.postal_code is not None:
            changes["postal_code"] = {
                "old": station.postal_code,
                "new": request.postal_code,
            }
            station.postal_code = request.postal_code

        if request.country is not None:
            changes["country"] = {
                "old": station.country,
                "new": request.country,
            }
            station.country = request.country

        if request.timezone is not None:
            changes["timezone"] = {
                "old": station.timezone,
                "new": request.timezone,
            }
            station.timezone = request.timezone

        if request.status is not None:
            changes["status"] = {"old": station.status, "new": request.status}
            station.status = request.status

        if request.settings is not None:
            changes["settings"] = {
                "old": station.settings,
                "new": request.settings,
            }
            station.settings = request.settings

        if request.business_hours is not None:
            changes["business_hours"] = {
                "old": station.business_hours,
                "new": request.business_hours,
            }
            station.business_hours = request.business_hours

        if request.service_area_radius is not None:
            changes["service_area_radius"] = {
                "old": station.service_area_radius,
                "new": request.service_area_radius,
            }
            station.service_area_radius = request.service_area_radius

        if request.escalation_radius_miles is not None:
            changes["escalation_radius_miles"] = {
                "old": station.escalation_radius_miles,
                "new": request.escalation_radius_miles,
            }
            station.escalation_radius_miles = request.escalation_radius_miles

        if request.max_concurrent_bookings is not None:
            changes["max_concurrent_bookings"] = {
                "old": station.max_concurrent_bookings,
                "new": request.max_concurrent_bookings,
            }
            station.max_concurrent_bookings = request.max_concurrent_bookings

        if request.booking_lead_time_hours is not None:
            changes["booking_lead_time_hours"] = {
                "old": station.booking_lead_time_hours,
                "new": request.booking_lead_time_hours,
            }
            station.booking_lead_time_hours = request.booking_lead_time_hours

        if request.branding_config is not None:
            changes["branding_config"] = {
                "old": station.branding_config,
                "new": request.branding_config,
            }
            station.branding_config = request.branding_config

        station.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(station)

        # Sync notification group with updated station info
        if "name" in changes or "city" in changes or "state" in changes or "status" in changes:
            try:
                from services.station_notification_sync import (
                    sync_station_with_notification_group,
                )

                station_location = (
                    f"{station.city}, {station.state}"
                    if station.city and station.state
                    else station.name
                )
                is_active = station.status == "active" if hasattr(station, "status") else True
                await sync_station_with_notification_group(
                    db=db,
                    station_id=station.id,
                    station_name=station.name,
                    station_location=station_location,
                    is_active=is_active,
                    created_by=current_user.id,
                )
                logger.info(f"✅ Synced notification group for station: {station.name}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to sync notification group: {e}")

        await log_station_activity(
            action="update_station",
            auth_user=current_user,
            db=db,
            resource_type="station",
            resource_id=str(station_id),
            details={"changes": changes},
        )

        logger.info(
            f"Updated station: {station.code} (ID: {station_id}) - {len(changes)} field(s) changed"
        )

        # Use helper function to include computed properties (geocoding)
        return _build_station_response(station)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating station {station_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to update station: {e!s}",
        )


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    station_id: str,
    force: bool = Query(False, description="Force delete even with warnings"),
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_stations")),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Delete a station (with safety checks).

    Safety checks (Option A - Block if active bookings or users):
    - Blocks deletion if station has active bookings
    - Blocks deletion if station has assigned users
    - Can override with force=true (super admin only)

    Requires 'manage_stations' permission.
    Only super admins can delete stations.
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can delete stations",
        )

    try:
        # Find station
        result = await db.execute(select(Station).where(Station.id == station_id))
        station = result.scalar_one_or_none()

        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station not found",
            )

        # Safety check 1: Check for active bookings
        from models import Booking

        active_bookings_result = await db.execute(
            select(func.count(Booking.id)).where(
                and_(
                    Booking.station_id == station_id,
                    Booking.status.in_(["pending", "confirmed", "in_progress"]),
                )
            )
        )
        active_bookings_count = active_bookings_result.scalar_one()

        # Safety check 2: Check for assigned users
        assigned_users_result = await db.execute(
            select(func.count(StationUser.id)).where(
                and_(StationUser.station_id == station_id, StationUser.is_active)
            )
        )
        assigned_users_count = assigned_users_result.scalar_one()

        # Safety check 3: Check for total bookings (historical data)
        total_bookings_result = await db.execute(
            select(func.count(Booking.id)).where(Booking.station_id == station_id)
        )
        total_bookings_count = total_bookings_result.scalar_one()

        # Block deletion if safety checks fail (unless forced)
        blocking_issues = []

        if active_bookings_count > 0:
            blocking_issues.append(f"{active_bookings_count} active booking(s)")

        if assigned_users_count > 0:
            blocking_issues.append(f"{assigned_users_count} assigned user(s)")

        if blocking_issues and not force:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "Cannot delete station with active data",
                    "blocking_issues": blocking_issues,
                    "active_bookings": active_bookings_count,
                    "assigned_users": assigned_users_count,
                    "total_bookings": total_bookings_count,
                    "hint": "Reassign users and complete/cancel bookings first, or use force=true (super admin)",
                },
            )

        # Warn if historical data exists
        warnings = []
        if total_bookings_count > 0:
            warnings.append(
                f"Station has {total_bookings_count} historical bookings (will be orphaned)"
            )

        # Log deletion with full context
        await log_station_activity(
            action="delete_station",
            auth_user=current_user,
            db=db,
            resource_type="station",
            resource_id=str(station_id),
            details={
                "station_code": station.code,
                "station_name": station.name,
                "forced": force,
                "active_bookings": active_bookings_count,
                "assigned_users": assigned_users_count,
                "total_bookings": total_bookings_count,
                "warnings": warnings,
            },
        )

        # Perform deletion
        await db.delete(station)
        await db.commit()

        # Delete notification group for this station
        try:
            from services.station_notification_sync import (
                delete_station_notification_group,
            )

            await delete_station_notification_group(db=db, station_id=station.id)
            logger.info(f"✅ Deleted notification group for station: {station.name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to delete notification group: {e}")

        logger.warning(
            f"Station deleted: {station.code} (ID: {station_id}) by user {current_user.user_id}. "
            f"Force: {force}, Active bookings: {active_bookings_count}, Users: {assigned_users_count}"
        )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting station {station_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to delete station: {e!s}",
        )


# User-Station management endpoints
@router.get("/{station_id}/users", response_model=list[StationUserResponse])
async def list_station_users(
    station_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: str | None = Query(None, description="Filter by role"),
    active_only: bool = Query(True, description="Only return active assignments"),
    include_user_details: bool = Query(False, description="Include user profile information"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_station_users")),
    db: AsyncSession = Depends(get_db_session),
) -> list[StationUserResponse]:
    """
    List users assigned to a station.

    Requires 'view_station_users' permission.
    Users can only view assignments for their own station unless they're super admin.
    """
    try:
        # Check station access
        if not current_user.is_super_admin and station_id != current_user.station_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this station",
            )

        query = db.query(StationUser).filter(StationUser.station_id == station_id)

        # Apply filters
        if role:
            query = query.filter(StationUser.role == role)

        if active_only:
            query = query.filter(StationUser.is_active)

        # Apply pagination
        station_users = query.offset(skip).limit(limit).all()

        response = []
        for su in station_users:
            user_data = StationUserResponse.from_orm(su)

            if include_user_details:
                # Get user details from identity schema
                # Note: This would need to be implemented based on your user model
                pass

            response.append(user_data)

        await log_station_activity(
            action="view_station_users",
            auth_user=current_user,
            db=db,
            resource_type="station_user",
            details={"station_id": station_id, "count": len(response)},
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error listing station users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve station users",
        )


@router.post(
    "/{station_id}/users",
    response_model=StationUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_user_to_station(
    station_id: int,
    request: UserStationAssignmentRequest,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_station_users")),
    db: AsyncSession = Depends(get_db_session),
) -> StationUserResponse:
    """
    Assign a user to a station with specific role and permissions.

    Requires 'manage_station_users' permission.
    Users can only assign to their own station unless they're super admin.
    """
    try:
        # Check station access
        if not current_user.is_super_admin and station_id != current_user.station_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this station",
            )

        # Verify station exists
        station = db.query(Station).filter(Station.id == station_id).first()
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station not found",
            )

        # Check if assignment already exists
        existing = (
            db.query(StationUser)
            .filter(
                and_(
                    StationUser.station_id == station_id,
                    StationUser.user_id == request.user_id,
                )
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already assigned to this station",
            )

        # Get default permissions for role
        # Phase 1.1: Keep enums from station_models during transition
        from db.models.identity import (
            STATION_ROLE_PERMISSIONS,
            StationRole,
        )

        default_permissions = list(STATION_ROLE_PERMISSIONS.get(StationRole(request.role), set()))

        # Combine with additional permissions
        all_permissions = list(set(default_permissions + (request.permissions or [])))

        # Create assignment
        station_user = StationUser(
            station_id=station_id,
            user_id=request.user_id,
            role=request.role,
            permissions=all_permissions,
            assigned_by=current_user.user_id,
        )

        db.add(station_user)
        db.commit()
        db.refresh(station_user)

        await log_station_activity(
            action="assign_user_to_station",
            auth_user=current_user,
            db=db,
            resource_type="station_user",
            resource_id=str(station_user.id),
            details={
                "assigned_user_id": request.user_id,
                "role": request.role,
                "permissions": all_permissions,
            },
        )

        return StationUserResponse.from_orm(station_user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Error assigning user to station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to assign user to station",
        )


# Audit log endpoints
@router.get("/{station_id}/audit", response_model=list[AuditLogResponse])
async def get_station_audit_log(
    station_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: str | None = Query(None, description="Filter by action"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    user_id: int | None = Query(None, description="Filter by user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_audit_logs")),
    db: AsyncSession = Depends(get_db_session),
) -> list[AuditLogResponse]:
    """
    Get audit log for a station.

    Requires 'view_audit_logs' permission.
    Users can only view logs for their own station unless they're super admin.
    """
    try:
        # Check station access
        if not current_user.is_super_admin and station_id != current_user.station_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this station",
            )

        # Calculate date filter
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(StationAuditLog).filter(
            and_(
                StationAuditLog.station_id == station_id,
                StationAuditLog.timestamp >= cutoff_date,
            )
        )

        # Apply filters
        if action:
            query = query.filter(StationAuditLog.action == action)

        if resource_type:
            query = query.filter(StationAuditLog.resource_type == resource_type)

        if user_id:
            query = query.filter(StationAuditLog.user_id == user_id)

        # Order by timestamp descending
        query = query.order_by(desc(StationAuditLog.timestamp))

        # Apply pagination
        audit_logs = query.offset(skip).limit(limit).all()

        response = [AuditLogResponse.from_orm(log) for log in audit_logs]

        await log_station_activity(
            action="view_audit_logs",
            auth_user=current_user,
            db=db,
            resource_type="audit_log",
            details={
                "station_id": station_id,
                "count": len(response),
                "filters": {
                    "action": action,
                    "resource_type": resource_type,
                    "user_id": user_id,
                    "days": days,
                },
            },
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve audit logs",
        )


# ==================== STATION GEOCODING ====================


class GeocodeStationResponse(BaseModel):
    """Response model for geocoding a station."""

    success: bool
    station_id: str
    lat: float | None = None
    lng: float | None = None
    geocode_status: str
    geocoded_at: datetime | None = None
    full_address: str | None = None
    message: str


@router.post("/{station_id}/geocode", response_model=GeocodeStationResponse)
async def geocode_station(
    station_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_stations")),
) -> GeocodeStationResponse:
    """
    Geocode a station's address using Google Maps API.

    This endpoint:
    - Builds full address from station's address, city, state, postal_code
    - Calls Google Maps Geocoding API
    - Updates station's lat, lng, geocode_status, geocoded_at
    - Returns the geocoding result

    Requires manage_stations permission.
    """
    from uuid import UUID as PyUUID

    from services.scheduling.geocoding_service import GeocodingService

    try:
        # Parse station_id
        try:
            uuid_station_id = PyUUID(station_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid station ID format",
            )

        # Find station
        result = await db.execute(select(Station).where(Station.id == uuid_station_id))
        station = result.scalar_one_or_none()

        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Station {station_id} not found",
            )

        # Build full address
        address_parts = []
        if station.address:
            address_parts.append(station.address)
        if station.city:
            address_parts.append(station.city)
        if station.state:
            address_parts.append(station.state)
        if station.postal_code:
            address_parts.append(station.postal_code)
        if station.country:
            address_parts.append(station.country)

        if not address_parts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Station has no address to geocode",
            )

        full_address = ", ".join(address_parts)

        # Geocode
        geocoding_service = GeocodingService(db)
        geocode_result = await geocoding_service.geocode(full_address)

        if geocode_result and geocode_result.is_valid:
            # Update station with geocoding data
            station.lat = geocode_result.lat
            station.lng = geocode_result.lng
            station.geocode_status = "success"
            station.geocoded_at = datetime.now(timezone.utc)
            await db.commit()

            # Log the action
            await log_station_activity(
                action="geocode_station",
                auth_user=current_user,
                db=db,
                resource_type="station",
                resource_id=station_id,
                details={
                    "lat": geocode_result.lat,
                    "lng": geocode_result.lng,
                    "full_address": full_address,
                },
            )

            return GeocodeStationResponse(
                success=True,
                station_id=station_id,
                lat=geocode_result.lat,
                lng=geocode_result.lng,
                geocode_status="success",
                geocoded_at=station.geocoded_at,
                full_address=geocode_result.normalized_address or full_address,
                message="Station geocoded successfully",
            )
        else:
            # Geocoding failed
            station.geocode_status = "failed"
            station.geocoded_at = datetime.now(timezone.utc)
            await db.commit()

            return GeocodeStationResponse(
                success=False,
                station_id=station_id,
                lat=None,
                lng=None,
                geocode_status="failed",
                geocoded_at=station.geocoded_at,
                full_address=full_address,
                message="Could not geocode address. Please verify the address is correct.",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error geocoding station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to geocode station",
        )


# Export router
__all__ = ["router"]
