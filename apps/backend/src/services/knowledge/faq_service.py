"""
FAQ Service Module

Handles FAQ search, retrieval, and view tracking.
Provides keyword-based matching for quick FAQ lookup.

Created: 2025-11-12
"""

import logging
from typing import Dict, List, Optional, Any

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

# MIGRATED: from models.knowledge_base → db.models.knowledge_base
from db.models.knowledge_base import FAQItem

logger = logging.getLogger(__name__)


class FAQService:
    """Service for FAQ management and retrieval"""

    def __init__(self, db: AsyncSession, station_id: Optional[str] = None):
        self.db = db
        self.station_id = station_id

    async def get_faq_answer(
        self, question: str, category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
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
                    or_(FAQItem.station_id == self.station_id, FAQItem.station_id == None)
                )

            stmt = (
                select(FAQItem)
                .where(and_(*conditions))
                .order_by(FAQItem.priority.desc(), FAQItem.view_count.desc())
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
            stmt = (
                select(FAQItem)
                .where(and_(FAQItem.category == category, FAQItem.is_active == True))
                .order_by(FAQItem.priority.desc())
            )

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
            stmt = (
                select(FAQItem)
                .where(FAQItem.is_active == True)
                .order_by(FAQItem.view_count.desc(), FAQItem.helpful_count.desc())
                .limit(limit)
            )

            result = await self.db.execute(stmt)
            faqs = result.scalars().all()

            return [faq.to_dict() for faq in faqs]

        except Exception as e:
            logger.error(f"Error fetching top FAQs: {e}")
            return []

    async def get_all_categories(self) -> List[str]:
        """
        Get all unique FAQ categories

        Returns:
            List of category names
        """
        try:
            stmt = select(FAQItem.category).where(FAQItem.is_active == True).distinct()

            result = await self.db.execute(stmt)
            categories = result.scalars().all()

            return list(categories)

        except Exception as e:
            logger.error(f"Error fetching FAQ categories: {e}")
            return []
