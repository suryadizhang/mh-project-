"""
Automatic Audit Logging Middleware for Admin Actions

This middleware automatically captures ALL admin actions (POST, PUT, PATCH, DELETE)
to the audit_logs table without requiring manual changes to each router.

Coverage:
- All /api/v1/admin/* endpoints
- All /api/admin/* endpoints
- All POST, PUT, PATCH, DELETE requests to these paths
- Excludes GET requests (reads) and OPTIONS preflight

What gets logged:
- WHO: user_id, role, name, email (from JWT token)
- WHAT: action (CREATE/UPDATE/DELETE), resource_type (from URL path), resource_id
- WHEN: timestamp
- WHERE: IP address, user_agent
- RESPONSE: status_code, success/failure

Usage:
    # In main.py, register the middleware:
    from middleware.audit_middleware import AuditMiddleware

    app.add_middleware(AuditMiddleware)

Configuration:
    Set environment variable AUDIT_MIDDLEWARE_ENABLED=true to enable
    Default: enabled in production, disabled in development
"""

import json
import logging
import os
import re
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy import text

from core.database import get_db_context

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically logs all admin write operations (POST/PUT/PATCH/DELETE).

    Features:
    - Automatic user extraction from JWT token
    - Path-based resource type detection
    - Response status tracking
    - Minimal performance overhead
    """

    # Methods that modify data and should be logged
    AUDITABLE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    # Path patterns for admin endpoints
    # IMPORTANT: All 5 RBAC roles must have their endpoints covered:
    # - SUPER_ADMIN, ADMIN: /api/v1/admin/, /api/admin/
    # - CUSTOMER_SUPPORT: /api/v1/bookings/, /api/v1/leads/, /api/v1/customers/
    # - STATION_MANAGER: /api/v1/scheduling/, /api/v1/stations/, /api/v1/chefs/
    # - CHEF: /api/v1/chef-portal/
    ADMIN_PATH_PATTERNS = [
        r"^/api/v1/admin/",  # Admin panel operations (SUPER_ADMIN, ADMIN)
        r"^/api/admin/",  # Legacy admin paths
        r"^/api/v1/bookings/",  # Booking modifications (all admin roles)
        r"^/api/v1/leads/",  # Lead modifications (CUSTOMER_SUPPORT+)
        r"^/api/v1/crm/",  # CRM modifications (CUSTOMER_SUPPORT+)
        r"^/api/v1/customers/",  # Customer modifications (CUSTOMER_SUPPORT+)
        r"^/api/v1/chefs/",  # Chef modifications (STATION_MANAGER+)
        r"^/api/v1/stations/",  # Station modifications (STATION_MANAGER+)
        r"^/api/v1/newsletter/",  # Newsletter modifications (ADMIN+)
        r"^/api/v1/stripe/",  # Payment modifications (ADMIN+)
        # NEW: Previously missing path patterns for complete role coverage
        r"^/api/v1/chef-portal/",  # Chef portal actions (CHEF role)
        r"^/api/v1/scheduling/",  # Scheduling operations (STATION_MANAGER+)
        r"^/api/v1/agreements/",  # Agreement signing/updates (all roles)
        r"^/api/v1/booking-reminders/",  # Reminder operations (ADMIN+)
        r"^/api/v1/faq-settings/",  # FAQ modifications (ADMIN+)
        r"^/api/v1/monitoring/",  # Monitoring rules (ADMIN+)
        r"^/api/v1/knowledge-sync/",  # Knowledge base sync (ADMIN+)
    ]

    # Paths to exclude from logging (health checks, auth tokens, etc.)
    EXCLUDE_PATTERNS = [
        r"^/api/v1/auth/token",  # Token refresh (too noisy)
        r"^/api/v1/auth/login",  # Logged separately by auth system
        r"^/health",  # Health checks
        r"^/metrics",  # Prometheus metrics
        r"^/docs",  # Swagger docs
        r"^/openapi",  # OpenAPI schema
    ]

    # Map HTTP methods to action types
    METHOD_TO_ACTION = {
        "POST": "CREATE",
        "PUT": "UPDATE",
        "PATCH": "UPDATE",
        "DELETE": "DELETE",
    }

    def __init__(self, app):
        super().__init__(app)
        self.enabled = os.getenv("AUDIT_MIDDLEWARE_ENABLED", "true").lower() == "true"
        if self.enabled:
            logger.info("✅ Audit middleware enabled - logging all admin actions")
        else:
            logger.info("⚠️ Audit middleware disabled (set AUDIT_MIDDLEWARE_ENABLED=true to enable)")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Intercept requests and log admin write operations.
        """
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)

        # Skip non-auditable methods
        if request.method not in self.AUDITABLE_METHODS:
            return await call_next(request)

        # Check if path matches admin patterns
        path = request.url.path

        # Skip excluded paths
        for pattern in self.EXCLUDE_PATTERNS:
            if re.match(pattern, path):
                return await call_next(request)

        # Check if this is an admin endpoint
        is_admin_endpoint = False
        for pattern in self.ADMIN_PATH_PATTERNS:
            if re.match(pattern, path):
                is_admin_endpoint = True
                break

        if not is_admin_endpoint:
            return await call_next(request)

        # This is an admin write operation - log it!
        start_time = time.time()

        # Extract user info from request (set by auth dependency)
        user_info = await self._extract_user_info(request)

        # Execute the actual request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log the action asynchronously (don't block response)
        try:
            await self._log_action(
                request=request,
                response=response,
                user_info=user_info,
                duration_ms=duration_ms,
            )
        except Exception as e:
            # Never fail the request due to audit logging errors
            logger.error(f"Failed to log audit action: {e}", exc_info=True)

        return response

    async def _extract_user_info(self, request: Request) -> dict:
        """
        Extract user information from the request state.

        The auth dependency sets `request.state.user` with the current user.
        If not present, we return a minimal dict for anonymous/unauthenticated requests.
        """
        user_info = {
            "id": None,
            "role": "anonymous",
            "name": "Anonymous",
            "email": None,
        }

        # Try to get user from request state (set by get_current_user dependency)
        if hasattr(request.state, "user") and request.state.user:
            user = request.state.user
            if isinstance(user, dict):
                # Role might be a UserRole enum, convert to string
                role = user.get("role", "unknown")
                if hasattr(role, "value"):
                    role = role.value
                elif hasattr(role, "name"):
                    role = role.name
                else:
                    role = str(role) if role else "unknown"

                user_info = {
                    "id": user.get("id") or user.get("user_id"),
                    "role": role,
                    "name": user.get("name")
                    or user.get("full_name")
                    or user.get("email", "Unknown"),
                    "email": user.get("email"),
                }
            else:
                # User object with attributes
                role = getattr(user, "role", "unknown")
                if hasattr(role, "value"):
                    role = role.value
                elif hasattr(role, "name"):
                    role = role.name
                else:
                    role = str(role) if role else "unknown"

                user_info = {
                    "id": getattr(user, "id", None),
                    "role": role,
                    "name": getattr(user, "name", None)
                    or getattr(user, "full_name", None)
                    or getattr(user, "email", "Unknown"),
                    "email": getattr(user, "email", None),
                }

        # Try to extract from Authorization header if state not set
        elif "authorization" in request.headers:
            # Just note that there was an auth header - user details will be logged as "authenticated"
            user_info["role"] = "authenticated"
            user_info["name"] = "Authenticated User (details unavailable)"

        return user_info

    async def _log_action(
        self,
        request: Request,
        response: Response,
        user_info: dict,
        duration_ms: float,
    ):
        """
        Log the admin action to the audit_logs table.

        Bug fixes applied (2025-01-30):
        - Uses get_db_context() instead of get_db() for non-FastAPI context
        - Handles UUID casting properly for user_id
        - Uses valid action values only (VIEW, CREATE, UPDATE, DELETE)
        - Provides delete_reason for DELETE actions (required by DB constraint)
        """
        path = request.url.path
        method = request.method

        # Determine action type (must be: VIEW, CREATE, UPDATE, DELETE)
        action = self.METHOD_TO_ACTION.get(method, "VIEW")

        # Extract resource type and ID from path
        resource_type, resource_id = self._parse_path(path)

        # Get client info
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Determine success based on response status
        success = 200 <= response.status_code < 400

        # Build metadata
        metadata = {
            "path": path,
            "method": method,
            "query_params": str(request.query_params) if request.query_params else None,
            "status_code": response.status_code,
            "success": success,
            "duration_ms": round(duration_ms, 2),
            "logged_by": "audit_middleware",
        }

        # Provide delete_reason for DELETE actions (required by DB CHECK constraint)
        delete_reason = None
        if action == "DELETE":
            delete_reason = f"Deleted via {method} request to {resource_type}"

        # Handle user_id - needs to be UUID or None for PostgreSQL
        user_id = None
        if user_info.get("id"):
            user_id_str = str(user_info["id"])
            # Validate it looks like a UUID before passing
            if len(user_id_str) >= 32:
                user_id = user_id_str

        # Get database session using context manager (correct pattern for middleware)
        try:
            async with get_db_context() as db:
                query = text(
                    """
                    INSERT INTO audit_logs (
                        user_id,
                        user_role,
                        user_name,
                        user_email,
                        action,
                        resource_type,
                        resource_id,
                        ip_address,
                        user_agent,
                        delete_reason,
                        metadata
                    ) VALUES (
                        CAST(:user_id AS uuid),
                        :user_role,
                        :user_name,
                        :user_email,
                        :action,
                        :resource_type,
                        :resource_id,
                        :ip_address,
                        :user_agent,
                        :delete_reason,
                        CAST(:metadata AS jsonb)
                    )
                """
                )

                await db.execute(
                    query,
                    {
                        "user_id": user_id,
                        "user_role": user_info["role"],
                        "user_name": user_info["name"],
                        "user_email": user_info["email"],
                        "action": action,
                        "resource_type": resource_type,
                        "resource_id": resource_id,
                        "ip_address": ip_address,
                        "user_agent": user_agent[:500] if user_agent else None,
                        "delete_reason": delete_reason,
                        "metadata": json.dumps(metadata),
                    },
                )

                await db.commit()

                logger.debug(
                    f"Audit logged: {action} {resource_type}/{resource_id or 'N/A'} "
                    f"by {user_info['name']} ({user_info['role']}) -> {response.status_code}"
                )

        except Exception as e:
            logger.error(f"Failed to insert audit log: {e}", exc_info=True)

    def _parse_path(self, path: str) -> tuple[str, str | None]:
        """
        Parse the URL path to extract resource type and ID.

        Examples:
            /api/v1/admin/config/pricing/adult_price -> ("admin_config", "pricing/adult_price")
            /api/v1/bookings/123e4567-e89b-12d3-a456-426614174000 -> ("bookings", "123e4567...")
            /api/v1/leads/abc-123/convert -> ("leads", "abc-123")
        """
        # Remove /api/v1/ or /api/ prefix
        path = re.sub(r"^/api/(v1/)?", "", path)

        # Split by /
        parts = [p for p in path.split("/") if p]

        if not parts:
            return ("unknown", None)

        # First part is the resource type
        resource_type = parts[0]

        # If it's an admin path, combine admin + next part
        if resource_type == "admin" and len(parts) > 1:
            resource_type = f"admin_{parts[1]}"
            parts = parts[2:]  # Remove admin and subresource from path
        else:
            parts = parts[1:]  # Remove resource type

        # Look for UUID or ID in remaining parts
        resource_id = None
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

        for part in parts:
            if re.match(uuid_pattern, part, re.IGNORECASE):
                resource_id = part
                break

        # If no UUID found, use remaining path as identifier
        if not resource_id and parts:
            resource_id = "/".join(parts)

        return (resource_type, resource_id)

    def _get_client_ip(self, request: Request) -> str:
        """
        Get the real client IP, handling proxies and load balancers.
        """
        # Check X-Forwarded-For header (set by proxies)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Take the first IP in the chain (original client)
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header (set by Nginx)
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"
