"""
Registration module for CQRS handlers.
Registers all command and query handlers with their respective buses.
"""
from api.app.cqrs.base import register_command_handler, register_query_handler
from api.app.cqrs.command_handlers import (
    CreateBookingCommandHandler,
    ReceiveMessageCommandHandler,
    RecordPaymentCommandHandler,
)
from api.app.cqrs.crm_operations import *
from api.app.cqrs.query_handlers import (
    GetAvailabilitySlotsQueryHandler,
    GetBookingQueryHandler,
    GetBookingsQueryHandler,
    GetCustomer360QueryHandler,
    GetDashboardStatsQueryHandler,
    GetMessageThreadQueryHandler,
)


# Register command handlers
@register_command_handler(CreateBookingCommand)
class RegisteredCreateBookingCommandHandler(CreateBookingCommandHandler):
    """Registered create booking command handler."""
    pass


@register_command_handler(RecordPaymentCommand)
class RegisteredRecordPaymentCommandHandler(RecordPaymentCommandHandler):
    """Registered record payment command handler."""
    pass


@register_command_handler(ReceiveMessageCommand)
class RegisteredReceiveMessageCommandHandler(ReceiveMessageCommandHandler):
    """Registered receive message command handler."""
    pass


# Register query handlers
@register_query_handler(GetBookingQuery)
class RegisteredGetBookingQueryHandler(GetBookingQueryHandler):
    """Registered get booking query handler."""
    pass


@register_query_handler(GetBookingsQuery)
class RegisteredGetBookingsQueryHandler(GetBookingsQueryHandler):
    """Registered get bookings query handler."""
    pass


@register_query_handler(GetCustomer360Query)
class RegisteredGetCustomer360QueryHandler(GetCustomer360QueryHandler):
    """Registered get customer 360 query handler."""
    pass


@register_query_handler(GetMessageThreadQuery)
class RegisteredGetMessageThreadQueryHandler(GetMessageThreadQueryHandler):
    """Registered get message thread query handler."""
    pass


@register_query_handler(GetAvailabilitySlotsQuery)
class RegisteredGetAvailabilitySlotsQueryHandler(GetAvailabilitySlotsQueryHandler):
    """Registered get availability slots query handler."""
    pass


@register_query_handler(GetDashboardStatsQuery)
class RegisteredGetDashboardStatsQueryHandler(GetDashboardStatsQueryHandler):
    """Registered get dashboard stats query handler."""
    pass


def initialize_cqrs_handlers():
    """
    Initialize CQRS system by importing this module.
    This ensures all handlers are registered with their respective buses.
    """
    print("✅ CQRS handlers registered successfully")
    print("  📨 Command Handlers: CreateBooking, RecordPayment, ReceiveMessage")
    print("  🔍 Query Handlers: GetBooking, GetBookings, Customer360, MessageThread, Availability, Dashboard")


# Auto-initialize when module is imported
initialize_cqrs_handlers()


__all__ = [
    "initialize_cqrs_handlers",
    "RegisteredCreateBookingCommandHandler",
    "RegisteredRecordPaymentCommandHandler",
    "RegisteredReceiveMessageCommandHandler",
    "RegisteredGetBookingQueryHandler",
    "RegisteredGetBookingsQueryHandler",
    "RegisteredGetCustomer360QueryHandler",
    "RegisteredGetMessageThreadQueryHandler",
    "RegisteredGetAvailabilitySlotsQueryHandler",
    "RegisteredGetDashboardStatsQueryHandler"
]
