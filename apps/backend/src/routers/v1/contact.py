"""
Contact Form API Endpoint
=========================

Public endpoint for website contact form submissions.
Creates a lead and stores contact information for follow-up.

Endpoint:
    POST /api/v1/contact - Submit contact form (public, no auth required)

Related Components:
    - apps/customer/src/components/contact/ContactForm.tsx
    - apps/backend/src/db/models/crm.py (Lead model)
    - apps/backend/src/db/models/lead.py (LeadContact, LeadContext)
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from db.models.crm import Lead, LeadSource, LeadStatus, ContactChannel
from db.models.lead import LeadContact, LeadContext, LeadEvent

logger = logging.getLogger(__name__)
router = APIRouter(tags=["contact"])


class ContactFormRequest(BaseModel):
    """
    Contact form submission payload.

    Matches ContactForm.tsx frontend submission format.
    """

    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    preferred_communication: Optional[str] = Field(None, max_length=50)
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)
    sms_consent: bool = False
    source: str = Field(default="website_contact_form", max_length=100)


class ContactFormResponse(BaseModel):
    """Response after successful contact form submission."""

    success: bool
    message: str
    lead_id: Optional[UUID] = None


@router.post("/", response_model=ContactFormResponse, status_code=status.HTTP_201_CREATED)
async def submit_contact_form(
    request: ContactFormRequest,
    db: AsyncSession = Depends(get_db),
) -> ContactFormResponse:
    """
    Submit a contact form inquiry.

    Creates a new lead with contact information for follow-up.
    This endpoint is public and does not require authentication.

    Args:
        request: Contact form data including name, email, subject, and message

    Returns:
        Success response with lead ID for tracking

    Raises:
        HTTPException: 500 if database operation fails
    """
    try:
        logger.info(f"📧 Contact form submission from: {request.email}, subject: {request.subject}")

        # Create a new lead
        lead = Lead(
            source=LeadSource.WEBSITE,
            status=LeadStatus.NEW,
        )
        db.add(lead)
        await db.flush()  # Get the lead ID

        # Add email contact
        email_contact = LeadContact(
            lead_id=lead.id,
            channel=ContactChannel.EMAIL,
            handle_or_address=request.email,
            verified=False,
        )
        db.add(email_contact)

        # Add phone contact if provided
        if request.phone:
            phone_contact = LeadContact(
                lead_id=lead.id,
                channel=ContactChannel.SMS if request.sms_consent else ContactChannel.PHONE,
                handle_or_address=request.phone,
                verified=False,
            )
            db.add(phone_contact)

        # Add context with message details
        # We store the subject and message in the notes field, and name in notes
        context_notes = (
            f"Name: {request.name}\nSubject: {request.subject}\n\nMessage:\n{request.message}"
        )
        if request.preferred_communication:
            context_notes += f"\n\nPreferred Communication: {request.preferred_communication}"
        if request.sms_consent:
            context_notes += "\n\nSMS Consent: Yes"

        context = LeadContext(
            id=lead.id,  # LeadContext uses lead_id as PK
            notes=context_notes,
            service_type=request.subject,  # Use subject as service_type for categorization
        )
        db.add(context)

        # Add creation event for tracking (create directly, don't use relationship)
        event = LeadEvent(
            lead_id=lead.id,
            event_type="contact_form_submitted",
            payload={
                "source": request.source,
                "subject": request.subject,
                "has_phone": bool(request.phone),
                "sms_consent": request.sms_consent,
            },
        )
        db.add(event)

        await db.commit()

        logger.info(f"✅ Contact form lead created: {lead.id}")

        return ContactFormResponse(
            success=True,
            message="Thank you for your message! We'll be in touch soon.",
            lead_id=lead.id,
        )

    except Exception as e:
        logger.error(f"❌ Contact form submission failed: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit contact form. Please try again later.",
        )
