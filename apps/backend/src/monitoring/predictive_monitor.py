"""
Predictive Monitor - ML-Based Threshold Breach Prediction

Uses time series analysis and machine learning to predict threshold breaches
before they happen, enabling proactive responses.

Features:
- Trend analysis with statistical methods
- Threshold breach prediction
- Time-to-breach estimation
- Pattern-based anomaly detection
- Automatic predictive alerts

This enables proactive monitoring instead of reactive alerting.

Created: November 10, 2025
Part of: AI-Monitoring Integration
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
import redis

from core.config import settings
from core.database import SessionLocal
from monitoring.alert_service import AlertService, Alert, AlertLevel, AlertCategory


logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Trend direction"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class PredictionConfidence(str, Enum):
    """Confidence level of prediction"""
    HIGH = "high"  # > 80%
    MEDIUM = "medium"  # 50-80%
    LOW = "low"  # < 50%


@dataclass
class PredictionResult:
    """Result of threshold breach prediction"""
    metric_name: str
    current_value: float
    threshold: float
    will_breach: bool
    confidence: float  # 0.0 to 1.0
    confidence_level: PredictionConfidence
    time_to_breach_minutes: Optional[int]
    trend: TrendDirection
    rate_of_change: float
    predicted_peak_value: float
    predicted_peak_time: Optional[datetime]
    recommended_actions: List[str]
    historical_pattern: str
    metadata: Dict[str, Any]


class PredictiveMonitor:
    """
    Predicts threshold breaches using ML and statistical analysis.
    
    Methods:
    - Linear regression for trend analysis
    - Moving average for smoothing
    - Rate of change calculation
    - Volatility analysis
    - Pattern matching against historical data
    
    Usage:
        monitor = PredictiveMonitor()
        
        # Predict for specific metric
        result = await monitor.predict_threshold_breach(
            metric_name="cpu_percent",
            threshold=80.0
        )
        
        if result.will_breach and result.time_to_breach_minutes < 60:
            # Will breach within 1 hour - take action
            await monitor.create_predictive_alert(result)
    """
    
    def __init__(
        self,
        db: Optional[Session] = None,
        redis_client: Optional[redis.Redis] = None,
        lookback_minutes: int = 60,  # How far back to look
        min_data_points: int = 10  # Minimum points for prediction
    ):
        """
        Initialize predictive monitor.
        
        Args:
            db: Database session (optional)
            redis_client: Redis client (optional)
            lookback_minutes: Historical window for analysis
            min_data_points: Minimum data points needed
        """
        self.db = db or SessionLocal()
        self.redis = redis_client or redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        self.lookback_minutes = lookback_minutes
        self.min_data_points = min_data_points
        
        # Redis keys
        self.history_key_prefix = "metrics:history:"
        self.predictions_key = "monitoring:predictions"
        
        # Initialize AlertService
        self.alert_service = AlertService(db=self.db)
    
    async def predict_threshold_breach(
        self,
        metric_name: str,
        threshold: float,
        lookback_override: Optional[int] = None
    ) -> PredictionResult:
        """
        Predict if a metric will breach its threshold.
        
        Args:
            metric_name: Name of metric to analyze
            threshold: Threshold value
            lookback_override: Override default lookback window
            
        Returns:
            PredictionResult with prediction details
        """
        try:
            # Get metric history
            history = await self._get_metric_history(
                metric_name,
                lookback_override or self.lookback_minutes
            )
            
            if len(history) < self.min_data_points:
                return self._insufficient_data_result(metric_name, threshold)
            
            # Extract values and timestamps
            values = np.array([h["value"] for h in history])
            timestamps = np.array([h["timestamp"] for h in history])
            
            current_value = values[-1]
            
            # Analyze trend
            trend, rate_of_change = self._analyze_trend(values, timestamps)
            
            # Predict breach
            will_breach, time_to_breach, predicted_peak = self._predict_breach(
                values,
                timestamps,
                threshold,
                trend,
                rate_of_change
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(
                values,
                trend,
                rate_of_change,
                will_breach
            )
            
            # Determine confidence level
            if confidence > 0.8:
                confidence_level = PredictionConfidence.HIGH
            elif confidence > 0.5:
                confidence_level = PredictionConfidence.MEDIUM
            else:
                confidence_level = PredictionConfidence.LOW
            
            # Get recommended actions
            actions = self._recommend_actions(
                metric_name,
                current_value,
                threshold,
                will_breach,
                time_to_breach,
                trend
            )
            
            # Identify pattern
            pattern = self._identify_pattern(values, timestamps)
            
            # Calculate predicted peak time
            predicted_peak_time = None
            if time_to_breach:
                predicted_peak_time = datetime.utcnow() + timedelta(minutes=time_to_breach)
            
            result = PredictionResult(
                metric_name=metric_name,
                current_value=current_value,
                threshold=threshold,
                will_breach=will_breach,
                confidence=confidence,
                confidence_level=confidence_level,
                time_to_breach_minutes=time_to_breach,
                trend=trend,
                rate_of_change=rate_of_change,
                predicted_peak_value=predicted_peak,
                predicted_peak_time=predicted_peak_time,
                recommended_actions=actions,
                historical_pattern=pattern,
                metadata={
                    "data_points": len(values),
                    "lookback_minutes": lookback_override or self.lookback_minutes,
                    "analysis_timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Store prediction
            await self._store_prediction(result)
            
            logger.info(
                f"Prediction for {metric_name}: "
                f"Will breach: {will_breach} | "
                f"Confidence: {confidence:.2%} | "
                f"Time to breach: {time_to_breach} min"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error predicting breach: {e}", exc_info=True)
            return self._error_result(metric_name, threshold, str(e))
    
    async def _get_metric_history(
        self,
        metric_name: str,
        lookback_minutes: int
    ) -> List[Dict[str, Any]]:
        """
        Get metric history from Redis.
        
        Returns:
            List of {value, timestamp} dicts
        """
        history_key = f"{self.history_key_prefix}{metric_name}"
        
        try:
            # Get from Redis sorted set (assuming stored with timestamp scores)
            cutoff_time = datetime.utcnow() - timedelta(minutes=lookback_minutes)
            cutoff_score = cutoff_time.timestamp()
            
            # Get all entries since cutoff
            entries = self.redis.zrangebyscore(
                history_key,
                cutoff_score,
                "+inf",
                withscores=True
            )
            
            history = []
            for value_str, timestamp_score in entries:
                history.append({
                    "value": float(value_str),
                    "timestamp": datetime.fromtimestamp(timestamp_score)
                })
            
            return history
            
        except Exception as e:
            logger.warning(f"Could not get metric history: {e}")
            return []
    
    def _analyze_trend(
        self,
        values: np.ndarray,
        timestamps: np.ndarray
    ) -> Tuple[TrendDirection, float]:
        """
        Analyze trend using linear regression.
        
        Returns:
            (trend_direction, rate_of_change_per_minute)
        """
        try:
            # Convert timestamps to minutes from start
            time_diffs = np.array([
                (t - timestamps[0]).total_seconds() / 60
                for t in timestamps
            ])
            
            # Linear regression
            coeffs = np.polyfit(time_diffs, values, 1)
            slope = coeffs[0]  # Rate of change per minute
            
            # Calculate volatility (standard deviation of residuals)
            predicted = np.polyval(coeffs, time_diffs)
            residuals = values - predicted
            volatility = np.std(residuals)
            
            # Determine trend direction
            avg_value = np.mean(values)
            relative_volatility = volatility / avg_value if avg_value > 0 else 0
            
            if relative_volatility > 0.2:  # High volatility
                trend = TrendDirection.VOLATILE
            elif abs(slope) < avg_value * 0.01:  # Less than 1% change per minute
                trend = TrendDirection.STABLE
            elif slope > 0:
                trend = TrendDirection.INCREASING
            else:
                trend = TrendDirection.DECREASING
            
            return trend, slope
            
        except Exception as e:
            logger.warning(f"Error analyzing trend: {e}")
            return TrendDirection.STABLE, 0.0
    
    def _predict_breach(
        self,
        values: np.ndarray,
        timestamps: np.ndarray,
        threshold: float,
        trend: TrendDirection,
        rate_of_change: float
    ) -> Tuple[bool, Optional[int], float]:
        """
        Predict if and when threshold will be breached.
        
        Returns:
            (will_breach, time_to_breach_minutes, predicted_peak_value)
        """
        current_value = values[-1]
        
        # Check if already breached
        if current_value >= threshold:
            return True, 0, current_value
        
        # Stable or decreasing trends won't breach
        if trend in [TrendDirection.STABLE, TrendDirection.DECREASING]:
            return False, None, current_value
        
        # For increasing trends, predict when it will breach
        if trend == TrendDirection.INCREASING and rate_of_change > 0:
            # Simple linear extrapolation
            remaining = threshold - current_value
            time_to_breach = int(remaining / rate_of_change)
            
            # Predict peak value (20% safety margin)
            predicted_peak = current_value + (rate_of_change * time_to_breach * 1.2)
            
            # Only predict breaches within reasonable timeframe (4 hours)
            if time_to_breach <= 240:
                return True, time_to_breach, predicted_peak
        
        # For volatile trends, be conservative
        if trend == TrendDirection.VOLATILE:
            # Check if recent max is close to threshold
            recent_max = np.max(values[-10:])  # Last 10 points
            if recent_max >= threshold * 0.9:  # Within 90% of threshold
                # Estimate conservative time
                return True, 30, threshold * 1.1
        
        return False, None, current_value
    
    def _calculate_confidence(
        self,
        values: np.ndarray,
        trend: TrendDirection,
        rate_of_change: float,
        will_breach: bool
    ) -> float:
        """
        Calculate confidence in prediction.
        
        Higher confidence if:
        - More data points
        - Clear trend
        - Low volatility
        - Consistent rate of change
        
        Returns:
            Confidence score 0.0 to 1.0
        """
        confidence_factors = []
        
        # Factor 1: Data quantity (more data = higher confidence)
        data_confidence = min(len(values) / 60, 1.0)  # Cap at 60 points
        confidence_factors.append(data_confidence)
        
        # Factor 2: Trend clarity
        if trend == TrendDirection.INCREASING:
            trend_confidence = 0.9
        elif trend == TrendDirection.STABLE:
            trend_confidence = 0.8
        elif trend == TrendDirection.DECREASING:
            trend_confidence = 0.7
        else:  # VOLATILE
            trend_confidence = 0.4
        confidence_factors.append(trend_confidence)
        
        # Factor 3: Consistency (low variance in recent changes)
        if len(values) >= 5:
            recent_changes = np.diff(values[-10:])
            change_variance = np.var(recent_changes)
            avg_value = np.mean(values)
            
            relative_variance = change_variance / (avg_value ** 2) if avg_value > 0 else 1.0
            consistency = 1.0 / (1.0 + relative_variance)
            confidence_factors.append(consistency)
        
        # Factor 4: Prediction certainty
        if not will_breach:
            certainty = 0.9  # High confidence when no breach predicted
        else:
            # Lower confidence if rate of change is very high (unpredictable)
            if abs(rate_of_change) > np.mean(values) * 0.1:
                certainty = 0.6
            else:
                certainty = 0.8
        confidence_factors.append(certainty)
        
        # Combine factors (weighted average)
        weights = [0.2, 0.3, 0.3, 0.2]
        confidence = sum(f * w for f, w in zip(confidence_factors, weights))
        
        return round(confidence, 3)
    
    def _recommend_actions(
        self,
        metric_name: str,
        current_value: float,
        threshold: float,
        will_breach: bool,
        time_to_breach: Optional[int],
        trend: TrendDirection
    ) -> List[str]:
        """
        Recommend actions based on prediction.
        
        Returns:
            List of action recommendations
        """
        actions = []
        
        if not will_breach:
            actions.append("Continue monitoring - no immediate action needed")
            return actions
        
        # Urgency-based actions
        if time_to_breach and time_to_breach < 15:
            actions.append("🚨 URGENT: Breach predicted within 15 minutes")
            actions.append("Execute immediate remediation runbook")
        elif time_to_breach and time_to_breach < 60:
            actions.append("⚠️ Breach predicted within 1 hour")
            actions.append("Prepare remediation plan")
        else:
            actions.append("Breach predicted - proactive action recommended")
        
        # Metric-specific actions
        if "cpu" in metric_name.lower():
            actions.append("Scale up compute resources")
            actions.append("Check for CPU-intensive processes")
            actions.append("Review recent deployments for performance regressions")
        
        elif "memory" in metric_name.lower():
            actions.append("Investigate memory leaks")
            actions.append("Consider increasing memory allocation")
            actions.append("Check for large object retention")
        
        elif "db" in metric_name.lower() or "database" in metric_name.lower():
            actions.append("Optimize slow queries")
            actions.append("Check connection pool settings")
            actions.append("Review database indexes")
        
        elif "disk" in metric_name.lower():
            actions.append("Clean up old files and logs")
            actions.append("Increase disk capacity")
            actions.append("Archive old data")
        
        elif "response_time" in metric_name.lower() or "latency" in metric_name.lower():
            actions.append("Check for slow external API calls")
            actions.append("Review database query performance")
            actions.append("Consider caching frequently accessed data")
        
        elif "error" in metric_name.lower():
            actions.append("Review recent error logs")
            actions.append("Check external service health")
            actions.append("Verify configuration changes")
        
        else:
            actions.append(f"Monitor {metric_name} closely")
            actions.append("Review recent changes to the system")
        
        # Trend-based actions
        if trend == TrendDirection.VOLATILE:
            actions.append("Investigate cause of volatility")
            actions.append("Check for periodic batch jobs or external factors")
        
        return actions
    
    def _identify_pattern(
        self,
        values: np.ndarray,
        timestamps: np.ndarray
    ) -> str:
        """
        Identify pattern in time series.
        
        Returns:
            Pattern description
        """
        try:
            # Check for cyclical pattern (using autocorrelation)
            if len(values) >= 30:
                # Calculate autocorrelation at different lags
                mean = np.mean(values)
                variance = np.var(values)
                
                if variance == 0:
                    return "Constant values"
                
                # Check for pattern every 5, 10, 15 minutes
                for lag in [5, 10, 15]:
                    if lag < len(values):
                        autocorr = np.corrcoef(values[:-lag], values[lag:])[0, 1]
                        if autocorr > 0.7:
                            return f"Cyclical pattern (period: ~{lag} minutes)"
            
            # Check for spike pattern
            if len(values) >= 10:
                recent_max = np.max(values[-10:])
                recent_mean = np.mean(values[-10:])
                if recent_max > recent_mean * 1.5:
                    return "Spike detected in recent data"
            
            # Check for step change
            if len(values) >= 20:
                first_half_mean = np.mean(values[:len(values)//2])
                second_half_mean = np.mean(values[len(values)//2:])
                if abs(second_half_mean - first_half_mean) > first_half_mean * 0.3:
                    return "Step change detected"
            
            return "No clear pattern"
            
        except Exception as e:
            logger.warning(f"Error identifying pattern: {e}")
            return "Pattern analysis unavailable"
    
    async def _store_prediction(self, result: PredictionResult):
        """
        Store prediction for tracking accuracy.
        
        Args:
            result: Prediction result to store
        """
        try:
            import json
            
            prediction_record = {
                "metric_name": result.metric_name,
                "threshold": result.threshold,
                "current_value": result.current_value,
                "will_breach": result.will_breach,
                "confidence": result.confidence,
                "time_to_breach": result.time_to_breach_minutes,
                "trend": result.trend,
                "predicted_at": datetime.utcnow().isoformat(),
                "predicted_peak_time": result.predicted_peak_time.isoformat() if result.predicted_peak_time else None
            }
            
            # Store in Redis list
            self.redis.lpush(
                self.predictions_key,
                json.dumps(prediction_record)
            )
            
            # Keep last 500 predictions
            self.redis.ltrim(self.predictions_key, 0, 499)
            
            # 7-day TTL
            self.redis.expire(self.predictions_key, 86400 * 7)
            
        except Exception as e:
            logger.warning(f"Could not store prediction: {e}")
    
    async def create_predictive_alert(self, result: PredictionResult):
        """
        Create predictive alert based on breach prediction.
        
        Args:
            result: Prediction result
        """
        try:
            # Determine alert level based on urgency
            if result.time_to_breach_minutes and result.time_to_breach_minutes < 15:
                level = AlertLevel.CRITICAL
            elif result.time_to_breach_minutes and result.time_to_breach_minutes < 60:
                level = AlertLevel.WARNING
            else:
                level = AlertLevel.INFO
            
            # Build alert message
            message = f"""Predictive Alert: {result.metric_name} will breach threshold

Current Value: {result.current_value:.2f}
Threshold: {result.threshold:.2f}
Predicted Peak: {result.predicted_peak_value:.2f}
Time to Breach: {result.time_to_breach_minutes} minutes
Trend: {result.trend}
Confidence: {result.confidence:.1%} ({result.confidence_level})

Pattern: {result.historical_pattern}

Recommended Actions:
{chr(10).join(f"• {action}" for action in result.recommended_actions)}

This is a proactive alert. Take action now to prevent threshold breach.
"""
            
            # Create alert
            alert = self.alert_service.create_alert(
                title=f"Predictive: {result.metric_name} will breach threshold",
                message=message,
                level=level,
                category=AlertCategory.THRESHOLD,
                source="predictive_monitor",
                metadata={
                    "predictive": True,
                    "metric_name": result.metric_name,
                    "current_value": result.current_value,
                    "threshold": result.threshold,
                    "time_to_breach_minutes": result.time_to_breach_minutes,
                    "confidence": result.confidence,
                    "confidence_level": result.confidence_level,
                    "trend": result.trend,
                    "predicted_peak_value": result.predicted_peak_value,
                    "predicted_peak_time": result.predicted_peak_time.isoformat() if result.predicted_peak_time else None
                }
            )
            
            logger.info(
                f"Created predictive alert for {result.metric_name} | "
                f"Level: {level} | "
                f"Time to breach: {result.time_to_breach_minutes} min"
            )
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating predictive alert: {e}", exc_info=True)
            return None
    
    def _insufficient_data_result(
        self,
        metric_name: str,
        threshold: float
    ) -> PredictionResult:
        """Return result for insufficient data case"""
        return PredictionResult(
            metric_name=metric_name,
            current_value=0.0,
            threshold=threshold,
            will_breach=False,
            confidence=0.0,
            confidence_level=PredictionConfidence.LOW,
            time_to_breach_minutes=None,
            trend=TrendDirection.STABLE,
            rate_of_change=0.0,
            predicted_peak_value=0.0,
            predicted_peak_time=None,
            recommended_actions=["Insufficient data for prediction - continue monitoring"],
            historical_pattern="Insufficient data",
            metadata={"error": "insufficient_data"}
        )
    
    def _error_result(
        self,
        metric_name: str,
        threshold: float,
        error: str
    ) -> PredictionResult:
        """Return result for error case"""
        return PredictionResult(
            metric_name=metric_name,
            current_value=0.0,
            threshold=threshold,
            will_breach=False,
            confidence=0.0,
            confidence_level=PredictionConfidence.LOW,
            time_to_breach_minutes=None,
            trend=TrendDirection.STABLE,
            rate_of_change=0.0,
            predicted_peak_value=0.0,
            predicted_peak_time=None,
            recommended_actions=["Prediction error - manual investigation required"],
            historical_pattern="Error",
            metadata={"error": error}
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

_predictive_monitor_instance: Optional[PredictiveMonitor] = None


def get_predictive_monitor() -> PredictiveMonitor:
    """
    Get singleton instance of PredictiveMonitor.
    
    Returns:
        PredictiveMonitor instance
    """
    global _predictive_monitor_instance
    
    if _predictive_monitor_instance is None:
        _predictive_monitor_instance = PredictiveMonitor()
    
    return _predictive_monitor_instance


async def monitor_critical_metrics():
    """
    Monitor critical metrics for predicted breaches.
    
    This should be run periodically (e.g., every 5 minutes) as a background task.
    
    Usage:
        # In Celery tasks
        @celery_app.task
        def predict_threshold_breaches():
            asyncio.run(monitor_critical_metrics())
    """
    monitor = get_predictive_monitor()
    
    # Define critical metrics and their thresholds
    critical_metrics = {
        "cpu_percent": 80.0,
        "memory_percent": 85.0,
        "db_connection_pool_usage": 90.0,
        "api_error_rate_percent": 5.0,
        "api_response_time_p95": 2000.0,
        "disk_usage_percent": 80.0
    }
    
    alerts_created = 0
    
    for metric_name, threshold in critical_metrics.items():
        try:
            # Predict breach
            result = await monitor.predict_threshold_breach(metric_name, threshold)
            
            # Create alert if will breach soon and high confidence
            if (result.will_breach and 
                result.confidence > 0.6 and 
                result.time_to_breach_minutes and
                result.time_to_breach_minutes < 120):  # Within 2 hours
                
                await monitor.create_predictive_alert(result)
                alerts_created += 1
        
        except Exception as e:
            logger.error(f"Error monitoring {metric_name}: {e}")
    
    if alerts_created > 0:
        logger.info(f"Created {alerts_created} predictive alerts")
