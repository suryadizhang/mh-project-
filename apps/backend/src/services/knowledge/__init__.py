"""
Knowledge Base Service - Modular Architecture

Provides AI agents with dynamic access to business knowledge.
Split into focused modules for maintainability and scalability.

Modules:
- business_rules: Business charter, policies, terms (128 lines)
- faq_service: FAQ search and retrieval (176 lines)
- menu_service: Menu items, pricing, calculations (220 lines)
- upsell_service: Upsell suggestions and triggers (115 lines)
- availability: Calendar and booking availability (138 lines)
- training_data: Training examples for AI (96 lines)
- formatters: AI context formatters (166 lines)
- knowledge_service: Main orchestrator (257 lines)

Total: ~1,296 lines split across 8 files (was 884 lines in 1 file)

Created: 2025-11-12
"""

from .knowledge_service import KnowledgeService
from .business_rules import BusinessRulesService
from .faq_service import FAQService
from .menu_service import MenuService
from .upsell_service import UpsellService
from .availability import AvailabilityService
from .training_data import TrainingDataService
from .formatters import KnowledgeFormatters

__all__ = [
    "KnowledgeService",
    "BusinessRulesService",
    "FAQService",
    "MenuService",
    "UpsellService",
    "AvailabilityService",
    "TrainingDataService",
    "KnowledgeFormatters",
]
