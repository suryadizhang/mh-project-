"""
Travel Cache Database Model
===========================

SQLAlchemy model for persisting travel time calculations.
Used in conjunction with in-memory LRU cache for dual-layer caching.

Cache Strategy:
1. In-memory LRU cache (fast access, limited size)
2. Database persistence (7-day expiry, survives restarts)

Coordinate Precision:
- Rounded to 3 decimal places (~100m precision)
- Ensures cache hits for nearby locations

Table: public.travel_cache

Related:
- services/scheduling/travel_cache_service.py
- services/scheduling/travel_time_service.py
- 20-SINGLE_SOURCE_OF_TRUTH.instructions.md
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from db.base_class import Base

# Cache expiry: 7 days (travel times don't change frequently)
CACHE_EXPIRY_DAYS = 7


class TravelCache(Base):
    """
    Persistent cache for travel time calculations.

    Stores Google Maps API responses to reduce API calls and costs.
    Coordinates are rounded to 3 decimal places for better cache hit rates.

    Attributes:
        id: Unique cache entry ID
        origin_lat: Origin latitude (3 decimal precision)
        origin_lng: Origin longitude (3 decimal precision)
        dest_lat: Destination latitude (3 decimal precision)
        dest_lng: Destination longitude (3 decimal precision)
        travel_time_minutes: Calculated travel time
        distance_miles: Calculated distance
        is_rush_hour: Whether rush hour multiplier was applied
        source: API source ("google_maps", "openroute", "estimate")
        created_at: When the cache entry was created
        expires_at: When the cache entry expires (7 days from creation)
        hit_count: Number of times this cache entry was used

    Indexes:
        - idx_travel_cache_coords: Composite index on all 4 coordinates
        - idx_travel_cache_expires: Index on expires_at for cleanup jobs
    """

    __tablename__ = "travel_cache"
    __table_args__ = (
        # Composite index for coordinate lookups (most common query)
        Index(
            "idx_travel_cache_coords",
            "origin_lat",
            "origin_lng",
            "dest_lat",
            "dest_lng",
        ),
        # Index for cleanup job (delete expired entries)
        Index("idx_travel_cache_expires", "expires_at"),
        {"schema": "public"},
    )

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # Coordinates (rounded to 3 decimal places = ~100m precision)
    origin_lat: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    origin_lng: Mapped[float] = mapped_column(Float, nullable=False)
    dest_lat: Mapped[float] = mapped_column(Float, nullable=False)
    dest_lng: Mapped[float] = mapped_column(Float, nullable=False)

    # Travel data
    travel_time_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_miles: Mapped[float] = mapped_column(Float, nullable=False)
    is_rush_hour: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Source tracking
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="google_maps",
        comment="API source: google_maps, openroute, estimate",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("NOW()"),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.utcnow() + timedelta(days=CACHE_EXPIRY_DAYS),
    )

    # Usage tracking
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return (
            f"<TravelCache("
            f"origin=({self.origin_lat}, {self.origin_lng}), "
            f"dest=({self.dest_lat}, {self.dest_lng}), "
            f"time={self.travel_time_minutes}min, "
            f"distance={self.distance_miles}mi, "
            f"source={self.source}"
            f")>"
        )

    @classmethod
    def round_coordinate(cls, value: float, decimals: int = 3) -> float:
        """
        Round coordinate to specified decimal places.

        Default 3 decimals = ~100m precision, good balance between
        cache hit rate and accuracy.

        Args:
            value: Coordinate value to round
            decimals: Number of decimal places (default: 3)

        Returns:
            Rounded coordinate value
        """
        return round(value, decimals)

    @classmethod
    def create_cache_key(
        cls,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> str:
        """
        Create a standardized cache key for coordinates.

        Rounds coordinates to 3 decimal places for consistency.

        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude

        Returns:
            String cache key in format "lat1_lng1_lat2_lng2"
        """
        return (
            f"{cls.round_coordinate(origin_lat)}_"
            f"{cls.round_coordinate(origin_lng)}_"
            f"{cls.round_coordinate(dest_lat)}_"
            f"{cls.round_coordinate(dest_lng)}"
        )

    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return datetime.utcnow() > self.expires_at if self.expires_at else True

    def increment_hit_count(self) -> None:
        """Increment the hit count for this cache entry."""
        self.hit_count += 1
