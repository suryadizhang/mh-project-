"""
Monitoring Module - Cost and Growth Tracking

Tracks API usage, costs, and customer growth to trigger automatic
scaling alerts when thresholds are crossed.
"""

from .pricing import (
    PRICES_USD_PER_1K_TOKENS,
    get_model_pricing,
    calculate_cost,
    MONTHLY_ALERT_THRESHOLD,
    DAILY_ALERT_THRESHOLD
)
from .usage_tracker import UsageTracker, get_usage_tracker
from .cost_monitor import CostMonitor, get_cost_monitor
from .growth_tracker import GrowthTracker, get_growth_tracker
from .alerts import AlertManager, get_alert_manager

__all__ = [
    # Pricing
    "PRICES_USD_PER_1K_TOKENS",
    "get_model_pricing",
    "calculate_cost",
    "MONTHLY_ALERT_THRESHOLD",
    "DAILY_ALERT_THRESHOLD",
    
    # Usage tracking
    "UsageTracker",
    "get_usage_tracker",
    
    # Cost monitoring
    "CostMonitor",
    "get_cost_monitor",
    
    # Growth tracking
    "GrowthTracker",
    "get_growth_tracker",
    
    # Alerts
    "AlertManager",
    "get_alert_manager",
]
