"""
Stripe webhook handler for unified inbox.
Handles payment events, customer communications, and financial notifications.
"""
from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import json
import logging
from datetime import datetime
import stripe
import hmac
import hashlib

from api.app.database import get_db
from api.app.config import settings
from api.app.models.lead_newsletter import Lead, LeadSource, LeadStatus, SocialThread, ThreadStatus
from api.app.models.core import Event
from api.app.services.ai_lead_management import get_ai_lead_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/stripe", tags=["webhooks", "payments"])

# Initialize Stripe
if settings.stripe_secret_key:
    stripe.api_key = settings.stripe_secret_key


def verify_stripe_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Stripe webhook signature."""
    try:
        stripe.Webhook.construct_event(payload, signature, secret)
        return True
    except (ValueError, stripe.error.SignatureVerificationError):
        return False


async def process_payment_event(
    stripe_event: Dict[str, Any],
    db: Session
) -> Optional[Dict[str, Any]]:
    """Process Stripe payment events."""
    try:
        event_type = stripe_event.get("type")
        event_data = stripe_event.get("data", {}).get("object", {})
        
        # Extract customer information
        customer_id = event_data.get("customer")
        customer_email = event_data.get("receipt_email") or event_data.get("billing_details", {}).get("email")
        
        if not customer_id and not customer_email:
            return None
        
        # Get customer details from Stripe
        customer_info = None
        if customer_id:
            try:
                customer_info = stripe.Customer.retrieve(customer_id)
            except Exception as e:
                logger.error(f"Error retrieving Stripe customer: {e}")
        
        customer_name = ""
        if customer_info:
            customer_name = customer_info.get("name") or customer_info.get("email", "").split("@")[0]
        elif customer_email:
            customer_name = customer_email.split("@")[0]
        
        # Find or create lead
        existing_lead = None
        
        # Try to find by Stripe customer ID first
        if customer_id:
            existing_lead = db.query(Lead).filter(
                Lead.social_handles.contains({
                    "stripe": {"customer_id": customer_id}
                })
            ).first()
        
        # Try to find by email if not found by customer ID
        if not existing_lead and customer_email:
            existing_lead = db.query(Lead).filter(
                Lead.email == customer_email
            ).first()
        
        if not existing_lead:
            # Create new lead from payment event
            lead_data = {
                "source": LeadSource.PAYMENT,
                "status": LeadStatus.CUSTOMER,  # Payment events indicate existing customer
                "name": customer_name or f"Stripe Customer {customer_id[-4:] if customer_id else 'Unknown'}",
                "email": customer_email,
                "social_handles": {
                    "stripe": {
                        "customer_id": customer_id,
                        "email": customer_email
                    }
                },
                "notes": f"Created from Stripe event: {event_type}"
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
                    "source": "stripe_webhook",
                    "customer_id": customer_id,
                    "email": customer_email,
                    "trigger_event": event_type
                }
            )
            db.add(lead_event)
        
        # Find or create payment thread
        thread_external_id = f"stripe_{customer_id or customer_email}"
        thread = db.query(SocialThread).filter(
            SocialThread.lead_id == existing_lead.id,
            SocialThread.platform == "stripe",
            SocialThread.thread_external_id == thread_external_id
        ).first()
        
        if not thread:
            thread = SocialThread(
                lead_id=existing_lead.id,
                platform="stripe",
                thread_external_id=thread_external_id,
                status=ThreadStatus.OPEN,
                customer_handle=customer_name or customer_email,
                platform_metadata={
                    "customer_id": customer_id,
                    "email": customer_email,
                    "name": customer_name
                }
            )
            db.add(thread)
            db.flush()
        
        # Generate human-readable message based on event type
        message_content = generate_payment_message(event_type, event_data)
        
        # Create payment event
        payment_event = Event(
            event_type="payment_notification",
            entity_type="thread",
            entity_id=str(thread.id),
            data={
                "stripe_event_id": stripe_event.get("id"),
                "stripe_event_type": event_type,
                "customer_id": customer_id,
                "message": message_content,
                "event_data": event_data,
                "timestamp": datetime.now().isoformat(),
                "direction": "system",
                "channel": "stripe"
            }
        )
        db.add(payment_event)
        
        # Update thread
        thread.last_message_at = datetime.now()
        if event_type in ["payment_intent.payment_failed", "invoice.payment_failed"]:
            thread.unread_count = (thread.unread_count or 0) + 1  # Failed payments need attention
        
        db.commit()
        
        return {
            "thread_id": str(thread.id),
            "lead_id": str(existing_lead.id),
            "event_type": event_type,
            "customer": customer_name or customer_email,
            "message": message_content,
            "platform": "stripe"
        }
        
    except Exception as e:
        logger.error(f"Error processing Stripe payment event: {e}")
        db.rollback()
        return None


def generate_payment_message(event_type: str, event_data: Dict[str, Any]) -> str:
    """Generate human-readable message for payment events."""
    amount = event_data.get("amount", 0) / 100  # Convert from cents
    currency = event_data.get("currency", "usd").upper()
    
    message_templates = {
        "payment_intent.succeeded": f"✅ Payment of ${amount:.2f} {currency} completed successfully",
        "payment_intent.payment_failed": f"❌ Payment of ${amount:.2f} {currency} failed",
        "payment_intent.requires_action": f"⚠️ Payment of ${amount:.2f} {currency} requires additional action",
        "invoice.payment_succeeded": f"✅ Invoice payment of ${amount:.2f} {currency} received",
        "invoice.payment_failed": f"❌ Invoice payment of ${amount:.2f} {currency} failed",
        "invoice.created": f"📄 New invoice created for ${amount:.2f} {currency}",
        "customer.subscription.created": f"🎉 New subscription started",
        "customer.subscription.updated": f"📝 Subscription updated",
        "customer.subscription.deleted": f"❌ Subscription cancelled",
        "charge.dispute.created": f"⚠️ Payment dispute created for ${amount:.2f} {currency}",
        "customer.created": f"👤 New customer profile created",
        "customer.updated": f"📝 Customer profile updated",
    }
    
    return message_templates.get(event_type, f"💳 Payment event: {event_type}")


async def process_dispute_event(
    stripe_event: Dict[str, Any],
    db: Session
) -> Optional[Dict[str, Any]]:
    """Process Stripe dispute events with high priority."""
    try:
        event_data = stripe_event.get("data", {}).get("object", {})
        charge_id = event_data.get("charge")
        
        if not charge_id:
            return None
        
        # Get charge details to find customer
        try:
            charge = stripe.Charge.retrieve(charge_id)
            customer_id = charge.get("customer")
        except Exception as e:
            logger.error(f"Error retrieving charge for dispute: {e}")
            return None
        
        if not customer_id:
            return None
        
        # Find lead by customer ID
        existing_lead = db.query(Lead).filter(
            Lead.social_handles.contains({
                "stripe": {"customer_id": customer_id}
            })
        ).first()
        
        if not existing_lead:
            return None
        
        # Create high-priority dispute thread
        thread_external_id = f"stripe_dispute_{charge_id}"
        thread = SocialThread(
            lead_id=existing_lead.id,
            platform="stripe",
            thread_external_id=thread_external_id,
            status=ThreadStatus.URGENT,
            customer_handle=existing_lead.name,
            metadata={
                "customer_id": customer_id,
                "charge_id": charge_id,
                "dispute_id": event_data.get("id"),
                "priority": "high"
            }
        )
        db.add(thread)
        db.flush()
        
        # Create dispute event
        dispute_event = Event(
            event_type="payment_dispute",
            entity_type="thread",
            entity_id=str(thread.id),
            data={
                "stripe_event_id": stripe_event.get("id"),
                "dispute_id": event_data.get("id"),
                "charge_id": charge_id,
                "customer_id": customer_id,
                "amount": event_data.get("amount", 0) / 100,
                "reason": event_data.get("reason"),
                "status": event_data.get("status"),
                "timestamp": datetime.now().isoformat(),
                "direction": "system",
                "channel": "stripe",
                "priority": "high"
            }
        )
        db.add(dispute_event)
        
        thread.last_message_at = datetime.now()
        thread.unread_count = 1
        
        db.commit()
        
        return {
            "thread_id": str(thread.id),
            "lead_id": str(existing_lead.id),
            "event_type": "dispute",
            "customer": existing_lead.name,
            "priority": "high",
            "platform": "stripe"
        }
        
    except Exception as e:
        logger.error(f"Error processing Stripe dispute: {e}")
        db.rollback()
        return None


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhooks.
    Processes payment events, disputes, and customer notifications.
    """
    try:
        payload = await request.body()
        
        # Verify webhook signature
        if settings.stripe_webhook_secret and stripe_signature:
            if not verify_stripe_signature(
                payload,
                stripe_signature,
                settings.stripe_webhook_secret
            ):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        stripe_event = json.loads(payload.decode())
        event_type = stripe_event.get("type")
        
        # Process different types of Stripe events
        if event_type.startswith("payment_intent.") or event_type.startswith("invoice."):
            # Payment events
            result = await process_payment_event(stripe_event, db)
            
            if result:
                background_tasks.add_task(
                    analyze_payment_event,
                    result["thread_id"],
                    event_type,
                    stripe_event.get("data", {}).get("object", {})
                )
                
                background_tasks.add_task(
                    broadcast_thread_update,
                    result
                )
        
        elif event_type.startswith("charge.dispute."):
            # Dispute events (high priority)
            result = await process_dispute_event(stripe_event, db)
            
            if result:
                background_tasks.add_task(
                    handle_dispute_alert,
                    result["thread_id"],
                    stripe_event.get("data", {}).get("object", {})
                )
                
                background_tasks.add_task(
                    broadcast_thread_update,
                    result
                )
        
        elif event_type.startswith("customer.subscription."):
            # Subscription events
            result = await process_payment_event(stripe_event, db)
            
            if result:
                background_tasks.add_task(
                    handle_subscription_change,
                    result["thread_id"],
                    event_type
                )
        
        return {"status": "processed", "type": event_type}
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def analyze_payment_event(
    thread_id: str, 
    event_type: str, 
    event_data: Dict[str, Any]
):
    """Analyze payment events for patterns and insights."""
    try:
        ai_manager = await get_ai_lead_manager()
        
        # AI analysis for payment patterns
        logger.info(f"AI analysis for payment event {event_type} in thread {thread_id}")
        
        # Could analyze for:
        # - Failed payment patterns
        # - Customer payment behavior
        # - Revenue insights
        # - Churn risk indicators
        
    except Exception as e:
        logger.error(f"Error in payment event AI analysis: {e}")


async def handle_dispute_alert(thread_id: str, dispute_data: Dict[str, Any]):
    """Handle high-priority dispute alerts."""
    try:
        # Send immediate notifications for disputes
        logger.warning(f"Payment dispute alert for thread {thread_id}: {dispute_data}")
        
        # Could trigger:
        # - Email notifications to finance team
        # - Slack alerts
        # - Priority escalation
        
    except Exception as e:
        logger.error(f"Error handling dispute alert: {e}")


async def handle_subscription_change(thread_id: str, event_type: str):
    """Handle subscription lifecycle events."""
    try:
        logger.info(f"Subscription change {event_type} for thread {thread_id}")
        
        # Could trigger:
        # - Customer success outreach
        # - Retention campaigns
        # - Upgrade/downgrade notifications
        
    except Exception as e:
        logger.error(f"Error handling subscription change: {e}")


async def broadcast_thread_update(thread_data: Dict[str, Any]):
    """Broadcast thread updates via WebSocket."""
    try:
        logger.info(f"Broadcasting Stripe thread update: {thread_data}")
    except Exception as e:
        logger.error(f"Error broadcasting Stripe thread update: {e}")


@router.get("/health")
async def webhook_health():
    """Health check for Stripe webhook."""
    return {
        "status": "healthy",
        "service": "stripe_webhook",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/events/{customer_id}")
async def get_customer_payment_history(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """Get payment history for a customer."""
    try:
        # Find lead by Stripe customer ID
        lead = db.query(Lead).filter(
            Lead.social_handles.contains({
                "stripe": {"customer_id": customer_id}
            })
        ).first()
        
        if not lead:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        # Get payment events for this customer
        events = db.query(Event).filter(
            Event.entity_type == "thread",
            Event.event_type == "payment_notification",
            Event.data.contains({"customer_id": customer_id})
        ).order_by(Event.created_at.desc()).limit(50).all()
        
        return {
            "customer_id": customer_id,
            "lead_id": str(lead.id),
            "events": [
                {
                    "id": str(event.id),
                    "type": event.data.get("stripe_event_type"),
                    "message": event.data.get("message"),
                    "timestamp": event.created_at.isoformat()
                }
                for event in events
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting customer payment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment history")