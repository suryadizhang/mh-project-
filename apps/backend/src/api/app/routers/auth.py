from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def get_current_user_info() -> dict[str, Any]:
    """Get current user information (placeholder)."""
    # This is a placeholder for your existing auth system
    # In development, return mock data
    return {
        "id": "dev-user-123",
        "email": "dev@myhibachi.com",
        "name": "Dev User",
        "is_admin": True,
        "created_at": "2024-01-01T00:00:00Z",
    }


@router.post("/login")
async def login() -> dict[str, Any]:
    """Login endpoint (placeholder)."""
    return {
        "access_token": "dev-token-123",
        "token_type": "bearer",
        "user": {
            "id": "dev-user-123",
            "email": "dev@myhibachi.com",
            "name": "Dev User",
        },
    }


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Logout endpoint (placeholder)."""
    return {"message": "Logged out successfully"}
