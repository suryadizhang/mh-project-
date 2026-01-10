"""
Customer Email Monitor - IONOS IMAP
Monitors cs@myhibachichef.com for incoming customer inquiries, support requests, and replies.

This is SEPARATE from payment monitoring (myhibachichef@gmail.com).
cs@myhibachichef.com = Customer support inbox (IONOS)
myhibachichef@gmail.com = Payment notifications only (Gmail)

Architecture:
- INBOUND: IONOS IMAP (cs@myhibachichef.com) → This service
- OUTBOUND: Resend API (cs@myhibachichef.com) → email_service.py
"""

import email
from email.header import decode_header
from email.message import Message
import imaplib
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


class CustomerEmailMonitor:
    """Monitor IONOS inbox for customer emails"""

    def __init__(
        self,
        email_address: str = "cs@myhibachichef.com",
        password: str = "",
        imap_server: str = "imap.ionos.com",
        imap_port: int = 993,
    ):
        """
        Initialize IONOS IMAP monitor for customer support emails.

        Args:
            email_address: IONOS email address (cs@myhibachichef.com)
            password: IONOS email password (from SMTP_PASSWORD in .env)
            imap_server: IONOS IMAP server
            imap_port: IMAP SSL port (993)
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.imap_connection: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> bool:
        """Connect to IONOS IMAP server"""
        try:
            self.imap_connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.imap_connection.login(self.email_address, self.password)
            logger.info(f"✅ Connected to IONOS IMAP for {self.email_address}")
            return True
        except Exception as e:
            logger.exception(f"❌ Failed to connect to IONOS IMAP: {e}")
            return False

    def disconnect(self):
        """Disconnect from IONOS IMAP server"""
        if self.imap_connection:
            try:
                self.imap_connection.logout()
                logger.info("✅ Disconnected from IONOS IMAP")
            except Exception as e:
                logger.error(f"Error disconnecting from IONOS IMAP: {e}")
            finally:
                self.imap_connection = None

    def _decode_header_value(self, value: str) -> str:
        """Decode email header value (handles UTF-8, base64, etc.)"""
        if not value:
            return ""

        decoded_parts = decode_header(value)
        result = []

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    result.append(part.decode(encoding or "utf-8", errors="ignore"))
                except Exception:
                    result.append(part.decode("utf-8", errors="ignore"))
            else:
                result.append(str(part))

        return " ".join(result)

    def _get_email_body(self, msg: Message) -> tuple[str, str]:
        """
        Extract email body (text and HTML).

        Returns:
            (text_body, html_body)
        """
        text_body = ""
        html_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition"))

                # Skip attachments
                if "attachment" in disposition:
                    continue

                try:
                    body = part.get_payload(decode=True)
                    if body:
                        body_text = body.decode("utf-8", errors="ignore")

                        if content_type == "text/plain":
                            text_body += body_text
                        elif content_type == "text/html":
                            html_body += body_text
                except Exception as e:
                    logger.error(f"Error decoding email part: {e}")
        else:
            # Single part email
            try:
                body = msg.get_payload(decode=True)
                if body:
                    body_text = body.decode("utf-8", errors="ignore")
                    content_type = msg.get_content_type()

                    if content_type == "text/plain":
                        text_body = body_text
                    elif content_type == "text/html":
                        html_body = body_text
            except Exception as e:
                logger.error(f"Error decoding email body: {e}")

        return text_body.strip(), html_body.strip()

    def fetch_unread_emails(self, mark_as_read: bool = False) -> list[dict]:
        """
        Fetch unread customer emails from IONOS inbox.

        Args:
            mark_as_read: Mark emails as read after fetching

        Returns:
            List of email dictionaries with fields:
            - message_id: Email message ID
            - from_address: Sender email
            - from_name: Sender name
            - subject: Email subject
            - text_body: Plain text body
            - html_body: HTML body
            - received_at: Timestamp
            - has_attachments: Boolean
        """
        if not self.imap_connection:
            if not self.connect():
                return []

        try:
            # Select inbox
            self.imap_connection.select("INBOX")

            # Search for unread emails
            _, message_numbers = self.imap_connection.search(None, "UNSEEN")
            email_ids = message_numbers[0].split()

            if not email_ids:
                logger.info("📭 No unread customer emails")
                return []

            logger.info(f"📬 Found {len(email_ids)} unread customer emails")

            emails = []
            for email_id in email_ids:
                try:
                    # Fetch email
                    _, msg_data = self.imap_connection.fetch(email_id, "(RFC822)")
                    email_body = msg_data[0][1]
                    msg = email.message_from_bytes(email_body)

                    # Extract fields
                    from_header = self._decode_header_value(msg.get("From", ""))
                    subject = self._decode_header_value(msg.get("Subject", ""))
                    message_id = msg.get("Message-ID", "")
                    date_str = msg.get("Date", "")

                    # Parse sender (format: "Name <email@example.com>")
                    from_name = ""
                    from_address = from_header
                    if "<" in from_header and ">" in from_header:
                        from_name = from_header.split("<")[0].strip().strip('"')
                        from_address = from_header.split("<")[1].split(">")[0].strip()

                    # Get email body
                    text_body, html_body = self._get_email_body(msg)

                    # Check for attachments
                    has_attachments = False
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_disposition() == "attachment":
                                has_attachments = True
                                break

                    email_data = {
                        "message_id": message_id,
                        "from_address": from_address,
                        "from_name": from_name,
                        "subject": subject,
                        "text_body": text_body,
                        "html_body": html_body,
                        "received_at": datetime.now(timezone.utc),
                        "has_attachments": has_attachments,
                        "raw_date": date_str,
                    }

                    emails.append(email_data)

                    logger.info(f"📧 Fetched email from {from_address}: {subject[:50]}...")

                    # Mark as read if requested
                    if mark_as_read:
                        self.imap_connection.store(email_id, "+FLAGS", "\\Seen")

                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {e}")
                    continue

            return emails

        except Exception as e:
            logger.exception(f"❌ Error fetching unread emails: {e}")
            return []

    def mark_email_as_read(self, message_id: str) -> bool:
        """Mark a specific email as read by message ID"""
        if not self.imap_connection:
            if not self.connect():
                return False

        try:
            self.imap_connection.select("INBOX")
            _, msg_nums = self.imap_connection.search(None, f'HEADER Message-ID "{message_id}"')
            email_ids = msg_nums[0].split()

            if email_ids:
                self.imap_connection.store(email_ids[0], "+FLAGS", "\\Seen")
                logger.info(f"✅ Marked email {message_id} as read")
                return True

            return False
        except Exception as e:
            logger.exception(f"❌ Error marking email as read: {e}")
            return False

    def get_email_count(self) -> dict[str, int]:
        """Get email counts (total, unread, etc.)"""
        if not self.imap_connection:
            if not self.connect():
                return {"total": 0, "unread": 0}

        try:
            self.imap_connection.select("INBOX")

            # Total emails
            _, total_data = self.imap_connection.search(None, "ALL")
            total = len(total_data[0].split())

            # Unread emails
            _, unread_data = self.imap_connection.search(None, "UNSEEN")
            unread = len(unread_data[0].split())

            return {"total": total, "unread": unread}

        except Exception as e:
            logger.exception(f"❌ Error getting email count: {e}")
            return {"total": 0, "unread": 0}


def get_customer_email_monitor() -> CustomerEmailMonitor:
    """
    Factory function to create CustomerEmailMonitor instance.
    Uses settings from GSM instead of os.getenv().
    """
    from core.config import get_settings

    settings = get_settings()

    return CustomerEmailMonitor(
        email_address=getattr(settings, "SMTP_USER", "cs@myhibachichef.com"),
        password=getattr(settings, "SMTP_PASSWORD", ""),
        imap_server=getattr(settings, "IMAP_SERVER", "imap.ionos.com"),
        imap_port=int(getattr(settings, "IMAP_PORT", 993)),
    )


# Lazy-loaded global instance
_customer_email_monitor: Optional[CustomerEmailMonitor] = None


def customer_email_monitor() -> CustomerEmailMonitor:
    """Get the global CustomerEmailMonitor instance (lazy initialization)."""
    global _customer_email_monitor
    if _customer_email_monitor is None:
        _customer_email_monitor = get_customer_email_monitor()
    return _customer_email_monitor
