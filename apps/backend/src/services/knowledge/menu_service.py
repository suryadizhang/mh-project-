"""
Menu Service Module

Handles menu items, pricing tiers, and price calculations.
Provides AI agents with dynamic menu and pricing information.

Created: 2025-11-12
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

# MIGRATED: from models.knowledge_base → db.models.knowledge_base
from db.models.knowledge_base import MenuItem, PricingTier, MenuCategory, PricingTierLevel

logger = logging.getLogger(__name__)


class MenuService:
    """Service for menu and pricing management"""

    def __init__(self, db: AsyncSession, station_id: Optional[str] = None):
        self.db = db
        self.station_id = station_id

    async def get_menu_by_category(
        self, category: Optional[MenuCategory] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get menu items organized by category

        Args:
            category: Optional category filter

        Returns:
            Dictionary of categories with their items
        """
        try:
            conditions = [MenuItem.is_available == True]

            if category:
                conditions.append(MenuItem.category == category)

            if self.station_id:
                conditions.append(
                    or_(MenuItem.station_id == self.station_id, MenuItem.station_id == None)
                )

            stmt = (
                select(MenuItem)
                .where(and_(*conditions))
                .order_by(
                    MenuItem.category,
                    MenuItem.is_premium.desc(),
                    MenuItem.display_order,
                    MenuItem.name,
                )
            )

            result = await self.db.execute(stmt)
            items = result.scalars().all()

            # Organize by category
            menu = {}
            for item in items:
                cat = item.category.value if hasattr(item.category, "value") else item.category
                if cat not in menu:
                    menu[cat] = []
                menu[cat].append(item.to_dict())

            return menu

        except Exception as e:
            logger.error(f"Error fetching menu: {e}")
            return {}

    async def get_proteins(self, premium_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get available protein options

        Args:
            premium_only: Only return premium proteins

        Returns:
            List of protein items
        """
        try:
            conditions = [
                MenuItem.is_available == True,
                MenuItem.category.in_(
                    [MenuCategory.POULTRY, MenuCategory.BEEF, MenuCategory.SEAFOOD]
                ),
            ]

            if premium_only:
                conditions.append(MenuItem.is_premium == True)

            if self.station_id:
                conditions.append(
                    or_(MenuItem.station_id == self.station_id, MenuItem.station_id == None)
                )

            stmt = (
                select(MenuItem)
                .where(and_(*conditions))
                .order_by(MenuItem.is_premium.desc(), MenuItem.display_order, MenuItem.name)
            )

            result = await self.db.execute(stmt)
            proteins = result.scalars().all()

            return [p.to_dict() for p in proteins]

        except Exception as e:
            logger.error(f"Error fetching proteins: {e}")
            return []

    async def get_pricing_tiers(self, guest_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get available pricing tiers/packages

        Args:
            guest_count: Optional guest count to filter by min_guests

        Returns:
            List of pricing tiers
        """
        try:
            conditions = [PricingTier.is_active == True]

            if guest_count:
                conditions.append(PricingTier.min_guests <= guest_count)

            if self.station_id:
                conditions.append(
                    or_(PricingTier.station_id == self.station_id, PricingTier.station_id == None)
                )

            stmt = (
                select(PricingTier)
                .where(and_(*conditions))
                .order_by(PricingTier.display_order, PricingTier.price_per_person)
            )

            result = await self.db.execute(stmt)
            tiers = result.scalars().all()

            return [tier.to_dict() for tier in tiers]

        except Exception as e:
            logger.error(f"Error fetching pricing tiers: {e}")
            return []

    async def calculate_total_price(
        self, guest_count: int, tier_level: PricingTierLevel, add_ons: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Calculate total price for a booking

        Args:
            guest_count: Number of guests
            tier_level: Selected pricing tier
            add_ons: Optional list of add-on service names

        Returns:
            Price breakdown
        """
        try:
            # Get pricing tier
            stmt = select(PricingTier).where(
                and_(PricingTier.tier_level == tier_level, PricingTier.is_active == True)
            )

            result = await self.db.execute(stmt)
            tier = result.scalar_one_or_none()

            if not tier:
                return {"error": "Pricing tier not found", "total": 0}

            # Calculate base price
            base_price = tier.price_per_person * guest_count

            # TODO: Add travel fee calculation (would need service area rules)
            travel_fee = Decimal("0.00")

            # TODO: Add add-ons pricing (would need additional services table)
            add_ons_price = Decimal("0.00")

            total = base_price + travel_fee + add_ons_price

            return {
                "tier_name": tier.name,
                "price_per_person": str(tier.price_per_person),
                "guest_count": guest_count,
                "base_price": str(base_price),
                "travel_fee": str(travel_fee),
                "add_ons_price": str(add_ons_price),
                "total": str(total),
                "breakdown": {
                    "base": f"${base_price} ({guest_count} guests × ${tier.price_per_person})",
                    "travel": f"${travel_fee}",
                    "add_ons": f"${add_ons_price}",
                },
            }

        except Exception as e:
            logger.error(f"Error calculating price: {e}")
            return {"error": str(e), "total": 0}
