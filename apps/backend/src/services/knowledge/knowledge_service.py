"""
Knowledge Service - Main Orchestrator

Provides unified interface to all knowledge modules.
AI agents interact with this service to access business knowledge.

Architecture:
- Delegates to specialized service modules
- Each module handles a specific domain
- Clean separation of concerns
- Easy to test and maintain

Modules:
- BusinessRulesService: Policies, terms, rules
- FAQService: FAQ search and retrieval
- MenuService: Menu items and pricing
- UpsellService: Upsell suggestions
- AvailabilityService: Calendar and capacity
- TrainingDataService: AI training examples
- KnowledgeFormatters: Context formatters

Created: 2025-11-12
"""
import logging
from datetime import date, time
from typing import Dict, List, Optional, Any
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from .business_rules import BusinessRulesService
from .faq_service import FAQService
from .menu_service import MenuService
from .upsell_service import UpsellService
from .availability import AvailabilityService
from .training_data import TrainingDataService
from .formatters import KnowledgeFormatters

from models.knowledge_base import (
    RuleCategory,
    ToneType,
    MenuCategory,
    PricingTierLevel,
)

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    Main knowledge service orchestrator
    
    Provides AI agents with dynamic access to business knowledge.
    All methods are database-backed for real-time updates.
    """
    
    def __init__(self, db: AsyncSession, station_id: Optional[str] = None):
        """
        Initialize knowledge service with all modules
        
        Args:
            db: Database session
            station_id: Optional station ID for multi-location support
        """
        self.db = db
        self.station_id = station_id
        
        # Initialize all service modules
        self.business_rules = BusinessRulesService(db, station_id)
        self.faq = FAQService(db, station_id)
        self.menu = MenuService(db, station_id)
        self.upsell = UpsellService(db, station_id)
        self.availability = AvailabilityService(db, station_id)
        self.training = TrainingDataService(db)
        self.formatters = KnowledgeFormatters()
    
    # ============================================
    # BUSINESS RULES & POLICIES
    # ============================================
    
    async def get_business_charter(self) -> Dict[str, Any]:
        """Get comprehensive business charter for AI context"""
        return await self.business_rules.get_business_charter()
    
    async def get_rule_by_category(self, category: RuleCategory) -> List[Dict[str, Any]]:
        """Get all rules for a specific category"""
        return await self.business_rules.get_rule_by_category(category)
    
    async def search_rules(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search business rules by keywords"""
        return await self.business_rules.search_rules(keywords)
    
    # ============================================
    # FAQ SYSTEM
    # ============================================
    
    async def get_faq_answer(
        self, 
        question: str, 
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Search FAQ for an answer"""
        return await self.faq.get_faq_answer(question, category)
    
    async def get_faqs_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all FAQs for a category"""
        return await self.faq.get_faqs_by_category(category)
    
    async def get_top_faqs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular FAQs"""
        return await self.faq.get_top_faqs(limit)
    
    async def get_all_faq_categories(self) -> List[str]:
        """Get all unique FAQ categories"""
        return await self.faq.get_all_categories()
    
    # ============================================
    # MENU & PRICING
    # ============================================
    
    async def get_menu_by_category(
        self, 
        category: Optional[MenuCategory] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get menu items organized by category"""
        return await self.menu.get_menu_by_category(category)
    
    async def get_proteins(self, premium_only: bool = False) -> List[Dict[str, Any]]:
        """Get available protein options"""
        return await self.menu.get_proteins(premium_only)
    
    async def get_pricing_tiers(
        self, 
        guest_count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get available pricing tiers/packages"""
        return await self.menu.get_pricing_tiers(guest_count)
    
    async def calculate_total_price(
        self,
        guest_count: int,
        tier_level: PricingTierLevel,
        add_ons: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calculate total price for a booking"""
        return await self.menu.calculate_total_price(guest_count, tier_level, add_ons)
    
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
        """Get contextual upsell suggestions"""
        return await self.upsell.get_upsell_suggestions(
            guest_count, event_type, event_date, location, budget
        )
    
    # ============================================
    # AVAILABILITY CALENDAR
    # ============================================
    
    async def check_availability(
        self,
        event_date: date,
        time_slot: Optional[time] = None,
        guest_count: int = 1
    ) -> Dict[str, Any]:
        """Check availability for a date/time"""
        return await self.availability.check_availability(event_date, time_slot, guest_count)
    
    async def get_next_available_dates(
        self, 
        days_ahead: int = 30, 
        limit: int = 10
    ) -> List[date]:
        """Get next available dates"""
        return await self.availability.get_next_available_dates(days_ahead, limit)
    
    # ============================================
    # TRAINING DATA
    # ============================================
    
    async def get_training_examples(
        self,
        tone: Optional[ToneType] = None,
        example_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get training examples for AI learning"""
        return await self.training.get_training_examples(tone, example_type, limit)
    
    async def get_examples_by_scenario(self, scenario: str) -> List[Dict[str, Any]]:
        """Get training examples for a specific scenario"""
        return await self.training.get_examples_by_scenario(scenario)
    
    # ============================================
    # AI CONTEXT FORMATTERS
    # ============================================
    
    async def get_menu_summary_for_ai(self) -> str:
        """Get formatted menu summary for AI context"""
        menu = await self.get_menu_by_category()
        tiers = await self.get_pricing_tiers()
        return self.formatters.format_menu_summary(menu, tiers)
    
    async def get_business_charter_for_ai(self) -> str:
        """Get formatted business charter for AI context"""
        charter = await self.get_business_charter()
        return self.formatters.format_business_charter(charter)
    
    async def get_faqs_for_ai(self, limit: int = 20) -> str:
        """Get formatted FAQs for AI context"""
        faqs = await self.get_top_faqs(limit)
        return self.formatters.format_faqs(faqs, limit)
    
    async def get_upsell_context(
        self,
        guest_count: Optional[int] = None,
        event_type: Optional[str] = None,
        event_date: Optional[date] = None,
        location: Optional[str] = None,
        budget: Optional[Decimal] = None
    ) -> str:
        """Get formatted upsell suggestions for AI context"""
        suggestions = await self.get_upsell_suggestions(
            guest_count, event_type, event_date, location, budget
        )
        return self.formatters.format_upsell_suggestions(suggestions)
    
    # ============================================
    # COMPREHENSIVE AI CONTEXT
    # ============================================
    
    async def get_full_ai_context(
        self,
        include_menu: bool = True,
        include_charter: bool = True,
        include_faqs: bool = True,
        guest_count: Optional[int] = None,
        event_type: Optional[str] = None
    ) -> str:
        """
        Get comprehensive AI context including all relevant knowledge
        
        Args:
            include_menu: Include menu and pricing
            include_charter: Include business rules
            include_faqs: Include top FAQs
            guest_count: For contextual upselling
            event_type: For contextual upselling
            
        Returns:
            Complete formatted context for AI
        """
        context_parts = []
        
        if include_menu:
            menu_context = await self.get_menu_summary_for_ai()
            context_parts.append(menu_context)
        
        if include_charter:
            charter_context = await self.get_business_charter_for_ai()
            context_parts.append(charter_context)
        
        if include_faqs:
            faq_context = await self.get_faqs_for_ai(limit=15)
            context_parts.append(faq_context)
        
        if guest_count or event_type:
            upsell_context = await self.get_upsell_context(
                guest_count=guest_count,
                event_type=event_type
            )
            if upsell_context:
                context_parts.append(upsell_context)
        
        return "\n\n---\n\n".join(context_parts)
