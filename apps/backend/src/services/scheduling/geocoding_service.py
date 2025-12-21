"""
Geocoding Service - Adapter for AddressService

This is an adapter that wraps AddressService to provide the interface
expected by the scheduling router. Uses the enterprise address caching pattern.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from services.address_service import AddressService

logger = logging.getLogger(__name__)


@dataclass
class GeocodedAddress:
    """Result from geocoding operation."""

    original_address: str
    normalized_address: Optional[str]
    lat: Optional[float]
    lng: Optional[float]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    is_valid: bool
    confidence: float = 1.0


class GeocodingService:
    """
    Adapter service for geocoding that uses enterprise AddressService.

    Benefits:
    - Uses cached geocoding from AddressService
    - No duplicate API calls for same addresses
    - Provides scheduling-router-compatible interface
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.address_service = AddressService(db)

    async def geocode(self, address: str) -> Optional[GeocodedAddress]:
        """
        Geocode an address using the caching AddressService.

        Returns GeocodedAddress dataclass or None if geocoding fails.
        """
        try:
            # Use enterprise address service (caches result)
            addr = await self.address_service.find_or_create_address(
                raw_address=address,
                customer_id=None,  # Don't link to customer for simple geocoding
            )

            if addr.geocode_status == "success":
                return GeocodedAddress(
                    original_address=address,
                    normalized_address=addr.formatted_address,
                    lat=float(addr.lat) if addr.lat else None,
                    lng=float(addr.lng) if addr.lng else None,
                    city=addr.city,
                    state=addr.state,
                    zip_code=addr.zip_code,
                    is_valid=True,
                    confidence=1.0,
                )
            else:
                # Geocoding failed but we still have the record
                return GeocodedAddress(
                    original_address=address,
                    normalized_address=None,
                    lat=None,
                    lng=None,
                    city=None,
                    state=None,
                    zip_code=None,
                    is_valid=False,
                    confidence=0.0,
                )

        except Exception as e:
            logger.error(f"Geocoding error for {address[:50]}...: {e}")
            return None

    async def validate_address(self, address: str) -> tuple[bool, str]:
        """
        Validate an address string.

        Returns (is_valid, message).
        """
        if not address or len(address.strip()) < 10:
            return False, "Address too short. Please provide a full street address."

        result = await self.geocode(address)

        if result is None:
            return False, "Could not process address. Please try again."

        if not result.is_valid:
            return False, "Address could not be verified. Please check and try again."

        if not result.lat or not result.lng:
            return False, "Could not determine location. Please provide more details."

        return True, f"Address verified: {result.normalized_address or address}"
