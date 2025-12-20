"""
Protein Tool for AI Orchestrator

This tool calculates protein upgrade costs using the smart protein calculator.
Handles FREE proteins, premium upgrades, and extra protein charges.

Author: MyHibachi Development Team
Created: October 31, 2025
"""

import logging

from api.ai.endpoints.services.protein_calculator_service import (
    get_protein_calculator_service,
)

from .base_tool import BaseTool, ToolParameter, ToolResult

logger = logging.getLogger(__name__)


class ProteinTool(BaseTool):
    """
    Calculate protein upgrade costs with smart FREE protein logic.

    Protein Pricing Rules:
    1. First 2 proteins per guest: FREE (if from FREE list)
    2. Premium upgrades: Filet/Salmon/Scallops (+$5), Lobster (+$15)
    3. Extra protein (beyond 2 per guest): +$10 additional charge

    FREE Proteins:
    - Chicken
    - NY Strip Steak
    - Shrimp
    - Tofu
    - Vegetables

    Example AI Usage:
        Customer: "What's the extra cost for 5 filet mignon and 5 lobster for 10 guests?"

        AI calls: calculate_protein_costs(
            guest_count=10,
            protein_selections={"filet_mignon": 5, "lobster_tail": 5}
        )

        Result: {
            "upgrade_cost": $25 (5 filet @ $5),
            "lobster_cost": $75 (5 lobster @ $15),
            "third_protein_cost": $0,
            "total": $100
        }
    """

    @property
    def name(self) -> str:
        return "calculate_protein_costs"

    @property
    def description(self) -> str:
        return """Calculate protein upgrade costs for hibachi party.

Use this tool when customer asks specifically about:
- Protein pricing or costs
- "How much extra for filet mignon?"
- "What's the upgrade cost for lobster?"
- Protein combinations and pricing

Protein Rules:
- Each guest gets 2 FREE proteins (from FREE list)
- Premium upgrades: Filet/Salmon/Scallops (+$5 each), Lobster (+$15 each)
- Extra protein (beyond 2 per guest): +$10 each charge
- Proteins are per portion, not per guest

FREE Proteins (no charge):
- Chicken
- NY Strip Steak
- Shrimp
- Tofu
- Vegetables

UPGRADE Proteins:
- Filet Mignon: +$5 per portion
- Salmon: +$5 per portion
- Scallops: +$5 per portion
- Lobster Tail: +$15 per portion

Note: For complete quote with proteins, use calculate_party_quote tool instead."""

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="guest_count",
                type="integer",
                description="Total number of guests (adults + children). Required for extra protein calculation.",
                required=True,
            ),
            ToolParameter(
                name="protein_selections",
                type="object",
                description="""Protein choices as dictionary with protein name as key and quantity as value.
Example: {"chicken": 10, "filet_mignon": 5, "lobster_tail": 3}

Valid protein names:
- FREE: chicken, ny_strip_steak, steak, shrimp, tofu, vegetables
- UPGRADE (+$5): filet_mignon, salmon, scallops
- PREMIUM (+$15): lobster_tail

Note: Quantities are per portion, not per guest. Each guest gets 2 proteins.""",
                required=True,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute protein cost calculation.

        Args:
            guest_count: Number of guests
            protein_selections: Dict of protein name to quantity

        Returns:
            ToolResult with protein cost breakdown
        """
        try:
            # Extract parameters
            guest_count = kwargs.get("guest_count", 0)
            protein_selections = kwargs.get("protein_selections", {})

            # Validate inputs
            if guest_count < 1:
                return ToolResult(success=False, error="guest_count must be at least 1")

            if not protein_selections:
                return ToolResult(success=False, error="protein_selections cannot be empty")

            # Initialize protein calculator
            protein_calc = get_protein_calculator_service()

            # Calculate protein costs
            result = protein_calc.calculate_protein_costs(
                guest_count=guest_count, protein_selections=protein_selections
            )

            # Format response data
            response_data = {
                "guest_count": guest_count,
                "total_protein_portions": sum(protein_selections.values()),
                "proteins_per_guest": round(sum(protein_selections.values()) / guest_count, 1),
                "cost_breakdown": {
                    "upgrade_cost": result["upgrade_cost"],
                    "third_protein_cost": result["third_protein_cost"],
                    "total_protein_cost": result["total_protein_cost"],
                },
                "protein_details": [],
                "pricing_notes": [],
            }

            # Add detailed breakdown for each protein
            for item in result["breakdown"]:
                protein_detail = {
                    "protein_name": item["protein_name"],
                    "quantity": item["quantity"],
                    "upgrade_price": item["upgrade_price"],
                    "total_cost": item["quantity"] * item["upgrade_price"],
                    "is_free": item["is_free"],
                    "is_upgrade": item["is_upgrade"],
                    "is_third_protein": item["is_third_protein"],
                    "display_name": item["protein_name"].replace("_", " ").title(),
                }
                response_data["protein_details"].append(protein_detail)

            # Add helpful notes
            notes = []

            # FREE proteins note
            free_proteins = [
                p for p in result["breakdown"] if p["is_free"] and p["upgrade_price"] == 0
            ]
            if free_proteins:
                free_names = [p["protein_name"].replace("_", " ").title() for p in free_proteins]
                notes.append(f"FREE proteins: {', '.join(free_names)} (within 2 per guest)")

            # Upgrade proteins note
            upgrade_proteins = [
                p for p in result["breakdown"] if p["is_upgrade"] and not p["is_third_protein"]
            ]
            if upgrade_proteins and result["upgrade_cost"] > 0:
                notes.append(f"Premium upgrades: ${result['upgrade_cost']:.2f}")

            # Extra protein note
            if result["third_protein_cost"] > 0:
                total_portions = sum(protein_selections.values())
                allowed_free = guest_count * 2
                extra_portions = total_portions - allowed_free
                notes.append(
                    f"Extra protein charge: ${result['third_protein_cost']:.2f} (+$10 per portion beyond 2 per guest, {extra_portions} extra portions)"
                )

            # Educational note
            if sum(protein_selections.values()) <= guest_count * 2:
                free_count = sum(
                    1 for p in result["breakdown"] if p["is_free"] and p["upgrade_price"] == 0
                )
                if free_count > 0:
                    notes.append("Within the 2 proteins per guest limit - no extra protein charges")

            response_data["pricing_notes"] = notes
            response_data["proteins_summary"] = result["proteins_summary"]

            logger.info(
                "Protein tool executed successfully",
                extra={
                    "guest_count": guest_count,
                    "total_proteins": sum(protein_selections.values()),
                    "total_cost": result["total_protein_cost"],
                },
            )

            return ToolResult(
                success=True,
                data=response_data,
                metadata={"calculator_version": "v2.0", "includes_third_protein_logic": True},
            )

        except Exception as e:
            logger.error(f"Protein tool execution failed: {e!s}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Failed to calculate protein costs: {e!s}",
                metadata={"error_type": type(e).__name__},
            )
