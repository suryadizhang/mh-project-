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

# MIGRATED: from models.call_recording → db.models.call_recording
from db.models.call_recording import CallRecording, RecordingStatus, RecordingType

# MIGRATED: from models.escalation → db.models.escalation
from db.models.escalation import Escalation, EscalationStatus

# MIGRATED: Imports moved from OLD models to NEW db.models system
from db.models.newsletter import Subscriber

# TODO: Manual migration needed for: SMSDeliveryEvent
# from models import SMSDeliveryEvent
# MIGRATED: Enum imports moved from models.enums to NEW db.models system
# TODO: Manual migration needed for enums: SMSDeliveryStatus
# from models.enums import SMSDeliveryStatus
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
        elif event_type in ["message-store", "sms.delivery_status"]:
            # RingCentral sends SMS delivery status updates as message-store events
            await handle_sms_delivery_status(payload)
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
            if "sms_messages" not in escalation.escalation_metadata:
                escalation.escalation_metadata["sms_messages"] = []

            escalation.escalation_metadata["sms_messages"].append(
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
            if "calls" not in escalation.escalation_metadata:
                escalation.escalation_metadata["calls"] = []

            escalation.escalation_metadata["calls"].append(
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
            calls = escalation.escalation_metadata.get("calls", [])

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


async def handle_sms_delivery_status(payload: dict):
    """
    Handle SMS delivery status events from RingCentral

    Updates SMSDeliveryEvent and Subscriber metrics when:
    - SMS is delivered successfully
    - SMS delivery fails
    - SMS bounces

    RingCentral sends delivery updates as message-store events with:
    - messageStatus: "Delivered", "SendingFailed", "DeliveryFailed"
    - messageId: unique message identifier
    """
    message_id = payload.get("messageId") or payload.get("message_id")
    message_status = payload.get("messageStatus") or payload.get("status")

    if not message_id:
        logger.error("Missing messageId in SMS delivery status webhook")
        return

    if not message_status:
        logger.warning(f"Missing messageStatus for message {message_id}")
        return

    logger.info(f"Processing SMS delivery status: {message_id} -> {message_status}")

    db = next(get_db_session())

    try:
        # Find the delivery event record
        delivery_event = (
            db.query(SMSDeliveryEvent)
            .filter(SMSDeliveryEvent.ringcentral_message_id == message_id)
            .first()
        )

        if not delivery_event:
            logger.warning(
                f"No SMSDeliveryEvent found for RingCentral message_id: {message_id}. "
                f"This may be an SMS not sent through our campaign system."
            )
            return

        # Get the associated campaign event
        from models import CampaignEvent

        campaign_event = (
            db.query(CampaignEvent)
            .filter(CampaignEvent.id == delivery_event.campaign_event_id)
            .first()
        )

        if not campaign_event:
            logger.error(f"CampaignEvent {delivery_event.campaign_event_id} not found")
            return

        subscriber = (
            db.query(Subscriber).filter(Subscriber.id == campaign_event.subscriber_id).first()
        )

        if not subscriber:
            logger.error(f"Subscriber {campaign_event.subscriber_id} not found")
            return

        # Map RingCentral status to our enum
        old_status = delivery_event.status
        new_status = old_status

        if message_status in ["Delivered", "delivered"]:
            new_status = SMSDeliveryStatus.DELIVERED
        elif message_status in ["SendingFailed", "DeliveryFailed", "failed"]:
            new_status = SMSDeliveryStatus.FAILED
        elif message_status in ["Queued", "queued"]:
            new_status = SMSDeliveryStatus.QUEUED
        else:
            logger.warning(f"Unknown message status: {message_status}")
            return

        # Only process if status changed
        if new_status == old_status:
            logger.info(f"Status unchanged for message {message_id}: {old_status}")
            return

        # Update delivery event
        delivery_event.status = new_status
        delivery_event.delivery_timestamp = datetime.utcnow()

        # Extract failure information if failed
        if new_status == SMSDeliveryStatus.FAILED:
            delivery_event.failure_reason = payload.get("failureReason") or payload.get(
                "error_message", "Delivery failed"
            )
            delivery_event.carrier_error_code = payload.get("carrierErrorCode") or payload.get(
                "error_code"
            )

        # Update RingCentral metadata with full payload
        delivery_event.ringcentral_metadata = delivery_event.ringcentral_metadata or {}
        delivery_event.ringcentral_metadata["delivery_update"] = {
            "status": message_status,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
        }

        # Update subscriber metrics based on new status
        if new_status == SMSDeliveryStatus.DELIVERED and old_status != SMSDeliveryStatus.DELIVERED:
            # Increment delivered counter
            subscriber.total_sms_delivered = (subscriber.total_sms_delivered or 0) + 1
            subscriber.last_sms_delivered_date = datetime.utcnow()

            logger.info(
                f"Updated subscriber {subscriber.id}: delivered count = {subscriber.total_sms_delivered}"
            )

        elif new_status == SMSDeliveryStatus.FAILED and old_status == SMSDeliveryStatus.SENT:
            # Increment failed counter (only if transitioning from SENT to FAILED)
            # Note: failed counter was already incremented during send if immediate failure occurred
            subscriber.total_sms_failed = (subscriber.total_sms_failed or 0) + 1

            logger.info(
                f"Updated subscriber {subscriber.id}: failed count = {subscriber.total_sms_failed}"
            )

        # Recalculate engagement score
        subscriber.recalculate_engagement_score()

        db.commit()

        logger.info(
            f"Successfully updated SMS delivery status for message {message_id}: "
            f"{old_status} -> {new_status}"
        )

    except Exception as e:
        logger.error(f"Failed to handle SMS delivery status event: {str(e)}")
        db.rollback()
        raise

    finally:
        db.close()
