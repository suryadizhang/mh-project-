"""
Lead Commands
Placeholder for lead-related commands (to be implemented)
"""

from cqrs.base import Command


class CreateLeadCommand(Command):
    """Command to create a new lead (placeholder)"""

    pass


class UpdateLeadCommand(Command):
    """Command to update a lead (placeholder)"""

    pass


class DeleteLeadCommand(Command):
    """Command to delete a lead (placeholder)"""

    pass


__all__ = [
    "CreateLeadCommand",
    "UpdateLeadCommand",
    "DeleteLeadCommand",
]
