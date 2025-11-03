"""
Public lead capture endpoint - no authentication required
Rate limited to prevent spam
"""

from datetime import date, datetime
import logging

from api.app.database import get_db
from api.app.models.lead_newsletter import LeadSource
from api.app.services.lead_service import LeadService
from api.app.services.newsletter_service import NewsletterService
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class PublicLeadCreate(BaseModel):
    """Public lead submission schema - Name and Phone are REQUIRED for lead generation"""

    name: str = Field(..., min_length=2, max_length=100, description="Full name (required)")
    phone: str = Field(
        ...,
        min_length=10,
        max_length=20,
        description="Phone number (required - accepts various formats like (555) 123-4567)",
    )
    email: EmailStr | None = Field(None, description="Email address (optional but recommended)")
    event_date: date | None = Field(None, description="Preferred event date")
    guest_count: int | None = Field(None, ge=1, le=500, description="Number of guests")
    budget: str | None = Field(None, max_length=50, description="Budget range (e.g., $500-1000)")
    location: str | None = Field(None, max_length=200, description="Event location or zip code")
    message: str | None = Field(
        None, max_length=2000, description="Additional message or questions"
    )
    source: str = Field(default="website", description="Lead source")

    # Consent fields
    email_consent: bool = Field(default=False, description="Consent to email contact")
    sms_consent: bool = Field(default=False, description="Consent to SMS contact")

    # Spam prevention
    honeypot: str | None = Field(default=None, description="Honeypot field (should be empty)")


class PublicLeadResponse(BaseModel):
    """Public lead submission response"""

    success: bool
    message: str
    lead_id: str | None = None


def clean_phone_number(phone: str | None) -> str | None:
    """
    Clean and format phone number to digits only.
    Accepts formats like: (555) 123-4567, 555-123-4567, 555.123.4567, etc.
    Returns: digits only (e.g., "5551234567" or "+15551234567")
    """
    if not phone:
        return None

    # Keep only digits and leading +
    cleaned = "".join(c for c in phone if c.isdigit() or (c == "+" and phone.index(c) == 0))

    # Validate length (10-15 digits for international)
    digit_count = len(cleaned.replace("+", ""))
    if digit_count < 10 or digit_count > 15:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Phone number must contain 10-15 digits, got {digit_count}",
        )

    return cleaned


@router.post("/leads", response_model=PublicLeadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def capture_public_lead(
    lead_data: PublicLeadCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint to capture leads from website forms

    Rate limit: 10 requests/minute per IP (enforced)
    No authentication required

    Use cases:
    - Quote request forms
    - Contact forms
    - "Get a quote" CTAs
    - Newsletter signups with event interest
    """
    try:
        # Clean phone number (remove formatting, keep digits)
        cleaned_phone = clean_phone_number(lead_data.phone)

        # Spam prevention - honeypot check
        if lead_data.honeypot:
            logger.warning(f"Honeypot triggered from IP {request.client.host}")
            # Return success to not reveal honeypot
            return PublicLeadResponse(success=True, message="Thank you! We'll be in touch soon.")

        # Name and phone are required (enforced by Pydantic)
        # Email is optional but recommended
        if not cleaned_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number is required to contact you about your quote",
            )

        # Map source string to LeadSource enum
        source_map = {
            "website": LeadSource.WEB_QUOTE,
            "quote": LeadSource.WEB_QUOTE,
            "chat": LeadSource.CHAT,
            "instagram": LeadSource.INSTAGRAM,
            "facebook": LeadSource.FACEBOOK,
            "phone": LeadSource.PHONE,
            "referral": LeadSource.REFERRAL,
            "google": LeadSource.GOOGLE,
        }
        source = source_map.get(lead_data.source.lower(), LeadSource.WEB_QUOTE)

        # Create lead service
        lead_service = LeadService(db=db)

        # Capture lead using quote request method (with cleaned phone)
        lead = await lead_service.capture_quote_request(
            name=lead_data.name,
            phone=cleaned_phone,  # Required - cleaned phone number
            email=lead_data.email,  # Optional
            event_date=lead_data.event_date,
            guest_count=lead_data.guest_count,
            budget=lead_data.budget,
            message=lead_data.message,
            location=lead_data.location,
        )

        logger.info(
            f"Public lead captured: {lead.id} from {request.client.host} "
            f"(name={lead_data.name}, email={lead_data.email}, source={source.value})"
        )

        # Auto-subscribe to newsletter (opt-out system)
        try:
            newsletter_service = NewsletterService(db)
            subscriber = await newsletter_service.subscribe(
                phone=cleaned_phone,
                email=lead_data.email,
                name=lead_data.name,
                source="web_quote",
                auto_subscribed=True,
            )
            logger.info(
                f"Auto-subscribed {lead_data.name} to newsletter from quote form. "
                f"Subscriber ID: {subscriber.id}"
            )
            await db.commit()
        except Exception as newsletter_error:
            # Don't fail lead creation if newsletter subscription fails
            logger.exception(
                f"Newsletter subscription failed for lead {lead.id}: {newsletter_error}"
            )
            await db.rollback()
            # Re-commit the lead
            await db.commit()

        # TODO: Send email notification to admin
        # TODO: Send confirmation email to customer (if consent given)

        return PublicLeadResponse(
            success=True,
            message="Thank you! We've received your request and will contact you shortly.",
            lead_id=str(lead.id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error capturing public lead: {e}", exc_info=True)
        # Return detailed error in development
        import traceback

        error_details = traceback.format_exc()
        logger.exception(f"Full traceback:\n{error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {e!s}",  # More detailed in development
        )


@router.post(
    "/leads/failed-booking", response_model=PublicLeadResponse, status_code=status.HTTP_201_CREATED
)
async def capture_failed_booking_lead(
    booking_data: dict, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Internal endpoint called by booking service when booking fails
    Captures customer info as lead for follow-up

    Note: This should be protected by internal service authentication in production
    """
    try:
        lead_service = LeadService(db=db)

        # Extract contact info
        contact_info = {
            "email": booking_data.get("email") or booking_data.get("contact_email"),
            "phone": booking_data.get("phone") or booking_data.get("contact_phone"),
        }

        # Capture failed booking
        lead = await lead_service.capture_failed_booking(
            contact_info=contact_info,
            booking_data=booking_data,
            failure_reason=booking_data.get("failure_reason", "Slot unavailable"),
        )

        logger.info(f"Failed booking captured as lead: {lead.id}")

        return PublicLeadResponse(
            success=True,
            message="We've saved your information and will contact you with alternative dates.",
            lead_id=str(lead.id),
        )

    except Exception as e:
        logger.error(f"Error capturing failed booking lead: {e}", exc_info=True)
        # Don't fail the booking flow if lead capture fails
        return PublicLeadResponse(
            success=False, message="Unable to save for follow-up, but you can contact us directly."
        )


# Health check for public endpoints
@router.get("/health")
async def public_health_check():
    """Health check for public lead capture endpoint"""
    return {
        "status": "healthy",
        "service": "public-lead-capture",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ===== PUBLIC BOOKING ENDPOINT =====


class PublicBookingCreate(BaseModel):
    """Public booking submission schema - NO authentication required"""

    # Customer info (required)
    customer_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    customer_phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    customer_email: EmailStr = Field(..., description="Email address")

    # Event details (required)
    date: str = Field(..., description="Event date (YYYY-MM-DD)")
    time: str = Field(..., description="Event time (HH:MM 24-hour format)")
    guests: int = Field(..., ge=1, le=50, description="Number of guests")
    location_address: str = Field(
        ..., min_length=10, max_length=500, description="Full event address"
    )

    # Optional fields
    special_requests: str | None = Field(
        None, max_length=2000, description="Special requests or dietary needs"
    )

    # Spam prevention
    honeypot: str | None = Field(default=None, description="Honeypot field (should be empty)")


class PublicBookingResponse(BaseModel):
    success: bool
    message: str
    booking_id: str | None = None


@router.post("/bookings", response_model=PublicBookingResponse)
@limiter.limit("5/minute")  # More restrictive than leads since bookings are heavier
async def create_public_booking(
    booking_data: PublicBookingCreate, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    Public booking submission endpoint - NO authentication required

    This endpoint:
    1. Creates a booking lead (since user may not be registered)
    2. Auto-subscribes to newsletter with opt-out capability
    3. Rate limited to 5 requests/minute
    4. Validates all inputs

    Returns:
        Booking confirmation with ID

    Raises:
        HTTPException(400): Invalid input or spam detected
        HTTPException(429): Too many requests
    """
    # Honeypot spam check
    if booking_data.honeypot:
        logger.warning(f"Spam booking attempt detected from {request.client.host}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid submission")

    try:
        # Clean phone number (remove formatting)
        cleaned_phone = "".join(filter(str.isdigit, booking_data.customer_phone))
        if not (10 <= len(cleaned_phone) <= 15):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide a valid phone number",
            )

        # Add country code if missing (assume US)
        if len(cleaned_phone) == 10:
            cleaned_phone = f"+1{cleaned_phone}"
        elif not cleaned_phone.startswith("+"):
            cleaned_phone = f"+{cleaned_phone}"

        # Validate date/time format
        try:
            event_date_obj = datetime.strptime(booking_data.date, "%Y-%m-%d").date()
            datetime.strptime(booking_data.time, "%H:%M")  # Validate time format
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date or time format: {e!s}",
            )

        # Check date is in future
        if event_date_obj < date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Event date must be in the future"
            )

        # Create lead with booking intent
        lead_service = LeadService(db=db)
        lead = await lead_service.capture_quote_request(
            name=booking_data.customer_name,
            phone=cleaned_phone,
            email=booking_data.customer_email,
            event_date=event_date_obj,
            guest_count=booking_data.guests,
            location=booking_data.location_address,
            message=f"BOOKING REQUEST - Time: {booking_data.time}, Guests: {booking_data.guests}\n{booking_data.special_requests or ''}",
            source="web_booking",
            ip_address=request.client.host if request.client else None,
        )

        await db.commit()
        await db.refresh(lead)

        logger.info(
            f"✅ Public booking lead created: {lead.id} for {booking_data.customer_name} "
            f"on {booking_data.date} at {booking_data.time}"
        )

        # Auto-subscribe to newsletter (opt-out system)
        try:
            newsletter_service = NewsletterService(db)
            subscriber = await newsletter_service.subscribe(
                phone=cleaned_phone,
                email=booking_data.customer_email,
                name=booking_data.customer_name,
                source="web_booking",
                auto_subscribed=True,
            )
            logger.info(
                f"Auto-subscribed {booking_data.customer_name} to newsletter from booking form. "
                f"Subscriber ID: {subscriber.id}"
            )
            await db.commit()
        except Exception as newsletter_error:
            # Don't fail booking if newsletter subscription fails
            logger.exception(
                f"Newsletter subscription failed for lead {lead.id}: {newsletter_error}"
            )
            # Don't rollback the lead - we still want to capture it
            await db.rollback()
            await db.commit()  # Re-commit the lead

        return PublicBookingResponse(
            success=True,
            message="Thank you! We've received your booking request and will contact you shortly to confirm details.",
            booking_id=str(lead.id),
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error creating public booking: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sorry, we couldn't process your booking request. Please try again or contact us directly.",
        )
