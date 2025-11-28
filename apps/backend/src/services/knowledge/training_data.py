"""
Training Data Service Module

Handles training examples and AI learning data.
Provides examples for few-shot prompting and tone matching.

Created: 2025-11-12
"""

import logging
from typing import Dict, List, Optional, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# MIGRATED: from models.knowledge_base → db.models.knowledge_base
from db.models.knowledge_base import TrainingData, ToneType

logger = logging.getLogger(__name__)


class TrainingDataService:
    """Service for managing AI training data"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_training_examples(
        self, tone: Optional[ToneType] = None, example_type: Optional[str] = None, limit: int = 5
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

            stmt = (
                select(TrainingData)
                .where(and_(*conditions))
                .order_by(TrainingData.quality_score.desc(), TrainingData.used_count.asc())
                .limit(limit)
            )

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

    async def get_examples_by_scenario(self, scenario: str) -> List[Dict[str, Any]]:
        """
        Get training examples for a specific scenario

        Args:
            scenario: Scenario name (e.g., 'objection_handling', 'pricing_inquiry')

        Returns:
            List of training examples
        """
        try:
            stmt = (
                select(TrainingData)
                .where(and_(TrainingData.example_type == scenario, TrainingData.is_active == True))
                .order_by(TrainingData.quality_score.desc())
                .limit(10)
            )

            result = await self.db.execute(stmt)
            examples = result.scalars().all()

            return [example.to_dict() for example in examples]

        except Exception as e:
            logger.error(f"Error fetching examples for scenario {scenario}: {e}")
            return []
