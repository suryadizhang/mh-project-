"""
Monitoring Package for MyHibachi

Provides comprehensive monitoring, alerting, and health check capabilities:
- AlertService: Core alert management and notification system
- ThresholdMonitor: Performance metric monitoring with configurable thresholds
- NotificationChannel: Multi-channel notification delivery (email, SMS, webhook)
- HealthMonitor: System health checks and status reporting
- MonitoringState: Activity-based wake/sleep state machine
"""

from .alert_service import AlertService, Alert, AlertLevel, AlertCategory
from .models import (
    AlertModel,
    AlertStatus,
    AlertPriority,
    NotificationChannel as NotificationChannelEnum,
)
from .metric_collector import (
    MetricCollector,
    push_metric_update,
    track_response_time,
    track_error,
)
from .activity_classifier import (
    SmartActivityClassifier,
    get_activity_classifier,
)
from .middleware import MonitoringMiddleware, monitoring_exception_handler
from .monitoring_state import (
    MonitoringState,
    MonitoringStateEnum,
    get_monitoring_state,
    reset_monitoring_state,
)
from .metric_subscriber import (
    MetricSubscriber,
    MetricBuffer,
    get_metric_subscriber,
    reset_metric_subscriber,
)
from .alert_rule_model import (
    AlertRule,
    ThresholdOperator,
    RuleSeverity,
)
from .rule_evaluator import (
    RuleEvaluator,
    RuleViolation,
    get_rule_evaluator,
)
from .threshold_monitor import (
    ThresholdMonitor,
    get_threshold_monitor,
    threshold_monitor_context,
)
from .startup import (
    startup_monitoring,
    shutdown_monitoring,
    get_monitor_instance,
    monitoring_lifespan,
)

__all__ = [
    "AlertService",
    "Alert",
    "AlertLevel",
    "AlertCategory",
    "AlertModel",
    "AlertStatus",
    "AlertPriority",
    "NotificationChannelEnum",
    "MetricCollector",
    "push_metric_update",
    "track_response_time",
    "track_error",
    "SmartActivityClassifier",
    "get_activity_classifier",
    "MonitoringMiddleware",
    "monitoring_exception_handler",
    "MonitoringState",
    "MonitoringStateEnum",
    "get_monitoring_state",
    "reset_monitoring_state",
    "MetricSubscriber",
    "MetricBuffer",
    "get_metric_subscriber",
    "reset_metric_subscriber",
    "AlertRule",
    "ThresholdOperator",
    "RuleSeverity",
    "RuleEvaluator",
    "RuleViolation",
    "get_rule_evaluator",
    "ThresholdMonitor",
    "get_threshold_monitor",
    "threshold_monitor_context",
    "startup_monitoring",
    "shutdown_monitoring",
    "get_monitor_instance",
    "monitoring_lifespan",
]
