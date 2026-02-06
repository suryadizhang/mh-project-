"""
Enhanced RingCentral webhook handler for unified inbox integration.
Integrates with existing RingCentralSMSService for consistent processing.
"""

from datetime import datetime, timezone
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
    Request,
)
from sqlalchemy.orm import Session

settings = get_settings()
from services.ringcentral_sms import RingCentralSMSService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/ringcentral", tags=["webhooks", "sms"])


def verify_ringcentral_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify RingCentral webhook signature for security."""
    if not signature or not secret:
        return False

    expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_signature)


@router.post("/sms")
async def ringcentral_sms_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_ringcentral_signature: str | None = Header(None),
):
    """
    Handle RingCentral SMS webhooks using unified message router.
    Processes inbound messages and creates conversation threads.
    """
    try:
        payload = await request.body()

        # Verify webhook signature if configured
        webhook_secret = getattr(settings, "ringcentral_webhook_secret", None)
        if webhook_secret and x_ringcentral_signature:
            if not verify_ringcentral_signature(payload, x_ringcentral_signature, webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid signature")

        webhook_data = json.loads(payload.decode())

        # Handle different event types
        for event in webhook_data.get("events", []):
            event_type = event.get("eventType")

            if event_type == "SMS" and event.get("body"):
                message_data = event["body"]
                direction = message_data.get("direction", "")

                if direction == "Inbound":
                    # Extract message details
                    from_number = message_data.get("from", {}).get("phoneNumber", "")
                    to_number = message_data.get("to", [{}])[0].get("phoneNumber", "")
                    message_text = message_data.get("subject", "")
                    message_id = message_data.get("id", "")

                    if from_number and message_text:
                        # Process using existing RingCentral SMS service
                        RingCentralSMSService()

                        # Create a background task to handle the message processing
                        background_tasks.add_task(
                            process_inbound_sms,
                            from_number=from_number,
                            to_number=to_number,
                            message_text=message_text,
                            message_id=message_id,
                            raw_data=message_data,
                            db=db,
                        )

                        # Broadcast real-time update via WebSocket (if available)
                        background_tasks.add_task(
                            broadcast_message_update,
                            {
                                "from_number": from_number,
                                "to_number": to_number,
                                "message_text": message_text,
                                "message_id": message_id,
                                "channel": "sms",
                                "direction": "inbound",
                            },
                        )

                        logger.info(f"SMS processed via RingCentral service: {message_id}")
                    else:
                        logger.warning("Invalid SMS data: missing phone number or text")

                elif direction == "Outbound":
                    # Log outbound SMS for thread tracking
                    logger.info(f"Outbound SMS logged: {message_data.get('id')}")

        return {"status": "processed", "timestamp": datetime.now(timezone.utc).isoformat()}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.exception(f"Error processing RingCentral webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/voice")
async def ringcentral_voice_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_ringcentral_signature: str | None = Header(None),
):
    """
    Handle RingCentral voice call webhooks.
    Processes call events for lead tracking.
    """
    try:
        payload = await request.body()

        # Verify webhook signature if configured
        webhook_secret = getattr(settings, "ringcentral_webhook_secret", None)
        if webhook_secret and x_ringcentral_signature:
            if not verify_ringcentral_signature(payload, x_ringcentral_signature, webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid signature")

        webhook_data = json.loads(payload.decode())

        # Handle call events
        for event in webhook_data.get("events", []):
            event_type = event.get("eventType")

            if event_type == "CallLog" and event.get("body"):
                call_data = event["body"]

                # Log call for future processing
                logger.info(f"Call event received: {call_data.get('id')}")

                # Future: Process call data with unified message router
                # This would create call records and link to leads

        return {"status": "processed", "timestamp": datetime.now(timezone.utc).isoformat()}

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.exception(f"Error processing RingCentral voice webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


async def process_inbound_sms(
    from_number: str,
    to_number: str,
    message_text: str,
    message_id: str,
    raw_data: dict[str, Any],
    db: Session,
):
    """Process inbound SMS message using existing service architecture."""
    try:
        logger.info(f"Processing inbound SMS: {message_id} from {from_number}")

        # Here you would add your lead management logic
        # For now, just log the message details
        logger.info(f"SMS Content: {message_text}")

        # Future: Add lead creation/update logic here
        # This would follow the same pattern as the main webhook handler

    except Exception as e:
        logger.exception(f"Error processing inbound SMS {message_id}: {e}")


async def broadcast_message_update(processing_result: dict[str, Any]):
    """Broadcast message updates to WebSocket connections."""
    try:
        {
            "type": "sms_received",
            "data": processing_result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Note: WebSocket manager would be imported here if available
        # await manager.broadcast_to_subscribers(update_message, "inbox_updates")

        logger.info(f"SMS update prepared for broadcast: {processing_result.get('message_id')}")

    except Exception as e:
        logger.exception(f"Error preparing message update: {e}")


@router.get("/health")
async def webhook_health():
    """Health check endpoint for RingCentral webhook."""
    return {
        "status": "healthy",
        "service": "ringcentral_webhook",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "endpoints": ["sms", "voice", "health"],
        "integration": "ringcentral_sms_service",
    }
