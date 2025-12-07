"""
Pricing API Endpoints
Provides pricing data using BusinessConfig for dynamic values (Single Source of Truth)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
import logging

from core.database import get_db
from services.business_config_service import get_business_config

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/pricing/current", response_model=dict[str, Any])
async def get_current_pricing(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get current menu pricing and addon items

    Uses BusinessConfig for dynamic pricing values (Single Source of Truth).
    Menu items and addons are hardcoded as they rarely change.
    """
    try:
        # Get dynamic pricing from BusinessConfig (Single Source of Truth)
        config = await get_business_config(db)

        adult_price = config.adult_price_cents / 100
        child_price = config.child_price_cents / 100
        party_minimum = config.party_minimum_cents / 100
        child_free_under_age = config.child_free_under_age
        free_miles = config.travel_free_miles
        price_per_mile = config.travel_per_mile_cents / 100

        logger.info(
            f"📊 Pricing loaded from {config.source}: adult=${adult_price}, child=${child_price}"
        )

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
            # PREMIUM PROTEIN UPGRADES (+$7 per person - replace any base protein)
            {
                "id": 1,
                "name": "Salmon",
                "category": "protein_upgrade",
                "price": 7.00,
                "description": "Wild-caught Atlantic salmon with teriyaki glaze",
                "is_active": True,
                "display_order": 1,
            },
            {
                "id": 2,
                "name": "Scallops",
                "category": "protein_upgrade",
                "price": 9.00,
                "description": "Fresh sea scallops grilled to perfection",
                "is_active": True,
                "display_order": 2,
            },
            {
                "id": 3,
                "name": "Filet Mignon",
                "category": "protein_upgrade",
                "price": 10.00,
                "description": "Premium tender beef filet",
                "is_active": True,
                "display_order": 3,
            },
            # PREMIUM PROTEIN UPGRADES (+$20 per person)
            {
                "id": 4,
                "name": "Lobster Tail",
                "category": "protein_upgrade",
                "price": 20.00,
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

        # Travel fee configuration from BusinessConfig
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
                "free_miles": float(free_miles),  # From BusinessConfig
                "price_per_mile": price_per_mile,  # From BusinessConfig
                "max_service_distance": None,  # Unlimited
                "is_active": True,
                "notes": "Main station covering Bay Area and Sacramento regions",
                "display_order": 1,
            }
        ]

        response = {
            "base_pricing": {
                "adult_price": adult_price,  # From BusinessConfig
                "child_price": child_price,  # From BusinessConfig
                "child_free_under_age": child_free_under_age,  # From BusinessConfig
                "party_minimum": party_minimum,  # From BusinessConfig
                "deposit_amount": config.deposit_amount_cents / 100,  # From BusinessConfig
            },
            "travel_fee_config": {
                "free_miles": free_miles,
                "price_per_mile": price_per_mile,
            },
            "travel_fee_stations": travel_fee_stations_data,
            "menu_items": menu_items_data,
            "addon_items": addon_items_data,
            "config_source": config.source,  # Debug: shows where config came from
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
    Uses BusinessConfig for dynamic pricing values.

    NOTE: For public quote calculation without auth, use /api/v1/public/quote/calculate
    """
    try:
        # Get dynamic pricing from BusinessConfig
        config = await get_business_config(db)

        adult_price = config.adult_price_cents / 100
        child_price = config.child_price_cents / 100
        party_minimum = config.party_minimum_cents / 100
        deposit_amount = config.deposit_amount_cents / 100

        # Calculate base total
        base_total = (adults * adult_price) + (children * child_price)

        # Apply party minimum
        applied_minimum = False
        if base_total < party_minimum:
            base_total = party_minimum
            applied_minimum = True

        return {
            "adults": adults,
            "children": children,
            "children_under_5": children_under_5,
            "adult_price": adult_price,
            "child_price": child_price,
            "subtotal": round(base_total, 2),
            "travel_fee": 0.00,  # TODO: Calculate based on address
            "total": round(base_total, 2),
            "deposit_required": deposit_amount,
            "balance_due": round(max(0, base_total - deposit_amount), 2),
            "party_minimum": party_minimum,
            "applied_minimum": applied_minimum,
            "breakdown": {
                "adult_meals": round(adults * adult_price, 2),
                "child_meals": round(children * child_price, 2),
            },
        }

    except Exception as e:
        logger.exception(f"Error calculating quote: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate quote: {str(e)}")


@router.get("/pricing/summary", response_model=dict[str, Any])
async def get_pricing_summary(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get comprehensive pricing summary for display
    Delegates to /pricing/current
    """
    try:
        return await get_current_pricing(db=db)

    except Exception as e:
        logger.exception(f"Error fetching pricing summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pricing summary: {str(e)}")
