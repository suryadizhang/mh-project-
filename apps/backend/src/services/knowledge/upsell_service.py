"""
Upsell Service Module

Handles upsell suggestions based on contextual triggers.
Provides AI agents with dynamic upselling recommendations.

Created: 2025-11-12
"""
import logging
from datetime import date
from typing import Dict, List, Optional, Any
from decimal import Decimal

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge_base import UpsellRule, UpsellTriggerType

logger = logging.getLogger(__name__)


class UpsellService:
    """Service for managing upsell suggestions"""
    
    def __init__(self, db: AsyncSession, station_id: Optional[str] = None):
        self.db = db
        self.station_id = station_id
    
    async def get_upsell_suggestions(
        self,
        guest_count: Optional[int] = None,
        event_type: Optional[str] = None,
        event_date: Optional[date] = None,
        location: Optional[str] = None,
        budget: Optional[Decimal] = None
    ) -> List[Dict[str, Any]]:
        """
        Get contextual upsell suggestions
        
        Args:
            guest_count: Number of guests
            event_type: Type of event (birthday, corporate, etc.)
            event_date: Date of event
            location: Event location
            budget: Customer's budget
            
        Returns:
            List of relevant upsell suggestions
        """
        try:
            stmt = select(UpsellRule).where(
                and_(
                    UpsellRule.is_active == True,
                    or_(
                        UpsellRule.station_id == self.station_id,
                        UpsellRule.station_id == None
                    )
                )
            ).order_by(UpsellRule.priority.desc())
            
            result = await self.db.execute(stmt)
            rules = result.scalars().all()
            
            # Filter by conditions
            suggestions = []
            for rule in rules:
                condition = rule.trigger_condition
                matches = False
                
                if rule.trigger_type == UpsellTriggerType.GUEST_COUNT and guest_count:
                    min_guests = condition.get("min", 0)
                    max_guests = condition.get("max", 999999)
                    if min_guests <= guest_count <= max_guests:
                        matches = True
                
                elif rule.trigger_type == UpsellTriggerType.EVENT_TYPE and event_type:
                    if event_type.lower() in [et.lower() for et in condition.get("types", [])]:
                        matches = True
                
                elif rule.trigger_type == UpsellTriggerType.DATE and event_date:
                    # Check if date falls in specified range or season
                    # Implementation depends on condition structure
                    matches = True  # Simplified for now
                
                elif rule.trigger_type == UpsellTriggerType.LOCATION and location:
                    if location.lower() in [loc.lower() for loc in condition.get("locations", [])]:
                        matches = True
                
                elif rule.trigger_type == UpsellTriggerType.BUDGET and budget:
                    min_budget = Decimal(str(condition.get("min", 0)))
                    max_budget = Decimal(str(condition.get("max", 999999)))
                    if min_budget <= budget <= max_budget:
                        matches = True
                
                if matches:
                    suggestions.append({
                        "item": rule.upsell_item,
                        "description": rule.upsell_description,
                        "price": str(rule.upsell_price) if rule.upsell_price else None,
                        "success_rate": str(rule.success_rate) if rule.success_rate else None,
                        "priority": rule.priority
                    })
            
            return suggestions
        
        except Exception as e:
            logger.error(f"Error fetching upsell suggestions: {e}")
            return []
