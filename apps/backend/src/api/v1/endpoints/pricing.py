"""
Pricing API Endpoints
Provides pricing data (temporarily hardcoded pending mapper conflict resolution)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
import logging

from core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/pricing/current", response_model=dict[str, Any])
async def get_current_pricing(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get current menu pricing and addon items

    NOTE: Temporarily hardcoded pending database mapper conflict resolution
    """
    try:
        # Hardcoded menu items (REAL data from customer menu page)
        menu_items_data = [
            # FREE PROTEINS (Poultry - included in base price, choose any 2)
            {
                "id": 1,
                "name": "Chicken",
                "category": "poultry",
                "price": 0.00,
                "description": "Tender grilled chicken with teriyaki glaze",
                "is_active": True,
                "is_included": True,
                "display_order": 1,
            },
            # FREE PROTEINS (Beef - included in base price, choose any 2)
            {
                "id": 2,
                "name": "NY Strip Steak",
                "category": "beef",
                "price": 0.00,
                "description": "Premium NY strip steak cooked to your preference",
                "is_active": True,
                "is_included": True,
                "display_order": 2,
            },
            # FREE PROTEINS (Seafood - included in base price, choose any 2)
            {
                "id": 3,
                "name": "Shrimp",
                "category": "seafood",
                "price": 0.00,
                "description": "Fresh jumbo shrimp with garlic butter",
                "is_active": True,
                "is_included": True,
                "display_order": 3,
            },
            {
                "id": 4,
                "name": "Calamari",
                "category": "seafood",
                "price": 0.00,
                "description": "Fresh tender calamari grilled with garlic",
                "is_active": True,
                "is_included": True,
                "display_order": 4,
            },
            # SPECIALTY (included in base price, choose any 2)
            {
                "id": 5,
                "name": "Tofu",
                "category": "specialty",
                "price": 0.00,
                "description": "Fried tofu with house special seasoning",
                "is_active": True,
                "is_included": True,
                "display_order": 5,
            },
            # SIDES (included in base price)
            {
                "id": 6,
                "name": "Fried Rice",
                "category": "side",
                "price": 0.00,
                "description": "Hibachi fried rice with eggs and vegetables",
                "is_active": True,
                "is_included": True,
                "display_order": 1,
            },
            {
                "id": 7,
                "name": "Mixed Vegetables",
                "category": "side",
                "price": 0.00,
                "description": "Zucchini, carrots, onions, mushrooms, broccoli",
                "is_active": True,
                "is_included": True,
                "display_order": 2,
            },
            {
                "id": 8,
                "name": "Salad",
                "category": "side",
                "price": 0.00,
                "description": "Fresh greens with ginger dressing",
                "is_active": True,
                "is_included": True,
                "display_order": 3,
            },
            # SAUCES (included - complimentary)
            {
                "id": 9,
                "name": "Yum Yum Sauce",
                "category": "sauce",
                "price": 0.00,
                "description": "Famous creamy signature sauce",
                "is_active": True,
                "is_included": True,
                "display_order": 1,
            },
            {
                "id": 10,
                "name": "Special Hot Sauce",
                "category": "sauce",
                "price": 0.00,
                "description": "House special hot sauce with perfect heat",
                "is_active": True,
                "is_included": True,
                "display_order": 2,
            },
        ]

        # Hardcoded addon items (REAL data from customer menu page - Additional Enhancements section)
        addon_items_data = [
            # PREMIUM PROTEIN UPGRADES (+$5 per person - replace any base protein)
            {
                "id": 1,
                "name": "Salmon",
                "category": "protein_upgrade",
                "price": 5.00,
                "description": "Wild-caught Atlantic salmon with teriyaki glaze",
                "is_active": True,
                "display_order": 1,
            },
            {
                "id": 2,
                "name": "Scallops",
                "category": "protein_upgrade",
                "price": 5.00,
                "description": "Fresh sea scallops grilled to perfection",
                "is_active": True,
                "display_order": 2,
            },
            {
                "id": 3,
                "name": "Filet Mignon",
                "category": "protein_upgrade",
                "price": 5.00,
                "description": "Premium tender beef filet",
                "is_active": True,
                "display_order": 3,
            },
            # PREMIUM PROTEIN UPGRADES (+$15 per person)
            {
                "id": 4,
                "name": "Lobster Tail",
                "category": "protein_upgrade",
                "price": 15.00,
                "description": "Fresh lobster tail with garlic butter",
                "is_active": True,
                "display_order": 4,
            },
            # ADDITIONAL ENHANCEMENTS (from menu page)
            {
                "id": 5,
                "name": "Yakisoba Noodles",
                "category": "enhancement",
                "price": 5.00,
                "description": "Japanese style lo mein noodles",
                "is_active": True,
                "display_order": 1,
            },
            {
                "id": 6,
                "name": "Extra Fried Rice",
                "category": "enhancement",
                "price": 5.00,
                "description": "Additional portion of hibachi fried rice",
                "is_active": True,
                "display_order": 2,
            },
            {
                "id": 7,
                "name": "Extra Vegetables",
                "category": "enhancement",
                "price": 5.00,
                "description": "Additional portion of mixed seasonal vegetables",
                "is_active": True,
                "display_order": 3,
            },
            {
                "id": 8,
                "name": "Edamame",
                "category": "enhancement",
                "price": 5.00,
                "description": "Fresh steamed soybeans with sea salt",
                "is_active": True,
                "display_order": 4,
            },
            {
                "id": 9,
                "name": "Gyoza",
                "category": "enhancement",
                "price": 10.00,
                "description": "Pan-fried Japanese dumplings",
                "is_active": True,
                "display_order": 5,
            },
            {
                "id": 10,
                "name": "3rd Protein",
                "category": "enhancement",
                "price": 10.00,
                "description": "Add a third protein to your meal",
                "is_active": True,
                "display_order": 6,
            },
        ]

        # Hardcoded travel fee configurations (REAL data - station-based)
        # NOTE: Will be replaced with database query once mapper conflict resolved
        travel_fee_stations_data = [
            {
                "id": 1,
                "station_name": "Fremont Station (Main)",
                "station_address": "47481 Towhee St, Fremont, CA 94539",
                "city": "Fremont",
                "state": "CA",
                "postal_code": "94539",
                "latitude": None,  # Will be geocoded in production
                "longitude": None,
                "free_miles": 30.00,
                "price_per_mile": 2.00,
                "max_service_distance": None,  # Unlimited
                "is_active": True,
                "notes": "Main station covering Bay Area and Sacramento regions",
                "display_order": 1,
            }
        ]

        response = {
            "base_pricing": {
                "adult_price": 55.00,
                "child_price": 30.00,
                "child_free_under_age": 5,
                "party_minimum": 550.00,  # Updated to match menu page ($550 ≈ 10 adults)
            },
            "travel_fee_stations": travel_fee_stations_data,
            "menu_items": menu_items_data,
            "addon_items": addon_items_data,
        }

        return response

    except Exception as e:
        logger.exception(f"Error fetching pricing data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pricing data: {str(e)}")


@router.post("/pricing/calculate", response_model=dict[str, Any])
async def calculate_quote(
    adults: int,
    children: int = 0,
    children_under_5: int = 0,
    upgrades: dict[str, int] | None = None,
    addons: list[str] | None = None,
    customer_address: str | None = None,
    customer_zipcode: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Calculate party quote with breakdown
    NOTE: Temporarily simplified - full calculation coming soon
    """
    try:
        # Simple calculation without PricingService
        base_total = (adults * 55.00) + (children * 30.00)
        return {
            "adults": adults,
            "children": children,
            "children_under_5": children_under_5,
            "subtotal": base_total,
            "travel_fee": 0.00,
            "total": base_total,
            "breakdown": {
                "adult_meals": adults * 55.00,
                "child_meals": children * 30.00,
            },
        }

        quote = pricing_service.calculate_party_quote(
            adults=adults,
            children=children,
            children_under_5=children_under_5,
            upgrades=upgrades or {},
            addons=addons or [],
            customer_address=customer_address,
            customer_zipcode=customer_zipcode,
        )

        return quote

    except Exception as e:
        logger.exception(f"Error calculating quote: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate quote: {str(e)}")


@router.get("/pricing/summary", response_model=dict[str, Any])
async def get_pricing_summary(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get comprehensive pricing summary for display
    NOTE: Temporarily simplified - delegates to /pricing/current
    """
    try:
        # Redirect to current pricing endpoint
        return await get_current_pricing(db=db)

    except Exception as e:
        logger.exception(f"Error fetching pricing summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pricing summary: {str(e)}")
