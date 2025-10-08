"""
Station Administration API
Comprehensive endpoints for managing stations, users, roles, and permissions.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.database import get_db
from app.auth.station_models import Station, StationUser, StationAuditLog, StationAccessToken
from app.auth.station_auth import StationAuthenticationService
from app.auth.station_middleware import (
    get_current_station_user, 
    require_station_permission,
    require_station_role,
    AuthenticatedUser,
    audit_log_action as log_station_activity
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["station-admin"])

# Pydantic models for station management
class StationCreateRequest(BaseModel):
    """Request model for creating a new station."""
    name: str = Field(..., min_length=1, max_length=100, description="Station name")
    description: Optional[str] = Field(None, max_length=500, description="Station description")
    location: Optional[str] = Field(None, max_length=200, description="Physical location")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    email: Optional[str] = Field(None, description="Contact email")
    manager_name: Optional[str] = Field(None, max_length=100, description="Manager name")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Station-specific settings")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Downtown Location",
                "description": "Main downtown branch serving the city center",
                "location": "123 Main St, Downtown, CA 90210",
                "phone": "+1-555-0123",
                "email": "downtown@myhibachi.com",
                "manager_name": "John Smith",
                "settings": {
                    "operating_hours": "10:00-22:00",
                    "max_bookings_per_day": 50,
                    "auto_confirmation": True
                }
            }
        }


class StationUpdateRequest(BaseModel):
    """Request model for updating an existing station."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None)
    manager_name: Optional[str] = Field(None, max_length=100)
    settings: Optional[Dict[str, Any]] = Field(None)
    is_active: Optional[bool] = Field(None, description="Station active status")


class StationResponse(BaseModel):
    """Response model for station information."""
    id: int
    name: str
    description: Optional[str]
    location: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    manager_name: Optional[str]
    settings: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Statistics
    user_count: Optional[int] = None
    booking_count: Optional[int] = None
    last_activity: Optional[datetime] = None
    
    class Config:
        from_attributes = True


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
@router.get("/", response_model=List[StationResponse])
async def list_stations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    active_only: bool = Query(True, description="Only return active stations"),
    include_stats: bool = Query(False, description="Include user and booking statistics"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_stations")),
    db: Session = Depends(get_db)
) -> List[StationResponse]:
    """
    List all stations with optional filtering and statistics.
    
    Requires 'view_stations' permission.
    Super admins see all stations, others see only their assigned stations.
    """
    try:
        query = db.query(Station)
        
        # Apply station scoping unless super admin
        if not current_user.is_super_admin:
            query = query.filter(Station.id == current_user.station_id)
        
        # Apply filters
        if active_only:
            query = query.filter(Station.is_active == True)
        
        # Apply pagination
        stations = query.offset(skip).limit(limit).all()
        
        # Build response with optional statistics
        response = []
        for station in stations:
            station_data = StationResponse.from_orm(station)
            
            if include_stats:
                # Count users
                user_count = db.query(StationUser).filter(
                    and_(
                        StationUser.station_id == station.id,
                        StationUser.is_active == True
                    )
                ).count()
                
                # Get last activity
                last_activity = db.query(StationAuditLog.timestamp).filter(
                    StationAuditLog.station_id == station.id
                ).order_by(desc(StationAuditLog.timestamp)).first()
                
                station_data.user_count = user_count
                station_data.last_activity = last_activity[0] if last_activity else None
            
            response.append(station_data)
        
        await log_station_activity(
            db=db,
            user_id=current_user.user_id,
            station_id=current_user.station_id,
            action="view_stations",
            resource_type="station",
            details={"count": len(response), "include_stats": include_stats}
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing stations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve stations"
        )


@router.post("/", response_model=StationResponse, status_code=status.HTTP_201_CREATED)
async def create_station(
    request: StationCreateRequest,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_stations")),
    db: Session = Depends(get_db)
) -> StationResponse:
    """
    Create a new station.
    
    Requires 'manage_stations' permission.
    Only super admins can create stations.
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create stations"
        )
    
    try:
        # Create station
        station = Station(
            name=request.name,
            description=request.description,
            location=request.location,
            phone=request.phone,
            email=request.email,
            manager_name=request.manager_name,
            settings=request.settings or {},
            created_by=current_user.user_id
        )
        
        db.add(station)
        db.commit()
        db.refresh(station)
        
        await log_station_activity(
            db=db,
            user_id=current_user.user_id,
            station_id=current_user.station_id,
            action="create_station",
            resource_type="station",
            resource_id=str(station.id),
            details={"station_name": station.name}
        )
        
        return StationResponse.from_orm(station)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create station"
        )


@router.get("/{station_id}", response_model=StationResponse)
async def get_station(
    station_id: int,
    include_stats: bool = Query(False, description="Include detailed statistics"),
    current_user: AuthenticatedUser = Depends(require_station_permission("view_stations")),
    db: Session = Depends(get_db)
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
            db=db,
            user_id=current_user.user_id,
            station_id=current_user.station_id,
            action="view_station",
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
    station_id: int,
    request: StationUpdateRequest,
    current_user: AuthenticatedUser = Depends(require_station_permission("manage_stations")),
    db: Session = Depends(get_db)
) -> StationResponse:
    """
    Update an existing station.
    
    Requires 'manage_stations' permission.
    Station admins can only update their own station.
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
        
        # Track changes for audit
        changes = {}
        
        # Update fields
        if request.name is not None:
            changes["name"] = {"old": station.name, "new": request.name}
            station.name = request.name
        
        if request.description is not None:
            changes["description"] = {"old": station.description, "new": request.description}
            station.description = request.description
        
        if request.location is not None:
            changes["location"] = {"old": station.location, "new": request.location}
            station.location = request.location
        
        if request.phone is not None:
            changes["phone"] = {"old": station.phone, "new": request.phone}
            station.phone = request.phone
        
        if request.email is not None:
            changes["email"] = {"old": station.email, "new": request.email}
            station.email = request.email
        
        if request.manager_name is not None:
            changes["manager_name"] = {"old": station.manager_name, "new": request.manager_name}
            station.manager_name = request.manager_name
        
        if request.settings is not None:
            changes["settings"] = {"old": station.settings, "new": request.settings}
            station.settings = request.settings
        
        if request.is_active is not None:
            changes["is_active"] = {"old": station.is_active, "new": request.is_active}
            station.is_active = request.is_active
        
        station.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(station)
        
        await log_station_activity(
            db=db,
            user_id=current_user.user_id,
            station_id=current_user.station_id,
            action="update_station",
            resource_type="station",
            resource_id=str(station_id),
            details={"changes": changes}
        )
        
        return StationResponse.from_orm(station)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating station {station_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update station"
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
    db: Session = Depends(get_db)
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
            db=db,
            user_id=current_user.user_id,
            station_id=current_user.station_id,
            action="view_station_users",
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
    db: Session = Depends(get_db)
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
            db=db,
            user_id=current_user.user_id,
            station_id=current_user.station_id,
            action="assign_user_to_station",
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
    db: Session = Depends(get_db)
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
            db=db,
            user_id=current_user.user_id,
            station_id=current_user.station_id,
            action="view_audit_logs",
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