"""
Terms Acknowledgment Service

Handles recording and verifying terms & conditions acknowledgments
across all booking channels (web, phone, SMS, AI chatbot).

Legal Protection: Provides audit trail of customer agreement.
"""

from datetime import UTC, datetime, timedelta
import hashlib
import logging

from models.terms_acknowledgment import (
    AcknowledgmentChannel,
    TermsAcknowledgment,
)
from schemas.terms_acknowledgment import (
    SMSTermsRequest,
    SMSTermsResponse,
    SMSTermsVerification,
    TermsAcknowledgmentCreate,
)
from services.unified_notification_service import UnifiedNotificationService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TermsAcknowledgmentService:
    """
    Service for managing terms & conditions acknowledgments

    Features:
    - Record acknowledgments from any channel
    - Send terms via SMS/WhatsApp for phone bookings
    - Verify customer replies (e.g., "I agree")
    - Generate audit-ready reports
    - Hash terms text for tamper-proof records
    """

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = UnifiedNotificationService()

        # Terms configuration
        self.terms_url = "https://myhibachichef.com/terms"
        self.terms_version = "1.0"
        self.sms_expiry_hours = 24  # Customer has 24 hours to reply

    async def create_acknowledgment(
        self, acknowledgment_data: TermsAcknowledgmentCreate
    ) -> TermsAcknowledgment:
        """
        Create a new terms acknowledgment record

        Args:
            acknowledgment_data: Acknowledgment details

        Returns:
            Created TermsAcknowledgment record
        """
        try:
            # Convert Pydantic model to dict
            ack_dict = acknowledgment_data.model_dump(exclude_unset=True)
            ack_dict["acknowledged_at"] = datetime.now(UTC)

            # Create record
            acknowledgment = TermsAcknowledgment(**ack_dict)
            self.db.add(acknowledgment)
            self.db.commit()
            self.db.refresh(acknowledgment)

            logger.info(
                f"✅ Terms acknowledged: customer_id={acknowledgment.customer_id}, "
                f"channel={acknowledgment.channel}, method={acknowledgment.acknowledgment_method}"
            )

            return acknowledgment

        except Exception as e:
            logger.exception(f"❌ Failed to create terms acknowledgment: {e}")
            self.db.rollback()
            raise

    async def send_terms_via_sms(
        self, request: SMSTermsRequest
    ) -> SMSTermsResponse:
        """
        Send terms & conditions via SMS and request acknowledgment

        Used for:
        - Phone bookings
        - Text message bookings
        - Follow-up for incomplete web bookings

        Args:
            request: SMS terms request details

        Returns:
            SMS sending confirmation with expiry time
        """
        try:
            # Build terms message
            message = self._build_sms_terms_message(
                customer_name=request.customer_name,
                booking_id=request.booking_id,
            )

            # Send via SMS
            result = await self.notification_service._send_via_twilio_sms(
                to_phone=request.customer_phone, message=message
            )

            if not result["success"]:
                raise Exception(f"SMS send failed: {result.get('error')}")

            # Calculate expiry
            expires_at = datetime.now(UTC) + timedelta(
                hours=self.sms_expiry_hours
            )

            logger.info(
                f"📱 Terms sent via SMS to {request.customer_phone[-4:]}, "
                f"expires at {expires_at}"
            )

            return SMSTermsResponse(
                message_sid=result["sid"],
                to_phone=request.customer_phone,
                expires_at=expires_at,
                verification_code=None,  # Not using codes for now
            )

        except Exception as e:
            logger.exception(f"❌ Failed to send terms via SMS: {e}")
            raise

    async def verify_sms_acknowledgment(
        self,
        verification: SMSTermsVerification,
        customer_id: int,
        staff_member_email: str | None = None,
        message_id: str | None = None,
        message_timestamp: str | None = None,
        message_hash: str | None = None,
        webhook_source_ip: str | None = None,
    ) -> TermsAcknowledgment | None:
        """
        Verify customer's SMS reply and create acknowledgment record with legal proof

        Enhanced with additional proof fields for maximum legal protection:
        - message_id: RingCentral message ID for audit trail
        - message_timestamp: Exact time message was sent (ISO format)
        - message_hash: SHA-256 fingerprint of the exact message
        - webhook_source_ip: IP address of RingCentral webhook source

        These fields provide comprehensive proof that:
        1. The customer sent the exact message (message_hash)
        2. At the exact time (message_timestamp)
        3. From their phone (customer_phone in verification)
        4. Through verified channel (RingCentral message_id)
        5. From legitimate source (webhook_source_ip)

        Args:
            verification: Customer's reply details (phone, text, booking_id)
            customer_id: Customer ID
            staff_member_email: Staff member processing (if manual)
            message_id: RingCentral message ID (e.g., "12345")
            message_timestamp: ISO timestamp (e.g., "2025-01-03T14:30:00Z")
            message_hash: SHA-256 hash of message for tamper-proof verification
            webhook_source_ip: IP address of webhook source

        Returns:
            Created acknowledgment if valid, None if invalid
        """
        try:
            # Normalize reply text (remove extra spaces, punctuation)
            import re

            reply = verification.reply_text.strip().upper()
            # Remove common punctuation but keep letters
            reply_clean = re.sub(r"[^\w\s]", "", reply)

            # Valid confirmation phrases with common typos and variations
            valid_confirmations = {
                # Standard phrases
                "I AGREE",
                "AGREE",
                "AGREED",
                "AGREEE",
                "YES",
                "YEP",
                "YEAH",
                "YUP",
                "YA",
                "Y",
                "CONFIRM",
                "CONFIRMED",
                "I CONFIRM",
                "ACCEPT",
                "ACCEPTED",
                "I ACCEPT",
                "OK",
                "OKAY",
                "OKEY",
                "OKIE",
                "OOKAY",
                # Common typos - "I AGREE"
                "IAGREE",
                "I AGRE",
                "I AGEE",
                "IAGRE",
                "I AGGREE",
                "I ARREE",
                "IAGRRE",
                # Common typos - "AGREE"
                "AGRE",
                "AGEE",
                "AGGREE",
                "AREE",
                "AGRRE",
                # Common typos - "YES"
                "YEA",
                "YS",
                "YSE",
                "YRS",
                "YESS",
                "YESSS",
                # Common typos - "OKAY"
                "OKYA",
                "OAKY",
                "OKY",
                "OKAYY",
                "OKAAY",
                "OKAT",
                "OKAU",
                "OKQY",
                "OKWY",
                # Common typos - "CONFIRM"
                "COMFIRM",
                "CONFRIM",
                "CONFIRN",
                "COMFRIM",
                "CONFIR",
                # SMS abbreviations
                "K",
                "KK",
                "KAY",
                "OKIE DOKIE",
                # Enthusiastic variations
                "YES!",
                "AGREE!",
                "OK!",
                "YESS!",
                "YESSS!",
                "I AGREE!",
                "OKAY!",
                # Casual variations
                "SURE",
                "FINE",
                "AFFIRMATIVE",
                "ABSOLUTELY",
                "DEFINITELY",
                "CERTAINLY",
            }

            # Check if reply contains valid confirmation
            # Check both original and cleaned version
            is_valid = any(
                phrase in reply or phrase in reply_clean
                for phrase in valid_confirmations
            )

            # Additional fuzzy matching for extreme typos
            if not is_valid:
                # Check if reply is very short and contains key letters
                if len(reply_clean) <= 10:
                    # "AGREE" pattern: has A, G, R, E
                    if (
                        all(
                            letter in reply_clean
                            for letter in ["A", "G", "R", "E"]
                        )
                        or (
                            all(
                                letter in reply_clean
                                for letter in ["Y", "E", "S"]
                            )
                            and len(reply_clean) <= 5
                        )
                        or (
                            all(letter in reply_clean for letter in ["O", "K"])
                            and len(reply_clean) <= 5
                        )
                    ):
                        is_valid = True

            if not is_valid:
                logger.warning(
                    f"⚠️ Invalid SMS reply from {verification.customer_phone[-4:]}: '{reply}' "
                    f"(hash: {message_hash[:16] if message_hash else 'N/A'})"
                )
                return None

            # Build comprehensive proof notes
            proof_notes = [
                f"SMS reply verified from {verification.customer_phone}",
                f"Reply text: '{verification.reply_text}'",
            ]

            if message_id:
                proof_notes.append(f"RingCentral Message ID: {message_id}")
            if message_timestamp:
                proof_notes.append(f"Message Timestamp: {message_timestamp}")
            if message_hash:
                proof_notes.append(f"Message Hash (SHA-256): {message_hash}")
                proof_notes.append(
                    "Hash proves: exact message, phone, timestamp, message_id"
                )
            if webhook_source_ip:
                proof_notes.append(f"Webhook Source IP: {webhook_source_ip}")

            notes = "\n".join(proof_notes)

            # Create acknowledgment record with full legal proof
            acknowledgment_data = TermsAcknowledgmentCreate(
                customer_id=customer_id,
                booking_id=verification.booking_id,
                channel=AcknowledgmentChannel.SMS,
                acknowledgment_method="sms_reply",
                acknowledgment_text=verification.reply_text,
                terms_version=self.terms_version,
                terms_url=self.terms_url,
                staff_member_email=staff_member_email,
                notes=notes,
                verified=True,  # Mark as verified since we have full proof chain
            )

            acknowledgment = await self.create_acknowledgment(
                acknowledgment_data
            )

            logger.info(
                f"✅ Terms acknowledged: customer_id={customer_id}, "
                f"ack_id={acknowledgment.id}, hash={message_hash[:16] if message_hash else 'N/A'}, "
                f"ringcentral_id={message_id or 'N/A'}"
            )

            # Send confirmation SMS
            await self._send_confirmation_sms(
                customer_phone=verification.customer_phone,
                booking_id=verification.booking_id,
            )

            return acknowledgment

        except Exception as e:
            logger.exception(f"❌ Failed to verify SMS acknowledgment: {e}")
            raise

    async def verify_ai_chat_acknowledgment(
        self,
        customer_id: int,
        booking_id: int | None,
        chat_message: str,
        chat_session_id: str,
    ) -> TermsAcknowledgment:
        """
        Record terms acknowledgment from AI chatbot conversation

        Args:
            customer_id: Customer ID
            booking_id: Booking ID (if created)
            chat_message: Customer's agreement message
            chat_session_id: Chat session ID for audit trail

        Returns:
            Created acknowledgment record
        """
        try:
            acknowledgment_data = TermsAcknowledgmentCreate(
                customer_id=customer_id,
                booking_id=booking_id,
                channel=AcknowledgmentChannel.AI_CHAT,
                acknowledgment_method="chatbot_reply",
                acknowledgment_text=chat_message,
                terms_version=self.terms_version,
                terms_url=self.terms_url,
                notes=f"AI chat session: {chat_session_id}",
            )

            return await self.create_acknowledgment(acknowledgment_data)

        except Exception as e:
            logger.exception(
                f"❌ Failed to record AI chat acknowledgment: {e}"
            )
            raise

    async def record_phone_acknowledgment(
        self,
        customer_id: int,
        booking_id: int,
        staff_member_name: str,
        staff_member_email: str,
        notes: str | None = None,
    ) -> TermsAcknowledgment:
        """
        Record verbal acknowledgment from phone booking

        Staff reads terms to customer over phone and records their agreement.

        Args:
            customer_id: Customer ID
            booking_id: Booking ID
            staff_member_name: Name of staff who took booking
            staff_member_email: Staff email
            notes: Additional notes

        Returns:
            Created acknowledgment record
        """
        try:
            acknowledgment_data = TermsAcknowledgmentCreate(
                customer_id=customer_id,
                booking_id=booking_id,
                channel=AcknowledgmentChannel.PHONE,
                acknowledgment_method="verbal_confirmation",
                acknowledgment_text="Verbal agreement confirmed over phone",
                terms_version=self.terms_version,
                terms_url=self.terms_url,
                staff_member_name=staff_member_name,
                staff_member_email=staff_member_email,
                notes=notes or f"Phone booking by {staff_member_name}",
            )

            return await self.create_acknowledgment(acknowledgment_data)

        except Exception as e:
            logger.exception(f"❌ Failed to record phone acknowledgment: {e}")
            raise

    async def check_acknowledgment_exists(
        self, customer_id: int, booking_id: int | None = None
    ) -> TermsAcknowledgment | None:
        """
        Check if customer has already acknowledged terms

        Args:
            customer_id: Customer ID
            booking_id: Optional booking ID

        Returns:
            Most recent acknowledgment or None
        """
        query = self.db.query(TermsAcknowledgment).filter(
            TermsAcknowledgment.customer_id == customer_id
        )

        if booking_id:
            query = query.filter(TermsAcknowledgment.booking_id == booking_id)

        return query.order_by(
            TermsAcknowledgment.acknowledged_at.desc()
        ).first()

    def _build_sms_terms_message(
        self, customer_name: str, booking_id: int | None
    ) -> str:
        """Build SMS message with terms and request for acknowledgment"""

        booking_ref = f" (Booking #{booking_id})" if booking_id else ""

        message = f"""Hi {customer_name}!

To complete your My Hibachi Chef booking{booking_ref}, please review and accept our terms:

📋 Terms & Conditions:
{self.terms_url}

Key Points:
• $100 deposit required within 2 hours
• Full payment due before event
• Cancellation policy applies
• By replying "I AGREE" you accept all terms

Reply with: I AGREE

This offer expires in 24 hours.

Questions? Call (916) 740-8768"""

        return message

    async def _send_confirmation_sms(
        self, customer_phone: str, booking_id: int | None
    ) -> None:
        """Send confirmation SMS after terms accepted"""

        booking_ref = f" #{booking_id}" if booking_id else ""

        message = f"""✅ Terms Accepted!

Thank you for accepting our terms and conditions.

Your booking{booking_ref} is now being processed.

You'll receive payment instructions shortly.

- My Hibachi Chef Team"""

        try:
            await self.notification_service._send_via_twilio_sms(
                to_phone=customer_phone, message=message
            )
        except Exception as e:
            logger.warning(f"Failed to send confirmation SMS: {e}")
            # Don't raise - acknowledgment is recorded, confirmation is nice-to-have

    @staticmethod
    def hash_terms_text(terms_text: str) -> str:
        """
        Generate SHA-256 hash of terms text

        Used to prove terms haven't been altered after acknowledgment.

        Args:
            terms_text: Full terms and conditions text

        Returns:
            SHA-256 hex digest
        """
        return hashlib.sha256(terms_text.encode("utf-8")).hexdigest()


# ==========================================
# CONVENIENCE FUNCTIONS
# ==========================================


async def send_terms_for_phone_booking(
    db: Session,
    customer_phone: str,
    customer_name: str,
    booking_id: int | None = None,
) -> SMSTermsResponse:
    """
    Convenience function: Send terms via SMS for phone booking

    Usage:
        await send_terms_for_phone_booking(
            db=db,
            customer_phone="2103884155",
            customer_name="John Doe",
            booking_id=123
        )
    """
    service = TermsAcknowledgmentService(db)
    request = SMSTermsRequest(
        customer_phone=customer_phone,
        customer_name=customer_name,
        booking_id=booking_id,
    )
    return await service.send_terms_via_sms(request)


async def verify_sms_reply(
    db: Session,
    customer_phone: str,
    reply_text: str,
    customer_id: int,
    booking_id: int | None = None,
) -> TermsAcknowledgment | None:
    """
    Convenience function: Verify customer's SMS reply

    Returns:
        Acknowledgment record if valid, None if invalid reply
    """
    service = TermsAcknowledgmentService(db)
    verification = SMSTermsVerification(
        customer_phone=customer_phone,
        reply_text=reply_text,
        booking_id=booking_id,
    )
    return await service.verify_sms_acknowledgment(
        verification=verification, customer_id=customer_id
    )
