"""
Alert Rule Models - Database Models for Threshold Monitoring Rules

Defines the schema for alert rules that monitor metrics and trigger alerts
when thresholds are exceeded.

Created: November 10, 2025
Part of: Week 2 - ThresholdMonitor Implementation
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Enum as SQLEnum, JSON, DateTime
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from database.base_class import Base


class ThresholdOperator(str, Enum):
    """Threshold comparison operators"""
    GREATER_THAN = "gt"  # >
    GREATER_THAN_OR_EQUAL = "gte"  # >=
    LESS_THAN = "lt"  # <
    LESS_THAN_OR_EQUAL = "lte"  # <=
    EQUAL = "eq"  # ==
    NOT_EQUAL = "neq"  # !=


class RuleSeverity(str, Enum):
    """Rule severity levels"""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"  # Urgent attention needed
    MEDIUM = "medium"  # Should be addressed soon
    LOW = "low"  # Informational
    INFO = "info"  # Just for awareness


class AlertRule(Base):
    """
    Alert rule for threshold monitoring.
    
    Defines conditions under which alerts should be created:
    - Which metric to monitor
    - Threshold value and comparison operator
    - Duration requirement (must exceed for X seconds)
    - Cooldown period (prevent alert spam)
    - Severity level
    """
    
    __tablename__ = "alert_rules"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Rule identification
    name = Column(String(255), nullable=False, index=True, unique=True)
    description = Column(String(1000), nullable=True)
    
    # Metric to monitor
    metric_name = Column(String(100), nullable=False, index=True)
    
    # Threshold definition
    operator = Column(SQLEnum(ThresholdOperator), nullable=False)
    threshold_value = Column(Float, nullable=False)
    
    # Duration requirement (seconds)
    # Alert only if threshold exceeded for this long
    duration_seconds = Column(Integer, nullable=False, default=0)
    
    # Cooldown period (seconds)
    # After creating alert, don't create another for this duration
    cooldown_seconds = Column(Integer, nullable=False, default=300)  # 5 minutes default
    
    # Severity
    severity = Column(SQLEnum(RuleSeverity), nullable=False, default=RuleSeverity.MEDIUM)
    
    # Status
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    
    # Alert details
    alert_title_template = Column(String(500), nullable=True)
    alert_message_template = Column(String(2000), nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)  # List of tags for categorization
    metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    trigger_count = Column(Integer, nullable=False, default=0)
    
    def __repr__(self):
        return (
            f"<AlertRule(id={self.id}, name='{self.name}', "
            f"metric='{self.metric_name}', "
            f"condition='{self.operator.value} {self.threshold_value}', "
            f"enabled={self.enabled})>"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "metric_name": self.metric_name,
            "operator": self.operator.value,
            "threshold_value": self.threshold_value,
            "duration_seconds": self.duration_seconds,
            "cooldown_seconds": self.cooldown_seconds,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "alert_title_template": self.alert_title_template,
            "alert_message_template": self.alert_message_template,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_triggered_at": self.last_triggered_at.isoformat() if self.last_triggered_at else None,
            "trigger_count": self.trigger_count,
        }
    
    def get_condition_display(self) -> str:
        """Get human-readable condition."""
        op_symbols = {
            ThresholdOperator.GREATER_THAN: ">",
            ThresholdOperator.GREATER_THAN_OR_EQUAL: ">=",
            ThresholdOperator.LESS_THAN: "<",
            ThresholdOperator.LESS_THAN_OR_EQUAL: "<=",
            ThresholdOperator.EQUAL: "==",
            ThresholdOperator.NOT_EQUAL: "!=",
        }
        
        symbol = op_symbols.get(self.operator, self.operator.value)
        duration_str = f" for {self.duration_seconds}s" if self.duration_seconds > 0 else ""
        
        return f"{self.metric_name} {symbol} {self.threshold_value}{duration_str}"
    
    def format_alert_title(self, current_value: float) -> str:
        """
        Format alert title with current value.
        
        Template variables:
        - {metric_name}: Name of the metric
        - {current_value}: Current metric value
        - {threshold_value}: Threshold value
        - {rule_name}: Name of the rule
        
        Args:
            current_value: Current metric value
            
        Returns:
            Formatted alert title
        """
        if self.alert_title_template:
            return self.alert_title_template.format(
                metric_name=self.metric_name,
                current_value=current_value,
                threshold_value=self.threshold_value,
                rule_name=self.name,
            )
        else:
            # Default template
            return f"{self.name}: {self.metric_name} = {current_value}"
    
    def format_alert_message(self, current_value: float, duration: Optional[float] = None) -> str:
        """
        Format alert message with current value.
        
        Template variables:
        - {metric_name}: Name of the metric
        - {current_value}: Current metric value
        - {threshold_value}: Threshold value
        - {operator}: Operator symbol
        - {rule_name}: Name of the rule
        - {duration}: Duration in seconds (if applicable)
        
        Args:
            current_value: Current metric value
            duration: Duration exceeded (optional)
            
        Returns:
            Formatted alert message
        """
        op_symbols = {
            ThresholdOperator.GREATER_THAN: ">",
            ThresholdOperator.GREATER_THAN_OR_EQUAL: ">=",
            ThresholdOperator.LESS_THAN: "<",
            ThresholdOperator.LESS_THAN_OR_EQUAL: "<=",
            ThresholdOperator.EQUAL: "==",
            ThresholdOperator.NOT_EQUAL: "!=",
        }
        
        if self.alert_message_template:
            return self.alert_message_template.format(
                metric_name=self.metric_name,
                current_value=current_value,
                threshold_value=self.threshold_value,
                operator=op_symbols.get(self.operator, self.operator.value),
                rule_name=self.name,
                duration=duration or 0,
            )
        else:
            # Default template
            duration_str = f" for {duration:.0f}s" if duration else ""
            return (
                f"Alert rule '{self.name}' triggered: "
                f"{self.metric_name} = {current_value} "
                f"({op_symbols.get(self.operator)} {self.threshold_value}){duration_str}"
            )
