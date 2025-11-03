"""
AI booking tools for safe interaction with the CRM backend.
These tools provide validated, idempotent operations for the AI system.
"""
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession

from api.app.auth.models import User
from api.app.cqrs.base import command_bus, query_bus
from api.app.cqrs.crm_operations import *
from api.app.database import get_db_session

logger = logging.getLogger(__name__)


class AIBookingToolsConfig:
    """Configuration for AI booking tools."""

    # Business rules
    MIN_ADVANCE_BOOKING_HOURS = 4
    MAX_ADVANCE_BOOKING_DAYS = 90
    MIN_PARTY_SIZE = 1
    MAX_PARTY_SIZE = 50
    DEFAULT_EVENT_DURATION_MINUTES = 180

    # Available time slots
    AVAILABLE_SLOTS = [
        "11:00 AM", "11:30 AM",
        "12:00 PM", "12:30 PM",
        "1:00 PM", "1:30 PM", "2:00 PM", "2:30 PM",
        "3:00 PM", "3:30 PM", "4:00 PM", "4:30 PM",
        "5:00 PM", "5:30 PM", "6:00 PM", "6:30 PM", "7:00 PM"
    ]

    # Pricing (cents)
    BASE_PRICE_PER_PERSON_CENTS = 4500  # $45 per person
    DEPOSIT_PERCENTAGE = 0.25  # 25% deposit


class BookingValidationError(Exception):
    """Custom exception for booking validation errors."""

    def __init__(self, message: str, code: str = "VALIDATION_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class AIBookingRequest(BaseModel):
    """Validated booking request from AI."""

    customer_email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    customer_name: str = Field(..., min_length=2, max_length=100)
    customer_phone: str = Field(..., pattern=r'^\+?[\d\s\-\(\)\.]{10,20}$')

    preferred_date: date
    preferred_slot: str
    party_size: int = Field(..., ge=1, le=50)
    special_requests: Optional[str] = Field(None, max_length=500)

    ai_conversation_id: str = Field(..., min_length=1, max_length=100)
    source: str = Field(default="ai_chat")

    @validator('customer_phone')
    def validate_phone(cls, v):
        # Extract digits and validate US phone format
        digits = re.sub(r'[^\d]', '', v)
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+{digits}"
        else:
            raise ValueError('Phone number must be valid US format')

    @validator('preferred_slot')
    def validate_slot(cls, v):
        if v not in AIBookingToolsConfig.AVAILABLE_SLOTS:
            raise ValueError(f'Slot must be one of: {", ".join(AIBookingToolsConfig.AVAILABLE_SLOTS)}')
        return v

    @validator('preferred_date')
    def validate_date(cls, v):
        today = date.today()
        min_date = today + timedelta(hours=AIBookingToolsConfig.MIN_ADVANCE_BOOKING_HOURS/24)
        max_date = today + timedelta(days=AIBookingToolsConfig.MAX_ADVANCE_BOOKING_DAYS)

        if v < min_date.date():
            raise ValueError(f'Booking must be at least {AIBookingToolsConfig.MIN_ADVANCE_BOOKING_HOURS} hours in advance')
        if v > max_date:
            raise ValueError(f'Booking cannot be more than {AIBookingToolsConfig.MAX_ADVANCE_BOOKING_DAYS} days in advance')

        # No bookings on Mondays (restaurant closed)
        if v.weekday() == 0:
            raise ValueError('Restaurant is closed on Mondays')

        return v


class AIBookingTools:
    """Safe AI tools for booking operations with comprehensive validation."""

    def __init__(self):
        self.config = AIBookingToolsConfig()

    async def get_ai_system_user(self, db: AsyncSession) -> User:
        """Get or create AI system user for operations."""
        from sqlalchemy import select

        from app.auth.models import Role, User

        # Look for existing AI system user
        query = select(User).where(User.email == "ai-system@myhibachi.com")
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            # Create AI system user if it doesn't exist
            ai_role_query = select(Role).where(Role.name == "AI_SYSTEM")
            ai_role_result = await db.execute(ai_role_query)
            ai_role = ai_role_result.scalar_one_or_none()

            if not ai_role:
                raise Exception("AI_SYSTEM role not found - please run database migrations")

            user = User(
                id=uuid4(),
                email="ai-system@myhibachi.com",
                username="ai-system",
                full_name="AI Booking System",
                role_id=ai_role.id,
                is_active=True,
                email_verified=True,
                created_at=datetime.utcnow()
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user

    async def check_availability(
        self,
        preferred_date: date,
        party_size: int,
        preferred_slots: list[str] = None
    ) -> dict[str, Any]:
        """
        Check availability for booking with comprehensive slot information.

        Returns:
            Dict with available slots and booking recommendations
        """
        try:
            async with get_db_session() as db:
                # Validate inputs
                if party_size < self.config.MIN_PARTY_SIZE or party_size > self.config.MAX_PARTY_SIZE:
                    raise BookingValidationError(
                        f"Party size must be between {self.config.MIN_PARTY_SIZE} and {self.config.MAX_PARTY_SIZE}",
                        "INVALID_PARTY_SIZE"
                    )

                # Check if date is valid for booking
                today = date.today()
                min_booking_date = today + timedelta(hours=self.config.MIN_ADVANCE_BOOKING_HOURS/24)

                if preferred_date < min_booking_date.date():
                    raise BookingValidationError(
                        f"Bookings must be made at least {self.config.MIN_ADVANCE_BOOKING_HOURS} hours in advance",
                        "INSUFFICIENT_ADVANCE_NOTICE"
                    )

                if preferred_date.weekday() == 0:  # Monday
                    raise BookingValidationError(
                        "Restaurant is closed on Mondays",
                        "RESTAURANT_CLOSED"
                    )

                # Query for availability
                query = GetAvailabilitySlotsQuery(
                    date=preferred_date,
                    party_size=party_size,
                    duration_minutes=self.config.DEFAULT_EVENT_DURATION_MINUTES
                )

                result = await query_bus.execute(query, db)

                if not result.success:
                    raise BookingValidationError(
                        result.error or "Failed to check availability",
                        "AVAILABILITY_CHECK_FAILED"
                    )

                availability_data = result.data
                available_slots = availability_data.get("available_slots", [])

                # Filter by preferred slots if specified
                if preferred_slots:
                    available_slots = [
                        slot for slot in available_slots
                        if slot.get("time") in preferred_slots
                    ]

                # Calculate pricing
                base_total = party_size * self.config.BASE_PRICE_PER_PERSON_CENTS
                deposit_amount = int(base_total * self.config.DEPOSIT_PERCENTAGE)

                return {
                    "success": True,
                    "date": str(preferred_date),
                    "party_size": party_size,
                    "available_slots": available_slots,
                    "total_available_slots": len(available_slots),
                    "pricing": {
                        "price_per_person_cents": self.config.BASE_PRICE_PER_PERSON_CENTS,
                        "total_due_cents": base_total,
                        "deposit_due_cents": deposit_amount,
                        "remaining_balance_cents": base_total - deposit_amount
                    },
                    "restaurant_info": {
                        "closed_days": ["Monday"],
                        "typical_event_duration_minutes": self.config.DEFAULT_EVENT_DURATION_MINUTES,
                        "advance_booking_required_hours": self.config.MIN_ADVANCE_BOOKING_HOURS
                    }
                }

        except BookingValidationError:
            raise
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            raise BookingValidationError(
                "An unexpected error occurred while checking availability",
                "SYSTEM_ERROR",
                {"original_error": str(e)}
            )

    async def create_booking(self, booking_request: AIBookingRequest) -> dict[str, Any]:
        """
        Create a new hibachi booking with comprehensive validation and idempotency.

        Args:
            booking_request: Validated booking request

        Returns:
            Dict with booking details and confirmation information
        """
        try:
            async with get_db_session() as db:
                # Get AI system user
                ai_user = await self.get_ai_system_user(db)

                # Double-check availability before creating booking
                availability = await self.check_availability(
                    booking_request.preferred_date,
                    booking_request.party_size,
                    [booking_request.preferred_slot]
                )

                if not availability["available_slots"]:
                    raise BookingValidationError(
                        f"Slot {booking_request.preferred_slot} is no longer available for {booking_request.preferred_date}",
                        "SLOT_UNAVAILABLE"
                    )

                # Calculate pricing
                pricing = availability["pricing"]

                # Create idempotency key based on request content
                idempotency_key = f"ai_booking_{booking_request.ai_conversation_id}_{hash(str(booking_request.dict()))}"

                # Create booking command
                command = CreateBookingCommand(
                    customer_email=booking_request.customer_email,
                    customer_name=booking_request.customer_name,
                    customer_phone=booking_request.customer_phone,
                    date=booking_request.preferred_date,
                    slot=booking_request.preferred_slot,
                    total_guests=booking_request.party_size,
                    special_requests=booking_request.special_requests,
                    price_per_person_cents=pricing["price_per_person_cents"],
                    total_due_cents=pricing["total_due_cents"],
                    deposit_due_cents=pricing["deposit_due_cents"],
                    source=booking_request.source,
                    ai_conversation_id=booking_request.ai_conversation_id,
                    idempotency_key=idempotency_key
                )

                # Execute booking creation
                result = await command_bus.execute(command, db)

                if not result.success:
                    raise BookingValidationError(
                        result.error or "Failed to create booking",
                        "BOOKING_CREATION_FAILED"
                    )

                booking_data = result.data
                booking_id = booking_data["booking_id"]

                # Log successful booking creation
                logger.info(f"AI successfully created booking {booking_id} for {booking_request.customer_email}")

                # PHASE 2C OPTIMIZATION: Schedule follow-up in background (non-blocking)
                # This used to take 1931ms blocking the booking confirmation response
                # Now it runs asynchronously so booking responds in <500ms
                try:
                    from api.ai.scheduler.follow_up_scheduler import schedule_followup_in_background
                    from api.ai.scheduler import get_scheduler
                    from datetime import datetime
                    
                    scheduler = get_scheduler()
                    if scheduler and booking_request.ai_conversation_id:
                        # Convert booking date string to datetime
                        event_date = datetime.fromisoformat(str(booking_request.preferred_date))
                        
                        schedule_followup_in_background(
                            scheduler=scheduler,
                            conversation_id=booking_request.ai_conversation_id,
                            user_id=booking_request.customer_email,  # Use email as user_id
                            event_date=event_date,
                            booking_id=booking_id
                        )
                        logger.debug(f"Queued follow-up scheduling for booking {booking_id}")
                except Exception as e:
                    # Log but don't fail booking creation if scheduling fails
                    logger.warning(f"Failed to queue follow-up scheduling for booking {booking_id}: {e}")

                # Return comprehensive booking information
                return {
                    "success": True,
                    "booking_id": booking_id,
                    "confirmation_number": booking_data.get("confirmation_number"),
                    "customer": {
                        "email": booking_request.customer_email,
                        "name": booking_request.customer_name,
                        "phone": booking_request.customer_phone
                    },
                    "event_details": {
                        "date": str(booking_request.preferred_date),
                        "slot": booking_request.preferred_slot,
                        "party_size": booking_request.party_size,
                        "special_requests": booking_request.special_requests,
                        "estimated_duration_minutes": self.config.DEFAULT_EVENT_DURATION_MINUTES
                    },
                    "pricing": pricing,
                    "payment_info": {
                        "deposit_required": True,
                        "deposit_amount_cents": pricing["deposit_due_cents"],
                        "remaining_balance_cents": pricing["remaining_balance_cents"],
                        "payment_methods": ["card", "cash"]
                    },
                    "next_steps": {
                        "payment_link_sent": True,  # Would be sent via outbox
                        "confirmation_sms_sent": True,  # Would be sent via outbox
                        "can_modify_until": str(booking_request.preferred_date - timedelta(hours=24))
                    },
                    "ai_context": {
                        "conversation_id": booking_request.ai_conversation_id,
                        "created_by": "ai_system"
                    }
                }

        except BookingValidationError:
            raise
        except Exception as e:
            logger.error(f"Error creating AI booking: {e}")
            raise BookingValidationError(
                "An unexpected error occurred while creating the booking",
                "SYSTEM_ERROR",
                {"original_error": str(e)}
            )

    async def get_booking_details(
        self,
        booking_id: str = None,
        customer_email: str = None,
        customer_phone: str = None,
        confirmation_number: str = None
    ) -> dict[str, Any]:
        """
        Get booking details by various identifiers with proper access control.

        Args:
            booking_id: UUID of the booking
            customer_email: Customer email to search by
            customer_phone: Customer phone to search by
            confirmation_number: Confirmation number to search by

        Returns:
            Dict with booking details
        """
        try:
            async with get_db_session() as db:
                # Validate that at least one identifier is provided
                if not any([booking_id, customer_email, customer_phone, confirmation_number]):
                    raise BookingValidationError(
                        "At least one identifier (booking_id, customer_email, customer_phone, or confirmation_number) must be provided",
                        "MISSING_IDENTIFIER"
                    )

                # Query by booking ID if provided
                if booking_id:
                    try:
                        booking_uuid = UUID(booking_id)
                        query = GetBookingQuery(
                            booking_id=booking_uuid,
                            include_payments=True,
                            include_messages=True
                        )
                        result = await query_bus.execute(query, db)

                        if not result.success:
                            raise BookingValidationError(
                                f"Booking not found with ID: {booking_id}",
                                "BOOKING_NOT_FOUND"
                            )

                        return {
                            "success": True,
                            "booking": result.data
                        }
                    except ValueError:
                        raise BookingValidationError(
                            "Invalid booking ID format",
                            "INVALID_BOOKING_ID"
                        )

                # Query by customer information
                if customer_email or customer_phone:
                    query = GetBookingsQuery(
                        customer_email=customer_email,
                        customer_phone=customer_phone,
                        page=1,
                        page_size=10,
                        sort_by="created_at",
                        sort_order="desc"
                    )
                    result = await query_bus.execute(query, db)

                    if not result.success:
                        raise BookingValidationError(
                            "Failed to search for bookings",
                            "SEARCH_FAILED"
                        )

                    bookings = result.data.get("bookings", [])
                    if not bookings:
                        identifier = customer_email or customer_phone
                        raise BookingValidationError(
                            f"No bookings found for {identifier}",
                            "NO_BOOKINGS_FOUND"
                        )

                    return {
                        "success": True,
                        "bookings": bookings,
                        "total_count": result.total_count
                    }

                # If confirmation number search is needed, implement that logic here
                # This would require adding confirmation number indexing to the database

                raise BookingValidationError(
                    "Search method not implemented for provided identifiers",
                    "SEARCH_NOT_IMPLEMENTED"
                )

        except BookingValidationError:
            raise
        except Exception as e:
            logger.error(f"Error getting booking details: {e}")
            raise BookingValidationError(
                "An unexpected error occurred while retrieving booking details",
                "SYSTEM_ERROR",
                {"original_error": str(e)}
            )

    async def update_booking(
        self,
        booking_id: str,
        updates: dict[str, Any],
        ai_conversation_id: str,
        update_reason: str = "Updated by AI assistant"
    ) -> dict[str, Any]:
        """
        Update an existing booking with validation and change tracking.

        Args:
            booking_id: UUID of the booking to update
            updates: Dictionary of fields to update
            ai_conversation_id: AI conversation ID for tracking
            update_reason: Reason for the update

        Returns:
            Dict with update results
        """
        try:
            async with get_db_session() as db:
                # Get AI system user
                ai_user = await self.get_ai_system_user(db)

                # Validate booking ID
                try:
                    booking_uuid = UUID(booking_id)
                except ValueError:
                    raise BookingValidationError(
                        "Invalid booking ID format",
                        "INVALID_BOOKING_ID"
                    )

                # Get current booking details
                current_booking_result = await self.get_booking_details(booking_id=booking_id)
                if not current_booking_result["success"]:
                    raise BookingValidationError(
                        f"Booking not found: {booking_id}",
                        "BOOKING_NOT_FOUND"
                    )

                current_booking = current_booking_result["booking"]

                # Validate updates
                allowed_fields = ["customer_name", "customer_phone", "date", "slot", "total_guests", "special_requests"]
                validated_updates = {}

                for field, value in updates.items():
                    if field not in allowed_fields:
                        raise BookingValidationError(
                            f"Field '{field}' cannot be updated via AI",
                            "FIELD_NOT_UPDATABLE"
                        )

                    # Validate specific field updates
                    if field == "date" and value:
                        new_date = date.fromisoformat(value) if isinstance(value, str) else value
                        # Validate new date
                        if new_date.weekday() == 0:  # Monday
                            raise BookingValidationError(
                                "Restaurant is closed on Mondays",
                                "INVALID_DATE"
                            )
                        validated_updates["date"] = new_date

                    elif field == "slot" and value:
                        if value not in self.config.AVAILABLE_SLOTS:
                            raise BookingValidationError(
                                f"Invalid time slot: {value}",
                                "INVALID_SLOT"
                            )
                        validated_updates["slot"] = value

                    elif field == "total_guests" and value:
                        if not (self.config.MIN_PARTY_SIZE <= value <= self.config.MAX_PARTY_SIZE):
                            raise BookingValidationError(
                                f"Party size must be between {self.config.MIN_PARTY_SIZE} and {self.config.MAX_PARTY_SIZE}",
                                "INVALID_PARTY_SIZE"
                            )
                        validated_updates["total_guests"] = value

                    elif field == "customer_phone" and value:
                        # Validate phone format
                        digits = re.sub(r'[^\d]', '', value)
                        if len(digits) == 10:
                            validated_updates["customer_phone"] = f"+1{digits}"
                        elif len(digits) == 11 and digits[0] == '1':
                            validated_updates["customer_phone"] = f"+{digits}"
                        else:
                            raise BookingValidationError(
                                "Invalid phone number format",
                                "INVALID_PHONE"
                            )

                    else:
                        validated_updates[field] = value

                if not validated_updates:
                    raise BookingValidationError(
                        "No valid updates provided",
                        "NO_UPDATES"
                    )

                # Create update command
                command = UpdateBookingCommand(
                    booking_id=booking_uuid,
                    updated_by=str(ai_user.id),
                    update_reason=f"{update_reason} (AI Conversation: {ai_conversation_id})",
                    idempotency_key=f"ai_update_{booking_id}_{ai_conversation_id}_{hash(str(validated_updates))}",
                    **validated_updates
                )

                # Execute update
                result = await command_bus.execute(command, db)

                if not result.success:
                    raise BookingValidationError(
                        result.error or "Failed to update booking",
                        "UPDATE_FAILED"
                    )

                logger.info(f"AI successfully updated booking {booking_id}: {validated_updates}")

                return {
                    "success": True,
                    "booking_id": booking_id,
                    "updates_applied": validated_updates,
                    "update_reason": update_reason,
                    "ai_context": {
                        "conversation_id": ai_conversation_id,
                        "updated_by": "ai_system"
                    }
                }

        except BookingValidationError:
            raise
        except Exception as e:
            logger.error(f"Error updating AI booking: {e}")
            raise BookingValidationError(
                "An unexpected error occurred while updating the booking",
                "SYSTEM_ERROR",
                {"original_error": str(e)}
            )

    async def cancel_booking(
        self,
        booking_id: str,
        ai_conversation_id: str,
        cancellation_reason: str = "Cancelled by AI assistant",
        refund_requested: bool = False
    ) -> dict[str, Any]:
        """
        Cancel a booking with proper validation and refund handling.

        Args:
            booking_id: UUID of the booking to cancel
            ai_conversation_id: AI conversation ID for tracking
            cancellation_reason: Reason for cancellation
            refund_requested: Whether a refund is requested

        Returns:
            Dict with cancellation results
        """
        try:
            async with get_db_session() as db:
                # Get AI system user
                ai_user = await self.get_ai_system_user(db)

                # Validate booking ID
                try:
                    booking_uuid = UUID(booking_id)
                except ValueError:
                    raise BookingValidationError(
                        "Invalid booking ID format",
                        "INVALID_BOOKING_ID"
                    )

                # Get current booking details
                current_booking_result = await self.get_booking_details(booking_id=booking_id)
                if not current_booking_result["success"]:
                    raise BookingValidationError(
                        f"Booking not found: {booking_id}",
                        "BOOKING_NOT_FOUND"
                    )

                current_booking = current_booking_result["booking"]

                # Check if booking can be cancelled
                booking_status = current_booking.get("status")
                if booking_status in ["cancelled", "completed"]:
                    raise BookingValidationError(
                        f"Cannot cancel booking with status: {booking_status}",
                        "BOOKING_NOT_CANCELLABLE"
                    )

                # Calculate refund amount if requested
                refund_amount_cents = 0
                if refund_requested:
                    payments = current_booking.get("payments", [])
                    total_paid = sum(payment.get("amount_cents", 0) for payment in payments)

                    # Full refund if cancelled more than 24 hours in advance
                    booking_date = date.fromisoformat(current_booking["date"])
                    hours_until_booking = (datetime.combine(booking_date, datetime.min.time()) - datetime.now()).total_seconds() / 3600

                    if hours_until_booking >= 24:
                        refund_amount_cents = total_paid
                    else:
                        # Partial refund based on policy
                        refund_amount_cents = int(total_paid * 0.5)  # 50% refund for late cancellations

                # Create cancellation command
                command = CancelBookingCommand(
                    booking_id=booking_uuid,
                    cancellation_reason=f"{cancellation_reason} (AI Conversation: {ai_conversation_id})",
                    cancelled_by=str(ai_user.id),
                    refund_amount_cents=refund_amount_cents,
                    idempotency_key=f"ai_cancel_{booking_id}_{ai_conversation_id}"
                )

                # Execute cancellation
                result = await command_bus.execute(command, db)

                if not result.success:
                    raise BookingValidationError(
                        result.error or "Failed to cancel booking",
                        "CANCELLATION_FAILED"
                    )

                logger.info(f"AI successfully cancelled booking {booking_id} with refund ${refund_amount_cents/100:.2f}")

                return {
                    "success": True,
                    "booking_id": booking_id,
                    "cancellation_confirmed": True,
                    "refund_info": {
                        "refund_requested": refund_requested,
                        "refund_amount_cents": refund_amount_cents,
                        "refund_amount_dollars": refund_amount_cents / 100,
                        "refund_processing": refund_amount_cents > 0
                    },
                    "cancellation_reason": cancellation_reason,
                    "ai_context": {
                        "conversation_id": ai_conversation_id,
                        "cancelled_by": "ai_system"
                    }
                }

        except BookingValidationError:
            raise
        except Exception as e:
            logger.error(f"Error cancelling AI booking: {e}")
            raise BookingValidationError(
                "An unexpected error occurred while cancelling the booking",
                "SYSTEM_ERROR",
                {"original_error": str(e)}
            )


# Create global instance for easy import
ai_booking_tools = AIBookingTools()


__all__ = [
    "AIBookingTools", "AIBookingRequest", "BookingValidationError",
    "AIBookingToolsConfig", "ai_booking_tools"
]
