"""
Meta (Facebook/Instagram) webhook handler for unified inbox.
Handles Instagram DMs and Facebook messages integration.
"""

from datetime import datetime
import hashlib
import hmac
import json
import logging
from typing import Any

from core.database import get_db
from core.config import get_settings
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy.orm import Session

settings = get_settings()
from models.legacy_core import Event
from models.legacy_lead_newsletter import (
    Lead,
    LeadSource,
    LeadStatus,
    SocialThread,
    ThreadStatus,
)
from services.ai_lead_management import get_ai_lead_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/meta", tags=["webhooks", "social"])


def verify_meta_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Meta webhook signature for security."""
    if not signature or not secret:
        return False

    expected_signature = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


async def process_instagram_message(
    messaging_event: dict[str, Any], db: Session
) -> dict[str, Any] | None:
    """Process Instagram direct message."""
    try:
        sender_id = messaging_event.get("sender", {}).get("id")
        recipient_id = messaging_event.get("recipient", {}).get("id")
        message = messaging_event.get("message", {})

        if not sender_id or not message:
            return None

        # Extract message content
        message_text = message.get("text", "")
        message_id = message.get("mid", "")
        attachments = message.get("attachments", [])

        # Get sender info from Instagram API (if available)
        sender_username = await get_instagram_username(sender_id)

        # Find or create lead
        existing_lead = (
            db.query(Lead)
            .filter(
                Lead.social_handles.contains(
                    {"instagram": {"id": sender_id, "username": sender_username}}
                )
            )
            .first()
        )

        if not existing_lead:
            # Create new lead from Instagram message
            lead_data = {
                "source": LeadSource.INSTAGRAM,
                "status": LeadStatus.NEW,
                "name": sender_username or f"Instagram User {sender_id[-4:]}",
                "social_handles": {"instagram": {"id": sender_id, "username": sender_username}},
                "notes": f"Instagram DM: {message_text[:100]}...",
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
                    "source": "instagram_webhook",
                    "sender_id": sender_id,
                    "username": sender_username,
                    "initial_message": message_text,
                },
            )
            db.add(lead_event)

        # Find or create conversation thread
        thread = (
            db.query(SocialThread)
            .filter(SocialThread.lead_id == existing_lead.id, SocialThread.platform == "instagram")
            .first()
        )

        if not thread:
            thread = SocialThread(
                lead_id=existing_lead.id,
                platform="instagram",
                thread_external_id=f"ig_{sender_id}_{recipient_id}",
                status=ThreadStatus.OPEN,
                customer_handle=sender_username or sender_id,
                platform_metadata={
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "username": sender_username,
                },
            )
            db.add(thread)
            db.flush()

        # Process attachments
        attachment_data = []
        for attachment in attachments:
            attachment_data.append(
                {"type": attachment.get("type"), "url": attachment.get("payload", {}).get("url")}
            )

        # Create message event
        message_event = Event(
            event_type="message_received",
            entity_type="thread",
            entity_id=str(thread.id),
            data={
                "message_id": message_id,
                "sender_id": sender_id,
                "text": message_text,
                "attachments": attachment_data,
                "timestamp": datetime.now().isoformat(),
                "direction": "inbound",
                "channel": "instagram",
            },
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
            "sender": sender_username or sender_id,
            "text": message_text,
            "platform": "instagram",
        }

    except Exception as e:
        logger.exception(f"Error processing Instagram message: {e}")
        db.rollback()
        return None


async def process_facebook_message(
    messaging_event: dict[str, Any], db: Session
) -> dict[str, Any] | None:
    """Process Facebook page message."""
    try:
        sender_id = messaging_event.get("sender", {}).get("id")
        recipient_id = messaging_event.get("recipient", {}).get("id")
        message = messaging_event.get("message", {})

        if not sender_id or not message:
            return None

        message_text = message.get("text", "")
        message_id = message.get("mid", "")

        # Get sender info from Facebook API
        sender_name = await get_facebook_user_name(sender_id)

        # Find or create lead
        existing_lead = (
            db.query(Lead)
            .filter(
                Lead.social_handles.contains({"facebook": {"id": sender_id, "name": sender_name}})
            )
            .first()
        )

        if not existing_lead:
            lead_data = {
                "source": LeadSource.FACEBOOK,
                "status": LeadStatus.NEW,
                "name": sender_name or f"Facebook User {sender_id[-4:]}",
                "social_handles": {"facebook": {"id": sender_id, "name": sender_name}},
                "notes": f"Facebook message: {message_text[:100]}...",
            }

            existing_lead = Lead(**lead_data)
            db.add(existing_lead)
            db.flush()

        # Create/update thread (similar to Instagram logic)
        thread = (
            db.query(SocialThread)
            .filter(SocialThread.lead_id == existing_lead.id, SocialThread.platform == "facebook")
            .first()
        )

        if not thread:
            thread = SocialThread(
                lead_id=existing_lead.id,
                platform="facebook",
                thread_external_id=f"fb_{sender_id}_{recipient_id}",
                status=ThreadStatus.OPEN,
                customer_handle=sender_name or sender_id,
                platform_metadata={
                    "sender_id": sender_id,
                    "recipient_id": recipient_id,
                    "name": sender_name,
                },
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
                "sender_id": sender_id,
                "text": message_text,
                "timestamp": datetime.now().isoformat(),
                "direction": "inbound",
                "channel": "facebook",
            },
        )
        db.add(message_event)

        thread.last_message_at = datetime.now()
        thread.unread_count = (thread.unread_count or 0) + 1

        db.commit()

        return {
            "thread_id": str(thread.id),
            "lead_id": str(existing_lead.id),
            "message_id": message_id,
            "sender": sender_name or sender_id,
            "text": message_text,
            "platform": "facebook",
        }

    except Exception as e:
        logger.exception(f"Error processing Facebook message: {e}")
        db.rollback()
        return None


async def get_instagram_username(user_id: str) -> str | None:
    """Get Instagram username from user ID via Instagram Basic Display API."""
    try:
        # This would make an API call to Instagram
        # For now, return a placeholder
        return f"ig_user_{user_id[-4:]}"
    except Exception as e:
        logger.exception(f"Error getting Instagram username: {e}")
        return None


async def get_facebook_user_name(user_id: str) -> str | None:
    """Get Facebook user name from user ID via Graph API."""
    try:
        # This would make an API call to Facebook Graph API
        # For now, return a placeholder
        return f"fb_user_{user_id[-4:]}"
    except Exception as e:
        logger.exception(f"Error getting Facebook user name: {e}")
        return None


@router.get("/verify")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """Verify Meta webhook during setup."""
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_verify_token:
        return int(hub_challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def meta_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_hub_signature_256: str | None = Header(None),
):
    """
    Handle Meta (Facebook/Instagram) webhooks.
    Processes messages from both platforms.
    """
    try:
        payload = await request.body()

        # Verify webhook signature
        if settings.meta_app_secret and x_hub_signature_256:
            if not verify_meta_signature(payload, x_hub_signature_256, settings.meta_app_secret):
                raise HTTPException(status_code=401, detail="Invalid signature")

        webhook_data = json.loads(payload.decode())

        # Process webhook entries
        for entry in webhook_data.get("entry", []):
            # Instagram messaging
            if "messaging" in entry:
                for messaging_event in entry["messaging"]:
                    if "message" in messaging_event:
                        result = await process_instagram_message(messaging_event, db)

                        if result:
                            # Trigger AI analysis
                            background_tasks.add_task(
                                analyze_social_message,
                                result["thread_id"],
                                result["text"],
                                "instagram",
                            )

                            # Broadcast update
                            background_tasks.add_task(broadcast_thread_update, result)

            # Facebook page messaging
            elif "changes" in entry:
                for change in entry["changes"]:
                    if change.get("field") == "messages" and "value" in change:
                        # Process Facebook message
                        messaging_data = change["value"]
                        result = await process_facebook_message(messaging_data, db)

                        if result:
                            background_tasks.add_task(
                                analyze_social_message,
                                result["thread_id"],
                                result["text"],
                                "facebook",
                            )

                            background_tasks.add_task(broadcast_thread_update, result)

        return {"status": "processed"}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.exception(f"Error processing Meta webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def analyze_social_message(thread_id: str, message_text: str, platform: str):
    """Analyze social media message with AI."""
    try:
        await get_ai_lead_manager()
        # AI analysis would happen here
        logger.info(f"AI analysis for {platform} message in thread {thread_id}: {message_text}")
    except Exception as e:
        logger.exception(f"Error in social message AI analysis: {e}")


async def broadcast_thread_update(thread_data: dict[str, Any]):
    """Broadcast thread updates via WebSocket."""
    try:
        logger.info(f"Broadcasting social thread update: {thread_data}")
    except Exception as e:
        logger.exception(f"Error broadcasting social thread update: {e}")


@router.get("/health")
async def webhook_health():
    """Health check for Meta webhook."""
    return {"status": "healthy", "service": "meta_webhook", "timestamp": datetime.now().isoformat()}
