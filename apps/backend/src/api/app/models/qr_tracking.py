"""
QR Code Tracking Models
Tracks QR code scans from business cards, flyers, and other marketing materials
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship

from api.app.models.declarative_base import Base


class QRCodeType(str, PyEnum):
    """Types of QR codes"""
    BUSINESS_CARD = "business_card"
    FLYER = "flyer"
    MENU = "menu"
    VEHICLE = "vehicle"
    BANNER = "banner"
    OTHER = "other"


class QRCode(Base):
    """
    QR Code Definition
    Represents a unique QR code used in marketing materials
    """
    __tablename__ = "qr_codes"
    __table_args__ = {"schema": "marketing"}

    id: UUID = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    code: str = Column(String(50), unique=True, nullable=False, index=True)
    type: QRCodeType = Column(
        Enum('business_card', 'flyer', 'menu', 'vehicle', 'banner', 'other', 
             schema="marketing", name="qr_code_type"),
        nullable=False
    )
    destination_url: str = Column(String(500), nullable=False)
    description: Optional[str] = Column(Text, nullable=True)
    campaign_name: Optional[str] = Column(String(100), nullable=True)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    created_at: datetime = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_by: Optional[UUID] = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("core.users.id", ondelete="SET NULL"),
        nullable=True
    )
    extra_metadata: Optional[dict] = Column('metadata', JSONB, nullable=True)  # Renamed to avoid SQLAlchemy conflict

    # Relationships
    scans = relationship("QRScan", back_populates="qr_code", cascade="all, delete-orphan")

    @property
    def total_scans(self) -> int:
        """Total number of scans"""
        return len(self.scans)

    @property
    def unique_scans(self) -> int:
        """Unique scans based on IP address"""
        return len(set(scan.ip_address for scan in self.scans if scan.ip_address))

    @property
    def conversion_rate(self) -> float:
        """Percentage of scans that converted to bookings"""
        if not self.scans:
            return 0.0
        converted = sum(1 for scan in self.scans if scan.converted_to_booking)
        return round((converted / len(self.scans)) * 100, 2)

    def __repr__(self):
        return f"<QRCode {self.code} ({self.type})>"


class QRScan(Base):
    """
    QR Code Scan Event
    Records each time a QR code is scanned with device and location data
    """
    __tablename__ = "qr_scans"
    __table_args__ = {"schema": "marketing"}

    id: UUID = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    qr_code_id: UUID = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("marketing.qr_codes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    scanned_at: datetime = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        index=True
    )

    # Device Information
    ip_address: Optional[str] = Column(String(45), nullable=True)
    user_agent: Optional[str] = Column(Text, nullable=True)
    device_type: Optional[str] = Column(String(50), nullable=True)  # mobile, tablet, desktop
    os: Optional[str] = Column(String(50), nullable=True)  # iOS, Android, Windows
    browser: Optional[str] = Column(String(50), nullable=True)

    # Location Information (from IP geolocation)
    city: Optional[str] = Column(String(100), nullable=True)
    region: Optional[str] = Column(String(100), nullable=True)
    country: Optional[str] = Column(String(2), nullable=True)
    latitude: Optional[float] = Column(Numeric(10, 7), nullable=True)
    longitude: Optional[float] = Column(Numeric(10, 7), nullable=True)

    # Tracking
    referrer: Optional[str] = Column(String(500), nullable=True)
    session_id: Optional[str] = Column(String(100), nullable=True, index=True)

    # Conversion Tracking
    converted_to_lead: bool = Column(Boolean, default=False, nullable=False)
    converted_to_booking: bool = Column(Boolean, default=False, nullable=False)
    conversion_value: Optional[float] = Column(Numeric(10, 2), nullable=True)

    # Additional metadata
    extra_metadata: Optional[dict] = Column('metadata', JSONB, nullable=True)  # Renamed to avoid SQLAlchemy conflict

    # Relationships
    qr_code = relationship("QRCode", back_populates="scans")

    @property
    def location_display(self) -> str:
        """Human-readable location"""
        parts = []
        if self.city:
            parts.append(self.city)
        if self.region:
            parts.append(self.region)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts) if parts else "Unknown"

    def __repr__(self):
        return f"<QRScan {self.qr_code.code} at {self.scanned_at}>"
