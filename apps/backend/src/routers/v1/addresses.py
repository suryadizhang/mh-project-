"""
Address API Router

Enterprise address management endpoints:
- Create/geocode addresses with caching
- Get customer saved addresses
- Set default address
- Validate service area

This router uses the enterprise AddressService pattern where:
1. First check = cache lookup (free)
2. Cache miss = Google API call + permanent cache
3. Same address = instant travel fee calculation

IMPORTANT: Route ordering matters in FastAPI!
Static routes MUST come before dynamic routes (/{address_id}).
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.scheduling import (
    AddressCreateRequest,
    AddressResponse,
    CustomerAddressListResponse,
)
from services.address_service import AddressService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/addresses", tags=["Addresses"])


# ============================================================================
# STATIC ROUTES FIRST (must come before /{address_id})
# ============================================================================


@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_or_find_address(
    request: AddressCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new address or return existing cached address.

    Enterprise Pattern:
    - If address already exists in cache: return immediately (no API call)
    - If new address: geocode with Google and cache permanently

    Benefits:
    - Pay Google once per unique address
    - Instant response for returning customers
    - "My Addresses" feature for customer portal
    """
    address_service = AddressService(db)

    try:
        # This checks cache first, then geocodes if needed
        address = await address_service.find_or_create_address(
            raw_address=request.raw_address,
            customer_id=request.customer_id,
            label=request.label,
            is_default=request.is_default,
        )

        # Determine if this was a cache hit
        is_cached = address.geocode_status == "success" and address.geocoded_at is not None

        return AddressResponse(
            id=address.id,
            raw_address=address.raw_address,
            formatted_address=address.formatted_address,
            lat=address.lat,
            lng=address.lng,
            city=address.city,
            state=address.state,
            zip_code=address.zip_code,
            geocode_status=address.geocode_status,
            is_cached=is_cached,
            is_serviceable=address.is_serviceable,
        )

    except Exception as e:
        logger.error(f"Error creating address: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process address. Please try again.",
        )


@router.get("/check-service-area")
async def check_service_area(
    address: str = Query(..., min_length=10, description="Full street address"),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if an address is within our service area.

    Multi-station support: Finds nearest active station and checks distance.
    Service Area: California - 150 mile radius from nearest station.
    Distances > 150 miles require human escalation.

    Also returns geocoded coordinates for travel fee calculation.
    """
    address_service = AddressService(db)

    # This will geocode and cache
    addr = await address_service.find_or_create_address(raw_address=address)

    if addr.geocode_status != "success":
        return {
            "is_serviceable": False,
            "reason": "Could not verify address location",
            "suggestion": "Please enter a valid street address",
            "service_area": "California - Bay Area, Sacramento, Central Valley",
        }

    # Get station info if serviceable
    station_code = None
    distance_miles = None
    requires_escalation = False

    if addr.service_station_id:
        # Query station for code
        from db.models.identity import Station
        from sqlalchemy import select

        stmt = select(Station).where(Station.id == addr.service_station_id)
        result = await db.execute(stmt)
        station = result.scalar_one_or_none()
        if station:
            station_code = station.code
            if addr.distance_to_station_km:
                distance_miles = float(addr.distance_to_station_km) * 0.621371
                requires_escalation = station.requires_escalation(float(addr.lat), float(addr.lng))

    # Build response with service area info
    response = {
        "is_serviceable": addr.is_serviceable,
        "lat": float(addr.lat) if addr.lat else None,
        "lng": float(addr.lng) if addr.lng else None,
        "city": addr.city,
        "state": addr.state,
        "formatted_address": addr.formatted_address,
        "distance_to_station_km": (
            float(addr.distance_to_station_km) if addr.distance_to_station_km else None
        ),
        "distance_to_station_miles": round(distance_miles, 1) if distance_miles else None,
        "station_code": station_code,
        "requires_escalation": requires_escalation,
        "service_area": "California - Bay Area, Sacramento, Central Valley",
    }

    if not addr.is_serviceable:
        response["reason"] = (
            f"Sorry, we currently only serve California within 150 miles of our stations. "
            f"Your address is in {addr.state or 'an unsupported area'}."
        )
        response["suggestion"] = "Please contact us if you'd like to request service in your area."
    elif requires_escalation:
        response["reason"] = (
            f"Your address is {round(distance_miles, 0):.0f} miles from our nearest station. "
            f"A team member will confirm availability."
        )
        response["suggestion"] = None
    else:
        response["reason"] = None
        response["suggestion"] = None

    return response


@router.post("/bulk-geocode")
async def bulk_geocode_addresses(
    addresses: list[str],
    db: AsyncSession = Depends(get_db),
):
    """
    Geocode multiple addresses at once.

    Rate-limited to prevent Google API abuse.
    Maximum 50 addresses per request.
    """
    if len(addresses) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 addresses per request",
        )

    address_service = AddressService(db)
    results = []

    for addr_str in addresses:
        try:
            addr = await address_service.find_or_create_address(raw_address=addr_str)
            results.append(
                {
                    "input": addr_str,
                    "success": addr.geocode_status == "success",
                    "formatted": addr.formatted_address,
                    "lat": float(addr.lat) if addr.lat else None,
                    "lng": float(addr.lng) if addr.lng else None,
                }
            )
        except Exception as e:
            results.append(
                {
                    "input": addr_str,
                    "success": False,
                    "error": str(e),
                }
            )

    return {
        "total": len(addresses),
        "successful": sum(1 for r in results if r.get("success")),
        "results": results,
    }


# ============================================================================
# Customer Saved Addresses (has /customer/ prefix before variable)
# ============================================================================


@router.get("/customer/{customer_id}", response_model=CustomerAddressListResponse)
async def get_customer_addresses(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all saved addresses for a customer.

    Use Case: "My Addresses" feature in customer portal.
    Returns addresses ordered by: default first, then by most recent.
    """
    address_service = AddressService(db)

    addresses = await address_service.get_customer_addresses(customer_id)

    return CustomerAddressListResponse(
        addresses=[
            AddressResponse(
                id=addr.id,
                raw_address=addr.raw_address,
                formatted_address=addr.formatted_address,
                lat=addr.lat,
                lng=addr.lng,
                city=addr.city,
                state=addr.state,
                zip_code=addr.zip_code,
                geocode_status=addr.geocode_status,
                is_cached=True,
                is_serviceable=addr.is_serviceable,
            )
            for addr in addresses
        ],
        count=len(addresses),
    )


@router.post("/customer/{customer_id}/default/{address_id}")
async def set_default_address(
    customer_id: UUID,
    address_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Set an address as the customer's default.

    Clears is_default from all other addresses for this customer.
    """
    address_service = AddressService(db)

    success = await address_service.set_default_address(customer_id, address_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found or does not belong to customer",
        )

    return {"success": True, "message": "Default address updated"}


# ============================================================================
# DYNAMIC ROUTES LAST (/{address_id} matches anything)
# ============================================================================


@router.get("/{address_id}", response_model=AddressResponse)
async def get_address(
    address_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get address by ID.
    """
    address_service = AddressService(db)

    address = await address_service.get_address_by_id(address_id)

    if not address:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    return AddressResponse(
        id=address.id,
        raw_address=address.raw_address,
        formatted_address=address.formatted_address,
        lat=address.lat,
        lng=address.lng,
        city=address.city,
        state=address.state,
        zip_code=address.zip_code,
        geocode_status=address.geocode_status,
        is_cached=True,  # If we found it, it's cached
        is_serviceable=address.is_serviceable,
    )
