"""
Enterprise Address Management Model

Enterprise-grade address handling following Uber/DoorDash/Lyft patterns:
- Separate reusable address table
- Cached geocoding (pay once, use forever)
- Customer saved addresses ("Home", "Work", "Mom's House")
- Same address = instant travel fee (no Google API call)
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# CRITICAL: Use same Base as other models (unified metadata registry)
from ..base_class import Base


class Address(Base):
    """
    Enterprise address management table.

    Benefits:
    - Geocoding is cached (pay Google once per address, not per booking)
    - Customers can save addresses for reuse
    - Same address = instant travel fee calculation
    - Enables "My Addresses" feature in customer portal
    """

    __tablename__ = "addresses"
    __table_args__ = (
        Index("idx_addresses_geocode", "lat", "lng", postgresql_where="lat IS NOT NULL"),
        Index("idx_addresses_customer", "customer_id", postgresql_where="customer_id IS NOT NULL"),
        Index(
            "idx_addresses_place_id",
            "google_place_id",
            postgresql_where="google_place_id IS NOT NULL",
        ),
        Index("idx_addresses_zip", "zip_code"),
        Index(
            "idx_addresses_unique_customer",
            "customer_id",
            "raw_address",
            unique=True,
            postgresql_where="customer_id IS NOT NULL",
        ),
        {"schema": "core"},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    # Raw input (what customer typed)
    raw_address: Mapped[str] = mapped_column(Text, nullable=False)

    # Google normalized components
    formatted_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    street_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    street_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unit_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Apt, Suite
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="USA")

    # Geocoding (from Google Maps)
    lat: Mapped[Optional[float]] = mapped_column(Numeric(10, 8), nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(Numeric(11, 8), nullable=True)
    google_place_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    geocode_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, success, failed, partial
    geocoded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    geocode_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="google")

    # Location metadata
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_residential: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    location_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # ROOFTOP, etc.

    # Customer ownership (for saved addresses)
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("core.customers.id", ondelete="CASCADE"), nullable=True
    )
    address_label: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # "Home", "Work"
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Service area check
    is_serviceable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    service_station_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    distance_to_station_km: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    customer = relationship("Customer", back_populates="addresses", lazy="selectin")
    bookings = relationship("Booking", back_populates="venue_address", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Address {self.formatted_address or self.raw_address[:50]}>"

    @property
    def is_geocoded(self) -> bool:
        """Check if address has been successfully geocoded."""
        return self.geocode_status == "success" and self.lat is not None

    @property
    def coordinates(self) -> tuple[float, float] | None:
        """Get lat/lng tuple if geocoded."""
        if self.lat and self.lng:
            return (float(self.lat), float(self.lng))
        return None

    @property
    def short_address(self) -> str:
        """Get a short display version of the address."""
        if self.city and self.state:
            return f"{self.city}, {self.state}"
        return self.raw_address[:50]


class GeocodeStatus:
    """Constants for geocode status."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"  # Some fields missing
