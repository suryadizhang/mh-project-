"""
Admin router re-export for backward compatibility.
"""

from routers.v1.admin_analytics import router as admin_router

__all__ = ["admin_router"]
