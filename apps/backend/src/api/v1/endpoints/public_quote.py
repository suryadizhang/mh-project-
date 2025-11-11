"""
Public Quote Calculation Endpoint
No authentication required - allows customers to get instant quotes
Includes travel fee calculation using Google Maps API
"""

import logging
from decimal import Decimal

from api.ai.endpoints.services.pricing_service import get_pricing_service
from api.app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class PublicQuoteRequest(BaseModel):
    """Public quote calculation request"""

    adults: int = Field(..., ge=1, le=100, description="Number of adults (13+)")
    children: int = Field(default=0, ge=0, le=100, description="Number of children (6-12)")
    
    # Protein upgrades
    salmon: int = Field(default=0, ge=0, description="Salmon portions (+$5 each)")
    scallops: int = Field(default=0, ge=0, description="Scallop portions (+$5 each)")
    filet_mignon: int = Field(default=0, ge=0, description="Filet Mignon portions (+$5 each)")
    lobster_tail: int = Field(default=0, ge=0, description="Lobster Tail portions (+$15 each)")
    
    # 3rd protein rule
    third_proteins: int = Field(default=0, ge=0, description="Additional proteins beyond 2 per guest (+$10 each)")
    
    # Add-ons
    yakisoba_noodles: int = Field(default=0, ge=0, description="Yakisoba noodles add-on (+$6 each)")
    extra_fried_rice: int = Field(default=0, ge=0, description="Extra fried rice (+$6 each)")
    extra_vegetables: int = Field(default=0, ge=0, description="Extra vegetables (+$5 each)")
    edamame: int = Field(default=0, ge=0, description="Edamame (+$4 each)")
    gyoza: int = Field(default=0, ge=0, description="Gyoza (+$10 each)")
    
    # Travel fee calculation
    venue_address: str | None = Field(None, max_length=500, description="Full venue address for accurate travel fee")
    zip_code: str | None = Field(None, max_length=10, description="ZIP code for travel fee estimation")


class TravelFeeInfo(BaseModel):
    """Travel fee calculation details"""

    distance_miles: float | None = None
    travel_fee: float = 0.0
    is_free: bool = True
    free_radius_miles: int = 30
    per_mile_rate: float = 2.00
    message: str = "Travel fee will be calculated"


class PublicQuoteResponse(BaseModel):
    """Public quote calculation response"""

    success: bool = True
    
    # Base pricing
    base_total: float = Field(..., description="Base cost (adults + children)")
    upgrade_total: float = Field(..., description="All upgrades and add-ons")
    subtotal: float = Field(..., description="Base + Upgrades")
    
    # Travel fee
    travel_info: TravelFeeInfo
    
    # Final total
    grand_total: float = Field(..., description="Subtotal + Travel Fee (minimum $550)")
    
    # Breakdown for display
    breakdown: dict = Field(..., description="Detailed cost breakdown")
    
    # Gratuity suggestions
    gratuity_suggestions: dict | None = None


def calculate_gratuity_suggestions(grand_total: float) -> dict:
    """Calculate gratuity suggestions at 20%, 25%, and 30-35%"""
    return {
        "standard": {
            "percentage": 20,
            "amount": round(grand_total * 0.20, 2)
        },
        "excellent": {
            "percentage": 25,
            "amount": round(grand_total * 0.25, 2)
        },
        "exceptional": {
            "percentage_range": "30-35",
            "amount_min": round(grand_total * 0.30, 2),
            "amount_max": round(grand_total * 0.35, 2)
        }
    }


@router.post("/calculate", response_model=PublicQuoteResponse)
@limiter.limit("30/minute")
async def calculate_public_quote(
    quote: PublicQuoteRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate instant quote with travel fees
    
    Rate limit: 30 requests/minute per IP
    No authentication required
    
    **Features:**
    - Base pricing: $55/adult, $30/child
    - Protein upgrades: Salmon/Scallops/Filet (+$5), Lobster (+$15)
    - 3rd protein rule: +$10 per extra protein beyond 2 per guest
    - Add-ons: Noodles, rice, vegetables, appetizers
    - Travel fee: FREE within 30 miles, $2/mile after
    - Party minimum: $550
    - Google Maps integration for accurate travel distance
    
    **Example Request:**
    ```json
    {
      "adults": 10,
      "children": 2,
      "filet_mignon": 5,
      "lobster_tail": 5,
      "yakisoba_noodles": 2,
      "venue_address": "123 Main St, Sacramento, CA 95814"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "success": true,
      "base_total": 610.00,
      "upgrade_total": 112.00,
      "subtotal": 722.00,
      "travel_info": {
        "distance_miles": 15.2,
        "travel_fee": 0.00,
        "is_free": true,
        "message": "FREE delivery within 30 miles!"
      },
      "grand_total": 722.00,
      "breakdown": {...}
    }
    ```
    """
    try:
        # Initialize pricing service
        pricing_service = get_pricing_service()
        
        # Calculate base pricing
        adult_cost = quote.adults * 55.00
        child_cost = quote.children * 30.00
        base_total = adult_cost + child_cost
        
        # Calculate protein upgrades
        protein_upgrades = (
            (quote.salmon * 5.00) +
            (quote.scallops * 5.00) +
            (quote.filet_mignon * 5.00) +
            (quote.lobster_tail * 15.00) +
            (quote.third_proteins * 10.00)
        )
        
        # Calculate add-ons
        addons = (
            (quote.yakisoba_noodles * 6.00) +
            (quote.extra_fried_rice * 6.00) +
            (quote.extra_vegetables * 5.00) +
            (quote.edamame * 4.00) +
            (quote.gyoza * 10.00)
        )
        
        upgrade_total = protein_upgrades + addons
        subtotal = base_total + upgrade_total
        
        # Calculate travel fee if address provided
        travel_info = TravelFeeInfo()
        
        if quote.venue_address or quote.zip_code:
            try:
                travel_result = pricing_service.calculate_travel_distance(
                    quote.venue_address or "",
                    quote.zip_code
                )
                
                if travel_result.get("status") != "api_error" and travel_result.get("distance_miles"):
                    distance_miles = travel_result.get("distance_miles", 0)
                    travel_fee = travel_result.get("travel_fee", 0)
                    
                    travel_info = TravelFeeInfo(
                        distance_miles=round(distance_miles, 1),
                        travel_fee=float(travel_fee),
                        is_free=(travel_fee == 0),
                        free_radius_miles=30,
                        per_mile_rate=2.00,
                        message=(
                            f"FREE delivery! You're {distance_miles:.1f} miles away."
                            if travel_fee == 0
                            else f"${travel_fee:.2f} travel fee for {distance_miles:.1f} miles"
                        )
                    )
                else:
                    # API error or no distance - provide fallback message
                    travel_info = TravelFeeInfo(
                        message="Travel fee calculated at booking (FREE within 30 miles)"
                    )
            except Exception as e:
                logger.warning(f"Travel fee calculation failed: {e}")
                travel_info = TravelFeeInfo(
                    message="Travel fee calculated at booking (FREE within 30 miles)"
                )
        
        # Calculate grand total with minimum $550
        grand_total_before_minimum = subtotal + travel_info.travel_fee
        grand_total = max(grand_total_before_minimum, 550.00)
        
        # Build detailed breakdown
        breakdown = {
            "adults": {
                "count": quote.adults,
                "price_each": 55.00,
                "total": adult_cost
            },
            "children": {
                "count": quote.children,
                "price_each": 30.00,
                "total": child_cost
            },
            "protein_upgrades": {
                "salmon": {"count": quote.salmon, "price_each": 5.00, "total": quote.salmon * 5.00},
                "scallops": {"count": quote.scallops, "price_each": 5.00, "total": quote.scallops * 5.00},
                "filet_mignon": {"count": quote.filet_mignon, "price_each": 5.00, "total": quote.filet_mignon * 5.00},
                "lobster_tail": {"count": quote.lobster_tail, "price_each": 15.00, "total": quote.lobster_tail * 15.00},
                "third_proteins": {"count": quote.third_proteins, "price_each": 10.00, "total": quote.third_proteins * 10.00},
                "total": protein_upgrades
            },
            "addons": {
                "yakisoba_noodles": {"count": quote.yakisoba_noodles, "price_each": 6.00, "total": quote.yakisoba_noodles * 6.00},
                "extra_fried_rice": {"count": quote.extra_fried_rice, "price_each": 6.00, "total": quote.extra_fried_rice * 6.00},
                "extra_vegetables": {"count": quote.extra_vegetables, "price_each": 5.00, "total": quote.extra_vegetables * 5.00},
                "edamame": {"count": quote.edamame, "price_each": 4.00, "total": quote.edamame * 4.00},
                "gyoza": {"count": quote.gyoza, "price_each": 10.00, "total": quote.gyoza * 10.00},
                "total": addons
            },
            "subtotal": subtotal,
            "minimum_applied": (grand_total == 550.00 and subtotal < 550.00)
        }
        
        # Calculate gratuity suggestions
        gratuity_suggestions = calculate_gratuity_suggestions(grand_total)
        
        logger.info(
            "Public quote calculated",
            extra={
                "adults": quote.adults,
                "children": quote.children,
                "base_total": base_total,
                "upgrade_total": upgrade_total,
                "travel_fee": travel_info.travel_fee,
                "grand_total": grand_total
            }
        )
        
        return PublicQuoteResponse(
            success=True,
            base_total=round(base_total, 2),
            upgrade_total=round(upgrade_total, 2),
            subtotal=round(subtotal, 2),
            travel_info=travel_info,
            grand_total=round(grand_total, 2),
            breakdown=breakdown,
            gratuity_suggestions=gratuity_suggestions
        )
        
    except Exception as e:
        logger.error(f"Quote calculation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate quote. Please try again."
        )
