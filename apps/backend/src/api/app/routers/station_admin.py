"""
Station Administration API
Comprehensive endpoints for managing stations, users, roles, and permissions.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, select, func

from api.app.database import get_db_session
from api.app.auth.station_models import Station, StationUser, StationAuditLog, StationAccessToken
from api.app.auth.station_auth import StationAuthenticationService
from api.app.auth.station_middleware import (
    get_current_station_user, 
    require_station_permission,
    require_station_role,
    AuthenticatedUser,
    audit_log_action as log_station_activity
)
from api.app.utils.station_code_generator import generate_station_code, validate_station_code_format

logger = logging.getLogger(__name__)

router = APIRouter(tags=["station-admin"])

# Add a simple test endpoint without authentication
@router.get("/test", response_model=Dict[str, Any])
async def test_endpoint(db: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """Simple test endpoint to verify router is working."""
    try:
        # Test database connection
        result = await db.execute(select(func.count(Station.id)))
        station_count = result.scalar_one()
        
        return {
            "status": "success",
            "message": "Station Management API is operational",
            "station_count": station_count
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "station_count": 0
        }


# Pydantic models for station management
class StationCreateRequest(BaseModel):
    """Request model for creating a new station (code is auto-generated)."""
    name: str = Field(..., min_length=1, max_length=100, description="Station name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Display name for UI")
    
    # Location (required for code generation)
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    state: str = Field(..., min_length=2, max_length=2, description="2-letter state code (e.g., CA, TX)")
    country: str = Field(default="US", min_length=2, max_length=2, description="Country code")
    timezone: str = Field(..., description="IANA timezone (e.g., America/Los_Angeles)")
    
    # Optional contact & location details
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    address: Optional[str] = Field(None, description="Street address")
    postal_code: Optional[str] = Field(None, max_length=20, description="ZIP/Postal code")
    
    # Business settings
    status: Optional[str] = Field(default="active", description="Station status")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Station settings JSON")
    business_hours: Optional[Dict[str, Any]] = Field(None, description="Operating hours JSON")
    service_area_radius: Optional[int] = Field(None, ge=0, description="Service radius in miles")
    max_concurrent_bookings: Optional[int] = Field(default=10, ge=1, description="Max concurrent bookings")
    booking_lead_time_hours: Optional[int] = Field(default=24, ge=0, description="Minimum booking lead time")
    branding_config: Optional[Dict[str, Any]] = Field(None, description="Branding configuration JSON")
    
    model_config = ConfigDict(json_schema_extra={
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
                    "sunday": {"open": "09:00", "close": "22:00"}
                },
                "max_concurrent_bookings": 15,
                "booking_lead_time_hours": 24
            }
        })


class StationUpdateRequest(BaseModel):
    """Request model for updating an existing station."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=2)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=2)
    timezone: Optional[str] = Field(None)
    status: Optional[str] = Field(None, description="Station status: active, inactive, suspended, maintenance")
    settings: Optional[Dict[str, Any]] = Field(None)
    business_hours: Optional[Dict[str, Any]] = Field(None)
    service_area_radius: Optional[int] = Field(None, ge=0)
    max_concurrent_bookings: Optional[int] = Field(None, ge=1)
    booking_lead_time_hours: Optional[int] = Field(None, ge=0)
    branding_config: Optional[Dict[str, Any]] = Field(None)


class StationResponse(BaseModel):
    """Response model for station information."""
    id: str  # UUID as string
    code: str
    name: str
    display_name: str
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    postal_code: Optional[str]
    country: str
    timezone: str
    status: str
    settings: Dict[str, Any]
    business_hours: Optional[Dict[str, Any]]
    service_area_radius: Optional[int]
    max_concurrent_bookings: int
    booking_lead_time_hours: int
    branding_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    # Statistics (populated optionally)
    user_count: Optional[int] = None
    active_booking_count: Optional[int] = None
    total_booking_count: Optional[int] = None
    last_activity: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserStationAssignmentRequest(BaseModel):
    """Request model for assigning users to stations."""
    user_id: int = Field(..., description="User ID to assign")
    role: str = Field(..., description="Role to assign", pattern="^(super_admin|admin|station_admin|customer_support)$")
    permissions: Optional[List[str]] = Field(None, description="Additional permissions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "role": "station_admin",
                "permissions": ["manage_bookings", "view_analytics"]
            }
        }


class StationUserResponse(BaseModel):
    """Response model for station user information."""
    id: int
    user_id: int
    station_id: int
    role: str
    permissions: List[str]
    assigned_at: datetime
    assigned_by: int
    is_active: bool
    
    # User details (if requested)
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    """Response model for audit log entries."""
    id: int
    station_id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    timestamp: datetime
    
    # User details
    user_email: Optional[str] = None
    user_role: Optional[str] = None
    
    class Config:
        from_attributes = True


# Station management endpoints

# NO-AUTH TESTING ENDPOINT (Remove in production)
@router.get("/list-no-auth")
async def list_stations_no_auth(
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """List all stations WITHOUT authentication (testing only - REMOVE IN PRODUCTION)."""
    try:
        # Build async query
        query = select(Station)
        
        # Execute
        result = await db.execute(query)
        stations = result.scalars().all()
        
        # Build simple response
        response = []
        for station in stations:
            response.append({
                "id": str(station.id),
                "code": station.code,
                "name": station.name,
                "display_name": station.display_name,
                "city": station.city,
                "state": station.state,
                "status": station.status
            })
        
        logger.info(f"Listed {len(response)} stations (no auth)")
        return {
            "count": len(response),
            "stations": response
        }
        
    except Exception as e:
        logger.error(f"Error listing stations: {e}", exc_info=True)
        return {
            "error": str(e),
            "count": 0,
            "stations": []
        }


@router.get("/", response_model=List[StationResponse])
async def list_stations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    active_only: bool = Query(True, description="Only return active stations"),
    include_stats: bool = Query(False, description="Include user and booking statistics"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_stations")),
    db: AsyncSession = Depends(get_db_session)
) -> List[StationResponse]:
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
            query = query.where(Station.is_active == True)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute async query
        result = await db.execute(query)
        stations = result.scalars().all()
        
        # Build response with optional statistics
        response = []
        for station in stations:
            station_data = StationResponse.model_validate(station)
            
            if include_stats:
                # Count users (async)
                user_count_result = await db.execute(
                    select(func.count(StationUser.id)).where(
                        and_(
                            StationUser.station_id == station.id,
                            StationUser.is_active == True
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
            details={"count": len(response), "include_stats": include_stats}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing stations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve stations"
        )


@router.post("/", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(
    request: StationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_stations")),
    db: AsyncSession = Depends(get_db_session)
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
            detail="Only super administrators can create stations"
        )
    
    try:
        # Auto-generate unique station code
        station_code = await generate_station_code(
            db=db,
            city=request.city,
            state=request.state,
            country=request.country
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
            branding_config=request.branding_config
        )
        
        db.add(station)
        await db.commit()
        await db.refresh(station)
        
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
                "state": request.state
            }
        )
        
        logger.info(f"Created station: {station_code} (ID: {station.id})")
        
        return StationResponse.model_validate(station)
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating station: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to create station: {str(e)}"
        )


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(
    station_id: int,
    include_stats: bool = Query(False, description="Include detailed statistics"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_stations")),
    db: AsyncSession = Depends(get_db_session)
) -> StationResponse:
    """
    Get detailed information about a specific station.
    
    Requires 'view_stations' permission.
    Users can only view their assigned station unless they're super admin.
    """
    try:
        # Check station access
        if not current_user.is_super_admin and station_id != current_user.station_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this station"
            )
        
        station = db.query(Station).filter(Station.id == station_id).first()
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station not found"
            )
        
        response = StationResponse.from_orm(station)
        
        if include_stats:
            # Detailed statistics
            user_count = db.query(StationUser).filter(
                and_(
                    StationUser.station_id == station_id,
                    StationUser.is_active == True
                )
            ).count()
            
            last_activity = db.query(StationAuditLog.timestamp).filter(
                StationAuditLog.station_id == station_id
            ).order_by(desc(StationAuditLog.timestamp)).first()
            
            response.user_count = user_count
            response.last_activity = last_activity[0] if last_activity else None
        
        await log_station_activity(
            action="view_station",
            auth_user=current_user,
            db=db,
            resource_type="station",
            resource_id=str(station_id)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting station {station_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve station"
        )


@router.put("/{station_id}", response_model=StationResponse)
async def update_station(
    station_id: str,
    request: StationUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_stations")),
    db: AsyncSession = Depends(get_db_session)
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
                detail="Access denied to this station"
            )
        
        # Fetch station
        result = await db.execute(
            select(Station).where(Station.id == station_id)
        )
        station = result.scalar_one_or_none()
        
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station not found"
            )
        
        # Track changes for audit
        changes = {}
        
        # Update fields from new schema
        if request.name is not None:
            changes["name"] = {"old": station.name, "new": request.name}
            station.name = request.name
        
        if request.display_name is not None:
            changes["display_name"] = {"old": station.display_name, "new": request.display_name}
            station.display_name = request.display_name
        
        if request.email is not None:
            changes["email"] = {"old": station.email, "new": request.email}
            station.email = request.email
        
        if request.phone is not None:
            changes["phone"] = {"old": station.phone, "new": request.phone}
            station.phone = request.phone
        
        if request.address is not None:
            changes["address"] = {"old": station.address, "new": request.address}
            station.address = request.address
        
        if request.city is not None:
            changes["city"] = {"old": station.city, "new": request.city}
            station.city = request.city
        
        if request.state is not None:
            changes["state"] = {"old": station.state, "new": request.state}
            station.state = request.state
        
        if request.postal_code is not None:
            changes["postal_code"] = {"old": station.postal_code, "new": request.postal_code}
            station.postal_code = request.postal_code
        
        if request.country is not None:
            changes["country"] = {"old": station.country, "new": request.country}
            station.country = request.country
        
        if request.timezone is not None:
            changes["timezone"] = {"old": station.timezone, "new": request.timezone}
            station.timezone = request.timezone
        
        if request.status is not None:
            changes["status"] = {"old": station.status, "new": request.status}
            station.status = request.status
        
        if request.settings is not None:
            changes["settings"] = {"old": station.settings, "new": request.settings}
            station.settings = request.settings
        
        if request.business_hours is not None:
            changes["business_hours"] = {"old": station.business_hours, "new": request.business_hours}
            station.business_hours = request.business_hours
        
        if request.service_area_radius is not None:
            changes["service_area_radius"] = {"old": station.service_area_radius, "new": request.service_area_radius}
            station.service_area_radius = request.service_area_radius
        
        if request.max_concurrent_bookings is not None:
            changes["max_concurrent_bookings"] = {"old": station.max_concurrent_bookings, "new": request.max_concurrent_bookings}
            station.max_concurrent_bookings = request.max_concurrent_bookings
        
        if request.booking_lead_time_hours is not None:
            changes["booking_lead_time_hours"] = {"old": station.booking_lead_time_hours, "new": request.booking_lead_time_hours}
            station.booking_lead_time_hours = request.booking_lead_time_hours
        
        if request.branding_config is not None:
            changes["branding_config"] = {"old": station.branding_config, "new": request.branding_config}
            station.branding_config = request.branding_config
        
        station.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(station)
        
        await log_station_activity(
            action="update_station",
            auth_user=current_user,
            db=db,
            resource_type="station",
            resource_id=str(station_id),
            details={"changes": changes}
        )
        
        logger.info(f"Updated station: {station.code} (ID: {station_id}) - {len(changes)} field(s) changed")
        
        return StationResponse.model_validate(station)
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating station {station_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to update station: {str(e)}"
        )


@router.delete("/{station_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_station(
    station_id: str,
    force: bool = Query(False, description="Force delete even with warnings"),
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_stations")),
    db: AsyncSession = Depends(get_db_session)
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
            detail="Only super administrators can delete stations"
        )
    
    try:
        # Find station
        result = await db.execute(
            select(Station).where(Station.id == station_id)
        )
        station = result.scalar_one_or_none()
        
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station not found"
            )
        
        # Safety check 1: Check for active bookings
        from api.app.models.booking_models import Booking
        active_bookings_result = await db.execute(
            select(func.count(Booking.id))
            .where(
                and_(
                    Booking.station_id == station_id,
                    Booking.status.in_(["pending", "confirmed", "in_progress"])
                )
            )
        )
        active_bookings_count = active_bookings_result.scalar_one()
        
        # Safety check 2: Check for assigned users
        assigned_users_result = await db.execute(
            select(func.count(StationUser.id))
            .where(
                and_(
                    StationUser.station_id == station_id,
                    StationUser.is_active == True
                )
            )
        )
        assigned_users_count = assigned_users_result.scalar_one()
        
        # Safety check 3: Check for total bookings (historical data)
        total_bookings_result = await db.execute(
            select(func.count(Booking.id))
            .where(Booking.station_id == station_id)
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
                    "hint": "Reassign users and complete/cancel bookings first, or use force=true (super admin)"
                }
            )
        
        # Warn if historical data exists
        warnings = []
        if total_bookings_count > 0:
            warnings.append(f"Station has {total_bookings_count} historical bookings (will be orphaned)")
        
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
                "warnings": warnings
            }
        )
        
        # Perform deletion
        await db.delete(station)
        await db.commit()
        
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
            detail=f"Unable to delete station: {str(e)}"
        )


# User-Station management endpoints
@router.get("/{station_id}/users", response_model=List[StationUserResponse])
async def list_station_users(
    station_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[str] = Query(None, description="Filter by role"),
    active_only: bool = Query(True, description="Only return active assignments"),
    include_user_details: bool = Query(False, description="Include user profile information"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_station_users")),
    db: AsyncSession = Depends(get_db_session)
) -> List[StationUserResponse]:
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
                detail="Access denied to this station"
            )
        
        query = db.query(StationUser).filter(StationUser.station_id == station_id)
        
        # Apply filters
        if role:
            query = query.filter(StationUser.role == role)
        
        if active_only:
            query = query.filter(StationUser.is_active == True)
        
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
            details={"station_id": station_id, "count": len(response)}
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing station users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve station users"
        )


@router.post("/{station_id}/users", response_model=StationUserResponse, status_code=status.HTTP_201_CREATED)
async def assign_user_to_station(
    station_id: int,
    request: UserStationAssignmentRequest,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_station_users")),
    db: AsyncSession = Depends(get_db_session)
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
                detail="Access denied to this station"
            )
        
        # Verify station exists
        station = db.query(Station).filter(Station.id == station_id).first()
        if not station:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Station not found"
            )
        
        # Check if assignment already exists
        existing = db.query(StationUser).filter(
            and_(
                StationUser.station_id == station_id,
                StationUser.user_id == request.user_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already assigned to this station"
            )
        
        # Get default permissions for role
        from app.auth.station_models import get_role_permissions
        default_permissions = get_role_permissions(request.role)
        
        # Combine with additional permissions
        all_permissions = list(set(default_permissions + (request.permissions or [])))
        
        # Create assignment
        station_user = StationUser(
            station_id=station_id,
            user_id=request.user_id,
            role=request.role,
            permissions=all_permissions,
            assigned_by=current_user.user_id
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
                "permissions": all_permissions
            }
        )
        
        return StationUserResponse.from_orm(station_user)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error assigning user to station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to assign user to station"
        )


# Audit log endpoints
@router.get("/{station_id}/audit", response_model=List[AuditLogResponse])
async def get_station_audit_log(
    station_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_audit_logs")),
    db: AsyncSession = Depends(get_db_session)
) -> List[AuditLogResponse]:
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
                detail="Access denied to this station"
            )
        
        # Calculate date filter
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(StationAuditLog).filter(
            and_(
                StationAuditLog.station_id == station_id,
                StationAuditLog.timestamp >= cutoff_date
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
                    "days": days
                }
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve audit logs"
        )


# Export router
__all__ = ["router"]