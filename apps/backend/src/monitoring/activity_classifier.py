"""
Smart Activity Classifier - Hybrid Route + Anomaly Detection

Determines if API activity should trigger monitoring system.

3-tier classification:
1. ALWAYS IGNORE - Health checks, monitoring endpoints
2. ALWAYS WAKE - Critical user actions, admin operations  
3. SMART DECISION - Pattern analysis for ambiguous cases

Action-based alert viewing:
- GET /api/alerts = viewing (don't wake)
- POST/PATCH /api/alerts = action (wake!)
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import redis
from fastapi import Request

from core.config import settings

logger = logging.getLogger(__name__)


class SmartActivityClassifier:
    """
    Hybrid activity classification using route patterns + anomaly detection
    
    Features:
    - Route-based classification (explicit wake/ignore lists)
    - Method-based classification (writes = activity)
    - Time-based anomaly detection (unusual hours)
    - Frequency-based anomaly detection (traffic spikes)
    - Pattern learning (baseline establishment)
    """
    
    # ========================================================================
    # TIER 1: ALWAYS IGNORE (Never wake monitor)
    # ========================================================================
    
    ALWAYS_IGNORE = [
        # Health checks
        "/health",
        "/api/health/live",
        "/api/health/ready",
        "/api/health/startup",
        "/ready",
        "/startup",
        
        # Monitoring endpoints
        "/metrics",
        "/api/monitoring/status",
        
        # Static assets
        "/static/",
        "/favicon.ico",
        "/robots.txt",
        
        # Internal cron/scheduled tasks
        "/api/internal/cron",
        "/api/internal/scheduled",
    ]
    
    # ========================================================================
    # TIER 2: ALWAYS WAKE (Critical user actions)
    # ========================================================================
    
    ALWAYS_WAKE = [
        # User-facing actions
        "/api/bookings",
        "/api/payments",
        "/api/customers",
        "/api/menu",
        "/api/contact",
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/logout",
        "/api/orders",
        
        # Admin operations
        "/api/admin/",
        "/api/dashboard/",
        
        # Critical webhooks
        "/api/webhooks/",
        "/api/stripe/webhook",
        "/api/twilio/webhook",
    ]
    
    # ========================================================================
    # TIER 2.5: ACTION-BASED (Viewing = don't wake, Actions = wake)
    # ========================================================================
    
    ACTION_BASED_PATHS = {
        "/api/alerts": {
            "wake_methods": ["POST", "PATCH", "PUT", "DELETE"],  # Actions wake
            "ignore_methods": ["GET", "HEAD"],                    # Viewing doesn't wake
            "reason_wake": "alert_action",
            "reason_ignore": "viewing_alerts",
        },
        "/api/monitoring/alerts": {
            "wake_methods": ["POST", "PATCH", "PUT", "DELETE"],
            "ignore_methods": ["GET", "HEAD"],
            "reason_wake": "alert_action",
            "reason_ignore": "viewing_alerts",
        },
        "/api/monitoring/rules": {
            "wake_methods": ["POST", "PATCH", "PUT", "DELETE"],
            "ignore_methods": ["GET", "HEAD"],
            "reason_wake": "rule_management",
            "reason_ignore": "viewing_rules",
        },
    }
    
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    def should_wake(self, request: Request) -> Tuple[bool, str]:
        """
        Determine if request should wake monitoring system
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Tuple of (should_wake: bool, reason: str)
            
        Examples:
            (True, "critical_user_action")  # Wake for booking
            (False, "routine_monitoring")    # Don't wake for health check
            (True, "alert_action")           # Wake for acknowledging alert
            (False, "viewing_alerts")        # Don't wake for viewing alerts
        """
        path = request.url.path
        method = request.method
        
        # ====================================================================
        # TIER 1: Always ignore (highest priority)
        # ====================================================================
        
        if any(path.startswith(ignore) for ignore in self.ALWAYS_IGNORE):
            return False, "routine_monitoring"
        
        # ====================================================================
        # TIER 2: Always wake for critical actions
        # ====================================================================
        
        if any(path.startswith(wake) for wake in self.ALWAYS_WAKE):
            return True, "critical_user_action"
        
        # ====================================================================
        # TIER 2.5: Action-based (viewing vs actions)
        # ====================================================================
        
        for action_path, config in self.ACTION_BASED_PATHS.items():
            if path.startswith(action_path):
                if method in config["wake_methods"]:
                    # Action on alert/rule - WAKE!
                    return True, config["reason_wake"]
                elif method in config["ignore_methods"]:
                    # Just viewing - don't wake
                    return False, config["reason_ignore"]
        
        # ====================================================================
        # TIER 3: Smart decision (analyze patterns)
        # ====================================================================
        
        return self._analyze_pattern(request)
    
    def log_wake_event(self, request: Request, reason: str):
        """
        Log wake event for analysis
        
        Args:
            request: FastAPI Request object
            reason: Wake reason
        """
        try:
            wake_data = {
                "timestamp": time.time(),
                "path": request.url.path,
                "method": request.method,
                "reason": reason,
                "hour": datetime.now().hour,
            }
            
            # Add to wake log (keep last 1000 events)
            self.redis.lpush("monitor:wake_log", json.dumps(wake_data))
            self.redis.ltrim("monitor:wake_log", 0, 999)
            
            # Update hourly pattern
            hour_key = f"traffic:hours:{request.url.path}"
            self.redis.sadd(hour_key, str(datetime.now().hour))
            self.redis.expire(hour_key, 604800)  # 7 days
            
        except Exception as e:
            logger.error(f"Error logging wake event: {e}")
    
    # ========================================================================
    # PATTERN ANALYSIS
    # ========================================================================
    
    def _analyze_pattern(self, request: Request) -> Tuple[bool, str]:
        """
        Analyze request patterns to determine if should wake
        
        Uses multiple heuristics:
        1. Write operations = wake
        2. First request in 10 minutes = wake
        3. Unusual endpoint at unusual hour = wake
        4. High frequency (3x baseline) = wake
        5. Default: Don't wake for routine reads
        
        Args:
            request: FastAPI Request object
            
        Returns:
            Tuple of (should_wake: bool, reason: str)
        """
        path = request.url.path
        method = request.method
        hour = datetime.now().hour
        
        # ====================================================================
        # Heuristic 1: Write operations = activity
        # ====================================================================
        
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            return True, "write_operation"
        
        # ====================================================================
        # Heuristic 2: First request in 10 minutes = wake up
        # ====================================================================
        
        last_request_key = "traffic:last_request"
        last_request = self.redis.get(last_request_key)
        
        if not last_request or (time.time() - float(last_request)) > 600:
            # First request in 10+ minutes
            self.redis.set(last_request_key, time.time())
            return True, "first_request_in_10min"
        
        # Update last request time
        self.redis.set(last_request_key, time.time())
        
        # ====================================================================
        # Heuristic 3: Unusual endpoint at unusual hour = anomaly
        # ====================================================================
        
        hour_key = f"traffic:hours:{path}"
        typical_hours = self.redis.smembers(hour_key)
        
        if typical_hours and str(hour) not in typical_hours:
            # This endpoint not normally called at this hour
            return True, f"unusual_time:hour_{hour}"
        
        # ====================================================================
        # Heuristic 4: High frequency = traffic spike = anomaly
        # ====================================================================
        
        rate_key = f"traffic:rate:{path}:minute"
        current_rate = self.redis.incr(rate_key)
        self.redis.expire(rate_key, 60)
        
        baseline_key = f"traffic:baseline:{path}"
        baseline = float(self.redis.get(baseline_key) or 10)
        
        if current_rate > baseline * 3:
            # 3x normal rate = anomaly/attack
            return True, f"high_frequency:{current_rate}>{baseline*3:.0f}"
        
        # ====================================================================
        # Heuristic 5: Admin endpoints = wake (even for GET)
        # ====================================================================
        
        if "/admin" in path or "/dashboard" in path:
            return True, "admin_access"
        
        # ====================================================================
        # Default: Routine read, don't wake
        # ====================================================================
        
        return False, "routine_read"
    
    # ========================================================================
    # BASELINE MANAGEMENT
    # ========================================================================
    
    def update_baseline(self, path: str):
        """
        Update baseline traffic rate for an endpoint
        
        Should be called periodically (e.g., daily) to learn normal patterns
        
        Args:
            path: Endpoint path
        """
        try:
            # Get historical request rates from last 7 days
            history_key = f"traffic:history:{path}"
            history = self.redis.lrange(history_key, 0, -1)
            
            if history:
                rates = [float(r) for r in history]
                avg_rate = sum(rates) / len(rates)
                
                baseline_key = f"traffic:baseline:{path}"
                self.redis.setex(baseline_key, 604800, str(avg_rate))  # 7 days TTL
                
                logger.info(f"Updated baseline for {path}: {avg_rate:.2f} req/min")
        
        except Exception as e:
            logger.error(f"Error updating baseline for {path}: {e}")
    
    def update_all_baselines(self):
        """Update baselines for all tracked endpoints"""
        try:
            # Get all tracked paths
            pattern = "traffic:rate:*"
            keys = self.redis.keys(pattern)
            
            paths = set()
            for key in keys:
                # Extract path from key: traffic:rate:/api/bookings:minute
                parts = key.split(":")
                if len(parts) >= 3:
                    path = ":".join(parts[2:-1])  # Handle paths with colons
                    paths.add(path)
            
            # Update baseline for each path
            for path in paths:
                self.update_baseline(path)
            
            logger.info(f"Updated baselines for {len(paths)} endpoints")
            
        except Exception as e:
            logger.error(f"Error updating all baselines: {e}")
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_wake_statistics(self, hours: int = 24) -> Dict[str, any]:
        """
        Get wake event statistics
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary of statistics
        """
        try:
            # Get wake log
            wake_log = self.redis.lrange("monitor:wake_log", 0, -1)
            
            cutoff_time = time.time() - (hours * 3600)
            recent_wakes = []
            
            for entry in wake_log:
                data = json.loads(entry)
                if data["timestamp"] > cutoff_time:
                    recent_wakes.append(data)
            
            # Analyze reasons
            reason_counts = {}
            for wake in recent_wakes:
                reason = wake["reason"]
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            # Analyze by hour
            hour_counts = {}
            for wake in recent_wakes:
                hour = wake.get("hour", 0)
                hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
            return {
                "total_wakes": len(recent_wakes),
                "reason_distribution": reason_counts,
                "hourly_distribution": hour_counts,
                "most_common_reason": max(reason_counts.items(), key=lambda x: x[1])[0] if reason_counts else None,
                "peak_hour": max(hour_counts.items(), key=lambda x: x[1])[0] if hour_counts else None,
            }
            
        except Exception as e:
            logger.error(f"Error getting wake statistics: {e}")
            return {}
    
    def get_classification_summary(self) -> Dict[str, List[str]]:
        """
        Get summary of classification rules
        
        Returns:
            Dictionary of tier: paths
        """
        return {
            "always_ignore": self.ALWAYS_IGNORE,
            "always_wake": self.ALWAYS_WAKE,
            "action_based": list(self.ACTION_BASED_PATHS.keys()),
            "smart_analysis": [
                "write_operations",
                "first_request_in_10min",
                "unusual_time",
                "high_frequency",
                "admin_access",
            ]
        }


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_classifier_instance = None

def get_activity_classifier() -> SmartActivityClassifier:
    """Get singleton classifier instance"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = SmartActivityClassifier()
    return _classifier_instance
