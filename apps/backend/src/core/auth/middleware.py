"""
Authentication middleware and security decorators for FastAPI.
Implements JWT validation, role-based access control, and security headers.
"""

from collections.abc import Callable
from datetime import datetime, timezone
from functools import wraps
import time

from core.auth.models import (  # Phase 2C: Updated from api.app.auth.models
    AuditLog,
    AuthenticationService,
    Permission,
    Role,
    SessionStatus,
    StationUser,
    UserSession,
    UserStatus,
)
from core.config import get_settings  # Added for jwt_secret_key access
from core.database import get_db_session  # Phase 2C: Updated from api.app.database
from utils.encryption import FieldEncryption  # Phase 2C: Updated from api.app.utils.encryption
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeaders:
    """Security headers for all responses."""

    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    }


class SecurityMiddleware(BaseHTTPMiddleware):
    """Middleware for security headers and request logging."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers and log requests."""
        start_time = time.time()

        # Add security headers
        response = await call_next(request)

        for header, value in SecurityHeaders.HEADERS.items():
            response.headers[header] = value

        # Add processing time header
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        return response


class JWTBearer(HTTPBearer):
    """Custom JWT Bearer token handler."""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.auth_service = None
        self.encryption = None

    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        """Extract and validate JWT token."""
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Initialize services if needed
            if not self.auth_service:
                settings = get_settings()
                self.auth_service = AuthenticationService(
                    FieldEncryption(), settings.jwt_secret_key
                )

            # Verify token
            payload = self.auth_service.verify_jwt_token(credentials.credentials, "access")
            if not payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Store payload in request state for later use
            request.state.jwt_payload = payload
            return credentials

        return None


# Global JWT bearer instance
jwt_bearer = JWTBearer()


class AuthenticatedUser:
    """Represents an authenticated user with permissions."""

    def __init__(self, user: StationUser, session: UserSession, permissions: set[str]):
        self.user = user
        self.session = session
        self.permissions = permissions
        self.id = user.id
        self.email = None  # Decrypted on demand
        self.role = Role(user.role)

    async def get_email(self, encryption: FieldEncryption) -> str:
        """Get decrypted email."""
        if not self.email:
            self.email = encryption.decrypt(self.user.email_encrypted)
        return self.email

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission."""
        return permission.value in self.permissions

    def has_any_permission(self, permissions: list[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(p.value in self.permissions for p in permissions)

    def has_all_permissions(self, permissions: list[Permission]) -> bool:
        """Check if user has all specified permissions."""
        return all(p.value in self.permissions for p in permissions)

    def can_access_role(self, required_role: Role) -> bool:
        """Check if user has required role or higher."""
        role_hierarchy = {
            Role.VIEWER: 0,
            Role.STAFF: 1,
            Role.MANAGER: 2,
            Role.ADMIN: 3,
            Role.SUPER_ADMIN: 4,
            Role.AI_SYSTEM: 1,  # Special case - same as staff
        }

        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)

        return user_level >= required_level


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(jwt_bearer),
    db: AsyncSession = Depends(get_db_session),
) -> AuthenticatedUser:
    """Get current authenticated user with full validation."""

    if not hasattr(request.state, "jwt_payload"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    payload = request.state.jwt_payload
    user_id = payload.get("sub")
    session_id = payload.get("session_id")

    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    # Get user and session from database
    stmt = (
        select(User, UserSession)
        .join(UserSession, User.id == UserSession.user_id)
        .where(
            and_(
                User.id == user_id,
                UserSession.id == session_id,
                User.status == UserStatus.ACTIVE.value,
                UserSession.status == SessionStatus.ACTIVE.value,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
    )

    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session or user inactive"
        )

    user, session = row

    # Update last active time
    session.last_used_at = datetime.now(timezone.utc)
    user.last_active_at = datetime.now(timezone.utc)
    await db.commit()

    # Get permissions from JWT (cached for performance)
    permissions = set(payload.get("permissions", []))

    return AuthenticatedUser(user, session, permissions)


async def get_current_active_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """Get current user ensuring they are active."""
    if current_user.user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is not active"
        )
    return current_user


async def audit_log_action(
    action: str,
    user: AuthenticatedUser,
    db: AsyncSession,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    success: bool = True,
    error_message: str | None = None,
):
    """Log user action for audit trail."""
    log = AuditLog(
        user_id=user.id,
        session_id=user.session.id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        success=success,
        error_message=error_message,
    )

    db.add(log)
    await db.flush()


def require_permission(permission: Permission):
    """Decorator to require specific permission."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in kwargs
            current_user = None
            for _key, value in kwargs.items():
                if isinstance(value, AuthenticatedUser):
                    current_user = value
                    break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication not properly configured",
                )

            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {permission.value}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: Role):
    """Decorator to require specific role or higher."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in kwargs
            current_user = None
            for _key, value in kwargs.items():
                if isinstance(value, AuthenticatedUser):
                    current_user = value
                    break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication not properly configured",
                )

            if not current_user.can_access_role(role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient role. Required: {role.value} or higher",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(permissions: list[Permission]):
    """Decorator to require any of the specified permissions."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in kwargs
            current_user = None
            for _key, value in kwargs.items():
                if isinstance(value, AuthenticatedUser):
                    current_user = value
                    break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication not properly configured",
                )

            if not current_user.has_any_permission(permissions):
                perm_names = [p.value for p in permissions]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions. Need any of: {', '.join(perm_names)}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def require_all_permissions(permissions: list[Permission]):
    """Decorator to require all specified permissions."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find current_user in kwargs
            current_user = None
            for _key, value in kwargs.items():
                if isinstance(value, AuthenticatedUser):
                    current_user = value
                    break

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication not properly configured",
                )

            if not current_user.has_all_permissions(permissions):
                perm_names = [p.value for p in permissions]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions. Need all of: {', '.join(perm_names)}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self.requests = {}  # {key: [(timestamp, count), ...]}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed within rate limit."""
        now = time.time()

        # Cleanup old entries periodically
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_entries(now - window_seconds)
            self.last_cleanup = now

        # Get current requests for this key
        if key not in self.requests:
            self.requests[key] = []

        key_requests = self.requests[key]

        # Remove expired entries
        key_requests[:] = [req for req in key_requests if req[0] > now - window_seconds]

        # Count current requests
        total_requests = sum(req[1] for req in key_requests)

        if total_requests >= max_requests:
            return False

        # Add current request
        key_requests.append((now, 1))
        return True

    def _cleanup_old_entries(self, cutoff_time: float):
        """Remove old entries to prevent memory leaks."""
        for key in list(self.requests.keys()):
            self.requests[key] = [req for req in self.requests[key] if req[0] > cutoff_time]
            if not self.requests[key]:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_requests: int, window_seconds: int, per_user: bool = True):
    """Rate limiting decorator."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request and user context
            request = None
            current_user = None

            for _key, value in kwargs.items():
                if hasattr(value, "client"):  # Likely a Request object
                    request = value
                elif isinstance(value, AuthenticatedUser):
                    current_user = value

            # Determine rate limit key
            if per_user and current_user:
                rate_key = f"user_{current_user.id}"
            elif request:
                rate_key = f"ip_{request.client.host}"
            else:
                rate_key = "global"

            # Check rate limit
            if not rate_limiter.is_allowed(rate_key, max_requests, window_seconds):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": str(window_seconds)},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def setup_auth_middleware(app):
    """Setup authentication middleware on the FastAPI app."""

    # Add security middleware
    app.add_middleware(SecurityMiddleware)

    # Define exempt paths (no authentication required)
    exempt_paths = [
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/ready",
        "/info",
        "/api/health",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/verify-email",
        "/api/auth/reset-password",
        "/api/auth/forgot-password",
        "/api/auth/refresh-token",
        "/api/stripe/webhook",
        "/metrics",
    ]

    # Store exempt paths in app state for reference
    app.state.auth_exempt_paths = exempt_paths


__all__ = [
    "AuthenticatedUser",
    "JWTBearer",
    "RateLimiter",
    "SecurityMiddleware",
    "audit_log_action",
    "get_current_active_user",
    "get_current_user",
    "rate_limit",
    "require_all_permissions",
    "require_any_permission",
    "require_permission",
    "require_role",
    "setup_auth_middleware",
]
