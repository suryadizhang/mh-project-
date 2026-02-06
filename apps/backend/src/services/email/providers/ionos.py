"""
IONOS SMTP Email Provider
Implements email sending via IONOS SMTP service with full CAN-SPAM compliance.
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Any

from ..base import (
    BaseEmailProvider,
    EmailMessage,
    EmailResult,
    EmailAddress,
    EmailPriority,
)


logger = logging.getLogger(__name__)


class IONOSEmailProvider(BaseEmailProvider):
    """IONOS SMTP email provider with TLS support"""

    def _validate_config(self) -> None:
        """Validate IONOS SMTP configuration"""
        required_keys = ["smtp_host", "smtp_port", "smtp_user", "smtp_password"]
        missing = [key for key in required_keys if key not in self.config]
        if missing:
            raise ValueError(f"Missing required config keys: {missing}")

    def get_provider_name(self) -> str:
        return "ionos_smtp"

    async def send(self, message: EmailMessage) -> EmailResult:
        """
        Send email via IONOS SMTP with comprehensive error handling.

        Supports:
        - HTML and plain text bodies
        - Attachments
        - Custom headers (including List-Unsubscribe)
        - CC/BCC recipients
        - Reply-To addresses
        """
        try:
            # Create MIME message
            mime_msg = self._create_mime_message(message)

            # Connect to SMTP server with retry logic
            result = await self._send_with_retry(mime_msg, message)

            logger.info(
                f"✅ Email sent successfully via IONOS SMTP: '{message.subject}' to {len(message.to)} recipients",
                extra={
                    "provider": "ionos_smtp",
                    "subject": message.subject,
                    "recipients": len(message.to),
                    "has_attachments": len(message.attachments) > 0,
                },
            )

            return result

        except Exception as e:
            logger.exception(
                f"❌ Failed to send email via IONOS SMTP: {e}",
                extra={
                    "subject": message.subject,
                    "recipients": len(message.to),
                    "error": str(e),
                },
            )
            return EmailResult(
                success=False,
                error=str(e),
                provider="ionos_smtp",
            )

    def _create_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Create MIME message from EmailMessage"""
        mime_msg = MIMEMultipart("alternative")

        # Set headers
        mime_msg["Subject"] = message.subject
        mime_msg["From"] = self._format_from_address(message)
        mime_msg["To"] = self._format_addresses(message.to)

        if message.cc:
            mime_msg["Cc"] = self._format_addresses(message.cc)

        if message.reply_to:
            mime_msg["Reply-To"] = str(message.reply_to)

        # Add priority header
        if message.priority != EmailPriority.NORMAL:
            priority_map = {
                EmailPriority.LOW: "5",
                EmailPriority.HIGH: "2",
                EmailPriority.URGENT: "1",
            }
            mime_msg["X-Priority"] = priority_map.get(message.priority, "3")

        # Add custom headers (including List-Unsubscribe for CAN-SPAM)
        for header_name, header_value in message.headers.items():
            mime_msg[header_name] = header_value

        # Add message bodies
        if message.text_body:
            text_part = MIMEText(message.text_body, "plain", "utf-8")
            mime_msg.attach(text_part)

        html_part = MIMEText(message.html_body, "html", "utf-8")
        mime_msg.attach(html_part)

        # Add attachments
        for attachment in message.attachments:
            self._attach_file(mime_msg, attachment)

        return mime_msg

    def _format_from_address(self, message: EmailMessage) -> str:
        """Format From address using config or message override"""
        if message.from_address:
            return str(message.from_address)

        from_email = self.config["smtp_user"]
        from_name = self.config.get("from_name", "My Hibachi Chef")
        return f"{from_name} <{from_email}>"

    def _attach_file(self, mime_msg: MIMEMultipart, attachment: Any) -> None:
        """Attach file to MIME message"""
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.content)
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {attachment.filename}",
        )
        mime_msg.attach(part)

    async def _send_with_retry(
        self, mime_msg: MIMEMultipart, message: EmailMessage, max_retries: int = 3
    ) -> EmailResult:
        """
        Send email with retry logic for transient failures.

        Retries on:
        - Connection timeouts
        - Temporary SMTP errors (4xx codes)

        Does NOT retry on:
        - Authentication errors (invalid credentials)
        - Permanent failures (5xx codes)
        """
        import asyncio
        from smtplib import SMTPException, SMTPAuthenticationError

        smtp_host = self.config["smtp_host"]
        smtp_port = int(self.config["smtp_port"])
        smtp_user = self.config["smtp_user"]
        smtp_password = self.config["smtp_password"]
        use_tls = self.config.get("smtp_use_tls", True)
        timeout = self.config.get("timeout", 30)

        # Collect all recipients
        all_recipients = [addr.email for addr in message.to]
        if message.cc:
            all_recipients.extend([addr.email for addr in message.cc])
        if message.bcc:
            all_recipients.extend([addr.email for addr in message.bcc])

        for attempt in range(max_retries):
            try:
                # Run SMTP operation in executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self._smtp_send,
                    smtp_host,
                    smtp_port,
                    smtp_user,
                    smtp_password,
                    use_tls,
                    timeout,
                    mime_msg,
                    all_recipients,
                )

                # Success!
                return EmailResult(
                    success=True,
                    message_id=mime_msg.get("Message-ID"),
                    provider="ionos_smtp",
                    metadata={
                        "attempt": attempt + 1,
                        "recipients": len(all_recipients),
                    },
                )

            except SMTPAuthenticationError as e:
                # Don't retry authentication errors
                logger.error(f"❌ SMTP Authentication failed: {e}")
                return EmailResult(
                    success=False,
                    error=f"Authentication failed: {e}",
                    provider="ionos_smtp",
                )

            except (ConnectionError, TimeoutError, SMTPException) as e:
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"⚠️ SMTP error (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ SMTP failed after {max_retries} attempts: {e}")
                    return EmailResult(
                        success=False,
                        error=f"Failed after {max_retries} attempts: {e}",
                        provider="ionos_smtp",
                        metadata={"attempts": max_retries},
                    )

        # Should never reach here, but just in case
        return EmailResult(
            success=False,
            error="Unexpected error in retry logic",
            provider="ionos_smtp",
        )

    def _smtp_send(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        use_tls: bool,
        timeout: int,
        mime_msg: MIMEMultipart,
        recipients: list[str],
    ) -> None:
        """Synchronous SMTP send operation (runs in executor)"""
        with smtplib.SMTP(host, port, timeout=timeout) as server:
            # Enable debug output in development
            # server.set_debuglevel(1)

            if use_tls:
                server.starttls()

            server.login(user, password)
            server.send_message(mime_msg, to_addrs=recipients)


# Register provider with factory
from ..base import EmailProviderFactory

EmailProviderFactory.register_provider("ionos", IONOSEmailProvider)
