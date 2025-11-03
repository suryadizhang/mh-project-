"""
Protein Upgrade Calculator Service
Handles complex protein selection logic based on guest count and protein choices

PRICING VERIFIED FROM WEBSITE (apps/customer/src/data/faqsData.ts):
- Each guest gets 2 FREE protein choices
- FREE proteins: Chicken, NY Strip Steak, Shrimp, Tofu
- UPGRADE proteins: Salmon (+$5), Scallops (+$5), Filet Mignon (+$5), Lobster Tail (+$15)
- 3rd protein: +$10 per person (any protein)
- If 3rd protein is premium: +$10 (3rd) + premium price (+$5 or +$15)
"""

import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProteinBreakdown:
    """Represents the breakdown of protein selections"""
    protein_name: str
    quantity: int
    is_free: bool
    is_upgrade: bool
    upgrade_price: Decimal
    is_third_protein: bool


class ProteinCalculatorService:
    """
    Calculate protein upgrade costs based on guest count and protein selections
    
    Business Rules:
    1. Each guest gets 2 FREE protein choices
    2. FREE proteins: Chicken, NY Strip Steak, Shrimp, Tofu
    3. UPGRADE proteins: Salmon (+$5), Scallops (+$5), Filet Mignon (+$5), Lobster Tail (+$15)
    4. If total proteins > (guests × 2): Extra proteins are charged as "3rd protein" (+$10 each)
    5. If a 3rd protein is premium: +$10 (3rd) + premium price
    """
    
    # FREE base proteins (included in base price)
    FREE_PROTEINS = {
        "chicken": "Chicken",
        "ny_strip_steak": "NY Strip Steak",
        "steak": "NY Strip Steak",  # Alias
        "shrimp": "Shrimp",
        "tofu": "Tofu",
        "vegetables": "Vegetables"
    }
    
    # Premium protein upgrades
    PREMIUM_UPGRADES = {
        "salmon": {"name": "Salmon", "price": Decimal("5.00")},
        "scallops": {"name": "Scallops", "price": Decimal("5.00")},
        "filet_mignon": {"name": "Filet Mignon", "price": Decimal("5.00")},
        "filet": {"name": "Filet Mignon", "price": Decimal("5.00")},  # Alias
        "lobster_tail": {"name": "Lobster Tail", "price": Decimal("15.00")},
        "lobster": {"name": "Lobster Tail", "price": Decimal("15.00")}  # Alias
    }
    
    # 3rd protein pricing
    THIRD_PROTEIN_PRICE = Decimal("10.00")
    
    def __init__(self):
        """Initialize the protein calculator service"""
        self._all_proteins = {**self.FREE_PROTEINS, **self.PREMIUM_UPGRADES}
    
    def calculate_protein_costs(
        self,
        guest_count: int,
        protein_selections: Dict[str, int]
    ) -> Dict:
        """
        Calculate protein upgrade costs based on selections
        
        Args:
            guest_count: Total number of guests
            protein_selections: Dict mapping protein names to quantities
                Example: {
                    "steak": 11,
                    "chicken": 9,
                    "filet_mignon": 0,
                    "lobster_tail": 1
                }
        
        Returns:
            Dict with:
                - upgrade_cost: Total cost for premium upgrades
                - third_protein_cost: Total cost for 3rd proteins
                - total_protein_cost: Combined total
                - breakdown: List of ProteinBreakdown objects
                - explanation: Human-readable explanation
                - proteins_summary: Summary for customer
        """
        logger.info(f"Calculating protein costs for {guest_count} guests")
        logger.info(f"Protein selections: {protein_selections}")
        
        # Calculate total proteins and free allowance
        total_proteins = sum(protein_selections.values())
        free_protein_allowance = guest_count * 2
        
        logger.info(f"Total proteins: {total_proteins}, Free allowance: {free_protein_allowance}")
        
        # Initialize costs
        upgrade_cost = Decimal("0.00")
        third_protein_cost = Decimal("0.00")
        breakdown = []
        
        # Track how many free proteins we've used
        free_proteins_used = 0
        
        # First pass: Calculate upgrade costs for premium proteins
        for protein_key, quantity in protein_selections.items():
            if quantity == 0:
                continue
            
            protein_lower = protein_key.lower().replace(" ", "_")
            
            # Check if it's a premium upgrade
            if protein_lower in self.PREMIUM_UPGRADES:
                premium_info = self.PREMIUM_UPGRADES[protein_lower]
                upgrade_price_per = premium_info["price"]
                
                # Each premium protein selected incurs the upgrade cost
                upgrade_cost += upgrade_price_per * quantity
                
                breakdown.append(ProteinBreakdown(
                    protein_name=premium_info["name"],
                    quantity=quantity,
                    is_free=False,
                    is_upgrade=True,
                    upgrade_price=upgrade_price_per,
                    is_third_protein=False
                ))
                
                logger.info(f"Premium protein: {premium_info['name']} × {quantity} = ${upgrade_price_per * quantity}")
            
            # Track free protein usage
            elif protein_lower in self.FREE_PROTEINS:
                free_proteins_used += quantity
                
                breakdown.append(ProteinBreakdown(
                    protein_name=self.FREE_PROTEINS[protein_lower],
                    quantity=quantity,
                    is_free=True,
                    is_upgrade=False,
                    upgrade_price=Decimal("0.00"),
                    is_third_protein=False
                ))
                
                logger.info(f"Free protein: {self.FREE_PROTEINS[protein_lower]} × {quantity} (FREE)")
        
        # Second pass: Check if we have 3rd proteins
        if total_proteins > free_protein_allowance:
            extra_proteins = total_proteins - free_protein_allowance
            third_protein_cost = self.THIRD_PROTEIN_PRICE * extra_proteins
            
            logger.info(f"Extra proteins detected: {extra_proteins} × ${self.THIRD_PROTEIN_PRICE} = ${third_protein_cost}")
            
            # Update breakdown to mark 3rd proteins
            # Note: The last proteins in the order are considered "3rd proteins"
            proteins_marked = 0
            for item in reversed(breakdown):
                if proteins_marked >= extra_proteins:
                    break
                
                proteins_to_mark = min(item.quantity, extra_proteins - proteins_marked)
                item.is_third_protein = True
                proteins_marked += proteins_to_mark
        
        # Calculate total
        total_protein_cost = upgrade_cost + third_protein_cost
        
        # Generate explanation
        explanation = self._generate_explanation(
            guest_count,
            total_proteins,
            free_protein_allowance,
            upgrade_cost,
            third_protein_cost,
            breakdown
        )
        
        # Generate customer-friendly summary
        proteins_summary = self._generate_summary(breakdown)
        
        return {
            "upgrade_cost": float(upgrade_cost),
            "third_protein_cost": float(third_protein_cost),
            "total_protein_cost": float(total_protein_cost),
            "total_proteins": total_proteins,
            "free_protein_allowance": free_protein_allowance,
            "breakdown": [
                {
                    "protein_name": item.protein_name,
                    "quantity": item.quantity,
                    "is_free": item.is_free,
                    "is_upgrade": item.is_upgrade,
                    "upgrade_price": float(item.upgrade_price),
                    "is_third_protein": item.is_third_protein
                }
                for item in breakdown
            ],
            "explanation": explanation,
            "proteins_summary": proteins_summary
        }
    
    def _generate_explanation(
        self,
        guest_count: int,
        total_proteins: int,
        free_allowance: int,
        upgrade_cost: Decimal,
        third_protein_cost: Decimal,
        breakdown: List[ProteinBreakdown]
    ) -> str:
        """Generate detailed explanation of protein costs"""
        
        lines = [
            f"🍖 **Protein Breakdown for {guest_count} Guests:**",
            f"",
            f"📊 **Protein Allowance:**",
            f"   • Each guest gets 2 FREE protein choices",
            f"   • Your group: {guest_count} guests × 2 = {free_allowance} FREE proteins",
            f"   • Total proteins selected: {total_proteins}",
            f""
        ]
        
        # Show breakdown by protein type
        if breakdown:
            lines.append("🥩 **Your Protein Selections:**")
            
            for item in breakdown:
                if item.is_free:
                    lines.append(f"   • {item.protein_name}: {item.quantity} portions (FREE base protein)")
                elif item.is_upgrade:
                    cost = item.upgrade_price * item.quantity
                    lines.append(
                        f"   • {item.protein_name}: {item.quantity} portions "
                        f"(Premium upgrade: +${item.upgrade_price} each = ${cost})"
                    )
            lines.append("")
        
        # Show 3rd protein charge if applicable
        if third_protein_cost > 0:
            extra_count = total_proteins - free_allowance
            lines.append(f"🔢 **3rd Protein Charges:**")
            lines.append(
                f"   • {extra_count} extra protein(s) beyond your {free_allowance} free allowance"
            )
            lines.append(f"   • 3rd protein fee: {extra_count} × ${self.THIRD_PROTEIN_PRICE} = ${third_protein_cost}")
            lines.append("")
        
        # Show totals
        lines.append("💰 **Protein Cost Summary:**")
        if upgrade_cost > 0:
            lines.append(f"   • Premium upgrades: ${upgrade_cost}")
        if third_protein_cost > 0:
            lines.append(f"   • 3rd protein charges: ${third_protein_cost}")
        
        total = upgrade_cost + third_protein_cost
        if total > 0:
            lines.append(f"   • **Total protein extras: ${total}**")
        else:
            lines.append(f"   • **No additional protein charges** ✅")
        
        return "\n".join(lines)
    
    def _generate_summary(self, breakdown: List[ProteinBreakdown]) -> str:
        """Generate short customer-friendly summary"""
        
        lines = []
        
        for item in breakdown:
            if item.quantity > 0:
                if item.is_upgrade:
                    lines.append(
                        f"{item.quantity}× {item.protein_name} "
                        f"(+${item.upgrade_price} each)"
                    )
                else:
                    lines.append(f"{item.quantity}× {item.protein_name}")
        
        return " | ".join(lines) if lines else "No proteins selected"
    
    def validate_protein_selection(
        self,
        guest_count: int,
        protein_selections: Dict[str, int]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate protein selections
        
        Args:
            guest_count: Total number of guests
            protein_selections: Dict mapping protein names to quantities
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        
        # Check if any proteins are selected
        total_proteins = sum(protein_selections.values())
        if total_proteins == 0:
            return False, "No proteins selected. Each guest needs to choose at least 1 protein."
        
        # Check if minimum protein count is met (at least 1 per guest)
        min_proteins = guest_count
        if total_proteins < min_proteins:
            return (
                False,
                f"Not enough proteins selected. You have {guest_count} guests but only "
                f"{total_proteins} protein(s). Each guest needs at least 1 protein choice."
            )
        
        # Check if protein names are valid
        for protein_key in protein_selections.keys():
            protein_lower = protein_key.lower().replace(" ", "_")
            if protein_lower not in {**self.FREE_PROTEINS, **self.PREMIUM_UPGRADES}:
                return False, f"Invalid protein: '{protein_key}'. Please check the spelling."
        
        return True, None
    
    def get_available_proteins(self) -> Dict:
        """
        Get list of all available proteins with pricing
        
        Returns:
            Dict with free_proteins and premium_upgrades
        """
        
        return {
            "free_proteins": [
                {"key": key, "name": name, "price": 0}
                for key, name in self.FREE_PROTEINS.items()
            ],
            "premium_upgrades": [
                {
                    "key": key,
                    "name": info["name"],
                    "price": float(info["price"])
                }
                for key, info in self.PREMIUM_UPGRADES.items()
            ],
            "third_protein_price": float(self.THIRD_PROTEIN_PRICE),
            "protein_allowance_per_guest": 2
        }


# Singleton instance
_protein_calculator_service = None


def get_protein_calculator_service() -> ProteinCalculatorService:
    """Get or create singleton instance of ProteinCalculatorService"""
    global _protein_calculator_service
    if _protein_calculator_service is None:
        _protein_calculator_service = ProteinCalculatorService()
    return _protein_calculator_service
