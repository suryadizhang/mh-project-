"""
Smart Scheduling System Services

This module provides intelligent booking and chef scheduling optimization:
- Travel time calculation (Google Maps integration)
- Slot management with flexible adjustment
- Smart availability suggestions
- Chef assignment optimization
- Booking negotiation system
- Geocoding (address to coordinates)

Business Rules:
- Event duration: min(60 + (guests × 3), 120) minutes
- 4 time slots per day: 12PM, 3PM, 6PM, 9PM
- Slots adjustable: 12PM (0,+60), 3PM (-30,+60), 6PM (-60,+60), 9PM (-60,+30)
- Rush hour (Mon-Fri 3-7 PM) = travel time × 1.5
- Buffer time: 15 minutes between events
- Customer chef preference takes priority over optimization
- Last booked party adjusts when conflicts arise
"""

from .slot_manager import SlotManagerService, SlotConfig
from .suggestion_engine import SuggestionEngine, SlotAvailability, SuggestionResult
from .travel_time_service import TravelTimeService, TravelTimeResult
from .geocoding_service import GeocodingService, GeocodedAddress
from .chef_optimizer_service import ChefOptimizerService, ChefScore, AssignmentRecommendation
from .negotiation_service import (
    NegotiationService,
    NegotiationRequest,
    NegotiationResult,
    NegotiationStatus,
    NegotiationReason,
    ShiftProposal,
)

__all__ = [
    # Core Services
    "SlotManagerService",
    "SuggestionEngine",
    "TravelTimeService",
    "GeocodingService",
    "ChefOptimizerService",
    "NegotiationService",
    # Data Classes
    "SlotConfig",
    "SlotAvailability",
    "SuggestionResult",
    "TravelTimeResult",
    "GeocodedAddress",
    "ChefScore",
    "AssignmentRecommendation",
    "NegotiationRequest",
    "NegotiationResult",
    "ShiftProposal",
    # Enums
    "NegotiationStatus",
    "NegotiationReason",
]
