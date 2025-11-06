"""
Booking Queries
Re-exports booking-related queries from crm_operations for cleaner imports
"""

from cqrs.crm_operations import (
    GetBookingsQuery,
    GetBookingQuery,
)

__all__ = [
    "GetBookingsQuery",
    "GetBookingQuery",
    # Alias for backward compatibility
    "GetBookingByIdQuery",
]

# Alias for backward compatibility
GetBookingByIdQuery = GetBookingQuery
