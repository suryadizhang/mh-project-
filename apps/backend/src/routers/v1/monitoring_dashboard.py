"""
Unified Monitoring Dashboard API

Provides comprehensive monitoring data combining:
- System metrics (CPU, memory, database)
- AI metrics (costs, usage, quality)
- Active alerts with AI analysis
- Predictive breach warnings
- Historical trends and correlations

This gives a complete picture of system health in one API call.

Created: November 10, 2025
Part of: AI-Monitoring Integration
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from monitoring.metric_collector import MetricCollector
from monitoring.alert_service import AlertService, Alert
from monitoring.ai_alert_analyzer import get_alert_analyzer
from monitoring.predictive_monitor import get_predictive_monitor
import redis
from core.config import settings


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring/dashboard", tags=["Monitoring - Dashboard"])


# ============================================================================
# Pydantic Models
# ============================================================================

class SystemHealth(BaseModel):
    """Overall system health status"""
    status: str  # healthy, degraded, critical
    score: float  # 0-100
    issues: List[str]
    last_updated: datetime


class MetricSummary(BaseModel):
    """Summary of a metric"""
    name: str
    current_value: float
    threshold: Optional[float] = None
    status: str  # normal, warning, critical
    trend: str  # increasing, decreasing, stable
    change_24h_percent: Optional[float] = None


class AIMetricsSummary(BaseModel):
    """Summary of AI system metrics"""
    requests_per_hour: float
    cost_per_hour_usd: float
    cost_today_usd: float
    cost_month_usd: float
    avg_confidence: float
    error_rate_percent: float
    escalation_rate_percent: float
    active_conversations: int
    avg_latency_ms: float


class AlertSummary(BaseModel):
    """Summary of an alert with AI analysis"""
    id: int
    title: str
    level: str
    category: str
    created_at: datetime
    status: str
    ai_root_cause: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_suggested_actions: Optional[List[str]] = None
    auto_resolvable: bool = False


class PredictiveSummary(BaseModel):
    """Summary of predictive breach warnings"""
    metric_name: str
    current_value: float
    threshold: float
    will_breach: bool
    time_to_breach_minutes: Optional[int]
    confidence: float
    recommended_actions: List[str]


class CorrelationInsight(BaseModel):
    """Correlation between metrics"""
    metric1: str
    metric2: str
    correlation: float
    insight: str


class DashboardResponse(BaseModel):
    """Complete dashboard data"""
    health: SystemHealth
    system_metrics: List[MetricSummary]
    ai_metrics: AIMetricsSummary
    active_alerts: List[AlertSummary]
    predictive_warnings: List[PredictiveSummary]
    correlations: List[CorrelationInsight]
    timestamp: datetime


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    include_predictions: bool = Query(True, description="Include predictive analysis"),
    include_correlations: bool = Query(True, description="Include metric correlations"),
    db: Session = Depends(get_db)
):
    """
    Get unified monitoring dashboard data.
    
    Returns comprehensive monitoring data in a single response:
    - System health score and status
    - Key system metrics (CPU, memory, DB, API)
    - AI metrics (costs, usage, quality)
    - Active alerts with AI analysis
    - Predictive breach warnings
    - Metric correlations and insights
    
    This endpoint is optimized for dashboard UIs and provides all monitoring
    data needed to display a complete system health overview.
    """
    try:
        # Initialize services
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        collector = MetricCollector(db=db, redis_client=redis_client)
        alert_service = AlertService(db=db)
        
        # Collect all current metrics
        all_metrics = collector.collect_all_metrics()
        
        # Calculate system health
        health = _calculate_system_health(all_metrics, alert_service)
        
        # Get system metrics summary
        system_metrics = _get_system_metrics_summary(all_metrics)
        
        # Get AI metrics summary
        ai_metrics = _get_ai_metrics_summary(all_metrics)
        
        # Get active alerts with AI analysis
        active_alerts = await _get_active_alerts_with_ai(alert_service)
        
        # Get predictive warnings (if requested)
        predictive_warnings = []
        if include_predictions:
            predictive_warnings = await _get_predictive_warnings()
        
        # Get correlations (if requested)
        correlations = []
        if include_correlations:
            correlations = _get_metric_correlations(all_metrics)
        
        response = DashboardResponse(
            health=health,
            system_metrics=system_metrics,
            ai_metrics=ai_metrics,
            active_alerts=active_alerts,
            predictive_warnings=predictive_warnings,
            correlations=correlations,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Dashboard generated | "
            f"Health: {health.status} | "
            f"Active alerts: {len(active_alerts)} | "
            f"Predictive warnings: {len(predictive_warnings)}"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating dashboard: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error generating dashboard: {str(e)}"
        )


@router.get("/health")
async def get_health_only(db: Session = Depends(get_db)):
    """
    Get just the system health status (lightweight endpoint).
    
    Use this for health checks and quick status updates.
    """
    try:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        collector = MetricCollector(db=db, redis_client=redis_client)
        alert_service = AlertService(db=db)
        
        all_metrics = collector.collect_all_metrics()
        health = _calculate_system_health(all_metrics, alert_service)
        
        return health
        
    except Exception as e:
        logger.error(f"Error getting health: {e}")
        return SystemHealth(
            status="unknown",
            score=0.0,
            issues=[f"Health check failed: {str(e)}"],
            last_updated=datetime.utcnow()
        )


@router.get("/metrics/trends")
async def get_metric_trends(
    metric_name: str = Query(..., description="Metric name"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history (max 7 days)"),
    db: Session = Depends(get_db)
):
    """
    Get historical trend data for a specific metric.
    
    Returns time series data for charting and analysis.
    """
    try:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        
        # Get metric history from Redis
        history_key = f"metrics:history:{metric_name}"
        
        # Calculate time range
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        cutoff_score = cutoff_time.timestamp()
        
        # Get entries from Redis sorted set
        entries = redis_client.zrangebyscore(
            history_key,
            cutoff_score,
            "+inf",
            withscores=True
        )
        
        # Format response
        trend_data = []
        for value_str, timestamp_score in entries:
            trend_data.append({
                "timestamp": datetime.fromtimestamp(timestamp_score).isoformat(),
                "value": float(value_str)
            })
        
        return {
            "metric_name": metric_name,
            "hours": hours,
            "data_points": len(trend_data),
            "data": trend_data
        }
        
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting metric trends: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _calculate_system_health(
    metrics: Dict[str, float],
    alert_service: AlertService
) -> SystemHealth:
    """
    Calculate overall system health score.
    
    Health score based on:
    - Critical metrics (CPU, memory, DB)
    - Active critical alerts
    - Error rates
    - Response times
    """
    score = 100.0
    issues = []
    
    # Check CPU
    cpu = metrics.get("cpu_percent", 0)
    if cpu > 90:
        score -= 30
        issues.append(f"Critical CPU usage: {cpu:.1f}%")
    elif cpu > 75:
        score -= 15
        issues.append(f"High CPU usage: {cpu:.1f}%")
    
    # Check memory
    memory = metrics.get("memory_percent", 0)
    if memory > 90:
        score -= 30
        issues.append(f"Critical memory usage: {memory:.1f}%")
    elif memory > 80:
        score -= 15
        issues.append(f"High memory usage: {memory:.1f}%")
    
    # Check database
    db_connections = metrics.get("db_connection_pool_usage", 0)
    if db_connections > 90:
        score -= 20
        issues.append(f"Database connection pool critical: {db_connections:.1f}%")
    elif db_connections > 75:
        score -= 10
        issues.append(f"Database connection pool high: {db_connections:.1f}%")
    
    # Check API error rate
    error_rate = metrics.get("api_error_rate_percent", 0)
    if error_rate > 5:
        score -= 25
        issues.append(f"High error rate: {error_rate:.1f}%")
    elif error_rate > 2:
        score -= 10
        issues.append(f"Elevated error rate: {error_rate:.1f}%")
    
    # Check response time
    p95_response = metrics.get("api_response_time_p95", 0)
    if p95_response > 2000:
        score -= 15
        issues.append(f"Slow response times: {p95_response:.0f}ms (p95)")
    
    # Check active critical alerts
    critical_alerts = alert_service.get_active_alert_count("critical")
    if critical_alerts > 0:
        score -= critical_alerts * 10
        issues.append(f"{critical_alerts} critical alert(s)")
    
    # Determine status
    if score >= 80:
        status = "healthy"
    elif score >= 50:
        status = "degraded"
    else:
        status = "critical"
    
    # Ensure score doesn't go below 0
    score = max(score, 0.0)
    
    return SystemHealth(
        status=status,
        score=round(score, 1),
        issues=issues,
        last_updated=datetime.utcnow()
    )


def _get_system_metrics_summary(metrics: Dict[str, float]) -> List[MetricSummary]:
    """Get summary of key system metrics"""
    
    key_metrics = [
        ("cpu_percent", 80.0, "CPU Usage"),
        ("memory_percent", 85.0, "Memory Usage"),
        ("db_connection_pool_usage", 80.0, "Database Connections"),
        ("api_error_rate_percent", 2.0, "API Error Rate"),
        ("api_response_time_p95", 1000.0, "API Response Time (p95)"),
        ("api_requests_per_minute", None, "API Requests/min"),
    ]
    
    summaries = []
    
    for metric_name, threshold, display_name in key_metrics:
        value = metrics.get(metric_name, 0.0)
        
        # Determine status
        if threshold is not None:
            if value >= threshold:
                status = "critical"
            elif value >= threshold * 0.8:
                status = "warning"
            else:
                status = "normal"
        else:
            status = "normal"
        
        # Simple trend (would be calculated from history in production)
        trend = "stable"
        
        summaries.append(MetricSummary(
            name=display_name,
            current_value=round(value, 2),
            threshold=threshold,
            status=status,
            trend=trend,
            change_24h_percent=None
        ))
    
    return summaries


def _get_ai_metrics_summary(metrics: Dict[str, float]) -> AIMetricsSummary:
    """Get summary of AI metrics"""
    
    return AIMetricsSummary(
        requests_per_hour=metrics.get("ai_requests_last_hour", 0.0),
        cost_per_hour_usd=metrics.get("ai_cost_per_hour_usd", 0.0),
        cost_today_usd=metrics.get("ai_cost_today_usd", 0.0),
        cost_month_usd=metrics.get("ai_cost_month_usd", 0.0),
        avg_confidence=metrics.get("ai_avg_confidence_percent", 0.0),
        error_rate_percent=metrics.get("ai_error_rate_percent", 0.0),
        escalation_rate_percent=metrics.get("ai_escalation_rate_percent", 0.0),
        active_conversations=int(metrics.get("ai_active_conversations_hour", 0)),
        avg_latency_ms=metrics.get("ai_avg_latency_ms", 0.0)
    )


async def _get_active_alerts_with_ai(alert_service: AlertService) -> List[AlertSummary]:
    """Get active alerts with AI analysis"""
    
    # Get active alerts
    active_alerts = alert_service.get_active_alerts(limit=20)
    
    summaries = []
    
    for alert in active_alerts:
        # Extract AI analysis from metadata if available
        ai_root_cause = None
        ai_confidence = None
        ai_suggested_actions = None
        auto_resolvable = False
        
        if alert.metadata:
            ai_root_cause = alert.metadata.get("ai_root_cause")
            ai_confidence = alert.metadata.get("ai_confidence")
            
            # Parse suggestions if present
            suggestions = alert.metadata.get("ai_suggestions")
            if suggestions and isinstance(suggestions, str):
                # Extract actions from suggestions text
                import re
                action_matches = re.findall(r'\d+\.\s+(.+)', suggestions)
                if action_matches:
                    ai_suggested_actions = action_matches[:3]  # Top 3 actions
            
            auto_resolvable = alert.metadata.get("auto_resolvable", False)
        
        summaries.append(AlertSummary(
            id=alert.id,
            title=alert.title,
            level=alert.level,
            category=alert.category,
            created_at=alert.created_at,
            status=alert.status,
            ai_root_cause=ai_root_cause,
            ai_confidence=ai_confidence,
            ai_suggested_actions=ai_suggested_actions,
            auto_resolvable=auto_resolvable
        ))
    
    return summaries


async def _get_predictive_warnings() -> List[PredictiveSummary]:
    """Get predictive breach warnings"""
    
    monitor = get_predictive_monitor()
    
    # Critical metrics to check
    critical_metrics = {
        "cpu_percent": 80.0,
        "memory_percent": 85.0,
        "db_connection_pool_usage": 90.0,
        "api_error_rate_percent": 5.0
    }
    
    warnings = []
    
    for metric_name, threshold in critical_metrics.items():
        try:
            result = await monitor.predict_threshold_breach(metric_name, threshold)
            
            # Only include if will breach and reasonable confidence
            if result.will_breach and result.confidence > 0.5:
                warnings.append(PredictiveSummary(
                    metric_name=metric_name,
                    current_value=result.current_value,
                    threshold=result.threshold,
                    will_breach=result.will_breach,
                    time_to_breach_minutes=result.time_to_breach_minutes,
                    confidence=result.confidence,
                    recommended_actions=result.recommended_actions[:3]  # Top 3
                ))
        except Exception as e:
            logger.warning(f"Error predicting {metric_name}: {e}")
    
    return warnings


def _get_metric_correlations(metrics: Dict[str, float]) -> List[CorrelationInsight]:
    """
    Identify interesting correlations between metrics.
    
    This is a simplified version. In production, you'd calculate
    actual correlations from historical data.
    """
    insights = []
    
    # Common correlations to check
    
    # 1. CPU and Response Time
    cpu = metrics.get("cpu_percent", 0)
    response_time = metrics.get("api_response_time_p95", 0)
    if cpu > 70 and response_time > 1000:
        insights.append(CorrelationInsight(
            metric1="cpu_percent",
            metric2="api_response_time_p95",
            correlation=0.85,
            insight="High CPU usage is correlated with slow response times"
        ))
    
    # 2. Database Connections and Response Time
    db_connections = metrics.get("db_connection_pool_usage", 0)
    if db_connections > 75 and response_time > 1000:
        insights.append(CorrelationInsight(
            metric1="db_connection_pool_usage",
            metric2="api_response_time_p95",
            correlation=0.78,
            insight="Database connection pool saturation is affecting response times"
        ))
    
    # 3. AI Requests and Cost
    ai_requests = metrics.get("ai_requests_last_hour", 0)
    ai_cost = metrics.get("ai_cost_per_hour_usd", 0)
    if ai_requests > 0 and ai_cost > 0:
        cost_per_request = ai_cost / ai_requests
        insights.append(CorrelationInsight(
            metric1="ai_requests_last_hour",
            metric2="ai_cost_per_hour_usd",
            correlation=0.95,
            insight=f"AI cost per request: ${cost_per_request:.4f}"
        ))
    
    # 4. Error Rate and Escalation Rate
    error_rate = metrics.get("ai_error_rate_percent", 0)
    escalation_rate = metrics.get("ai_escalation_rate_percent", 0)
    if error_rate > 2 and escalation_rate > 10:
        insights.append(CorrelationInsight(
            metric1="ai_error_rate_percent",
            metric2="ai_escalation_rate_percent",
            correlation=0.72,
            insight="Higher AI error rates lead to more human escalations"
        ))
    
    return insights
