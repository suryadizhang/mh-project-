"""
Email Service Abstraction Layer
Provides clean interface for sending emails with support for multiple providers.
Follows dependency injection pattern for easy testing and provider switching.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol
from enum import Enum


class EmailPriority(str, Enum):
    """Email priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class EmailAddress:
    """Email address with optional display name"""
    email: str
    name: str | None = None
    
    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


@dataclass
class EmailAttachment:
    """Email attachment data"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    """Complete email message with all metadata"""
    to: list[EmailAddress]
    subject: str
    html_body: str
    text_body: str | None = None
    from_address: EmailAddress | None = None
    cc: list[EmailAddress] | None = None
    bcc: list[EmailAddress] | None = None
    reply_to: EmailAddress | None = None
    attachments: list[EmailAttachment] | None = None
    headers: dict[str, str] | None = None
    priority: EmailPriority = EmailPriority.NORMAL
    tags: list[str] | None = None
    
    def __post_init__(self):
        """Ensure lists are initialized"""
        if self.cc is None:
            self.cc = []
        if self.bcc is None:
            self.bcc = []
        if self.attachments is None:
            self.attachments = []
        if self.headers is None:
            self.headers = {}
        if self.tags is None:
            self.tags = []


@dataclass
class EmailResult:
    """Result of email send operation"""
    success: bool
    message_id: str | None = None
    error: str | None = None
    provider: str | None = None
    metadata: dict[str, Any] | None = None


class IEmailProvider(Protocol):
    """Protocol for email provider implementations"""
    
    async def send(self, message: EmailMessage) -> EmailResult:
        """Send an email message"""
        ...
    
    async def send_bulk(self, messages: list[EmailMessage]) -> list[EmailResult]:
        """Send multiple emails (batch operation)"""
        ...
    
    def get_provider_name(self) -> str:
        """Get the provider name"""
        ...


class BaseEmailProvider(ABC):
    """Base class for email providers with common functionality"""
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration"""
        pass
    
    @abstractmethod
    async def send(self, message: EmailMessage) -> EmailResult:
        """Send an email message"""
        pass
    
    async def send_bulk(self, messages: list[EmailMessage]) -> list[EmailResult]:
        """Default bulk send implementation (can be overridden)"""
        results = []
        for message in messages:
            result = await self.send(message)
            results.append(result)
        return results
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name"""
        pass
    
    def _format_address(self, address: EmailAddress) -> str:
        """Format email address with optional name"""
        return str(address)
    
    def _format_addresses(self, addresses: list[EmailAddress]) -> str:
        """Format list of addresses"""
        return ", ".join(str(addr) for addr in addresses)


class EmailProviderFactory:
    """Factory for creating email provider instances"""
    
    _providers: dict[str, type[BaseEmailProvider]] = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type[BaseEmailProvider]) -> None:
        """Register a new email provider"""
        cls._providers[name] = provider_class
    
    @classmethod
    def create_provider(cls, name: str, config: dict[str, Any]) -> BaseEmailProvider:
        """Create a provider instance"""
        if name not in cls._providers:
            raise ValueError(f"Unknown email provider: {name}")
        
        provider_class = cls._providers[name]
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of registered providers"""
        return list(cls._providers.keys())
