"""
Webhook endpoints for RingCentral and Meta integrations
"""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
)
from sqlalchemy.ext.asyncio import AsyncSession

from api.ai.endpoints.database import get_db
from api.ai.endpoints.schemas import ChatIngestRequest
from api.ai.endpoints.services.channel_manager import channel_manager
from api.ai.endpoints.services.chat_service import chat_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# RingCentral Webhooks
@router.post("/ringcentral/sms")
async def ringcentral_sms_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Handle RingCentral SMS webhook"""
    try:
        # Get request body and signature
        body = await request.body()
        signature = request.headers.get("X-Ringcentral-Signature", "")

        # Validate signature
        if not channel_manager.validate_ringcentral_webhook(body, signature):
            raise HTTPException(
                status_code=401, detail="Invalid webhook signature"
            )

        # Parse webhook data
        webhook_data = await request.json()

        # Convert to chat ingest format
        ingest_data = channel_manager.parse_ringcentral_sms(webhook_data)

        # Create ingest request
        ingest_request = ChatIngestRequest(
            channel=ingest_data["channel"],
            user_id=ingest_data["user_id"],
            thread_id=ingest_data["thread_id"],
            text=ingest_data["text"],
            metadata=ingest_data["metadata"],
        )

        # Process message
        response = await chat_service.ingest_chat(ingest_request, db)

        # Send reply via SMS (background task to avoid blocking webhook response)
        background_tasks.add_task(
            channel_manager.send_sms,
            ingest_data["metadata"]["from_number"],
            response.reply,
        )

        return {"status": "processed", "message_id": str(response.message_id)}

    except Exception as e:
        print(f"Error processing RingCentral SMS webhook: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process SMS webhook"
        )


@router.post("/ringcentral/voice")
async def ringcentral_voice_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Handle RingCentral voice webhook"""
    try:
        # Get request body and signature
        body = await request.body()
        signature = request.headers.get("X-Ringcentral-Signature", "")

        # Validate signature
        if not channel_manager.validate_ringcentral_webhook(body, signature):
            raise HTTPException(
                status_code=401, detail="Invalid webhook signature"
            )

        # Parse webhook data
        webhook_data = await request.json()

        # Convert to chat ingest format
        ingest_data = channel_manager.parse_ringcentral_voice(webhook_data)

        if not ingest_data:
            return {
                "status": "ignored",
                "reason": "Not a relevant voice event",
            }

        # For voice calls, we might want to handle differently
        # For now, just log the call event
        print(
            f"Voice call event: {ingest_data['text']} from {ingest_data['user_id']}"
        )

        # If this is a call that needs IVR response, we could:
        # 1. Generate an AI response
        # 2. Convert to speech using TTS
        # 3. Send back to RingCentral for playback

        return {"status": "logged", "event": ingest_data["text"]}

    except Exception as e:
        print(f"Error processing RingCentral voice webhook: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process voice webhook"
        )


# Meta (Facebook/Instagram) Webhooks
@router.get("/meta")
async def meta_webhook_verify(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_token: str = Query(..., alias="hub.verify_token"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
):
    """Meta webhook verification endpoint"""
    challenge = channel_manager.verify_meta_webhook(
        hub_mode, hub_token, hub_challenge
    )

    if challenge:
        return int(challenge)  # Meta expects an integer response
    else:
        raise HTTPException(status_code=403, detail="Invalid verify token")


@router.post("/meta")
async def meta_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Handle Meta (Facebook/Instagram) webhook"""
    try:
        # Get request body and signature
        body = await request.body()
        signature = request.headers.get("X-Hub-Signature-256", "")

        # Validate signature
        if not channel_manager.validate_meta_webhook(body.decode(), signature):
            raise HTTPException(
                status_code=401, detail="Invalid webhook signature"
            )

        # Parse webhook data
        webhook_data = await request.json()

        # Parse messages from webhook
        messages = channel_manager.parse_meta_webhook(webhook_data)

        processed_messages = []

        for message_data in messages:
            try:
                # Create ingest request
                ingest_request = ChatIngestRequest(
                    channel=message_data["channel"],
                    user_id=message_data["user_id"],
                    thread_id=message_data["thread_id"],
                    text=message_data["text"],
                    metadata=message_data["metadata"],
                )

                # Process message
                response = await chat_service.ingest_chat(ingest_request, db)

                # Send reply via appropriate Meta channel (background task)
                if message_data["metadata"].get("type") == "comment":
                    # Reply to comment
                    background_tasks.add_task(
                        channel_manager.reply_to_comment,
                        message_data["metadata"]["comment_id"],
                        response.reply,
                    )
                else:
                    # Send direct message
                    background_tasks.add_task(
                        channel_manager.send_facebook_message,
                        message_data["metadata"]["sender_id"],
                        response.reply,
                    )

                processed_messages.append(
                    {
                        "message_id": str(response.message_id),
                        "user_id": message_data["user_id"],
                    }
                )

            except Exception as e:
                print(f"Error processing individual message: {e}")
                continue

        return {
            "status": "processed",
            "messages_count": len(processed_messages),
            "messages": processed_messages,
        }

    except Exception as e:
        print(f"Error processing Meta webhook: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to process Meta webhook"
        )


# Webhook status and testing endpoints
@router.get("/status")
async def webhook_status():
    """Get webhook service status"""
    return {
        "status": "healthy",
        "services": {
            "ringcentral": {
                "configured": bool(channel_manager.rc_client_id),
                "endpoints": [
                    "/webhooks/ringcentral/sms",
                    "/webhooks/ringcentral/voice",
                ],
            },
            "meta": {
                "configured": bool(channel_manager.meta_app_id),
                "endpoints": ["/webhooks/meta"],
            },
        },
    }


@router.post("/test/sms")
async def test_sms_send(
    phone_number: str, message: str, current_user=None  # Skip auth for testing
):
    """Test SMS sending functionality"""
    success = await channel_manager.send_sms(phone_number, message)

    if success:
        return {"status": "sent", "phone_number": phone_number}
    else:
        raise HTTPException(status_code=500, detail="Failed to send SMS")


@router.post("/test/facebook")
async def test_facebook_send(
    recipient_id: str, message: str, current_user=None  # Skip auth for testing
):
    """Test Facebook message sending functionality"""
    success = await channel_manager.send_facebook_message(
        recipient_id, message
    )

    if success:
        return {"status": "sent", "recipient_id": recipient_id}
    else:
        raise HTTPException(
            status_code=500, detail="Failed to send Facebook message"
        )
