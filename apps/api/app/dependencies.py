"""
Dependency injection functions for FastAPI endpoints.
Provides access to CQRS buses and authentication.
"""

from app.cqrs.base import CommandBus, QueryBus, command_bus, query_bus
from app.utils.auth import get_admin_user


def get_command_bus() -> CommandBus:
    """Provide access to the command bus."""
    return command_bus


def get_query_bus() -> QueryBus:
    """Provide access to the query bus."""
    return query_bus


# Alias for compatibility with existing imports
get_current_admin_user = get_admin_user
