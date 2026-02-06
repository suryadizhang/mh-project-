"""
Station Authentication API Endpoints
Provides station-aware authentication endpoints for the admin interface.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth.middleware import get_current_user, get_db_session
from core.auth.models import AuthenticationService
from core.auth.station_auth import StationAuthenticationService
from core.security import verify_password
from core.security.roles import role_matches
from cqrs.crm_operations import ApiResponse
from db.models.identity import Station, User


# Request/Response Models
class StationLoginRequest(BaseModel):
    email: EmailStr
    password: str | None = None  # Required for password login
    oauth_token: str | None = None  # Required for OAuth login
    station_id: str | None = None  # UUID string from frontend

    # Validate that either password or oauth_token is provided
    def model_post_init(self, __context):
        if not self.password and not self.oauth_token:
            raise ValueError("Either password or oauth_token must be provided")


class StationLoginResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None  # For token refresh support
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
    # Use SECRET_KEY for consistency with token creation in OAuth flow
    return AuthenticationService(FieldEncryption(), settings.SECRET_KEY)


def get_station_auth_service():
    from core.config import get_settings
    from core.security import FieldEncryption

    settings = get_settings()
    # Use SECRET_KEY for consistency with token creation in OAuth flow
    return StationAuthenticationService(FieldEncryption(), settings.SECRET_KEY)


@router.post("/station-login", response_model=ApiResponse)
async def station_login(
    request: StationLoginRequest,
    db: AsyncSession = Depends(get_db_session),
    auth_service: AuthenticationService = Depends(get_auth_service),
    station_auth_service: StationAuthenticationService = Depends(get_station_auth_service),
):
    """
    Station-aware login endpoint.
    Supports both password-based and OAuth token-based authentication.
    If station_id is provided, user will be logged into that specific station.
    If not provided, returns available stations for selection.
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        user = None

        # METHOD 1: OAuth Token Authentication
        if request.oauth_token:
            # Verify the OAuth token and extract user
            try:
                import jwt
                from jwt.exceptions import DecodeError as JWTError

                from core.config import get_settings

                settings = get_settings()

                # DEBUG: Log token and key info (first 20 chars only for security)
                token_preview = (
                    request.oauth_token[:50] + "..."
                    if len(request.oauth_token) > 50
                    else request.oauth_token
                )
                key_preview = (
                    settings.jwt_secret_key[:20] + "..."
                    if len(settings.jwt_secret_key) > 20
                    else settings.jwt_secret_key
                )
                secret_key_preview = (
                    settings.SECRET_KEY[:20] + "..."
                    if len(settings.SECRET_KEY) > 20
                    else settings.SECRET_KEY
                )

                logger.warning(f"🔍 DEBUG station-login: Token preview: {token_preview}")
                logger.warning(f"🔍 DEBUG station-login: jwt_secret_key preview: {key_preview}")
                logger.warning(f"🔍 DEBUG station-login: SECRET_KEY preview: {secret_key_preview}")
                logger.warning(
                    f"🔍 DEBUG station-login: Keys match: {settings.jwt_secret_key == settings.SECRET_KEY}"
                )

                # Try decoding with SECRET_KEY directly first (like verify_token does)
                try:
                    test_payload = jwt.decode(
                        request.oauth_token,
                        settings.SECRET_KEY,
                        algorithms=["HS256"],
                        audience="myhibachi-api",
                        options={"verify_aud": True},
                    )
                    logger.warning(
                        f"✅ DEBUG: Decode with SECRET_KEY SUCCESS: {list(test_payload.keys())}"
                    )
                except Exception as e:
                    logger.warning(f"❌ DEBUG: Decode with SECRET_KEY FAILED: {e}")

                payload = jwt.decode(
                    request.oauth_token,
                    settings.SECRET_KEY,
                    algorithms=["HS256"],
                    audience="myhibachi-api",
                    options={"verify_aud": True},
                )
                # Token has "sub" = user_id and "email" = user email
                token_email = payload.get("email")
                token_user_id = payload.get("sub")

                logger.warning(
                    f"✅ DEBUG station-login: Decode SUCCESS! email={token_email}, sub={token_user_id}"
                )

                # Verify token email matches request email
                if token_email and token_email.lower() == request.email.lower():
                    result = await db.execute(
                        select(User).where(User.email == request.email.lower())
                    )
                    user = result.scalar_one_or_none()

                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid OAuth token or user not found",
                    )
            except JWTError as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid OAuth token: {e!s}",
                )

        # METHOD 2: Password Authentication
        elif request.password:
            # Authenticate the user credentials by querying User directly
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
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either password or oauth_token must be provided",
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

        # Fetch actual station details from database
        station_name = "Unknown Station"
        if target_station_id:
            station_result = await db.execute(
                select(Station).where(Station.id == target_station_id)
            )
            station_record = station_result.scalar_one_or_none()
            if station_record:
                station_name = (
                    station_record.display_name
                    or station_record.name
                    or f"Station {target_station_id}"
                )

        # Determine if this is a global role (super_admin, admin, customer_support)
        # Global roles don't need station context in UI header
        user_role = station_context.highest_role.value
        is_global_role = role_matches(user_role, "super_admin", "admin", "customer_support")

        # Count accessible stations for multi-station dropdown logic
        station_count = len(station_context.accessible_station_ids)

        # Build station context response with enhanced data
        station_info = {
            "station_id": str(target_station_id) if target_station_id else None,
            "station_name": station_name,
            "role": station_context.station_roles.get(target_station_id, "user"),
            "permissions": list(station_context.station_permissions.get(target_station_id, set())),
            # Handle both "super_admin" and "superadmin" formats
            "is_super_admin": (
                user_role.lower().replace("_", "") == "superadmin" if user_role else False
            ),
            # New fields for dashboard UX
            "user_email": user.email,
            "user_name": user.full_name or user.email,
            "is_global_role": is_global_role,
            "station_count": station_count,
            "highest_role": user_role,
        }

        return ApiResponse(
            success=True,
            data=StationLoginResponse(
                access_token=access_token,
                refresh_token=refresh_token,  # Include refresh token for token refresh support
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

        # Build stations list with actual station details from DB
        stations = []
        if station_context.accessible_station_ids:
            # Fetch all accessible stations in one query
            stmt = select(Station).where(Station.id.in_(station_context.accessible_station_ids))
            result = await db.execute(stmt)
            station_records = {str(s.id): s for s in result.scalars().all()}

            for station_id in station_context.accessible_station_ids:
                station_id_str = str(station_id)
                station_record = station_records.get(station_id_str)
                if station_record:
                    stations.append(
                        {
                            "id": station_id_str,
                            "name": station_record.name,
                            "location": station_record.display_name or station_record.name,
                            "role": station_context.station_roles.get(station_id, "user"),
                            "is_primary": station_id == station_context.primary_station_id,
                        }
                    )
                else:
                    # Fallback if station not found in DB
                    stations.append(
                        {
                            "id": station_id_str,
                            "name": f"Station {station_id}",
                            "location": "Unknown Location",
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
        if station_id not in station_context.accessible_station_ids:
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

        # Fetch actual station details from database
        station_name = "Unknown Station"
        station_result = await db.execute(select(Station).where(Station.id == station_id))
        station_record = station_result.scalar_one_or_none()
        if station_record:
            station_name = station_record.display_name or station_record.name

        # Determine if this is a global role
        user_role = station_context.highest_role.value
        is_global_role = role_matches(user_role, "super_admin", "admin", "customer_support")

        # Build new station context with enhanced data
        station_info = {
            "station_id": str(station_id),
            "station_name": station_name,
            "role": station_context.station_roles.get(station_id, "user"),
            "permissions": list(station_context.station_permissions.get(station_id, set())),
            # Handle both "super_admin" and "superadmin" formats
            "is_super_admin": (
                user_role.lower().replace("_", "") == "superadmin" if user_role else False
            ),
            # Enhanced fields
            "user_email": current_user.email,
            "user_name": current_user.full_name or current_user.email,
            "is_global_role": is_global_role,
            "station_count": len(station_context.accessible_station_ids),
            "highest_role": user_role,
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
