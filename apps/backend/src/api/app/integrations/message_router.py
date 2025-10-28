"""
Enhanced Unified Message Router
Integrates RingCentral SMS with existing multi-channel communication system.

This router handles all incoming messages from:
- RingCentral (SMS/Voice)
- Meta (Instagram/Facebook)
- Google Business (Reviews/Messages)
- Stripe (Payment notifications)
- Plaid (Financial data)

Provides unified message processing, lead management, and real-time updates.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import json
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from api.app.database import get_db
from core.config import get_settings

settings = get_settings()
from api.app.models.lead_newsletter import Lead, LeadSource, LeadStatus, SocialThread, ThreadStatus, SocialPlatform
from api.app.models.core import Event, Customer
from api.app.services.ai_lead_management import get_ai_lead_manager
from api.app.services.ringcentral_sms import RingCentralSMSService, send_sms_notification
from api.app.websockets.unified_inbox import manager

logger = logging.getLogger(__name__)


class MessageChannel(str, Enum):
    """Supported message channels."""
    SMS = "sms"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    GOOGLE_BUSINESS = "google_business"
    STRIPE = "stripe"
    PLAID = "plaid"
    EMAIL = "email"
    PHONE = "phone"


class MessageDirection(str, Enum):
    """Message direction."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class UnifiedMessage:
    """Unified message structure for all channels."""
    
    # Core identifiers
    message_id: str
    external_id: Optional[str] = None
    thread_id: Optional[str] = None
    
    # Channel information
    channel: MessageChannel = MessageChannel.SMS
    platform: str = "unknown"
    direction: MessageDirection = MessageDirection.INBOUND
    
    # Content
    text: Optional[str] = None
    subject: Optional[str] = None
    attachments: List[Dict[str, Any]] = None
    
    # Participants
    from_contact: Optional[str] = None  # Phone, email, handle, etc.
    to_contact: Optional[str] = None
    customer_handle: Optional[str] = None
    
    # Metadata
    timestamp: Optional[datetime] = None
    received_at: Optional[datetime] = None
    priority: MessagePriority = MessagePriority.NORMAL
    
    # Integration data
    raw_data: Optional[Dict[str, Any]] = None
    platform_metadata: Optional[Dict[str, Any]] = None
    
    # Processing status
    processed: bool = False
    ai_analyzed: bool = False
    lead_created: bool = False
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.received_at is None:
            self.received_at = datetime.now()


@dataclass
class ThreadInfo:
    """Thread information for conversation management."""
    thread_id: str
    lead_id: Optional[str]
    customer_id: Optional[str]
    platform: str
    channel: MessageChannel
    status: ThreadStatus
    customer_handle: str
    unread_count: int = 0
    last_message_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    platform_metadata: Optional[Dict[str, Any]] = None


class UnifiedMessageRouter:
    """Central message router for all communication channels."""
    
    def __init__(self):
        self.channel_handlers = {
            MessageChannel.SMS: self._handle_sms_message,
            MessageChannel.INSTAGRAM: self._handle_instagram_message,
            MessageChannel.FACEBOOK: self._handle_facebook_message,
            MessageChannel.GOOGLE_BUSINESS: self._handle_google_business_message,
            MessageChannel.STRIPE: self._handle_stripe_message,
            MessageChannel.PLAID: self._handle_plaid_message,
            MessageChannel.EMAIL: self._handle_email_message,
            MessageChannel.PHONE: self._handle_phone_message,
        }
        
        self._ai_manager = None
    
    async def process_message(
        self, 
        message: UnifiedMessage, 
        db: Session,
        background_processing: bool = True
    ) -> Dict[str, Any]:
        """
        Process incoming message through unified pipeline.
        
        Args:
            message: Unified message object
            db: Database session
            background_processing: Whether to perform background AI analysis
            
        Returns:
            Dict: Processing results with thread and lead information
        """
        try:
            logger.info(f"Processing {message.channel} message: {message.message_id}")
            
            # 1. Channel-specific processing
            channel_result = await self._process_by_channel(message, db)
            
            # 2. Find or create lead and thread
            lead_info = await self._process_lead(message, db)
            thread_info = await self._process_thread(message, lead_info, db)
            
            # 3. Store message event
            message_event = await self._store_message_event(message, thread_info, db)
            
            # 4. Update thread metadata
            await self._update_thread_activity(thread_info, message, db)
            
            # 5. Handle special commands/triggers
            command_result = await self._handle_special_commands(message, lead_info, db)
            
            # 6. Prepare processing results
            processing_result = {
                "status": "processed",
                "message_id": message.message_id,
                "channel": message.channel,
                "thread_id": thread_info.thread_id,
                "lead_id": lead_info.get("lead_id") if lead_info else None,
                "new_lead": lead_info.get("created", False) if lead_info else False,
                "new_thread": thread_info.created_at and thread_info.created_at > datetime.now().replace(second=0, microsecond=0),
                "command_handled": command_result is not None,
                "ai_analysis_queued": background_processing and not command_result,
                "timestamp": datetime.now().isoformat()
            }
            
            # 7. Real-time notifications
            await self._broadcast_message_update(processing_result, message, thread_info)
            
            # 8. Background AI processing (if enabled and not a command)
            if background_processing and not command_result:
                asyncio.create_task(self._background_ai_processing(
                    message, lead_info, thread_info, db
                ))
            
            # 9. Auto-response handling
            if command_result:
                await self._send_auto_response(message, command_result, db)
            
            db.commit()
            logger.info(f"Message processed successfully: {message.message_id}")
            
            return processing_result
            
        except Exception as e:
            logger.error(f"Error processing message {message.message_id}: {e}")
            db.rollback()
            raise
    
    async def _process_by_channel(self, message: UnifiedMessage, db: Session) -> Optional[Dict[str, Any]]:
        """Process message using channel-specific handler."""
        handler = self.channel_handlers.get(message.channel)
        if handler:
            return await handler(message, db)
        
        logger.warning(f"No handler found for channel: {message.channel}")
        return None
    
    async def _handle_sms_message(self, message: UnifiedMessage, db: Session) -> Dict[str, Any]:
        """Handle SMS-specific processing."""
        try:
            # Extract phone numbers and normalize
            from_number = self._normalize_phone_number(message.from_contact)
            to_number = self._normalize_phone_number(message.to_contact)
            
            # Validate SMS data
            if not from_number or not message.text:
                raise ValueError("Invalid SMS data: missing phone number or text")
            
            # Update message with normalized data
            message.customer_handle = from_number
            message.platform = "ringcentral"
            
            # SMS-specific metadata
            if not message.platform_metadata:
                message.platform_metadata = {}
            
            message.platform_metadata.update({
                "from_number": from_number,
                "to_number": to_number,
                "sms_type": "text",
                "character_count": len(message.text) if message.text else 0
            })
            
            logger.info(f"SMS message processed: {from_number} -> {to_number}")
            
            return {
                "channel_processed": True,
                "from_number": from_number,
                "to_number": to_number,
                "normalized": True
            }
            
        except Exception as e:
            logger.error(f"Error handling SMS message: {e}")
            return {"channel_processed": False, "error": str(e)}
    
    async def _handle_instagram_message(self, message: UnifiedMessage, db: Session) -> Dict[str, Any]:
        """Handle Instagram-specific processing."""
        try:
            # Instagram handles and mentions
            if message.from_contact:
                message.customer_handle = message.from_contact.replace('@', '')
            
            message.platform = "meta_instagram"
            
            # Instagram-specific metadata
            if not message.platform_metadata:
                message.platform_metadata = {}
            
            message.platform_metadata.update({
                "instagram_handle": message.customer_handle,
                "message_type": "direct_message",
                "has_media": len(message.attachments) > 0 if message.attachments else False
            })
            
            return {"channel_processed": True, "platform": "instagram"}
            
        except Exception as e:
            logger.error(f"Error handling Instagram message: {e}")
            return {"channel_processed": False, "error": str(e)}
    
    async def _handle_facebook_message(self, message: UnifiedMessage, db: Session) -> Dict[str, Any]:
        """Handle Facebook-specific processing."""
        try:
            message.platform = "meta_facebook"
            
            if not message.platform_metadata:
                message.platform_metadata = {}
            
            message.platform_metadata.update({
                "facebook_user_id": message.from_contact,
                "message_type": "messenger",
                "has_attachments": len(message.attachments) > 0 if message.attachments else False
            })
            
            return {"channel_processed": True, "platform": "facebook"}
            
        except Exception as e:
            logger.error(f"Error handling Facebook message: {e}")
            return {"channel_processed": False, "error": str(e)}
    
    async def _handle_google_business_message(self, message: UnifiedMessage, db: Session) -> Dict[str, Any]:
        """Handle Google Business-specific processing."""
        try:
            message.platform = "google_business"
            
            if not message.platform_metadata:
                message.platform_metadata = {}
            
            message.platform_metadata.update({
                "google_account_id": message.from_contact,
                "message_type": "business_message",
                "business_location": message.platform_metadata.get("location") if message.platform_metadata else None
            })
            
            return {"channel_processed": True, "platform": "google_business"}
            
        except Exception as e:
            logger.error(f"Error handling Google Business message: {e}")
            return {"channel_processed": False, "error": str(e)}
    
    async def _handle_stripe_message(self, message: UnifiedMessage, db: Session) -> Dict[str, Any]:
        """Handle Stripe payment notifications."""
        try:
            message.platform = "stripe"
            message.priority = MessagePriority.HIGH  # Payment events are high priority
            
            if not message.platform_metadata:
                message.platform_metadata = {}
            
            message.platform_metadata.update({
                "payment_event": True,
                "stripe_customer_id": message.from_contact,
                "event_type": message.platform_metadata.get("event_type") if message.platform_metadata else "unknown"
            })
            
            return {"channel_processed": True, "platform": "stripe", "priority": "high"}
            
        except Exception as e:
            logger.error(f"Error handling Stripe message: {e}")
            return {"channel_processed": False, "error": str(e)}
    
    async def _handle_plaid_message(self, message: UnifiedMessage, db: Session) -> Dict[str, Any]:
        """Handle Plaid financial data notifications."""
        try:
            message.platform = "plaid"
            message.priority = MessagePriority.HIGH  # Financial events are high priority
            
            if not message.platform_metadata:
                message.platform_metadata = {}
            
            message.platform_metadata.update({
                "financial_event": True,
                "plaid_user_id": message.from_contact,
                "event_type": message.platform_metadata.get("event_type") if message.platform_metadata else "unknown"
            })
            
            return {"channel_processed": True, "platform": "plaid", "priority": "high"}
            
        except Exception as e:
            logger.error(f"Error handling Plaid message: {e}")
            return {"channel_processed": False, "error": str(e)}
    
    async def _handle_email_message(self, message: UnifiedMessage, db: Session) -> Dict[str, Any]:
        """Handle email-specific processing."""
        try:
            message.platform = "email"
            
            if not message.platform_metadata:
                message.platform_metadata = {}
            
            message.platform_metadata.update({
                "email_address": message.from_contact,
                "subject": message.subject,
                "has_attachments": len(message.attachments) > 0 if message.attachments else False
            })
            
            return {"channel_processed": True, "platform": "email"}
            
        except Exception as e:
            logger.error(f"Error handling email message: {e}")
            return {"channel_processed": False, "error": str(e)}
    
    async def _handle_phone_message(self, message: UnifiedMessage, db: Session) -> Dict[str, Any]:
        """Handle phone call-specific processing."""
        try:
            from_number = self._normalize_phone_number(message.from_contact)
            message.customer_handle = from_number
            message.platform = "ringcentral_voice"
            
            if not message.platform_metadata:
                message.platform_metadata = {}
            
            message.platform_metadata.update({
                "call_type": "voice",
                "from_number": from_number,
                "call_duration": message.platform_metadata.get("duration") if message.platform_metadata else None,
                "call_result": message.platform_metadata.get("result") if message.platform_metadata else None
            })
            
            return {"channel_processed": True, "platform": "ringcentral_voice"}
            
        except Exception as e:
            logger.error(f"Error handling phone message: {e}")
            return {"channel_processed": False, "error": str(e)}
    
    def _normalize_phone_number(self, phone: Optional[str]) -> Optional[str]:
        """Normalize phone number format."""
        if not phone:
            return None
        
        # Remove all non-digit characters except +
        normalized = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Add + if not present and has 10+ digits
        if not normalized.startswith('+') and len(normalized) >= 10:
            normalized = '+1' + normalized[-10:]  # Assume US number
        
        return normalized
        
    # Additional method stubs to prevent errors
    async def _process_lead(self, message: UnifiedMessage, db: Session) -> Optional[Dict[str, Any]]:
        """Find or create lead for message."""
        # Implementation would go here
        return {"lead_id": "1", "created": False}
    
    async def _process_thread(self, message: UnifiedMessage, lead_info: Optional[Dict[str, Any]], db: Session):
        """Find or create conversation thread."""
        # Implementation would go here
        return ThreadInfo(
            thread_id="1",
            lead_id=lead_info.get("lead_id") if lead_info else None,
            customer_id=None,
            platform=message.platform,
            channel=message.channel,
            status=ThreadStatus.OPEN,
            customer_handle=message.customer_handle or "unknown",
            created_at=datetime.now()
        )
    
    async def _store_message_event(self, message: UnifiedMessage, thread_info, db: Session):
        """Store message as event in database."""
        # Implementation would go here
        pass
    
    async def _update_thread_activity(self, thread_info, message: UnifiedMessage, db: Session):
        """Update thread activity and metadata."""
        # Implementation would go here
        pass
    
    async def _handle_special_commands(self, message: UnifiedMessage, lead_info: Optional[Dict[str, Any]], db: Session) -> Optional[str]:
        """Handle special commands like STOP, START, HELP."""
        # Implementation would go here
        return None
    
    async def _broadcast_message_update(self, processing_result: Dict[str, Any], message: UnifiedMessage, thread_info):
        """Broadcast real-time message updates via WebSocket."""
        # Implementation would go here
        pass
    
    async def _background_ai_processing(self, message: UnifiedMessage, lead_info: Optional[Dict[str, Any]], thread_info, db: Session):
        """Background AI analysis and processing."""
        # Implementation would go here
        pass
    
    async def _send_auto_response(self, message: UnifiedMessage, response_text: str, db: Session):
        """Send automated response based on command."""
        # Implementation would go here
        pass


# Global router instance
_message_router: Optional[UnifiedMessageRouter] = None


async def get_message_router() -> UnifiedMessageRouter:
    """Get or create unified message router instance."""
    global _message_router
    
    if _message_router is None:
        _message_router = UnifiedMessageRouter()
    
    return _message_router


# Convenience functions for webhook integration
async def process_ringcentral_sms(
    from_number: str,
    to_number: str,
    message_text: str,
    message_id: str,
    raw_data: Dict[str, Any],
    db: Session
) -> Dict[str, Any]:
    """Process RingCentral SMS message."""
    try:
        router = await get_message_router()
        
        unified_message = UnifiedMessage(
            message_id=message_id,
            external_id=message_id,
            channel=MessageChannel.SMS,
            platform="ringcentral",
            direction=MessageDirection.INBOUND,
            text=message_text,
            from_contact=from_number,
            to_contact=to_number,
            customer_handle=from_number,
            timestamp=datetime.now(),
            raw_data=raw_data
        )
        
        return await router.process_message(unified_message, db)
        
    except Exception as e:
        logger.error(f"Error processing RingCentral SMS: {e}")
        raise