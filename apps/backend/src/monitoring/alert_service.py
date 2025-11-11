"""
Alert Service - Core Alert Management System

Provides comprehensive alert management with detailed error diagnostics:
- Specific error messages with full context
- Actionable recommendations for fixes
- Historical pattern tracking
- Integration with existing monitoring systems
- Multi-channel notification support
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from monitoring.models import (
    AlertModel,
    AlertPriority,
    AlertRule,
    AlertStatus,
    NotificationChannel,
)

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels with clear meaning"""

    CRITICAL = "critical"  # System down, data loss risk, revenue impact
    HIGH = "high"  # Degraded performance, customer impact
    MEDIUM = "medium"  # Performance warnings, potential issues
    LOW = "low"  # Minor issues, optimization opportunities
    INFO = "info"  # Informational, metrics, events


class AlertCategory(str, Enum):
    """Alert categories for organization"""

    SYSTEM = "system"  # CPU, memory, disk, network
    APPLICATION = "application"  # Service errors, exceptions
    DATABASE = "database"  # Query performance, connections
    SECURITY = "security"  # Auth failures, suspicious activity
    BUSINESS = "business"  # Revenue, bookings, customer issues
    PERFORMANCE = "performance"  # Response times, throughput
    AVAILABILITY = "availability"  # Uptime, health checks


class Alert:
    """
    Alert data structure with comprehensive diagnostic information
    
    Provides all context needed to understand and fix the issue.
    """

    def __init__(
        self,
        alert_type: str,
        title: str,
        message: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        category: AlertCategory = AlertCategory.APPLICATION,
        source: Optional[str] = None,
        resource: Optional[str] = None,
        metric_name: Optional[str] = None,
        metric_value: Optional[Union[str, float, int]] = None,
        threshold_value: Optional[Union[str, float, int]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None,
        related_logs: Optional[str] = None,
        stack_trace: Optional[str] = None,
        affected_users: Optional[int] = None,
        error_code: Optional[str] = None,
        notification_channels: Optional[List[NotificationChannel]] = None,
    ):
        self.alert_type = alert_type
        self.title = title
        self.message = message
        self.priority = priority
        self.category = category
        self.source = source or "system"
        self.resource = resource
        self.metric_name = metric_name
        self.metric_value = str(metric_value) if metric_value is not None else None
        self.threshold_value = str(threshold_value) if threshold_value is not None else None
        self.metadata = metadata or {}
        self.recommendations = recommendations or []
        self.related_logs = related_logs
        self.stack_trace = stack_trace
        self.affected_users = affected_users
        self.error_code = error_code
        self.notification_channels = notification_channels or []
        self.triggered_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary with all diagnostic data"""
        return {
            "alert_type": self.alert_type,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value if isinstance(self.priority, AlertPriority) else self.priority,
            "category": self.category.value if isinstance(self.category, AlertCategory) else self.category,
            "source": self.source,
            "resource": self.resource,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
            "metadata": self.metadata,
            "recommendations": self.recommendations,
            "related_logs": self.related_logs,
            "stack_trace": self.stack_trace,
            "affected_users": self.affected_users,
            "error_code": self.error_code,
            "notification_channels": [
                ch.value if isinstance(ch, NotificationChannel) else ch
                for ch in self.notification_channels
            ],
            "triggered_at": self.triggered_at.isoformat(),
        }


class AlertService:
    """
    Core Alert Management Service
    
    Features:
    - Detailed error diagnostics with actionable recommendations
    - Deduplication to avoid alert spam
    - Historical pattern analysis
    - Integration with monitoring systems
    - Multi-channel notifications
    """

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)

    # ============================================================================
    # CREATING ALERTS WITH DETAILED DIAGNOSTICS
    # ============================================================================

    def create_alert(
        self,
        alert: Alert,
        auto_notify: bool = True,
        deduplicate: bool = True,
    ) -> AlertModel:
        """
        Create alert with comprehensive diagnostic information
        
        Args:
            alert: Alert object with full context
            auto_notify: Send notifications immediately
            deduplicate: Check for similar recent alerts
            
        Returns:
            Created AlertModel instance
            
        Example:
            ```python
            alert = Alert(
                alert_type="database_slow_query",
                title="Slow Database Query Detected",
                message="Query took 5.2 seconds (threshold: 1.0s)",
                priority=AlertPriority.HIGH,
                category=AlertCategory.DATABASE,
                source="booking_service",
                resource="bookings table",
                metric_name="query_duration_seconds",
                metric_value=5.2,
                threshold_value=1.0,
                metadata={
                    "query": "SELECT * FROM bookings WHERE...",
                    "execution_plan": "Seq Scan on bookings...",
                    "rows_scanned": 50000,
                },
                recommendations=[
                    "Add index on customer_id column",
                    "Consider adding WHERE clause to limit rows",
                    "Review query execution plan",
                ],
                related_logs="/var/log/postgresql/slow_queries.log",
            )
            service.create_alert(alert)
            ```
        """
        try:
            # Check for duplicate alerts if requested
            if deduplicate:
                existing = self._find_duplicate_alert(alert)
                if existing:
                    self.logger.info(
                        f"Duplicate alert found (ID: {existing.id}), "
                        f"incrementing notification count"
                    )
                    existing.notification_count += 1
                    existing.updated_at = datetime.utcnow()
                    self.db.commit()
                    return existing

            # Create new alert with all diagnostic data
            db_alert = AlertModel(
                alert_type=alert.alert_type,
                category=alert.category.value if isinstance(alert.category, AlertCategory) else alert.category,
                title=alert.title,
                message=alert.message,
                priority=alert.priority,
                status=AlertStatus.ACTIVE,
                source=alert.source,
                resource=alert.resource,
                metric_name=alert.metric_name,
                metric_value=alert.metric_value,
                threshold_value=alert.threshold_value,
                metadata={
                    **alert.metadata,
                    "recommendations": alert.recommendations,
                    "related_logs": alert.related_logs,
                    "stack_trace": alert.stack_trace,
                    "affected_users": alert.affected_users,
                    "error_code": alert.error_code,
                },
                notification_channels=[
                    ch.value if isinstance(ch, NotificationChannel) else ch
                    for ch in alert.notification_channels
                ],
                triggered_at=alert.triggered_at,
            )

            self.db.add(db_alert)
            self.db.commit()
            self.db.refresh(db_alert)

            self.logger.info(
                f"Alert created: {db_alert.id} - {db_alert.title} "
                f"(Priority: {db_alert.priority.value}, Type: {db_alert.alert_type})"
            )

            # Send notifications if requested
            if auto_notify:
                self._send_notifications(db_alert)

            return db_alert

        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}", exc_info=True)
            self.db.rollback()
            raise

    def create_system_alert(
        self,
        metric_name: str,
        current_value: Union[float, int],
        threshold_value: Union[float, int],
        resource: str,
        recommendations: Optional[List[str]] = None,
    ) -> AlertModel:
        """
        Create system resource alert with specific details
        
        Example:
            High CPU usage alert with actionable steps
        """
        # Determine severity based on how much threshold is exceeded
        overage_percent = ((current_value - threshold_value) / threshold_value) * 100
        
        if overage_percent > 50:
            priority = AlertPriority.CRITICAL
        elif overage_percent > 20:
            priority = AlertPriority.HIGH
        else:
            priority = AlertPriority.MEDIUM

        # Build detailed message
        message = (
            f"{metric_name.replace('_', ' ').title()} is at {current_value}% "
            f"(threshold: {threshold_value}%, exceeded by {overage_percent:.1f}%)"
        )

        # Default recommendations based on metric type
        if not recommendations:
            recommendations = self._get_default_recommendations(metric_name, resource)

        alert = Alert(
            alert_type=f"system_{metric_name}",
            title=f"High {metric_name.replace('_', ' ').title()} - {resource}",
            message=message,
            priority=priority,
            category=AlertCategory.SYSTEM,
            source="system_monitor",
            resource=resource,
            metric_name=metric_name,
            metric_value=current_value,
            threshold_value=threshold_value,
            recommendations=recommendations,
            notification_channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
        )

        return self.create_alert(alert)

    def create_application_error_alert(
        self,
        error_type: str,
        error_message: str,
        stack_trace: str,
        source: str,
        affected_endpoint: Optional[str] = None,
        affected_users: Optional[int] = None,
        error_count: int = 1,
    ) -> AlertModel:
        """
        Create application error alert with full diagnostic context
        
        Example:
            Database connection error with stack trace and recommendations
        """
        # Determine priority based on error type and impact
        if "database" in error_type.lower() or "connection" in error_type.lower():
            priority = AlertPriority.CRITICAL
        elif affected_users and affected_users > 10:
            priority = AlertPriority.HIGH
        elif error_count > 5:
            priority = AlertPriority.HIGH
        else:
            priority = AlertPriority.MEDIUM

        # Build detailed message with context
        message_parts = [error_message]
        
        if affected_endpoint:
            message_parts.append(f"Endpoint: {affected_endpoint}")
        
        if affected_users:
            message_parts.append(f"Affected users: {affected_users}")
        
        if error_count > 1:
            message_parts.append(f"Error count: {error_count}")

        message = " | ".join(message_parts)

        # Generate recommendations based on error type
        recommendations = self._generate_error_recommendations(
            error_type, error_message, stack_trace
        )

        alert = Alert(
            alert_type=f"app_error_{error_type}",
            title=f"Application Error: {error_type}",
            message=message,
            priority=priority,
            category=AlertCategory.APPLICATION,
            source=source,
            resource=affected_endpoint,
            metadata={
                "error_type": error_type,
                "error_count": error_count,
            },
            recommendations=recommendations,
            stack_trace=stack_trace,
            affected_users=affected_users,
            error_code=error_type,
            notification_channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
        )

        return self.create_alert(alert)

    def create_performance_alert(
        self,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        resource: str,
        percentile: Optional[str] = None,
        sample_count: Optional[int] = None,
    ) -> AlertModel:
        """
        Create performance degradation alert with metrics
        
        Example:
            Slow API response time with percentile data
        """
        # Calculate severity
        if current_value > threshold_value * 2:
            priority = AlertPriority.CRITICAL
        elif current_value > threshold_value * 1.5:
            priority = AlertPriority.HIGH
        else:
            priority = AlertPriority.MEDIUM

        message_parts = [
            f"{metric_name} is {current_value:.2f}ms (threshold: {threshold_value:.2f}ms)"
        ]
        
        if percentile:
            message_parts.append(f"Percentile: {percentile}")
        
        if sample_count:
            message_parts.append(f"Samples: {sample_count}")

        message = " | ".join(message_parts)

        # Performance-specific recommendations
        recommendations = [
            f"Check {resource} for slow operations",
            "Review recent deployments or configuration changes",
            "Analyze database query performance",
            "Check for resource contention (CPU, memory, I/O)",
            "Review application logs for errors or warnings",
        ]

        alert = Alert(
            alert_type=f"performance_{metric_name}",
            title=f"Performance Degradation: {resource}",
            message=message,
            priority=priority,
            category=AlertCategory.PERFORMANCE,
            source="performance_monitor",
            resource=resource,
            metric_name=metric_name,
            metric_value=current_value,
            threshold_value=threshold_value,
            metadata={
                "percentile": percentile,
                "sample_count": sample_count,
            },
            recommendations=recommendations,
            notification_channels=[NotificationChannel.EMAIL, NotificationChannel.DASHBOARD],
        )

        return self.create_alert(alert)

    # ============================================================================
    # ALERT RETRIEVAL AND MANAGEMENT
    # ============================================================================

    def get_active_alerts(
        self,
        priority: Optional[AlertPriority] = None,
        category: Optional[AlertCategory] = None,
        limit: int = 100,
    ) -> List[AlertModel]:
        """Get currently active alerts with optional filtering"""
        query = self.db.query(AlertModel).filter(
            AlertModel.status == AlertStatus.ACTIVE
        )

        if priority:
            query = query.filter(AlertModel.priority == priority)

        if category:
            query = query.filter(AlertModel.category == category)

        return query.order_by(desc(AlertModel.triggered_at)).limit(limit).all()

    def get_alert_by_id(self, alert_id: int) -> Optional[AlertModel]:
        """Get specific alert with all diagnostic data"""
        return self.db.query(AlertModel).filter(AlertModel.id == alert_id).first()

    def acknowledge_alert(
        self,
        alert_id: int,
        acknowledged_by: str,
        notes: Optional[str] = None,
    ) -> AlertModel:
        """
        Acknowledge alert (mark as seen, working on it)
        """
        alert = self.get_alert_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()
        
        if notes:
            if not alert.metadata:
                alert.metadata = {}
            alert.metadata["acknowledgement_notes"] = notes

        self.db.commit()
        self.logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
        
        return alert

    def resolve_alert(
        self,
        alert_id: int,
        resolved_by: str,
        resolution_notes: str,
    ) -> AlertModel:
        """
        Resolve alert with explanation of fix
        """
        alert = self.get_alert_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = AlertStatus.RESOLVED
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.utcnow()
        alert.resolution_notes = resolution_notes

        self.db.commit()
        self.logger.info(
            f"Alert {alert_id} resolved by {resolved_by}: {resolution_notes}"
        )
        
        return alert

    def suppress_alert(
        self,
        alert_id: int,
        suppressed_by: str,
        suppression_reason: str,
        duration_hours: int = 24,
    ) -> AlertModel:
        """
        Temporarily suppress alert (e.g., during maintenance)
        """
        alert = self.get_alert_by_id(alert_id)
        if not alert:
            raise ValueError(f"Alert {alert_id} not found")

        alert.status = AlertStatus.SUPPRESSED
        alert.suppressed_by = suppressed_by
        alert.suppression_reason = suppression_reason
        alert.suppressed_until = datetime.utcnow() + timedelta(hours=duration_hours)

        self.db.commit()
        self.logger.info(
            f"Alert {alert_id} suppressed by {suppressed_by} for {duration_hours}h: "
            f"{suppression_reason}"
        )
        
        return alert

    # ============================================================================
    # PATTERN ANALYSIS AND INSIGHTS
    # ============================================================================

    def get_alert_patterns(
        self,
        alert_type: Optional[str] = None,
        days: int = 7,
    ) -> Dict[str, Any]:
        """
        Analyze alert patterns to identify recurring issues
        
        Returns insights like:
        - Most common alert types
        - Time patterns (when alerts occur)
        - Resolution times
        - Recurring issues
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(AlertModel).filter(
            AlertModel.triggered_at >= start_date
        )

        if alert_type:
            query = query.filter(AlertModel.alert_type == alert_type)

        alerts = query.all()

        # Analyze patterns
        type_counts = {}
        priority_counts = {}
        category_counts = {}
        hourly_distribution = [0] * 24
        resolution_times = []

        for alert in alerts:
            # Type distribution
            type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1
            
            # Priority distribution
            if alert.priority:
                priority_counts[alert.priority.value] = (
                    priority_counts.get(alert.priority.value, 0) + 1
                )
            
            # Category distribution
            category_counts[alert.category] = (
                category_counts.get(alert.category, 0) + 1
            )
            
            # Time distribution
            hour = alert.triggered_at.hour
            hourly_distribution[hour] += 1
            
            # Resolution time
            if alert.resolved_at:
                resolution_time = (alert.resolved_at - alert.triggered_at).total_seconds() / 60
                resolution_times.append(resolution_time)

        # Calculate statistics
        avg_resolution_time = (
            sum(resolution_times) / len(resolution_times) if resolution_times else 0
        )

        # Find peak hour
        peak_hour = hourly_distribution.index(max(hourly_distribution))

        return {
            "period_days": days,
            "total_alerts": len(alerts),
            "type_distribution": type_counts,
            "priority_distribution": priority_counts,
            "category_distribution": category_counts,
            "peak_hour": peak_hour,
            "hourly_distribution": hourly_distribution,
            "avg_resolution_time_minutes": round(avg_resolution_time, 2),
            "most_common_type": max(type_counts, key=type_counts.get) if type_counts else None,
        }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _find_duplicate_alert(self, alert: Alert) -> Optional[AlertModel]:
        """
        Check for similar recent alerts to avoid spam
        
        Considers an alert duplicate if:
        - Same alert_type
        - Same resource
        - Still active
        - Triggered within last hour
        """
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        existing = (
            self.db.query(AlertModel)
            .filter(
                and_(
                    AlertModel.alert_type == alert.alert_type,
                    AlertModel.resource == alert.resource,
                    AlertModel.status == AlertStatus.ACTIVE,
                    AlertModel.triggered_at >= one_hour_ago,
                )
            )
            .first()
        )

        return existing

    def _send_notifications(self, alert: AlertModel):
        """
        Send alert notifications via configured channels
        
        Note: Actual notification sending will be implemented in Week 3
        For now, just log the notification
        """
        self.logger.info(
            f"Sending notifications for alert {alert.id} via channels: "
            f"{alert.notification_channels}"
        )

        alert.notification_sent_at = datetime.utcnow()
        alert.notification_count = 1
        self.db.commit()

    def _get_default_recommendations(
        self, metric_name: str, resource: str
    ) -> List[str]:
        """Generate default recommendations based on metric type"""
        recommendations = {
            "cpu_percent": [
                "Check for runaway processes consuming CPU",
                "Review recent code deployments for inefficient algorithms",
                "Scale horizontally by adding more instances",
                "Analyze CPU profiling data to identify hotspots",
            ],
            "memory_percent": [
                "Check for memory leaks in application code",
                "Review database connection pool settings",
                "Analyze heap dumps to identify memory usage",
                "Consider increasing available memory or scaling",
            ],
            "disk_percent": [
                "Clean up old log files and temporary data",
                "Archive or delete old database backups",
                "Review application data retention policies",
                "Consider adding more disk space",
            ],
            "response_time": [
                "Analyze slow database queries",
                "Check for external API timeouts",
                "Review application performance profiling",
                "Consider adding caching layers",
            ],
        }

        return recommendations.get(
            metric_name,
            [
                f"Investigate {metric_name} on {resource}",
                "Review application logs for related errors",
                "Check system resources (CPU, memory, disk)",
            ],
        )

    def _generate_error_recommendations(
        self, error_type: str, error_message: str, stack_trace: str
    ) -> List[str]:
        """Generate specific recommendations based on error details"""
        recommendations = []

        # Database-related errors
        if "database" in error_type.lower() or "connection" in error_message.lower():
            recommendations.extend([
                "Check database server status and connectivity",
                "Verify database credentials and permissions",
                "Review connection pool configuration",
                "Check for database locks or long-running transactions",
            ])

        # Memory-related errors
        if "memory" in error_type.lower() or "OOM" in error_message:
            recommendations.extend([
                "Analyze heap dumps to identify memory leaks",
                "Review recent code changes for memory-intensive operations",
                "Check for unbounded caches or collections",
                "Consider increasing available memory",
            ])

        # Timeout errors
        if "timeout" in error_type.lower() or "timeout" in error_message.lower():
            recommendations.extend([
                "Check external API response times",
                "Review timeout configuration values",
                "Implement retry logic with exponential backoff",
                "Add circuit breaker pattern for failing dependencies",
            ])

        # Generic recommendations
        if not recommendations:
            recommendations.extend([
                "Review full stack trace in logs",
                "Check for similar errors in monitoring system",
                "Verify all service dependencies are healthy",
                "Review recent deployments or configuration changes",
            ])

        return recommendations
