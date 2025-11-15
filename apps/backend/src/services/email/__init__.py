"""Email service package initialization"""

from .base import (
    EmailAddress,
    EmailAttachment,
    EmailMessage,
    EmailResult,
    EmailPriority,
    IEmailProvider,
    BaseEmailProvider,
    EmailProviderFactory,
)
from .newsletter_service import AdminEmailService  # Note: NOT for newsletters! Newsletters use SMS

__all__ = [
    "EmailAddress",
    "EmailAttachment",
    "EmailMessage",
    "EmailResult",
    "EmailPriority",
    "IEmailProvider",
    "BaseEmailProvider",
    "EmailProviderFactory",
    "AdminEmailService",  # For admin emails only, NOT newsletters!
]
