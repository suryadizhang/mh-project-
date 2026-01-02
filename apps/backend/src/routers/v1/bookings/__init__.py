"""
Bookings API Package
====================

Modular booking management endpoints for My Hibachi.

This package splits the large bookings router into focused modules:

Modules:
--------
- schemas.py (~260 lines) - All Pydantic request/response models
- constants.py (~109 lines) - Business constants (deposit, minimums, etc.)
- crud.py (~350 lines) - GET/POST/PUT endpoints
- delete.py (~200 lines) - Soft-delete with RBAC and audit trail
- calendar.py (~280 lines) - Weekly/monthly calendar views, reschedule
- availability.py (~250 lines) - Slot availability checking
- cancellation.py (~350 lines) - 2-step cancellation workflow
- notifications.py (~170 lines) - Async notification helpers

Why Modular?
------------
- Each module is <500 lines (maintainable)
- Single responsibility per module
- Easier to test, review, and maintain
- Clear separation of concerns

Usage:
------
    from routers.v1.bookings import router as bookings_router
    app.include_router(bookings_router, prefix="/api/v1/bookings")

File Organization Standard:
---------------------------
Per coding standards (11-CODING_STANDARDS.instructions.md):
- Maximum file size: 500 lines
- If a file exceeds 500 lines, split into logical modules
- Each module should have single responsibility
- Use __init__.py to combine routers
"""

from fastapi import APIRouter

# Import sub-routers from each module
from .availability import router as availability_router
from .calendar import router as calendar_router
from .cancellation import router as cancellation_router
from .crud import router as crud_router
from .delete import router as delete_router

# Create main router that combines all sub-routers
router = APIRouter(tags=["bookings"])

# Include all sub-routers
# Order matters for route matching - more specific routes first
router.include_router(calendar_router)
router.include_router(availability_router)
router.include_router(cancellation_router)
router.include_router(delete_router)
router.include_router(crud_router)

# Export router for main.py
__all__ = ["router"]
