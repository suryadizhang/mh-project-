"""
Public Quote Calculation Endpoint (No Authentication Required)

This module handles public quote calculations for the customer website.
Uses BusinessConfig for dynamic pricing values.
Uses TravelTimeService for accurate Google Maps distance calculations.

Endpoints:
- POST /calculate - Calculate party quote with travel fee
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from services.business_config_service import get_business_config
from services.scheduling import GeocodingService, TravelTimeService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["public-quote"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================


class QuoteRequest(BaseModel):
    """Schema for quote calculation request."""

    adults: int = Field(..., ge=0, le=100, description="Number of adults (13+)")
    children: int = Field(default=0, ge=0, le=50, description="Number of children (6-12)")

    # Upgrade proteins (price per serving)
    salmon: int = Field(default=0, ge=0, description="Number of salmon upgrades")
    scallops: int = Field(default=0, ge=0, description="Number of scallop upgrades")
    filet_mignon: int = Field(default=0, ge=0, description="Number of filet mignon upgrades")
    lobster_tail: int = Field(default=0, ge=0, description="Number of lobster tail upgrades")
    extra_proteins: int = Field(default=0, ge=0, description="Number of extra protein additions")

    # Add-ons (per serving)
    yakisoba_noodles: int = Field(default=0, ge=0, description="Number of yakisoba noodle portions")
    extra_fried_rice: int = Field(
        default=0, ge=0, description="Number of extra fried rice portions"
    )
    extra_vegetables: int = Field(default=0, ge=0, description="Number of extra vegetable portions")
    edamame: int = Field(default=0, ge=0, description="Number of edamame portions")
    gyoza: int = Field(default=0, ge=0, description="Number of gyoza portions")

    # Location for travel fee calculation (at least one method required)
    venue_address: str | None = Field(
        default=None, description="Full venue address for travel calculation"
    )
    zip_code: str | None = Field(
        default=None, description="ZIP code for fallback travel calculation"
    )
    # Pre-geocoded coordinates (from frontend Google Places)
    venue_lat: float | None = Field(
        default=None, description="Venue latitude (if already geocoded)"
    )
    venue_lng: float | None = Field(
        default=None, description="Venue longitude (if already geocoded)"
    )

    @property
    def has_location(self) -> bool:
        """Check if at least one location method is provided."""
        return bool(
            self.venue_address
            or self.zip_code
            or (self.venue_lat is not None and self.venue_lng is not None)
        )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "adults": 10,
                    "children": 2,
                    "salmon": 2,
                    "lobster_tail": 1,
                    "venue_address": "123 Main St, San Jose, CA 95123",
                }
            ]
        }
    }


class TravelInfo(BaseModel):
    """Travel fee calculation details."""

    distance_miles: float | None = None
    duration_minutes: int | None = None
    travel_fee: float = 0.0
    free_miles: int = 30
    per_mile_rate: float = 2.0
    station_name: str = "Fremont Station"
    source: str = "estimate"  # 'google_maps', 'cache', 'estimate'


class QuoteResponse(BaseModel):
    """Schema for quote calculation response."""

    # Breakdown
    adults: int
    children: int
    adult_price: float
    child_price: float
    base_total: float
    upgrade_total: float
    addon_total: float
    subtotal: float

    # Travel
    travel_info: TravelInfo | None = None

    # Final
    grand_total: float
    deposit_required: float
    balance_due: float

    # Metadata
    party_minimum: float
    applied_minimum: bool = False


# ============================================================================
# UPGRADE AND ADDON PRICING (from menu)
# ============================================================================

# Upgrade prices (per serving)
UPGRADE_PRICES = {
    "salmon": 7.00,  # Premium seafood upgrade
    "scallops": 9.00,  # Premium seafood upgrade
    "filet_mignon": 10.00,  # Premium beef upgrade
    "lobster_tail": 20.00,  # Luxury upgrade
    "extra_protein": 10.00,  # Add an extra protein (+$10, premium adds upgrade price)
}

# Addon prices (per serving)
ADDON_PRICES = {
    "yakisoba_noodles": 5.00,
    "extra_fried_rice": 5.00,
    "extra_vegetables": 5.00,
    "edamame": 5.00,
    "gyoza": 10.00,
}


# ============================================================================
# PUBLIC ENDPOINTS
# ============================================================================


@router.post(
    "/calculate",
    response_model=QuoteResponse,
    summary="Calculate party quote (PUBLIC)",
    description="""
    Calculate a hibachi party quote with dynamic pricing from BusinessConfig.
    No authentication required - used by customer website.

    ## Pricing (from BusinessConfig):
    - Adult price: $55/person (13+)
    - Child price: $30/person (6-12)
    - Children under 5: FREE
    - Party minimum: $550

    ## Upgrades (per serving):
    - Salmon: +$7
    - Scallops: +$9
    - Filet Mignon: +$10
    - Lobster Tail: +$20
    - Extra Protein: +$10 (premium adds upgrade price)

    ## Add-ons (per serving):
    - Yakisoba Noodles: +$5
    - Extra Fried Rice: +$5
    - Extra Vegetables: +$5
    - Edamame: +$5
    - Gyoza: +$10

    ## Travel Fee:
    - First 30 miles: FREE
    - After 30 miles: $2/mile

    ## Deposit:
    - Fixed $100 deposit required
    """,
)
async def calculate_quote(
    request: QuoteRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Calculate party quote with travel fee.
    Uses BusinessConfig for dynamic pricing values.
    """
    try:
        # Validate location is provided (industry best practice: fail fast with clear error)
        if not request.has_location:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Location required",
                    "message": "Please provide venue location using one of: venue_address, zip_code, or (venue_lat, venue_lng)",
                    "fields": ["venue_address", "zip_code", "venue_lat", "venue_lng"],
                },
            )

        # Get dynamic pricing from BusinessConfig
        config = await get_business_config(db)

        adult_price = config.adult_price_cents / 100  # $55.00
        child_price = config.child_price_cents / 100  # $30.00
        party_minimum = config.party_minimum_cents / 100  # $550.00
        deposit_amount = config.deposit_amount_cents / 100  # $100.00
        free_miles = config.travel_free_miles  # 30
        per_mile_rate = config.travel_per_mile_cents / 100  # $2.00

        logger.info(
            f"📊 Quote calculation using {config.source} config: adult=${adult_price}, child=${child_price}"
        )

        # Calculate base total
        base_total = (request.adults * adult_price) + (request.children * child_price)

        # Calculate upgrade total
        upgrade_total = 0.0
        upgrade_total += request.salmon * UPGRADE_PRICES["salmon"]
        upgrade_total += request.scallops * UPGRADE_PRICES["scallops"]
        upgrade_total += request.filet_mignon * UPGRADE_PRICES["filet_mignon"]
        upgrade_total += request.lobster_tail * UPGRADE_PRICES["lobster_tail"]
        upgrade_total += request.extra_proteins * UPGRADE_PRICES["extra_protein"]

        # Calculate addon total
        addon_total = 0.0
        addon_total += request.yakisoba_noodles * ADDON_PRICES["yakisoba_noodles"]
        addon_total += request.extra_fried_rice * ADDON_PRICES["extra_fried_rice"]
        addon_total += request.extra_vegetables * ADDON_PRICES["extra_vegetables"]
        addon_total += request.edamame * ADDON_PRICES["edamame"]
        addon_total += request.gyoza * ADDON_PRICES["gyoza"]

        # Calculate subtotal (before minimum and travel)
        subtotal = base_total + upgrade_total + addon_total

        # Apply party minimum
        applied_minimum = False
        if subtotal < party_minimum:
            subtotal = party_minimum
            applied_minimum = True

        # Calculate travel fee using TravelTimeService (Google Maps) or fallback
        travel_info = TravelInfo(
            free_miles=free_miles,
            per_mile_rate=per_mile_rate,
            station_name="Fremont Station (Bay Area)",
            source="estimate",
        )

        # Station location (Fremont) - would come from travel_fee_configurations table
        station_lat = 37.5485  # Fremont, CA
        station_lng = -121.9886

        venue_lat = request.venue_lat
        venue_lng = request.venue_lng

        # If coordinates not provided, try to geocode the address
        if (venue_lat is None or venue_lng is None) and request.venue_address:
            try:
                geocoding_service = GeocodingService(db)
                geocode_result = await geocoding_service.geocode(request.venue_address)
                if geocode_result and geocode_result.is_valid:
                    venue_lat = geocode_result.lat
                    venue_lng = geocode_result.lng
                    logger.debug(f"Geocoded venue: {venue_lat}, {venue_lng}")
            except Exception as e:
                logger.warning(f"Geocoding failed, using ZIP fallback: {e}")

        # If we have coordinates, use Google Maps Distance Matrix for accurate distance
        if venue_lat is not None and venue_lng is not None:
            try:
                travel_service = TravelTimeService(
                    google_maps_api_key=getattr(settings, "GOOGLE_MAPS_API_KEY", None),
                    db_session=db,
                )
                travel_result = await travel_service.get_travel_time(
                    origin_lat=station_lat,
                    origin_lng=station_lng,
                    dest_lat=venue_lat,
                    dest_lng=venue_lng,
                    departure_time=datetime.now(),
                )
                travel_info.distance_miles = travel_result.distance_miles
                travel_info.duration_minutes = travel_result.travel_time_minutes
                travel_info.source = travel_result.source

                if travel_result.distance_miles > free_miles:
                    travel_info.travel_fee = (
                        travel_result.distance_miles - free_miles
                    ) * per_mile_rate

                logger.info(
                    f"📍 Travel calculated via {travel_result.source}: "
                    f"{travel_result.distance_miles:.1f} miles, {travel_result.travel_time_minutes} min"
                )
            except Exception as e:
                logger.warning(f"TravelTimeService failed, using ZIP fallback: {e}")
                # Fall through to ZIP estimation

        # FAIL-SAFE: If Google Maps didn't work, return error state instead of inaccurate estimates
        # Per user requirement: NO fallback estimates - only accurate Google Maps or human agent
        if travel_info.distance_miles is None:
            # Mark as calculation error - frontend will show "contact live agent" message
            travel_info.source = "error"
            travel_info.distance_miles = None
            travel_info.travel_fee = 0.0  # Will be ignored by frontend when source is 'error'
            logger.warning(
                f"⚠️ Travel fee calculation failed for address: {request.venue_address} "
                f"(ZIP: {request.zip_code}). Returning error state for human agent escalation."
            )

        # Calculate grand total
        grand_total = subtotal + travel_info.travel_fee

        # Calculate balance
        balance_due = grand_total - deposit_amount

        response = {
            "adults": request.adults,
            "children": request.children,
            "adult_price": adult_price,
            "child_price": child_price,
            "base_total": round(base_total, 2),
            "upgrade_total": round(upgrade_total, 2),
            "addon_total": round(addon_total, 2),
            "subtotal": round(subtotal, 2),
            "travel_info": {
                "distance_miles": travel_info.distance_miles,
                "duration_minutes": travel_info.duration_minutes,
                "travel_fee": round(travel_info.travel_fee, 2),
                "free_miles": travel_info.free_miles,
                "per_mile_rate": travel_info.per_mile_rate,
                "station_name": travel_info.station_name,
                "source": travel_info.source,
            },
            "grand_total": round(grand_total, 2),
            "deposit_required": deposit_amount,
            "balance_due": round(max(0, balance_due), 2),
            "party_minimum": party_minimum,
            "applied_minimum": applied_minimum,
        }

        logger.info(
            f"✅ Quote calculated: ${grand_total:.2f} for {request.adults} adults, {request.children} children"
        )

        return response

    except Exception as e:
        logger.exception(f"❌ Quote calculation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate quote. Please try again.",
        )


def _estimate_distance(zip_code: str | None, address: str | None) -> float | None:
    """
    Estimate distance from Fremont station based on ZIP code.

    In production, this would use Google Maps Distance Matrix API.
    This is a simplified estimation for Bay Area ZIP codes.

    Fremont Station: 47481 Towhee St, Fremont, CA 94539
    """
    if not zip_code and not address:
        return None

    # Extract ZIP from address if not provided
    if not zip_code and address:
        import re

        zip_match = re.search(r"\b(\d{5})\b", address)
        if zip_match:
            zip_code = zip_match.group(1)

    if not zip_code:
        return None

    # Estimated distances from Fremont (94539) based on ZIP code areas
    # These are rough estimates for the Bay Area
    bay_area_distances = {
        # Fremont/Newark/Union City (local)
        "94536": 3,
        "94538": 2,
        "94539": 0,
        "94555": 4,
        "94560": 5,
        "94587": 6,
        # San Jose area (15-25 miles)
        "95110": 15,
        "95111": 18,
        "95112": 16,
        "95113": 15,
        "95116": 17,
        "95117": 20,
        "95118": 22,
        "95119": 20,
        "95120": 25,
        "95121": 18,
        "95122": 17,
        "95123": 20,
        "95124": 23,
        "95125": 21,
        "95126": 19,
        "95127": 16,
        "95128": 21,
        "95129": 24,
        "95130": 23,
        "95131": 15,
        "95132": 14,
        "95133": 15,
        "95134": 13,
        "95135": 18,
        "95136": 20,
        # Milpitas/Santa Clara (10-15 miles)
        "95035": 8,
        "95050": 12,
        "95051": 13,
        "95054": 11,
        # Hayward/Castro Valley (5-10 miles)
        "94541": 7,
        "94542": 8,
        "94544": 6,
        "94545": 5,
        "94546": 10,
        # Oakland/Berkeley (20-30 miles)
        "94601": 25,
        "94602": 26,
        "94606": 24,
        "94607": 28,
        "94608": 30,
        "94609": 28,
        "94610": 27,
        "94611": 28,
        "94612": 26,
        "94618": 30,
        "94702": 32,
        "94703": 33,
        "94704": 32,
        "94705": 31,
        "94720": 33,
        # San Francisco (40-45 miles)
        "94102": 42,
        "94103": 43,
        "94104": 43,
        "94105": 44,
        "94107": 42,
        "94108": 43,
        "94109": 44,
        "94110": 41,
        "94111": 44,
        "94112": 38,
        "94114": 40,
        "94115": 44,
        "94116": 39,
        "94117": 43,
        "94118": 44,
        "94121": 46,
        "94122": 42,
        "94123": 45,
        "94124": 36,
        "94127": 40,
        "94131": 39,
        "94132": 38,
        "94133": 45,
        "94134": 35,
        # Palo Alto/Mountain View (20-25 miles)
        "94301": 22,
        "94303": 20,
        "94304": 21,
        "94306": 23,
        "94040": 18,
        "94041": 19,
        "94043": 17,
        # Sunnyvale/Cupertino (15-20 miles)
        "94085": 14,
        "94086": 15,
        "94087": 16,
        "94089": 13,
        "95014": 20,
        # Livermore/Pleasanton (15-20 miles)
        "94550": 18,
        "94551": 20,
        "94566": 15,
        "94568": 12,
        "94588": 14,
        # Walnut Creek/Concord (25-35 miles)
        "94520": 28,
        "94521": 30,
        "94523": 32,
        "94595": 25,
        "94596": 26,
        "94597": 27,
        "94598": 28,
        # Vacaville/Fairfield/Solano County (45-55 miles)
        "94533": 45,  # Fairfield
        "94534": 48,  # Fairfield
        "94535": 50,  # Travis AFB
        "95687": 50,  # Vacaville
        "95688": 50,  # Vacaville
        "95696": 52,  # Vacaville
        "94585": 42,  # Suisun City
        "94510": 35,  # Benicia
        "94590": 38,  # Vallejo
        "94591": 40,  # Vallejo
        "94592": 42,  # Mare Island
        # Napa area (50-60 miles)
        "94558": 55,  # Napa
        "94559": 55,  # Napa
        "94574": 60,  # St. Helena
        "94599": 55,  # Yountville
        # Sacramento area (80+ miles)
        "95814": 85,
        "95816": 85,
        "95818": 85,
        "95819": 86,
        "95820": 87,
        "95821": 88,
        "95822": 88,
        "95823": 90,
        "95824": 87,
        "95825": 89,
        "95826": 90,
        "95828": 92,
        "95829": 93,
        "95830": 95,
        "95831": 90,
        "95832": 88,
        "95833": 86,
        "95834": 85,
        "95835": 84,
        "95838": 82,
    }

    # Look up distance or default estimate
    distance = bay_area_distances.get(zip_code)

    if distance is not None:
        return float(distance)

    # Default estimation based on ZIP code prefix
    # More granular prefix matching for California regions
    if zip_code.startswith("945"):
        return 8.0  # Fremont/Hayward area (local)
    elif zip_code.startswith("944"):
        return 30.0  # San Leandro/Oakland area
    elif zip_code.startswith("946") or zip_code.startswith("947"):
        return 35.0  # Berkeley/Richmond area
    elif zip_code.startswith("9458") or zip_code.startswith("9459"):
        return 40.0  # Vallejo/Benicia area
    elif zip_code.startswith("951") or zip_code.startswith("950"):
        return 18.0  # San Jose/Milpitas area (South Bay)
    elif zip_code.startswith("956") or zip_code.startswith("957"):
        return 50.0  # Vacaville/Fairfield/Solano area
    elif zip_code.startswith("958"):
        return 85.0  # Sacramento area
    elif zip_code.startswith("940"):
        return 40.0  # San Francisco area
    elif zip_code.startswith("94"):
        return 25.0  # Other East Bay
    elif zip_code.startswith("95"):
        return 35.0  # Other 95xxx (could be North Bay or Central Valley)
    else:
        return 50.0  # Outside Bay Area


# ============================================================================
# EMAIL QUOTE ENDPOINT
# ============================================================================


class EmailQuoteRequest(BaseModel):
    """Schema for emailing a quote to customer."""

    customerEmail: str = Field(..., description="Customer email address")
    customerName: str = Field(..., description="Customer name")
    customerPhone: str = Field(default="", description="Customer phone number")

    # Event details
    adults: int = Field(..., ge=0, description="Number of adults")
    children: int = Field(default=0, ge=0, description="Number of children")
    venueAddress: str = Field(default="", description="Venue address")
    venueCity: str = Field(default="", description="Venue city")
    venueZipcode: str = Field(default="", description="Venue ZIP code")

    # Quote results
    baseTotal: float = Field(..., ge=0, description="Base price total")
    upgradeTotal: float = Field(default=0, ge=0, description="Upgrades total")
    travelFee: float = Field(default=0, ge=0, description="Travel fee")
    grandTotal: float = Field(..., ge=0, description="Grand total")
    depositRequired: float = Field(default=100, ge=0, description="Deposit required")

    # Upgrades selected (quantities)
    salmon: int = Field(default=0, ge=0)
    scallops: int = Field(default=0, ge=0)
    filetMignon: int = Field(default=0, ge=0)
    lobsterTail: int = Field(default=0, ge=0)
    extraProteins: int = Field(default=0, ge=0)
    yakisobaNoodles: int = Field(default=0, ge=0)
    extraFriedRice: int = Field(default=0, ge=0)
    extraVegetables: int = Field(default=0, ge=0)
    edamame: int = Field(default=0, ge=0)
    gyoza: int = Field(default=0, ge=0)


class EmailQuoteResponse(BaseModel):
    """Response for email quote endpoint."""

    success: bool = Field(..., description="Whether email was sent successfully")
    message: str = Field(..., description="Success or error message")


@router.post(
    "/email",
    response_model=EmailQuoteResponse,
    summary="Email Quote to Customer",
    description="Send the calculated quote to customer's email in plain text format.",
)
async def email_quote(
    request: EmailQuoteRequest,
) -> EmailQuoteResponse:
    """
    Send the quote summary via email to the customer.

    This endpoint:
    1. Validates the email address
    2. Formats the quote as a plain text email
    3. Sends via SMTP (cs@myhibachichef.com)
    """
    from services.email_service import email_service

    # Basic email validation
    if not request.customerEmail or "@" not in request.customerEmail:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid email address is required",
        )

    # Build upgrades dict
    upgrades = {
        "salmon": request.salmon,
        "scallops": request.scallops,
        "filetMignon": request.filetMignon,
        "lobsterTail": request.lobsterTail,
        "extraProteins": request.extraProteins,
        "yakisobaNoodles": request.yakisobaNoodles,
        "extraFriedRice": request.extraFriedRice,
        "extraVegetables": request.extraVegetables,
        "edamame": request.edamame,
        "gyoza": request.gyoza,
    }

    # Send the email
    success = email_service.send_quote_email(
        customer_email=request.customerEmail,
        customer_name=request.customerName,
        customer_phone=request.customerPhone,
        adults=request.adults,
        children=request.children,
        venue_address=request.venueAddress,
        venue_city=request.venueCity,
        venue_zipcode=request.venueZipcode,
        base_total=request.baseTotal,
        upgrade_total=request.upgradeTotal,
        travel_fee=request.travelFee,
        grand_total=request.grandTotal,
        deposit_required=request.depositRequired,
        upgrades=upgrades,
    )

    if success:
        logger.info(f"Quote email sent to {request.customerEmail}")
        return EmailQuoteResponse(
            success=True,
            message=f"Quote sent to {request.customerEmail}",
        )
    else:
        logger.error(f"Failed to send quote email to {request.customerEmail}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send email. Please try again later.",
        )
