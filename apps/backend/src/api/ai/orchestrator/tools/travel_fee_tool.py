"""
Travel Fee Tool for AI Orchestrator

This tool calculates travel fees using Google Maps Distance Matrix API.
Provides accurate distance-based fees for customer locations.

Author: MyHibachi Development Team
Created: October 31, 2025
"""

import logging

from api.ai.endpoints.services.pricing_service import get_pricing_service

from .base_tool import BaseTool, ToolParameter, ToolResult

logger = logging.getLogger(__name__)


class TravelFeeTool(BaseTool):
    """
    Calculate travel fee based on customer location.

    Uses Google Maps Distance Matrix API for accurate distance calculation.

    Pricing:
    - FREE within 30 miles
    - $2.00 per mile after 30 miles

    Example AI Usage:
        Customer: "Do you charge a travel fee to Roseville?"

        AI calls: calculate_travel_fee(
            customer_address="Roseville, CA"
        )

        Result: {
            "distance_miles": 18.5,
            "travel_fee": 0.00,
            "is_free": true,
            "message": "Great news! Your location is within our FREE 30-mile service area."
        }
    """

    @property
    def name(self) -> str:
        return "calculate_travel_fee"

    @property
    def description(self) -> str:
        return """Calculate travel fee for customer location using Google Maps.

Use this tool when customer asks:
- "Do you charge travel fees?"
- "How much is the travel fee to [location]?"
- "Do you service my area?"
- Any question about location-based fees

Service Area: California - Bay Area, Sacramento, Central Valley
Headquarters: Fremont, CA

Pricing:
- FREE within 30 miles of Fremont, CA
- $2.00 per mile after the first 30 miles
- Calculated using Google Maps for accuracy

Returns exact distance and fee amount."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="customer_address",
                type="string",
                description="""Customer location for travel fee calculation.
Can be:
- Full address: "123 Main St, Fremont, CA 94536"
- City: "San Jose, CA"
- ZIP code: "94536"

More specific addresses give more accurate results.""",
                required=False,
            ),
            ToolParameter(
                name="customer_zipcode",
                type="string",
                description="""Customer ZIP code (if full address not available).
Example: "94536"

Use customer_address for better accuracy when possible.""",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute travel fee calculation.

        Args:
            customer_address: Full address or city
            customer_zipcode: ZIP code

        Returns:
            ToolResult with travel fee details
        """
        try:
            # Extract parameters
            customer_address = kwargs.get("customer_address")
            customer_zipcode = kwargs.get("customer_zipcode")

            # Validate input
            if not customer_address and not customer_zipcode:
                return ToolResult(
                    success=False, error="Either customer_address or customer_zipcode is required"
                )

            # Initialize pricing service
            pricing_service = get_pricing_service()

            # Calculate travel distance
            travel_info = pricing_service.calculate_travel_distance(
                customer_address, customer_zipcode
            )

            # Check for errors
            if travel_info.get("status") == "api_error":
                return ToolResult(
                    success=True,  # Not a tool error, just API unavailable
                    data={
                        "error_type": "api_unavailable",
                        "message": travel_info.get("message"),
                        "requires_admin_follow_up": True,
                        "fallback_instruction": "Please call us at (916) 740-8768 and we'll provide an immediate quote with accurate travel fees.",
                    },
                )

            if travel_info.get("status") == "routing_error":
                return ToolResult(
                    success=True,  # Not a tool error, just invalid address
                    data={
                        "error_type": "invalid_address",
                        "message": travel_info.get("message"),
                        "requires_full_address": True,
                        "suggestion": "Please provide your complete address (street, city, state, ZIP) for accurate calculation.",
                    },
                )

            # Successful calculation
            distance_miles = travel_info.get("distance_miles", 0)
            travel_fee = travel_info.get("travel_fee", 0)
            is_free = travel_fee == 0

            # Create friendly message
            if is_free:
                message = f"Great news! Your location is within our FREE 30-mile service area (you're {distance_miles:.1f} miles away)."
            else:
                billable_miles = distance_miles - 30
                message = f"Your location is {distance_miles:.1f} miles away. Travel fee: ${travel_fee:.2f} (${2.00:.2f}/mile for the {billable_miles:.1f} miles beyond our FREE 30-mile radius)."

            response_data = {
                "distance_miles": round(distance_miles, 2),
                "travel_fee": float(travel_fee),
                "is_free": is_free,
                "free_radius_miles": 30,
                "per_mile_rate": 2.00,
                "billable_miles": max(0, distance_miles - 30),
                "message": message,
                "driving_time": travel_info.get("duration_text", "Unknown"),
                "location_details": {
                    "address_provided": customer_address,
                    "zipcode_provided": customer_zipcode,
                    "note": travel_info.get("note", ""),
                },
            }

            logger.info(
                "Travel fee tool executed successfully",
                extra={
                    "distance_miles": distance_miles,
                    "travel_fee": travel_fee,
                    "is_free": is_free,
                },
            )

            return ToolResult(
                success=True,
                data=response_data,
                metadata={
                    "calculation_method": "google_maps" if customer_address else "zipcode_estimate"
                },
            )

        except Exception as e:
            logger.error(f"Travel fee tool execution failed: {e!s}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to calculate travel fee: {e!s}",
                metadata={"error_type": type(e).__name__},
            )
