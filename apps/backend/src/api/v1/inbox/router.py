"""
Unified Inbox Message Router
Central routing system for all message types and channels
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from .models import (
    Message, Thread, TCPAOptStatus, WebSocketConnection,
    MessageChannel, MessageDirection, MessageStatus, TCPAStatus
)
from .schemas import SendMessageRequest, MessageResponse
from api.app.database import get_db

logger = logging.getLogger(__name__)


class MessageRouter:
    """Central message routing and processing system"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.tcpa_handler = TCPAHandler(db_session)
        self.channel_handlers = {
            MessageChannel.SMS: SMSHandler(),
            MessageChannel.EMAIL: EmailHandler(),
            MessageChannel.WEBSOCKET: WebSocketHandler(),
            MessageChannel.FACEBOOK: SocialMediaHandler("facebook"),
            MessageChannel.INSTAGRAM: SocialMediaHandler("instagram"),
            MessageChannel.TWITTER: SocialMediaHandler("twitter"),
        }

    async def route_message(self, request: SendMessageRequest) -> MessageResponse:
        """Route and process a message through appropriate channel"""
        try:
            logger.info(f"Routing {request.channel} message to {request.phone_number or request.email_address}")
            
            # TCPA compliance check for SMS
            if request.channel == MessageChannel.SMS and request.phone_number:
                tcpa_allowed = await self.tcpa_handler.check_tcpa_compliance(
                    request.phone_number, 
                    request.channel
                )
                if not tcpa_allowed:
                    raise ValueError(f"TCPA compliance failed for {request.phone_number}")
            
            # Create message record
            message = await self._create_message_record(request)
            
            # Get or create thread
            thread = await self._get_or_create_thread(message, request)
            message.thread_id = thread.id
            
            # Route to appropriate channel handler
            handler = self.channel_handlers.get(request.channel)
            if not handler:
                raise ValueError(f"No handler for channel: {request.channel}")
            
            # Send through channel
            result = await handler.send_message(message, request)
            
            # Update message with result
            message.external_id = result.get("external_id")
            message.status = MessageStatus.DELIVERED if result.get("success") else MessageStatus.FAILED
            message.sent_at = datetime.now(timezone.utc)
            message.message_metadata = {**(message.message_metadata or {}), **result.get("metadata", {})}
            
            await self.db.commit()
            await self.db.refresh(message)
            
            # Notify WebSocket clients
            await self._notify_websocket_clients(message, "message_sent")
            
            return MessageResponse.from_orm(message)
            
        except Exception as e:
            logger.error(f"Message routing failed: {str(e)}")
            await self.db.rollback()
            raise

    async def process_inbound_message(
        self, 
        channel: MessageChannel,
        content: str,
        sender_info: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> MessageResponse:
        """Process incoming message from external channels"""
        try:
            logger.info(f"Processing inbound {channel} message from {sender_info}")
            
            # Handle TCPA commands for SMS
            if channel == MessageChannel.SMS and sender_info.get("phone_number"):
                tcpa_command = await self.tcpa_handler.handle_tcpa_command(
                    content.strip().upper(),
                    sender_info["phone_number"],
                    channel
                )
                if tcpa_command:
                    # TCPA command processed, send auto-response
                    return await self._send_tcpa_auto_response(
                        sender_info["phone_number"], 
                        tcpa_command,
                        channel
                    )
            
            # Find or create contact
            contact_id = await self._find_or_create_contact(sender_info, channel)
            
            # Create message record
            message = Message(
                id=uuid4(),
                channel=channel,
                direction=MessageDirection.INBOUND,
                contact_id=contact_id,
                phone_number=sender_info.get("phone_number"),
                email_address=sender_info.get("email_address"),
                social_handle=sender_info.get("social_handle"),
                content=content,
                status=MessageStatus.DELIVERED,
                external_id=metadata.get("external_id") if metadata else None,
                message_metadata=metadata,
                created_at=datetime.now(timezone.utc),
                delivered_at=datetime.now(timezone.utc)
            )
            
            # Get or create thread
            thread = await self._get_or_create_thread(message, None)
            message.thread_id = thread.id
            
            self.db.add(message)
            await self.db.commit()
            await self.db.refresh(message)
            
            # Update thread timestamp
            thread.last_message_at = message.created_at
            await self.db.commit()
            
            # Notify WebSocket clients
            await self._notify_websocket_clients(message, "message_received")
            
            # Check for auto-responses
            await self._check_auto_responses(message)
            
            return MessageResponse.from_orm(message)
            
        except Exception as e:
            logger.error(f"Inbound message processing failed: {str(e)}")
            await self.db.rollback()
            raise

    async def _create_message_record(self, request: SendMessageRequest) -> Message:
        """Create message database record"""
        message = Message(
            id=uuid4(),
            channel=request.channel,
            direction=request.direction,
            contact_id=request.contact_id,
            phone_number=request.phone_number,
            email_address=request.email_address,
            social_handle=request.social_handle,
            content=request.content,
            content_type=request.content_type,
            subject=request.subject,
            status=MessageStatus.PENDING,
            parent_message_id=request.parent_message_id,
            message_metadata=request.metadata,
            created_at=datetime.now(timezone.utc)
        )
        
        self.db.add(message)
        await self.db.flush()  # Get ID without committing
        return message

    async def _get_or_create_thread(
        self, 
        message: Message, 
        request: Optional[SendMessageRequest]
    ) -> Thread:
        """Get existing thread or create new one"""
        
        # Use provided thread_id if available
        if request and request.thread_id:
            thread = await self.db.get(Thread, request.thread_id)
            if thread:
                return thread
        
        # Look for existing thread by contact and channel
        query = select(Thread).where(
            and_(
                Thread.contact_id == message.contact_id,
                Thread.channel == message.channel,
                Thread.is_active == True
            )
        ).order_by(desc(Thread.updated_at))
        
        result = await self.db.execute(query)
        existing_thread = result.scalar_one_or_none()
        
        if existing_thread:
            return existing_thread
        
        # Create new thread
        thread = Thread(
            id=uuid4(),
            channel=message.channel,
            contact_id=message.contact_id,
            subject=message.subject or f"{message.channel.value} conversation",
            tcpa_status=TCPAStatus.PENDING,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(thread)
        await self.db.flush()
        return thread

    async def _find_or_create_contact(
        self, 
        sender_info: Dict[str, Any], 
        channel: MessageChannel
    ) -> Optional[UUID]:
        """Find existing contact or create new one"""
        # This would integrate with the existing CRM contact system
        # For now, return None to allow anonymous messaging
        return None

    async def _notify_websocket_clients(self, message: Message, event_type: str):
        """Notify connected WebSocket clients of message events"""
        try:
            # Get active WebSocket connections
            query = select(WebSocketConnection).where(
                WebSocketConnection.is_active == True
            )
            result = await self.db.execute(query)
            connections = result.scalars().all()
            
            # Notify each connection (implementation depends on WebSocket manager)
            notification = {
                "type": event_type,
                "message_id": str(message.id),
                "channel": message.channel.value,
                "content": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                "timestamp": message.created_at.isoformat()
            }
            
            logger.info(f"Notifying {len(connections)} WebSocket clients of {event_type}")
            # WebSocket notification implementation would go here
            
        except Exception as e:
            logger.error(f"WebSocket notification failed: {str(e)}")

    async def _send_tcpa_auto_response(
        self, 
        phone_number: str, 
        command: str, 
        channel: MessageChannel
    ) -> MessageResponse:
        """Send automatic TCPA compliance response"""
        
        responses = {
            "STOP": "You have been unsubscribed from SMS messages. Reply START to re-subscribe.",
            "START": "You have been subscribed to SMS messages. Reply STOP to unsubscribe.",
            "HELP": "SMS Help - Reply STOP to unsubscribe, START to subscribe. For support: (916) 740-8768"
        }
        
        content = responses.get(command, responses["HELP"])
        
        # Create auto-response message
        auto_request = SendMessageRequest(
            channel=channel,
            direction=MessageDirection.OUTBOUND,
            phone_number=phone_number,
            content=content,
            metadata={"auto_response": True, "tcpa_command": command}
        )
        
        return await self.route_message(auto_request)

    async def _check_auto_responses(self, message: Message):
        """Check and trigger auto-responses if configured"""
        # Auto-response logic would be implemented here
        pass


class TCPAHandler:
    """TCPA compliance handler for SMS communications"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def check_tcpa_compliance(
        self, 
        phone_number: str, 
        channel: MessageChannel
    ) -> bool:
        """Check if messaging is allowed under TCPA"""
        
        # Normalize phone number
        normalized_phone = self._normalize_phone(phone_number)
        
        # Check TCPA status
        query = select(TCPAOptStatus).where(
            and_(
                TCPAOptStatus.phone_number == normalized_phone,
                TCPAOptStatus.channel == channel
            )
        )
        
        result = await self.db.execute(query)
        tcpa_status = result.scalar_one_or_none()
        
        if not tcpa_status:
            # No explicit opt-out, allow messaging (business relationship)
            return True
        
        return tcpa_status.status == TCPAStatus.OPTED_IN

    async def handle_tcpa_command(
        self, 
        content: str, 
        phone_number: str, 
        channel: MessageChannel
    ) -> Optional[str]:
        """Handle TCPA command (STOP, START, HELP)"""
        
        command = content.strip().upper()
        if command not in ["STOP", "START", "HELP"]:
            return None
        
        normalized_phone = self._normalize_phone(phone_number)
        
        if command in ["STOP", "START"]:
            # Update TCPA status
            new_status = TCPAStatus.OPTED_OUT if command == "STOP" else TCPAStatus.OPTED_IN
            
            await self._update_tcpa_status(
                normalized_phone,
                channel,
                new_status,
                "sms_reply"
            )
        
        return command

    async def _update_tcpa_status(
        self,
        phone_number: str,
        channel: MessageChannel,
        status: TCPAStatus,
        method: str
    ):
        """Update TCPA opt status"""
        
        # Check for existing record
        query = select(TCPAOptStatus).where(
            and_(
                TCPAOptStatus.phone_number == phone_number,
                TCPAOptStatus.channel == channel
            )
        )
        
        result = await self.db.execute(query)
        tcpa_record = result.scalar_one_or_none()
        
        now = datetime.now(timezone.utc)
        
        if tcpa_record:
            tcpa_record.status = status
            tcpa_record.updated_at = now
        else:
            tcpa_record = TCPAOptStatus(
                id=uuid4(),
                phone_number=phone_number,
                channel=channel,
                status=status,
                opt_in_method=method,
                created_at=now,
                updated_at=now
            )
            self.db.add(tcpa_record)
        
        await self.db.commit()

    def _normalize_phone(self, phone_number: str) -> str:
        """Normalize phone number format"""
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone_number))
        
        # Add country code if missing
        if len(digits) == 10:
            digits = "1" + digits
        elif len(digits) == 11 and digits.startswith("1"):
            pass  # Already has country code
        
        return f"+{digits}"


# Channel-specific handlers
class SMSHandler:
    """SMS message handler"""
    
    async def send_message(self, message: Message, request: SendMessageRequest) -> Dict[str, Any]:
        """Send SMS message via provider"""
        # Implementation would integrate with SMS provider (Twilio, etc.)
        return {
            "success": True,
            "external_id": f"sms_{uuid4()}",
            "metadata": {"provider": "twilio", "cost": 0.0075}
        }


class EmailHandler:
    """Email message handler"""
    
    async def send_message(self, message: Message, request: SendMessageRequest) -> Dict[str, Any]:
        """Send email message via provider"""
        # Implementation would integrate with email provider (SendGrid, etc.)
        return {
            "success": True,
            "external_id": f"email_{uuid4()}",
            "metadata": {"provider": "sendgrid"}
        }


class WebSocketHandler:
    """WebSocket message handler"""
    
    async def send_message(self, message: Message, request: SendMessageRequest) -> Dict[str, Any]:
        """Send WebSocket message to connected clients"""
        # Implementation would use WebSocket manager
        return {
            "success": True,
            "external_id": f"ws_{uuid4()}",
            "metadata": {"delivered_to_connections": 0}
        }


class SocialMediaHandler:
    """Social media message handler"""
    
    def __init__(self, platform: str):
        self.platform = platform
    
    async def send_message(self, message: Message, request: SendMessageRequest) -> Dict[str, Any]:
        """Send social media message via platform API"""
        # Implementation would integrate with platform APIs
        return {
            "success": True,
            "external_id": f"{self.platform}_{uuid4()}",
            "metadata": {"platform": self.platform}
        }