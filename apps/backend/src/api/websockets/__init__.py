"""
WebSocket Managers Module
=========================

Provides WebSocket connection managers for real-time functionality.

Modules:
    - escalation_manager: Manages escalation notification WebSocket connections
    - compliance_manager: Manages compliance monitoring WebSocket connections
"""

from .escalation_manager import get_escalation_ws_manager
from .compliance_manager import get_compliance_ws_manager

__all__ = [
    "get_escalation_ws_manager",
    "get_compliance_ws_manager",
]
