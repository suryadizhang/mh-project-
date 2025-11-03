"""
Station-aware authentication utilities for AI API.
Simplified version that extracts station context from JWT tokens.
"""

import logging
from typing import Any

from fastapi import Header, HTTPException, status
import jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class StationContext(BaseModel):
    """Station context extracted from JWT token."""

    station_id: int
    station_name: str
    user_id: int
    role: str
    permissions: list[str]
    is_super_admin: bool = False


def extract_station_context(authorization: str | None = Header(None)) -> StationContext | None:
    """
    Extract station context from Authorization header.

    Returns None if no valid station context is found.
    This allows backward compatibility for non-station requests.
    """
    if not authorization:
        return None

    try:
        # Extract JWT token
        if not authorization.startswith("Bearer "):
            return None

        token = authorization.split(" ")[1]

        # Note: In production, use proper JWT verification with secret
        # For now, decode without verification for simplicity
        payload = jwt.decode(token, options={"verify_signature": False})

        # Extract station context if present
        station_data = payload.get("station_context")
        if not station_data:
            return None

        return StationContext(
            station_id=station_data.get("station_id"),
            station_name=station_data.get("station_name", ""),
            user_id=payload.get("user_id"),
            role=station_data.get("role", "customer_support"),
            permissions=station_data.get("permissions", []),
            is_super_admin=station_data.get("role") == "super_admin",
        )

    except Exception as e:
        logger.warning(f"Failed to extract station context: {e}")
        return None


def get_station_context_optional(authorization: str | None = Header(None)) -> StationContext | None:
    """
    FastAPI dependency for optional station context extraction.

    Returns None if no station context is available, allowing backward compatibility.
    """
    return extract_station_context(authorization)


def require_station_context(authorization: str | None = Header(None)) -> StationContext:
    """
    FastAPI dependency that requires station context.

    Raises HTTPException if no valid station context is found.
    """
    context = extract_station_context(authorization)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Station context required. Please provide valid station-scoped authentication.",
        )
    return context


def has_permission(context: StationContext | None, permission: str) -> bool:
    """Check if station context has specific permission."""
    if not context:
        return False

    # Super admin has all permissions
    if context.is_super_admin:
        return True

    return permission in context.permissions


def has_agent_access(context: StationContext | None, agent: str) -> bool:
    """Check if station context allows access to specific agent."""
    if not context:
        # Allow basic customer agent access without station context
        return agent == "customer"

    # Super admin and admin can access all agents
    if context.role in ["super_admin", "admin"]:
        return True

    # Station admin can access customer, staff, and support agents
    if context.role == "station_admin":
        return agent in ["customer", "staff", "support"]

    # Customer support can access customer and support agents
    if context.role == "customer_support":
        return agent in ["customer", "support"]

    # Default: only customer agent
    return agent == "customer"


def get_station_filter(context: StationContext | None) -> dict[str, Any]:
    """Get database filter for station-scoped queries."""
    if not context:
        return {}

    # Super admin can see all stations
    if context.is_super_admin:
        return {}

    # All other roles are scoped to their station
    return {"station_id": context.station_id}
