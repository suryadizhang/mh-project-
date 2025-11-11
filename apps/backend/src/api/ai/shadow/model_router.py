"""
Model Router - Smart AI Model Selection
Routes requests between OpenAI (teacher) and Ollama (student)
"""

from datetime import datetime, timezone
import logging
import random
from typing import Any, Literal

from api.ai.shadow.readiness_service import get_readiness_service
from core.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()


ModelChoice = Literal["openai", "ollama_local"]


class TrafficSplitConfig:
    """Traffic split configuration for gradual rollout"""

    def __init__(self):
        # Intent -> Percentage of traffic to send to local model
        self.splits: dict[str, int] = {"faq": 0, "quote": 0, "booking": 0}
        self.last_updated = datetime.now(timezone.utc)

    def get_split(self, intent: str) -> int:
        """Get traffic split percentage for intent"""
        return self.splits.get(intent, 0)

    def set_split(self, intent: str, percentage: int):
        """Set traffic split for intent (0-100)"""
        if not 0 <= percentage <= 100:
            raise ValueError("Percentage must be between 0 and 100")
        self.splits[intent] = percentage
        self.last_updated = datetime.now(timezone.utc)
        logger.info(f"Traffic split updated: {intent} = {percentage}%")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "splits": self.splits,
            "last_updated": self.last_updated.isoformat(),
        }


class ModelRouter:
    """
    Smart router that decides which AI model to use

    Decision factors:
    1. LOCAL_AI_MODE setting (shadow vs active)
    2. Intent readiness (from AIReadinessService)
    3. Confidence score (from ML predictor)
    4. Traffic split percentage (gradual rollout)
    5. Quality monitoring (auto-rollback if degraded)
    """

    def __init__(self):
        self.readiness_service = get_readiness_service()
        self.traffic_split = TrafficSplitConfig()
        self.stats = {
            "total_requests": 0,
            "openai_requests": 0,
            "ollama_requests": 0,
            "by_intent": {},
        }

    async def route_message(
        self,
        db: AsyncSession,
        intent: str,
        message: str,
        confidence: float,
        context: dict[str, Any] | None = None,
    ) -> ModelChoice:
        """
        Route a message to appropriate AI model

        Args:
            db: Database session
            intent: Intent category (faq/quote/booking)
            message: User message
            confidence: ML confidence score (0-1)
            context: Additional context

        Returns:
            "openai" or "ollama_local"
        """
        self.stats["total_requests"] += 1

        # Always use OpenAI in shadow mode
        if settings.LOCAL_AI_MODE == "shadow":
            self._record_routing("openai", intent)
            return "openai"

        # Check if intent is ready for local model
        if not await self._is_intent_ready(db, intent, confidence):
            self._record_routing("openai", intent)
            return "openai"

        # Check traffic split (gradual rollout)
        split_percentage = self.traffic_split.get_split(intent)
        if split_percentage == 0:
            self._record_routing("openai", intent)
            return "openai"

        # Random selection based on traffic split
        if random.random() * 100 < split_percentage:
            self._record_routing("ollama_local", intent)
            return "ollama_local"
        else:
            self._record_routing("openai", intent)
            return "openai"

    async def _is_intent_ready(self, db: AsyncSession, intent: str, confidence: float) -> bool:
        """Check if intent is ready for local model"""
        try:
            return await self.readiness_service.should_use_local_model(db, intent, confidence)
        except Exception as e:
            logger.warning(f"Error checking readiness: {e}")
            return False

    def _record_routing(self, model: str, intent: str):
        """Record routing statistics"""
        if model == "openai":
            self.stats["openai_requests"] += 1
        else:
            self.stats["ollama_requests"] += 1

        if intent not in self.stats["by_intent"]:
            self.stats["by_intent"][intent] = {
                "total": 0,
                "openai": 0,
                "ollama": 0,
            }

        self.stats["by_intent"][intent]["total"] += 1
        self.stats["by_intent"][intent][model.replace("_local", "")] += 1

    def get_routing_stats(self) -> dict[str, Any]:
        """Get routing statistics"""
        total = self.stats["total_requests"]
        if total == 0:
            openai_percent = 0
            ollama_percent = 0
        else:
            openai_percent = (self.stats["openai_requests"] / total) * 100
            ollama_percent = (self.stats["ollama_requests"] / total) * 100

        return {
            "total_requests": total,
            "openai_requests": self.stats["openai_requests"],
            "ollama_requests": self.stats["ollama_requests"],
            "openai_percent": round(openai_percent, 2),
            "ollama_percent": round(ollama_percent, 2),
            "by_intent": self.stats["by_intent"],
            "current_splits": self.traffic_split.to_dict(),
            "local_ai_mode": settings.LOCAL_AI_MODE,
        }

    def update_traffic_split(self, intent: str, percentage: int):
        """Update traffic split for gradual rollout"""
        self.traffic_split.set_split(intent, percentage)

    def reset_stats(self):
        """Reset routing statistics"""
        self.stats = {
            "total_requests": 0,
            "openai_requests": 0,
            "ollama_requests": 0,
            "by_intent": {},
        }
        logger.info("Routing stats reset")


# Singleton instance
_model_router = None


def get_model_router() -> ModelRouter:
    """Get singleton model router instance"""
    global _model_router
    if _model_router is None:
        _model_router = ModelRouter()
    return _model_router
