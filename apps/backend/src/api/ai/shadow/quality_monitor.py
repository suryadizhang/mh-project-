"""
Quality Monitor - Detect degradation and trigger auto-rollback
Monitors student model performance and prevents quality issues
"""

from datetime import datetime, timezone, timedelta
import logging
from typing import Any

from api.ai.shadow.model_router import get_model_router
from api.ai.shadow.models import AITutorPair
from core.config import get_settings
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()


class QualityAlert:
    """Quality alert notification"""

    def __init__(
        self,
        severity: str,
        intent: str,
        metric: str,
        current_value: float,
        expected_value: float,
        message: str,
    ):
        self.severity = severity  # "info", "warning", "critical"
        self.intent = intent
        self.metric = metric
        self.current_value = current_value
        self.expected_value = expected_value
        self.message = message
        self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "intent": self.intent,
            "metric": self.metric,
            "current_value": round(self.current_value, 3),
            "expected_value": round(self.expected_value, 3),
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }


class QualityMonitor:
    """
    Monitors AI quality and triggers rollback if degraded

    Tracks:
    - Similarity score trends
    - Response time regression
    - Customer feedback signals
    - Automatic rollback to OpenAI if issues detected
    """

    def __init__(self):
        self.alerts: list[QualityAlert] = []
        self.rollback_history: list[dict[str, Any]] = []

    async def check_quality(self, db: AsyncSession) -> list[QualityAlert]:
        """
        Run quality checks and return alerts

        Returns list of alerts (empty if all good)
        """
        if not settings.QUALITY_MONITOR_ENABLED:
            return []

        new_alerts = []

        # Check each intent
        for intent in ["faq", "quote", "booking"]:
            # Check similarity degradation
            sim_alert = await self._check_similarity_degradation(db, intent)
            if sim_alert:
                new_alerts.append(sim_alert)

            # Check response time regression
            time_alert = await self._check_response_time_regression(db, intent)
            if time_alert:
                new_alerts.append(time_alert)

        # Store alerts
        self.alerts.extend(new_alerts)

        # Trigger auto-rollback if critical alerts
        if settings.AUTO_ROLLBACK_ENABLED:
            for alert in new_alerts:
                if alert.severity == "critical":
                    await self._trigger_rollback(alert.intent, alert.message)

        return new_alerts

    async def _check_similarity_degradation(
        self, db: AsyncSession, intent: str
    ) -> QualityAlert | None:
        """Check if similarity scores are degrading"""

        # Get baseline (last 30 days)
        baseline_date = datetime.now(timezone.utc) - timedelta(days=30)
        baseline_query = select(func.avg(AITutorPair.similarity_score)).where(
            and_(
                AITutorPair.agent_type == intent,
                AITutorPair.created_at >= baseline_date,
                AITutorPair.similarity_score.isnot(None),
            )
        )
        result = await db.execute(baseline_query)
        baseline_sim = result.scalar() or 0.0

        # Get recent (last 24 hours)
        recent_date = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_query = select(func.avg(AITutorPair.similarity_score)).where(
            and_(
                AITutorPair.agent_type == intent,
                AITutorPair.created_at >= recent_date,
                AITutorPair.similarity_score.isnot(None),
            )
        )
        result = await db.execute(recent_query)
        recent_sim = result.scalar() or 0.0

        if baseline_sim == 0 or recent_sim == 0:
            return None

        # Calculate degradation
        degradation = (baseline_sim - recent_sim) / baseline_sim

        # Alert if degradation exceeds threshold
        if degradation > settings.QUALITY_DEGRADATION_THRESHOLD:
            severity = "critical" if degradation > 0.20 else "warning"
            return QualityAlert(
                severity=severity,
                intent=intent,
                metric="similarity_score",
                current_value=recent_sim,
                expected_value=baseline_sim,
                message=f"{intent.upper()}: Similarity dropped {int(degradation*100)}% "
                f"(baseline: {baseline_sim:.2f}, recent: {recent_sim:.2f})",
            )

        return None

    async def _check_response_time_regression(
        self, db: AsyncSession, intent: str
    ) -> QualityAlert | None:
        """Check if student response time is increasing"""

        # Get baseline (last 30 days)
        baseline_date = datetime.now(timezone.utc) - timedelta(days=30)
        baseline_query = select(func.avg(AITutorPair.student_response_time_ms)).where(
            and_(
                AITutorPair.agent_type == intent,
                AITutorPair.created_at >= baseline_date,
                AITutorPair.student_response_time_ms.isnot(None),
            )
        )
        result = await db.execute(baseline_query)
        baseline_time = result.scalar() or 0

        # Get recent (last 24 hours)
        recent_date = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_query = select(func.avg(AITutorPair.student_response_time_ms)).where(
            and_(
                AITutorPair.agent_type == intent,
                AITutorPair.created_at >= recent_date,
                AITutorPair.student_response_time_ms.isnot(None),
            )
        )
        result = await db.execute(recent_query)
        recent_time = result.scalar() or 0

        if baseline_time == 0 or recent_time == 0:
            return None

        # Calculate regression (50% increase is concerning)
        regression = (recent_time - baseline_time) / baseline_time

        if regression > 0.50:  # 50% slower
            return QualityAlert(
                severity="warning",
                intent=intent,
                metric="response_time",
                current_value=recent_time,
                expected_value=baseline_time,
                message=f"{intent.upper()}: Response time increased {int(regression*100)}% "
                f"(baseline: {int(baseline_time)}ms, recent: {int(recent_time)}ms)",
            )

        return None

    async def _trigger_rollback(self, intent: str, reason: str):
        """
        Trigger automatic rollback to OpenAI

        Disables local model for this intent
        """
        logger.critical(f"AUTO-ROLLBACK triggered for {intent}: {reason}")

        # Disable traffic for this intent
        router = get_model_router()
        router.update_traffic_split(intent, 0)

        # Record rollback
        self.rollback_history.append(
            {
                "intent": intent,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # TODO: Send alert notification (Slack, email, etc.)

    def get_alerts(self, severity: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent quality alerts"""

        filtered_alerts = self.alerts
        if severity:
            filtered_alerts = [a for a in self.alerts if a.severity == severity]

        # Most recent first
        sorted_alerts = sorted(filtered_alerts, key=lambda a: a.timestamp, reverse=True)[:limit]

        return [a.to_dict() for a in sorted_alerts]

    def clear_alerts(self):
        """Clear alert history"""
        self.alerts = []
        logger.info("Quality alerts cleared")

    def get_rollback_history(self) -> list[dict[str, Any]]:
        """Get rollback history"""
        return self.rollback_history

    async def get_quality_comparison(
        self, db: AsyncSession, intent: str | None = None, days: int = 7
    ) -> dict[str, Any]:
        """
        Get teacher vs student quality comparison

        Returns detailed metrics for analysis
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Build query
        query = select(AITutorPair).where(AITutorPair.created_at >= cutoff_date)
        if intent:
            query = query.where(AITutorPair.agent_type == intent)

        result = await db.execute(query)
        pairs = result.scalars().all()

        if not pairs:
            return {"error": "No data available"}

        # Calculate metrics
        similarities = [p.similarity_score for p in pairs if p.similarity_score]
        teacher_times = [p.teacher_response_time_ms for p in pairs if p.teacher_response_time_ms]
        student_times = [p.student_response_time_ms for p in pairs if p.student_response_time_ms]
        costs = [p.teacher_cost_usd for p in pairs if p.teacher_cost_usd]

        comparison = {
            "period_days": days,
            "total_pairs": len(pairs),
            "intent": intent or "all",
            "similarity": {
                "avg": (round(sum(similarities) / len(similarities), 3) if similarities else 0),
                "min": round(min(similarities), 3) if similarities else 0,
                "max": round(max(similarities), 3) if similarities else 0,
                "count_high_quality": len([s for s in similarities if s >= 0.85]),
            },
            "response_time": {
                "teacher_avg_ms": (
                    int(sum(teacher_times) / len(teacher_times)) if teacher_times else 0
                ),
                "student_avg_ms": (
                    int(sum(student_times) / len(student_times)) if student_times else 0
                ),
                "student_faster_percent": 0,
            },
            "cost_analysis": {
                "avg_teacher_cost_usd": (round(sum(costs) / len(costs), 4) if costs else 0),
                "total_teacher_cost_usd": round(sum(costs), 2) if costs else 0,
                "potential_savings_usd": round(sum(costs), 2) if costs else 0,
            },
        }

        # Calculate speedup
        if comparison["response_time"]["teacher_avg_ms"] > 0:
            teacher_avg = comparison["response_time"]["teacher_avg_ms"]
            student_avg = comparison["response_time"]["student_avg_ms"]
            speedup = ((teacher_avg - student_avg) / teacher_avg) * 100
            comparison["response_time"]["student_faster_percent"] = int(speedup)

        return comparison


# Singleton instance
_quality_monitor = None


def get_quality_monitor() -> QualityMonitor:
    """Get singleton quality monitor instance"""
    global _quality_monitor
    if _quality_monitor is None:
        _quality_monitor = QualityMonitor()
    return _quality_monitor
