"""
ML Confidence Predictor - Predict student model quality per message
Uses historical performance to estimate confidence before generation
"""

from datetime import datetime, timezone, timedelta
import logging
from typing import Any

from api.ai.shadow.models import AITutorPair
from core.config import get_settings
import numpy as np
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()


class ConfidencePredictor:
    """
    ML-based confidence predictor for student model responses

    Predicts quality before generation using:
    - Message complexity (length, entities, technical terms)
    - Intent type historical performance
    - Similar past conversations
    - Time-based trends
    """

    def __init__(self):
        self.trained = False
        self.feature_weights: dict[str, float] = {}
        self.intent_baselines: dict[str, float] = {}
        self.last_training: datetime | None = None

    async def predict_confidence(
        self,
        db: AsyncSession,
        message: str,
        intent: str,
        context: dict[str, Any] | None = None,
    ) -> float:
        """
        Predict confidence that student model will perform well

        Args:
            db: Database session
            message: User message
            intent: Intent category
            context: Additional context

        Returns:
            Confidence score (0-1)
        """
        if not settings.ML_PREDICTOR_ENABLED:
            return self._simple_confidence(intent)

        # Train model if needed
        if await self._should_retrain(db):
            await self.train(db)

        # Extract features
        features = self._extract_features(message, intent, context)

        # Get base confidence from intent performance
        base_confidence = self.intent_baselines.get(intent, 0.5)

        # Apply feature adjustments
        confidence = base_confidence
        for feature_name, feature_value in features.items():
            if feature_name in self.feature_weights:
                confidence += self.feature_weights[feature_name] * feature_value

        # Clamp to [0, 1]
        confidence = max(0.0, min(1.0, confidence))

        # Adjust based on similar past conversations
        similar_adjustment = await self._get_similar_conversation_adjustment(db, message, intent)
        confidence += similar_adjustment

        return max(0.0, min(1.0, confidence))

    def _simple_confidence(self, intent: str) -> float:
        """Simple confidence when ML predictor disabled"""
        # Conservative estimates
        simple_scores = {"faq": 0.75, "quote": 0.65, "booking": 0.50}
        return simple_scores.get(intent, 0.50)

    def _extract_features(
        self, message: str, intent: str, context: dict[str, Any] | None
    ) -> dict[str, float]:
        """Extract predictive features from message"""

        features = {}

        # Message length (normalized)
        features["length"] = min(1.0, len(message) / 200)

        # Complexity indicators
        features["has_numbers"] = 1.0 if any(c.isdigit() for c in message) else 0.0
        features["has_questions"] = 1.0 if "?" in message else 0.0
        features["word_count"] = min(1.0, len(message.split()) / 50)

        # Intent encoding (one-hot)
        features["is_faq"] = 1.0 if intent == "faq" else 0.0
        features["is_quote"] = 1.0 if intent == "quote" else 0.0
        features["is_booking"] = 1.0 if intent == "booking" else 0.0

        # Context features
        if context:
            features["has_context"] = 1.0
            features["context_length"] = min(1.0, len(str(context)) / 500)
        else:
            features["has_context"] = 0.0
            features["context_length"] = 0.0

        # Technical terms (domain-specific)
        tech_terms = [
            "booking",
            "payment",
            "schedule",
            "reservation",
            "cancel",
        ]
        features["has_tech_terms"] = float(any(term in message.lower() for term in tech_terms))

        return features

    async def train(self, db: AsyncSession):
        """
        Train confidence predictor on historical data

        Uses past tutor pairs to learn feature weights
        """
        logger.info("Training ML confidence predictor...")

        # Get training data (recent pairs with similarity scores)
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        query = (
            select(AITutorPair)
            .where(
                and_(
                    AITutorPair.created_at >= cutoff_date,
                    AITutorPair.similarity_score.isnot(None),
                )
            )
            .limit(settings.ML_PREDICTOR_MIN_TRAINING_SAMPLES)
        )

        result = await db.execute(query)
        pairs = result.scalars().all()

        if len(pairs) < settings.ML_PREDICTOR_MIN_TRAINING_SAMPLES:
            logger.warning(
                f"Insufficient training data: {len(pairs)} pairs "
                f"(need {settings.ML_PREDICTOR_MIN_TRAINING_SAMPLES})"
            )
            return

        # Extract features and targets
        X = []  # Features
        y = []  # Target (similarity scores)

        for pair in pairs:
            features = self._extract_features(
                pair.prompt,
                pair.agent_type or "unknown",
                {"context": pair.context} if pair.context else None,
            )
            X.append(list(features.values()))
            y.append(pair.similarity_score)

        X = np.array(X)
        y = np.array(y)

        # Simple linear regression (OLS)
        # y = X @ weights
        # weights = (X^T X)^-1 X^T y
        try:
            XTX = X.T @ X
            XTy = X.T @ y
            weights = np.linalg.solve(XTX, XTy)

            # Store feature weights
            feature_names = list(self._extract_features("", "faq", None).keys())
            self.feature_weights = dict(zip(feature_names, weights, strict=False))

        except np.linalg.LinAlgError:
            logger.warning("Failed to train predictor: singular matrix")
            return

        # Calculate intent baselines
        for intent in ["faq", "quote", "booking"]:
            intent_pairs = [p for p in pairs if p.agent_type == intent]
            if intent_pairs:
                avg_sim = np.mean([p.similarity_score for p in intent_pairs])
                self.intent_baselines[intent] = avg_sim

        self.trained = True
        self.last_training = datetime.now(timezone.utc)
        logger.info(
            f"ML predictor trained on {len(pairs)} pairs. "
            f"Intent baselines: {self.intent_baselines}"
        )

    async def _should_retrain(self, db: AsyncSession) -> bool:
        """Check if model should be retrained"""
        if not self.trained:
            return True

        if self.last_training is None:
            return True

        hours_since_training = (
            datetime.now(timezone.utc) - self.last_training
        ).total_seconds() / 3600

        return hours_since_training >= settings.ML_PREDICTOR_RETRAIN_INTERVAL_HOURS

    async def _get_similar_conversation_adjustment(
        self, db: AsyncSession, message: str, intent: str
    ) -> float:
        """
        Adjust confidence based on similar past conversations

        Uses simple text similarity (message length + shared words)
        """
        # Get recent pairs with same intent
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        query = (
            select(AITutorPair)
            .where(
                and_(
                    AITutorPair.agent_type == intent,
                    AITutorPair.created_at >= cutoff_date,
                    AITutorPair.similarity_score.isnot(None),
                )
            )
            .order_by(desc(AITutorPair.created_at))
            .limit(10)
        )

        result = await db.execute(query)
        recent_pairs = result.scalars().all()

        if not recent_pairs:
            return 0.0

        # Simple similarity: shared words
        message_words = set(message.lower().split())
        similarities = []

        for pair in recent_pairs:
            pair_words = set(pair.prompt.lower().split())
            shared = len(message_words & pair_words)
            total = len(message_words | pair_words)

            if total > 0:
                text_sim = shared / total
                # Weight by pair's similarity score
                weighted_sim = text_sim * pair.similarity_score
                similarities.append(weighted_sim)

        if similarities:
            # Average adjustment (max ±0.1)
            avg_sim = np.mean(similarities)
            return (avg_sim - 0.5) * 0.2  # Scale to [-0.1, 0.1]

        return 0.0

    def get_stats(self) -> dict[str, Any]:
        """Get predictor statistics"""
        return {
            "trained": self.trained,
            "last_training": (self.last_training.isoformat() if self.last_training else None),
            "intent_baselines": self.intent_baselines,
            "feature_count": len(self.feature_weights),
            "enabled": settings.ML_PREDICTOR_ENABLED,
        }


# Singleton instance
_confidence_predictor = None


def get_confidence_predictor() -> ConfidencePredictor:
    """Get singleton confidence predictor instance"""
    global _confidence_predictor
    if _confidence_predictor is None:
        _confidence_predictor = ConfidencePredictor()
    return _confidence_predictor
