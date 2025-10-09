"""
Station Authentication API Endpoints
Provides station-aware authentication endpoints for the admin interface.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import AuthenticationService, User
from app.auth.station_auth import StationAuthenticationService, StationContext
from app.auth.station_models import Station
from app.auth.middleware import get_current_user, get_db_session
from app.crm.endpoints import ApiResponse


# Request/Response Models
class StationLoginRequest(BaseModel):
    email: EmailStr
    password: str
    station_id: Optional[int] = None


class StationLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    station_context: Dict[str, Any]


class UserStationsResponse(BaseModel):
    stations: List[Dict[str, Any]]


# Router setup
router = APIRouter(tags=["station-auth"])

# Services will be initialized per request
def get_auth_service():
    from app.utils.encryption import FieldEncryption
    from app.config import settings
    return AuthenticationService(
        FieldEncryption(),
        settings.jwt_secret_key
    )

def get_station_auth_service():
    from app.utils.encryption import FieldEncryption
    from app.config import settings
    return StationAuthenticationService(
        FieldEncryption(),
        settings.jwt_secret_key
    )


@router.post("/station-login", response_model=ApiResponse)
async def station_login(
    request: StationLoginRequest,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
    station_auth_service: StationAuthenticationService = Depends(get_station_auth_service)
):
    """
    Station-aware login endpoint.
    If station_id is provided, user will be logged into that specific station.
    If not provided, returns available stations for selection.
    """
    try:
        # First, authenticate the user credentials
        user = await auth_service.authenticate_user(
            db=db,
            email=request.email,
            password=request.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Get user's station access
        station_context = await station_auth_service.get_user_station_context(
            db=db, 
            user=user
        )
        
        if not station_context or not station_context.accessible_stations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No station access available"
            )
        
        # If specific station requested, validate access
        target_station_id = None
        if request.station_id:
            target_station_id = request.station_id
            if target_station_id not in station_context.accessible_stations:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to requested station"
                )
        else:
            # Default to primary station or first accessible station
            target_station_id = (
                station_context.primary_station_id or 
                list(station_context.accessible_stations)[0]
            )
        
        # Create station-aware session and tokens
        session_info = await station_auth_service.create_station_session(
            db=db,
            user=user,
            station_id=target_station_id,
            ip_address="127.0.0.1",  # In production, get from request
            user_agent="Admin Interface"
        )
        
        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create station session"
            )
        
        access_token, refresh_token, session_id = session_info
        
        # Build station context response
        station_info = {
            "station_id": target_station_id,
            "station_name": f"Station {target_station_id}",  # In production, get from DB
            "role": station_context.station_roles.get(target_station_id, "user"),
            "permissions": list(station_context.station_permissions.get(target_station_id, set())),
            "is_super_admin": station_context.highest_role.value == "super_admin"
        }
        
        return ApiResponse(
            success=True,
            data=StationLoginResponse(
                access_token=access_token,
                expires_in=3600,  # 1 hour
                station_context=station_info
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.get("/user-stations", response_model=ApiResponse)
async def get_user_stations(
    email: str,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
    station_auth_service: StationAuthenticationService = Depends(get_station_auth_service)
):
    """
    Get available stations for a user by email.
    Used during login process to show station selection.
    """
    try:
        # Find user by email
        user = await auth_service.get_user_by_email(db=db, email=email)
        if not user:
            return ApiResponse(
                success=True,
                data=UserStationsResponse(stations=[])
            )
        
        # Get station context
        station_context = await station_auth_service.get_user_station_context(
            db=db, 
            user=user
        )
        
        if not station_context:
            return ApiResponse(
                success=True,
                data=UserStationsResponse(stations=[])
            )
        
        # Build stations list (in production, fetch actual station details)
        stations = []
        for station_id in station_context.accessible_stations:
            stations.append({
                "id": station_id,
                "name": f"Station {station_id}",
                "location": f"Location {station_id}",
                "role": station_context.station_roles.get(station_id, "user"),
                "is_primary": station_id == station_context.primary_station_id
            })
        
        return ApiResponse(
            success=True,
            data=UserStationsResponse(stations=stations)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stations: {str(e)}"
        )


@router.post("/switch-station")
async def switch_station(
    station_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    station_auth_service: StationAuthenticationService = Depends(get_station_auth_service)
):
    """
    Switch user's current station context.
    Returns new tokens with updated station context.
    """
    try:
        # Get current station context
        station_context = await station_auth_service.get_user_station_context(
            db=db, 
            user=current_user
        )
        
        if not station_context:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No station access available"
            )
        
        # Validate access to target station
        if station_id not in station_context.accessible_stations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to requested station"
            )
        
        # Switch station context
        new_tokens = await station_auth_service.switch_station_context(
            db=db,
            user=current_user,
            current_station_context=station_context,
            target_station_id=station_id,
            session_id=current_user.current_session_id  # Assuming this exists
        )
        
        if not new_tokens:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to switch station context"
            )
        
        access_token, refresh_token, _, _ = new_tokens
        
        # Build new station context
        station_info = {
            "station_id": station_id,
            "station_name": f"Station {station_id}",
            "role": station_context.station_roles.get(station_id, "user"),
            "permissions": list(station_context.station_permissions.get(station_id, set())),
            "is_super_admin": station_context.highest_role.value == "super_admin"
        }
        
        return ApiResponse(
            success=True,
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "station_context": station_info
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Station switch failed: {str(e)}"
        )


__all__ = ["router"]