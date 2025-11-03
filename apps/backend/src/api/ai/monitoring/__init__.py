"""
Monitoring Module - Cost and Growth Tracking

Tracks API usage, costs, and customer growth to trigger automatic
scaling alerts when thresholds are crossed.
"""

from .alerts import AlertManager, get_alert_manager
from .cost_monitor import CostMonitor, get_cost_monitor
from .growth_tracker import GrowthTracker, get_growth_tracker
from .pricing import (
    DAILY_ALERT_THRESHOLD,
    MONTHLY_ALERT_THRESHOLD,
    PRICES_USD_PER_1K_TOKENS,
    calculate_cost,
    get_model_pricing,
)
from .usage_tracker import UsageTracker, get_usage_tracker

__all__ = [
    "DAILY_ALERT_THRESHOLD",
    "MONTHLY_ALERT_THRESHOLD",
    # Pricing
    "PRICES_USD_PER_1K_TOKENS",
    # Alerts
    "AlertManager",
    # Cost monitoring
    "CostMonitor",
    # Growth tracking
    "GrowthTracker",
    # Usage tracking
    "UsageTracker",
    "calculate_cost",
    "get_alert_manager",
    "get_cost_monitor",
    "get_growth_tracker",
    "get_model_pricing",
    "get_usage_tracker",
]
