"""
Alert Data Models

Database models for storing and managing system alerts.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import JSON, Column, DateTime, Enum as SQLEnum, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

from models.base import Base


class AlertStatus(str, Enum):
    """Alert status states"""

    ACTIVE = "active"  # Alert is currently active
    ACKNOWLEDGED = "acknowledged"  # Alert has been seen by admin
    RESOLVED = "resolved"  # Issue has been fixed
    SUPPRESSED = "suppressed"  # Alert is temporarily muted
    EXPIRED = "expired"  # Alert auto-resolved after timeout


class AlertPriority(str, Enum):
    """Alert priority levels"""

    CRITICAL = "critical"  # Immediate action required (system down)
    HIGH = "high"  # Urgent attention needed (degraded performance)
    MEDIUM = "medium"  # Should be addressed soon (warnings)
    LOW = "low"  # Informational (notifications)
    INFO = "info"  # Just for tracking (analytics)


class NotificationChannel(str, Enum):
    """Notification delivery channels"""

    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"
    DASHBOARD = "dashboard"  # In-app notification only


class AlertModel(Base):
    """
    Alert storage model

    Stores system alerts with metadata for tracking, notification, and resolution.
    """

    __tablename__ = "monitoring_alerts"

    id = Column(Integer, primary_key=True, index=True)

    # Alert identification
    alert_type = Column(String(100), nullable=False, index=True)  # cpu, memory, service_down, etc.
    category = Column(String(50), nullable=False, index=True)  # system, application, business
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    # Priority and status
    priority = Column(SQLEnum(AlertPriority), nullable=False, default=AlertPriority.MEDIUM, index=True)
    status = Column(SQLEnum(AlertStatus), nullable=False, default=AlertStatus.ACTIVE, index=True)

    # Context and metadata
    source = Column(String(100), nullable=True)  # Which component triggered alert
    resource = Column(String(255), nullable=True)  # Affected resource (server, service, etc.)
    metadata = Column(JSON, nullable=True)  # Additional context data

    # Metrics that triggered alert
    metric_name = Column(String(100), nullable=True)
    metric_value = Column(String(50), nullable=True)
    threshold_value = Column(String(50), nullable=True)

    # Notification tracking
    notification_channels = Column(JSON, nullable=True)  # List of channels notified
    notification_sent_at = Column(DateTime, nullable=True)
    notification_count = Column(Integer, default=0)

    # Resolution tracking
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)

    # Suppression
    suppressed_until = Column(DateTime, nullable=True)
    suppressed_by = Column(String(100), nullable=True)
    suppression_reason = Column(Text, nullable=True)

    # Timestamps
    triggered_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=True)  # Auto-resolve after this time

    def __repr__(self):
        return (
            f"<AlertModel(id={self.id}, type={self.alert_type}, "
            f"priority={self.priority}, status={self.status})>"
        )

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "alert_type": self.alert_type,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "source": self.source,
            "resource": self.resource,
            "metadata": self.metadata,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold_value": self.threshold_value,
            "notification_channels": self.notification_channels,
            "notification_sent_at": self.notification_sent_at.isoformat() if self.notification_sent_at else None,
            "notification_count": self.notification_count,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "suppressed_until": self.suppressed_until.isoformat() if self.suppressed_until else None,
            "suppressed_by": self.suppressed_by,
            "suppression_reason": self.suppression_reason,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class AlertRule(Base):
    """
    Alert Rule configuration

    Defines when and how alerts should be triggered based on metric thresholds.
    """

    __tablename__ = "monitoring_alert_rules"

    id = Column(Integer, primary_key=True, index=True)

    # Rule identification
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    alert_type = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)

    # Monitoring configuration
    metric_name = Column(String(100), nullable=False)
    operator = Column(String(20), nullable=False)  # gt, lt, eq, gte, lte
    threshold = Column(String(50), nullable=False)
    duration_seconds = Column(Integer, default=0)  # How long condition must persist

    # Alert configuration
    priority = Column(SQLEnum(AlertPriority), nullable=False, default=AlertPriority.MEDIUM)
    notification_channels = Column(JSON, nullable=True)  # Which channels to notify
    cooldown_seconds = Column(Integer, default=300)  # Minimum time between alerts

    # Rule state
    is_enabled = Column(Integer, default=1)  # Boolean as integer
    last_triggered_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<AlertRule(id={self.id}, name={self.name}, enabled={bool(self.is_enabled)})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "alert_type": self.alert_type,
            "category": self.category,
            "metric_name": self.metric_name,
            "operator": self.operator,
            "threshold": self.threshold,
            "duration_seconds": self.duration_seconds,
            "priority": self.priority.value if self.priority else None,
            "notification_channels": self.notification_channels,
            "cooldown_seconds": self.cooldown_seconds,
            "is_enabled": bool(self.is_enabled),
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
