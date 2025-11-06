"""
Booking Commands
Re-exports booking-related commands from crm_operations for cleaner imports
"""

from cqrs.crm_operations import (
    CreateBookingCommand,
    UpdateBookingCommand,
    CancelBookingCommand,
)

__all__ = [
    "CreateBookingCommand",
    "UpdateBookingCommand",
    "CancelBookingCommand",
    # Alias for backward compatibility
    "DeleteBookingCommand",
]

# Alias for backward compatibility
DeleteBookingCommand = CancelBookingCommand
