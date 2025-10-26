"""
QR Code Tracking Router
Handles QR code redirects and tracking analytics
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
import secrets

from api.app.database import get_db
from api.app.services.qr_tracking_service import QRTrackingService
from api.app.models.qr_tracking import QRCodeType

router = APIRouter(prefix="/api/qr", tags=["qr_tracking"])


@router.get("/scan/{code}")
async def scan_qr_code(
    code: str,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Track QR code scan and redirect to destination.
    This is the endpoint that QR codes should point to.

    Example: https://myhibachichef.com/api/qr/scan/BC001
    """
    service = QRTrackingService(db)

    # Extract tracking information from request
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")

    # Generate or retrieve session ID from cookie
    session_id = request.cookies.get("qr_session")
    if not session_id:
        session_id = secrets.token_urlsafe(32)
        response.set_cookie(
            key="qr_session",
            value=session_id,
            max_age=30 * 24 * 60 * 60,  # 30 days
            httponly=True,
            samesite="lax",
        )

    try:
        # Track the scan
        scan, destination_url = await service.track_qr_scan(
            code=code,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            session_id=session_id,
        )

        # Redirect to destination
        # If destination is relative, make it absolute
        if destination_url.startswith("/"):
            # Get base URL from request
            base_url = str(request.base_url).rstrip("/")
            redirect_url = f"{base_url}{destination_url}"
        else:
            redirect_url = destination_url

        return RedirectResponse(
            url=redirect_url,
            status_code=307,  # Temporary redirect (preserves method)
        )

    except ValueError as e:
        # QR code not found or inactive
        return {"error": str(e)}, 404


@router.post("/conversion")
async def track_conversion(
    session_id: str,
    converted_to_lead: bool = False,
    converted_to_booking: bool = False,
    conversion_value: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a QR scan session as converted.
    Call this when a user completes a lead form or booking.
    """
    service = QRTrackingService(db)

    success = await service.mark_conversion(
        session_id=session_id,
        converted_to_lead=converted_to_lead,
        converted_to_booking=converted_to_booking,
        conversion_value=conversion_value,
    )

    return {
        "success": success,
        "message": "Conversion tracked" if success else "Session not found",
    }


@router.get("/analytics/{code}")
async def get_qr_analytics(
    code: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get analytics for a specific QR code.
    Admin endpoint for viewing QR code performance.
    """
    service = QRTrackingService(db)

    try:
        analytics = await service.get_qr_analytics(code=code)
        return analytics
    except ValueError as e:
        return {"error": str(e)}, 404


@router.get("/list")
async def list_qr_codes(
    type: Optional[QRCodeType] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    List all QR codes with optional filtering.
    Admin endpoint for managing QR codes.
    """
    service = QRTrackingService(db)

    qr_codes = await service.list_qr_codes(type=type, is_active=is_active)

    return {
        "qr_codes": [
            {
                "id": str(qr.id),
                "code": qr.code,
                "type": qr.type,
                "destination_url": qr.destination_url,
                "campaign_name": qr.campaign_name,
                "total_scans": qr.total_scans,
                "unique_scans": qr.unique_scans,
                "conversion_rate": qr.conversion_rate,
                "is_active": qr.is_active,
                "created_at": qr.created_at.isoformat(),
            }
            for qr in qr_codes
        ]
    }


@router.post("/create")
async def create_qr_code(
    code: str,
    type: QRCodeType,
    destination_url: str,
    description: Optional[str] = None,
    campaign_name: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new QR code.
    Admin endpoint for generating new QR codes.
    """
    service = QRTrackingService(db)

    qr_code = await service.create_qr_code(
        code=code,
        type=type,
        destination_url=destination_url,
        description=description,
        campaign_name=campaign_name,
    )

    return {
        "success": True,
        "qr_code": {
            "id": str(qr_code.id),
            "code": qr_code.code,
            "type": qr_code.type,
            "destination_url": qr_code.destination_url,
            "full_url": f"https://myhibachichef.com/api/qr/scan/{qr_code.code}",
        },
    }
