"""
Knowledge Base Service

Provides AI agents with dynamic access to:
- Business rules and policies
- FAQs
- Upsell suggestions
- Seasonal offers
- Availability calendar

This replaces static prompts with database-driven knowledge.

Created: 2025-11-12
"""
import logging
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.knowledge_base import (
    BusinessRule,
    FAQItem,
    TrainingData,
    UpsellRule,
    SeasonalOffer,
    AvailabilityCalendar,
    MenuItem,
    PricingTier,
    RuleCategory,
    ToneType,
    UpsellTriggerType,
    OfferStatus,
    MenuCategory,
    PricingTierLevel,
)

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Service for retrieving business knowledge for AI agents
    
    All methods are database-backed, allowing real-time updates
    without code deployment.
    """
    
    def __init__(self, db: AsyncSession, station_id: Optional[str] = None):
        """
        Initialize knowledge service
        
        Args:
            db: Database session
            station_id: Optional station ID for multi-location support
        """
        self.db = db
        self.station_id = station_id
    
    # ============================================
    # BUSINESS RULES & POLICIES
    # ============================================
    
    async def get_business_charter(self) -> Dict[str, Any]:
        """
        Get comprehensive business charter for AI context
        
        Returns:
            Dictionary with all active business rules organized by category
        """
        try:
            # Query all active rules
            stmt = select(BusinessRule).where(
                and_(
                    BusinessRule.is_active == True,
                    or_(
                        BusinessRule.station_id == self.station_id,
                        BusinessRule.station_id == None
                    ),
                    or_(
                        BusinessRule.effective_from == None,
                        BusinessRule.effective_from <= datetime.now()
                    ),
                    or_(
                        BusinessRule.effective_until == None,
                        BusinessRule.effective_until >= datetime.now()
                    )
                )
            ).order_by(BusinessRule.category, BusinessRule.priority.desc())
            
            result = await self.db.execute(stmt)
            rules = result.scalars().all()
            
            # Organize by category
            charter = {}
            for rule in rules:
                category = rule.category.value if hasattr(rule.category, 'value') else rule.category
                if category not in charter:
                    charter[category] = []
                
                charter[category].append({
                    "name": rule.rule_name,
                    "content": rule.rule_content,
                    "summary": rule.rule_summary,
                    "keywords": rule.keywords or [],
                    "priority": rule.priority
                })
            
            return charter
        
        except Exception as e:
            logger.error(f"Error fetching business charter: {e}")
            return {}
    
    async def get_rule_by_category(self, category: RuleCategory) -> List[Dict[str, Any]]:
        """
        Get all rules for a specific category
        
        Args:
            category: Rule category enum
            
        Returns:
            List of rules
        """
        try:
            stmt = select(BusinessRule).where(
                and_(
                    BusinessRule.category == category,
                    BusinessRule.is_active == True,
                    or_(
                        BusinessRule.station_id == self.station_id,
                        BusinessRule.station_id == None
                    )
                )
            ).order_by(BusinessRule.priority.desc())
            
            result = await self.db.execute(stmt)
            rules = result.scalars().all()
            
            return [rule.to_dict() for rule in rules]
        
        except Exception as e:
            logger.error(f"Error fetching rules for category {category}: {e}")
            return []
    
    async def search_rules(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Search business rules by keywords
        
        Args:
            keywords: List of keywords to search
            
        Returns:
            Matching rules
        """
        try:
            # PostgreSQL array overlap operator
            stmt = select(BusinessRule).where(
                and_(
                    BusinessRule.keywords.overlap(keywords),
                    BusinessRule.is_active == True
                )
            ).order_by(BusinessRule.priority.desc())
            
            result = await self.db.execute(stmt)
            rules = result.scalars().all()
            
            return [rule.to_dict() for rule in rules]
        
        except Exception as e:
            logger.error(f"Error searching rules: {e}")
            return []
    
    # ============================================
    # FAQ SYSTEM
    # ============================================
    
    async def get_faq_answer(self, question: str, category: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search FAQ for an answer
        
        Uses keyword matching (good enough for 50 FAQs)
        
        Args:
            question: User's question
            category: Optional category filter
            
        Returns:
            Best matching FAQ item or None
        """
        try:
            # Build query
            conditions = [FAQItem.is_active == True]
            
            if category:
                conditions.append(FAQItem.category == category)
            
            if self.station_id:
                conditions.append(
                    or_(
                        FAQItem.station_id == self.station_id,
                        FAQItem.station_id == None
                    )
                )
            
            stmt = select(FAQItem).where(and_(*conditions)).order_by(
                FAQItem.priority.desc(),
                FAQItem.view_count.desc()
            )
            
            result = await self.db.execute(stmt)
            faqs = result.scalars().all()
            
            if not faqs:
                return None
            
            # Simple keyword matching
            question_lower = question.lower()
            best_match = None
            best_score = 0
            
            for faq in faqs:
                score = 0
                
                # Check question match
                if question_lower in faq.question.lower():
                    score += 10
                
                # Check keywords
                if faq.keywords:
                    for keyword in faq.keywords:
                        if keyword.lower() in question_lower:
                            score += 5
                
                # Check tags
                if faq.tags:
                    for tag in faq.tags:
                        if tag.lower() in question_lower:
                            score += 3
                
                if score > best_score:
                    best_score = score
                    best_match = faq
            
            if best_match and best_score >= 3:  # Minimum threshold
                # Increment view count
                best_match.view_count = (best_match.view_count or 0) + 1
                await self.db.commit()
                
                return best_match.to_dict()
            
            return None
        
        except Exception as e:
            logger.error(f"Error searching FAQ: {e}")
            return None
    
    async def get_faqs_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get all FAQs for a category
        
        Args:
            category: FAQ category
            
        Returns:
            List of FAQ items
        """
        try:
            stmt = select(FAQItem).where(
                and_(
                    FAQItem.category == category,
                    FAQItem.is_active == True
                )
            ).order_by(FAQItem.priority.desc())
            
            result = await self.db.execute(stmt)
            faqs = result.scalars().all()
            
            return [faq.to_dict() for faq in faqs]
        
        except Exception as e:
            logger.error(f"Error fetching FAQs for category {category}: {e}")
            return []
    
    async def get_top_faqs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular FAQs
        
        Args:
            limit: Number of FAQs to return
            
        Returns:
            List of top FAQs
        """
        try:
            stmt = select(FAQItem).where(
                FAQItem.is_active == True
            ).order_by(
                FAQItem.view_count.desc(),
                FAQItem.helpful_count.desc()
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            faqs = result.scalars().all()
            
            return [faq.to_dict() for faq in faqs]
        
        except Exception as e:
            logger.error(f"Error fetching top FAQs: {e}")
            return []
    
    # ============================================
    # UPSELL SYSTEM
    # ============================================
    
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
    
    # ============================================
    # SEASONAL OFFERS
    # ============================================
    
    async def get_active_offers(self, event_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Get currently active seasonal offers
        
        Args:
            event_date: Optional date to check offers for
            
        Returns:
            List of active offers
        """
        try:
            now = datetime.now()
            check_date = event_date or now.date()
            
            stmt = select(SeasonalOffer).where(
                and_(
                    SeasonalOffer.status == OfferStatus.ACTIVE,
                    SeasonalOffer.valid_from <= now,
                    SeasonalOffer.valid_until >= now,
                    or_(
                        SeasonalOffer.station_id == self.station_id,
                        SeasonalOffer.station_id == None
                    )
                )
            ).order_by(SeasonalOffer.discount_percentage.desc())
            
            result = await self.db.execute(stmt)
            offers = result.scalars().all()
            
            # Filter by conditions if provided
            valid_offers = []
            for offer in offers:
                if not offer.conditions:
                    valid_offers.append(offer.to_dict())
                    continue
                
                # Check conditions (simplified)
                conditions = offer.conditions
                valid = True
                
                # Check day of week
                if "days" in conditions:
                    day_name = check_date.strftime("%A").lower()
                    if day_name not in [d.lower() for d in conditions["days"]]:
                        valid = False
                
                # Check minimum guests
                if "min_guests" in conditions:
                    # This will be checked at booking time
                    pass
                
                if valid:
                    valid_offers.append(offer.to_dict())
            
            return valid_offers
        
        except Exception as e:
            logger.error(f"Error fetching active offers: {e}")
            return []
    
    # ============================================
    # AVAILABILITY CALENDAR
    # ============================================
    
    async def check_availability(
        self,
        event_date: date,
        time_slot: Optional[time] = None,
        guest_count: int = 1
    ) -> Dict[str, Any]:
        """
        Check availability for a date/time
        
        Args:
            event_date: Requested date
            time_slot: Optional time slot
            guest_count: Number of guests
            
        Returns:
            Availability information
        """
        try:
            conditions = [
                AvailabilityCalendar.date == event_date,
                or_(
                    AvailabilityCalendar.station_id == self.station_id,
                    AvailabilityCalendar.station_id == None
                )
            ]
            
            if time_slot:
                conditions.append(AvailabilityCalendar.time_slot == time_slot)
            
            stmt = select(AvailabilityCalendar).where(and_(*conditions))
            
            result = await self.db.execute(stmt)
            slots = result.scalars().all()
            
            if not slots:
                # No calendar entry = available (default behavior)
                return {
                    "available": True,
                    "capacity": 50,  # Default capacity
                    "message": "Available"
                }
            
            # Check each slot
            available_slots = []
            for slot in slots:
                if not slot.is_available:
                    continue
                
                available_capacity = slot.max_capacity - slot.booked_capacity
                if available_capacity >= guest_count:
                    available_slots.append({
                        "time": slot.time_slot.isoformat() if slot.time_slot else None,
                        "capacity": available_capacity,
                        "max_capacity": slot.max_capacity
                    })
            
            if available_slots:
                return {
                    "available": True,
                    "slots": available_slots,
                    "message": f"Available - {len(available_slots)} time slot(s)"
                }
            else:
                return {
                    "available": False,
                    "message": "Fully booked for this date"
                }
        
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return {
                "available": True,  # Fail open
                "message": "Unable to check availability"
            }
    
    async def get_next_available_dates(self, days_ahead: int = 30, limit: int = 10) -> List[date]:
        """
        Get next available dates
        
        Args:
            days_ahead: How many days to look ahead
            limit: Maximum number of dates to return
            
        Returns:
            List of available dates
        """
        try:
            start_date = date.today()
            end_date = start_date + timedelta(days=days_ahead)
            
            stmt = select(AvailabilityCalendar).where(
                and_(
                    AvailabilityCalendar.date >= start_date,
                    AvailabilityCalendar.date <= end_date,
                    AvailabilityCalendar.is_available == True,
                    AvailabilityCalendar.booked_capacity < AvailabilityCalendar.max_capacity
                )
            ).order_by(AvailabilityCalendar.date).limit(limit)
            
            result = await self.db.execute(stmt)
            slots = result.scalars().all()
            
            # Get unique dates
            available_dates = list(set(slot.date for slot in slots))
            available_dates.sort()
            
            return available_dates[:limit]
        
        except Exception as e:
            logger.error(f"Error fetching next available dates: {e}")
            return []
    
    # ============================================
    # TRAINING DATA
    # ============================================
    
    async def get_training_examples(
        self,
        tone: Optional[ToneType] = None,
        example_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get training examples for AI learning
        
        Args:
            tone: Filter by tone
            example_type: Filter by example type
            limit: Number of examples
            
        Returns:
            List of training examples
        """
        try:
            conditions = [TrainingData.is_active == True]
            
            if tone:
                conditions.append(TrainingData.tone == tone)
            
            if example_type:
                conditions.append(TrainingData.example_type == example_type)
            
            stmt = select(TrainingData).where(and_(*conditions)).order_by(
                TrainingData.quality_score.desc(),
                TrainingData.used_count.asc()
            ).limit(limit)
            
            result = await self.db.execute(stmt)
            examples = result.scalars().all()
            
            # Increment used_count
            for example in examples:
                example.used_count = (example.used_count or 0) + 1
            await self.db.commit()
            
            return [example.to_dict() for example in examples]
        
        except Exception as e:
            logger.error(f"Error fetching training examples: {e}")
            return []
    
    # ============================================
    # MENU & PRICING
    # ============================================
    
    async def get_menu_by_category(self, category: Optional[MenuCategory] = None) -> Dict[str, List[Dict[str, Any]]]:
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
                    or_(
                        MenuItem.station_id == self.station_id,
                        MenuItem.station_id == None
                    )
                )
            
            stmt = select(MenuItem).where(and_(*conditions)).order_by(
                MenuItem.category,
                MenuItem.is_premium.desc(),
                MenuItem.display_order,
                MenuItem.name
            )
            
            result = await self.db.execute(stmt)
            items = result.scalars().all()
            
            # Organize by category
            menu = {}
            for item in items:
                cat = item.category.value if hasattr(item.category, 'value') else item.category
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
                MenuItem.category.in_([MenuCategory.POULTRY, MenuCategory.BEEF, MenuCategory.SEAFOOD])
            ]
            
            if premium_only:
                conditions.append(MenuItem.is_premium == True)
            
            if self.station_id:
                conditions.append(
                    or_(
                        MenuItem.station_id == self.station_id,
                        MenuItem.station_id == None
                    )
                )
            
            stmt = select(MenuItem).where(and_(*conditions)).order_by(
                MenuItem.is_premium.desc(),
                MenuItem.display_order,
                MenuItem.name
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
                    or_(
                        PricingTier.station_id == self.station_id,
                        PricingTier.station_id == None
                    )
                )
            
            stmt = select(PricingTier).where(and_(*conditions)).order_by(
                PricingTier.display_order,
                PricingTier.price_per_person
            )
            
            result = await self.db.execute(stmt)
            tiers = result.scalars().all()
            
            return [tier.to_dict() for tier in tiers]
        
        except Exception as e:
            logger.error(f"Error fetching pricing tiers: {e}")
            return []
    
    async def calculate_total_price(
        self,
        guest_count: int,
        tier_level: PricingTierLevel,
        add_ons: Optional[List[str]] = None
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
                and_(
                    PricingTier.tier_level == tier_level,
                    PricingTier.is_active == True
                )
            )
            
            result = await self.db.execute(stmt)
            tier = result.scalar_one_or_none()
            
            if not tier:
                return {
                    "error": "Pricing tier not found",
                    "total": 0
                }
            
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
                    "add_ons": f"${add_ons_price}"
                }
            }
        
        except Exception as e:
            logger.error(f"Error calculating price: {e}")
            return {
                "error": str(e),
                "total": 0
            }
    
    async def get_menu_summary_for_ai(self) -> str:
        """
        Get formatted menu summary for AI context
        
        Returns:
            Markdown-formatted menu summary
        """
        try:
            menu = await self.get_menu_by_category()
            tiers = await self.get_pricing_tiers()
            
            summary = "# MENU & PRICING\n\n"
            
            # Pricing tiers
            summary += "## Pricing Packages\n\n"
            for tier in tiers:
                popular = " ⭐ MOST POPULAR" if tier.get("is_popular") else ""
                summary += f"### {tier['name']}{popular}\n"
                summary += f"- **${tier['price_per_person']}/person** (min {tier['min_guests']} guests)\n"
                summary += f"- {tier['description']}\n"
                if tier.get('features'):
                    summary += "- Includes:\n"
                    for feature in tier['features']:
                        summary += f"  - {feature}\n"
                summary += "\n"
            
            # Menu items by category
            summary += "## Menu Options\n\n"
            
            category_names = {
                "poultry": "🍗 Poultry",
                "beef": "🥩 Beef",
                "seafood": "🦐 Seafood",
                "specialty": "🌱 Specialty",
                "sides": "🍚 Sides",
                "appetizers": "🥢 Appetizers",
                "desserts": "🍰 Desserts"
            }
            
            for category, items in menu.items():
                summary += f"### {category_names.get(category, category.title())}\n\n"
                for item in items:
                    premium = " 💎" if item.get("is_premium") else ""
                    price = f" (${item['base_price']})" if item.get("base_price") else ""
                    summary += f"- **{item['name']}**{premium}{price}"
                    if item.get("description"):
                        summary += f" - {item['description']}"
                    if item.get("dietary_info"):
                        summary += f" [{', '.join(item['dietary_info'])}]"
                    summary += "\n"
                summary += "\n"
            
            return summary
        
        except Exception as e:
            logger.error(f"Error generating menu summary: {e}")
            return "# MENU & PRICING\n\n(Unable to load menu data)"
