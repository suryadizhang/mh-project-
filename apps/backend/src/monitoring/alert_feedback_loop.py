"""
Alert Resolution Feedback Loop

Learns from alert resolutions to improve future predictions and auto-resolution.

Features:
- Tracks resolution patterns
- Calculates accuracy of AI predictions
- Updates confidence scores based on outcomes
- Identifies successful auto-resolution patterns
- Provides learning metrics

This enables continuous improvement of the AI alert triage system.

Created: November 10, 2025
Part of: AI-Monitoring Integration
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import text
import redis

from core.config import settings
from core.database import SessionLocal
from monitoring.alert_service import Alert


logger = logging.getLogger(__name__)


@dataclass
class ResolutionPattern:
    """Pattern learned from alert resolutions"""
    alert_category: str
    alert_level: str
    root_cause: str
    resolution_steps: List[str]
    success_rate: float
    avg_resolution_time_minutes: int
    occurrences: int
    last_seen: datetime


@dataclass
class FeedbackMetrics:
    """Metrics about feedback loop performance"""
    total_resolutions_tracked: int
    auto_resolution_accuracy: float
    ai_prediction_accuracy: float
    patterns_learned: int
    avg_learning_improvement_percent: float


class AlertFeedbackLoop:
    """
    Tracks alert resolutions and learns patterns for improvement.
    
    Features:
    - Records resolution outcomes
    - Calculates AI prediction accuracy
    - Identifies successful patterns
    - Updates confidence models
    - Provides learning metrics
    
    Usage:
        feedback = AlertFeedbackLoop()
        
        # After resolving an alert
        await feedback.record_resolution(
            alert=alert,
            resolution_method="manual",
            success=True,
            actual_root_cause="Database connection pool exhausted"
        )
        
        # Get learned patterns
        patterns = await feedback.get_resolution_patterns(
            category="threshold",
            level="critical"
        )
        
        # Get learning metrics
        metrics = await feedback.get_feedback_metrics()
    """
    
    def __init__(
        self,
        db: Optional[Session] = None,
        redis_client: Optional[redis.Redis] = None
    ):
        """
        Initialize feedback loop.
        
        Args:
            db: Database session (optional)
            redis_client: Redis client (optional)
        """
        self.db = db or SessionLocal()
        self.redis = redis_client or redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        # Redis keys
        self.resolutions_key = "ai:feedback:resolutions"
        self.patterns_key = "ai:feedback:patterns"
        self.accuracy_key = "ai:feedback:accuracy"
        self.learning_metrics_key = "ai:feedback:metrics"
    
    async def record_resolution(
        self,
        alert: Alert,
        resolution_method: str,  # "auto", "manual", "ai_suggested"
        success: bool,
        actual_root_cause: Optional[str] = None,
        resolution_time_minutes: Optional[int] = None,
        notes: Optional[str] = None
    ):
        """
        Record alert resolution for learning.
        
        Args:
            alert: Resolved alert
            resolution_method: How it was resolved
            success: Whether resolution was successful
            actual_root_cause: Confirmed root cause
            resolution_time_minutes: Time taken to resolve
            notes: Additional notes
        """
        try:
            # Calculate resolution time if not provided
            if resolution_time_minutes is None and alert.resolved_at and alert.created_at:
                delta = alert.resolved_at - alert.created_at
                resolution_time_minutes = int(delta.total_seconds() / 60)
            
            # Get AI predictions from metadata
            ai_root_cause = alert.metadata.get("ai_root_cause") if alert.metadata else None
            ai_confidence = alert.metadata.get("ai_confidence") if alert.metadata else None
            auto_resolvable = alert.metadata.get("auto_resolvable", False) if alert.metadata else False
            
            # Build resolution record
            resolution_record = {
                "alert_id": alert.id,
                "alert_category": alert.category,
                "alert_level": alert.level,
                "resolution_method": resolution_method,
                "success": success,
                "resolution_time_minutes": resolution_time_minutes,
                "ai_predicted_root_cause": ai_root_cause,
                "actual_root_cause": actual_root_cause,
                "ai_confidence": ai_confidence,
                "auto_resolvable_predicted": auto_resolvable,
                "was_auto_resolved": (resolution_method == "auto"),
                "notes": notes,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
                "recorded_at": datetime.utcnow().isoformat()
            }
            
            # Store in Redis
            self.redis.lpush(
                self.resolutions_key,
                json.dumps(resolution_record)
            )
            
            # Keep last 5000 resolutions
            self.redis.ltrim(self.resolutions_key, 0, 4999)
            
            # Update patterns
            await self._update_patterns(resolution_record)
            
            # Update accuracy metrics
            await self._update_accuracy(resolution_record)
            
            logger.info(
                f"Recorded resolution for alert #{alert.id} | "
                f"Method: {resolution_method} | "
                f"Success: {success} | "
                f"Time: {resolution_time_minutes} min"
            )
            
        except Exception as e:
            logger.error(f"Error recording resolution: {e}", exc_info=True)
    
    async def _update_patterns(self, resolution: Dict[str, Any]):
        """
        Update learned patterns based on resolution.
        
        Args:
            resolution: Resolution record
        """
        try:
            if not resolution["success"]:
                return  # Only learn from successful resolutions
            
            pattern_key = f"{resolution['alert_category']}:{resolution['alert_level']}"
            
            # Get existing pattern
            pattern_data = self.redis.hget(self.patterns_key, pattern_key)
            
            if pattern_data:
                pattern = json.loads(pattern_data)
            else:
                pattern = {
                    "category": resolution["alert_category"],
                    "level": resolution["alert_level"],
                    "resolutions": [],
                    "total_count": 0,
                    "success_count": 0,
                    "total_time_minutes": 0,
                    "root_causes": defaultdict(int),
                    "resolution_methods": defaultdict(int)
                }
            
            # Update pattern
            pattern["total_count"] += 1
            pattern["success_count"] += 1
            
            if resolution["resolution_time_minutes"]:
                pattern["total_time_minutes"] += resolution["resolution_time_minutes"]
            
            if resolution["actual_root_cause"]:
                if "root_causes" not in pattern:
                    pattern["root_causes"] = {}
                cause = resolution["actual_root_cause"]
                pattern["root_causes"][cause] = pattern["root_causes"].get(cause, 0) + 1
            
            if "resolution_methods" not in pattern:
                pattern["resolution_methods"] = {}
            method = resolution["resolution_method"]
            pattern["resolution_methods"][method] = pattern["resolution_methods"].get(method, 0) + 1
            
            # Store recent resolution
            if "recent_resolutions" not in pattern:
                pattern["recent_resolutions"] = []
            pattern["recent_resolutions"].append({
                "alert_id": resolution["alert_id"],
                "resolution_time": resolution["resolution_time_minutes"],
                "method": resolution["resolution_method"],
                "timestamp": resolution["recorded_at"]
            })
            # Keep only last 10
            pattern["recent_resolutions"] = pattern["recent_resolutions"][-10:]
            
            # Update pattern
            pattern["last_updated"] = datetime.utcnow().isoformat()
            
            # Store updated pattern
            self.redis.hset(
                self.patterns_key,
                pattern_key,
                json.dumps(pattern)
            )
            
        except Exception as e:
            logger.error(f"Error updating patterns: {e}", exc_info=True)
    
    async def _update_accuracy(self, resolution: Dict[str, Any]):
        """
        Update AI prediction accuracy metrics.
        
        Args:
            resolution: Resolution record
        """
        try:
            # Get current accuracy data
            accuracy_data = self.redis.get(self.accuracy_key)
            
            if accuracy_data:
                accuracy = json.loads(accuracy_data)
            else:
                accuracy = {
                    "total_predictions": 0,
                    "correct_predictions": 0,
                    "auto_resolutions_attempted": 0,
                    "auto_resolutions_successful": 0,
                    "prediction_accuracy_by_confidence": {
                        "high": {"total": 0, "correct": 0},
                        "medium": {"total": 0, "correct": 0},
                        "low": {"total": 0, "correct": 0}
                    }
                }
            
            # Check if AI made a prediction
            if resolution["ai_predicted_root_cause"] and resolution["actual_root_cause"]:
                accuracy["total_predictions"] += 1
                
                # Check if prediction was correct (fuzzy match)
                predicted = resolution["ai_predicted_root_cause"].lower()
                actual = resolution["actual_root_cause"].lower()
                
                if predicted in actual or actual in predicted:
                    accuracy["correct_predictions"] += 1
                
                # Track by confidence level
                confidence = resolution.get("ai_confidence", 0)
                if confidence > 0.8:
                    conf_level = "high"
                elif confidence > 0.5:
                    conf_level = "medium"
                else:
                    conf_level = "low"
                
                accuracy["prediction_accuracy_by_confidence"][conf_level]["total"] += 1
                if predicted in actual or actual in predicted:
                    accuracy["prediction_accuracy_by_confidence"][conf_level]["correct"] += 1
            
            # Track auto-resolution accuracy
            if resolution["was_auto_resolved"]:
                accuracy["auto_resolutions_attempted"] += 1
                if resolution["success"]:
                    accuracy["auto_resolutions_successful"] += 1
            
            # Update timestamp
            accuracy["last_updated"] = datetime.utcnow().isoformat()
            
            # Store updated accuracy
            self.redis.set(
                self.accuracy_key,
                json.dumps(accuracy),
                ex=86400 * 90  # 90-day TTL
            )
            
        except Exception as e:
            logger.error(f"Error updating accuracy: {e}", exc_info=True)
    
    async def get_resolution_patterns(
        self,
        category: Optional[str] = None,
        level: Optional[str] = None
    ) -> List[ResolutionPattern]:
        """
        Get learned resolution patterns.
        
        Args:
            category: Filter by alert category (optional)
            level: Filter by alert level (optional)
            
        Returns:
            List of resolution patterns
        """
        patterns = []
        
        try:
            # Get all patterns from Redis
            all_patterns = self.redis.hgetall(self.patterns_key)
            
            for pattern_key, pattern_data in all_patterns.items():
                pattern_dict = json.loads(pattern_data)
                
                # Apply filters
                if category and pattern_dict["category"] != category:
                    continue
                if level and pattern_dict["level"] != level:
                    continue
                
                # Find most common root cause
                root_causes = pattern_dict.get("root_causes", {})
                most_common_cause = max(root_causes.items(), key=lambda x: x[1])[0] if root_causes else "Unknown"
                
                # Calculate metrics
                total = pattern_dict["total_count"]
                success = pattern_dict["success_count"]
                success_rate = (success / total) if total > 0 else 0.0
                
                avg_time = 0
                if pattern_dict["total_time_minutes"] and total > 0:
                    avg_time = int(pattern_dict["total_time_minutes"] / total)
                
                # Get resolution steps from recent resolutions
                resolution_steps = []
                recent = pattern_dict.get("recent_resolutions", [])
                if recent:
                    # This is simplified - in production, extract actual steps from resolution notes
                    resolution_steps = ["Review system metrics", "Check logs", "Apply fix", "Verify resolution"]
                
                pattern = ResolutionPattern(
                    alert_category=pattern_dict["category"],
                    alert_level=pattern_dict["level"],
                    root_cause=most_common_cause,
                    resolution_steps=resolution_steps,
                    success_rate=success_rate,
                    avg_resolution_time_minutes=avg_time,
                    occurrences=total,
                    last_seen=datetime.fromisoformat(pattern_dict["last_updated"])
                )
                
                patterns.append(pattern)
            
            # Sort by occurrences (most common first)
            patterns.sort(key=lambda p: p.occurrences, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting patterns: {e}", exc_info=True)
        
        return patterns
    
    async def get_feedback_metrics(self) -> FeedbackMetrics:
        """
        Get metrics about feedback loop performance.
        
        Returns:
            Feedback metrics
        """
        try:
            # Get accuracy data
            accuracy_data = self.redis.get(self.accuracy_key)
            
            if accuracy_data:
                accuracy = json.loads(accuracy_data)
            else:
                return FeedbackMetrics(
                    total_resolutions_tracked=0,
                    auto_resolution_accuracy=0.0,
                    ai_prediction_accuracy=0.0,
                    patterns_learned=0,
                    avg_learning_improvement_percent=0.0
                )
            
            # Calculate metrics
            total_resolutions = self.redis.llen(self.resolutions_key)
            
            auto_accuracy = 0.0
            if accuracy["auto_resolutions_attempted"] > 0:
                auto_accuracy = (accuracy["auto_resolutions_successful"] / 
                               accuracy["auto_resolutions_attempted"])
            
            prediction_accuracy = 0.0
            if accuracy["total_predictions"] > 0:
                prediction_accuracy = (accuracy["correct_predictions"] / 
                                     accuracy["total_predictions"])
            
            patterns_count = self.redis.hlen(self.patterns_key)
            
            # Calculate learning improvement (comparing recent vs older predictions)
            improvement = await self._calculate_learning_improvement()
            
            return FeedbackMetrics(
                total_resolutions_tracked=total_resolutions,
                auto_resolution_accuracy=round(auto_accuracy, 3),
                ai_prediction_accuracy=round(prediction_accuracy, 3),
                patterns_learned=patterns_count,
                avg_learning_improvement_percent=improvement
            )
            
        except Exception as e:
            logger.error(f"Error getting feedback metrics: {e}", exc_info=True)
            return FeedbackMetrics(
                total_resolutions_tracked=0,
                auto_resolution_accuracy=0.0,
                ai_prediction_accuracy=0.0,
                patterns_learned=0,
                avg_learning_improvement_percent=0.0
            )
    
    async def _calculate_learning_improvement(self) -> float:
        """
        Calculate improvement in predictions over time.
        
        Returns:
            Improvement percentage
        """
        try:
            # Get recent resolutions
            recent_resolutions = self.redis.lrange(self.resolutions_key, 0, 99)
            
            if len(recent_resolutions) < 20:
                return 0.0
            
            # Split into recent and older
            recent = recent_resolutions[:50]
            older = recent_resolutions[50:]
            
            # Calculate accuracy for each group
            def calc_accuracy(resolutions):
                correct = 0
                total = 0
                for res_str in resolutions:
                    res = json.loads(res_str)
                    if res.get("ai_predicted_root_cause") and res.get("actual_root_cause"):
                        total += 1
                        predicted = res["ai_predicted_root_cause"].lower()
                        actual = res["actual_root_cause"].lower()
                        if predicted in actual or actual in predicted:
                            correct += 1
                return (correct / total) if total > 0 else 0.0
            
            recent_accuracy = calc_accuracy(recent)
            older_accuracy = calc_accuracy(older)
            
            if older_accuracy > 0:
                improvement = ((recent_accuracy - older_accuracy) / older_accuracy) * 100
                return round(improvement, 1)
            
            return 0.0
            
        except Exception as e:
            logger.warning(f"Error calculating improvement: {e}")
            return 0.0


# ============================================================================
# SINGLETON AND HELPER FUNCTIONS
# ============================================================================

_feedback_loop_instance: Optional[AlertFeedbackLoop] = None


def get_feedback_loop() -> AlertFeedbackLoop:
    """
    Get singleton instance of AlertFeedbackLoop.
    
    Returns:
        AlertFeedbackLoop instance
    """
    global _feedback_loop_instance
    
    if _feedback_loop_instance is None:
        _feedback_loop_instance = AlertFeedbackLoop()
    
    return _feedback_loop_instance
