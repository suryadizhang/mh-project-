"""
WebhookService - Base handler pattern for webhook processing.

This module provides a clean, testable architecture for processing webhooks
from various platforms (Meta/Facebook, Twilio, Stripe, etc.).

Key benefits:
- Business logic separated from route handlers
- Easy to test with mocked dependencies
- Reusable base class for all webhook types
- Consistent error handling and logging
"""

import hashlib
import hmac
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from core.base_service import BaseService, EventTrackingMixin
from models.enums.lead_enums import LeadSource
from models.enums.social_enums import ThreadStatus
from models.social import SocialThread
from services.lead_service import LeadService
from services.event_service import EventService
# TODO: Legacy lead/newsletter models not migrated yet - needs refactor


class BaseWebhookHandler(ABC, BaseService, EventTrackingMixin):
    """
    Abstract base class for all webhook handlers.

    Provides:
    - Signature verification (platform-specific)
    - Event processing (platform-specific)
    - Automatic event tracking
    - Consistent error handling
    - Structured logging

    Subclasses must implement:
    - verify_signature(): Platform-specific signature verification
    - process_event(): Platform-specific event processing
    """

    def __init__(
        self,
        db: AsyncSession,
        event_service: EventService,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize base webhook handler.

        Args:
            db: Database session
            event_service: Event tracking service
            logger: Optional logger (auto-created if not provided)
        """
        super().__init__(db, logger)
        self.event_service = event_service

    @abstractmethod
    async def verify_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Verify webhook signature for security.

        Each platform has different signature algorithms:
        - Meta: HMAC-SHA256 with 'sha256=' prefix
        - Twilio: HMAC-SHA1 with base64 encoding
        - Stripe: HMAC-SHA256 with timestamp

        Args:
            payload: Raw request body as bytes
            signature: Signature from webhook headers
            secret: Platform-specific secret key

        Returns:
            True if signature is valid, False otherwise
        """
        pass

    @abstractmethod
    async def process_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process a webhook event.

        Args:
            event_type: Type of event (e.g., 'messages', 'leadgen', 'payment')
            data: Event data from webhook payload

        Returns:
            Processing result (varies by platform)
        """
        pass

    async def handle_webhook(
        self,
        payload: bytes,
        signature: str,
        secret: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main webhook processing workflow.

        1. Verify signature
        2. Extract event type
        3. Process event
        4. Track event
        5. Handle errors

        Args:
            payload: Raw request body
            signature: Signature header
            secret: Platform secret
            data: Parsed webhook data

        Returns:
            Processing result

        Raises:
            HTTPException: If signature is invalid or processing fails
        """
        # Step 1: Verify signature
        if not await self.verify_signature(payload, signature, secret):
            self.logger.error("Invalid webhook signature")
            await self.track_event(
                action="webhook_rejected",
                metadata={"reason": "invalid_signature"},
            )
            raise HTTPException(status_code=403, detail="Invalid signature")

        # Step 2: Extract event type
        event_type = data.get("object", "unknown")

        # Step 3: Process event
        try:
            result = await self.process_event(event_type, data)

            # Step 4: Track successful processing
            await self.track_event(
                action="webhook_processed",
                metadata={
                    "event_type": event_type,
                    "result": result,
                },
            )

            return result

        except Exception as e:
            # Step 5: Handle errors
            self.logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            await self.track_event(
                action="webhook_error",
                metadata={
                    "event_type": event_type,
                    "error": str(e),
                },
            )
            raise


class MetaWebhookHandler(BaseWebhookHandler):
    """
    Handle Meta (Facebook/Instagram) webhooks.

    Supports:
    - Instagram direct messages
    - Facebook Messenger messages
    - Lead generation ads
    - Page messaging
    """

    def __init__(
        self,
        db: AsyncSession,
        lead_service: LeadService,
        event_service: EventService,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Meta webhook handler.

        Args:
            db: Database session
            lead_service: Service for lead management
            event_service: Event tracking service
            logger: Optional logger
        """
        super().__init__(db, event_service, logger)
        self.lead_service = lead_service

    async def verify_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Verify Meta webhook signature using HMAC-SHA256.

        Meta sends: X-Hub-Signature-256: sha256=<hash>

        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
            secret: Meta app secret

        Returns:
            True if signature is valid
        """
        if not signature or not secret:
            return False

        # Calculate expected signature
        expected = "sha256=" + hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected)

    async def process_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process Meta webhook event.

        Args:
            event_type: Event type ('page', 'instagram', 'leadgen')
            data: Event data from Meta

        Returns:
            Processing result with status and counts
        """
        entries = data.get("entry", [])
        processed_count = 0

        for entry in entries:
            # Process based on event type
            if event_type == "instagram":
                processed_count += await self._process_instagram_entry(entry)
            elif event_type == "page":
                processed_count += await self._process_facebook_entry(entry)
            elif event_type == "leadgen":
                processed_count += await self._process_leadgen_entry(entry)
            else:
                self.logger.warning(f"Unknown Meta event type: {event_type}")

        return {
            "status": "success",
            "processed": processed_count,
            "event_type": event_type,
        }

    async def _process_instagram_entry(self, entry: Dict[str, Any]) -> int:
        """
        Process Instagram messaging entry.

        Args:
            entry: Instagram entry from webhook

        Returns:
            Number of messages processed
        """
        messaging_events = entry.get("messaging", [])
        count = 0

        for event in messaging_events:
            try:
                await self._process_instagram_message(event)
                count += 1
            except Exception as e:
                self.logger.error(f"Error processing Instagram message: {str(e)}")

        return count

    async def _process_facebook_entry(self, entry: Dict[str, Any]) -> int:
        """
        Process Facebook page messaging entry.

        Args:
            entry: Facebook entry from webhook

        Returns:
            Number of messages processed
        """
        messaging_events = entry.get("messaging", [])
        count = 0

        for event in messaging_events:
            try:
                await self._process_facebook_message(event)
                count += 1
            except Exception as e:
                self.logger.error(f"Error processing Facebook message: {str(e)}")

        return count

    async def _process_leadgen_entry(self, entry: Dict[str, Any]) -> int:
        """
        Process lead generation ad entry.

        Args:
            entry: Leadgen entry from webhook

        Returns:
            Number of leads processed
        """
        changes = entry.get("changes", [])
        count = 0

        for change in changes:
            try:
                if change.get("field") == "leadgen":
                    await self._process_leadgen_form(change.get("value", {}))
                    count += 1
            except Exception as e:
                self.logger.error(f"Error processing leadgen: {str(e)}")

        return count

    async def _process_instagram_message(self, event: Dict[str, Any]) -> None:
        """
        Process a single Instagram direct message.

        Creates or updates lead, tracks in social thread, and logs event.

        Args:
            event: Instagram messaging event
        """
        sender_id = event.get("sender", {}).get("id")
        message = event.get("message", {})

        if not sender_id or not message:
            return

        message_text = message.get("text", "")
        message_id = message.get("mid", "")

        # Extract or fetch sender username
        sender_username = event.get("sender", {}).get("username") or f"ig_user_{sender_id[-4:]}"

        # Create lead from Instagram message
        lead_data = {
            "name": sender_username,
            "instagram_handle": sender_username,
            "notes": f"Instagram DM: {message_text[:200]}",
            "source": LeadSource.INSTAGRAM,
        }

        # Use lead service to create/update lead
        contact_info = {
            "instagram_handle": sender_username,
        }

        context = {
            "notes": f"Instagram DM received: {message_text}",
            "message_id": message_id,
        }

        lead = await self.lead_service.create_lead(
            source=LeadSource.INSTAGRAM,
            contact_info=contact_info,
            context=context,
        )

        # Track the message in social thread
        thread = SocialThread(
            lead_id=lead.id,
            platform="instagram",
            thread_id=sender_id,
            status=ThreadStatus.ACTIVE,
            last_message_at=datetime.utcnow(),
            last_message_from="customer",
            message_count=1,
        )

        self.db.add(thread)
        await self.db.flush()

        self.logger.info(
            f"Processed Instagram message from {sender_username}",
            extra={"lead_id": lead.id, "message_id": message_id}
        )

    async def _process_facebook_message(self, event: Dict[str, Any]) -> None:
        """
        Process a single Facebook Messenger message.

        Similar to Instagram processing but for Facebook platform.

        Args:
            event: Facebook messaging event
        """
        sender_id = event.get("sender", {}).get("id")
        message = event.get("message", {})

        if not sender_id or not message:
            return

        message_text = message.get("text", "")

        # Similar processing to Instagram
        contact_info = {
            "facebook_id": sender_id,
        }

        context = {
            "notes": f"Facebook message: {message_text}",
        }

        lead = await self.lead_service.create_lead(
            source=LeadSource.FACEBOOK,
            contact_info=contact_info,
            context=context,
        )

        self.logger.info(
            f"Processed Facebook message from {sender_id}",
            extra={"lead_id": lead.id}
        )

    async def _process_leadgen_form(self, value: Dict[str, Any]) -> None:
        """
        Process a lead generation form submission.

        Args:
            value: Leadgen form data from Meta
        """
        leadgen_id = value.get("leadgen_id")
        form_id = value.get("form_id")

        # In a real implementation, we'd fetch form data from Graph API
        # For now, we'll create a basic lead record

        contact_info = {
            "notes": f"Lead gen form submission (form_id: {form_id})",
        }

        context = {
            "leadgen_id": leadgen_id,
            "form_id": form_id,
        }

        lead = await self.lead_service.create_lead(
            source=LeadSource.FACEBOOK_AD,
            contact_info=contact_info,
            context=context,
        )

        self.logger.info(
            f"Processed leadgen form submission",
            extra={"lead_id": lead.id, "form_id": form_id}
        )
