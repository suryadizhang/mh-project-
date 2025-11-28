"""
Outbox processor workers for external service integrations.
Handles SMS, email, and payment processing with retry logic.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import json
import logging
from typing import Any

import aiohttp
from core.database import get_db_context
from models import DomainEvent, OutboxEntry
from utils.encryption import decrypt_field, get_field_encryption
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

logger = logging.getLogger(__name__)


@dataclass
class WorkerConfig:
    """Worker configuration settings."""

    max_retries: int = 5
    initial_delay_seconds: int = 1
    max_delay_seconds: int = 300
    batch_size: int = 10
    poll_interval_seconds: int = 5
    worker_timeout_seconds: int = 3600


class OutboxWorkerBase:
    """Base class for outbox event processors."""

    def __init__(self, config: WorkerConfig = None):
        self.config = config or WorkerConfig()
        self.running = False

    async def start(self):
        """Start the worker."""
        self.running = True
        logger.info(f"Starting {self.__class__.__name__}")

        try:
            while self.running:
                try:
                    await self._process_batch()
                    await asyncio.sleep(self.config.poll_interval_seconds)
                except Exception as e:
                    logger.exception(f"Worker error in {self.__class__.__name__}: {e}")
                    await asyncio.sleep(self.config.poll_interval_seconds)
        except asyncio.CancelledError:
            logger.info(f"Worker {self.__class__.__name__} was cancelled")
            raise
        except Exception as e:
            logger.exception(f"Fatal error in {self.__class__.__name__}: {e}")
            raise
        finally:
            self.running = False

    async def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info(f"Stopping {self.__class__.__name__}")

    async def _process_batch(self):
        """Process a batch of outbox events."""
        # use get_db_context() which is an asynccontextmanager for non-FastAPI usage
        async with get_db_context() as db:
            # Get pending events for this worker
            events = await self._get_pending_events(db)

            for event in events:
                try:
                    await self._process_event(event, db)
                    await self._mark_event_processed(event.id, db)
                    await db.commit()

                except Exception as e:
                    logger.exception(f"Error processing event {event.id}: {e}")
                    await self._handle_event_error(event, str(e), db)
                    await db.commit()

    async def _get_pending_events(self, db: AsyncSession) -> list[OutboxEntry]:
        """Get pending events for this worker type."""
        # First, fetch candidate pending entries (no JSON extraction in SQL)
        query = (
            select(OutboxEntry)
            .where(
                and_(
                    OutboxEntry.status == "pending",
                    OutboxEntry.attempts < self.config.max_retries,
                    OutboxEntry.next_attempt_at <= datetime.now(timezone.utc),
                )
            )
            .order_by(OutboxEntry.created_at)
            .limit(self.config.batch_size * 4)  # fetch some extra to filter in-Python
        )

        result = await db.execute(query)
        candidates = result.scalars().all()

        # Filter by payload.event_type in Python to support multiple DB backends
        supported = set(self.get_supported_event_types())
        selected = [e for e in candidates if (e.payload or {}).get("event_type") in supported]

        # Respect batch_size
        return selected[: self.config.batch_size]

    async def _mark_event_processed(self, event_id: str, db: AsyncSession):
        """Mark event as processed."""
        await db.execute(
            update(OutboxEntry)
            .where(OutboxEntry.id == event_id)
            .values(completed_at=datetime.now(timezone.utc), status="completed")
        )

    async def _handle_event_error(self, event: OutboxEntry, error_message: str, db: AsyncSession):
        """Handle event processing error with exponential backoff."""
        retry_count = (getattr(event, "attempts", None) or 0) + 1

        # Calculate next retry time with exponential backoff
        delay_seconds = min(
            self.config.initial_delay_seconds * (2**retry_count), self.config.max_delay_seconds
        )
        next_retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)

        if retry_count >= self.config.max_retries:
            # Mark as failed after max retries
            await db.execute(
                update(OutboxEntry)
                .where(OutboxEntry.id == event.id)
                .values(
                    status="failed",
                    last_error=error_message,
                    completed_at=datetime.now(timezone.utc),
                    attempts=retry_count,
                )
            )
            logger.error(f"Event {event.id} failed after {retry_count} retries: {error_message}")
        else:
            # Schedule for retry
            await db.execute(
                update(OutboxEntry)
                .where(OutboxEntry.id == event.id)
                .values(
                    attempts=retry_count, last_error=error_message, next_attempt_at=next_retry_at
                )
            )
            logger.warning(
                f"Event {event.id} retry {retry_count} scheduled for {next_retry_at}: {error_message}"
            )

    def get_supported_event_types(self) -> list[str]:
        """Get list of event types this worker handles."""
        raise NotImplementedError

    async def _process_event(self, event: OutboxEntry, db: AsyncSession):
        """Process a single event."""
        raise NotImplementedError


class SMSWorker(OutboxWorkerBase):
    """Worker for sending SMS messages via RingCentral."""

    def __init__(self, config: WorkerConfig = None, rc_config: dict[str, str] | None = None):
        super().__init__(config)
        self.rc_config = rc_config or {}
        self._access_token: str | None = None
        self._token_expires_at: datetime | None = None

    def get_supported_event_types(self) -> list[str]:
        return ["sms_send", "sms_reminder", "sms_confirmation"]

    async def _process_event(self, event: OutboxEntry, db: AsyncSession):
        """Process SMS event."""
        event_data = json.loads(event.event_data)

        # Decrypt phone number if encrypted
        phone_number = event_data.get("phone_number")
        if event_data.get("phone_encrypted", False):
            field_encryption = get_field_encryption()
            phone_number = decrypt_field(phone_number, field_encryption.key)

        message = event_data.get("message", "")

        # Send SMS
        await self._send_sms(phone_number, message)

        logger.info(f"SMS sent successfully for event {event.id} to {phone_number[:6]}***")

    async def _send_sms(self, phone_number: str, message: str):
        """Send SMS via RingCentral API."""
        # Ensure we have a valid access token
        await self._ensure_access_token()

        url = f"{self.rc_config.get('server_url', '')}/restapi/v1.0/account/~/extension/~/sms"

        payload = {
            "from": {"phoneNumber": self.rc_config.get("from_number", "")},
            "to": [{"phoneNumber": phone_number}],
            "text": message,
        }

        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    # Token expired, refresh and retry
                    await self._refresh_access_token()
                    headers["Authorization"] = f"Bearer {self._access_token}"

                    async with session.post(url, json=payload, headers=headers) as retry_response:
                        if retry_response.status != 200:
                            error_text = await retry_response.text()
                            raise Exception(
                                f"SMS API error after retry: {retry_response.status} - {error_text}"
                            )
                        return await retry_response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"SMS API error: {response.status} - {error_text}")

    async def _ensure_access_token(self):
        """Ensure we have a valid access token."""
        if not self._access_token or (
            self._token_expires_at
            and datetime.now(timezone.utc) >= self._token_expires_at - timedelta(minutes=5)
        ):
            await self._refresh_access_token()

    async def _refresh_access_token(self):
        """Refresh RingCentral access token."""
        url = f"{self.rc_config.get('server_url', '')}/restapi/oauth/token"

        auth_string = (
            f"{self.rc_config.get('client_id', '')}:{self.rc_config.get('client_secret', '')}"
        )
        import base64

        auth_header = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        payload = {
            "grant_type": "password",
            "username": self.rc_config.get("username", ""),
            "password": self.rc_config.get("password", ""),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Token refresh error: {response.status} - {error_text}")

                token_data = await response.json()
                self._access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 3600)
                self._token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)


class EmailWorker(OutboxWorkerBase):
    """Worker for sending emails."""

    def __init__(self, config: WorkerConfig = None, email_config: dict[str, str] | None = None):
        super().__init__(config)
        self.email_config = email_config or {}

    def get_supported_event_types(self) -> list[str]:
        return ["email_send", "email_confirmation", "email_reminder", "email_receipt"]

    async def _process_event(self, event: OutboxEntry, db: AsyncSession):
        """Process email event."""
        event_data = json.loads(event.event_data)

        # Decrypt email if encrypted
        email_address = event_data.get("email")
        if event_data.get("email_encrypted", False):
            field_encryption = get_field_encryption()
            email_address = decrypt_field(email_address, field_encryption.key)

        subject = event_data.get("subject", "")
        html_body = event_data.get("html_body", "")
        text_body = event_data.get("text_body", "")
        attachments = event_data.get("attachments", [])

        # Send email
        await self._send_email(email_address, subject, html_body, text_body, attachments)

        logger.info(f"Email sent successfully for event {event.id} to {email_address}")

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        attachments: list[dict] | None = None,
    ):
        """Send email via configured email service."""

        # Use SendGrid, AWS SES, or SMTP based on configuration
        email_provider = self.email_config.get("provider", "sendgrid")

        if email_provider == "sendgrid":
            await self._send_via_sendgrid(to_email, subject, html_body, text_body, attachments)
        elif email_provider == "ses":
            await self._send_via_ses(to_email, subject, html_body, text_body, attachments)
        elif email_provider == "smtp":
            await self._send_via_smtp(to_email, subject, html_body, text_body, attachments)
        else:
            raise Exception(f"Unknown email provider: {email_provider}")

    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        attachments: list[dict] | None = None,
    ):
        """Send email via SendGrid API."""
        try:
            import sendgrid
            from sendgrid.helpers.mail import (
                Attachment,
                Disposition,
                FileContent,
                FileName,
                FileType,
                Mail,
            )
        except ImportError:
            raise Exception("SendGrid package not installed. Install with: pip install sendgrid")

        sg = sendgrid.SendGridAPIClient(api_key=self.email_config.get("sendgrid_api_key"))

        message = Mail(
            from_email=self.email_config.get("from_email", ""),
            to_emails=to_email,
            subject=subject,
            html_content=html_body,
            plain_text_content=text_body,
        )

        # Add attachments if any
        if attachments:
            for attachment_data in attachments:
                attachment = Attachment(
                    FileContent(attachment_data.get("content", "")),
                    FileName(attachment_data.get("filename", "")),
                    FileType(attachment_data.get("type", "application/octet-stream")),
                    Disposition("attachment"),
                )
                message.attachment = attachment

        response = sg.send(message)

        if response.status_code not in [200, 201, 202]:
            raise Exception(f"SendGrid error: {response.status_code} - {response.body}")

    async def _send_via_ses(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        attachments: list[dict] | None = None,
    ):
        """Send email via AWS SES."""
        from email.mime.application import MIMEApplication
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        try:
            import boto3
        except ImportError:
            raise Exception("boto3 package not installed. Install with: pip install boto3")

        ses = boto3.client(
            "ses",
            region_name=self.email_config.get("aws_region", "us-east-1"),
            aws_access_key_id=self.email_config.get("aws_access_key_id"),
            aws_secret_access_key=self.email_config.get("aws_secret_access_key"),
        )

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.email_config.get("from_email", "")
        msg["To"] = to_email

        # Add text and HTML parts
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        # Add attachments if any
        if attachments:
            for attachment_data in attachments:
                part = MIMEApplication(attachment_data.get("content", ""))
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=attachment_data.get("filename", ""),
                )
                msg.attach(part)

        # Send email
        response = ses.send_raw_email(
            Source=self.email_config.get("from_email", ""),
            Destinations=[to_email],
            RawMessage={"Data": msg.as_string()},
        )

        logger.info(f"SES MessageId: {response['MessageId']}")

    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str = "",
        attachments: list[dict] | None = None,
    ):
        """Send email via SMTP."""
        from email.mime.application import MIMEApplication
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        import smtplib

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.email_config.get("from_email", "")
        msg["To"] = to_email

        # Add text and HTML parts
        if text_body:
            msg.attach(MIMEText(text_body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        # Add attachments if any
        if attachments:
            for attachment_data in attachments:
                part = MIMEApplication(attachment_data.get("content", ""))
                part.add_header(
                    "Content-Disposition",
                    "attachment",
                    filename=attachment_data.get("filename", ""),
                )
                msg.attach(part)

        # Send via SMTP
        with smtplib.SMTP(
            self.email_config.get("smtp_host", ""), self.email_config.get("smtp_port", 587)
        ) as server:
            server.starttls()
            server.login(
                self.email_config.get("smtp_username", ""),
                self.email_config.get("smtp_password", ""),
            )
            server.send_message(msg)


class StripeWorker(OutboxWorkerBase):
    """Worker for Stripe payment processing."""

    def __init__(self, config: WorkerConfig = None, stripe_config: dict[str, str] | None = None):
        super().__init__(config)
        self.stripe_config = stripe_config or {}

        # Configure Stripe
        stripe.api_key = self.stripe_config.get("secret_key", "")

    def get_supported_event_types(self) -> list[str]:
        return ["stripe_payment_intent", "stripe_refund", "stripe_customer_create"]

    async def _process_event(self, event: OutboxEntry, db: AsyncSession):
        """Process Stripe event."""
        event_data = json.loads(event.event_data)
        event_type = event.event_type

        if event_type == "stripe_payment_intent":
            await self._process_payment_intent(event_data, db)
        elif event_type == "stripe_refund":
            await self._process_refund(event_data, db)
        elif event_type == "stripe_customer_create":
            await self._process_customer_create(event_data, db)
        else:
            raise Exception(f"Unknown Stripe event type: {event_type}")

        logger.info(f"Stripe event {event_type} processed successfully for event {event.id}")

    async def _process_payment_intent(self, event_data: dict[str, Any], db: AsyncSession):
        """Process Stripe payment intent creation."""
        booking_id = event_data.get("booking_id")
        amount_cents = event_data.get("amount_cents")
        customer_email = event_data.get("customer_email")

        # Decrypt customer email if encrypted
        if event_data.get("email_encrypted", False):
            field_encryption = get_field_encryption()
            customer_email = decrypt_field(customer_email, field_encryption.key)

        # Create or retrieve Stripe customer
        try:
            customers = stripe.Customer.list(email=customer_email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(
                    email=customer_email, metadata={"booking_id": str(booking_id)}
                )
        except Exception as e:
            logger.exception(f"Error creating/retrieving Stripe customer: {e}")
            raise

        # Create payment intent
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                customer=customer.id,
                metadata={"booking_id": str(booking_id), "customer_email": customer_email},
                automatic_payment_methods={"enabled": True},
            )

            # Store payment intent ID for later reference
            # This would typically update the booking record
            logger.info(f"Created PaymentIntent {payment_intent.id} for booking {booking_id}")

        except Exception as e:
            logger.exception(f"Error creating Stripe payment intent: {e}")
            raise

    async def _process_refund(self, event_data: dict[str, Any], db: AsyncSession):
        """Process Stripe refund."""
        payment_intent_id = event_data.get("payment_intent_id")
        refund_amount_cents = event_data.get("refund_amount_cents")
        reason = event_data.get("reason", "requested_by_customer")

        try:
            refund = stripe.Refund.create(
                payment_intent=payment_intent_id, amount=refund_amount_cents, reason=reason
            )

            logger.info(f"Created refund {refund.id} for PaymentIntent {payment_intent_id}")

        except Exception as e:
            logger.exception(f"Error creating Stripe refund: {e}")
            raise

    async def _process_customer_create(self, event_data: dict[str, Any], db: AsyncSession):
        """Process Stripe customer creation."""
        customer_email = event_data.get("customer_email")
        customer_name = event_data.get("customer_name", "")

        # Decrypt customer data if encrypted
        if event_data.get("email_encrypted", False):
            field_encryption = get_field_encryption()
            customer_email = decrypt_field(customer_email, field_encryption.key)

        if event_data.get("name_encrypted", False):
            field_encryption = get_field_encryption()
            customer_name = decrypt_field(customer_name, field_encryption.key)

        try:
            customer = stripe.Customer.create(
                email=customer_email, name=customer_name, metadata=event_data.get("metadata", {})
            )

            logger.info(f"Created Stripe customer {customer.id} for {customer_email}")

        except Exception as e:
            logger.exception(f"Error creating Stripe customer: {e}")
            raise


class OutboxProcessorManager:
    """Manages all outbox processor workers."""

    def __init__(self, worker_configs: dict[str, Any] | None = None):
        self.worker_configs = worker_configs or {}
        self.workers: list[OutboxWorkerBase] = []
        self.worker_tasks: list[asyncio.Task] = []
        self.running = False

    def add_worker(self, worker: OutboxWorkerBase):
        """Add a worker to the manager."""
        self.workers.append(worker)

    async def start_all(self):
        """Start all workers."""
        self.running = True
        logger.info("Starting OutboxProcessorManager")

        if not self.workers:
            logger.info("No workers configured - skipping worker startup")
            return

        try:
            # Start each worker as a background task
            for worker in self.workers:
                task = asyncio.create_task(self._run_worker_safely(worker))
                self.worker_tasks.append(task)

            logger.info(f"Started {len(self.workers)} outbox workers")
        except Exception as e:
            logger.exception(f"Error starting workers: {e}")
            # Clean up any started tasks
            await self.stop_all()
            raise

    async def _run_worker_safely(self, worker: OutboxWorkerBase):
        """Run a worker with proper error handling."""
        try:
            await worker.start()
        except asyncio.CancelledError:
            logger.info(f"Worker {worker.__class__.__name__} cancelled")
            raise
        except Exception as e:
            logger.exception(f"Worker {worker.__class__.__name__} failed: {e}")
            # Don't re-raise to prevent taking down other workers

    async def stop_all(self):
        """Stop all workers gracefully."""
        self.running = False
        logger.info("Stopping OutboxProcessorManager")

        # Stop all workers
        for worker in self.workers:
            await worker.stop()

        # Cancel all tasks
        for task in self.worker_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)

        self.worker_tasks.clear()
        logger.info("All outbox workers stopped")


# Factory function to create and configure workers
def create_outbox_processor_manager(app_config: dict[str, Any]) -> OutboxProcessorManager:
    """Create and configure the outbox processor manager."""

    manager = OutboxProcessorManager()

    # Configure SMS worker
    if app_config.get("ringcentral", {}).get("enabled", False):
        rc_config = app_config.get("ringcentral", {})
        # Validate RingCentral configuration
        required_rc_keys = [
            "server_url",
            "client_id",
            "client_secret",
            "username",
            "password",
            "from_number",
        ]
        if all(rc_config.get(key) for key in required_rc_keys):
            sms_worker = SMSWorker(
                config=WorkerConfig(
                    max_retries=app_config.get("sms_worker", {}).get("max_retries", 5),
                    batch_size=app_config.get("sms_worker", {}).get("batch_size", 10),
                ),
                rc_config=rc_config,
            )
            manager.add_worker(sms_worker)
            logger.info("✅ SMS Worker configured")
        else:
            logger.warning("⚠️ SMS Worker disabled - incomplete RingCentral configuration")

    # Configure email worker
    if app_config.get("email", {}).get("enabled", False):
        email_config = app_config.get("email", {})
        # Validate email configuration based on provider
        provider = email_config.get("provider", "smtp")
        config_valid = False

        if provider == "smtp":
            config_valid = all(
                email_config.get(key)
                for key in ["smtp_host", "smtp_username", "smtp_password", "from_email"]
            )
        elif provider == "sendgrid":
            config_valid = all(email_config.get(key) for key in ["sendgrid_api_key", "from_email"])
        elif provider == "ses":
            config_valid = all(
                email_config.get(key)
                for key in ["aws_access_key_id", "aws_secret_access_key", "from_email"]
            )

        if config_valid:
            email_worker = EmailWorker(
                config=WorkerConfig(
                    max_retries=app_config.get("email_worker", {}).get("max_retries", 3),
                    batch_size=app_config.get("email_worker", {}).get("batch_size", 20),
                ),
                email_config=email_config,
            )
            manager.add_worker(email_worker)
            logger.info(f"✅ Email Worker configured (provider: {provider})")
        else:
            logger.warning(f"⚠️ Email Worker disabled - incomplete {provider} configuration")

    # Configure Stripe worker
    if app_config.get("stripe", {}).get("enabled", False):
        stripe_config = app_config.get("stripe", {})
        # Validate Stripe configuration
        if stripe_config.get("secret_key") and stripe_config["secret_key"].startswith(
            ("sk_test_", "sk_live_")
        ):
            stripe_worker = StripeWorker(
                config=WorkerConfig(
                    max_retries=app_config.get("stripe_worker", {}).get("max_retries", 3),
                    batch_size=app_config.get("stripe_worker", {}).get("batch_size", 5),
                ),
                stripe_config=stripe_config,
            )
            manager.add_worker(stripe_worker)
            logger.info("✅ Stripe Worker configured")
        else:
            logger.warning("⚠️ Stripe Worker disabled - invalid or missing secret key")

    logger.info(f"Worker Manager created with {len(manager.workers)} workers")
    return manager


__all__ = [
    "EmailWorker",
    "OutboxProcessorManager",
    "OutboxWorkerBase",
    "SMSWorker",
    "StripeWorker",
    "WorkerConfig",
    "create_outbox_processor_manager",
]
