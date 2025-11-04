"""
Authentication module for MyHibachi API
"""

from .middleware import setup_auth_middleware


# Define require_roles helper function here to avoid circular imports
# This is imported by payment notification endpoints
def require_roles(roles: list[str]):
    """
    Generic helper to require specific roles for endpoint access.

    Usage:
        @router.get("/admin")
        async def admin_endpoint(user = Depends(require_roles([UserRole.ADMIN]))):
            ...
    """
    # Import here to avoid circular dependency
    from fastapi import Depends, HTTPException, status

    # Try to import from the auth.py file in parent directory
    try:
        # Import the auth_service from api.app.auth module (file, not package)
        import sys
        from pathlib import Path

        # Add api.app to path temporarily
        api_app_path = str(Path(__file__).parent.parent)
        if api_app_path not in sys.path:
            sys.path.insert(0, api_app_path)

        from auth import auth_service

        return auth_service.require_roles(roles)
    except ImportError:
        # Fallback: create inline dependency
        async def role_checker(current_user=Depends(lambda: None)):
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
                )
            if not hasattr(current_user, "roles") or not any(
                role in current_user.roles for role in roles
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
                )
            return current_user

        return role_checker


__all__ = ["setup_auth_middleware", "require_roles"]
