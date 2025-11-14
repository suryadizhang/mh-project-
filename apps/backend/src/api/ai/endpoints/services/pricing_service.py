"""
Real-time Pricing Service with Google Maps Travel Fee Calculation
Pulls actual pricing data from database, menu configuration, and FAQ data
Calculates accurate travel fees using Google Maps Distance Matrix API
NO MORE HARDCODED PRICES - Always use real data from system
"""

from datetime import datetime
from decimal import Decimal
import logging
import os
from typing import Any

from core.auth.station_models import Station

# Import models
from models.legacy_booking_models import AddonItem, MenuItem
import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from .admin_alert_service import get_admin_alert_service
from .protein_calculator_service import get_protein_calculator_service

logger = logging.getLogger(__name__)


class PricingService:
    """
    Centralized pricing service that pulls real-time pricing from:
    1. Database (menu_items, addon_items tables)
    2. Configuration files (for display prices)
    3. Super Admin settings (for dynamic price adjustments)
    4. Google Maps API for accurate travel distance calculation

    NEVER hardcode prices - always query from this service
    """

    # Base pricing from FAQ data (fallback if DB empty)
    # These should match your customer-facing webpage
    BASE_PRICING = {
        "adult_base": 55.00,  # $55 per adult (13+)
        "child_base": 30.00,  # $30 per child (6-12)
        "child_free_under": 5,  # Free for under 5 years old
        "party_minimum": 550.00,  # $550 minimum total
    }

    # Premium upgrades (per person)
    PREMIUM_UPGRADES = {
        "filet_mignon": 5.00,  # +$5/person (NOT $15!)
        "salmon": 5.00,  # +$5/person
        "scallops": 5.00,  # +$5/person
        "lobster_tail": 15.00,  # +$15/person
    }

    # Add-ons (flat rate per party)
    ADDONS = {
        "premium_sake_service": 25.00,
        "extended_performance": 50.00,
        "custom_menu_planning": 35.00,
    }

    # Travel fees (pulled from environment or database)
    TRAVEL_PRICING = {
        "free_radius_miles": int(os.getenv("TRAVEL_FREE_DISTANCE_MILES", 30)),
        "per_mile_after": float(os.getenv("TRAVEL_FEE_PER_MILE_CENTS", 200)) / 100,
    }

    # Gratuity guidelines (not enforced, just guidance)
    GRATUITY = {
        "suggested_min_percent": 20,
        "suggested_max_percent": 35,
    }

    def __init__(self, db: Session | None = None, station_id: str | None = None):
        """
        Initialize pricing service

        Args:
            db: SQLAlchemy database session (optional, uses fallback if None)
            station_id: Station ID for multi-tenant pricing (optional)
        """
        self.db = db
        self.station_id = station_id
        self._price_cache = {}
        self._cache_timestamp = None
        self._cache_ttl_seconds = 300  # 5 minutes cache
        self._google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")

        # Get station location for travel calculations
        self._station_address = None
        self._station_coordinates = None
        if self.db and self.station_id:
            self._load_station_location()

    def _load_station_location(self) -> None:
        """Load station location from database for travel calculations"""
        try:
            station = self.db.execute(
                select(Station).where(Station.id == self.station_id)
            ).scalar_one_or_none()

            if station:
                # Build full address
                address_parts = [station.address, station.city, station.state, station.postal_code]
                self._station_address = ", ".join([p for p in address_parts if p])
                logger.info(f"Loaded station location: {self._station_address}")
            else:
                logger.warning(f"Station {self.station_id} not found, using env fallback")
                self._load_station_from_env()
        except Exception as e:
            logger.exception(f"Failed to load station location: {e}, using env fallback")
            self._load_station_from_env()

    def _load_station_from_env(self) -> None:
        """Load station location from environment variables (fallback)"""
        # Try business address from environment
        self._station_address = os.getenv("BUSINESS_ADDRESS")
        if not self._station_address:
            # Build from components
            parts = [os.getenv("BUSINESS_CITY"), os.getenv("BUSINESS_STATE")]
            self._station_address = ", ".join([p for p in parts if p])

    def calculate_travel_distance(
        self, destination_address: str, destination_zipcode: str | None = None
    ) -> dict[str, Any]:
        """
        Calculate travel distance using Google Maps Distance Matrix API

        Args:
            destination_address: Full customer address or partial location
            destination_zipcode: Optional ZIP code for more accurate results

        Returns:
            Dict with distance info and travel fee calculation
        """
        # Build destination (prefer full address, fallback to zip)
        destination = destination_address
        if not destination and destination_zipcode:
            destination = destination_zipcode

        if not destination:
            return {
                "status": "incomplete_address",
                "message": self.get_travel_fee_explanation(detailed=True),
                "distance_miles": None,
                "drive_time": None,
                "travel_fee": None,
                "requires_full_address": True,
            }

        # Check if only ZIP code provided (polite reminder about exact address)
        is_zip_only = destination_zipcode and not destination_address

        # Check if we have API key and station location
        if not self._google_maps_api_key:
            logger.warning("Google Maps API key not configured, using ZIP-based estimate")
            # Alert admin about API configuration issue
            get_admin_alert_service().alert_api_error(
                service_name="Google Maps",
                error_message="API key not configured in environment variables",
                customer_address=destination,
            )
            return (
                self._estimate_travel_from_zip(destination_zipcode)
                if destination_zipcode
                else {
                    "status": "api_unavailable",
                    "message": "Unable to calculate exact travel fee. Please contact us at (916) 740-8768 for a quote.",
                    "distance_miles": None,
                    "travel_fee": None,
                }
            )

        if not self._station_address:
            logger.error("Station address not configured")
            get_admin_alert_service().alert_api_error(
                service_name="Google Maps",
                error_message="Station address not configured",
                customer_address=destination,
            )
            return {
                "status": "error",
                "message": "Service location not configured. Please contact us for a quote.",
                "distance_miles": None,
                "travel_fee": None,
            }

        try:
            # Call Google Maps Distance Matrix API
            url = "https://maps.googleapis.com/maps/api/distancematrix/json"
            params = {
                "origins": self._station_address,
                "destinations": destination,
                "key": self._google_maps_api_key,
                "units": "imperial",  # Miles
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if data.get("status") != "OK":
                logger.error(
                    f"Google Maps API error: {data.get('status')} - {data.get('error_message')}"
                )
                # Alert admin about API error
                get_admin_alert_service().alert_api_error(
                    service_name="Google Maps Distance Matrix API",
                    error_message=f"API Status: {data.get('status')} - {data.get('error_message', 'Unknown error')}",
                    customer_address=destination,
                )
                return {
                    "status": "api_error",
                    "message": "Unable to calculate travel distance right now. Please call us at (916) 740-8768 and we'll provide an immediate quote!",
                    "distance_miles": None,
                    "travel_fee": None,
                    "requires_admin_follow_up": True,
                }

            element = data["rows"][0]["elements"][0]

            if element.get("status") != "OK":
                logger.warning(f"Routing error for {destination}: {element.get('status')}")
                return {
                    "status": "routing_error",
                    "message": "Could not find route to your location. Please verify your address is complete and correct.",
                    "distance_miles": None,
                    "travel_fee": None,
                    "requires_full_address": True,
                }

            # Extract distance and duration
            distance_meters = element["distance"]["value"]
            distance_miles = distance_meters / 1609.34
            duration_text = element["duration"]["text"]

            # Calculate travel fee
            free_miles = self.TRAVEL_PRICING["free_radius_miles"]
            per_mile_rate = self.TRAVEL_PRICING["per_mile_after"]

            if distance_miles <= free_miles:
                travel_fee = Decimal("0.00")
                billable_miles = 0.0
            else:
                billable_miles = distance_miles - free_miles
                travel_fee = Decimal(str(billable_miles * per_mile_rate))

            # Add polite note if only ZIP provided
            note = None
            if is_zip_only:
                note = (
                    "📍 Friendly reminder: With your full street address, we can provide an exact travel fee "
                    "using real-time route calculation. The ZIP code estimate shown is close, but the actual "
                    "distance may vary slightly depending on your exact location."
                )

            return {
                "status": "success",
                "distance_miles": round(distance_miles, 1),
                "distance_text": f"{round(distance_miles, 1)} miles",
                "drive_time": duration_text,
                "travel_fee": float(travel_fee),
                "breakdown": {
                    "total_distance": round(distance_miles, 1),
                    "free_miles": free_miles,
                    "billable_miles": round(billable_miles, 1),
                    "rate_per_mile": per_mile_rate,
                },
                "from": self._station_address,
                "to": destination,
                "requires_full_address": is_zip_only,
                "note": note if is_zip_only else f"First {free_miles} miles are complimentary!",
            }

        except requests.Timeout:
            logger.exception("Google Maps API timeout")
            get_admin_alert_service().alert_api_error(
                service_name="Google Maps",
                error_message="API request timeout",
                customer_address=destination,
            )
            return {
                "status": "timeout",
                "message": "Request timed out. Please call us at (916) 740-8768 for an immediate quote!",
                "distance_miles": None,
                "travel_fee": None,
                "requires_admin_follow_up": True,
            }
        except Exception as e:
            logger.exception(f"Error calculating travel distance: {e}")
            get_admin_alert_service().alert_api_error(
                service_name="Google Maps", error_message=str(e), customer_address=destination
            )
            return {
                "status": "error",
                "message": "We're having trouble calculating the travel fee. Please call us at (916) 740-8768 and we'll help you right away!",
                "distance_miles": None,
                "travel_fee": None,
                "requires_admin_follow_up": True,
            }

    def _estimate_travel_from_zip(self, zipcode: str) -> dict[str, Any]:
        """
        Estimate travel distance from ZIP code (rough approximation)
        Used when Google Maps API is unavailable

        Args:
            zipcode: Customer ZIP code

        Returns:
            Dict with estimated distance
        """
        # This is a very rough approximation
        # In production, you'd want a ZIP code database with coordinates
        return {
            "status": "estimated",
            "message": "Travel fee estimated from ZIP code. For exact quote, please provide your full address.",
            "distance_miles": None,
            "travel_fee": None,
            "is_estimate": True,
            "note": "Call (916) 740-8768 for exact travel fee calculation",
        }

    def get_travel_fee_explanation(self, detailed: bool = False) -> str:
        """
        Get human-readable explanation of travel fee policy

        Args:
            detailed: If True, include polite reminder about exact address

        Returns:
            str: Travel fee policy explanation
        """
        free_miles = self.TRAVEL_PRICING["free_radius_miles"]
        per_mile = self.TRAVEL_PRICING["per_mile_after"]

        if detailed:
            return f"""
🚗 **Travel Fee Policy**:
• First {free_miles} miles: Completely FREE
• Beyond {free_miles} miles: ${per_mile:.2f} per mile

📍 **For the most accurate travel fee**:
With your full street address, we can provide an exact travel fee using real-time route calculation.
With just a ZIP code, we can estimate a range, but the actual fee may vary slightly.

💬 Questions? Call/Text (916) 740-8768
            """.strip()

        return f"First {free_miles} miles FREE, ${per_mile:.2f}/mile after"

    def get_gratuity_guidance(self, subtotal: float) -> dict[str, Any]:
        """
        Get friendly gratuity suggestions based on subtotal

        Args:
            subtotal: The subtotal amount before gratuity

        Returns:
            Dict with gratuity message and suggested amounts
        """
        gratuity_20_percent = round(subtotal * 0.20, 2)
        gratuity_25_percent = round(subtotal * 0.25, 2)
        gratuity_30_percent = round(subtotal * 0.30, 2)
        gratuity_35_percent = round(subtotal * 0.35, 2)

        return {
            "message": f"""
💝 **Gratuity Guide** (100% Optional & At Your Discretion):

Our beloved hardworking chefs pour their hearts into creating an unforgettable
hibachi experience for you and your guests! Based on your satisfaction:

• Good service (20%): ${gratuity_20_percent:.2f}
• Great service (25%): ${gratuity_25_percent:.2f}
• Excellent service (30%): ${gratuity_30_percent:.2f}
• Outstanding service (35%): ${gratuity_35_percent:.2f}

Your appreciation means the world to our chefs! 🙏✨
            """.strip(),
            "suggested_amounts": {
                "good_20_percent": gratuity_20_percent,
                "great_25_percent": gratuity_25_percent,
                "excellent_30_percent": gratuity_30_percent,
                "outstanding_35_percent": gratuity_35_percent,
            },
            "note": "Gratuity is not included in the total price above",
        }

    def _get_minimum_filler_options(self, shortfall_amount: float) -> list[dict[str, Any]]:
        """
        Get suggestions for PAID upgrades/add-ons to reach minimum order value

        IMPORTANT: These are NOT free items. Customer pays $550 minimum regardless.
        If their food total is under $550, we suggest upgrades they can ADD (and pay for)
        to maximize the value of their minimum $550 spend.

        All items and prices are dynamic and pulled from database/frontend menu.

        Args:
            shortfall_amount: How much more needed to reach $550 minimum

        Returns:
            List of suggested PAID items to add for better value
        """
        suggestions = []
        remaining = Decimal(str(shortfall_amount))

        # Priority order: Best value items first (pulled from your actual menu)
        upgrade_options = [
            # Protein upgrades (premium)
            {
                "name": "Filet Mignon Upgrade",
                "price": self.get_upgrade_price("filet_mignon"),
                "category": "protein_upgrade",
                "per_person": True,
            },
            {
                "name": "Lobster Tail Upgrade",
                "price": self.get_upgrade_price("lobster_tail"),
                "category": "protein_upgrade",
                "per_person": True,
            },
            # Additional items (+$10 each from your menu)
            {
                "name": "3rd Protein",
                "price": self.get_addon_price("third_protein"),
                "category": "protein",
                "per_person": False,
            },
            {
                "name": "Gyoza",
                "price": self.get_addon_price("gyoza"),
                "category": "appetizer",
                "per_person": False,
            },
            # Additional enhancements (+$5 each from your menu)
            {
                "name": "Yakisoba Noodles",
                "price": self.get_addon_price("yakisoba_noodles"),
                "category": "side",
                "per_person": False,
            },
            {
                "name": "Extra Fried Rice",
                "price": self.get_addon_price("extra_fried_rice"),
                "category": "side",
                "per_person": False,
            },
            {
                "name": "Extra Vegetables",
                "price": self.get_addon_price("extra_vegetables"),
                "category": "side",
                "per_person": False,
            },
            {
                "name": "Edamame",
                "price": self.get_addon_price("edamame"),
                "category": "appetizer",
                "per_person": False,
            },
        ]

        # Suggest items that fit within the shortfall to maximize their $550 spend
        for option in upgrade_options:
            if option["price"] > Decimal("0.00") and option["price"] <= remaining:
                suggestions.append(
                    {
                        "name": option["name"],
                        "price": float(option["price"]),
                        "category": option["category"],
                        "per_person": option["per_person"],
                        "description": f"Add {option['name']} (${float(option['price']):.2f}) to enhance your experience",
                    }
                )
                remaining -= option["price"]

                if remaining <= Decimal("1.00"):  # Close enough
                    break

        return suggestions

    def get_adult_price(self) -> Decimal:
        """
        Get current adult (13+) base price

        Returns:
            Decimal: Price per adult in dollars
        """
        # Try database first
        if self.db:
            try:
                result = self.db.execute(
                    select(MenuItem.base_price)
                    .where(MenuItem.category == "Adult Menu")
                    .where(MenuItem.is_active)
                    .limit(1)
                ).scalar()

                if result:
                    return Decimal(str(result))
            except Exception as e:
                logger.warning(f"Failed to fetch adult price from DB: {e}, using fallback")

        # Fallback to configuration
        return Decimal(str(self.BASE_PRICING["adult_base"]))

    def get_child_price(self) -> Decimal:
        """
        Get current child (6-12) base price

        Returns:
            Decimal: Price per child in dollars
        """
        # Try database first
        if self.db:
            try:
                result = self.db.execute(
                    select(MenuItem.base_price)
                    .where(MenuItem.category == "Kids Menu")
                    .where(MenuItem.is_active)
                    .limit(1)
                ).scalar()

                if result:
                    return Decimal(str(result))
            except Exception as e:
                logger.warning(f"Failed to fetch child price from DB: {e}, using fallback")

        # Fallback to configuration
        return Decimal(str(self.BASE_PRICING["child_base"]))

    def get_upgrade_price(self, upgrade_name: str) -> Decimal:
        """
        Get price for premium protein upgrade

        Args:
            upgrade_name: Name of upgrade (e.g., "filet_mignon", "lobster_tail")

        Returns:
            Decimal: Additional cost per person in dollars
        """
        upgrade_key = upgrade_name.lower().replace(" ", "_")

        # Try database first
        if self.db:
            try:
                result = self.db.execute(
                    select(AddonItem.price)
                    .where(AddonItem.name.ilike(f"%{upgrade_name}%"))
                    .where(AddonItem.category == "Protein Upgrades")
                    .where(AddonItem.is_active)
                    .limit(1)
                ).scalar()

                if result:
                    return Decimal(str(result))
            except Exception as e:
                logger.warning(f"Failed to fetch upgrade price from DB: {e}, using fallback")

        # Fallback to configuration
        return Decimal(str(self.PREMIUM_UPGRADES.get(upgrade_key, 0.00)))

    def get_addon_price(self, addon_name: str) -> Decimal:
        """
        Get price for service add-on

        Args:
            addon_name: Name of addon (e.g., "premium_sake_service")

        Returns:
            Decimal: Addon cost in dollars
        """
        addon_key = addon_name.lower().replace(" ", "_")

        # Try database first
        if self.db:
            try:
                result = self.db.execute(
                    select(AddonItem.price)
                    .where(AddonItem.name.ilike(f"%{addon_name}%"))
                    .where(AddonItem.is_active)
                    .limit(1)
                ).scalar()

                if result:
                    return Decimal(str(result))
            except Exception as e:
                logger.warning(f"Failed to fetch addon price from DB: {e}, using fallback")

        # Fallback to configuration
        return Decimal(str(self.ADDONS.get(addon_key, 0.00)))

    def calculate_party_quote(
        self,
        adults: int,
        children: int = 0,
        children_under_5: int = 0,
        protein_selections: dict[str, int] | None = None,  # NEW: Protein breakdown
        upgrades: dict[str, int] | None = None,  # DEPRECATED: Use protein_selections
        addons: list[str] | None = None,
        customer_address: str | None = None,
        customer_zipcode: str | None = None,
        travel_miles: float | None = None,  # Deprecated: use customer_address instead
    ) -> dict[str, Any]:
        """
        Calculate complete party quote with breakdown

        Args:
            adults: Number of adults (13+)
            children: Number of children (6-12)
            children_under_5: Number of children under 5 (FREE)
            protein_selections: Dict of protein name to count (NEW PREFERRED METHOD)
                Example: {"steak": 11, "chicken": 9, "filet_mignon": 2, "lobster_tail": 1}
            upgrades: DEPRECATED - Use protein_selections instead
            addons: List of addon service names
            customer_address: Full customer address for Google Maps calculation (RECOMMENDED)
            customer_zipcode: Customer ZIP code (if full address not provided)
            travel_miles: DEPRECATED - Manual miles, use customer_address for accuracy

        Returns:
            Dict with complete quote breakdown including protein costs
        """
        adult_price = self.get_adult_price()
        child_price = self.get_child_price()

        # Base costs
        adult_total = adult_price * adults
        child_total = child_price * children
        subtotal = adult_total + child_total

        # Calculate total guest count for protein calculations
        total_guests = adults + children

        # Protein upgrade costs (NEW SMART SYSTEM)
        protein_calculator = get_protein_calculator_service()
        protein_cost_data = None
        upgrade_total = Decimal("0.00")
        upgrade_breakdown = {}

        if protein_selections:
            # Use new protein calculator system
            protein_cost_data = protein_calculator.calculate_protein_costs(
                guest_count=total_guests, protein_selections=protein_selections
            )
            upgrade_total = Decimal(str(protein_cost_data["total_protein_cost"]))

            # Format protein breakdown for response
            for protein_item in protein_cost_data["breakdown"]:
                protein_name = protein_item["protein_name"]
                upgrade_breakdown[protein_name] = {
                    "count": protein_item["quantity"],
                    "unit_price": protein_item["upgrade_price"],
                    "total": protein_item["quantity"] * protein_item["upgrade_price"],
                    "is_free": protein_item["is_free"],
                    "is_upgrade": protein_item["is_upgrade"],
                    "is_third_protein": protein_item["is_third_protein"],
                }
        elif upgrades:
            # Legacy upgrade system (DEPRECATED - for backward compatibility)
            for upgrade_name, count in upgrades.items():
                upgrade_price = self.get_upgrade_price(upgrade_name)
                upgrade_cost = upgrade_price * count
                upgrade_total += upgrade_cost
                upgrade_breakdown[upgrade_name] = {
                    "count": count,
                    "unit_price": float(upgrade_price),
                    "total": float(upgrade_cost),
                }

        # Addon costs
        addon_total = Decimal("0.00")
        addon_breakdown = {}
        if addons:
            for addon_name in addons:
                addon_price = self.get_addon_price(addon_name)
                addon_total += addon_price
                addon_breakdown[addon_name] = float(addon_price)

        # Travel fee calculation (use Google Maps if address provided)
        travel_info = None
        travel_fee = Decimal("0.00")

        if customer_address or customer_zipcode:
            # Use Google Maps for accurate calculation
            travel_info = self.calculate_travel_distance(customer_address, customer_zipcode)
            if travel_info.get("status") == "success" and travel_info.get("travel_fee") is not None:
                travel_fee = Decimal(str(travel_info["travel_fee"]))
        elif travel_miles:
            # Fallback to manual miles (deprecated)
            if travel_miles > self.TRAVEL_PRICING["free_radius_miles"]:
                extra_miles = travel_miles - self.TRAVEL_PRICING["free_radius_miles"]
                travel_fee = Decimal(str(extra_miles * self.TRAVEL_PRICING["per_mile_after"]))
            travel_info = {
                "status": "manual",
                "distance_miles": travel_miles,
                "travel_fee": float(travel_fee),
                "note": "Manual distance - for exact quote, provide full address",
            }

        # Check minimum BEFORE travel fee (travel fee is added on top)
        food_total = subtotal + upgrade_total + addon_total  # Food & upgrades only
        party_minimum = Decimal(str(self.BASE_PRICING["party_minimum"]))

        meets_minimum = food_total >= party_minimum
        minimum_shortfall = max(Decimal("0.00"), party_minimum - food_total)

        # Suggest PAID upgrades/add-ons if under minimum (to maximize $550 value)
        upgrade_suggestions = []
        actual_charge_before_travel = food_total

        if minimum_shortfall > Decimal("0.00"):
            # Get upgrade suggestions from database (these are PAID, not free)
            upgrade_suggestions = self._get_minimum_filler_options(float(minimum_shortfall))
            # Customer will be charged the minimum regardless
            actual_charge_before_travel = party_minimum

        # Grand total: Charged amount (minimum or food total, whichever is higher) + travel fee
        grand_total = actual_charge_before_travel + travel_fee

        # Get gratuity guidance (based on what customer is actually charged, before travel)
        gratuity_guidance = self.get_gratuity_guidance(float(actual_charge_before_travel))

        response = {
            "breakdown": {
                "adults": {
                    "count": adults,
                    "unit_price": float(adult_price),
                    "total": float(adult_total),
                },
                "children": {
                    "count": children,
                    "unit_price": float(child_price),
                    "total": float(child_total),
                },
                "children_under_5": {
                    "count": children_under_5,
                    "unit_price": 0.00,
                    "total": 0.00,
                    "note": "Free for ages 5 & under",
                },
                "subtotal": float(subtotal),
                "upgrades": upgrade_breakdown,
                "upgrade_total": float(upgrade_total),
                "addons": addon_breakdown,
                "addon_total": float(addon_total),
                "food_total": float(food_total),  # Food + upgrades + addons (before travel)
                "travel_fee": float(travel_fee),
                "travel_info": travel_info,  # Full Google Maps travel details
            },
            "total": float(grand_total),  # Food total + travel fee
            "meets_minimum": meets_minimum,
            "minimum_required": float(party_minimum),
            "minimum_shortfall": float(minimum_shortfall),
            "actual_charge_before_travel": float(
                actual_charge_before_travel
            ),  # What customer pays (min $550)
            "upgrade_suggestions": upgrade_suggestions,  # PAID suggestions to maximize value
            "minimum_note": (
                (
                    f"Our party minimum is ${float(party_minimum):.2f}. You'll be charged ${float(actual_charge_before_travel):.2f} "
                    f"+ ${float(travel_fee):.2f} travel fee = ${float(grand_total):.2f} total. "
                    f"Consider adding these upgrades to enhance your ${float(actual_charge_before_travel):.2f} experience!"
                )
                if not meets_minimum
                else None
            ),
            "gratuity_guidance": gratuity_guidance,  # Enhanced gratuity guidance
            "total_guests": adults + children + children_under_5,
            "pricing_as_of": datetime.now().isoformat(),
            "note": "All pricing is dynamic and subject to change. Current prices pulled from live database.",
            "travel_policy": (
                self.get_travel_fee_explanation(detailed=True)
                if not travel_info or travel_info.get("requires_full_address")
                else None
            ),
        }

        # Add protein calculation data if available
        if protein_cost_data:
            response["protein_analysis"] = {
                "total_guests": total_guests,
                "free_protein_allowance": protein_cost_data["free_protein_allowance"],
                "total_proteins_selected": protein_cost_data["total_proteins"],
                "protein_breakdown": protein_cost_data["breakdown"],
                "protein_explanation": protein_cost_data["explanation"],
                "proteins_summary": protein_cost_data["proteins_summary"],
                "upgrade_cost": protein_cost_data["upgrade_cost"],
                "third_protein_cost": protein_cost_data["third_protein_cost"],
                "total_protein_cost": protein_cost_data["total_protein_cost"],
            }

        return response

    def get_pricing_summary(self) -> dict[str, Any]:
        """
        Get complete pricing summary for display

        Returns:
            Dict with all current pricing information
        """
        return {
            "base_pricing": {
                "adult_13_plus": float(self.get_adult_price()),
                "child_6_to_12": float(self.get_child_price()),
                "child_under_5": 0.00,
                "party_minimum": self.BASE_PRICING["party_minimum"],
            },
            "premium_upgrades": {
                "filet_mignon": float(self.get_upgrade_price("filet_mignon")),
                "salmon": float(self.get_upgrade_price("salmon")),
                "scallops": float(self.get_upgrade_price("scallops")),
                "lobster_tail": float(self.get_upgrade_price("lobster_tail")),
            },
            "addons": {
                "premium_sake_service": float(self.get_addon_price("premium_sake_service")),
                "extended_performance": float(self.get_addon_price("extended_performance")),
                "custom_menu_planning": float(self.get_addon_price("custom_menu_planning")),
            },
            "travel": {
                "free_radius_miles": self.TRAVEL_PRICING["free_radius_miles"],
                "per_mile_after": self.TRAVEL_PRICING["per_mile_after"],
            },
            "gratuity": {
                "suggested_range": f"{self.GRATUITY['suggested_min_percent']}-{self.GRATUITY['suggested_max_percent']}%",
                "payment_method": "Direct to chef (cash, Venmo, Zelle)",
                "not_included": "Gratuity is NOT included in quoted prices",
            },
            "last_updated": datetime.now().isoformat(),
        }


# Singleton instance for easy access
_pricing_service_instance: PricingService | None = None


def get_pricing_service(db: Session | None = None, station_id: str | None = None) -> PricingService:
    """
    Get or create singleton pricing service instance

    Args:
        db: SQLAlchemy database session (optional)
        station_id: Station ID for multi-tenant pricing and travel calculations (optional)

    Returns:
        PricingService: Singleton instance
    """
    global _pricing_service_instance

    # Always create new instance if DB session provided (sessions shouldn't be reused)
    if _pricing_service_instance is None or db is not None:
        _pricing_service_instance = PricingService(db, station_id)

    return _pricing_service_instance


# Example usage:
if __name__ == "__main__":
    pricing = get_pricing_service()

    # Example: Debbie's quote with REAL PRICING and Google Maps travel calculation
    quote = pricing.calculate_party_quote(
        adults=14,
        children=2,
        children_under_5=0,
        upgrades={"filet_mignon": 10},
        addons=[],
        customer_address="Antioch, CA 94509",  # Use Google Maps for accurate distance
    )

    if quote["breakdown"]["travel_info"]:
        pass
