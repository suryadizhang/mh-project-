"""
Monitoring State Machine

Activity-based wake/sleep system for efficient monitoring.
Like a gun trigger - activity pulls the trigger, monitoring fires.

States:
- IDLE: Sleeping, only critical checks (every 5 minutes)
- ACTIVE: Awake, full monitoring (activity detected)
- ALERT: Alert state, aggressive monitoring (threshold exceeded)

Transitions:
- IDLE → ACTIVE: When API activity detected (middleware trigger)
- ACTIVE → IDLE: After 15 minutes of inactivity
- ACTIVE → ALERT: When threshold exceeded
- ALERT → ACTIVE: When issue resolved
- ALERT → IDLE: After resolved + 15 min inactivity

Created: November 10, 2025
Part of: Week 2 - ThresholdMonitor Implementation
"""

import time
import logging
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import redis

from core.config import settings
from .metric_collector import MetricCollector

logger = logging.getLogger(__name__)


class MonitoringStateEnum(str, Enum):
    """Monitoring states"""
    IDLE = "IDLE"           # Sleeping, minimal checks
    ACTIVE = "ACTIVE"       # Awake, full monitoring
    ALERT = "ALERT"         # Alert state, aggressive monitoring


class MonitoringState:
    """
    State machine for activity-based monitoring.
    
    Manages transitions between IDLE, ACTIVE, and ALERT states
    based on API activity and threshold violations.
    
    Usage:
        state_machine = MonitoringState()
        
        # Check current state
        current = state_machine.get_current_state()
        
        # Check if should transition
        state_machine.check_and_transition()
        
        # Get monitoring interval
        interval = state_machine.get_check_interval()
    """
    
    # State transition thresholds
    IDLE_TIMEOUT = 900  # 15 minutes of inactivity → IDLE
    ALERT_RESOLUTION_TIMEOUT = 900  # 15 minutes after resolution → can go IDLE
    
    # Check intervals for each state
    IDLE_CHECK_INTERVAL = 300  # 5 minutes (critical only)
    ACTIVE_CHECK_INTERVAL = 120  # 2 minutes (full monitoring)
    ALERT_CHECK_INTERVAL = 15  # 15 seconds (aggressive)
    
    # Redis keys
    STATE_KEY = "monitor:state"
    LAST_ACTIVITY_KEY = "monitor:last_activity"
    LAST_ALERT_KEY = "monitor:last_alert"
    ALERT_RESOLVED_KEY = "monitor:alert_resolved_at"
    STATE_HISTORY_KEY = "monitor:state_history"
    STATE_STATS_KEY = "monitor:state_stats"
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        Initialize monitoring state machine.
        
        Args:
            redis_client: Redis client (optional, will create if not provided)
        """
        self.redis = redis_client or redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        self.metric_collector = MetricCollector(redis_client=self.redis)
        
        # Initialize state if not exists
        if not self.redis.exists(self.STATE_KEY):
            self._set_state(MonitoringStateEnum.IDLE, "initialization")
            logger.info("🔧 Initialized monitoring state: IDLE")
    
    def get_current_state(self) -> MonitoringStateEnum:
        """
        Get current monitoring state.
        
        Returns:
            Current state (IDLE, ACTIVE, or ALERT)
        """
        state_str = self.redis.get(self.STATE_KEY)
        if not state_str:
            return MonitoringStateEnum.IDLE
        
        try:
            return MonitoringStateEnum(state_str.decode() if isinstance(state_str, bytes) else state_str)
        except ValueError:
            logger.warning(f"Invalid state in Redis: {state_str}, defaulting to IDLE")
            return MonitoringStateEnum.IDLE
    
    def get_check_interval(self) -> int:
        """
        Get appropriate check interval for current state.
        
        Returns:
            Check interval in seconds
        """
        state = self.get_current_state()
        
        if state == MonitoringStateEnum.IDLE:
            return self.IDLE_CHECK_INTERVAL
        elif state == MonitoringStateEnum.ACTIVE:
            return self.ACTIVE_CHECK_INTERVAL
        elif state == MonitoringStateEnum.ALERT:
            return self.ALERT_CHECK_INTERVAL
        else:
            return self.ACTIVE_CHECK_INTERVAL
    
    def wake(self, reason: str = "activity_detected") -> bool:
        """
        Wake monitoring (IDLE → ACTIVE).
        Called by middleware when activity detected.
        
        Args:
            reason: Reason for waking
            
        Returns:
            True if state changed, False if already awake
        """
        current_state = self.get_current_state()
        
        # Update last activity timestamp
        self.redis.setex(
            self.LAST_ACTIVITY_KEY,
            self.IDLE_TIMEOUT,
            time.time()
        )
        
        # If already ACTIVE or ALERT, just update activity timestamp
        if current_state in [MonitoringStateEnum.ACTIVE, MonitoringStateEnum.ALERT]:
            return False
        
        # Transition IDLE → ACTIVE
        self._set_state(MonitoringStateEnum.ACTIVE, reason)
        logger.info(f"🔫 WAKE: IDLE → ACTIVE ({reason})")
        return True
    
    def enter_alert_state(self, alert_id: int, reason: str = "threshold_exceeded") -> bool:
        """
        Enter alert state (ACTIVE → ALERT).
        Called when threshold exceeded.
        
        Args:
            alert_id: ID of the alert that triggered this
            reason: Reason for alert
            
        Returns:
            True if state changed, False if already in ALERT
        """
        current_state = self.get_current_state()
        
        # Store alert info
        self.redis.setex(
            self.LAST_ALERT_KEY,
            86400,  # 24 hours
            alert_id
        )
        
        # Clear resolution timestamp
        self.redis.delete(self.ALERT_RESOLVED_KEY)
        
        # If already in ALERT, just update alert ID
        if current_state == MonitoringStateEnum.ALERT:
            return False
        
        # Transition to ALERT
        self._set_state(MonitoringStateEnum.ALERT, reason)
        logger.warning(f"🚨 ALERT: {current_state.value} → ALERT ({reason})")
        return True
    
    def resolve_alert(self) -> bool:
        """
        Mark alert as resolved.
        Sets timestamp but doesn't transition state immediately.
        State will transition after ALERT_RESOLUTION_TIMEOUT.
        
        Returns:
            True if marked as resolved
        """
        current_state = self.get_current_state()
        
        if current_state != MonitoringStateEnum.ALERT:
            return False
        
        # Mark resolution time
        self.redis.setex(
            self.ALERT_RESOLVED_KEY,
            self.ALERT_RESOLUTION_TIMEOUT * 2,  # Keep for 10 minutes
            time.time()
        )
        
        logger.info("✅ Alert resolved, will transition after timeout")
        return True
    
    def check_and_transition(self) -> Optional[Tuple[MonitoringStateEnum, MonitoringStateEnum]]:
        """
        Check if state should transition and perform transition if needed.
        
        Should be called periodically by monitoring loop.
        
        Returns:
            Tuple of (old_state, new_state) if transitioned, None otherwise
        """
        current_state = self.get_current_state()
        current_time = time.time()
        
        # Get last activity
        last_activity_str = self.redis.get(self.LAST_ACTIVITY_KEY)
        last_activity = float(last_activity_str) if last_activity_str else 0
        time_since_activity = current_time - last_activity if last_activity else float('inf')
        
        # ALERT state handling
        if current_state == MonitoringStateEnum.ALERT:
            # Check if alert resolved
            resolved_at_str = self.redis.get(self.ALERT_RESOLVED_KEY)
            
            if resolved_at_str:
                resolved_at = float(resolved_at_str)
                time_since_resolution = current_time - resolved_at
                
                # Check if should go to IDLE (resolved + no activity)
                if time_since_resolution >= self.ALERT_RESOLUTION_TIMEOUT:
                    if time_since_activity >= self.IDLE_TIMEOUT:
                        # ALERT → IDLE (resolved + inactive)
                        self._set_state(MonitoringStateEnum.IDLE, "alert_resolved_and_inactive")
                        logger.info("😴 SLEEP: ALERT → IDLE (resolved + inactive)")
                        return (current_state, MonitoringStateEnum.IDLE)
                    else:
                        # ALERT → ACTIVE (resolved but still active)
                        self._set_state(MonitoringStateEnum.ACTIVE, "alert_resolved_but_active")
                        logger.info("✅ ACTIVE: ALERT → ACTIVE (resolved)")
                        return (current_state, MonitoringStateEnum.ACTIVE)
        
        # ACTIVE state handling
        elif current_state == MonitoringStateEnum.ACTIVE:
            # Check if should go to IDLE (no activity)
            if time_since_activity >= self.IDLE_TIMEOUT:
                self._set_state(MonitoringStateEnum.IDLE, "inactivity_timeout")
                logger.info("😴 SLEEP: ACTIVE → IDLE (15min inactivity)")
                return (current_state, MonitoringStateEnum.IDLE)
        
        # No transition
        return None
    
    def force_state(self, state: MonitoringStateEnum, reason: str = "manual_override") -> bool:
        """
        Force state transition (for testing/manual control).
        
        Args:
            state: Target state
            reason: Reason for transition
            
        Returns:
            True if state changed
        """
        current_state = self.get_current_state()
        
        if current_state == state:
            return False
        
        self._set_state(state, reason)
        logger.warning(f"⚠️ FORCE: {current_state.value} → {state.value} ({reason})")
        return True
    
    def _set_state(self, state: MonitoringStateEnum, reason: str):
        """
        Internal method to set state and record history.
        
        Args:
            state: New state
            reason: Reason for transition
        """
        old_state = self.get_current_state()
        
        # Set new state
        self.redis.set(self.STATE_KEY, state.value)
        
        # Record in history (last 1000 transitions)
        history_entry = {
            "timestamp": time.time(),
            "from_state": old_state.value,
            "to_state": state.value,
            "reason": reason
        }
        
        self.redis.lpush(
            self.STATE_HISTORY_KEY,
            str(history_entry)
        )
        self.redis.ltrim(self.STATE_HISTORY_KEY, 0, 999)  # Keep last 1000
        
        # Update statistics
        self._update_state_stats(old_state, state)
    
    def _update_state_stats(self, old_state: MonitoringStateEnum, new_state: MonitoringStateEnum):
        """
        Update state transition statistics.
        
        Args:
            old_state: Previous state
            new_state: New state
        """
        # Increment transition counter
        transition_key = f"{old_state.value}_to_{new_state.value}"
        self.redis.hincrby(self.STATE_STATS_KEY, transition_key, 1)
        
        # Update state duration (time spent in old state)
        # This is approximate - based on when transitions happen
        last_transition_key = f"last_transition_{old_state.value}"
        last_transition_str = self.redis.hget(self.STATE_STATS_KEY, last_transition_key)
        
        if last_transition_str:
            last_transition = float(last_transition_str)
            duration = time.time() - last_transition
            
            # Add to total duration
            duration_key = f"total_duration_{old_state.value}"
            current_duration = float(self.redis.hget(self.STATE_STATS_KEY, duration_key) or 0)
            self.redis.hset(self.STATE_STATS_KEY, duration_key, current_duration + duration)
        
        # Update last transition time for new state
        self.redis.hset(
            self.STATE_STATS_KEY,
            f"last_transition_{new_state.value}",
            time.time()
        )
    
    def get_state_info(self) -> Dict[str, Any]:
        """
        Get comprehensive state information.
        
        Returns:
            Dictionary with current state, timings, and metadata
        """
        current_state = self.get_current_state()
        current_time = time.time()
        
        # Last activity
        last_activity_str = self.redis.get(self.LAST_ACTIVITY_KEY)
        last_activity = float(last_activity_str) if last_activity_str else None
        time_since_activity = current_time - last_activity if last_activity else None
        
        # Last alert
        last_alert_str = self.redis.get(self.LAST_ALERT_KEY)
        last_alert_id = int(last_alert_str) if last_alert_str else None
        
        # Alert resolution
        resolved_at_str = self.redis.get(self.ALERT_RESOLVED_KEY)
        resolved_at = float(resolved_at_str) if resolved_at_str else None
        time_since_resolution = current_time - resolved_at if resolved_at else None
        
        return {
            "current_state": current_state.value,
            "check_interval": self.get_check_interval(),
            "last_activity_timestamp": last_activity,
            "time_since_activity_seconds": time_since_activity,
            "last_alert_id": last_alert_id,
            "alert_resolved_at": resolved_at,
            "time_since_resolution_seconds": time_since_resolution,
            "will_sleep_in_seconds": (
                self.IDLE_TIMEOUT - time_since_activity
                if time_since_activity and time_since_activity < self.IDLE_TIMEOUT
                else None
            ),
            "timestamp": current_time,
        }
    
    def get_state_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get state transition history.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of transition records
        """
        history = self.redis.lrange(self.STATE_HISTORY_KEY, 0, limit - 1)
        
        result = []
        for entry_str in history:
            try:
                # Parse the string representation back to dict
                entry = eval(entry_str.decode() if isinstance(entry_str, bytes) else entry_str)
                result.append(entry)
            except Exception as e:
                logger.error(f"Failed to parse history entry: {e}")
        
        return result
    
    def get_state_statistics(self) -> Dict[str, Any]:
        """
        Get state transition statistics.
        
        Returns:
            Statistics about state transitions and durations
        """
        stats_raw = self.redis.hgetall(self.STATE_STATS_KEY)
        
        stats = {}
        for key, value in stats_raw.items():
            key_str = key.decode() if isinstance(key, bytes) else key
            value_str = value.decode() if isinstance(value, bytes) else value
            
            try:
                # Try to parse as number
                stats[key_str] = float(value_str) if '.' in value_str else int(value_str)
            except ValueError:
                stats[key_str] = value_str
        
        # Calculate percentages and averages
        total_transitions = sum(
            v for k, v in stats.items()
            if k.endswith("_to_IDLE") or k.endswith("_to_ACTIVE") or k.endswith("_to_ALERT")
        )
        
        # Add readable durations
        for state in ["IDLE", "ACTIVE", "ALERT"]:
            duration_key = f"total_duration_{state}"
            if duration_key in stats:
                total_seconds = stats[duration_key]
                stats[f"{duration_key}_hours"] = round(total_seconds / 3600, 2)
        
        stats["total_transitions"] = total_transitions
        
        return stats
    
    def should_collect_full_metrics(self) -> bool:
        """
        Check if should collect full metrics or only critical ones.
        
        Returns:
            True if should collect full metrics (ACTIVE or ALERT)
            False if should only collect critical metrics (IDLE)
        """
        state = self.get_current_state()
        return state in [MonitoringStateEnum.ACTIVE, MonitoringStateEnum.ALERT]
    
    def collect_metrics(self) -> Dict[str, float]:
        """
        Collect appropriate metrics based on current state.
        
        In IDLE state: Only critical metrics (lightweight)
        In ACTIVE/ALERT state: All metrics (comprehensive)
        
        Returns:
            Dictionary of collected metrics
        """
        if self.should_collect_full_metrics():
            logger.debug(f"Collecting full metrics ({self.get_current_state().value} state)")
            return self.metric_collector.collect_all_metrics()
        else:
            logger.debug("Collecting critical metrics only (IDLE state)")
            return self.metric_collector.collect_critical_metrics_only()


# Singleton instance for global access
_monitoring_state_instance: Optional[MonitoringState] = None


def get_monitoring_state(redis_client: Optional[redis.Redis] = None) -> MonitoringState:
    """
    Get singleton MonitoringState instance.
    
    Args:
        redis_client: Optional Redis client
        
    Returns:
        MonitoringState instance
    """
    global _monitoring_state_instance
    
    if _monitoring_state_instance is None:
        _monitoring_state_instance = MonitoringState(redis_client=redis_client)
    
    return _monitoring_state_instance


def reset_monitoring_state():
    """Reset singleton (for testing)."""
    global _monitoring_state_instance
    _monitoring_state_instance = None
