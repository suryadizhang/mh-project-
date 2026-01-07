"""
Station Authentication API Endpoints
Provides station-aware authentication endpoints for the admin interface.
"""

from typing import Any
from uuid import UUID

from core.auth.middleware import get_current_user, get_db_session
from core.auth.models import AuthenticationService
from core.security import verify_password
from db.models.identity import User, Station
from core.auth.station_auth import (
    StationAuthenticationService,
)
from sqlalchemy import select
from cqrs.crm_operations import ApiResponse
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession


# Request/Response Models
class StationLoginRequest(BaseModel):
    email: EmailStr
    password: str
    station_id: str | None = None  # UUID string from frontend


class StationLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    station_context: dict[str, Any]


class UserStationsResponse(BaseModel):
    stations: list[dict[str, Any]]


# Router setup
router = APIRouter(tags=["station-auth"])


# Services will be initialized per request
def get_auth_service():
    from core.config import get_settings
    from core.security import FieldEncryption

    settings = get_settings()
    return AuthenticationService(FieldEncryption(), settings.jwt_secret_key)


def get_station_auth_service():
    from core.config import get_settings
    from core.security import FieldEncryption

    settings = get_settings()
    return StationAuthenticationService(FieldEncryption(), settings.jwt_secret_key)


@router.post("/station-login", response_model=ApiResponse)
async def station_login(
    request: StationLoginRequest,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
    station_auth_service: StationAuthenticationService = Depends(get_station_auth_service),
):
    """
    Station-aware login endpoint.
    If station_id is provided, user will be logged into that specific station.
    If not provided, returns available stations for selection.
    """
    try:
        # First, authenticate the user credentials by querying User directly
        # (Not StationUser which has encrypted email - that's the wrong table!)
        result = await db.execute(select(User).where(User.email == request.email.lower()))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Verify password
        if not user.password_hash or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Get user's station access
        station_context = await station_auth_service.get_user_station_context(db=db, user=user)

        # SUPER_ADMIN bypass: super admins always have station access
        # accessible_station_ids is the correct property name on StationContext
        if not station_context or (
            not station_context.accessible_station_ids
            and not getattr(user, "is_super_admin", False)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No station access available",
            )

        # If specific station requested, validate access
        target_station_id: UUID | None = None
        if request.station_id:
            # Convert string to UUID for comparison with accessible_stations (which contains UUIDs)
            try:
                target_station_id = UUID(request.station_id)
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid station ID format",
                )
            if target_station_id not in station_context.accessible_station_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to requested station",
                )
        else:
            # Default to primary station or first accessible station
            target_station_id = station_context.primary_station_id or next(
                iter(station_context.accessible_station_ids), None
            )

        # Create station-aware session and tokens
        session_info = await station_auth_service.create_station_session(
            db=db,
            user=user,
            station_id=target_station_id,
            ip_address="127.0.0.1",  # In production, get from request
            user_agent="Admin Interface",
        )

        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create station session",
            )

        access_token, refresh_token, session_id = session_info

        # Build station context response
        station_info = {
            "station_id": target_station_id,
            "station_name": f"Station {target_station_id}",  # In production, get from DB
            "role": station_context.station_roles.get(target_station_id, "user"),
            "permissions": list(station_context.station_permissions.get(target_station_id, set())),
            "is_super_admin": station_context.highest_role.value == "super_admin",
        }

        return ApiResponse(
            success=True,
            data=StationLoginResponse(
                access_token=access_token,
                expires_in=3600,
                station_context=station_info,  # 1 hour
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {e!s}",
        )


@router.get("/user-stations", response_model=ApiResponse)
async def get_user_stations(
    email: str,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
    station_auth_service: StationAuthenticationService = Depends(get_station_auth_service),
):
    """
    Get available stations for a user by email.
    Used during login process to show station selection.
    """
    try:
        # Find user by email
        user = await auth_service.get_user_by_email(db=db, email=email)
        if not user:
            return ApiResponse(success=True, data=UserStationsResponse(stations=[]))

        # SUPER_ADMIN bypass: super admins get access to all active stations
        # without needing explicit station_users entries
        if user.is_super_admin:
            stmt = select(Station).where(Station.status == "active")
            result = await db.execute(stmt)
            all_stations = result.scalars().all()

            stations = []
            for idx, station in enumerate(all_stations):
                stations.append(
                    {
                        "id": str(station.id),
                        "name": station.name,
                        "location": getattr(station, "display_name", station.name) or station.name,
                        "role": "super_admin",
                        "is_primary": idx == 0,  # First station is primary
                    }
                )

            return ApiResponse(success=True, data=UserStationsResponse(stations=stations))

        # Get station context for regular users
        station_context = await station_auth_service.get_user_station_context(db=db, user=user)

        if not station_context:
            return ApiResponse(success=True, data=UserStationsResponse(stations=[]))

        # Build stations list (in production, fetch actual station details)
        stations = []
        for station_id in station_context.accessible_stations:
            stations.append(
                {
                    "id": station_id,
                    "name": f"Station {station_id}",
                    "location": f"Location {station_id}",
                    "role": station_context.station_roles.get(station_id, "user"),
                    "is_primary": station_id == station_context.primary_station_id,
                }
            )

        return ApiResponse(success=True, data=UserStationsResponse(stations=stations))

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user stations: {e!s}",
        )


@router.post("/switch-station")
async def switch_station(
    station_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    station_auth_service: StationAuthenticationService = Depends(get_station_auth_service),
):
    """
    Switch user's current station context.
    Returns new tokens with updated station context.
    """
    try:
        # Get current station context
        station_context = await station_auth_service.get_user_station_context(
            db=db, user=current_user
        )

        if not station_context:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No station access available",
            )

        # Validate access to target station
        if station_id not in station_context.accessible_stations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to requested station",
            )

        # Switch station context
        new_tokens = await station_auth_service.switch_station_context(
            db=db,
            user=current_user,
            current_station_context=station_context,
            target_station_id=station_id,
            session_id=current_user.current_session_id,  # Assuming this exists
        )

        if not new_tokens:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to switch station context",
            )

        access_token, refresh_token, _, _ = new_tokens

        # Build new station context
        station_info = {
            "station_id": station_id,
            "station_name": f"Station {station_id}",
            "role": station_context.station_roles.get(station_id, "user"),
            "permissions": list(station_context.station_permissions.get(station_id, set())),
            "is_super_admin": station_context.highest_role.value == "super_admin",
        }

        return ApiResponse(
            success=True,
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "station_context": station_info,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Station switch failed: {e!s}",
        )


__all__ = ["router"]
