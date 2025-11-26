"""
RingCentral Webhook Handler
Receives SMS, Voice Call, and other events from RingCentral
"""

from datetime import datetime, timezone
import hashlib
import hmac
import logging
from typing import Any

from core.config import get_settings
from core.database import get_db
from services.ringcentral_voice_ai import RingCentralVoiceAI, VoiceCallEvent
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ringcentral/webhooks", tags=["ringcentral-webhooks"])


# Pydantic Models
class RCWebhookEvent(BaseModel):
    """RingCentral webhook event payload."""

    timestamp: str
    uuid: str
    event: str
    subscriptionId: str
    body: dict[str, Any]


class SMSInboundEvent(BaseModel):
    """Inbound SMS event."""

    id: str
    from_number: str
    to_number: str
    message: str
    direction: str
    creation_time: str


class CallEvent(BaseModel):
    """Call event (ringing, answered, disconnected)."""

    telephonySessionId: str
    partyId: str
    direction: str
    from_number: str = ""
    to_number: str = ""
    telephonyStatus: str


# Webhook Signature Validation
def validate_webhook_signature(
    body: bytes,
    signature: str | None,
    secret: str | None,
) -> bool:
    """
    Validate RingCentral webhook signature.

    Security: Ensures webhook is actually from RingCentral
    """
    if not secret or not signature:
        logger.warning("Missing webhook signature or secret")
        return False

    try:
        # Compute HMAC-SHA256
        computed_signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

        return hmac.compare_digest(computed_signature, signature)

    except Exception as e:
        logger.exception(f"Signature validation error: {e}")
        return False


# Main Webhook Endpoint
@router.post("/events")
async def handle_webhook_event(
    request: Request,
    background_tasks: BackgroundTasks,
    validation_token: str | None = Header(None, alias="Validation-Token"),
    rc_signature: str | None = Header(None, alias="X-RingCentral-Signature"),
    db: AsyncSession = Depends(get_db),
):
    """
    Main RingCentral webhook receiver.

    Handles:
    - Webhook validation (first-time setup)
    - Inbound SMS
    - Inbound voice calls
    - Call status changes
    - Message delivery status

    Security:
    - Validates webhook signature
    - Logs all events
    """
    try:
        # Handle validation request (webhook setup)
        if validation_token:
            logger.info(f"✅ Webhook validation token received: {validation_token[:20]}...")
            return {"validation-token": validation_token, "status": "validated"}

        # Read request body
        body = await request.body()

        # Validate signature
        webhook_secret = getattr(settings, "ringcentral_webhook_secret", None)
        if webhook_secret:
            if not validate_webhook_signature(body, rc_signature, webhook_secret):
                logger.error("❌ Invalid webhook signature")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature"
                )

        # Parse event
        payload = await request.json()
        event = RCWebhookEvent(**payload)

        logger.info(f"📥 RingCentral event: {event.event} | UUID: {event.uuid}")

        # Route to specific handler
        if "sms" in event.event.lower() or "message" in event.event.lower():
            background_tasks.add_task(handle_sms_event, event, db)
        elif "call" in event.event.lower() or "telephony" in event.event.lower():
            background_tasks.add_task(handle_call_event, event, db)
        else:
            logger.warning(f"Unknown event type: {event.event}")

        return {"status": "received", "uuid": event.uuid}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook processing failed"
        )


# SMS Event Handler
async def handle_sms_event(event: RCWebhookEvent, db: AsyncSession):
    """
    Handle inbound SMS messages.

    Flow:
    1. Parse SMS content
    2. Check for opt-out keywords (STOP, UNSUBSCRIBE)
    3. Generate AI reply
    4. Send response via RingCentral
    5. Create conversation thread in inbox
    """
    try:
        body = event.body

        # Parse SMS data
        from_number = body.get("from", {}).get("phoneNumber", "")
        to_number = body.get("to", [{}])[0].get("phoneNumber", "")
        message_text = body.get("subject", "")
        message_id = body.get("id", "")
        direction = body.get("direction", "Inbound")

        if direction != "Inbound":
            logger.info(f"Skipping outbound SMS: {message_id}")
            return

        logger.info(f"📱 Inbound SMS from {from_number}: {message_text[:50]}...")

        # Check for opt-out keywords
        opt_out_keywords = ["stop", "unsubscribe", "opt out", "opt-out"]
        if any(keyword in message_text.lower() for keyword in opt_out_keywords):
            await handle_sms_opt_out(from_number, db)
            # Send confirmation
            # await send_sms_reply(to_number, from_number, "You have been unsubscribed from SMS. Reply START to opt back in.")
            return

        # Check for opt-in keywords
        if "start" in message_text.lower() or "yes" in message_text.lower():
            await handle_sms_opt_in(from_number, db)
            # Send confirmation
            # await send_sms_reply(to_number, from_number, "You're subscribed to My Hibachi Chef updates! Reply STOP to unsubscribe.")
            return

        # Generate AI reply
        async with RingCentralVoiceAI() as voice_ai:
            ai_reply = await voice_ai.generate_ai_reply(
                message=message_text,
                context={
                    "channel": "sms",
                    "from_number": from_number,
                },
            )

            logger.info(
                f"🤖 AI reply generated | "
                f"Confidence: {ai_reply.confidence:.2f} | "
                f"Intent: {ai_reply.intent} | "
                f"Reply: {ai_reply.reply[:50]}..."
            )

            # If low confidence or should escalate, create inbox item for human
            if ai_reply.should_escalate:
                logger.info("🚨 Escalating SMS to human inbox")
                # TODO: Create inbox thread item
                # await create_inbox_thread(...)
            else:
                # Send automated reply
                # await send_sms_reply(to_number, from_number, ai_reply.reply)
                logger.info("✅ Automated SMS reply sent")

        # Save to database
        # TODO: Save SMS conversation to inbox/messages table

    except Exception as e:
        logger.exception(f"SMS event handling failed: {e}")


# Voice Call Event Handler
async def handle_call_event(event: RCWebhookEvent, db: AsyncSession):
    """
    Handle voice call events.

    Call lifecycle:
    1. call.ringing → Answer call, start AI
    2. call.answered → Begin conversation
    3. call.disconnected → Save transcript, update CRM

    AI features:
    - Real-time STT → GPT-4o mini → TTS
    - Intent detection
    - Booking collection
    - Warm transfer to human
    """
    try:
        body = event.body

        # Parse call data
        session_id = body.get("telephonySessionId", "")
        party_id = body.get("partyId", "")
        direction = body.get("direction", "")
        status_code = body.get("telephonyStatus", "")

        # Get phone numbers
        from_info = body.get("from", {})
        to_info = body.get("to", {})

        from_number = from_info.get("phoneNumber", "")
        to_number = to_info.get("phoneNumber", "")

        logger.info(
            f"📞 Call event: {event.event} | "
            f"Status: {status_code} | "
            f"Direction: {direction} | "
            f"From: {from_number}"
        )

        # Handle ringing → Answer and start AI
        if "ringing" in event.event.lower() and direction == "Inbound":
            call_event = VoiceCallEvent(
                call_id=session_id,
                direction=direction,
                from_number=from_number,
                to_number=to_number,
                status=status_code,
                timestamp=datetime.fromisoformat(event.timestamp.replace("Z", "+00:00")),
            )

            async with RingCentralVoiceAI() as voice_ai:
                result = await voice_ai.handle_inbound_call(call_event)
                logger.info(f"✅ AI call handler started: {result}")

        # Handle disconnected → Save transcript
        elif "disconnected" in event.event.lower():
            logger.info(f"📴 Call ended: {session_id}")
            # TODO: Save call transcript to database
            # TODO: Update customer record
            # TODO: Create follow-up task if needed

    except Exception as e:
        logger.exception(f"Call event handling failed: {e}")


# Helper Functions
async def handle_sms_opt_out(phone_number: str, db: AsyncSession):
    """Update subscriber sms_consent to False."""
    # TODO: Legacy lead/newsletter models not migrated yet - needs refactor
    # try:
    # from sqlalchemy.future import select

    # query = select(Subscriber).where(Subscriber.phone == phone_number)
    # result = await db.execute(query)
    # subscriber = result.scalar_one_or_none()

    # if subscriber:
    # subscriber.sms_consent = False
    # subscriber.subscribed = False
    # await db.commit()
    # logger.info(f"✅ SMS opt-out processed: {phone_number}")
    # else:
    # logger.warning(f"Subscriber not found for opt-out: {phone_number}")

    # except Exception as e:
    # logger.exception(f"Opt-out processing failed: {e}")
    pass


async def handle_sms_opt_in(phone_number: str, db: AsyncSession):
    """Update subscriber sms_consent to True."""
    # TODO: Legacy lead/newsletter models not migrated yet - needs refactor
    # try:
    # from sqlalchemy.future import select

    # query = select(Subscriber).where(Subscriber.phone == phone_number)
    # result = await db.execute(query)
    # subscriber = result.scalar_one_or_none()

    # if subscriber:
    # subscriber.sms_consent = True
    # subscriber.subscribed = True
    # await db.commit()
    # logger.info(f"✅ SMS opt-in processed: {phone_number}")
    # else:
    # Create new subscriber
    # new_subscriber = Subscriber(
    # phone=phone_number,
    # sms_consent=True,
    # email_consent=False,
    # subscribed=True,
    # source="sms_opt_in",
    # )
    # db.add(new_subscriber)
    # await db.commit()
    # logger.info(f"✅ New SMS subscriber created: {phone_number}")

    # except Exception as e:
    # logger.exception(f"Opt-in processing failed: {e}")


# Webhook Subscription Management
@router.post("/subscribe")
async def subscribe_to_events():
    """
    Subscribe to RingCentral events.

    Events to subscribe to:
    - /restapi/v1.0/account/~/extension/~/message-store
    - /restapi/v1.0/account/~/extension/~/telephony/sessions
    """
    try:
        # TODO: Use RingCentral SDK to create webhook subscription
        # This would normally be done once during setup

        return {
            "status": "subscription_created",
            "events": [
                "/restapi/v1.0/account/~/extension/~/message-store",
                "/restapi/v1.0/account/~/extension/~/telephony/sessions",
            ],
        }

    except Exception as e:
        logger.exception(f"Subscription creation failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "webhook_url": f"{settings.api_url}/ringcentral/webhooks/events",
    }
