"""
Twilio Webhook Endpoints
Handle WhatsApp and SMS delivery status callbacks
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Depends

from api.deps_enhanced import get_database_session

# MIGRATED: from models.escalation → db.models.escalation
from db.models.escalation import Escalation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/twilio", tags=["webhooks"])


@router.post("/status")
async def twilio_message_status(
    request: Request,
    db: Session = Depends(get_database_session),
):
    """
    Twilio message status callback webhook

    Receives delivery status updates for WhatsApp and SMS messages.
    Updates escalation notification status for read receipts.

    Status values:
    - queued: Message queued for delivery
    - sending: Message is being sent
    - sent: Message sent to carrier
    - delivered: Message delivered to recipient
    - read: Message read by recipient (WhatsApp only)
    - failed: Message delivery failed
    - undelivered: Message could not be delivered

    Configure in Twilio Console:
    Messaging → Settings → WhatsApp sandbox settings
    Status callback URL: https://yourdomain.com/api/v1/webhooks/twilio/status
    """
    try:
        # Parse Twilio form data
        form_data = await request.form()

        message_sid = form_data.get("MessageSid")
        message_status = form_data.get("MessageStatus")
        to_number = form_data.get("To")
        from_number = form_data.get("From")
        error_code = form_data.get("ErrorCode")
        error_message = form_data.get("ErrorMessage")

        logger.info(
            f"Twilio status callback: SID={message_sid}, "
            f"Status={message_status}, To={to_number}"
        )

        if not message_sid or not message_status:
            logger.warning("Missing MessageSid or MessageStatus in webhook")
            return {"status": "ignored", "reason": "missing_fields"}

        # Find escalation with this message SID
        escalation = (
            db.query(Escalation).filter(Escalation.admin_notification_sid == message_sid).first()
        )

        if not escalation:
            logger.info(f"No escalation found for message SID {message_sid}")
            return {"status": "ignored", "reason": "escalation_not_found"}

        # Update notification status
        escalation.admin_notification_status = message_status

        # Record error if failed
        if message_status in ["failed", "undelivered"] and error_message:
            escalation.error_message = f"Twilio error {error_code}: {error_message}"
            escalation.retry_count = str(int(escalation.retry_count or 0) + 1)

        escalation.updated_at = datetime.utcnow()
        db.commit()

        logger.info(f"Updated escalation {escalation.id} notification status to {message_status}")

        return {
            "status": "success",
            "escalation_id": str(escalation.id),
            "message_status": message_status,
        }

    except Exception as e:
        logger.error(f"Failed to process Twilio webhook: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process webhook",
        )


@router.post("/incoming")
async def twilio_incoming_message(
    request: Request,
    db: Session = Depends(get_database_session),
):
    """
    Twilio incoming message webhook

    Receives incoming WhatsApp/SMS messages from customers.
    Can be used to track customer responses to escalations.

    Configure in Twilio Console:
    Messaging → Settings → WhatsApp sandbox settings
    When a message comes in: https://yourdomain.com/api/v1/webhooks/twilio/incoming
    """
    try:
        # Parse Twilio form data
        form_data = await request.form()

        from_number = form_data.get("From")  # Customer number
        to_number = form_data.get("To")  # Our Twilio number
        body = form_data.get("Body")  # Message text
        message_sid = form_data.get("MessageSid")

        logger.info(f"Twilio incoming message: From={from_number}, Body={body[:100]}")

        # Clean phone number (remove whatsapp: prefix if present)
        customer_phone = from_number.replace("whatsapp:", "") if from_number else None

        if not customer_phone or not body:
            logger.warning("Missing From or Body in incoming message")
            return {"status": "ignored", "reason": "missing_fields"}

        # Find active escalation for this customer
        escalation = (
            db.query(Escalation)
            .filter(
                Escalation.customer_phone == customer_phone,
                Escalation.status.in_(["pending", "assigned", "in_progress", "waiting_customer"]),
            )
            .order_by(Escalation.created_at.desc())
            .first()
        )

        if escalation:
            # Update last contact time
            escalation.last_contact_at = datetime.utcnow()

            # If waiting for customer, move to in_progress
            if escalation.status == "waiting_customer":
                escalation.status = "in_progress"

            # Store message in metadata
            if not escalation.escalation_metadata:
                escalation.escalation_metadata = {}

            if "customer_messages" not in escalation.escalation_metadata:
                escalation.escalation_metadata["customer_messages"] = []

            escalation.escalation_metadata["customer_messages"].append(
                {
                    "message_sid": message_sid,
                    "body": body,
                    "timestamp": datetime.utcnow().isoformat(),
                    "channel": "whatsapp" if "whatsapp:" in from_number else "sms",
                }
            )

            # Mark as modified to trigger JSONB update
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(escalation, "escalation_metadata")

            db.commit()

            logger.info(f"Recorded incoming message for escalation {escalation.id}")

        # Return empty response (Twilio doesn't need reply)
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Failed to process incoming message: {str(e)}", exc_info=True)
        # Return success to Twilio even on error (don't want retries)
        return {"status": "error", "message": str(e)}
