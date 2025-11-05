"""
Station-Aware Middleware and Permission Enforcement
Implements multi-tenant permission checking with station context.
"""

from collections.abc import Callable
from functools import wraps
import logging
from typing import Any
from uuid import UUID

from core.auth.models import User, UserSession  # Phase 2C: Updated from api.app.auth.models
from core.auth.station_auth import (  # Phase 2C: Updated from api.app.auth.station_auth
    StationAuthenticationService,
    StationContext,
)
from core.auth.station_models import (
    StationPermission,
    StationRole,
)  # Phase 2C: Updated from api.app.auth.station_models
from core.database import get_db_session  # Phase 2C: Updated from api.app.database
from utils.encryption import FieldEncryption  # Phase 2C: Updated from api.app.utils.encryption
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Initialize components
security = HTTPBearer(auto_error=False)


class AuthenticatedUser:
    """Enhanced user object with station context."""

    def __init__(
        self, user: User, session: UserSession, station_context: StationContext, request: Request
    ):
        self.user = user
        self.session = session
        self.station_context = station_context
        self.request = request

        # Quick access properties
        self.user_id = user.id
        self.username = user.username
        self.email = self._decrypt_email()
        self.current_station_id = station_context.current_station_id
        self.is_super_admin = station_context.is_super_admin
        self.is_admin = station_context.is_admin

    def _decrypt_email(self) -> str | None:
        """Decrypt user email for display."""
        try:
            from app.config import settings

            encryption = FieldEncryption(settings.field_encryption_key)
            return encryption.decrypt(self.user.email_encrypted)
        except Exception:
            return None

    def has_permission(
        self, permission: StationPermission | str, station_id: UUID | None = None
    ) -> bool:
        """Check if user has permission in current or specified station."""
        if isinstance(permission, str):
            try:
                permission = StationPermission(permission)
            except ValueError:
                return False

        target_station = station_id or self.current_station_id
        if not target_station:
            return False

        return self.station_context.has_permission_in_station(permission, target_station)

    def can_access_station(self, station_id: UUID) -> bool:
        """Check if user can access a specific station."""
        return self.station_context.can_access_station(station_id)

    def get_accessible_stations(self) -> set[UUID]:
        """Get all station IDs the user can access."""
        return self.station_context.accessible_station_ids

    def can_perform_cross_station_action(self, permission: StationPermission) -> bool:
        """Check if user can perform cross-station actions."""
        return self.station_context.can_perform_cross_station_action(permission)


async def get_current_station_user(
    request: Request, credentials=Depends(security), db: AsyncSession = Depends(get_db_session)
) -> AuthenticatedUser:
    """Enhanced dependency to get current authenticated user with station context."""

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    try:
        from app.config import settings

        # Initialize services
        encryption = FieldEncryption(settings.field_encryption_key)
        auth_service = StationAuthenticationService(
            encryption=encryption, jwt_secret=settings.jwt_secret_key
        )

        # Verify JWT token
        token_payload = auth_service.verify_jwt_token(credentials.credentials, "access")
        if not token_payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
            )

        user_id = UUID(token_payload["sub"])
        session_id = UUID(token_payload["session_id"])

        # Get user from database
        user_stmt = select(User).where(User.id == user_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or inactive",
            )

        # Get session
        session_stmt = select(UserSession).where(UserSession.id == session_id)
        session_result = await db.execute(session_stmt)
        session = session_result.scalar_one_or_none()

        if not session or session.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found or inactive"
            )

        # Extract station context from token
        station_context = auth_service.extract_station_context_from_token(token_payload)
        if not station_context:
            # Fallback: get fresh station context from database
            station_context = await auth_service.get_user_station_context(db, user)

            if not station_context:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No station access configured for user",
                )

        # Set database context for RLS policies
        await db.execute(text(f"SET app.current_user_id = '{user_id}'"))

        # Log access
        await auth_service.log_station_action(
            db=db,
            station_id=station_context.current_station_id,
            user_id=user.id,
            session_id=session.id,
            action="API_ACCESS",
            details={
                "endpoint": str(request.url.path),
                "method": request.method,
                "station_role": station_context.get_role_for_station(
                    station_context.current_station_id
                ).value,
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True,
        )

        return AuthenticatedUser(user, session, station_context, request)

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication service error"
        )


def require_station_permission(
    permission: StationPermission | str,
    station_id: UUID | None = None,
    allow_cross_station: bool = False,
):
    """
    FastAPI dependency to require specific station permission.

    Returns a dependency function that validates permissions and returns the authenticated user.
    """

    async def permission_checker(
        auth_user: AuthenticatedUser = Depends(get_current_station_user),
    ) -> AuthenticatedUser:
        """Check if user has required permission."""

        # Convert permission to enum if needed
        if isinstance(permission, str):
            try:
                perm = StationPermission(permission)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Invalid permission: {permission}",
                )
        else:
            perm = permission

        # Determine target station
        target_station = station_id or auth_user.current_station_id
        if not target_station:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No station context available"
            )

        # Check cross-station permission if needed
        if allow_cross_station and target_station != auth_user.current_station_id:
            if not auth_user.can_perform_cross_station_action(perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cross-station access not permitted",
                )

        # Check specific permission
        if not auth_user.has_permission(perm, target_station):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: {perm.value} required",
            )

        return auth_user

    return permission_checker


def require_station_role(minimum_role: StationRole | str, station_id: UUID | None = None):
    """
    FastAPI dependency to require minimum station role.

    Returns a dependency function that validates role and returns the authenticated user.
    """

    role_hierarchy = {
        StationRole.CUSTOMER_SUPPORT: 1,
        StationRole.STATION_ADMIN: 2,
        StationRole.ADMIN: 3,
        StationRole.SUPER_ADMIN: 4,
    }

    async def role_checker(
        auth_user: AuthenticatedUser = Depends(get_current_station_user),
    ) -> AuthenticatedUser:
        """Check if user has required role."""

        # Convert role to enum if needed
        if isinstance(minimum_role, str):
            try:
                min_role = StationRole(minimum_role)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail=f"Invalid role: {minimum_role}"
                )
        else:
            min_role = minimum_role

        # Determine target station
        target_station = station_id or auth_user.current_station_id
        if not target_station:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No station context available"
            )

        # Check user's role in target station
        user_role = auth_user.station_context.get_role_for_station(target_station)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="No role assigned for this station"
            )

        # Check role hierarchy
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(min_role, 999)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Minimum role required: {min_role.value}",
            )

        return auth_user

    return role_checker


def require_station_access(station_id_param: UUID | str | Callable):
    """
    FastAPI dependency to require access to a specific station.

    Returns a dependency function that validates station access and returns the authenticated user.
    """

    async def access_checker(
        auth_user: AuthenticatedUser = Depends(get_current_station_user),
    ) -> AuthenticatedUser:
        """Check if user has access to required station."""

        # Resolve station ID
        target_station_id = None
        if callable(station_id_param):
            # If station_id is a callable, we can't resolve it here
            # This pattern needs to be refactored - for now, raise error
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dynamic station ID resolution not supported in dependency pattern",
            )
        elif isinstance(station_id_param, str):
            target_station_id = UUID(station_id_param)
        else:
            target_station_id = station_id_param

        if not target_station_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Station ID required"
            )

        # Check access
        if not auth_user.can_access_station(target_station_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access to this station not permitted"
            )

        return auth_user

    return access_checker


async def audit_log_action(
    action: str,
    auth_user: AuthenticatedUser,
    db: AsyncSession,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict[str, Any] | None = None,
    success: bool = True,
    error_message: str | None = None,
) -> None:
    """Helper function to log user actions with station context."""
    try:
        from app.config import settings

        encryption = FieldEncryption(settings.field_encryption_key)
        auth_service = StationAuthenticationService(
            encryption=encryption, jwt_secret=settings.jwt_secret_key
        )

        # Get current role for logging
        current_role = auth_user.station_context.get_role_for_station(auth_user.current_station_id)

        # Get permissions used (from station context)
        permissions_used = list(
            auth_user.station_context.get_permissions_for_station(auth_user.current_station_id)
        )

        await auth_service.log_station_action(
            db=db,
            station_id=auth_user.current_station_id,
            user_id=auth_user.user_id,
            session_id=auth_user.session.id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_role=current_role.value if current_role else None,
            permissions_used=permissions_used,
            details=details,
            ip_address=auth_user.request.client.host if auth_user.request.client else None,
            user_agent=auth_user.request.headers.get("user-agent"),
            success=success,
            error_message=error_message,
        )

    except Exception as e:
        logger.exception(f"Failed to log audit action: {e}")


def rate_limit(calls: int = 100, period: int = 60):
    """Rate limiting decorator with station context."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract authenticated user for station-aware rate limiting
            for arg in args:
                if isinstance(arg, AuthenticatedUser):
                    break

            # Apply rate limiting logic here
            # For now, just pass through - implement Redis-based rate limiting

            return await func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "AuthenticatedUser",
    "audit_log_action",
    "get_current_station_user",
    "rate_limit",
    "require_station_access",
    "require_station_permission",
    "require_station_role",
]
