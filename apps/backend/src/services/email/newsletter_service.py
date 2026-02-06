"""
Admin Email Service (NOT for newsletters - newsletters use SMS!)
High-level service for sending admin/transactional emails with CAN-SPAM compliance.

IMPORTANT: This service is ONLY for admin/transactional emails like:
- Invoice copies
- Booking confirmations
- Account notifications
- Password resets

Marketing newsletters are sent via SMS (RingCentral), NOT email!

Uses dependency injection for email provider.
"""

import logging
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .base import (
    EmailAddress,
    EmailMessage,
    EmailResult,
    IEmailProvider,
)


logger = logging.getLogger(__name__)


class IComplianceValidator(Protocol):
    """Protocol for compliance validation"""

    def generate_unsubscribe_url(self, email: str, secret_key: str) -> str:
        """Generate secure unsubscribe URL"""
        ...

    def get_email_footer_html(self, unsubscribe_url: str) -> str:
        """Get CAN-SPAM compliant email footer"""
        ...


class AdminEmailService:
    """
    Service for sending admin/transactional emails with full CAN-SPAM compliance.

    IMPORTANT: This is NOT for marketing newsletters! Newsletters use SMS via RingCentral.

    Use Cases:
    - Invoice copies
    - Booking confirmations
    - Account notifications
    - Password reset emails

    Features:
    - Unique unsubscribe URLs per subscriber
    - List-Unsubscribe headers for Gmail/Outlook
    - CAN-SPAM compliant footers
    - Batch sending support
    - Event tracking integration
    """

    def __init__(
        self,
        email_provider: IEmailProvider,
        compliance_validator: IComplianceValidator,
        secret_key: str,
        from_email: str = "cs@myhibachichef.com",
        from_name: str = "My Hibachi Chef",
    ):
        """
        Initialize newsletter email service.

        Args:
            email_provider: Email provider implementation (IONOS, SendGrid, etc.)
            compliance_validator: Compliance validation service
            secret_key: Secret key for HMAC token generation
            from_email: Default from email address
            from_name: Default from name
        """
        self.email_provider = email_provider
        self.compliance_validator = compliance_validator
        self.secret_key = secret_key
        self.from_email = from_email
        self.from_name = from_name

    async def send_campaign_email(
        self,
        subscriber_email: str,
        subscriber_name: str | None,
        subject: str,
        html_body: str,
        text_body: str | None = None,
        campaign_id: UUID | None = None,
        tags: list[str] | None = None,
    ) -> EmailResult:
        """
        Send a single campaign email with full CAN-SPAM compliance.

        Args:
            subscriber_email: Recipient email address
            subscriber_name: Recipient name (optional)
            subject: Email subject line
            html_body: HTML email body (may contain {{unsubscribe_url}} placeholder)
            text_body: Plain text email body (optional)
            campaign_id: Campaign UUID for tracking
            tags: Email tags for analytics

        Returns:
            EmailResult with send status
        """
        try:
            # Generate secure unsubscribe URL
            unsubscribe_url = self.compliance_validator.generate_unsubscribe_url(
                email=subscriber_email,
                secret_key=self.secret_key,
            )

            # Replace placeholder in body
            personalized_html = html_body.replace("{{unsubscribe_url}}", unsubscribe_url)

            # Add CAN-SPAM compliant footer
            footer_html = self.compliance_validator.get_email_footer_html(unsubscribe_url)
            final_html = f"{personalized_html}\n{footer_html}"

            # Prepare text body
            final_text = text_body or self._html_to_text(personalized_html)
            final_text += f"\n\nUnsubscribe: {unsubscribe_url}"

            # Create email message
            message = EmailMessage(
                to=[EmailAddress(email=subscriber_email, name=subscriber_name)],
                subject=subject,
                html_body=final_html,
                text_body=final_text,
                from_address=EmailAddress(email=self.from_email, name=self.from_name),
                headers={
                    "List-Unsubscribe": f"<{unsubscribe_url}>",
                    "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
                },
                tags=tags or [],
            )

            # Add campaign ID to tags if provided
            if campaign_id:
                message.tags.append(f"campaign:{campaign_id}")

            # Send email via provider
            result = await self.email_provider.send(message)

            if result.success:
                logger.info(
                    f"✅ Campaign email sent: {subscriber_email}",
                    extra={
                        "email": subscriber_email,
                        "campaign_id": str(campaign_id) if campaign_id else None,
                        "provider": result.provider,
                    },
                )
            else:
                logger.error(
                    f"❌ Campaign email failed: {subscriber_email} - {result.error}",
                    extra={
                        "email": subscriber_email,
                        "campaign_id": str(campaign_id) if campaign_id else None,
                        "error": result.error,
                    },
                )

            return result

        except Exception as e:
            logger.exception(f"❌ Unexpected error sending campaign email: {e}")
            return EmailResult(
                success=False,
                error=str(e),
                provider=self.email_provider.get_provider_name(),
            )

    async def send_campaign_batch(
        self,
        recipients: list[dict],  # [{"email": "...", "name": "..."}]
        subject: str,
        html_body: str,
        text_body: str | None = None,
        campaign_id: UUID | None = None,
        tags: list[str] | None = None,
    ) -> list[EmailResult]:
        """
        Send campaign emails to multiple recipients in batch.

        Each recipient gets a unique unsubscribe URL.

        Args:
            recipients: List of recipient dicts with 'email' and optional 'name'
            subject: Email subject line
            html_body: HTML email body template
            text_body: Plain text email body template (optional)
            campaign_id: Campaign UUID for tracking
            tags: Email tags for analytics

        Returns:
            List of EmailResult for each recipient
        """
        results = []

        for recipient in recipients:
            result = await self.send_campaign_email(
                subscriber_email=recipient["email"],
                subscriber_name=recipient.get("name"),
                subject=subject,
                html_body=html_body,
                text_body=text_body,
                campaign_id=campaign_id,
                tags=tags,
            )
            results.append(result)

        # Log batch summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        logger.info(
            f"📧 Campaign batch complete: {successful} sent, {failed} failed",
            extra={
                "campaign_id": str(campaign_id) if campaign_id else None,
                "total": len(results),
                "successful": successful,
                "failed": failed,
            },
        )

        return results

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (basic implementation)"""
        import re

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", html)

        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')

        # Clean up whitespace
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.strip()

        return text


def create_admin_email_service(
    email_provider: IEmailProvider,
    compliance_validator: IComplianceValidator,
    secret_key: str,
) -> AdminEmailService:
    """
    Factory function for creating AdminEmailService with DI.

    IMPORTANT: This is for admin/transactional emails ONLY.
    Marketing newsletters use SMS via RingCentral!

    This is the recommended way to create the service for easier testing.
    """
    return AdminEmailService(
        email_provider=email_provider,
        compliance_validator=compliance_validator,
        secret_key=secret_key,
    )
