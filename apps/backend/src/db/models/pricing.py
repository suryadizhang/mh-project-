"""
Pricing Models - Core Schema
=============================

Dynamic pricing configuration models:
- MenuItem: Menu items (proteins, sides, sauces)
- AddonItem: Premium upgrades and enhancements
- TravelFeeConfiguration: Station-based travel fee rules

All models use:
- UUID primary keys
- Timezone-aware datetime fields
- Schema qualification (__table_args__)
- Proper foreign key relationships
- Type hints for IDE support
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy import (
    String,
    Text,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base


class TravelFeeConfiguration(Base):
    """
    Travel Fee Configuration - Station-based travel fee rules.

    Business Requirements:
    - Multi-station support (different locations, different rules)
    - Dynamic fee calculation based on distance
    - Configurable free miles threshold
    - Configurable per-mile rate
    - Station-specific pricing flexibility
    - Admin-manageable via pricing UI

    Travel Fee Calculation Logic:
    1. Calculate distance from station address to customer address
    2. If distance <= free_miles → fee = $0
    3. If distance > free_miles → fee = (distance - free_miles) × price_per_mile
    4. Round to 2 decimal places

    Examples:
    - Station 1: Fremont, CA
      - Address: 47481 Towhee St, Fremont, CA 94539
      - Free miles: 30
      - Per mile: $2.00
      - Customer 20 miles away → $0 (within free range)
      - Customer 45 miles away → $30 (15 miles × $2.00)

    - Station 2: San Jose, CA (future expansion)
      - Address: [TBD]
      - Free miles: 25
      - Per mile: $2.50
      - Different rules for different market

    Admin UI Features:
    - View all station travel fee configurations
    - Edit station address (for distance calculation)
    - Update free miles threshold
    - Update per-mile rate
    - Enable/disable specific station
    - Add new stations with custom rules

    Access Control:
    - Creation: super_admin only
    - Update: super_admin, station admin
    - Delete: super_admin only (soft delete via is_active)
    - View: super_admin, station admin, API (for booking quotes)

    Data Flow:
    1. Customer requests quote → includes customer address
    2. Backend finds nearest active station
    3. Backend loads TravelFeeConfiguration for that station
    4. Backend calculates distance (Google Maps API / geocoding)
    5. Backend applies travel fee rules
    6. Return total with breakdown (base + travel + gratuity)

    Future Enhancements:
    - Zone-based pricing (e.g., San Francisco premium zone)
    - Time-based pricing (e.g., weekend surcharge)
    - Seasonal adjustments (e.g., holiday pricing)
    - Multi-station dispatch (send closest available chef)
    """

    __tablename__ = "travel_fee_configurations"
    __table_args__ = (
        CheckConstraint("free_miles >= 0", name="travel_fee_free_miles_non_negative"),
        CheckConstraint("price_per_mile >= 0", name="travel_fee_price_per_mile_non_negative"),
        CheckConstraint(
            "max_service_distance IS NULL OR max_service_distance >= free_miles",
            name="travel_fee_max_distance_valid",
        ),
        UniqueConstraint("station_id", name="unique_station_travel_fee"),
        Index("idx_travel_fee_station_id", "station_id"),
        Index("idx_travel_fee_is_active", "is_active"),
        {"schema": "core", "extend_existing": True},
    )

    # Primary Key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    station_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("identity.stations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One configuration per station
    )

    # Station Location (for distance calculation)
    # NOTE: Duplicates Station.address fields for performance (avoid JOIN on every quote)
    # Admin UI syncs these fields when updating station
    station_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Station display name (e.g., 'Fremont Station')"
    )
    station_address: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Full street address (e.g., '47481 Towhee St')"
    )
    station_city: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="City (e.g., 'Fremont')"
    )
    station_state: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="State code (e.g., 'CA')"
    )
    station_postal_code: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="ZIP/postal code (e.g., '94539')"
    )
    station_latitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=7),
        nullable=True,
        comment="Latitude for distance calculation (geocoded)",
    )
    station_longitude: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=10, scale=7),
        nullable=True,
        comment="Longitude for distance calculation (geocoded)",
    )

    # Travel Fee Rules
    free_miles: Mapped[Decimal] = mapped_column(
        Numeric(precision=6, scale=2),
        nullable=False,
        server_default="30.00",
        comment="Miles included free (e.g., 30.00)",
    )
    price_per_mile: Mapped[Decimal] = mapped_column(
        Numeric(precision=6, scale=2),
        nullable=False,
        server_default="2.00",
        comment="Rate per mile beyond free miles (e.g., 2.00 = $2/mile)",
    )
    max_service_distance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=6, scale=2),
        nullable=True,
        comment="Maximum service distance in miles (NULL = unlimited)",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        index=True,
        comment="Whether this station accepts bookings",
    )

    # Additional Settings (future expansion)
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="'{}'",
        comment="Additional travel fee settings (zone pricing, time-based, etc.)",
    )

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Admin notes (e.g., 'Main station - covers Bay Area')"
    )

    # Display Order (for admin UI sorting)
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Display order in admin UI (lower = higher priority)",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    # NOTE: Station relationship available via ForeignKey
    # station: Mapped["Station"] = relationship("Station", back_populates="travel_fee_config")

    def __repr__(self) -> str:
        return (
            f"<TravelFeeConfiguration("
            f"id={self.id}, "
            f"station={self.station_name}, "
            f"free_miles={self.free_miles}, "
            f"price_per_mile={self.price_per_mile}, "
            f"active={self.is_active}"
            f")>"
        )

    def calculate_travel_fee(self, distance_miles: Decimal) -> Decimal:
        """
        Calculate travel fee based on distance.

        Args:
            distance_miles: Distance from station to customer (in miles)

        Returns:
            Travel fee amount (Decimal, 2 decimal places)

        Logic:
            - If distance <= free_miles → $0
            - If distance > free_miles → (distance - free_miles) × price_per_mile
            - If max_service_distance set and exceeded → raise ValueError

        Examples:
            >>> config = TravelFeeConfiguration(free_miles=30, price_per_mile=2)
            >>> config.calculate_travel_fee(Decimal("20"))
            Decimal("0.00")
            >>> config.calculate_travel_fee(Decimal("45"))
            Decimal("30.00")  # (45 - 30) × 2 = 15 × 2 = 30
        """
        from decimal import Decimal, ROUND_HALF_UP

        # Validate max service distance
        if self.max_service_distance is not None:
            if distance_miles > self.max_service_distance:
                raise ValueError(
                    f"Service distance {distance_miles} miles exceeds maximum "
                    f"{self.max_service_distance} miles for {self.station_name}"
                )

        # Calculate fee
        if distance_miles <= self.free_miles:
            return Decimal("0.00")

        billable_miles = distance_miles - self.free_miles
        fee = billable_miles * self.price_per_mile

        # Round to 2 decimal places
        return fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def get_full_address(self) -> str:
        """Get formatted full address for geocoding."""
        return (
            f"{self.station_address}, "
            f"{self.station_city}, "
            f"{self.station_state} "
            f"{self.station_postal_code}"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "station_id": str(self.station_id),
            "station_name": self.station_name,
            "station_address": self.get_full_address(),
            "latitude": float(self.station_latitude) if self.station_latitude else None,
            "longitude": float(self.station_longitude) if self.station_longitude else None,
            "free_miles": float(self.free_miles),
            "price_per_mile": float(self.price_per_mile),
            "max_service_distance": (
                float(self.max_service_distance) if self.max_service_distance else None
            ),
            "is_active": self.is_active,
            "settings": self.settings,
            "notes": self.notes,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
