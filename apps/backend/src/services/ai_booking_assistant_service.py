"""
AI Booking Assistant Service
Handles booking-related conversations across all channels (phone, SMS, WhatsApp, web chat)
"""

from enum import Enum
from typing import Optional, Dict, Any, List
import json
import logging

from sqlalchemy.orm import Session
from openai import OpenAI

from core.config import get_settings
from config.ai_booking_config import (
    PRICING,
    MENU_ITEMS,
    POLICIES,
    SERVICE_AREAS,
    RESPONSE_TEMPLATES,
    INTENT_CLASSIFIER_PROMPT,
    INFO_EXTRACTOR_PROMPT,
    get_response_generator_prompt,
)
from models.booking import Booking
from models.customer import Customer
from repositories.customer_repository import CustomerRepository
from services.booking_service import BookingService
from services.unified_notification_service import UnifiedNotificationService

logger = logging.getLogger(__name__)


class BookingIntent(str, Enum):
    """Customer intent during booking conversation"""

    INQUIRY = "inquiry"  # Just asking questions
    BOOKING = "booking"  # Wants to make a booking
    MODIFICATION = "modification"  # Change existing booking
    CANCELLATION = "cancellation"  # Cancel booking
    OBJECTION = "objection"  # Has concerns/questions
    ESCALATION = "escalation"  # Needs human help


class BookingStage(str, Enum):
    """Current stage in booking process"""

    INITIAL = "initial"  # Just started
    COLLECTING_INFO = "collecting_info"  # Gathering details
    CONFIRMING_INFO = "confirming_info"  # Reviewing with customer
    SENDING_TERMS = "sending_terms"  # Sent terms, awaiting confirmation
    TERMS_CONFIRMED = "terms_confirmed"  # Customer agreed to terms
    CREATING_BOOKING = "creating_booking"  # Submitting to system
    BOOKING_COMPLETE = "booking_complete"  # Success!
    ESCALATED = "escalated"  # Handed off to human


class AIBookingAssistant:
    """
    AI-powered booking assistant that handles conversations
    across phone, SMS, WhatsApp, and web chat.
    """

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.openai_client = OpenAI(api_key=self.settings.openai_api_key)
        self.booking_service = BookingService(db)
        self.customer_repo = CustomerRepository(db)
        self.notification_service = UnifiedNotificationService(db)

    async def process_message(
        self,
        message: str,
        customer_phone: Optional[str] = None,
        customer_id: Optional[int] = None,
        channel: str = "sms",  # 'phone', 'sms', 'whatsapp', 'web_chat'
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Process a customer message and determine response.

        Args:
            message: Customer's message text
            customer_phone: Customer's phone number (optional if customer_id provided)
            customer_id: Customer ID (optional if customer_phone provided)
            channel: Communication channel
            conversation_history: Previous messages in conversation

        Returns:
            Dict with:
                - response_text: What to say to customer
                - intent: Detected customer intent
                - stage: Current booking stage
                - next_action: What system should do next
                - booking_data: Extracted booking information
                - requires_human: Whether escalation is needed
        """
        try:
            # Get or create customer
            if customer_id:
                customer = self.customer_repo.get_by_id(customer_id)
            elif customer_phone:
                # Try to find existing customer by phone
                customer = self.customer_repo.find_by_phone(customer_phone)
                if not customer:
                    # Create new customer - use placeholder email
                    phone_digits = "".join(filter(str.isdigit, customer_phone))[-4:]
                    placeholder_email = f"customer_{phone_digits}@mhhhibachi.com"

                    customer = self.customer_repo.create_customer(
                        first_name="Guest",
                        last_name="Customer",
                        email=placeholder_email,
                        phone=customer_phone,
                        sms_notifications=True,  # They're texting us, so yes
                    )
            else:
                logger.error("Neither customer_phone nor customer_id provided")
                return self._error_response("Unable to identify customer")

            if not customer:
                return self._error_response("Customer not found")

            # Initialize conversation state
            if conversation_history is None:
                conversation_history = []

            # Classify intent
            intent = await self._classify_intent(message, conversation_history)

            # Extract booking information
            booking_data = await self._extract_booking_info(message, conversation_history)

            # Determine current stage
            stage = await self._determine_stage(intent, booking_data, conversation_history)

            # Generate appropriate response
            response = await self._generate_response(
                intent=intent,
                stage=stage,
                booking_data=booking_data,
                customer=customer,
                channel=channel,
                message=message,
            )

            return {
                "response_text": response["text"],
                "intent": intent.value,
                "stage": stage.value,
                "next_action": response["next_action"],
                "booking_data": booking_data,
                "requires_human": response.get("requires_human", False),
                "customer": customer,
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return self._error_response(f"An error occurred: {str(e)}")

    async def _classify_intent(self, message: str, history: List[Dict[str, str]]) -> BookingIntent:
        """Use AI to classify customer intent"""

        system_prompt = INTENT_CLASSIFIER_PROMPT

        messages = [{"role": "system", "content": system_prompt}]

        # Add recent history for context (last 3 messages)
        if history:
            messages.extend(history[-3:])

        messages.append({"role": "user", "content": message})

        try:
            response = self.openai_client.chat.completions.create(
                model=self.settings.openai_model or "gpt-4",
                messages=messages,
                temperature=0.3,
                max_tokens=10,
            )

            intent_str = response.choices[0].message.content.strip().lower()

            try:
                return BookingIntent(intent_str)
            except ValueError:
                logger.warning(f"Unknown intent: {intent_str}, defaulting to INQUIRY")
                return BookingIntent.INQUIRY

        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return BookingIntent.INQUIRY  # Safe default

    async def _extract_booking_info(
        self, message: str, history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Extract structured booking information from conversation"""

        system_prompt = INFO_EXTRACTOR_PROMPT

        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history for context
        if history:
            messages.extend(history[-5:])  # Last 5 messages

        messages.append({"role": "user", "content": message})

        try:
            response = self.openai_client.chat.completions.create(
                model=self.settings.openai_model or "gpt-4",
                messages=messages,
                temperature=0.1,
                max_tokens=300,
            )

            extracted = json.loads(response.choices[0].message.content)
            return extracted

        except Exception as e:
            logger.error(f"Error extracting booking info: {e}")
            return {}

    async def _determine_stage(
        self, intent: BookingIntent, booking_data: Dict[str, Any], history: List[Dict[str, str]]
    ) -> BookingStage:
        """Determine current stage in booking process"""

        # Check if terms were sent and confirmed
        if len(history) > 0:
            last_messages = " ".join([m.get("content", "") for m in history[-3:]])
            lower_messages = last_messages.lower()

            if "terms and conditions" in lower_messages or "terms & conditions" in lower_messages:
                # Check for agreement
                agree_words = ["agree", "yes", "confirm", "accept", "ok", "sure", "yep", "yeah"]
                if any(word in lower_messages for word in agree_words):
                    return BookingStage.TERMS_CONFIRMED
                return BookingStage.SENDING_TERMS

        # Check if we have complete booking info
        required_fields = ["event_date", "event_time", "guest_count", "location_address"]
        if all(booking_data.get(field) for field in required_fields):
            return BookingStage.CONFIRMING_INFO

        # Check if we're actively collecting info
        if intent == BookingIntent.BOOKING and any(booking_data.values()):
            return BookingStage.COLLECTING_INFO

        # Check if escalation needed
        if intent == BookingIntent.ESCALATION:
            return BookingStage.ESCALATED

        return BookingStage.INITIAL

    async def _generate_response(
        self,
        intent: BookingIntent,
        stage: BookingStage,
        booking_data: Dict[str, Any],
        customer: Customer,
        channel: str,
        message: str,
    ) -> Dict[str, Any]:
        """Generate appropriate response based on context"""

        # Handle escalation
        if stage == BookingStage.ESCALATED:
            return {
                "text": "I understand you'd like to speak with someone. I'm connecting you with our team now. Someone will be with you shortly! 👋",
                "next_action": "escalate_to_human",
                "requires_human": True,
            }

        # Handle different stages
        if stage == BookingStage.INITIAL:
            if intent == BookingIntent.INQUIRY:
                return await self._handle_inquiry(message, customer)
            else:
                return {
                    "text": self._get_greeting_message(),
                    "next_action": "await_customer_response",
                }

        elif stage == BookingStage.COLLECTING_INFO:
            missing_fields = self._get_missing_fields(booking_data)
            return {
                "text": self._get_info_collection_message(missing_fields),
                "next_action": "collect_more_info",
            }

        elif stage == BookingStage.CONFIRMING_INFO:
            confirmation_text = self._format_booking_confirmation(booking_data)
            return {"text": confirmation_text, "next_action": "send_terms"}

        elif stage == BookingStage.SENDING_TERMS:
            return {
                "text": "Please reply 'I agree' to confirm you accept our terms and conditions. 📋",
                "next_action": "await_terms_confirmation",
            }

        elif stage == BookingStage.TERMS_CONFIRMED:
            return {
                "text": "Thank you! Creating your booking now... ⏳",
                "next_action": "create_booking",
            }

        # Default response
        return {
            "text": "How can I help you with your hibachi booking? 🍱",
            "next_action": "await_customer_response",
        }

    async def _handle_inquiry(self, message: str, customer: Customer) -> Dict[str, Any]:
        """Handle general inquiries about pricing, packages, availability"""

        customer_name = (
            f"{customer.first_name}" if customer and customer.first_name != "Guest" else None
        )
        system_prompt = get_response_generator_prompt(customer_name)

        # Add specific context for inquiry handling
        system_prompt += f"""

**Customer is asking a question. Provide accurate information:**

**Pricing:**
- Adults (13+): ${PRICING['adult_base']}/person
- Children (6-12): ${PRICING['child_base']}/person
- Ages 5 & under: FREE
- Party Minimum: ${PRICING['party_minimum']} (~10 adults)

**What's Included:**
- {MENU_ITEMS['proteins_per_guest']} proteins per guest: {', '.join(MENU_ITEMS['standard_proteins'])}
- {', '.join(MENU_ITEMS['included_items'])}

**Premium Upgrades Available:**
- {', '.join(MENU_ITEMS['premium_proteins'])}

**Service Areas:** {', '.join(SERVICE_AREAS['primary'])}
**Travel:** First {PRICING['travel_free_miles']} miles free, then ${PRICING['travel_per_mile']}/mile
**Booking:** {POLICIES['booking']['minimum_advance_hours']} hours minimum advance notice
**Deposit:** ${PRICING['deposit']} (refundable if canceled {PRICING['deposit_refund_days']}+ days before)

Answer their question warmly and professionally. Keep it under 150 words. End with asking if they'd like to book."""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.settings.openai_model or "gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                temperature=0.7,
                max_tokens=200,
            )

            return {
                "text": response.choices[0].message.content,
                "next_action": "await_customer_response",
            }

        except Exception as e:
            logger.error(f"Error handling inquiry: {e}")
            return {
                "text": "I'd be happy to help! Could you tell me more about what you're looking for?",
                "next_action": "await_customer_response",
            }

    def _get_greeting_message(self) -> str:
        """Get friendly greeting message"""
        return RESPONSE_TEMPLATES["greeting"]

    def _get_missing_fields(self, booking_data: Dict[str, Any]) -> List[str]:
        """Identify missing required fields"""
        required = {
            "event_date": "event date",
            "event_time": "event time",
            "guest_count": "number of guests",
            "location_address": "event address",
        }

        return [label for field, label in required.items() if not booking_data.get(field)]

    def _get_info_collection_message(self, missing_fields: List[str]) -> str:
        """Generate message asking for missing information"""
        if not missing_fields:
            return "Great! I have all the information I need. Let me confirm the details..."

        if len(missing_fields) == 1:
            return f"I just need to know your {missing_fields[0]}. 📝"
        else:
            fields_text = ", ".join(missing_fields[:-1]) + f" and {missing_fields[-1]}"
            return f"I still need your {fields_text}. 📝"

    def _format_booking_confirmation(self, booking_data: Dict[str, Any]) -> str:
        """Format booking details for customer confirmation"""
        parts = [
            "Perfect! Here's what I have:",
            "",
            f"📅 Date: {booking_data.get('event_date')}",
            f"🕐 Time: {booking_data.get('event_time')}",
            f"👥 Guests: {booking_data.get('guest_count')}",
            f"📍 Location: {booking_data.get('location_address')}",
        ]

        if booking_data.get("package_type"):
            parts.append(f"🎁 Package: {booking_data.get('package_type').title()}")

        if booking_data.get("special_requests"):
            parts.append(f"📝 Special Requests: {booking_data.get('special_requests')}")

        parts.extend(["", "Is this correct? Reply 'yes' to proceed with booking. ✅"])

        return "\n".join(parts)

    async def create_booking_from_data(
        self, booking_data: Dict[str, Any], customer: Customer, channel: str
    ) -> Optional[Booking]:
        """Create actual booking in system"""
        try:
            # Validate required fields
            required = ["event_date", "event_time", "guest_count", "location_address"]
            if not all(booking_data.get(field) for field in required):
                logger.error(f"Missing required fields: {required}")
                return None

            # Create booking via booking service
            booking = await self.booking_service.create_booking(
                customer_id=customer.id,
                event_date=booking_data["event_date"],
                event_time=booking_data["event_time"],
                guest_count=int(booking_data["guest_count"]),
                location_address=booking_data["location_address"],
                package_type=booking_data.get("package_type", "standard"),
                special_requests=booking_data.get("special_requests"),
                source=channel,  # 'phone', 'sms', 'whatsapp', 'web_chat'
                sms_consent=True,  # Already confirmed via terms
            )

            logger.info(f"✅ Booking created: {booking.id} for customer {customer.id}")

            # Send confirmation
            await self.notification_service.send_booking_confirmation(
                customer=customer, booking=booking, channel=channel
            )

            return booking

        except Exception as e:
            logger.error(f"❌ Failed to create booking: {e}", exc_info=True)
            return None

    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            "response_text": "I'm sorry, I'm having trouble processing your request. Let me connect you with someone who can help. 🤝",
            "intent": "escalation",
            "stage": "escalated",
            "next_action": "escalate_to_human",
            "booking_data": {},
            "requires_human": True,
            "error": error_message,
        }


# Convenience functions for common use cases


async def process_sms_booking_message(
    db: Session,
    from_number: str,
    message_text: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Process an SMS message for booking intent.
    Convenience wrapper for SMS channel.
    """
    assistant = AIBookingAssistant(db)
    return await assistant.process_message(
        message=message_text,
        customer_phone=from_number,
        channel="sms",
        conversation_history=conversation_history,
    )


async def process_phone_booking_transcript(
    db: Session,
    caller_phone: str,
    transcript: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Process a phone call transcript for booking intent.
    Convenience wrapper for phone channel.
    """
    assistant = AIBookingAssistant(db)
    return await assistant.process_message(
        message=transcript,
        customer_phone=caller_phone,
        channel="phone",
        conversation_history=conversation_history,
    )


async def process_web_chat_message(
    db: Session,
    customer_id: int,
    message_text: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Process a web chat message for booking intent.
    Convenience wrapper for web chat channel.
    """
    assistant = AIBookingAssistant(db)
    return await assistant.process_message(
        message=message_text,
        customer_id=customer_id,
        channel="web_chat",
        conversation_history=conversation_history,
    )
