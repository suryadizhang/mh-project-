"""
Rule Evaluator - Threshold Monitoring Rule Evaluation Engine

Evaluates metrics against configured alert rules:
- Checks thresholds with various operators (>, <, >=, <=, ==, !=)
- Tracks duration requirements (must exceed for X seconds)
- Implements cooldown logic (prevents alert spam)
- Maintains rule violation state in Redis

Created: November 10, 2025
Part of: Week 2 - ThresholdMonitor Implementation
"""

import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import redis

from sqlalchemy.orm import Session

from core.config import settings
from .alert_rule_model import AlertRule, ThresholdOperator

logger = logging.getLogger(__name__)


class RuleViolation:
    """
    Represents a rule violation with state tracking.
    
    Tracks when a rule first started being violated and
    calculates if duration requirement is met.
    """
    
    def __init__(
        self,
        rule_id: int,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        operator: ThresholdOperator,
        first_exceeded_at: float,
        duration_required: int,
    ):
        """
        Initialize rule violation.
        
        Args:
            rule_id: ID of the rule
            metric_name: Name of the metric
            current_value: Current metric value
            threshold_value: Threshold value from rule
            operator: Comparison operator
            first_exceeded_at: Unix timestamp when first exceeded
            duration_required: Required duration in seconds
        """
        self.rule_id = rule_id
        self.metric_name = metric_name
        self.current_value = current_value
        self.threshold_value = threshold_value
        self.operator = operator
        self.first_exceeded_at = first_exceeded_at
        self.duration_required = duration_required
    
    @property
    def duration_exceeded(self) -> float:
        """Get duration exceeded in seconds."""
        return time.time() - self.first_exceeded_at
    
    @property
    def is_duration_met(self) -> bool:
        """Check if duration requirement is met."""
        return self.duration_exceeded >= self.duration_required
    
    @property
    def remaining_duration(self) -> float:
        """Get remaining duration before alert triggers."""
        return max(0, self.duration_required - self.duration_exceeded)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "operator": self.operator.value,
            "first_exceeded_at": self.first_exceeded_at,
            "duration_required": self.duration_required,
            "duration_exceeded": self.duration_exceeded,
            "is_duration_met": self.is_duration_met,
            "remaining_duration": self.remaining_duration,
        }


class RuleEvaluator:
    """
    Rule evaluation engine for threshold monitoring.
    
    Features:
    - Evaluates metrics against rules
    - Tracks violation duration
    - Implements cooldown logic
    - Prevents alert spam
    - State management in Redis
    
    Usage:
        evaluator = RuleEvaluator(db_session)
        
        # Check single metric
        violations = evaluator.evaluate_metric("cpu_percent", 85.5)
        
        # Check multiple metrics
        violations = evaluator.evaluate_metrics({
            "cpu_percent": 85.5,
            "memory_percent": 92.3,
        })
        
        # Get violations ready for alerting
        ready = evaluator.get_violations_ready_for_alert()
    """
    
    # Redis key prefixes
    VIOLATION_KEY_PREFIX = "rule:violation:"  # rule:violation:{rule_id}
    COOLDOWN_KEY_PREFIX = "rule:cooldown:"  # rule:cooldown:{rule_id}
    STATS_KEY = "rule:stats"  # Hash of rule statistics
    
    def __init__(
        self,
        db_session: Session,
        redis_client: Optional[redis.Redis] = None,
    ):
        """
        Initialize rule evaluator.
        
        Args:
            db_session: Database session
            redis_client: Redis client (optional)
        """
        self.db = db_session
        self.redis = redis_client or redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        # Cache of enabled rules (loaded once)
        self._rules_cache: Optional[List[AlertRule]] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 60  # Reload rules every 60 seconds
    
    def _get_enabled_rules(self, force_reload: bool = False) -> List[AlertRule]:
        """
        Get enabled rules with caching.
        
        Args:
            force_reload: Force reload from database
            
        Returns:
            List of enabled alert rules
        """
        current_time = time.time()
        
        # Check if cache is valid
        if (
            not force_reload
            and self._rules_cache is not None
            and self._cache_timestamp is not None
            and (current_time - self._cache_timestamp) < self._cache_ttl
        ):
            return self._rules_cache
        
        # Reload from database
        rules = self.db.query(AlertRule).filter(AlertRule.enabled == True).all()
        
        self._rules_cache = rules
        self._cache_timestamp = current_time
        
        logger.info(f"📚 Loaded {len(rules)} enabled alert rules")
        
        return rules
    
    def reload_rules(self):
        """Force reload rules from database."""
        self._get_enabled_rules(force_reload=True)
    
    def evaluate_metric(
        self,
        metric_name: str,
        value: float,
        timestamp: Optional[float] = None,
    ) -> List[RuleViolation]:
        """
        Evaluate a single metric against all applicable rules.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            List of rule violations
        """
        return self.evaluate_metrics({metric_name: value}, timestamp)
    
    def evaluate_metrics(
        self,
        metrics: Dict[str, float],
        timestamp: Optional[float] = None,
    ) -> List[RuleViolation]:
        """
        Evaluate multiple metrics against all applicable rules.
        
        Args:
            metrics: Dictionary of metric_name -> value
            timestamp: Optional timestamp (defaults to now)
            
        Returns:
            List of rule violations
        """
        if timestamp is None:
            timestamp = time.time()
        
        violations = []
        rules = self._get_enabled_rules()
        
        # Group rules by metric for efficiency
        rules_by_metric: Dict[str, List[AlertRule]] = {}
        for rule in rules:
            if rule.metric_name not in rules_by_metric:
                rules_by_metric[rule.metric_name] = []
            rules_by_metric[rule.metric_name].append(rule)
        
        # Evaluate each metric
        for metric_name, value in metrics.items():
            if metric_name not in rules_by_metric:
                continue
            
            for rule in rules_by_metric[metric_name]:
                violation = self._evaluate_rule(rule, value, timestamp)
                if violation:
                    violations.append(violation)
        
        return violations
    
    def _evaluate_rule(
        self,
        rule: AlertRule,
        value: float,
        timestamp: float,
    ) -> Optional[RuleViolation]:
        """
        Evaluate a single rule against a metric value.
        
        Args:
            rule: Alert rule
            value: Metric value
            timestamp: Timestamp
            
        Returns:
            RuleViolation if rule is violated, None otherwise
        """
        # Check if value violates threshold
        is_violated = self._check_threshold(
            value,
            rule.threshold_value,
            rule.operator
        )
        
        violation_key = f"{self.VIOLATION_KEY_PREFIX}{rule.id}"
        
        if is_violated:
            # Threshold is violated
            
            # Check if this is a new violation or continuing
            existing_violation_data = self.redis.get(violation_key)
            
            if existing_violation_data:
                # Continuing violation - parse existing data
                try:
                    first_exceeded_at = float(existing_violation_data)
                except (ValueError, TypeError):
                    # Invalid data, treat as new violation
                    first_exceeded_at = timestamp
                    self.redis.setex(violation_key, 3600, first_exceeded_at)  # 1 hour TTL
            else:
                # New violation - record start time
                first_exceeded_at = timestamp
                self.redis.setex(violation_key, 3600, first_exceeded_at)  # 1 hour TTL
                
                logger.info(
                    f"⚠️ Rule violation started: {rule.name} "
                    f"({rule.metric_name} = {value}, threshold: {rule.operator.value} {rule.threshold_value})"
                )
            
            # Create violation object
            violation = RuleViolation(
                rule_id=rule.id,
                metric_name=rule.metric_name,
                current_value=value,
                threshold_value=rule.threshold_value,
                operator=rule.operator,
                first_exceeded_at=first_exceeded_at,
                duration_required=rule.duration_seconds,
            )
            
            # Update statistics
            self._update_violation_stats(rule.id, timestamp)
            
            return violation
        
        else:
            # Threshold is not violated
            
            # Clear violation if it exists
            if self.redis.exists(violation_key):
                self.redis.delete(violation_key)
                logger.info(f"✅ Rule violation cleared: {rule.name}")
            
            return None
    
    def _check_threshold(
        self,
        value: float,
        threshold: float,
        operator: ThresholdOperator,
    ) -> bool:
        """
        Check if value violates threshold.
        
        Args:
            value: Current value
            threshold: Threshold value
            operator: Comparison operator
            
        Returns:
            True if threshold is violated
        """
        if operator == ThresholdOperator.GREATER_THAN:
            return value > threshold
        elif operator == ThresholdOperator.GREATER_THAN_OR_EQUAL:
            return value >= threshold
        elif operator == ThresholdOperator.LESS_THAN:
            return value < threshold
        elif operator == ThresholdOperator.LESS_THAN_OR_EQUAL:
            return value <= threshold
        elif operator == ThresholdOperator.EQUAL:
            return abs(value - threshold) < 0.0001  # Float equality with tolerance
        elif operator == ThresholdOperator.NOT_EQUAL:
            return abs(value - threshold) >= 0.0001
        else:
            logger.error(f"Unknown operator: {operator}")
            return False
    
    def get_violations_ready_for_alert(self) -> List[Tuple[AlertRule, RuleViolation]]:
        """
        Get violations that are ready to trigger alerts.
        
        A violation is ready if:
        1. Duration requirement is met
        2. Not in cooldown period
        
        Returns:
            List of (rule, violation) tuples ready for alerting
        """
        ready_violations = []
        rules = self._get_enabled_rules()
        
        for rule in rules:
            violation_key = f"{self.VIOLATION_KEY_PREFIX}{rule.id}"
            violation_data = self.redis.get(violation_key)
            
            if not violation_data:
                continue  # No active violation
            
            try:
                first_exceeded_at = float(violation_data)
            except (ValueError, TypeError):
                continue  # Invalid data
            
            # Check duration requirement
            duration_exceeded = time.time() - first_exceeded_at
            if duration_exceeded < rule.duration_seconds:
                # Duration not met yet
                logger.debug(
                    f"⏳ Rule {rule.name}: waiting for duration "
                    f"({duration_exceeded:.0f}s / {rule.duration_seconds}s)"
                )
                continue
            
            # Check cooldown
            if self._is_in_cooldown(rule.id):
                logger.debug(f"❄️ Rule {rule.name}: in cooldown")
                continue
            
            # Get current value (fetch from Redis metric store)
            current_value = self._get_current_metric_value(rule.metric_name)
            if current_value is None:
                logger.warning(f"⚠️ No current value for {rule.metric_name}")
                continue
            
            # Re-check threshold (metric might have recovered)
            if not self._check_threshold(current_value, rule.threshold_value, rule.operator):
                # Metric recovered, clear violation
                self.redis.delete(violation_key)
                logger.info(f"✅ Metric recovered: {rule.metric_name}")
                continue
            
            # Create violation object
            violation = RuleViolation(
                rule_id=rule.id,
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold_value=rule.threshold_value,
                operator=rule.operator,
                first_exceeded_at=first_exceeded_at,
                duration_required=rule.duration_seconds,
            )
            
            ready_violations.append((rule, violation))
        
        return ready_violations
    
    def _is_in_cooldown(self, rule_id: int) -> bool:
        """
        Check if rule is in cooldown period.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            True if in cooldown
        """
        cooldown_key = f"{self.COOLDOWN_KEY_PREFIX}{rule_id}"
        return self.redis.exists(cooldown_key)
    
    def start_cooldown(self, rule_id: int, cooldown_seconds: int):
        """
        Start cooldown period for a rule.
        
        Args:
            rule_id: Rule ID
            cooldown_seconds: Cooldown duration in seconds
        """
        cooldown_key = f"{self.COOLDOWN_KEY_PREFIX}{rule_id}"
        self.redis.setex(cooldown_key, cooldown_seconds, time.time())
        logger.info(f"❄️ Started cooldown for rule {rule_id} ({cooldown_seconds}s)")
    
    def clear_violation(self, rule_id: int):
        """
        Clear violation state for a rule.
        
        Args:
            rule_id: Rule ID
        """
        violation_key = f"{self.VIOLATION_KEY_PREFIX}{rule_id}"
        self.redis.delete(violation_key)
        logger.info(f"🗑️ Cleared violation for rule {rule_id}")
    
    def clear_cooldown(self, rule_id: int):
        """
        Clear cooldown for a rule.
        
        Args:
            rule_id: Rule ID
        """
        cooldown_key = f"{self.COOLDOWN_KEY_PREFIX}{rule_id}"
        self.redis.delete(cooldown_key)
        logger.info(f"🗑️ Cleared cooldown for rule {rule_id}")
    
    def _get_current_metric_value(self, metric_name: str) -> Optional[float]:
        """
        Get current value of a metric from Redis.
        
        Args:
            metric_name: Name of the metric
            
        Returns:
            Current value or None
        """
        metric_key = f"metric:{metric_name}"
        value_str = self.redis.get(metric_key)
        
        if value_str:
            try:
                return float(value_str)
            except (ValueError, TypeError):
                return None
        
        return None
    
    def _update_violation_stats(self, rule_id: int, timestamp: float):
        """
        Update violation statistics.
        
        Args:
            rule_id: Rule ID
            timestamp: Timestamp
        """
        # Track violation count
        count_key = f"violation_count_{rule_id}"
        self.redis.hincrby(self.STATS_KEY, count_key, 1)
        
        # Track last violation time
        time_key = f"last_violation_{rule_id}"
        self.redis.hset(self.STATS_KEY, time_key, timestamp)
    
    def get_rule_stats(self, rule_id: int) -> Dict[str, Any]:
        """
        Get statistics for a rule.
        
        Args:
            rule_id: Rule ID
            
        Returns:
            Dictionary with statistics
        """
        count_key = f"violation_count_{rule_id}"
        time_key = f"last_violation_{rule_id}"
        
        count = self.redis.hget(self.STATS_KEY, count_key)
        last_time = self.redis.hget(self.STATS_KEY, time_key)
        
        violation_key = f"{self.VIOLATION_KEY_PREFIX}{rule_id}"
        is_violated = self.redis.exists(violation_key)
        
        cooldown_key = f"{self.COOLDOWN_KEY_PREFIX}{rule_id}"
        in_cooldown = self.redis.exists(cooldown_key)
        cooldown_ttl = self.redis.ttl(cooldown_key) if in_cooldown else 0
        
        return {
            "rule_id": rule_id,
            "violation_count": int(count) if count else 0,
            "last_violation_time": float(last_time) if last_time else None,
            "is_currently_violated": bool(is_violated),
            "in_cooldown": bool(in_cooldown),
            "cooldown_remaining_seconds": cooldown_ttl if cooldown_ttl > 0 else 0,
        }
    
    def get_all_violations(self) -> List[RuleViolation]:
        """
        Get all active violations (regardless of duration/cooldown).
        
        Returns:
            List of all active violations
        """
        violations = []
        rules = self._get_enabled_rules()
        
        for rule in rules:
            violation_key = f"{self.VIOLATION_KEY_PREFIX}{rule.id}"
            violation_data = self.redis.get(violation_key)
            
            if not violation_data:
                continue
            
            try:
                first_exceeded_at = float(violation_data)
            except (ValueError, TypeError):
                continue
            
            # Get current value
            current_value = self._get_current_metric_value(rule.metric_name)
            if current_value is None:
                continue
            
            violation = RuleViolation(
                rule_id=rule.id,
                metric_name=rule.metric_name,
                current_value=current_value,
                threshold_value=rule.threshold_value,
                operator=rule.operator,
                first_exceeded_at=first_exceeded_at,
                duration_required=rule.duration_seconds,
            )
            
            violations.append(violation)
        
        return violations


# Singleton instance for global access
_rule_evaluator_instance: Optional[RuleEvaluator] = None


def get_rule_evaluator(
    db_session: Session,
    redis_client: Optional[redis.Redis] = None,
) -> RuleEvaluator:
    """
    Get RuleEvaluator instance.
    
    Note: Not a true singleton since it depends on db_session.
    Creates new instance each time.
    
    Args:
        db_session: Database session
        redis_client: Optional Redis client
        
    Returns:
        RuleEvaluator instance
    """
    return RuleEvaluator(db_session=db_session, redis_client=redis_client)
