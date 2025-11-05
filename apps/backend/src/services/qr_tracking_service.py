"""
QR Code Tracking Service
Handles QR code scanning, tracking, and analytics
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from api.app.models.qr_tracking import QRCode, QRCodeType, QRScan
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from user_agents import parse


class QRTrackingService:
    """Service for QR code tracking and analytics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def track_qr_scan(
        self,
        code: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        referrer: str | None = None,
        session_id: str | None = None,
    ) -> tuple[QRScan, str]:
        """
        Track a QR code scan and return the destination URL.

        Args:
            code: QR code identifier
            ip_address: IP address of scanner
            user_agent: User agent string
            referrer: Referring URL
            session_id: Session tracking ID

        Returns:
            Tuple of (QRScan record, destination_url)

        Raises:
            ValueError: If QR code not found or inactive
        """
        # Find QR code
        stmt = select(QRCode).where(QRCode.code == code.upper(), QRCode.is_active)
        result = await self.db.execute(stmt)
        qr_code = result.scalar_one_or_none()

        if not qr_code:
            raise ValueError(f"QR code '{code}' not found or inactive")

        # Parse device information from user agent
        device_info = self._parse_user_agent(user_agent) if user_agent else {}

        # Create scan record
        scan = QRScan(
            qr_code_id=qr_code.id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_info.get("device_type"),
            os=device_info.get("os"),
            browser=device_info.get("browser"),
            referrer=referrer,
            session_id=session_id,
            scanned_at=datetime.utcnow(),
        )

        # TODO: Add IP geolocation lookup (optional)
        # This would require a service like MaxMind GeoIP2 or ipapi.co
        # For now, we'll leave location fields as None

        self.db.add(scan)
        await self.db.commit()
        await self.db.refresh(scan)

        return scan, qr_code.destination_url

    async def mark_conversion(
        self,
        session_id: str,
        converted_to_lead: bool = False,
        converted_to_booking: bool = False,
        conversion_value: float | None = None,
    ) -> bool:
        """
        Mark a QR scan as converted to lead or booking.

        Args:
            session_id: Session tracking ID from the scan
            converted_to_lead: Whether user became a lead
            converted_to_booking: Whether user made a booking
            conversion_value: Booking value if converted

        Returns:
            True if conversion was recorded
        """
        stmt = select(QRScan).where(QRScan.session_id == session_id)
        result = await self.db.execute(stmt)
        scans = result.scalars().all()

        if not scans:
            return False

        for scan in scans:
            if converted_to_lead:
                scan.converted_to_lead = True
            if converted_to_booking:
                scan.converted_to_booking = True
            if conversion_value:
                scan.conversion_value = conversion_value

        await self.db.commit()
        return True

    async def create_qr_code(
        self,
        code: str,
        type: QRCodeType,
        destination_url: str,
        description: str | None = None,
        campaign_name: str | None = None,
        metadata: dict[str, Any] | None = None,
        created_by: UUID | None = None,
    ) -> QRCode:
        """
        Create a new QR code.

        Args:
            code: Unique QR code identifier (e.g., BC001)
            type: Type of QR code
            destination_url: Where to redirect
            description: Description of usage
            campaign_name: Marketing campaign name
            metadata: Additional metadata
            created_by: User ID who created it

        Returns:
            Created QRCode record
        """
        qr_code = QRCode(
            code=code.upper(),
            type=type,
            destination_url=destination_url,
            description=description,
            campaign_name=campaign_name,
            metadata=metadata,
            created_by=created_by,
        )

        self.db.add(qr_code)
        await self.db.commit()
        await self.db.refresh(qr_code)

        return qr_code

    async def get_qr_analytics(
        self,
        code: str | None = None,
        qr_code_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Get analytics for a specific QR code.

        Args:
            code: QR code identifier
            qr_code_id: QR code UUID

        Returns:
            Analytics dictionary
        """
        # Find QR code
        stmt = select(QRCode)
        if code:
            stmt = stmt.where(QRCode.code == code.upper())
        elif qr_code_id:
            stmt = stmt.where(QRCode.id == qr_code_id)
        else:
            raise ValueError("Must provide either code or qr_code_id")

        result = await self.db.execute(stmt)
        qr_code = result.scalar_one_or_none()

        if not qr_code:
            raise ValueError("QR code not found")

        # Get scans
        scans = qr_code.scans

        # Calculate analytics
        total_scans = len(scans)
        unique_ips = len({scan.ip_address for scan in scans if scan.ip_address})
        unique_sessions = len({scan.session_id for scan in scans if scan.session_id})

        leads = sum(1 for scan in scans if scan.converted_to_lead)
        bookings = sum(1 for scan in scans if scan.converted_to_booking)
        revenue = sum(scan.conversion_value or 0 for scan in scans)

        # Device breakdown
        device_counts = {}
        for scan in scans:
            device = scan.device_type or "unknown"
            device_counts[device] = device_counts.get(device, 0) + 1

        # Location breakdown
        location_counts = {}
        for scan in scans:
            location = scan.city or scan.region or scan.country or "Unknown"
            location_counts[location] = location_counts.get(location, 0) + 1

        # Recent scans
        recent_scans = sorted(scans, key=lambda s: s.scanned_at, reverse=True)[:10]

        return {
            "qr_code": {
                "code": qr_code.code,
                "type": qr_code.type,
                "destination_url": qr_code.destination_url,
                "campaign_name": qr_code.campaign_name,
                "created_at": qr_code.created_at.isoformat(),
            },
            "metrics": {
                "total_scans": total_scans,
                "unique_ips": unique_ips,
                "unique_sessions": unique_sessions,
                "leads_generated": leads,
                "bookings_generated": bookings,
                "total_revenue": float(revenue),
                "conversion_rate": (
                    round((bookings / unique_sessions * 100), 2) if unique_sessions > 0 else 0
                ),
                "lead_rate": (
                    round((leads / unique_sessions * 100), 2) if unique_sessions > 0 else 0
                ),
            },
            "devices": device_counts,
            "locations": location_counts,
            "recent_scans": [
                {
                    "scanned_at": scan.scanned_at.isoformat(),
                    "device_type": scan.device_type,
                    "location": scan.location_display,
                    "converted": scan.converted_to_booking,
                }
                for scan in recent_scans
            ],
        }

    async def list_qr_codes(
        self,
        type: QRCodeType | None = None,
        is_active: bool | None = None,
    ) -> list[QRCode]:
        """
        List all QR codes with optional filtering.

        Args:
            type: Filter by QR code type
            is_active: Filter by active status

        Returns:
            List of QR codes
        """
        stmt = select(QRCode)

        if type:
            stmt = stmt.where(QRCode.type == type)
        if is_active is not None:
            stmt = stmt.where(QRCode.is_active == is_active)

        stmt = stmt.order_by(QRCode.created_at.desc())

        result = await self.db.execute(stmt)
        return result.scalars().all()

    def _parse_user_agent(self, user_agent_string: str) -> dict[str, str]:
        """
        Parse user agent string to extract device information.

        Args:
            user_agent_string: User agent string from request

        Returns:
            Dictionary with device_type, os, browser
        """
        ua = parse(user_agent_string)

        # Determine device type
        if ua.is_mobile:
            device_type = "mobile"
        elif ua.is_tablet:
            device_type = "tablet"
        elif ua.is_pc:
            device_type = "desktop"
        else:
            device_type = "other"

        return {
            "device_type": device_type,
            "os": f"{ua.os.family} {ua.os.version_string}" if ua.os.family else None,
            "browser": (
                f"{ua.browser.family} {ua.browser.version_string}" if ua.browser.family else None
            ),
        }
