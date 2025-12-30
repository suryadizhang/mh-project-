"""
Pricing Tool for AI Orchestrator

This tool wraps the existing PricingService to calculate accurate party quotes
with protein upgrades, addons, and travel fees. Integrates with the protein
calculator system for smart upgrade pricing.

The AI uses this tool to provide exact quotes instead of estimates.

Author: MyHibachi Development Team
Created: October 31, 2025
"""

import logging

from ...endpoints.services.pricing_service import get_pricing_service

from .base_tool import BaseTool, ToolParameter, ToolResult

logger = logging.getLogger(__name__)


class PricingTool(BaseTool):
    """
    Calculate accurate hibachi party quote with travel fees and protein upgrades.

    This tool provides the AI with the ability to generate exact pricing quotes
    instead of estimates. It integrates with:
    - Base pricing (adults, children)
    - Protein calculator (FREE proteins + upgrades)
    - Travel fee calculation (Google Maps API)
    - Addon services
    - Party minimums

    Example AI Usage:
        Customer: "What's the price for 10 adults with 5 filet and 5 lobster in 95630?"

        AI calls: calculate_party_quote(
            adults=10,
            protein_selections={"filet_mignon": 5, "lobster_tail": 5},
            customer_zipcode="95630"
        )

        Result: {
            "subtotal": $550.00,
            "protein_upgrades": $100.00,
            "travel_fee": $0.00,
            "total": $650.00,
            "breakdown": {...}
        }
    """

    @property
    def name(self) -> str:
        return "calculate_party_quote"

    @property
    def description(self) -> str:
        return """Calculate accurate hibachi party quote with protein upgrades, travel fees, and addons.

This tool provides EXACT pricing (not estimates) for hibachi party bookings. Use it whenever
a customer asks about pricing, costs, or "how much does it cost".

Key Features:
- Base pricing: Per-person rates for adults (13+), children (6-12), FREE for under 5
- Protein upgrades: Premium proteins (Filet/Salmon/Scallops/Lobster) at upgrade fees
- FREE proteins: Chicken, NY Strip Steak, Shrimp, Tofu, Vegetables (2 per guest included)
- Extra protein: Additional fee per extra protein beyond 2 per guest
- Travel fees: FREE within service radius, per-mile fee beyond
- Party minimum: Minimum total applies to smaller parties
- Addon services: Premium sake, extended performance, custom menu

ALWAYS use this tool for pricing questions - NEVER estimate or guess prices.
The tool returns current pricing from our pricing system."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="adults",
                type="integer",
                description="Number of adult guests (13+ years old). Required.",
                required=True,
            ),
            ToolParameter(
                name="children",
                type="integer",
                description="Number of children (6-12 years old). Optional, defaults to 0.",
                required=False,
            ),
            ToolParameter(
                name="children_under_5",
                type="integer",
                description="Number of children under 5 years old (FREE). Optional, defaults to 0.",
                required=False,
            ),
            ToolParameter(
                name="protein_selections",
                type="object",
                description="""Protein choices as a dictionary with protein name as key and quantity as value.
Example: {"chicken": 8, "filet_mignon": 3, "lobster_tail": 2}

Valid protein names:
- FREE: chicken, ny_strip_steak, steak, shrimp, tofu, vegetables
- UPGRADE: filet_mignon, salmon, scallops (premium upgrade fee applies)
- PREMIUM: lobster_tail (higher premium fee applies)

Note: First 2 proteins per guest are included. Extra proteins add additional fee.""",
                required=False,
            ),
            ToolParameter(
                name="addons",
                type="array",
                description="""List of addon services requested. Optional.
Valid addons:
- "premium_sake_service" (premium fee)
- "extended_performance" (premium fee)
- "custom_menu_planning" (premium fee)
Addon pricing is determined by current rates.""",
                required=False,
                items={"type": "string"},  # Required for OpenAI array schema validation
            ),
            ToolParameter(
                name="customer_address",
                type="string",
                description="""Full customer address for accurate travel fee calculation (RECOMMENDED).
Example: "123 Main St, Sacramento, CA 95814"

Used with Google Maps API for exact distance and travel fees.
If only ZIP code available, use customer_zipcode parameter instead.""",
                required=False,
            ),
            ToolParameter(
                name="customer_zipcode",
                type="string",
                description="""Customer ZIP code for travel fee estimation (if full address not available).
Example: "95630"

Use customer_address for more accurate calculation when possible.""",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute pricing calculation.

        Args:
            adults: Number of adult guests
            children: Number of children (6-12)
            children_under_5: Number of children under 5
            protein_selections: Dict of protein name to quantity
            addons: List of addon service names
            customer_address: Full address for travel calculation
            customer_zipcode: ZIP code for travel calculation

        Returns:
            ToolResult with complete quote breakdown
        """
        try:
            # Extract parameters
            adults = kwargs.get("adults", 0)
            children = kwargs.get("children", 0)
            children_under_5 = kwargs.get("children_under_5", 0)
            protein_selections = kwargs.get("protein_selections")
            addons = kwargs.get("addons")
            customer_address = kwargs.get("customer_address")
            customer_zipcode = kwargs.get("customer_zipcode")

            # Validate adults
            if adults < 1:
                return ToolResult(
                    success=False, error="At least 1 adult guest is required for a party"
                )

            # Initialize pricing service
            pricing_service = get_pricing_service()

            # Calculate quote
            quote = pricing_service.calculate_party_quote(
                adults=adults,
                children=children,
                children_under_5=children_under_5,
                protein_selections=protein_selections,
                addons=addons,
                customer_address=customer_address,
                customer_zipcode=customer_zipcode,
            )

            # Format response data
            response_data = {
                "party_details": {
                    "adults": adults,
                    "children": children,
                    "children_under_5": children_under_5,
                    "total_guests": adults + children + children_under_5,
                    "billable_guests": adults + children,
                },
                "pricing_breakdown": {
                    "base_cost": float(quote.get("subtotal", 0)),
                    "protein_upgrades": float(quote.get("upgrade_total", 0)),
                    "addons": float(quote.get("addon_total", 0)),
                    "travel_fee": float(quote.get("travel_fee", 0)),
                    "subtotal": float(quote.get("subtotal_before_min", 0)),
                    "party_minimum_applied": quote.get("party_minimum_applied", False),
                    "total": float(quote.get("total", 0)),
                },
                "protein_breakdown": quote.get("upgrade_breakdown", {}),
                "addon_breakdown": quote.get("addon_breakdown", {}),
                "travel_info": quote.get("travel_info"),
                "pricing_notes": [],
            }

            # Add helpful notes for the AI
            notes = []

            if quote.get("party_minimum_applied"):
                # Use dynamic minimum from quote response (SSoT - no hardcoded values)
                min_required = quote.get("minimum_required", 550)
                notes.append(
                    f"Party minimum of ${min_required:.2f} applied (original subtotal: ${quote.get('subtotal_before_min', 0):.2f})"
                )

            if protein_selections:
                protein_cost = quote.get("upgrade_total", 0)
                if protein_cost > 0:
                    notes.append(
                        f"Protein upgrades: ${protein_cost:.2f} (includes premium selections and extra protein charges)"
                    )
                else:
                    notes.append(
                        "All protein selections are FREE (within the 2 proteins per guest limit)"
                    )

            if quote.get("travel_fee", 0) > 0:
                travel_info = quote.get("travel_info", {})
                distance = travel_info.get("distance_miles", 0)
                # Use dynamic free_miles from travel_info (SSoT - no hardcoded values)
                free_miles = travel_info.get("breakdown", {}).get("free_miles", 30)
                notes.append(
                    f"Travel fee: ${quote['travel_fee']:.2f} for {distance:.1f} miles (FREE first {free_miles} miles)"
                )
            elif customer_address or customer_zipcode:
                # Use dynamic free_miles from quote travel_info for consistency
                travel_info = quote.get("travel_info", {})
                free_miles = travel_info.get("breakdown", {}).get("free_miles", 30)
                notes.append(f"No travel fee (within FREE {free_miles}-mile radius)")

            if children_under_5 > 0:
                notes.append(f"Children under 5: {children_under_5} (FREE)")

            response_data["pricing_notes"] = notes

            # Add suggested gratuity range
            total = quote.get("total", 0)
            response_data["gratuity_suggestion"] = {
                "min_20_percent": round(total * 0.20, 2),
                "max_35_percent": round(total * 0.35, 2),
                "note": "Gratuity is not included and is at your discretion. Our chefs appreciate 20-35%.",
            }

            logger.info(
                "Pricing tool executed successfully",
                extra={
                    "adults": adults,
                    "children": children,
                    "total": total,
                    "has_proteins": bool(protein_selections),
                    "has_travel": bool(customer_address or customer_zipcode),
                },
            )

            return ToolResult(
                success=True,
                data=response_data,
                metadata={
                    "pricing_version": "v2.0",
                    "includes_protein_calculator": True,
                    "travel_calculation_method": (
                        "google_maps" if customer_address else "zipcode_estimate"
                    ),
                },
            )

        except Exception as e:
            logger.error(f"Pricing tool execution failed: {e!s}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to calculate quote: {e!s}",
                metadata={"error_type": type(e).__name__},
            )
