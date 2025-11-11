"""
Registration module for CQRS handlers.
Registers all command and query handlers with their respective buses.
"""

from cqrs.base import (
    register_command_handler,
    register_query_handler,
)  # Phase 2C: Updated from api.app.cqrs.base
from cqrs.command_handlers import (  # Phase 2C: Updated from api.app.cqrs.command_handlers
    CreateBookingCommandHandler,
    ReceiveMessageCommandHandler,
    RecordPaymentCommandHandler,
)
from cqrs.crm_operations import *  # Phase 2C: Updated from api.app.cqrs.crm_operations
from cqrs.query_handlers import (  # Phase 2C: Updated from api.app.cqrs.query_handlers
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


@register_command_handler(RecordPaymentCommand)
class RegisteredRecordPaymentCommandHandler(RecordPaymentCommandHandler):
    """Registered record payment command handler."""


@register_command_handler(ReceiveMessageCommand)
class RegisteredReceiveMessageCommandHandler(ReceiveMessageCommandHandler):
    """Registered receive message command handler."""


# Register query handlers
@register_query_handler(GetBookingQuery)
class RegisteredGetBookingQueryHandler(GetBookingQueryHandler):
    """Registered get booking query handler."""


@register_query_handler(GetBookingsQuery)
class RegisteredGetBookingsQueryHandler(GetBookingsQueryHandler):
    """Registered get bookings query handler."""


@register_query_handler(GetCustomer360Query)
class RegisteredGetCustomer360QueryHandler(GetCustomer360QueryHandler):
    """Registered get customer 360 query handler."""


@register_query_handler(GetMessageThreadQuery)
class RegisteredGetMessageThreadQueryHandler(GetMessageThreadQueryHandler):
    """Registered get message thread query handler."""


@register_query_handler(GetAvailabilitySlotsQuery)
class RegisteredGetAvailabilitySlotsQueryHandler(GetAvailabilitySlotsQueryHandler):
    """Registered get availability slots query handler."""


@register_query_handler(GetDashboardStatsQuery)
class RegisteredGetDashboardStatsQueryHandler(GetDashboardStatsQueryHandler):
    """Registered get dashboard stats query handler."""


def initialize_cqrs_handlers():
    """
    Initialize CQRS system by importing this module.
    This ensures all handlers are registered with their respective buses.
    """


# Auto-initialize when module is imported
initialize_cqrs_handlers()


__all__ = [
    "RegisteredCreateBookingCommandHandler",
    "RegisteredGetAvailabilitySlotsQueryHandler",
    "RegisteredGetBookingQueryHandler",
    "RegisteredGetBookingsQueryHandler",
    "RegisteredGetCustomer360QueryHandler",
    "RegisteredGetDashboardStatsQueryHandler",
    "RegisteredGetMessageThreadQueryHandler",
    "RegisteredReceiveMessageCommandHandler",
    "RegisteredRecordPaymentCommandHandler",
    "initialize_cqrs_handlers",
]
