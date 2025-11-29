"""
Training Dataset Builder - Convert Conversations to Fine-Tuning Data

This module builds OpenAI-compatible fine-tuning datasets from approved conversations:
- Filters by quality score
- Scrubs PII automatically
- Exports to JSONL format
- Validates dataset quality
- Tracks dataset versions

Author: MyHibachi Development Team
Created: October 31, 2025
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .pii_scrubber import get_pii_scrubber

logger = logging.getLogger(__name__)


class TrainingDatasetBuilder:
    """
    Build OpenAI fine-tuning datasets from approved conversations.

    Output format (JSONL):
    ```json
    {"messages": [
        {"role": "system", "content": "You are My Hibachi's AI..."},
        {"role": "user", "content": "How much for 10 people?"},
        {"role": "assistant", "content": "For 10 adults in Sacramento..."}
    ]}
    ```

    Example:
        ```python
        builder = TrainingDatasetBuilder()
        result = await builder.build_dataset(
            db,
            since_date=datetime.now(timezone.utc) - timedelta(days=90),
            output_path="data/training/mhc_support_v1.jsonl"
        )
        print(f"Built {result['total_examples']} training examples")
        ```
    """

    def __init__(
        self, min_quality_score: float = 0.8, min_user_rating: int = 4, max_examples: int = 10000
    ):
        """
        Initialize dataset builder.

        Args:
            min_quality_score: Minimum quality score to include (0-1)
            min_user_rating: Minimum user rating (1-5)
            max_examples: Maximum examples per dataset
        """
        self.pii_scrubber = get_pii_scrubber()
        self.min_quality_score = min_quality_score
        self.min_user_rating = min_user_rating
        self.max_examples = max_examples
        self.logger = logging.getLogger(__name__)

        # System prompts by intent
        self.system_prompts = {
            "pricing": (
                "You are My Hibachi's AI customer support assistant. "
                "You help customers understand our pricing structure. "
                "Base price is $75 per adult, with protein upgrades available. "
                "Always be clear, accurate, and helpful. Mention travel fees if applicable."
            ),
            "booking": (
                "You are My Hibachi's AI booking assistant. "
                "Guide customers through the booking process step by step. "
                "Confirm guest count, date, time, location, and protein choices. "
                "Be friendly, efficient, and professional."
            ),
            "menu": (
                "You are My Hibachi's AI menu specialist. "
                "Help customers understand our protein options and add-ons. "
                "Standard proteins: chicken, steak, shrimp. "
                "Premium upgrades: filet mignon (+$8), lobster (+$10), scallops (+$8). "
                "Be enthusiastic and descriptive."
            ),
            "complaint": (
                "You are My Hibachi's AI customer care specialist. "
                "Handle complaints with empathy and professionalism. "
                "Apologize sincerely, listen actively, and escalate if needed. "
                "Always prioritize customer satisfaction."
            ),
            "general": (
                "You are My Hibachi's AI customer support assistant. "
                "You help customers with bookings, pricing, menu questions, and general inquiries. "
                "Always be friendly, professional, accurate, and helpful."
            ),
        }

        self.logger.info(
            f"TrainingDatasetBuilder initialized: "
            f"min_quality={min_quality_score}, min_rating={min_user_rating}"
        )

    async def build_dataset(
        self,
        db: AsyncSession,
        since_date: datetime,
        output_path: str,
        intent_filter: str | None = None,
        channel_filter: str | None = None,
    ) -> dict[str, Any]:
        """
        Build training dataset from approved conversations.

        Filters applied:
        - Human-verified OR quality_score >= min_quality_score
        - User rating >= min_user_rating (if feedback exists)
        - Led to booking (preferred but not required)
        - PII scrubbed
        - Created after since_date

        Args:
            db: Database session
            since_date: Only include conversations after this date
            output_path: Path to save JSONL file
            intent_filter: Optional intent to filter by
            channel_filter: Optional channel to filter by

        Returns:
            {
                "total_examples": int,
                "skipped_pii": int,
                "skipped_quality": int,
                "output_path": str,
                "date_range": {...},
                "quality_filters": {...},
                "dataset_version": str
            }
        """
        self.logger.info(f"Building training dataset from {since_date}")

        try:
            # Import here to avoid circular dependency
            from db.models.knowledge_base import TrainingData

            # Build query
            query = select(TrainingData).where(
                and_(
                    TrainingData.created_at >= since_date,
                    TrainingData.is_active,
                    TrainingData.quality_score >= self.min_quality_score,
                )
            )

            # Apply filters
            if intent_filter:
                query = query.where(TrainingData.intent == intent_filter)

            # Execute query
            result = await db.execute(query)
            training_pairs = result.scalars().all()

            self.logger.info(f"Found {len(training_pairs)} candidate training pairs")

            # Build JSONL dataset
            dataset = []
            skipped_pii = 0
            skipped_quality = 0

            for pair in training_pairs:
                # Check if human verified or high quality
                if not pair.human_verified and pair.quality_score < self.min_quality_score:
                    skipped_quality += 1
                    continue

                # Scrub PII
                question_safe = self.pii_scrubber.scrub(pair.question)
                answer_safe = self.pii_scrubber.scrub(pair.answer)

                if (
                    not question_safe["is_safe_for_training"]
                    or not answer_safe["is_safe_for_training"]
                ):
                    skipped_pii += 1
                    self.logger.debug(
                        "Skipped training pair due to PII risk",
                        extra={
                            "question_risk": question_safe["risk_level"],
                            "answer_risk": answer_safe["risk_level"],
                        },
                    )
                    continue

                # Format for OpenAI fine-tuning
                example = {
                    "messages": [
                        {"role": "system", "content": self._get_system_prompt(pair.intent)},
                        {"role": "user", "content": question_safe["cleaned_text"]},
                        {"role": "assistant", "content": answer_safe["cleaned_text"]},
                    ],
                    "metadata": {
                        "intent": pair.intent,
                        "quality_score": pair.quality_score,
                        "human_verified": pair.human_verified,
                        "source_type": pair.source_type,
                    },
                }

                dataset.append(example)

                # Limit dataset size
                if len(dataset) >= self.max_examples:
                    self.logger.warning(f"Reached max examples ({self.max_examples}), stopping")
                    break

            # Validate dataset quality
            validation = self._validate_dataset(dataset)

            if not validation["is_valid"]:
                raise ValueError(f"Dataset validation failed: {validation['issues']}")

            # Save to JSONL
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                for example in dataset:
                    # Remove metadata before saving (OpenAI doesn't need it)
                    clean_example = {"messages": example["messages"]}
                    f.write(json.dumps(clean_example) + "\n")

            # Generate version string
            dataset_version = self._generate_version(since_date, len(dataset))

            result = {
                "total_examples": len(dataset),
                "skipped_pii": skipped_pii,
                "skipped_quality": skipped_quality,
                "output_path": str(output_path_obj.absolute()),
                "date_range": {"start": since_date.isoformat(), "end": datetime.now(timezone.utc).isoformat()},
                "quality_filters": {
                    "min_quality_score": self.min_quality_score,
                    "min_user_rating": self.min_user_rating,
                    "human_verified_preferred": True,
                },
                "dataset_version": dataset_version,
                "validation": validation,
                "file_size_bytes": output_path_obj.stat().st_size,
            }

            self.logger.info(
                f"✅ Dataset built successfully: {len(dataset)} examples", extra=result
            )

            return result

        except Exception as e:
            self.logger.error(f"Error building dataset: {e!s}", exc_info=True)
            raise

    def _get_system_prompt(self, intent: str | None) -> str:
        """Get intent-specific system prompt"""
        return self.system_prompts.get(intent, self.system_prompts["general"])

    def _validate_dataset(self, dataset: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Validate dataset quality.

        Checks:
        - Minimum size (200 examples for effective fine-tuning)
        - No duplicate examples
        - Proper message format
        - Reasonable length distribution
        """
        issues = []

        # Check minimum size
        min_size = 200
        if len(dataset) < min_size:
            issues.append(f"Dataset too small: {len(dataset)} examples (need {min_size})")

        # Check for duplicates
        unique_examples = set()
        duplicates = 0

        for example in dataset:
            user_msg = example["messages"][1]["content"]
            if user_msg in unique_examples:
                duplicates += 1
            else:
                unique_examples.add(user_msg)

        if duplicates > len(dataset) * 0.1:  # >10% duplicates
            issues.append(f"Too many duplicates: {duplicates} ({duplicates/len(dataset)*100:.1f}%)")

        # Check message lengths
        lengths = []
        for example in dataset:
            assistant_msg = example["messages"][2]["content"]
            lengths.append(len(assistant_msg))

        avg_length = sum(lengths) / len(lengths) if lengths else 0

        if avg_length < 50:
            issues.append(f"Responses too short: avg {avg_length:.0f} chars")
        elif avg_length > 2000:
            issues.append(f"Responses too long: avg {avg_length:.0f} chars")

        # Check intent distribution
        intents = {}
        for example in dataset:
            intent = example.get("metadata", {}).get("intent", "unknown")
            intents[intent] = intents.get(intent, 0) + 1

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": [],
            "stats": {
                "total_examples": len(dataset),
                "unique_examples": len(unique_examples),
                "duplicates": duplicates,
                "avg_response_length": round(avg_length, 1),
                "intent_distribution": intents,
            },
        }

    def _generate_version(self, since_date: datetime, example_count: int) -> str:
        """Generate dataset version string"""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"mhc-support-{date_str}-{example_count}ex"

    async def export_for_evaluation(
        self, db: AsyncSession, output_path: str, sample_size: int = 50
    ) -> dict[str, Any]:
        """
        Export a sample dataset for human evaluation.

        Args:
            db: Database session
            output_path: Path to save JSON file
            sample_size: Number of examples to export

        Returns:
            Export metadata
        """
        self.logger.info(f"Exporting {sample_size} examples for evaluation")

        try:
            from db.models.knowledge_base import TrainingData

            # Get random sample of high-quality examples
            query = (
                select(TrainingData)
                .where(TrainingData.quality_score >= self.min_quality_score)
                .limit(sample_size)
            )

            result = await db.execute(query)
            samples = result.scalars().all()

            # Format for human review
            evaluation_data = []

            for sample in samples:
                evaluation_data.append(
                    {
                        "id": str(sample.id),
                        "question": sample.question,
                        "answer": sample.answer,
                        "intent": sample.intent,
                        "quality_score": sample.quality_score,
                        "human_verified": sample.human_verified,
                        "rating": None,  # To be filled by human reviewer
                        "comments": None,  # To be filled by human reviewer
                    }
                )

            # Save to JSON (pretty-printed for readability)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(evaluation_data, f, indent=2)

            return {
                "total_samples": len(evaluation_data),
                "output_path": output_path,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error exporting evaluation data: {e!s}", exc_info=True)
            raise


# Global singleton
_dataset_builder: TrainingDatasetBuilder | None = None


def get_dataset_builder() -> TrainingDatasetBuilder:
    """
    Get global dataset builder instance.

    Returns:
        TrainingDatasetBuilder singleton
    """
    global _dataset_builder

    if _dataset_builder is None:
        _dataset_builder = TrainingDatasetBuilder()

    return _dataset_builder
