"""
SMS/WhatsApp Webhook Handler for Terms Acknowledgments

Handles incoming SMS/WhatsApp messages from customers
replying to terms & conditions requests.

RingCentral webhook: POST /api/v1/webhooks/sms/terms-reply

Legal Protection Features:
- Records exact message text and timestamp
- Validates message signature from RingCentral
- Captures sender phone number
- Stores RingCentral message ID for audit trail
- Creates immutable acknowledgment record
"""

import hashlib
import hmac
import logging
from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from core.database import get_db
from core.config import settings
from services.terms_acknowledgment_service import TermsAcknowledgmentService
from services.ai_booking_assistant_service import process_sms_booking_message
from services.unified_notification_service import UnifiedNotificationService
from db.models.core import Customer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks/sms", tags=["webhooks"])


def validate_ringcentral_signature(
    request_body: bytes, signature_header: str | None, validation_token: str
) -> bool:
    """
    Validate that request actually came from RingCentral

    Security: Prevents fake webhook calls

    RingCentral sends X-Glip-Signature header with HMAC-SHA256 signature
    of the request body using the validation token as the key.

    Args:
        request_body: Raw request body bytes
        signature_header: X-Glip-Signature header value
        validation_token: RingCentral webhook validation token

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        if not signature_header or not validation_token:
            logger.warning("Missing signature header or validation token")
            return False

        # Calculate expected signature
        expected_signature = hmac.new(
            validation_token.encode("utf-8"), request_body, hashlib.sha256
        ).hexdigest()

        # Compare signatures (constant-time comparison)
        return hmac.compare_digest(expected_signature, signature_header)

    except Exception as e:
        logger.error(f"RingCentral signature validation error: {e}")
        return False


def calculate_message_hash(
    phone_number: str, message_body: str, timestamp: str, message_id: str
) -> str:
    """
    Calculate SHA-256 hash of message for legal proof

    Creates immutable fingerprint of the acknowledgment that can be
    verified later to prove the exact message was received.

    Args:
        phone_number: Customer's phone number
        message_body: Exact message text
        timestamp: ISO timestamp when message received
        message_id: RingCentral message ID

    Returns:
        SHA-256 hex digest
    """
    # Combine all fields into canonical format
    canonical_string = f"{phone_number}|{message_body}|{timestamp}|{message_id}"

    # Calculate hash
    return hashlib.sha256(canonical_string.encode("utf-8")).hexdigest()


@router.post("/terms-reply")
async def handle_terms_reply(
    request: Request,
    db: Session = Depends(get_db),
    x_glip_signature: str | None = Header(None, alias="X-Glip-Signature"),
) -> dict[str, Any]:
    """
    Handle customer's SMS reply to terms & conditions request

    RingCentral webhook sends POST when customer replies to our SMS.

    Expected customer replies:
    - "I AGREE"
    - "AGREE"
    - "YES"
    - "CONFIRM"
    - "I CONFIRM"

    Legal Protection Features:
    - Validates RingCentral signature (prevents spoofing)
    - Records exact message text (verbatim proof)
    - Captures message timestamp (temporal proof)
    - Stores RingCentral message ID (audit trail)
    - Calculates message hash (tamper-proof fingerprint)
    - Records IP address of webhook source (origin proof)

    Flow:
    1. Validate request signature from RingCentral (security)
    2. Parse RingCentral webhook payload
    3. Extract phone number, message, timestamp, message ID
    4. Calculate message hash for legal proof
    5. Find customer by phone
    6. Verify reply contains agreement phrase
    7. Create immutable acknowledgment record with all proof
    8. Send confirmation SMS
    9. Return success response
    """
    try:
        # Read raw request body for signature validation
        request_body = await request.body()

        # Validate RingCentral signature (security - prevents fake webhooks)
        if not settings.SKIP_WEBHOOK_VALIDATION:
            validation_token = settings.RINGCENTRAL_WEBHOOK_VALIDATION_TOKEN
            if not validate_ringcentral_signature(request_body, x_glip_signature, validation_token):
                logger.warning("⚠️ Invalid RingCentral signature")
                raise HTTPException(status_code=403, detail="Invalid webhook signature")

        # Parse RingCentral webhook JSON payload
        payload = await request.json()

        # Extract message details from RingCentral format
        # RingCentral webhook structure:
        # {
        #   "event": "message.received",
        #   "timestamp": "2025-01-03T14:30:00Z",
        #   "body": {
        #     "id": "12345",
        #     "from": { "phoneNumber": "+12103884155" },
        #     "text": "I agree",
        #     "creationTime": "2025-01-03T14:30:00Z"
        #   }
        # }

        message_body = payload.get("body", {})
        from_data = message_body.get("from", {})
        phone_number = from_data.get("phoneNumber", "")
        message_text = message_body.get("text", "")
        message_id = message_body.get("id", "")
        message_timestamp = message_body.get("creationTime", datetime.now(timezone.utc).isoformat())

        # Get webhook source IP for audit trail
        webhook_source_ip = request.client.host if request.client else None

        # Normalize phone number to 10 digits
        phone_normalized = "".join(c for c in phone_number if c.isdigit())[-10:]

        # Calculate message hash for legal proof (tamper-proof fingerprint)
        message_hash = calculate_message_hash(
            phone_number=phone_normalized,
            message_body=message_text,
            timestamp=message_timestamp,
            message_id=message_id,
        )

        logger.info(
            f"📱 SMS received from {phone_normalized[-4:]}: '{message_text[:50]}...' "
            f"(RingCentral ID: {message_id}, Hash: {message_hash[:16]}...)"
        )

        # Find customer by phone
        customer = db.query(Customer).filter(Customer.phone.like(f"%{phone_normalized}%")).first()

        if not customer:
            logger.warning(f"⚠️ Customer not found for phone {phone_normalized[-4:]}")

            # Log attempt for security audit
            logger.warning(
                f"⚠️ Terms reply from unknown number: "
                f"phone={phone_normalized}, message='{message_text}', "
                f"hash={message_hash}"
            )

            # Send helpful response
            return {
                "message": "Thank you for your message. We couldn't find your booking. "
                "Please call us at (916) 740-8768 for assistance.",
                "status": "customer_not_found",
                "message_hash": message_hash,  # Include hash for audit trail
            }

        # Verify terms acknowledgment with enhanced proof
        service = TermsAcknowledgmentService(db)

        from schemas.terms_acknowledgment import SMSTermsVerification

        verification = SMSTermsVerification(
            customer_phone=phone_normalized,
            reply_text=message_text,
            booking_id=None,  # Will be associated with most recent pending booking
        )

        # Create acknowledgment with full legal proof
        acknowledgment = await service.verify_sms_acknowledgment(
            verification=verification,
            customer_id=customer.id,
            message_id=message_id,
            message_timestamp=message_timestamp,
            message_hash=message_hash,
            webhook_source_ip=webhook_source_ip,
        )

        if acknowledgment:
            logger.info(
                f"✅ Terms acknowledged via SMS: "
                f"customer_id={customer.id}, "
                f"ack_id={acknowledgment.id}, "
                f"hash={message_hash[:16]}..., "
                f"ringcentral_id={message_id}"
            )

            # Return comprehensive proof record
            return {
                "message": "Terms accepted successfully",
                "status": "acknowledged",
                "acknowledgment_id": acknowledgment.id,
                "proof": {
                    "message_hash": message_hash,
                    "ringcentral_message_id": message_id,
                    "timestamp": message_timestamp,
                    "phone_number": phone_normalized,
                    "exact_text": message_text,
                    "webhook_verified": True,
                },
            }
        else:
            logger.warning(
                f"⚠️ Invalid terms reply from customer {customer.id}: '{message_text}' "
                f"(hash={message_hash[:16]}...)"
            )

            # Send helpful response with examples
            return {
                "message": "To accept terms, please reply with one of these: "
                "'I AGREE', 'YES', 'AGREE', 'CONFIRM', or 'OK'. "
                "Call us at (916) 740-8768 if you have questions.",
                "status": "invalid_reply",
                "message_hash": message_hash,  # Track even invalid attempts
                "suggestion": "Try replying: I AGREE",
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Error handling terms reply: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/incoming")
async def handle_incoming_sms(
    request: Request,
    db: Session = Depends(get_db),
    x_glip_signature: str | None = Header(None, alias="X-Glip-Signature"),
) -> dict[str, Any]:
    """
    General incoming SMS handler (RingCentral)

    Routes messages to appropriate handlers based on content:
    - Terms agreement keywords → terms-reply handler
    - Booking questions → AI chatbot
    - Payment confirmations → payment system

    Security: Validates RingCentral webhook signature
    """
    try:
        # Read raw body for signature validation
        request_body = await request.body()

        # Validate RingCentral signature
        if not settings.SKIP_WEBHOOK_VALIDATION:
            validation_token = settings.RINGCENTRAL_WEBHOOK_VALIDATION_TOKEN
            if not validate_ringcentral_signature(request_body, x_glip_signature, validation_token):
                logger.warning("⚠️ Invalid RingCentral signature on incoming SMS")
                raise HTTPException(status_code=403, detail="Invalid webhook signature")

        # Parse RingCentral payload
        payload = await request.json()
        message_body = payload.get("body", {})
        from_data = message_body.get("from", {})
        phone_number = from_data.get("phoneNumber", "")
        message_text = message_body.get("text", "")

        # Normalize phone
        phone_normalized = "".join(c for c in phone_number if c.isdigit())[-10:]

        # Check if this is a terms reply
        import re

        message_upper = message_text.strip().upper()
        message_clean = re.sub(r"[^\w\s]", "", message_upper)

        # Expanded keywords to catch common variations and typos
        terms_keywords = [
            "AGREE",
            "AGRE",
            "AGEE",
            "IAGREE",
            "I AGREE",
            "CONFIRM",
            "CONFIR",
            "COMFIRM",
            "ACCEPT",
            "ACCEP",
            "YES",
            "YEP",
            "YEAH",
            "YUP",
            "YA",
            "OK",
            "OKAY",
            "OKEY",
            "KAY",
        ]

        if any(keyword in message_upper or keyword in message_clean for keyword in terms_keywords):
            # Route to terms handler
            return await handle_terms_reply(
                request=request, db=db, x_glip_signature=x_glip_signature
            )

        # Check if this is a booking-related message
        booking_keywords = [
            "BOOK",
            "BOOKING",
            "RESERVATION",
            "RESERVE",
            "PRICE",
            "COST",
            "HOW MUCH",
            "QUOTE",
            "AVAILABLE",
            "AVAILABILITY",
            "PARTY",
            "EVENT",
            "CELEBRATION",
            "HIBACHI",
            "CHEF",
        ]

        is_booking_related = any(keyword in message_upper for keyword in booking_keywords)

        if is_booking_related:
            try:
                logger.info(f"🤖 AI processing booking message from {phone_normalized[-4:]}")

                # Process with AI booking assistant
                result = await process_sms_booking_message(
                    db=db,
                    from_number=phone_number,
                    message_text=message_text,
                    conversation_history=[],  # TODO: Load from conversation_threads table
                )

                # Handle next actions
                if result["next_action"] == "send_terms":
                    # Send terms & conditions SMS
                    from services.terms_acknowledgment_service import send_terms_for_phone_booking

                    customer = result.get("customer")
                    if customer and customer.phone:
                        await send_terms_for_phone_booking(
                            db=db,
                            customer_phone=customer.phone,
                            customer_name=f"{customer.first_name} {customer.last_name}",
                            booking_id=None,
                        )

                elif result["next_action"] == "create_booking":
                    # Create the booking
                    from services.ai_booking_assistant_service import AIBookingAssistant

                    assistant = AIBookingAssistant(db)
                    booking = await assistant.create_booking_from_data(
                        booking_data=result["booking_data"],
                        customer=result["customer"],
                        channel="sms",
                    )

                    if booking:
                        logger.info(f"✅ AI created booking {booking.id}")
                    else:
                        logger.error("❌ AI failed to create booking")
                        result["response_text"] = (
                            "I had trouble creating your booking. Let me connect you with our team. 🤝"
                        )
                        result["requires_human"] = True

                elif result["requires_human"]:
                    # Escalate to staff
                    logger.info("👥 Escalating SMS conversation to human staff")
                    # TODO: Send notification to staff

                # Send AI response via SMS
                notification_service = UnifiedNotificationService(db)
                await notification_service.send_sms(
                    phone_number=phone_number, message=result["response_text"]
                )

                return {
                    "message": "AI response sent",
                    "status": "processed_by_ai",
                    "intent": result["intent"],
                    "stage": result["stage"],
                }

            except Exception as e:
                logger.error(f"❌ AI booking assistant error: {e}", exc_info=True)
                # Fall through to generic handler

        # Generic response for non-booking messages
        logger.info(f"📱 General SMS from {phone_normalized[-4:]}: '{message_text[:50]}...'")

        return {"message": "Message received. Our team will respond shortly.", "status": "received"}

    except Exception as e:
        logger.exception(f"❌ Error handling incoming SMS: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
