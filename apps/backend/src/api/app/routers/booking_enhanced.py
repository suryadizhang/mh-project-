from typing import Any, List, Optional
from datetime import datetime, timedelta
import os
import sqlite3
import csv
import logging
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Body, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.database import get_db
from api.app.utils.auth import get_current_user, admin_required, superadmin_required
from api.app.schemas.booking_schemas import (
    BookingCreate, WaitlistCreate, CancelBookingRequest, WaitlistEntry
)
from api.app.services.email_service import (
    send_booking_email, send_customer_confirmation, send_waitlist_confirmation,
    send_waitlist_slot_opened, send_waitlist_position_email,
    send_deposit_confirmation_email, send_booking_cancellation_email
)

router = APIRouter()
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/booking/token")
limiter = Limiter(key_func=get_remote_address)


# ============ AUTHENTICATION ENDPOINTS ============
@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return a JWT access token."""
    # Implementation for token login
    pass


@router.post("/admin/login")
async def admin_login(credentials: dict):
    """Authenticate admin user and return a JWT access token."""
    # Implementation for admin login
    pass


@router.get("/me")
async def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.get("id"),
        "username": current_user.get("username"),
        "role": current_user.get("role", "admin"),
        "user_type": current_user.get("role", "admin")
    }


# ============ SUPERADMIN ENDPOINTS ============
@router.post("/superadmin/create_admin")
async def create_admin(
    username: str = Form(...),
    password: str = Form(...),
    user=Depends(superadmin_required)
):
    """Create a new admin user (superadmin only)."""
    # Implementation for creating admin
    pass


@router.get("/superadmin/admins")
async def list_admins(user=Depends(superadmin_required)):
    """List all admin users (superadmin only)."""
    # Implementation for listing admins
    pass


@router.delete("/superadmin/admin/{admin_username}")
async def delete_admin(admin_username: str, user=Depends(superadmin_required)):
    """Delete an admin user (superadmin only)."""
    # Implementation for deleting admin
    pass


# ============ BOOKING ENDPOINTS ============
@router.post("/book")
@limiter.limit("5/minute")
async def book_service(
    data: BookingCreate, 
    background_tasks: BackgroundTasks, 
    request: Request
):
    """Create a new booking and send confirmation emails."""
    # Implementation for booking creation
    pass


@router.get("/availability")
async def get_availability(date: str):
    """Get availability status for each time slot on a given date."""
    # Implementation for availability check
    pass


@router.post("/availability/bulk")
async def get_bulk_availability(dates: List[str]):
    """Get availability status for multiple dates at once."""
    # Implementation for bulk availability
    pass


# ============ WAITLIST ENDPOINTS ============
@router.post("/waitlist")
@limiter.limit("10/minute")
async def join_waitlist(
    data: WaitlistCreate, 
    background_tasks: BackgroundTasks, 
    request: Request
):
    """Add a user to the waitlist, send confirmation and position email."""
    # Implementation for waitlist joining
    pass


@router.get("/admin/waitlist", response_model=List[WaitlistEntry])
async def get_waitlist(user=Depends(admin_required)):
    """Get all waitlist entries, sorted by preferred_date, preferred_time, and created_at (admin only)."""
    # Implementation for getting waitlist
    pass


@router.delete("/admin/waitlist/{waitlist_id}")
async def remove_waitlist_user(waitlist_id: int, user=Depends(admin_required)):
    """Admin removes a user from the waitlist by ID."""
    # Implementation for removing from waitlist
    pass


# ============ ADMIN BOOKING MANAGEMENT ============
@router.get("/admin/weekly")
async def admin_weekly(start_date: str, user=Depends(admin_required)):
    """Get all bookings for a given week (admin only)."""
    # Implementation for weekly bookings
    pass


@router.get("/admin/monthly")
async def admin_monthly(year: int, month: int, user=Depends(admin_required)):
    """Get all bookings for a given month (admin only)."""
    # Implementation for monthly bookings
    pass


@router.get("/admin/all-bookings")
async def admin_all_bookings(user=Depends(admin_required)):
    """Get all bookings from all time periods (admin only)."""
    # Implementation for all bookings
    pass


@router.delete("/admin/cancel_booking")
async def cancel_booking(
    booking_id: int,
    body: CancelBookingRequest = Body(...),
    user=Depends(admin_required)
):
    """Cancel a booking by ID, send cancellation email, and log the action (admin only)."""
    # Implementation for booking cancellation
    pass


@router.post("/admin/confirm_deposit")
async def confirm_deposit(
    booking_id: int,
    date: str,
    reason: str = Body(..., embed=True),
    user=Depends(admin_required)
):
    """Admin marks a booking as deposit received and sends notification."""
    # Implementation for deposit confirmation
    pass


# ============ ADMIN ANALYTICS & KPIs ============
@router.get("/admin/kpis")
async def admin_kpis(user=Depends(admin_required)):
    """Returns KPIs: total bookings, bookings this week, bookings this month, waitlist count."""
    # Implementation for KPIs
    pass


@router.get("/admin/customers")
async def get_all_customers(user=Depends(admin_required)):
    """Get all customer data with booking history (admin only)."""
    # Implementation for customer data
    pass


@router.get("/admin/customer/{email}")
async def get_customer_detail(email: str, user=Depends(admin_required)):
    """Get detailed information for a specific customer (admin only)."""
    # Implementation for customer details
    pass


@router.get("/admin/customer-analytics")
async def get_customer_analytics(user=Depends(admin_required)):
    """Get customer analytics and insights (admin only)."""
    # Implementation for customer analytics
    pass


# ============ NEWSLETTER MANAGEMENT ============
@router.get("/admin/newsletter/recipients")
async def get_newsletter_recipients(
    city: str = "", 
    name: str = "", 
    user=Depends(admin_required)
):
    """Get all newsletter recipients, optionally filtered by city and name."""
    # Implementation for newsletter recipients
    pass


@router.post("/admin/newsletter/send")
async def send_newsletter(
    newsletter_data: dict,
    user=Depends(admin_required)
):
    """Send newsletter to recipients (admin only)."""
    # Implementation for sending newsletter
    pass


@router.get("/admin/newsletter/cities")
async def get_newsletter_cities(user=Depends(admin_required)):
    """Get all unique cities from newsletter database (admin only)."""
    # Implementation for newsletter cities
    pass


@router.get("/admin/newsletter/export")
async def export_newsletter(user=Depends(admin_required)):
    """Export all company newsletter contacts as CSV (admin only)."""
    # Implementation for newsletter export
    pass


# ============ ACTIVITY LOGS ============
@router.get("/admin/activity-logs")
async def get_activity_logs(
    page: int = 1,
    limit: int = 50,
    entity_type: str = None,
    action_type: str = None,
    user=Depends(admin_required)
):
    """Get activity logs with pagination and filtering."""
    # Implementation for activity logs
    pass


@router.get("/superadmin/activity_logs")
async def get_admin_activity_logs(limit: int = 100, user=Depends(superadmin_required)):
    """Get admin activity logs (superadmin only)."""
    # Implementation for admin activity logs
    pass


# ============ UTILITIES & TESTING ============
@router.post("/admin/create-sample-data")
async def create_sample_data(user=Depends(admin_required)):
    """Create sample test data for development and testing."""
    # Implementation for sample data creation
    pass


@router.post("/admin/change_password")
async def change_own_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    user=Depends(admin_required)
):
    """Allow admin to change their own password."""
    # Implementation for password change
    pass


# ============ RATE LIMITED ENDPOINTS ============
@router.get("/protected-data")
@limiter.limit("2/minute")
async def protected_data(request: Request):
    """Example endpoint with rate limiting and dependency injection."""
    return {"message": "This is protected data with rate limiting"}


# ============ LEGACY COMPATIBILITY ============
@router.get("/")
async def get_bookings(
    user_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """Get bookings with optional filters (legacy compatibility)."""
    # Placeholder implementation for legacy compatibility
    return [
        {
            "id": "booking-123",
            "user_id": current_user["id"],
            "date": "2024-12-25",
            "time": "18:00",
            "guests": 8,
            "status": "confirmed",
            "total_cost": 800.00,
            "created_at": "2024-12-01T10:00:00Z"
        }
    ]


@router.post("/")
async def create_booking(
    booking_data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Create a new booking (legacy compatibility)."""
    # Placeholder implementation for legacy compatibility
    return {
        "id": "booking-124",
        "user_id": current_user["id"],
        "status": "pending",
        "message": "Booking created successfully"
    }


@router.get("/{booking_id}")
async def get_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Get a specific booking by ID (legacy compatibility)."""
    # Placeholder implementation for legacy compatibility
    return {
        "id": booking_id,
        "user_id": current_user["id"],
        "date": "2024-12-25",
        "time": "18:00",
        "guests": 8,
        "status": "confirmed",
        "total_cost": 800.00,
        "created_at": "2024-12-01T10:00:00Z"
    }


@router.put("/{booking_id}")
async def update_booking(
    booking_id: str,
    booking_data: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Update a booking (legacy compatibility)."""
    # Placeholder implementation for legacy compatibility
    return {
        "id": booking_id,
        "status": "updated",
        "message": "Booking updated successfully"
    }


@router.delete("/{booking_id}")
async def delete_booking(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    """Delete a booking (legacy compatibility)."""
    # Placeholder implementation for legacy compatibility
    return {"message": f"Booking {booking_id} deleted successfully"}