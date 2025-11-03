"""
AI Readiness Service - Shadow Learning Assessment
Determines when Ollama is ready for production use
"""

from datetime import datetime, timedelta
import logging
from typing import Any

from api.ai.shadow.models import AITutorPair
from core.config import get_settings
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()


class IntentReadiness:
    """Readiness assessment for a specific intent category"""

    def __init__(
        self,
        intent: str,
        pairs_collected: int,
        min_pairs_required: int,
        avg_similarity: float,
        min_similarity_required: float,
        avg_confidence: float,
        current_traffic_percent: int = 0,
    ):
        self.intent = intent
        self.pairs_collected = pairs_collected
        self.min_pairs_required = min_pairs_required
        self.avg_similarity = avg_similarity
        self.min_similarity_required = min_similarity_required
        self.avg_confidence = avg_confidence
        self.current_traffic_percent = current_traffic_percent

    @property
    def readiness_score(self) -> int:
        """Calculate readiness score (0-100)"""
        # Pairs score (0-40 points)
        pairs_score = min(40, (self.pairs_collected / self.min_pairs_required) * 40)

        # Similarity score (0-40 points)
        similarity_score = min(40, (self.avg_similarity / self.min_similarity_required) * 40)

        # Confidence score (0-20 points)
        confidence_score = min(20, (self.avg_confidence / 0.75) * 20)

        return int(pairs_score + similarity_score + confidence_score)

    @property
    def status(self) -> str:
        """Get status: green/yellow/red"""
        score = self.readiness_score
        if score >= 85:
            return "green"
        elif score >= 70:
            return "yellow"
        else:
            return "red"

    @property
    def can_activate(self) -> bool:
        """Can we activate this intent for production?"""
        return (
            self.pairs_collected >= self.min_pairs_required
            and self.avg_similarity >= self.min_similarity_required
            and self.avg_confidence >= 0.75
            and self.readiness_score >= 85
        )

    @property
    def recommended_traffic_percent(self) -> int:
        """Recommended traffic percentage for gradual rollout"""
        if not self.can_activate:
            return 0

        score = self.readiness_score
        if score >= 95:
            return 50  # High confidence
        elif score >= 90:
            return 25
        elif score >= 85:
            return 10  # Conservative start
        else:
            return 0

    def get_blocking_reasons(self) -> list[str]:
        """Get list of reasons why not ready"""
        reasons = []

        if self.pairs_collected < self.min_pairs_required:
            needed = self.min_pairs_required - self.pairs_collected
            reasons.append(f"Need {needed} more pairs (target: {self.min_pairs_required})")

        if self.avg_similarity < self.min_similarity_required:
            reasons.append(
                f"Similarity too low: {self.avg_similarity:.2f} "
                f"(need {self.min_similarity_required:.2f})"
            )

        if self.avg_confidence < 0.75:
            reasons.append(f"Confidence too low: {self.avg_confidence:.2f} (need 0.75)")

        return reasons

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "intent": self.intent,
            "readiness_score": self.readiness_score,
            "status": self.status,
            "pairs_collected": self.pairs_collected,
            "min_pairs_required": self.min_pairs_required,
            "avg_similarity": round(self.avg_similarity, 3),
            "min_similarity_required": self.min_similarity_required,
            "avg_confidence": round(self.avg_confidence, 3),
            "current_traffic_percent": self.current_traffic_percent,
            "recommended_traffic_percent": self.recommended_traffic_percent,
            "can_activate": self.can_activate,
            "blocking_reasons": (self.get_blocking_reasons() if not self.can_activate else []),
        }


class AIReadinessService:
    """
    Service for assessing when Ollama is ready for production

    Provides:
    - Overall readiness score
    - Per-intent readiness assessment
    - Gradual rollout recommendations
    - Quality monitoring
    """

    INTENT_CONFIG = {
        "faq": {
            "min_pairs": settings.READINESS_FAQ_MIN_PAIRS,
            "min_similarity": settings.READINESS_FAQ_MIN_SIMILARITY,
            "description": "FAQ and general info",
        },
        "quote": {
            "min_pairs": settings.READINESS_QUOTE_MIN_PAIRS,
            "min_similarity": settings.READINESS_QUOTE_MIN_SIMILARITY,
            "description": "Price quotes and estimates",
        },
        "booking": {
            "min_pairs": settings.READINESS_BOOKING_MIN_PAIRS,
            "min_similarity": settings.READINESS_BOOKING_MIN_SIMILARITY,
            "description": "Booking and scheduling",
        },
    }

    async def get_overall_readiness(self, db: AsyncSession) -> dict[str, Any]:
        """
        Get overall AI readiness assessment

        Returns comprehensive readiness status across all intents
        """
        # Get total pairs
        total_pairs_query = select(func.count(AITutorPair.id))
        result = await db.execute(total_pairs_query)
        total_pairs = result.scalar() or 0

        # Get average similarity
        avg_sim_query = select(func.avg(AITutorPair.similarity_score)).where(
            AITutorPair.similarity_score.isnot(None)
        )
        result = await db.execute(avg_sim_query)
        avg_similarity = result.scalar() or 0.0

        # Get per-intent readiness
        intent_readiness = {}
        ready_intents = []
        pending_intents = []

        for intent, _config in self.INTENT_CONFIG.items():
            readiness = await self.get_intent_readiness(db, intent)
            intent_readiness[intent] = readiness

            if readiness.can_activate:
                ready_intents.append(intent)
            else:
                pending_intents.append(intent)

        # Calculate overall score (average of all intents)
        overall_score = int(
            sum(r.readiness_score for r in intent_readiness.values()) / len(intent_readiness)
        )

        # Determine overall status
        if overall_score >= 85:
            status = "green"
        elif overall_score >= 70:
            status = "yellow"
        else:
            status = "red"

        # Get recent performance
        recent_stats = await self._get_recent_performance(db, days=7)

        return {
            "overall_readiness": {
                "score": overall_score,
                "status": status,
                "total_pairs": total_pairs,
                "avg_similarity": round(avg_similarity, 3),
                "ready_intents": ready_intents,
                "pending_intents": pending_intents,
                "local_ai_mode": settings.LOCAL_AI_MODE,
                "shadow_learning_enabled": settings.SHADOW_LEARNING_ENABLED,
            },
            "intent_breakdown": {
                intent: readiness.to_dict() for intent, readiness in intent_readiness.items()
            },
            "quality_metrics": recent_stats,
            "recommendations": self._generate_recommendations(intent_readiness),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_intent_readiness(self, db: AsyncSession, intent: str) -> IntentReadiness:
        """Get readiness assessment for specific intent"""

        if intent not in self.INTENT_CONFIG:
            raise ValueError(f"Unknown intent: {intent}")

        config = self.INTENT_CONFIG[intent]

        # Count pairs for this intent
        pairs_query = select(func.count(AITutorPair.id)).where(AITutorPair.agent_type == intent)
        result = await db.execute(pairs_query)
        pairs_collected = result.scalar() or 0

        # Get average similarity for this intent
        avg_sim_query = select(func.avg(AITutorPair.similarity_score)).where(
            and_(
                AITutorPair.agent_type == intent,
                AITutorPair.similarity_score.isnot(None),
            )
        )
        result = await db.execute(avg_sim_query)
        avg_similarity = result.scalar() or 0.0

        # Get average quality score (confidence)
        avg_conf_query = select(func.avg(AITutorPair.quality_score)).where(
            and_(
                AITutorPair.agent_type == intent,
                AITutorPair.quality_score.isnot(None),
            )
        )
        result = await db.execute(avg_conf_query)
        avg_confidence = result.scalar() or 0.0

        return IntentReadiness(
            intent=intent,
            pairs_collected=pairs_collected,
            min_pairs_required=config["min_pairs"],
            avg_similarity=avg_similarity,
            min_similarity_required=config["min_similarity"],
            avg_confidence=avg_confidence,
        )

    async def _get_recent_performance(self, db: AsyncSession, days: int = 7) -> dict[str, Any]:
        """Get performance metrics for recent period"""

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Recent pairs
        recent_query = select(func.count(AITutorPair.id)).where(
            AITutorPair.created_at >= cutoff_date
        )
        result = await db.execute(recent_query)
        recent_pairs = result.scalar() or 0

        # Recent average similarity
        recent_sim_query = select(func.avg(AITutorPair.similarity_score)).where(
            and_(
                AITutorPair.created_at >= cutoff_date,
                AITutorPair.similarity_score.isnot(None),
            )
        )
        result = await db.execute(recent_sim_query)
        recent_similarity = result.scalar() or 0.0

        # Speed comparison
        avg_teacher_time_query = select(func.avg(AITutorPair.teacher_response_time_ms)).where(
            and_(
                AITutorPair.created_at >= cutoff_date,
                AITutorPair.teacher_response_time_ms.isnot(None),
            )
        )
        result = await db.execute(avg_teacher_time_query)
        avg_teacher_time = result.scalar() or 0

        avg_student_time_query = select(func.avg(AITutorPair.student_response_time_ms)).where(
            and_(
                AITutorPair.created_at >= cutoff_date,
                AITutorPair.student_response_time_ms.isnot(None),
            )
        )
        result = await db.execute(avg_student_time_query)
        avg_student_time = result.scalar() or 0

        # Calculate speedup
        if avg_teacher_time > 0:
            speedup_percent = int(((avg_teacher_time - avg_student_time) / avg_teacher_time) * 100)
        else:
            speedup_percent = 0

        # Cost savings potential
        avg_cost_query = select(func.avg(AITutorPair.teacher_cost_usd)).where(
            and_(
                AITutorPair.created_at >= cutoff_date,
                AITutorPair.teacher_cost_usd.isnot(None),
            )
        )
        result = await db.execute(avg_cost_query)
        avg_cost_per_call = result.scalar() or 0.0

        # Estimate monthly savings at 100% local
        estimated_monthly_calls = recent_pairs * (30 / days)
        potential_savings = avg_cost_per_call * estimated_monthly_calls

        return {
            f"last_{days}_days_pairs": recent_pairs,
            f"last_{days}_days_similarity": round(recent_similarity, 3),
            "student_faster_by_percent": speedup_percent,
            "avg_teacher_time_ms": int(avg_teacher_time),
            "avg_student_time_ms": int(avg_student_time),
            "avg_cost_per_call_usd": round(avg_cost_per_call, 4),
            "estimated_monthly_savings_usd": round(potential_savings, 2),
            "quality_regression_detected": recent_similarity < 0.75,
        }

    def _generate_recommendations(self, intent_readiness: dict[str, IntentReadiness]) -> list[str]:
        """Generate actionable recommendations"""

        recommendations = []

        for intent, readiness in intent_readiness.items():
            if readiness.can_activate and readiness.current_traffic_percent == 0:
                recommendations.append(
                    f"✅ {intent.upper()} is ready! "
                    f"Enable {readiness.recommended_traffic_percent}% traffic to test"
                )
            elif not readiness.can_activate:
                reasons = readiness.get_blocking_reasons()
                if reasons:
                    recommendations.append(f"⏳ {intent.upper()}: {reasons[0]}")

        # Add shadow mode recommendation
        if settings.LOCAL_AI_MODE == "shadow":
            ready_count = sum(1 for r in intent_readiness.values() if r.can_activate)
            if ready_count > 0:
                recommendations.append(
                    f"💡 {ready_count} intent(s) ready. "
                    f"Consider switching LOCAL_AI_MODE to 'active'"
                )

        return recommendations

    async def should_use_local_model(
        self, db: AsyncSession, intent: str, confidence: float
    ) -> bool:
        """
        Decide if we should use local model for this request

        Used by ModelRouter to make real-time routing decisions
        """
        # Always use OpenAI in shadow mode
        if settings.LOCAL_AI_MODE == "shadow":
            return False

        # Check if intent is ready
        readiness = await self.get_intent_readiness(db, intent)
        if not readiness.can_activate:
            return False

        # Check confidence threshold
        if confidence < settings.LOCAL_AI_MIN_CONFIDENCE:
            return False

        # TODO: Check traffic split percentage
        # For now, use if ready and confident
        return True


# Singleton instance
_readiness_service = None


def get_readiness_service() -> AIReadinessService:
    """Get singleton readiness service instance"""
    global _readiness_service
    if _readiness_service is None:
        _readiness_service = AIReadinessService()
    return _readiness_service
