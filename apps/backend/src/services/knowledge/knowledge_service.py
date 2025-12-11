"""
Knowledge Service - Main Orchestrator

Provides unified interface to all knowledge modules.
AI agents interact with this service to access business knowledge.

Architecture:
- Delegates to specialized service modules
- Each module handles a specific domain
- Clean separation of concerns
- Easy to test and maintain
- Redis caching for frequently-accessed data

Modules:
- BusinessRulesService: Policies, terms, rules
- FAQService: FAQ search and retrieval
- MenuService: Menu items and pricing
- UpsellService: Upsell suggestions
- AvailabilityService: Calendar and capacity
- TrainingDataService: AI training examples
- KnowledgeFormatters: Context formatters

Caching:
- Menu data: 30 minutes (rarely changes)
- FAQ data: 30 minutes (rarely changes)
- Business rules: 30 minutes (rarely changes)
- Pricing tiers: 30 minutes (rarely changes)
- Availability: 30 seconds (changes frequently)

Created: 2025-11-12
Updated: 2025-11-22 - Added Redis caching support
"""

import hashlib
import json
import logging
from datetime import date, time
from typing import TYPE_CHECKING, Dict, List, Optional, Any
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from .business_rules import BusinessRulesService
from .faq_service import FAQService
from .menu_service import MenuService
from .upsell_service import UpsellService
from .availability import AvailabilityService
from .training_data import TrainingDataService
from .formatters import KnowledgeFormatters

# MIGRATED: from models.knowledge_base → db.models.knowledge_base
from db.models.knowledge_base import (
    RuleCategory,
    ToneType,
    MenuCategory,
    PricingTierLevel,
)

if TYPE_CHECKING:
    from core.cache import CacheService

logger = logging.getLogger(__name__)

# Cache TTL settings (seconds)
CACHE_TTL_MENU = 1800  # 30 minutes
CACHE_TTL_FAQ = 1800  # 30 minutes
CACHE_TTL_RULES = 1800  # 30 minutes
CACHE_TTL_PRICING = 1800  # 30 minutes
CACHE_TTL_AVAILABILITY = 30  # 30 seconds (changes frequently)


class KnowledgeService:
    """
    Main knowledge service orchestrator

    Provides AI agents with dynamic access to business knowledge.
    All methods are database-backed for real-time updates.
    Supports optional Redis caching for performance.
    """

    def __init__(
        self,
        db: AsyncSession,
        station_id: Optional[str] = None,
        cache: Optional["CacheService"] = None,
    ):
        """
        Initialize knowledge service with all modules

        Args:
            db: Database session
            station_id: Optional station ID for multi-location support
            cache: Optional CacheService for Redis caching
        """
        self.db = db
        self.station_id = station_id
        self.cache = cache

        # Initialize all service modules
        self.business_rules = BusinessRulesService(db, station_id)
        self.faq = FAQService(db, station_id)
        self.menu = MenuService(db, station_id)
        self.upsell = UpsellService(db, station_id)
        self.availability = AvailabilityService(db, station_id)
        self.training = TrainingDataService(db)
        self.formatters = KnowledgeFormatters()

    # Keys that should NOT be included in cache key generation (may contain sensitive data)
    _SENSITIVE_CACHE_KEYS = frozenset([
        'user_id', 'customer_id', 'email', 'phone', 'name', 'address',
        'token', 'password', 'ssn', 'card', 'account', 'secret'
    ])

    def _make_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a sanitized cache key from method name and arguments.

        Security: Excludes sensitive identifiers from cache keys to prevent
        exposure in Redis key listings or logs. Uses SHA256 for key hashing.
        """
        # Filter out sensitive kwargs
        safe_kwargs = {
            k: str(v) for k, v in kwargs.items()
            if not any(sensitive in k.lower() for sensitive in self._SENSITIVE_CACHE_KEYS)
        }
        # Normalize args to prevent injection
        safe_args = [str(a)[:100] for a in args]  # Truncate long values

        key_data = {
            "args": safe_args,
            "kwargs": safe_kwargs,
        }
        # Use SHA256 instead of MD5 for security
        key_hash = hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()[:16]
        # Sanitize station_id to prevent injection
        station_part = ""
        if self.station_id:
            sanitized_station = ''.join(c for c in str(self.station_id) if c.isalnum() or c in '-_')
            station_part = f":{sanitized_station[:32]}"
        return f"knowledge:{prefix}{station_part}:{key_hash}"

    async def _get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache if available.

        Logs cache operations at debug level for audit trail.
        Does not log the actual key to prevent sensitive data exposure.
        """
        if not self.cache:
            return None
        try:
            result = await self.cache.get(key)
            # Structured audit log without exposing full key
            key_prefix = key.split(':')[1] if ':' in key else 'unknown'
            if result is not None:
                logger.debug("Cache read: hit", extra={
                    'action': 'cache_read',
                    'outcome': 'hit',
                    'key_prefix': key_prefix,
                    'station_id': self.station_id,
                })
            return result
        except Exception as e:
            logger.warning("Cache read failed", extra={
                'action': 'cache_read',
                'outcome': 'error',
                'error_type': type(e).__name__,
            })
            return None

    async def _set_cached(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache if available.

        Logs cache operations at debug level for audit trail.
        Does not log the actual key or value to prevent sensitive data exposure.
        """
        if not self.cache:
            return
        try:
            await self.cache.set(key, value, ttl=ttl)
            # Structured audit log without exposing full key or value
            key_prefix = key.split(':')[1] if ':' in key else 'unknown'
            logger.debug("Cache write: success", extra={
                'action': 'cache_write',
                'outcome': 'success',
                'key_prefix': key_prefix,
                'ttl': ttl,
                'station_id': self.station_id,
            })
        except Exception as e:
            logger.warning("Cache write failed", extra={
                'action': 'cache_write',
                'outcome': 'error',
                'error_type': type(e).__name__,
            })

    # ============================================
    # BUSINESS RULES & POLICIES (with caching)
    # ============================================

    async def get_business_charter(self) -> Dict[str, Any]:
        """Get comprehensive business charter for AI context (cached 30 min)"""
        cache_key = self._make_cache_key("charter")
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = await self.business_rules.get_business_charter()
        await self._set_cached(cache_key, result, CACHE_TTL_RULES)
        return result

    async def get_rule_by_category(self, category: RuleCategory) -> List[Dict[str, Any]]:
        """Get all rules for a specific category (cached 30 min)"""
        cache_key = self._make_cache_key(
            "rules", category=category.value if hasattr(category, "value") else category
        )
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = await self.business_rules.get_rule_by_category(category)
        await self._set_cached(cache_key, result, CACHE_TTL_RULES)
        return result

    async def search_rules(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search business rules by keywords"""
        # Don't cache search results (too variable)
        return await self.business_rules.search_rules(keywords)

    # ============================================
    # FAQ SYSTEM (with caching)
    # ============================================

    async def get_faq_answer(
        self, question: str, category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Search FAQ for an answer"""
        # Don't cache search results (increments view count)
        return await self.faq.get_faq_answer(question, category)

    async def get_faqs_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all FAQs for a category (cached 30 min)"""
        cache_key = self._make_cache_key("faqs", category=category)
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = await self.faq.get_faqs_by_category(category)
        await self._set_cached(cache_key, result, CACHE_TTL_FAQ)
        return result

    async def get_top_faqs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular FAQs (cached 30 min)"""
        cache_key = self._make_cache_key("top_faqs", limit=limit)
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = await self.faq.get_top_faqs(limit)
        await self._set_cached(cache_key, result, CACHE_TTL_FAQ)
        return result

    async def get_all_faq_categories(self) -> List[str]:
        """Get all unique FAQ categories (cached 30 min)"""
        cache_key = self._make_cache_key("faq_categories")
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = await self.faq.get_all_categories()
        await self._set_cached(cache_key, result, CACHE_TTL_FAQ)
        return result

    # ============================================
    # MENU & PRICING (with caching)
    # ============================================

    async def get_menu_by_category(
        self, category: Optional[MenuCategory] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get menu items organized by category (cached 30 min)"""
        cache_key = self._make_cache_key("menu", category=category)
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = await self.menu.get_menu_by_category(category)
        await self._set_cached(cache_key, result, CACHE_TTL_MENU)
        return result

    async def get_proteins(self, premium_only: bool = False) -> List[Dict[str, Any]]:
        """Get available protein options (cached 30 min)"""
        cache_key = self._make_cache_key("proteins", premium_only=premium_only)
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = await self.menu.get_proteins(premium_only)
        await self._set_cached(cache_key, result, CACHE_TTL_MENU)
        return result

    async def get_pricing_tiers(self, guest_count: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get available pricing tiers/packages (cached 30 min)"""
        cache_key = self._make_cache_key("pricing_tiers", guest_count=guest_count)
        cached = await self._get_cached(cache_key)
        if cached is not None:
            return cached

        result = await self.menu.get_pricing_tiers(guest_count)
        await self._set_cached(cache_key, result, CACHE_TTL_PRICING)
        return result

    async def calculate_total_price(
        self, guest_count: int, tier_level: PricingTierLevel, add_ons: Optional[List[str]] = None
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
        budget: Optional[Decimal] = None,
    ) -> List[Dict[str, Any]]:
        """Get contextual upsell suggestions"""
        return await self.upsell.get_upsell_suggestions(
            guest_count, event_type, event_date, location, budget
        )

    # ============================================
    # AVAILABILITY CALENDAR
    # ============================================

    async def check_availability(
        self, event_date: date, time_slot: Optional[time] = None, guest_count: int = 1
    ) -> Dict[str, Any]:
        """Check availability for a date/time"""
        return await self.availability.check_availability(event_date, time_slot, guest_count)

    async def get_next_available_dates(self, days_ahead: int = 30, limit: int = 10) -> List[date]:
        """Get next available dates"""
        return await self.availability.get_next_available_dates(days_ahead, limit)

    # ============================================
    # TRAINING DATA
    # ============================================

    async def get_training_examples(
        self, tone: Optional[ToneType] = None, example_type: Optional[str] = None, limit: int = 5
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
        budget: Optional[Decimal] = None,
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
        event_type: Optional[str] = None,
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
                guest_count=guest_count, event_type=event_type
            )
            if upsell_context:
                context_parts.append(upsell_context)

        return "\n\n---\n\n".join(context_parts)

    # ============================================
    # CACHE INVALIDATION
    # ============================================

    async def invalidate_menu_cache(self) -> int:
        """
        Invalidate all menu-related caches.
        Call after admin updates menu items or pricing.

        Returns:
            Number of keys deleted
        """
        if not self.cache:
            return 0

        deleted = 0
        for pattern in ["knowledge:menu:*", "knowledge:proteins:*", "knowledge:pricing_tiers:*"]:
            try:
                deleted += await self.cache.delete_pattern(pattern)
            except Exception as e:
                logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")

        logger.info(f"🗑️ Invalidated {deleted} menu cache keys")
        return deleted

    async def invalidate_faq_cache(self) -> int:
        """
        Invalidate all FAQ-related caches.
        Call after admin updates FAQ items.

        Returns:
            Number of keys deleted
        """
        if not self.cache:
            return 0

        deleted = 0
        for pattern in ["knowledge:faqs:*", "knowledge:top_faqs:*", "knowledge:faq_categories:*"]:
            try:
                deleted += await self.cache.delete_pattern(pattern)
            except Exception as e:
                logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")

        logger.info(f"🗑️ Invalidated {deleted} FAQ cache keys")
        return deleted

    async def invalidate_rules_cache(self) -> int:
        """
        Invalidate all business rules caches.
        Call after admin updates business rules.

        Returns:
            Number of keys deleted
        """
        if not self.cache:
            return 0

        deleted = 0
        for pattern in ["knowledge:charter:*", "knowledge:rules:*"]:
            try:
                deleted += await self.cache.delete_pattern(pattern)
            except Exception as e:
                logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")

        logger.info(f"🗑️ Invalidated {deleted} rules cache keys")
        return deleted

    async def invalidate_all_caches(self) -> int:
        """
        Invalidate all knowledge caches.
        Use sparingly - prefer targeted invalidation.

        Returns:
            Number of keys deleted
        """
        if not self.cache:
            return 0

        try:
            deleted = await self.cache.delete_pattern("knowledge:*")
            logger.info(f"🗑️ Invalidated ALL {deleted} knowledge cache keys")
            return deleted
        except Exception as e:
            logger.error(f"Failed to invalidate all knowledge caches: {e}")
            return 0
