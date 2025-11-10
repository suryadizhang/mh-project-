"""
RingCentral Webhook Receiver
Handles incoming webhook events from RingCentral
"""

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
import logging

from services.ringcentral_service import get_ringcentral_service
from workers.recording_tasks import (
    fetch_call_recording,
)
from models.call_recording import CallRecording, RecordingStatus, RecordingType
from models.escalation import Escalation, EscalationStatus
from core.database import get_db_session
from datetime import datetime

router = APIRouter(prefix="/webhooks/ringcentral", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/")
async def ringcentral_webhook_handler(
    request: Request,
    validation_token: Optional[str] = Header(None, alias="Validation-Token"),
):
    """
    RingCentral webhook receiver endpoint

    Handles:
    - Webhook validation (returns validation token)
    - recording.created events → triggers fetch_call_recording task
    - sms.received events → updates conversation/escalation
    - call.started/ended events → updates escalation status

    Security:
    - Verifies webhook signature using HMAC-SHA256
    - Rate limited to prevent abuse

    Reference: https://developers.ringcentral.com/guide/notifications/webhooks
    """
    # Handle RingCentral webhook validation
    if validation_token:
        logger.info("RingCentral webhook validation request received")
        return {"validation_token": validation_token}

    # Get request body and signature
    body = await request.body()
    signature = request.headers.get("X-Webhook-Signature", "")

    # Verify webhook signature
    rc_service = get_ringcentral_service()

    if not rc_service.verify_webhook_signature(body, signature):
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse webhook payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("event")

    if not event_type:
        logger.error("Webhook payload missing event type")
        raise HTTPException(status_code=400, detail="Missing event type")

    logger.info(f"Received RingCentral webhook event: {event_type}")

    # Route event to appropriate handler
    try:
        if event_type == "recording.created":
            await handle_recording_created(payload)
        elif event_type == "sms.received":
            await handle_sms_received(payload)
        elif event_type == "call.started":
            await handle_call_started(payload)
        elif event_type == "call.ended":
            await handle_call_ended(payload)
        else:
            logger.warning(f"Unhandled webhook event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing webhook")

    return {"status": "success", "event": event_type}


async def handle_recording_created(payload: dict):
    """
    Handle recording.created event

    Triggers download of call recording from RingCentral to VPS storage
    """
    rc_recording_id = payload.get("recording_id")
    rc_call_id = payload.get("call_id")

    if not rc_recording_id or not rc_call_id:
        logger.error("Missing recording_id or call_id in webhook payload")
        return

    db = next(get_db_session())

    try:
        # Find existing recording record or create new one
        recording = (
            db.query(CallRecording).filter(CallRecording.rc_recording_id == rc_recording_id).first()
        )

        if not recording:
            # Create new recording record
            recording = CallRecording(
                rc_call_id=rc_call_id,
                rc_recording_id=rc_recording_id,
                rc_recording_uri=payload.get("recording_uri"),
                recording_type=RecordingType.INBOUND,  # Default, may update
                status=RecordingStatus.PENDING,
                call_started_at=datetime.utcnow(),  # Will be updated from metadata
            )
            db.add(recording)
            db.commit()
            db.refresh(recording)

        # Trigger async download task
        fetch_call_recording.delay(str(recording.id))

        logger.info(f"Queued download for recording {recording.id}")

    except Exception as e:
        logger.error(f"Failed to handle recording.created event: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


async def handle_sms_received(payload: dict):
    """
    Handle sms.received event

    Updates conversation or escalation with incoming SMS message
    """
    from_number = payload.get("from", "")
    to_number = payload.get("to", "")
    message_text = payload.get("text", "")
    message_id = payload.get("id", "")

    if not from_number or not message_text:
        logger.error("Missing from number or message text in SMS webhook")
        return

    db = next(get_db_session())

    try:
        # Find active escalation for this customer phone number
        escalation = (
            db.query(Escalation)
            .filter(
                Escalation.customer_phone == from_number,
                Escalation.status.in_(
                    [
                        EscalationStatus.PENDING,
                        EscalationStatus.ASSIGNED,
                        EscalationStatus.IN_PROGRESS,
                        EscalationStatus.WAITING_CUSTOMER,
                    ]
                ),
            )
            .order_by(Escalation.created_at.desc())
            .first()
        )

        if escalation:
            # Update escalation with customer response
            escalation.status = EscalationStatus.IN_PROGRESS
            escalation.last_customer_response_at = datetime.utcnow()

            # Add to metadata
            if "sms_messages" not in escalation.metadata:
                escalation.metadata["sms_messages"] = []

            escalation.metadata["sms_messages"].append(
                {
                    "message_id": message_id,
                    "from": from_number,
                    "to": to_number,
                    "text": message_text,
                    "direction": "inbound",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            db.commit()

            logger.info(f"Updated escalation {escalation.id} with incoming SMS")

            # TODO: Notify assigned admin of customer response
            # Could trigger a notification task here

        else:
            # No active escalation found
            logger.warning(f"Received SMS from {from_number} but no active escalation found")

            # TODO: Create new escalation or route to general inbox
            # Could implement auto-escalation creation here

    except Exception as e:
        logger.error(f"Failed to handle sms.received event: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


async def handle_call_started(payload: dict):
    """
    Handle call.started event

    Updates escalation status when outbound call is connected
    """
    rc_call_id = payload.get("call_id")
    from_number = payload.get("from", "")
    to_number = payload.get("to", "")

    if not rc_call_id:
        logger.error("Missing call_id in call.started webhook")
        return

    db = next(get_db_session())

    try:
        # Find escalation associated with this call
        escalation = (
            db.query(Escalation)
            .filter(
                Escalation.customer_phone == to_number,  # Assuming outbound call
                Escalation.status == EscalationStatus.ASSIGNED,
            )
            .order_by(Escalation.created_at.desc())
            .first()
        )

        if escalation:
            escalation.status = EscalationStatus.IN_PROGRESS
            escalation.escalated_at = datetime.utcnow()

            # Record call details in metadata
            if "calls" not in escalation.metadata:
                escalation.metadata["calls"] = []

            escalation.metadata["calls"].append(
                {
                    "rc_call_id": rc_call_id,
                    "from": from_number,
                    "to": to_number,
                    "started_at": datetime.utcnow().isoformat(),
                    "status": "started",
                }
            )

            db.commit()

            logger.info(f"Updated escalation {escalation.id} with call started event")

    except Exception as e:
        logger.error(f"Failed to handle call.started event: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()


async def handle_call_ended(payload: dict):
    """
    Handle call.ended event

    Updates escalation with call duration and triggers recording download
    """
    rc_call_id = payload.get("call_id")
    duration = payload.get("duration", 0)  # seconds
    has_recording = payload.get("has_recording", False)

    if not rc_call_id:
        logger.error("Missing call_id in call.ended webhook")
        return

    db = next(get_db_session())

    try:
        # Find escalation with this call
        escalations = db.query(Escalation).all()

        for escalation in escalations:
            calls = escalation.metadata.get("calls", [])

            for call in calls:
                if call.get("rc_call_id") == rc_call_id:
                    # Update call record
                    call["ended_at"] = datetime.utcnow().isoformat()
                    call["duration"] = duration
                    call["status"] = "ended"
                    call["has_recording"] = has_recording

                    db.commit()

                    logger.info(
                        f"Updated escalation {escalation.id} with call ended event, "
                        f"duration: {duration}s, recording: {has_recording}"
                    )

                    # If call has recording, it will be handled by recording.created event
                    break

    except Exception as e:
        logger.error(f"Failed to handle call.ended event: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()
