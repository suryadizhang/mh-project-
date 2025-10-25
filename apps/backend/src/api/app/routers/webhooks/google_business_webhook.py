"""
Google Business Messages webhook handler for unified inbox.
Handles customer messages from Google My Business and Google Search.
"""
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import json
import logging
from datetime import datetime
import hmac
import hashlib

from api.app.database import get_db
from api.app.config import settings
from api.app.models.lead_newsletter import Lead, LeadSource, LeadStatus, SocialThread, ThreadStatus
from api.app.models.core import Event
from api.app.services.ai_lead_management import get_ai_lead_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/google-business", tags=["webhooks", "business"])


def verify_google_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Google webhook signature."""
    if not signature or not secret:
        return False
    
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


async def process_google_business_message(
    message_data: Dict[str, Any],
    db: Session
) -> Optional[Dict[str, Any]]:
    """Process Google Business Message."""
    try:
        # Extract message information
        message_id = message_data.get("messageId")
        conversation_id = message_data.get("conversationId")
        agent_id = message_data.get("agentId")
        sender = message_data.get("sender", {})
        message = message_data.get("message", {})
        
        if not message_id or not conversation_id:
            return None
        
        # Extract sender information
        customer_id = sender.get("customerId")
        customer_name = sender.get("displayName", "")
        
        # Extract message content
        text_content = ""
        attachments = []
        
        if "text" in message:
            text_content = message["text"]
        
        if "suggestions" in message:
            # Handle suggested replies
            for suggestion in message["suggestions"]:
                if suggestion.get("action", {}).get("text"):
                    text_content += f"\n[Suggestion: {suggestion['action']['text']}]"
        
        if "richCard" in message:
            # Handle rich cards (images, etc.)
            rich_card = message["richCard"]
            attachments.append({
                "type": "rich_card",
                "content": rich_card
            })
        
        # Find or create lead
        existing_lead = db.query(Lead).filter(
            Lead.social_handles.contains({
                "google_business": {
                    "customer_id": customer_id,
                    "name": customer_name
                }
            })
        ).first()
        
        if not existing_lead:
            # Create new lead from Google Business message
            lead_data = {
                "source": LeadSource.GOOGLE_MY_BUSINESS,
                "status": LeadStatus.NEW,
                "name": customer_name or f"Google Customer {customer_id[-4:] if customer_id else 'Unknown'}",
                "social_handles": {
                    "google_business": {
                        "customer_id": customer_id,
                        "name": customer_name,
                        "agent_id": agent_id
                    }
                },
                "notes": f"Google Business Message: {text_content[:100]}..."
            }
            
            existing_lead = Lead(**lead_data)
            db.add(existing_lead)
            db.flush()
            
            # Log lead creation
            lead_event = Event(
                event_type="lead_created",
                entity_type="lead",
                entity_id=str(existing_lead.id),
                data={
                    "source": "google_business_webhook",
                    "customer_id": customer_id,
                    "name": customer_name,
                    "agent_id": agent_id,
                    "initial_message": text_content
                }
            )
            db.add(lead_event)
        
        # Find or create conversation thread
        thread = db.query(SocialThread).filter(
            SocialThread.lead_id == existing_lead.id,
            SocialThread.platform == "google_business",
            SocialThread.thread_external_id == conversation_id
        ).first()
        
        if not thread:
            thread = SocialThread(
                lead_id=existing_lead.id,
                platform="google_business",
                thread_external_id=conversation_id,
                status=ThreadStatus.OPEN,
                customer_handle=customer_name or customer_id,
                platform_metadata={
                    "conversation_id": conversation_id,
                    "customer_id": customer_id,
                    "agent_id": agent_id,
                    "customer_name": customer_name
                }
            )
            db.add(thread)
            db.flush()
        
        # Create message event
        message_event = Event(
            event_type="message_received",
            entity_type="thread",
            entity_id=str(thread.id),
            data={
                "message_id": message_id,
                "conversation_id": conversation_id,
                "customer_id": customer_id,
                "text": text_content,
                "attachments": attachments,
                "timestamp": datetime.now().isoformat(),
                "direction": "inbound",
                "channel": "google_business"
            }
        )
        db.add(message_event)
        
        # Update thread
        thread.last_message_at = datetime.now()
        thread.unread_count = (thread.unread_count or 0) + 1
        
        db.commit()
        
        return {
            "thread_id": str(thread.id),
            "lead_id": str(existing_lead.id),
            "message_id": message_id,
            "conversation_id": conversation_id,
            "sender": customer_name or customer_id,
            "text": text_content,
            "platform": "google_business"
        }
        
    except Exception as e:
        logger.error(f"Error processing Google Business message: {e}")
        db.rollback()
        return None


async def process_google_business_event(
    event_data: Dict[str, Any],
    db: Session
) -> Optional[Dict[str, Any]]:
    """Process Google Business messaging events (read receipts, etc.)."""
    try:
        event_type = event_data.get("eventType")
        conversation_id = event_data.get("conversationId")
        
        if not event_type or not conversation_id:
            return None
        
        # Find the thread
        thread = db.query(SocialThread).filter(
            SocialThread.platform == "google_business",
            SocialThread.thread_external_id == conversation_id
        ).first()
        
        if not thread:
            return None
        
        # Create event based on type
        event_mapping = {
            "MESSAGE_READ": "message_read",
            "TYPING_STARTED": "typing_started",
            "TYPING_STOPPED": "typing_stopped",
            "CONVERSATION_STARTED": "conversation_started",
            "CONVERSATION_ENDED": "conversation_ended"
        }
        
        mapped_event = event_mapping.get(event_type, "unknown_event")
        
        # Create event record
        event_record = Event(
            event_type=mapped_event,
            entity_type="thread",
            entity_id=str(thread.id),
            data={
                "conversation_id": conversation_id,
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "channel": "google_business"
            }
        )
        db.add(event_record)
        
        # Update thread status if conversation ended
        if event_type == "CONVERSATION_ENDED":
            thread.status = ThreadStatus.CLOSED
            thread.closed_at = datetime.now()
        
        db.commit()
        
        return {
            "thread_id": str(thread.id),
            "event_type": mapped_event,
            "conversation_id": conversation_id,
            "platform": "google_business"
        }
        
    except Exception as e:
        logger.error(f"Error processing Google Business event: {e}")
        db.rollback()
        return None


@router.post("/webhook")
async def google_business_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle Google Business Messages webhooks.
    Processes customer messages and conversation events.
    """
    try:
        payload = await request.body()
        webhook_data = json.loads(payload.decode())
        
        # Verify webhook if secret is configured
        if settings.google_business_webhook_secret:
            signature = request.headers.get("X-Goog-Signature")
            if not verify_google_signature(
                payload,
                signature,
                settings.google_business_webhook_secret
            ):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process webhook based on type
        webhook_type = webhook_data.get("eventType")
        
        if webhook_type == "MESSAGE_RECEIVED":
            # Process incoming message
            message_data = webhook_data.get("message", {})
            result = await process_google_business_message(message_data, db)
            
            if result:
                # Trigger AI analysis
                background_tasks.add_task(
                    analyze_business_message,
                    result["thread_id"],
                    result["text"]
                )
                
                # Broadcast update
                background_tasks.add_task(
                    broadcast_thread_update,
                    result
                )
                
                # Auto-respond with business hours if needed
                background_tasks.add_task(
                    check_business_hours_response,
                    result["conversation_id"]
                )
        
        elif webhook_type in [
            "MESSAGE_READ", 
            "TYPING_STARTED", 
            "TYPING_STOPPED",
            "CONVERSATION_STARTED",
            "CONVERSATION_ENDED"
        ]:
            # Process conversation events
            result = await process_google_business_event(webhook_data, db)
            
            if result:
                background_tasks.add_task(
                    broadcast_thread_update,
                    result
                )
        
        return {"status": "processed", "type": webhook_type}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing Google Business webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def analyze_business_message(thread_id: str, message_text: str):
    """Analyze business message with AI for intent and sentiment."""
    try:
        ai_manager = await get_ai_lead_manager()
        
        # AI analysis for business inquiries
        analysis_prompt = f"""
        Analyze this Google Business message for:
        1. Customer intent (inquiry, complaint, booking, etc.)
        2. Urgency level (low, medium, high)
        3. Sentiment (positive, neutral, negative)
        4. Suggested response type
        
        Message: {message_text}
        """
        
        # Would integrate with AI service
        logger.info(f"AI analysis for business message in thread {thread_id}: {message_text}")
        
    except Exception as e:
        logger.error(f"Error in business message AI analysis: {e}")


async def check_business_hours_response(conversation_id: str):
    """Check if auto-response needed based on business hours."""
    try:
        current_hour = datetime.now().hour
        
        # Check if outside business hours (9 AM - 6 PM)
        if current_hour < 9 or current_hour >= 18:
            # Would send auto-response via Google Business Messages API
            logger.info(f"Auto-response triggered for conversation {conversation_id} (outside business hours)")
        
    except Exception as e:
        logger.error(f"Error checking business hours response: {e}")


async def broadcast_thread_update(thread_data: Dict[str, Any]):
    """Broadcast thread updates via WebSocket."""
    try:
        logger.info(f"Broadcasting Google Business thread update: {thread_data}")
    except Exception as e:
        logger.error(f"Error broadcasting thread update: {e}")


@router.get("/health")
async def webhook_health():
    """Health check for Google Business webhook."""
    return {
        "status": "healthy",
        "service": "google_business_webhook",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/send-message")
async def send_business_message(
    conversation_id: str,
    message: str,
    db: Session = Depends(get_db)
):
    """
    Send message via Google Business Messages API.
    This would integrate with the actual API to send responses.
    """
    try:
        # Find the thread
        thread = db.query(SocialThread).filter(
            SocialThread.platform == "google_business",
            SocialThread.thread_external_id == conversation_id
        ).first()
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Would send via Google Business Messages API
        # For now, just log the outbound message
        
        # Create outbound message event
        message_event = Event(
            event_type="message_sent",
            entity_type="thread",
            entity_id=str(thread.id),
            data={
                "conversation_id": conversation_id,
                "text": message,
                "timestamp": datetime.now().isoformat(),
                "direction": "outbound",
                "channel": "google_business"
            }
        )
        db.add(message_event)
        
        # Update thread
        thread.last_message_at = datetime.now()
        db.commit()
        
        return {
            "status": "sent",
            "conversation_id": conversation_id,
            "message": message
        }
        
    except Exception as e:
        logger.error(f"Error sending Google Business message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")