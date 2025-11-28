"""
Business Rules Module

Handles business charter, policies, and terms retrieval.
Provides AI agents with company rules and guidelines.

Created: 2025-11-12
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

# MIGRATED: from models.knowledge_base → db.models.knowledge_base
from db.models.knowledge_base import BusinessRule, RuleCategory

logger = logging.getLogger(__name__)


class BusinessRulesService:
    """Service for managing business rules and policies"""

    def __init__(self, db: AsyncSession, station_id: Optional[str] = None):
        self.db = db
        self.station_id = station_id

    async def get_business_charter(self) -> Dict[str, Any]:
        """
        Get comprehensive business charter for AI context

        Returns:
            Dictionary with all active business rules organized by category
        """
        try:
            # Query all active rules
            stmt = (
                select(BusinessRule)
                .where(
                    and_(
                        BusinessRule.is_active == True,
                        or_(
                            BusinessRule.station_id == self.station_id,
                            BusinessRule.station_id == None,
                        ),
                        or_(
                            BusinessRule.effective_from == None,
                            BusinessRule.effective_from <= datetime.now(timezone.utc),
                        ),
                        or_(
                            BusinessRule.effective_until == None,
                            BusinessRule.effective_until >= datetime.now(timezone.utc),
                        ),
                    )
                )
                .order_by(BusinessRule.category, BusinessRule.priority.desc())
            )

            result = await self.db.execute(stmt)
            rules = result.scalars().all()

            # Organize by category
            charter = {}
            for rule in rules:
                category = rule.category.value if hasattr(rule.category, "value") else rule.category
                if category not in charter:
                    charter[category] = []

                charter[category].append(
                    {
                        "name": rule.rule_name,
                        "content": rule.rule_content,
                        "summary": rule.rule_summary,
                        "keywords": rule.keywords or [],
                        "priority": rule.priority,
                    }
                )

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
            stmt = (
                select(BusinessRule)
                .where(
                    and_(
                        BusinessRule.category == category,
                        BusinessRule.is_active == True,
                        or_(
                            BusinessRule.station_id == self.station_id,
                            BusinessRule.station_id == None,
                        ),
                    )
                )
                .order_by(BusinessRule.priority.desc())
            )

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
            stmt = (
                select(BusinessRule)
                .where(
                    and_(BusinessRule.keywords.overlap(keywords), BusinessRule.is_active == True)
                )
                .order_by(BusinessRule.priority.desc())
            )

            result = await self.db.execute(stmt)
            rules = result.scalars().all()

            return [rule.to_dict() for rule in rules]

        except Exception as e:
            logger.error(f"Error searching rules: {e}")
            return []
