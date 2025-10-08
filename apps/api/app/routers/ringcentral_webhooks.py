"""RingCentral SMS webhook and integration endpoints."""

import logging
import json
from datetime import datetime
from typing import Dict, Any, List
from uuid import UUID
from fastapi import APIRouter, Request, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database import get_db
from ..models.lead_newsletter import Lead, LeadContact, SocialThread, ContactChannel
from ..services.ringcentral_sms import ringcentral_sms, SMSMessage
from ..services.ai_lead_management import get_ai_lead_manager, get_social_media_ai


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/ringcentral", tags=["webhooks", "sms"])


@router.post("/sms")
async def handle_sms_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle RingCentral SMS webhook notifications."""
    
    try:
        # Get webhook payload
        payload = await request.json()
        
        logger.info(f"Received RingCentral SMS webhook: {payload}")
        
        # Process webhook with RingCentral service
        async with ringcentral_sms as sms_service:
            messages = await sms_service.handle_webhook_notification(payload)
        
        # Process each message
        for message in messages:
            background_tasks.add_task(_process_sms_message, message, db)
        
        return {"success": True, "processed_messages": len(messages)}
        
    except Exception as e:
        logger.error(f"SMS webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process SMS webhook"
        )


@router.post("/verification")
async def handle_verification_webhook(request: Request):
    """Handle RingCentral webhook verification."""
    
    try:
        payload = await request.json()
        
        # RingCentral sends a verification request when setting up webhooks
        if payload.get("validationToken"):
            return {"validationToken": payload["validationToken"]}
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Webhook verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification request"
        )


@router.post("/sync-messages")
async def sync_recent_messages(
    background_tasks: BackgroundTasks,
    hours_back: int = 24,
    db: Session = Depends(get_db)
):
    """Manually sync recent SMS messages from RingCentral."""
    
    try:
        # Get messages from the specified time range
        date_from = datetime.now() - datetime.timedelta(hours=hours_back)
        
        async with ringcentral_sms as sms_service:
            messages = await sms_service.get_messages(date_from=date_from)
        
        # Process each message
        for message in messages:
            background_tasks.add_task(_process_sms_message, message, db)
        
        return {
            "success": True,
            "message": f"Syncing {len(messages)} messages from last {hours_back} hours",
            "messages_count": len(messages)
        }
        
    except Exception as e:
        logger.error(f"Message sync failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync messages"
        )


async def _process_sms_message(message: SMSMessage, db: Session):
    """Process individual SMS message and create/update leads."""
    
    try:
        # Skip outbound messages (we sent them)
        if message.direction == "Outbound":
            return
        
        phone_number = message.from_number
        message_content = message.body
        
        # Find existing lead or customer by phone number
        lead = await _find_lead_by_phone(phone_number, db)
        customer = await _find_customer_by_phone(phone_number, db)
        
        # If no existing lead or customer, create new lead
        if not lead and not customer:
            lead = await _create_lead_from_sms(phone_number, message_content, db)
        
        # Update existing lead with new contact
        if lead:
            lead.last_contact_date = message.creation_time
            
            # Add SMS event
            lead.add_event("sms_received", {
                "phone_number": phone_number,
                "message": message_content,
                "message_id": message.id,
                "conversation_id": message.conversation_id
            })
            
            # Process with AI for lead scoring and insights
            await _process_message_with_ai(lead, message_content, db)
        
        db.commit()
        logger.info(f"Processed SMS message from {phone_number}")
        
    except Exception as e:
        logger.error(f"Error processing SMS message: {e}")
        db.rollback()


async def _find_lead_by_phone(phone_number: str, db: Session) -> Lead:
    """Find lead by phone number."""
    
    # Clean phone number for comparison
    clean_phone = _clean_phone_number(phone_number)
    
    # Query lead contacts for phone number
    lead_contact = db.query(LeadContact).filter(
        and_(
            LeadContact.channel == ContactChannel.SMS,
            LeadContact.handle_or_address.like(f"%{clean_phone}%")
        )
    ).first()
    
    if lead_contact:
        return db.query(Lead).filter(Lead.id == lead_contact.lead_id).first()
    
    return None


async def _find_customer_by_phone(phone_number: str, db: Session):
    """Find customer by phone number (encrypted)."""
    
    # This would require decrypting phone numbers to compare
    # For now, we'll skip customer lookup by phone
    # TODO: Implement encrypted phone search
    return None


async def _create_lead_from_sms(phone_number: str, message_content: str, db: Session) -> Lead:
    """Create new lead from SMS message."""
    
    # Create lead
    lead = Lead(
        source="sms",
        status="new"
    )
    db.add(lead)
    db.flush()  # Get the lead ID
    
    # Add phone contact
    contact = LeadContact(
        lead_id=lead.id,
        channel=ContactChannel.SMS,
        handle_or_address=phone_number,
        verified=True  # SMS numbers are considered verified
    )
    db.add(contact)
    
    # Add initial event
    lead.add_event("lead_created", {
        "source": "sms",
        "initial_message": message_content,
        "phone_number": phone_number
    })
    
    return lead


async def _process_message_with_ai(lead: Lead, message_content: str, db: Session):
    """Process message with AI for insights and scoring."""
    
    try:
        # Get conversation history for context
        conversation_history = []
        for event in lead.events:
            if event.type in ["sms_received", "sms_sent"]:
                conversation_history.append({
                    "role": "customer" if event.type == "sms_received" else "assistant",
                    "content": event.payload.get("message", ""),
                    "timestamp": event.occurred_at.isoformat()
                })
        
        # Add current message
        conversation_history.append({
            "role": "customer",
            "content": message_content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Analyze with AI
        ai_manager = await get_ai_lead_manager()
        insights = await ai_manager.analyze_conversation(conversation_history)
        
        # Update lead score
        ai_score = await ai_manager.score_lead_with_ai(lead, conversation_history)
        lead.score = ai_score
        
        # Update lead quality
        lead.quality = await ai_manager.determine_lead_quality(lead, ai_score)
        
        # Check for auto-qualification
        if await ai_manager.auto_qualify_lead(lead, conversation_history):
            lead.status = "qualified"
            lead.add_event("auto_qualified", {
                "reason": "AI analysis indicates high conversion probability",
                "ai_score": ai_score,
                "insights": {
                    "intent_score": insights.intent_score,
                    "urgency_level": insights.urgency_level,
                    "sentiment": insights.sentiment
                }
            })
        
        # Generate suggested response
        social_ai = await get_social_media_ai()
        context = {
            "lead_source": lead.source.value,
            "lead_score": ai_score,
            "insights": insights.__dict__
        }
        
        suggested_response = await social_ai.generate_response(message_content, context)
        
        # Add AI analysis event
        lead.add_event("ai_analysis", {
            "insights": insights.__dict__,
            "ai_score": ai_score,
            "suggested_response": suggested_response
        })
        
    except Exception as e:
        logger.error(f"AI processing failed for lead {lead.id}: {e}")


def _clean_phone_number(phone_number: str) -> str:
    """Clean phone number for comparison."""
    
    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone_number))
    
    # Remove leading '1' if present (US country code)
    if digits_only.startswith('1') and len(digits_only) == 11:
        digits_only = digits_only[1:]
    
    return digits_only


# SMS sending endpoints
@router.post("/send-sms")
async def send_sms_message(
    to_number: str,
    message: str,
    background_tasks: BackgroundTasks,
    lead_id: UUID = None,
    from_number: str = None,
    db: Session = Depends(get_db)
):
    """Send SMS message via RingCentral."""
    
    try:
        async with ringcentral_sms as sms_service:
            response = await sms_service.send_sms(
                to_number=to_number,
                message=message,
                from_number=from_number
            )
        
        if response.success:
            # Update lead if provided
            if lead_id:
                background_tasks.add_task(_record_outbound_sms, lead_id, to_number, message, response.message_id, db)
            
            return {
                "success": True,
                "message_id": response.message_id,
                "message": "SMS sent successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send SMS: {response.error}"
            )
            
    except Exception as e:
        logger.error(f"SMS sending failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send SMS"
        )


async def _record_outbound_sms(lead_id: UUID, to_number: str, message: str, message_id: str, db: Session):
    """Record outbound SMS in lead events."""
    
    try:
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            lead.add_event("sms_sent", {
                "to_number": to_number,
                "message": message,
                "message_id": message_id,
                "sent_at": datetime.now().isoformat()
            })
            lead.last_contact_date = datetime.now()
            db.commit()
            
    except Exception as e:
        logger.error(f"Failed to record outbound SMS: {e}")
        db.rollback()