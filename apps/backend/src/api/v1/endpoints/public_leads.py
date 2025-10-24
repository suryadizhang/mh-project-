"""
Public lead capture endpoint - no authentication required
Rate limited to prevent spam
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...services.lead_service import LeadService
from ...api.app.models.lead_newsletter import LeadSource
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class PublicLeadCreate(BaseModel):
    """Public lead submission schema"""
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: Optional[EmailStr] = Field(None, description="Email address")
    phone: Optional[str] = Field(
        None, 
        pattern=r"^\+?1?\d{10,15}$",
        description="Phone number (10-15 digits)"
    )
    event_date: Optional[date] = Field(None, description="Preferred event date")
    guest_count: Optional[int] = Field(None, ge=1, le=500, description="Number of guests")
    budget: Optional[str] = Field(None, max_length=50, description="Budget range (e.g., $500-1000)")
    location: Optional[str] = Field(None, max_length=200, description="Event location or zip code")
    message: Optional[str] = Field(None, max_length=2000, description="Additional message or questions")
    source: str = Field(default="website", description="Lead source")
    
    # Consent fields
    email_consent: bool = Field(default=False, description="Consent to email contact")
    sms_consent: bool = Field(default=False, description="Consent to SMS contact")
    
    # Spam prevention
    honeypot: Optional[str] = Field(default=None, description="Honeypot field (should be empty)")


class PublicLeadResponse(BaseModel):
    """Public lead submission response"""
    success: bool
    message: str
    lead_id: Optional[str] = None


@router.post("/leads", response_model=PublicLeadResponse, status_code=status.HTTP_201_CREATED)
async def capture_public_lead(
    lead_data: PublicLeadCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Public endpoint to capture leads from website forms
    
    Rate limit: 10 requests/minute per IP
    No authentication required
    
    Use cases:
    - Quote request forms
    - Contact forms
    - "Get a quote" CTAs
    - Newsletter signups with event interest
    """
    try:
        # Spam prevention - honeypot check
        if lead_data.honeypot:
            logger.warning(f"Honeypot triggered from IP {request.client.host}")
            # Return success to not reveal honeypot
            return PublicLeadResponse(
                success=True,
                message="Thank you! We'll be in touch soon."
            )
        
        # Validate at least one contact method
        if not lead_data.email and not lead_data.phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide at least email or phone number"
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
            "google": LeadSource.GOOGLE
        }
        source = source_map.get(lead_data.source.lower(), LeadSource.WEB_QUOTE)
        
        # Create lead service
        lead_service = LeadService(db=db)
        
        # Capture lead using quote request method
        lead = await lead_service.capture_quote_request(
            name=lead_data.name,
            email=lead_data.email,
            phone=lead_data.phone,
            event_date=lead_data.event_date,
            guest_count=lead_data.guest_count,
            budget=lead_data.budget,
            message=lead_data.message,
            location=lead_data.location
        )
        
        logger.info(
            f"Public lead captured: {lead.id} from {request.client.host} "
            f"(name={lead_data.name}, email={lead_data.email}, source={source.value})"
        )
        
        # TODO: Send email notification to admin
        # TODO: Send confirmation email to customer (if consent given)
        
        return PublicLeadResponse(
            success=True,
            message="Thank you! We've received your request and will contact you shortly.",
            lead_id=str(lead.id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error capturing public lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="We're unable to process your request right now. Please try again or call us directly."
        )


@router.post("/leads/failed-booking", response_model=PublicLeadResponse, status_code=status.HTTP_201_CREATED)
async def capture_failed_booking_lead(
    booking_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
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
            "phone": booking_data.get("phone") or booking_data.get("contact_phone")
        }
        
        # Capture failed booking
        lead = await lead_service.capture_failed_booking(
            contact_info=contact_info,
            booking_data=booking_data,
            failure_reason=booking_data.get("failure_reason", "Slot unavailable")
        )
        
        logger.info(f"Failed booking captured as lead: {lead.id}")
        
        return PublicLeadResponse(
            success=True,
            message="We've saved your information and will contact you with alternative dates.",
            lead_id=str(lead.id)
        )
        
    except Exception as e:
        logger.error(f"Error capturing failed booking lead: {e}", exc_info=True)
        # Don't fail the booking flow if lead capture fails
        return PublicLeadResponse(
            success=False,
            message="Unable to save for follow-up, but you can contact us directly."
        )


# Health check for public endpoints
@router.get("/health")
async def public_health_check():
    """Health check for public lead capture endpoint"""
    return {
        "status": "healthy",
        "service": "public-lead-capture",
        "timestamp": datetime.utcnow().isoformat()
    }
