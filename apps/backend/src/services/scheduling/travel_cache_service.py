"""
Travel Cache Service
====================

Dual-layer caching for travel time API responses:
1. In-Memory LRU Cache (fast, 1000 entries max)
2. Database Persistence (7-day TTL)

This service significantly reduces Google Maps API costs and improves
response times for repeated travel calculations.

Usage:
    from services.scheduling.travel_cache_service import TravelCacheService

    cache_service = TravelCacheService(db)

    # Check cache first
    cached = await cache_service.get(origin_lat, origin_lng, dest_lat, dest_lng, is_rush_hour)
    if cached:
        return cached  # Cache hit!

    # Calculate via API, then cache
    result = await google_maps_api(...)
    await cache_service.set(origin_lat, origin_lng, dest_lat, dest_lng, is_rush_hour, result)

Cache Key Strategy:
- Coordinates rounded to 3 decimals (~100m precision)
- Rush hour is separate cache key (different travel times)
- Format: "origin_lat:origin_lng:dest_lat:dest_lng:rush_hour"

TTL Strategy:
- LRU Cache: Evicts oldest when > 1000 entries
- Database: 7 days (configurable via TRAVEL_CACHE_TTL_DAYS)

See: apps/backend/src/db/models/travel_cache.py
See: database/migrations/011_travel_cache_table.sql
"""

import logging
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.travel_cache import TravelCache

logger = logging.getLogger(__name__)

# Configuration
LRU_CACHE_MAX_SIZE = 1000  # Max entries in LRU cache
CACHE_TTL_DAYS = 7  # Database cache expiration
COORDINATE_DECIMALS = 3  # Rounding precision (~100m)


@dataclass
class TravelCacheEntry:
    """Cached travel calculation result."""

    travel_time_minutes: int
    distance_miles: float
    is_rush_hour: bool
    source: str  # "google_maps", "openroute", "cache"


class TravelCacheService:
    """
    Dual-layer travel time cache service.

    Layer 1: In-Memory LRU (fast, limited size)
    Layer 2: Database (persistent, 7-day TTL)

    Flow:
    1. Check LRU cache → Return if hit
    2. Check database → Return + populate LRU if hit
    3. Miss → Caller should fetch from API and call set()
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize cache service.

        Args:
            db: SQLAlchemy async session for database operations
        """
        self.db = db
        # LRU cache: OrderedDict maintains insertion order
        # Most recently used items are moved to end
        self._lru_cache: OrderedDict[str, TravelCacheEntry] = OrderedDict()
        self._stats = {
            "lru_hits": 0,
            "lru_misses": 0,
            "db_hits": 0,
            "db_misses": 0,
        }

    @staticmethod
    def _round_coordinate(coord: float) -> float:
        """Round coordinate to configured precision (~100m at 3 decimals)."""
        return round(coord, COORDINATE_DECIMALS)

    @staticmethod
    def _make_cache_key(
        origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float, is_rush_hour: bool
    ) -> str:
        """
        Create cache key from coordinates.

        Coordinates are rounded to 3 decimals for reasonable precision
        while maximizing cache hits.
        """
        o_lat = round(origin_lat, COORDINATE_DECIMALS)
        o_lng = round(origin_lng, COORDINATE_DECIMALS)
        d_lat = round(dest_lat, COORDINATE_DECIMALS)
        d_lng = round(dest_lng, COORDINATE_DECIMALS)
        rush = "1" if is_rush_hour else "0"
        return f"{o_lat}:{o_lng}:{d_lat}:{d_lng}:{rush}"

    def _lru_get(self, key: str) -> Optional[TravelCacheEntry]:
        """Get from LRU cache, moving to end if found (most recently used)."""
        if key in self._lru_cache:
            self._lru_cache.move_to_end(key)
            self._stats["lru_hits"] += 1
            return self._lru_cache[key]
        self._stats["lru_misses"] += 1
        return None

    def _lru_set(self, key: str, entry: TravelCacheEntry) -> None:
        """Set in LRU cache, evicting oldest if at capacity."""
        if key in self._lru_cache:
            self._lru_cache.move_to_end(key)
        else:
            if len(self._lru_cache) >= LRU_CACHE_MAX_SIZE:
                self._lru_cache.popitem(last=False)  # Remove oldest
            self._lru_cache[key] = entry

    async def get(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        is_rush_hour: bool = False,
    ) -> Optional[TravelCacheEntry]:
        """
        Get cached travel calculation.

        Checks LRU cache first, then database.
        Populates LRU cache on database hit.

        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude
            is_rush_hour: Whether this is for rush hour calculation

        Returns:
            TravelCacheEntry if found and not expired, None otherwise
        """
        cache_key = self._make_cache_key(origin_lat, origin_lng, dest_lat, dest_lng, is_rush_hour)

        # Layer 1: Check LRU cache
        lru_entry = self._lru_get(cache_key)
        if lru_entry:
            logger.debug(f"🎯 LRU cache hit: {cache_key}")
            return lru_entry

        # Layer 2: Check database
        try:
            o_lat = self._round_coordinate(origin_lat)
            o_lng = self._round_coordinate(origin_lng)
            d_lat = self._round_coordinate(dest_lat)
            d_lng = self._round_coordinate(dest_lng)

            result = await self.db.execute(
                select(TravelCache)
                .where(
                    and_(
                        TravelCache.origin_lat == o_lat,
                        TravelCache.origin_lng == o_lng,
                        TravelCache.dest_lat == d_lat,
                        TravelCache.dest_lng == d_lng,
                        TravelCache.is_rush_hour == is_rush_hour,
                        TravelCache.expires_at > datetime.now(timezone.utc),  # Not expired
                    )
                )
                .limit(1)
            )
            db_entry = result.scalar_one_or_none()

            if db_entry:
                self._stats["db_hits"] += 1
                logger.debug(f"💾 Database cache hit: {cache_key}")

                # Update hit count (fire and forget)
                await self.db.execute(
                    update(TravelCache)
                    .where(TravelCache.id == db_entry.id)
                    .values(hit_count=TravelCache.hit_count + 1)
                )
                await self.db.commit()

                # Convert to entry and populate LRU
                entry = TravelCacheEntry(
                    travel_time_minutes=db_entry.travel_time_minutes,
                    distance_miles=db_entry.distance_miles,
                    is_rush_hour=db_entry.is_rush_hour,
                    source="cache",  # Marked as from cache
                )
                self._lru_set(cache_key, entry)
                return entry

            self._stats["db_misses"] += 1
            logger.debug(f"❌ Cache miss: {cache_key}")
            return None

        except Exception as e:
            logger.warning(f"⚠️ Cache lookup error: {e}")
            return None

    async def set(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        travel_time_minutes: int,
        distance_miles: float,
        is_rush_hour: bool = False,
        source: str = "google_maps",
    ) -> bool:
        """
        Cache a travel calculation result.

        Saves to both LRU cache and database.

        Args:
            origin_lat: Origin latitude
            origin_lng: Origin longitude
            dest_lat: Destination latitude
            dest_lng: Destination longitude
            travel_time_minutes: Calculated travel time
            distance_miles: Calculated distance
            is_rush_hour: Whether this is for rush hour
            source: Data source ("google_maps", "openroute", "estimate")

        Returns:
            True if successfully cached, False on error
        """
        cache_key = self._make_cache_key(origin_lat, origin_lng, dest_lat, dest_lng, is_rush_hour)

        # Create entry
        entry = TravelCacheEntry(
            travel_time_minutes=travel_time_minutes,
            distance_miles=distance_miles,
            is_rush_hour=is_rush_hour,
            source=source,
        )

        # Layer 1: Add to LRU cache
        self._lru_set(cache_key, entry)

        # Layer 2: Save to database
        try:
            o_lat = self._round_coordinate(origin_lat)
            o_lng = self._round_coordinate(origin_lng)
            d_lat = self._round_coordinate(dest_lat)
            d_lng = self._round_coordinate(dest_lng)

            # Check if entry exists (upsert logic)
            existing = await self.db.execute(
                select(TravelCache)
                .where(
                    and_(
                        TravelCache.origin_lat == o_lat,
                        TravelCache.origin_lng == o_lng,
                        TravelCache.dest_lat == d_lat,
                        TravelCache.dest_lng == d_lng,
                        TravelCache.is_rush_hour == is_rush_hour,
                    )
                )
                .limit(1)
            )
            existing_entry = existing.scalar_one_or_none()

            if existing_entry:
                # Update existing entry
                await self.db.execute(
                    update(TravelCache)
                    .where(TravelCache.id == existing_entry.id)
                    .values(
                        travel_time_minutes=travel_time_minutes,
                        distance_miles=distance_miles,
                        source=source,
                        expires_at=datetime.now(timezone.utc) + timedelta(days=CACHE_TTL_DAYS),
                        hit_count=0,  # Reset on update
                    )
                )
                logger.debug(f"📝 Updated cache entry: {cache_key}")
            else:
                # Create new entry
                new_entry = TravelCache(
                    origin_lat=o_lat,
                    origin_lng=o_lng,
                    dest_lat=d_lat,
                    dest_lng=d_lng,
                    travel_time_minutes=travel_time_minutes,
                    distance_miles=distance_miles,
                    is_rush_hour=is_rush_hour,
                    source=source,
                    expires_at=datetime.now(timezone.utc) + timedelta(days=CACHE_TTL_DAYS),
                )
                self.db.add(new_entry)
                logger.debug(f"✨ Created cache entry: {cache_key}")

            await self.db.commit()
            return True

        except Exception as e:
            logger.error(f"❌ Cache save error: {e}")
            await self.db.rollback()
            return False

    async def cleanup_expired(self) -> int:
        """
        Remove expired cache entries from database.

        Should be run periodically (e.g., daily cron job).

        Returns:
            Number of entries deleted
        """
        try:
            result = await self.db.execute(
                delete(TravelCache).where(TravelCache.expires_at < datetime.now(timezone.utc))
            )
            await self.db.commit()
            deleted = result.rowcount
            logger.info(f"🧹 Cleaned up {deleted} expired cache entries")
            return deleted
        except Exception as e:
            logger.error(f"❌ Cache cleanup error: {e}")
            await self.db.rollback()
            return 0

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with hit/miss counts and hit rates
        """
        total_lru = self._stats["lru_hits"] + self._stats["lru_misses"]
        total_db = self._stats["db_hits"] + self._stats["db_misses"]

        return {
            "lru_size": len(self._lru_cache),
            "lru_max_size": LRU_CACHE_MAX_SIZE,
            "lru_hits": self._stats["lru_hits"],
            "lru_misses": self._stats["lru_misses"],
            "lru_hit_rate": self._stats["lru_hits"] / total_lru if total_lru > 0 else 0,
            "db_hits": self._stats["db_hits"],
            "db_misses": self._stats["db_misses"],
            "db_hit_rate": self._stats["db_hits"] / total_db if total_db > 0 else 0,
        }

    def clear_lru(self) -> None:
        """Clear the LRU cache (useful for testing)."""
        self._lru_cache.clear()
        logger.info("🗑️ LRU cache cleared")
