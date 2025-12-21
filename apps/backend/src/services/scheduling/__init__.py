"""
Smart Scheduling System - Service Layer

This package contains all scheduling-related services for:
- Travel time calculation
- Slot management
- Availability checking
- Chef optimization
- Booking negotiations
- Address geocoding (with caching)
"""

from .travel_time_service import TravelTimeService
from .slot_manager import SlotManager, SlotManagerService
from .suggestion_engine import SuggestionEngine
from .negotiation_service import NegotiationService, NegotiationReason
from .geocoding_service import GeocodingService

# Optional imports (may not exist yet)
try:
    from .availability_engine import AvailabilityEngine
except ImportError:
    AvailabilityEngine = None  # type: ignore

try:
    from .chef_optimizer import ChefOptimizer, ChefOptimizerService
except ImportError:
    ChefOptimizer = None  # type: ignore
    ChefOptimizerService = None  # type: ignore

__all__ = [
    "TravelTimeService",
    "SlotManager",
    "SlotManagerService",
    "AvailabilityEngine",
    "ChefOptimizer",
    "ChefOptimizerService",
    "SuggestionEngine",
    "NegotiationService",
    "NegotiationReason",
    "GeocodingService",
]
