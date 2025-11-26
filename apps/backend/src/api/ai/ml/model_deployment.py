"""
Model Deployment - A/B Testing & Deployment Management

This module manages model deployment with A/B testing:
- Shadow deployments (10% traffic)
- Performance comparison
- Automatic promotion/rollback
- Traffic splitting
- Model versioning

Author: MyHibachi Development Team
Created: October 31, 2025
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
import hashlib
import logging
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DeploymentStatus(str, Enum):
    """Model deployment status"""

    SHADOW = "shadow"  # Testing with small traffic
    ACTIVE = "active"  # Full production
    RETIRED = "retired"  # Replaced by newer model


class ModelDeployment:
    """
    Manage model deployments with A/B testing.

    Example:
        ```python
        deployment = ModelDeployment()

        # Deploy new model in shadow mode (10% traffic)
        await deployment.deploy_shadow(
            new_model_id="ft:gpt-4o-mini:mhc-support-v2"
        )

        # After 7 days, compare performance
        comparison = await deployment.compare_performance(db, days=7)

        if comparison['winner'] == 'candidate':
            await deployment.promote_to_production("ft:gpt-4o-mini:mhc-support-v2")
        ```
    """

    def __init__(self):
        """Initialize deployment manager"""
        self.base_model = "gpt-4o-mini"  # Default production model
        self.candidate_model = None  # Model being tested
        self.traffic_split = 0.1  # 10% to candidate
        self.logger = logging.getLogger(__name__)

        self.deployment_history = []

        self.logger.info("ModelDeployment initialized")

    async def deploy_shadow(self, new_model_id: str, traffic_split: float = 0.1) -> dict[str, Any]:
        """
        Deploy new model in shadow mode.

        Args:
            new_model_id: New model to test
            traffic_split: % of traffic to route to new model (0-1)

        Returns:
            Deployment configuration
        """
        if traffic_split < 0 or traffic_split > 0.5:
            raise ValueError("Traffic split must be between 0 and 0.5")

        self.candidate_model = new_model_id
        self.traffic_split = traffic_split

        deployment = {
            "status": "shadow_deployed",
            "base_model": self.base_model,
            "candidate_model": self.candidate_model,
            "traffic_split": self.traffic_split,
            "deployed_at": datetime.now(timezone.utc).isoformat(),
        }

        self.deployment_history.append(deployment)

        self.logger.info(f"🚀 Shadow deployment: {new_model_id}", extra=deployment)

        return deployment

    def select_model(self, user_id: str) -> str:
        """
        Select model based on A/B split.

        Uses consistent hashing so same user always gets same model.

        Args:
            user_id: User identifier

        Returns:
            Model ID to use
        """
        if not self.candidate_model:
            return self.base_model

        # Consistent hashing
        hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        bucket = (hash_value % 100) / 100

        if bucket < self.traffic_split:
            self.logger.debug(f"User {user_id} → candidate model")
            return self.candidate_model
        else:
            self.logger.debug(f"User {user_id} → base model")
            return self.base_model

    async def compare_performance(self, db: AsyncSession, days: int = 7) -> dict[str, Any]:
        """
        Compare base vs candidate model performance.

        Metrics compared:
        - Containment rate (no escalation needed)
        - Avg confidence score
        - Customer satisfaction (feedback ratings)
        - Booking conversion rate
        - Response time

        Args:
            db: Database session
            days: Days of data to compare

        Returns:
            {
                "comparison_period_days": int,
                "base_model": {...metrics...},
                "candidate_model": {...metrics...},
                "winner": str,
                "recommendation": str
            }
        """
        self.logger.info(f"Comparing models over {days} days")

        try:

            since = datetime.now(timezone.utc) - timedelta(days=days)

            # Fetch messages from both models
            base_messages = await self._get_model_messages(db, self.base_model, since)
            candidate_messages = await self._get_model_messages(db, self.candidate_model, since)

            # Calculate metrics
            base_metrics = self._calculate_metrics(base_messages)
            candidate_metrics = self._calculate_metrics(candidate_messages)

            # Determine winner
            winner = self._determine_winner(base_metrics, candidate_metrics)
            recommendation = self._get_recommendation(winner, candidate_metrics, base_metrics)

            comparison = {
                "comparison_period_days": days,
                "base_model": {"name": self.base_model, **base_metrics},
                "candidate_model": {"name": self.candidate_model, **candidate_metrics},
                "winner": winner,
                "recommendation": recommendation,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

            self.logger.info(f"Performance comparison complete: {winner} wins", extra=comparison)

            return comparison

        except Exception as e:
            self.logger.error(f"Error comparing performance: {e!s}", exc_info=True)
            raise

    async def _get_model_messages(
        self, db: AsyncSession, model_id: str, since: datetime
    ) -> list[Any]:
        """Fetch messages from specific model"""
        try:
            from api.ai.endpoints.models import AIMessage, MessageRole

            query = select(Message).where(
                and_(
                    Message.model_used == model_id,
                    Message.role == MessageRole.ASSISTANT.value,
                    Message.created_at >= since,
                )
            )

            result = await db.execute(query)
            return result.scalars().all()

        except Exception as e:
            self.logger.exception(f"Error fetching messages: {e!s}")
            return []

    def _calculate_metrics(self, messages: list[Any]) -> dict[str, float]:
        """Calculate performance metrics for a set of messages"""
        if not messages:
            return {
                "total_messages": 0,
                "containment_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_satisfaction": 0.0,
                "booking_conversion_rate": 0.0,
                "avg_response_time_ms": 0.0,
            }

        # Containment rate (no escalation)
        escalated = sum(1 for m in messages if m.metadata and m.metadata.get("escalated"))
        containment_rate = (1 - escalated / len(messages)) * 100

        # Avg confidence
        total_confidence = sum(m.confidence or 0 for m in messages)
        avg_confidence = total_confidence / len(messages)

        # Customer satisfaction
        satisfaction_scores = []
        for m in messages:
            if m.metadata:
                feedback = m.metadata.get("user_feedback", {})
                if feedback.get("rating"):
                    satisfaction_scores.append(feedback["rating"])

        avg_satisfaction = (
            sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0
        )

        # Booking conversion
        bookings = sum(1 for m in messages if m.metadata and m.metadata.get("led_to_booking"))
        booking_rate = (bookings / len(messages)) * 100

        # Response time
        response_times = []
        for m in messages:
            if m.metadata and m.metadata.get("response_time_ms"):
                response_times.append(m.metadata["response_time_ms"])

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        return {
            "total_messages": len(messages),
            "containment_rate": round(containment_rate, 1),
            "avg_confidence": round(avg_confidence, 3),
            "avg_satisfaction": round(avg_satisfaction, 2),
            "booking_conversion_rate": round(booking_rate, 1),
            "avg_response_time_ms": round(avg_response_time, 0),
        }

    def _determine_winner(self, base_metrics: dict, candidate_metrics: dict) -> str:
        """
        Determine winner based on composite score.

        Weights:
        - Containment rate: 40%
        - Booking conversion: 30%
        - Customer satisfaction: 20%
        - Confidence: 10%
        """

        def composite_score(metrics):
            if metrics["total_messages"] == 0:
                return 0

            return (
                metrics["containment_rate"] * 0.4
                + metrics["booking_conversion_rate"] * 0.3
                + metrics["avg_satisfaction"] * 4 * 0.2  # Scale 1-5 to 0-20
                + metrics["avg_confidence"] * 10 * 0.1  # Scale 0-1 to 0-10
            )

        base_score = composite_score(base_metrics)
        candidate_score = composite_score(candidate_metrics)

        # Require 5% improvement to declare winner
        if candidate_score > base_score * 1.05:
            return "candidate"
        elif base_score > candidate_score * 1.05:
            return "base"
        else:
            return "tie"

    def _get_recommendation(self, winner: str, candidate_metrics: dict, base_metrics: dict) -> str:
        """Get deployment recommendation"""
        if winner == "candidate":
            improvement = (
                self._composite_score_simple(candidate_metrics)
                / self._composite_score_simple(base_metrics)
                - 1
            ) * 100
            return f"PROMOTE: Deploy candidate to 100% traffic (+{improvement:.1f}% improvement)"

        elif winner == "base":
            return "ROLLBACK: Keep base model, discard candidate"

        else:
            return "CONTINUE_TESTING: No clear winner, extend test to 14 days"

    def _composite_score_simple(self, metrics: dict) -> float:
        """Simple composite score calculation"""
        if metrics["total_messages"] == 0:
            return 0

        return (
            metrics["containment_rate"] * 0.4
            + metrics["booking_conversion_rate"] * 0.3
            + metrics["avg_satisfaction"] * 4 * 0.2
            + metrics["avg_confidence"] * 10 * 0.1
        )

    async def promote_to_production(self, model_id: str) -> dict[str, Any]:
        """
        Promote model to production (100% traffic).

        Args:
            model_id: Model to promote

        Returns:
            Promotion confirmation
        """
        old_base = self.base_model
        self.base_model = model_id
        self.candidate_model = None
        self.traffic_split = 0

        promotion = {
            "status": "promoted",
            "previous_model": old_base,
            "new_model": model_id,
            "traffic_split": "100%",
            "promoted_at": datetime.now(timezone.utc).isoformat(),
        }

        self.deployment_history.append(promotion)

        self.logger.info(f"✅ PROMOTED: {model_id} → Production", extra=promotion)

        return promotion

    async def rollback(self) -> dict[str, Any]:
        """
        Rollback to base model (remove candidate).

        Returns:
            Rollback confirmation
        """
        old_candidate = self.candidate_model
        self.candidate_model = None
        self.traffic_split = 0

        rollback = {
            "status": "rolled_back",
            "kept_model": self.base_model,
            "removed_model": old_candidate,
            "rolled_back_at": datetime.now(timezone.utc).isoformat(),
        }

        self.deployment_history.append(rollback)

        self.logger.info(f"⏮️  ROLLED BACK: Removed {old_candidate}", extra=rollback)

        return rollback

    def get_current_deployment(self) -> dict[str, Any]:
        """Get current deployment configuration"""
        return {
            "base_model": self.base_model,
            "candidate_model": self.candidate_model,
            "traffic_split": self.traffic_split,
            "status": "shadow" if self.candidate_model else "stable",
            "history": self.deployment_history[-5:],  # Last 5 deployments
        }


# Global singleton
_deployment_manager: ModelDeployment | None = None


def get_deployment_manager() -> ModelDeployment:
    """
    Get global deployment manager instance.

    Returns:
        ModelDeployment singleton
    """
    global _deployment_manager

    if _deployment_manager is None:
        _deployment_manager = ModelDeployment()

    return _deployment_manager
