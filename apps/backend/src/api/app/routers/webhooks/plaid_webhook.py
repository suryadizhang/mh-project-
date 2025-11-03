"""
Plaid webhook handler for unified inbox.
Handles financial account events, transaction monitoring, and banking notifications.
"""

from datetime import datetime
import hashlib
import hmac
import json
import logging
from typing import Any

from api.app.database import get_db
from core.config import get_settings
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

settings = get_settings()
from api.app.models.core import Event
from api.app.models.lead_newsletter import (
    Lead,
    LeadSource,
    LeadStatus,
    SocialThread,
    ThreadStatus,
)
from api.app.services.ai_lead_management import get_ai_lead_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/plaid", tags=["webhooks", "financial"])


def verify_plaid_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Plaid webhook signature."""
    if not signature or not secret:
        return False

    expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


async def process_transaction_event(
    webhook_data: dict[str, Any], db: Session
) -> dict[str, Any] | None:
    """Process Plaid transaction webhook events."""
    try:
        webhook_type = webhook_data.get("webhook_type")
        webhook_code = webhook_data.get("webhook_code")
        item_id = webhook_data.get("item_id")

        if not item_id:
            return None

        # Find lead by Plaid item ID
        existing_lead = (
            db.query(Lead)
            .filter(Lead.social_handles.contains({"plaid": {"item_id": item_id}}))
            .first()
        )

        if not existing_lead:
            # Create lead from financial data if we have enough info
            lead_data = {
                "source": LeadSource.FINANCIAL,
                "status": LeadStatus.CUSTOMER,
                "name": f"Plaid Customer {item_id[-4:]}",
                "social_handles": {
                    "plaid": {"item_id": item_id, "connected_at": datetime.now().isoformat()}
                },
                "notes": f"Created from Plaid webhook: {webhook_type}.{webhook_code}",
            }

            existing_lead = Lead(**lead_data)
            db.add(existing_lead)
            db.flush()

        # Find or create financial thread
        thread_external_id = f"plaid_{item_id}"
        thread = (
            db.query(SocialThread)
            .filter(
                SocialThread.lead_id == existing_lead.id,
                SocialThread.platform == "plaid",
                SocialThread.thread_external_id == thread_external_id,
            )
            .first()
        )

        if not thread:
            thread = SocialThread(
                lead_id=existing_lead.id,
                platform="plaid",
                thread_external_id=thread_external_id,
                status=ThreadStatus.OPEN,
                customer_handle=existing_lead.name,
                platform_metadata={"item_id": item_id, "webhook_types": [webhook_type]},
            )
            db.add(thread)
            db.flush()

        # Generate message based on webhook type and code
        message_content = generate_plaid_message(webhook_type, webhook_code, webhook_data)

        # Determine if this requires attention
        requires_attention = webhook_code in [
            "ITEM_ERROR",
            "NEW_ACCOUNTS_AVAILABLE",
            "PENDING_EXPIRATION",
            "USER_PERMISSION_REVOKED",
        ]

        # Create financial event
        financial_event = Event(
            event_type="financial_notification",
            entity_type="thread",
            entity_id=str(thread.id),
            data={
                "webhook_type": webhook_type,
                "webhook_code": webhook_code,
                "item_id": item_id,
                "message": message_content,
                "requires_attention": requires_attention,
                "webhook_data": webhook_data,
                "timestamp": datetime.now().isoformat(),
                "direction": "system",
                "channel": "plaid",
            },
        )
        db.add(financial_event)

        # Update thread
        thread.last_message_at = datetime.now()
        if requires_attention:
            thread.unread_count = (thread.unread_count or 0) + 1
            thread.status = (
                ThreadStatus.URGENT if webhook_code == "ITEM_ERROR" else ThreadStatus.OPEN
            )

        db.commit()

        return {
            "thread_id": str(thread.id),
            "lead_id": str(existing_lead.id),
            "webhook_type": webhook_type,
            "webhook_code": webhook_code,
            "customer": existing_lead.name,
            "message": message_content,
            "requires_attention": requires_attention,
            "platform": "plaid",
        }

    except Exception as e:
        logger.exception(f"Error processing Plaid transaction event: {e}")
        db.rollback()
        return None


async def process_item_event(webhook_data: dict[str, Any], db: Session) -> dict[str, Any] | None:
    """Process Plaid item-level webhook events."""
    try:
        webhook_code = webhook_data.get("webhook_code")
        item_id = webhook_data.get("item_id")
        error = webhook_data.get("error")

        if not item_id:
            return None

        # Find existing lead
        existing_lead = (
            db.query(Lead)
            .filter(Lead.social_handles.contains({"plaid": {"item_id": item_id}}))
            .first()
        )

        if not existing_lead:
            return None

        # Find existing thread
        thread = (
            db.query(SocialThread)
            .filter(SocialThread.lead_id == existing_lead.id, SocialThread.platform == "plaid")
            .first()
        )

        if not thread:
            return None

        # Handle different item events
        if webhook_code == "ITEM_ERROR":
            # Critical error requiring immediate attention
            thread.status = ThreadStatus.URGENT
            message_content = (
                f"🚨 Account connection error: {error.get('error_message', 'Unknown error')}"
            )

        elif webhook_code == "PENDING_EXPIRATION":
            # Account access expiring soon
            thread.status = ThreadStatus.URGENT
            message_content = "⚠️ Account access expiring soon - please reconnect"

        elif webhook_code == "USER_PERMISSION_REVOKED":
            # User revoked access
            thread.status = ThreadStatus.CLOSED
            message_content = "❌ Account access revoked by user"

        elif webhook_code == "NEW_ACCOUNTS_AVAILABLE":
            # New accounts detected
            message_content = "🏦 New bank accounts detected - please review"

        else:
            message_content = f"📊 Account update: {webhook_code}"

        # Create item event
        item_event = Event(
            event_type="item_notification",
            entity_type="thread",
            entity_id=str(thread.id),
            data={
                "webhook_code": webhook_code,
                "item_id": item_id,
                "error": error,
                "message": message_content,
                "timestamp": datetime.now().isoformat(),
                "direction": "system",
                "channel": "plaid",
            },
        )
        db.add(item_event)

        # Update thread
        thread.last_message_at = datetime.now()
        if webhook_code in ["ITEM_ERROR", "PENDING_EXPIRATION", "NEW_ACCOUNTS_AVAILABLE"]:
            thread.unread_count = (thread.unread_count or 0) + 1

        db.commit()

        return {
            "thread_id": str(thread.id),
            "lead_id": str(existing_lead.id),
            "webhook_code": webhook_code,
            "customer": existing_lead.name,
            "message": message_content,
            "platform": "plaid",
        }

    except Exception as e:
        logger.exception(f"Error processing Plaid item event: {e}")
        db.rollback()
        return None


def generate_plaid_message(
    webhook_type: str, webhook_code: str, webhook_data: dict[str, Any]
) -> str:
    """Generate human-readable message for Plaid events."""
    message_templates = {
        ("TRANSACTIONS", "INITIAL_UPDATE"): "💰 Initial transaction data loaded",
        ("TRANSACTIONS", "HISTORICAL_UPDATE"): "📈 Historical transaction data updated",
        ("TRANSACTIONS", "DEFAULT_UPDATE"): "💳 New transactions detected",
        ("TRANSACTIONS", "TRANSACTIONS_REMOVED"): "🗑️ Transactions removed from account",
        ("ITEM", "WEBHOOK_UPDATE_ACKNOWLEDGED"): "✅ Webhook configuration updated",
        ("ITEM", "ITEM_ERROR"): "🚨 Account connection error",
        ("ITEM", "PENDING_EXPIRATION"): "⏰ Account access expiring soon",
        ("ITEM", "USER_PERMISSION_REVOKED"): "❌ User revoked account access",
        ("ITEM", "NEW_ACCOUNTS_AVAILABLE"): "🏦 New accounts available",
        ("AUTH", "AUTOMATICALLY_VERIFIED"): "✅ Account automatically verified",
        ("AUTH", "VERIFICATION_EXPIRED"): "⏰ Account verification expired",
        ("IDENTITY", "DEFAULT_UPDATE"): "👤 Identity information updated",
        ("ASSETS", "PRODUCT_READY"): "📊 Asset report ready",
        ("HOLDINGS", "DEFAULT_UPDATE"): "📈 Investment holdings updated",
        ("LIABILITIES", "DEFAULT_UPDATE"): "📋 Liability information updated",
    }

    key = (webhook_type, webhook_code)
    default_message = f"📊 Financial update: {webhook_type}.{webhook_code}"

    message = message_templates.get(key, default_message)

    # Add additional context for specific events
    if webhook_code == "ITEM_ERROR":
        error = webhook_data.get("error", {})
        if error:
            message += f" - {error.get('error_message', 'Please reconnect your account')}"

    return message


@router.post("/webhook")
async def plaid_webhook(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Handle Plaid webhooks.
    Processes financial account events and transaction notifications.
    """
    try:
        payload = await request.body()
        webhook_data = json.loads(payload.decode())

        # Verify webhook signature if configured
        if settings.plaid_webhook_secret:
            signature = request.headers.get("Plaid-Signature")
            if not verify_plaid_signature(payload, signature, settings.plaid_webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid signature")

        webhook_type = webhook_data.get("webhook_type")
        webhook_code = webhook_data.get("webhook_code")

        # Process different types of Plaid webhooks
        if webhook_type == "TRANSACTIONS":
            # Transaction-related events
            result = await process_transaction_event(webhook_data, db)

            if result:
                background_tasks.add_task(
                    analyze_transaction_event, result["thread_id"], webhook_code, webhook_data
                )

                background_tasks.add_task(broadcast_thread_update, result)

        elif webhook_type == "ITEM":
            # Item-level events (connection issues, etc.)
            result = await process_item_event(webhook_data, db)

            if result:
                background_tasks.add_task(
                    handle_item_alert, result["thread_id"], webhook_code, webhook_data
                )

                background_tasks.add_task(broadcast_thread_update, result)

        elif webhook_type in ["AUTH", "IDENTITY", "ASSETS", "HOLDINGS", "LIABILITIES"]:
            # Other financial data events
            result = await process_transaction_event(webhook_data, db)

            if result:
                background_tasks.add_task(broadcast_thread_update, result)

        return {"status": "processed", "type": f"{webhook_type}.{webhook_code}"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.exception(f"Error processing Plaid webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def analyze_transaction_event(
    thread_id: str, webhook_code: str, webhook_data: dict[str, Any]
):
    """Analyze transaction events for insights."""
    try:
        await get_ai_lead_manager()

        # AI analysis for financial patterns
        logger.info(f"AI analysis for transaction event {webhook_code} in thread {thread_id}")

        # Could analyze for:
        # - Spending patterns
        # - Income stability
        # - Financial health indicators
        # - Risk factors

    except Exception as e:
        logger.exception(f"Error in transaction event AI analysis: {e}")


async def handle_item_alert(thread_id: str, webhook_code: str, webhook_data: dict[str, Any]):
    """Handle critical item-level alerts."""
    try:
        if webhook_code in ["ITEM_ERROR", "PENDING_EXPIRATION"]:
            logger.warning(f"Critical Plaid item alert {webhook_code} for thread {thread_id}")

            # Could trigger:
            # - Email notifications to customer
            # - Support team alerts
            # - Automated reconnection flows

    except Exception as e:
        logger.exception(f"Error handling item alert: {e}")


async def broadcast_thread_update(thread_data: dict[str, Any]):
    """Broadcast thread updates via WebSocket."""
    try:
        logger.info(f"Broadcasting Plaid thread update: {thread_data}")
    except Exception as e:
        logger.exception(f"Error broadcasting Plaid thread update: {e}")


@router.get("/health")
async def webhook_health():
    """Health check for Plaid webhook."""
    return {
        "status": "healthy",
        "service": "plaid_webhook",
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/accounts/{item_id}")
async def get_financial_summary(item_id: str, db: Session = Depends(get_db)):
    """Get financial activity summary for an item."""
    try:
        # Find lead by Plaid item ID
        lead = (
            db.query(Lead)
            .filter(Lead.social_handles.contains({"plaid": {"item_id": item_id}}))
            .first()
        )

        if not lead:
            raise HTTPException(status_code=404, detail="Financial account not found")

        # Get recent financial events
        events = (
            db.query(Event)
            .filter(
                Event.entity_type == "thread",
                Event.event_type.in_(["financial_notification", "item_notification"]),
                Event.data.contains({"item_id": item_id}),
            )
            .order_by(Event.created_at.desc())
            .limit(50)
            .all()
        )

        return {
            "item_id": item_id,
            "lead_id": str(lead.id),
            "customer": lead.name,
            "events": [
                {
                    "id": str(event.id),
                    "type": event.data.get("webhook_code"),
                    "message": event.data.get("message"),
                    "timestamp": event.created_at.isoformat(),
                    "requires_attention": event.data.get("requires_attention", False),
                }
                for event in events
            ],
        }

    except Exception as e:
        logger.exception(f"Error getting financial summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve financial summary")


@router.post("/reconnect/{item_id}")
async def trigger_reconnection(item_id: str, db: Session = Depends(get_db)):
    """Trigger account reconnection flow."""
    try:
        # Find the thread
        thread = (
            db.query(SocialThread)
            .filter(
                SocialThread.platform == "plaid",
                SocialThread.thread_external_id == f"plaid_{item_id}",
            )
            .first()
        )

        if not thread:
            raise HTTPException(status_code=404, detail="Financial thread not found")

        # Create reconnection event
        reconnect_event = Event(
            event_type="reconnection_requested",
            entity_type="thread",
            entity_id=str(thread.id),
            data={
                "item_id": item_id,
                "requested_at": datetime.now().isoformat(),
                "message": "🔄 Account reconnection requested",
                "direction": "system",
                "channel": "plaid",
            },
        )
        db.add(reconnect_event)

        # Update thread status
        thread.last_message_at = datetime.now()
        db.commit()

        return {"status": "reconnection_initiated", "item_id": item_id, "thread_id": str(thread.id)}

    except Exception as e:
        logger.exception(f"Error triggering reconnection: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger reconnection")
