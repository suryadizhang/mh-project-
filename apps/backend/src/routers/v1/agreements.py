"""
Legal Agreements API Router
===========================

Endpoints for liability waivers, allergen disclosures, and digital signatures.

Part of Legal Protection Implementation (Batch 1.x).
See: docs/04-DEPLOYMENT/LEGAL_PROTECTION_IMPLEMENTATION.md

Endpoints:
    POST /api/v1/agreements/sign          - Sign agreement (online)
    POST /api/v1/agreements/send-link     - Send SMS/email signing link
    GET  /api/v1/agreements/holds/{id}/link-status - Get signing link send status
    GET  /api/v1/agreements/status/{booking_id} - Check if signed
    GET  /api/v1/agreements/templates/{type}    - Get active template
    POST /api/v1/agreements/validate-signature  - Validate signature image
    POST /api/v1/agreements/holds         - Create slot hold
    GET  /api/v1/agreements/holds/{token} - Validate hold token
    DELETE /api/v1/agreements/holds/{token} - Release hold

Flow:
    1. Customer selects date/time → Create slot hold
    2. Customer reviews agreements → Render templates with variables
    3. Customer signs → Validate signature, create signed_agreement
    4. Generate PDF → Upload to R2, send confirmation email
    5. Convert hold to booking → Proceed with deposit
"""

import logging
from datetime import date, datetime
from datetime import time as time_type
from typing import Optional
from uuid import UUID

import markdown
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field, model_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.dependencies import get_booking_service
from services.agreements import (
    AgreementService,
    SigningService,
    SlotHoldService,
    get_agreement_service,
    get_signing_service,
    get_slot_hold_service,
)
from services.agreements.slot_hold_service import (
    DatabaseError,
    SlotHoldError,
    SlotUnavailableError,
)
from services.booking_service import BookingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agreements", tags=["Agreements"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class TemplateResponse(BaseModel):
    """Agreement template response."""

    id: UUID
    agreement_type: str
    version: str
    title: str
    content_rendered: str
    effective_date: date
    requires_signature: bool

    class Config:
        from_attributes = True


class SignAgreementRequest(BaseModel):
    """
    Request to sign an agreement.

    Accepts EITHER hold_token (pre-booking flow) OR booking_id (post-booking flow).
    Exactly one must be provided.
    """

    # One of these is required (validated below)
    hold_token: Optional[str] = Field(
        None, description="Slot hold token from hold creation (pre-booking flow)"
    )
    booking_id: Optional[UUID] = Field(None, description="Existing booking ID (post-booking flow)")

    agreement_type: str = Field(
        ..., description="Type: 'liability_waiver' or 'allergen_disclosure'"
    )
    signature_image_base64: str = Field(
        ..., description="Base64-encoded signature image (PNG/JPEG/WEBP)"
    )
    typed_name: Optional[str] = Field(
        None, description="Typed name if signature is typed instead of drawn"
    )
    customer_email: EmailStr = Field(..., description="Customer email for confirmation")
    customer_name: str = Field(..., description="Customer full name")

    # Allergen-specific fields (only for allergen_disclosure)
    allergens: Optional[list[str]] = Field(
        None, description="List of allergen codes for disclosure"
    )
    allergen_notes: Optional[str] = Field(
        None, description="Additional allergen notes from customer"
    )

    @model_validator(mode="after")
    def validate_identifier(self) -> "SignAgreementRequest":
        """Ensure exactly one of hold_token or booking_id is provided."""
        if self.hold_token and self.booking_id:
            raise ValueError("Provide EITHER hold_token OR booking_id, not both")
        if not self.hold_token and not self.booking_id:
            raise ValueError("Must provide either hold_token or booking_id")
        return self


class SignAgreementResponse(BaseModel):
    """Response after signing agreement."""

    agreement_id: UUID
    signed_at: datetime
    pdf_url: Optional[str] = None
    confirmation_sent: bool
    message: str


class SlotHoldRequest(BaseModel):
    """Request to create a slot hold."""

    station_id: UUID = Field(..., description="Station UUID")
    event_date: date = Field(..., description="Event date")
    slot_time: time_type = Field(..., description="Slot time (e.g., 18:00)")
    customer_email: EmailStr = Field(..., description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone (optional)")

    @model_validator(mode="after")
    def validate_dates(self) -> "SlotHoldRequest":
        """Ensure event date is in the future."""
        from datetime import date as date_module

        today = date_module.today()
        if self.event_date < today:
            raise ValueError("Event date must be in the future")
        return self


class SlotHoldResponse(BaseModel):
    """Response after creating slot hold."""

    hold_id: UUID
    signing_token: str
    expires_at: datetime
    signing_url: str
    message: str


class SlotHoldStatusResponse(BaseModel):
    """
    DEPRECATED: Old response format.
    Kept for backward compatibility. Use SigningPageResponse instead.
    """

    hold_id: UUID
    status: str
    station_id: UUID
    event_date: date
    slot_time: time_type
    expires_at: datetime
    is_valid: bool
    agreements_signed: list[str]


# =============================================================================
# New Response Schemas for Signing Page (matches frontend expectations)
# =============================================================================


class HoldInfoResponse(BaseModel):
    """Hold info for signing page - matches frontend HoldInfo interface."""

    id: str
    station_id: str
    station_name: str
    slot_datetime: str  # ISO format datetime string
    customer_email: str
    expires_at: str  # ISO format datetime string
    status: str  # 'pending' | 'converted' | 'expired' | 'cancelled'
    agreement_signed: bool
    deposit_paid: bool


class AgreementContentResponse(BaseModel):
    """Agreement content for signing page - matches frontend AgreementContent interface."""

    title: str
    content_html: str
    version: str
    effective_date: str  # ISO format date string


class SigningPageResponse(BaseModel):
    """
    Response for signing page - wrapped structure matching frontend expectations.

    Used by: apps/customer/src/app/sign/[token]/page.tsx
    """

    success: bool
    hold: Optional[HoldInfoResponse] = None
    agreement: Optional[AgreementContentResponse] = None
    error_code: Optional[str] = None  # e.g., 'SLOT_HOLD_EXPIRED', 'SLOT_HOLD_NOT_FOUND'


class SendLinkRequest(BaseModel):
    """Request to send signing link via SMS/email."""

    hold_token: str = Field(..., description="Slot hold token")
    send_via: str = Field("sms", description="Send method: 'sms' or 'email'")
    phone_number: Optional[str] = Field(None, description="Phone for SMS")
    email: Optional[EmailStr] = Field(None, description="Email for email link")


class AgreementStatusResponse(BaseModel):
    """Response for agreement status check."""

    booking_id: UUID
    liability_waiver_signed: bool
    allergen_disclosure_signed: bool
    all_required_signed: bool
    signed_at: Optional[datetime] = None


class ValidateSignatureRequest(BaseModel):
    """Request to validate signature image."""

    signature_image_base64: str = Field(..., description="Base64-encoded signature")


class ValidateSignatureResponse(BaseModel):
    """Response for signature validation."""

    is_valid: bool
    error: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    format: Optional[str] = None


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/templates/{agreement_type}", response_model=TemplateResponse)
async def get_agreement_template(
    agreement_type: str,
    station_id: Optional[UUID] = Query(None, description="Station for variable interpolation"),
    agreement_service: AgreementService = Depends(get_agreement_service),
) -> TemplateResponse:
    """
    Get the active agreement template with variables rendered.

    Agreement types:
    - `liability_waiver`: Service agreement and liability release
    - `allergen_disclosure`: Allergen acknowledgment and disclosure

    Variables are interpolated from database (SSoT) values.
    """
    try:
        # Service method: get_active_template(self, agreement_type: str) -> dict | None
        template = await agreement_service.get_active_template(agreement_type)

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No active template found for type: {agreement_type}",
            )

        # Service method: render_template(self, template: dict, additional_vars: dict | None) -> str
        additional_vars = {"STATION_ID": str(station_id)} if station_id else None
        rendered_content = await agreement_service.render_template(
            template=template,
            additional_vars=additional_vars,
        )

        return TemplateResponse(
            id=template["id"],
            agreement_type=template["agreement_type"],
            version=template["version"],
            title=template["title"],
            content_rendered=rendered_content,
            effective_date=template["effective_date"],
            requires_signature=template.get("requires_signature", True),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agreement template",
        )


class SlotHoldErrorCode:
    """Error codes for slot hold operations - for debugging and frontend handling."""

    SLOT_UNAVAILABLE = "SLOT_UNAVAILABLE"
    STATION_NOT_FOUND = "STATION_NOT_FOUND"
    INVALID_DATE = "INVALID_DATE"
    INVALID_TIME = "INVALID_TIME"
    DATABASE_ERROR = "DATABASE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@router.post("/holds", response_model=SlotHoldResponse)
async def create_slot_hold(
    request: SlotHoldRequest,
    slot_hold_service: SlotHoldService = Depends(get_slot_hold_service),
) -> SlotHoldResponse:
    """
    Create a temporary slot hold while customer signs agreements.

    Hold expires in 2 hours if not converted to booking.
    This prevents double-booking during the signing process.

    Error Codes:
    - SLOT_UNAVAILABLE: Slot already booked or held
    - STATION_NOT_FOUND: Invalid station_id
    - INVALID_DATE: Event date in past
    - DATABASE_ERROR: Database operation failed
    """
    try:
        # Log request for debugging (no PII in production)
        logger.info(
            f"Creating slot hold: station={request.station_id}, "
            f"date={request.event_date}, time={request.slot_time}"
        )

        # Create hold with separate event_date and slot_time
        # Service stores them in slot_holds table columns: event_date (DATE), slot_time (TIME)
        hold_result = await slot_hold_service.create_hold(
            station_id=request.station_id,
            event_date=request.event_date,
            slot_time=request.slot_time,
            customer_email=request.customer_email,
        )

        # TODO: Replace with actual frontend URL from settings
        base_url = "https://myhibachichef.com"
        signing_url = f"{base_url}/sign/{hold_result['signing_token']}"

        logger.info(f"Slot hold created: hold_id={hold_result['id']}")

        return SlotHoldResponse(
            hold_id=hold_result["id"],
            signing_token=hold_result["signing_token"],
            expires_at=hold_result["expires_at"],
            signing_url=signing_url,
            message="Slot held for 2 hours. Complete agreements to confirm booking.",
        )

    except SlotUnavailableError as e:
        logger.warning(f"Slot unavailable: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": e.error_code,
                "message": e.message,
            },
        )
    except DatabaseError as e:
        logger.error(f"Database error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": e.error_code,
                "message": "Database error occurred. Please try again.",
            },
        )
    except SlotHoldError as e:
        # Catch any other slot hold errors
        logger.error(f"Slot hold error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": e.error_code,
                "message": e.message,
            },
        )
    except ValueError as e:
        # Backward compatibility for old ValueError raises
        error_msg = str(e)
        logger.warning(f"Slot hold validation error: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": SlotHoldErrorCode.SLOT_UNAVAILABLE,
                "message": error_msg,
            },
        )
    except Exception as e:
        # Log full exception for debugging but return safe message
        logger.exception(
            f"Failed to create slot hold: {e}\n"
            f"Request: station={request.station_id}, date={request.event_date}, time={request.slot_time}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": SlotHoldErrorCode.INTERNAL_ERROR,
                "message": "Failed to create slot hold. Please try again.",
            },
        )


@router.get("/holds/{token}", response_model=SigningPageResponse)
async def get_hold_status(
    token: str,
    db: AsyncSession = Depends(get_db),
    slot_hold_service: SlotHoldService = Depends(get_slot_hold_service),
    agreement_service: AgreementService = Depends(get_agreement_service),
) -> SigningPageResponse:
    """
    Check the status of a slot hold by token.

    Returns hold details, station info, and agreement content for the signing page.

    Response matches frontend SigningPageResponse interface:
    - success: boolean
    - hold: HoldInfo (id, station_id, station_name, slot_datetime, customer_email, ...)
    - agreement: AgreementContent (title, content_html, version, effective_date)
    - error_code: optional error code (SLOT_HOLD_EXPIRED, SLOT_HOLD_NOT_FOUND)
    """
    try:
        # Validate token is a valid UUID format (defense against malformed tokens)
        try:
            from uuid import UUID as UUIDType

            UUIDType(token)  # Raises ValueError if invalid
        except ValueError:
            logger.warning(f"Invalid token format received: {token[:20]}...")
            return SigningPageResponse(
                success=False,
                error_code="INVALID_TOKEN_FORMAT",
            )

        # Service method: validate_hold(self, signing_token: str) -> dict | None
        # Returns: {id, station_id, slot_datetime, customer_email, customer_id, status, expires_at, created_at}
        hold = await slot_hold_service.validate_hold(signing_token=token)

        if not hold:
            return SigningPageResponse(
                success=False,
                error_code="SLOT_HOLD_NOT_FOUND",
            )

        # Check if hold is expired or invalid
        if hold["status"] != "pending":
            error_code = (
                "SLOT_HOLD_EXPIRED"
                if hold["status"] == "expired"
                else f"SLOT_HOLD_{hold['status'].upper()}"
            )
            return SigningPageResponse(
                success=False,
                error_code=error_code,
            )

        # Query station name from identity.stations
        station_result = await db.execute(
            text("SELECT name FROM identity.stations WHERE id = :station_id"),
            {"station_id": hold["station_id"]},
        )
        station_row = station_result.fetchone()
        station_name = station_row.name if station_row else "Unknown Station"

        # Get agreement template (liability_waiver is the primary agreement)
        template = await agreement_service.get_active_template("liability_waiver")
        if not template:
            logger.error("No active liability_waiver template found")
            return SigningPageResponse(
                success=False,
                error_code="AGREEMENT_TEMPLATE_NOT_FOUND",
            )

        # Render template with business config values
        rendered_markdown = await agreement_service.render_template(template)

        # Convert markdown to HTML
        content_html = markdown.markdown(rendered_markdown, extensions=["tables", "nl2br"])

        # Format slot datetime from separate event_date and slot_time fields
        event_date = hold["event_date"]
        slot_time = hold["slot_time"]
        # Combine date and time into datetime string
        slot_datetime_str = f"{event_date}T{slot_time}"

        # Format expires_at as ISO string
        expires_at = hold["expires_at"]
        if hasattr(expires_at, "isoformat"):
            expires_at_str = expires_at.isoformat()
        else:
            expires_at_str = str(expires_at)

        # Build response
        hold_info = HoldInfoResponse(
            id=str(hold["id"]),
            station_id=str(hold["station_id"]),
            station_name=station_name,
            slot_datetime=slot_datetime_str,
            customer_email=hold["customer_email"],
            expires_at=expires_at_str,
            status=hold["status"],
            agreement_signed=False,  # Not signed yet if they're on this page
            deposit_paid=False,  # Not paid yet if they're in signing flow
        )

        agreement_content = AgreementContentResponse(
            title=template["title"],
            content_html=content_html,
            version=template["version"],
            effective_date=(
                template["effective_date"].isoformat()
                if hasattr(template["effective_date"], "isoformat")
                else str(template["effective_date"])
            ),
        )

        return SigningPageResponse(
            success=True,
            hold=hold_info,
            agreement=agreement_content,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get hold status: {e}")
        return SigningPageResponse(
            success=False,
            error_code="INTERNAL_ERROR",
        )


@router.delete("/holds/{token}")
async def release_hold(
    token: str,
    slot_hold_service: SlotHoldService = Depends(get_slot_hold_service),
):
    """
    Release a slot hold (cancel signing process).

    Call this if customer abandons the signing flow.
    """
    try:
        # First validate the token to get the hold_id
        # Service method: validate_hold(signing_token: str) -> dict | None
        hold = await slot_hold_service.validate_hold(signing_token=token)

        if not hold:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hold not found or already released",
            )

        # Service method: release_hold(hold_id: UUID, reason: str) -> bool
        released = await slot_hold_service.release_hold(hold_id=hold["id"], reason="released")

        if not released:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hold not found or already released",
            )

        return {"message": "Slot hold released successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to release hold: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to release hold",
        )


@router.post("/validate-signature", response_model=ValidateSignatureResponse)
async def validate_signature(
    request: ValidateSignatureRequest,
    signing_service: SigningService = Depends(get_signing_service),
) -> ValidateSignatureResponse:
    """
    Validate a signature image before submission.

    Checks:
    - Format (PNG/JPEG/WEBP)
    - Size (max 500KB)
    - Dimensions (100-2000px width, 50-1000px height)
    - Not blank/empty
    """
    try:
        import base64

        # Decode base64 to bytes for service
        try:
            signature_bytes = base64.b64decode(request.signature_image_base64)
        except Exception:
            return ValidateSignatureResponse(
                is_valid=False,
                error="Invalid base64 signature data",
            )

        # Service method: validate_signature_image(signature_bytes: bytes) -> dict
        # Returns: {valid: bool, error?: str, format?: str, size?: tuple}
        result = signing_service.validate_signature_image(signature_bytes=signature_bytes)

        width, height = None, None
        if result.get("size"):
            width, height = result["size"]

        return ValidateSignatureResponse(
            is_valid=result.get("valid", False),
            error=result.get("error"),
            width=width,
            height=height,
            format=result.get("format"),
        )

    except Exception as e:
        logger.exception(f"Signature validation error: {e}")
        return ValidateSignatureResponse(
            is_valid=False,
            error="Failed to process signature image",
        )


@router.post("/sign", response_model=SignAgreementResponse)
async def sign_agreement(
    request: SignAgreementRequest,
    background_tasks: BackgroundTasks,
    agreement_service: AgreementService = Depends(get_agreement_service),
    signing_service: SigningService = Depends(get_signing_service),
    slot_hold_service: SlotHoldService = Depends(get_slot_hold_service),
    booking_service: BookingService = Depends(get_booking_service),
) -> SignAgreementResponse:
    """
    Sign an agreement digitally.

    Accepts EITHER:
    - hold_token: Pre-booking flow (slot hold before booking created)
    - booking_id: Post-booking flow (signing after booking exists)

    Process:
    1. Validate hold_token OR fetch booking by booking_id
    2. Validate signature image
    3. Get active template
    4. Create signed_agreement record (immutable)
    5. Generate PDF with signature embedded (background)
    6. Send confirmation email with PDF link (background)

    Allergen information is stored in the booking record, not a separate table.
    """
    try:
        # 1. Validate identifier (hold_token OR booking_id)
        customer_id = None
        station_id = None
        actual_booking_id = None

        if request.hold_token:
            # Pre-booking flow: validate slot hold
            hold = await slot_hold_service.validate_hold(request.hold_token)
            if not hold:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired hold token",
                )
            customer_id = hold.get("customer_id")
            station_id = hold.get("station_id")
            actual_booking_id = None  # No booking yet

        elif request.booking_id:
            # Post-booking flow: fetch booking details
            booking = await booking_service.get_booking_by_id(request.booking_id)
            if not booking:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Booking not found: {request.booking_id}",
                )
            customer_id = booking.customer_id
            station_id = booking.station_id
            actual_booking_id = request.booking_id

        # 2. Validate signature (decode base64 to bytes)
        import base64

        try:
            signature_bytes = base64.b64decode(request.signature_image_base64)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid base64 signature image",
            )

        validation_result = signing_service.validate_signature_image(signature_bytes)
        if not validation_result.get("valid"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid signature: {validation_result.get('error', 'Unknown error')}",
            )

        # 3. Get active template
        template = await agreement_service.get_active_template(request.agreement_type)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No active template for: {request.agreement_type}",
            )

        # 4. Render template content with station-specific values
        additional_vars = {"station_id": str(station_id)} if station_id else None
        rendered_content = await agreement_service.render_template(template, additional_vars)

        # 5. Create signed agreement
        # Build signer_info from request
        signer_info = {
            "name": request.customer_name,
            "email": request.customer_email,
            "ip_address": None,  # TODO: Extract from request headers
            "user_agent": None,  # TODO: Extract from request headers
            "device_fingerprint": None,
        }

        signed_agreement = await agreement_service.create_signed_agreement(
            booking_id=actual_booking_id,  # UUID if post-booking, None if pre-booking
            customer_id=customer_id,
            agreement_type=request.agreement_type,
            agreement_version=template.get("version", "1.0"),
            rendered_text=rendered_content,
            signature_image=signature_bytes,
            signature_typed_name=request.typed_name,
            signer_info=signer_info,
            signing_method="online",
        )

        # 6. Generate PDF and send email in background (non-blocking)
        agreement_id = signed_agreement.get("id")

        async def generate_pdf_and_email():
            """Background task to generate PDF and send confirmation email."""
            try:
                await signing_service.generate_and_store_pdf(agreement_id)
                await signing_service.send_confirmation_email(agreement_id)
            except Exception as e:
                logger.error(f"Background PDF/email task failed: {e}")

        background_tasks.add_task(generate_pdf_and_email)

        return SignAgreementResponse(
            agreement_id=agreement_id,
            signed_at=signed_agreement.get("signed_at"),
            pdf_url=None,  # PDF generated in background
            confirmation_sent=False,  # Email sent in background
            message="Agreement signed successfully. Confirmation email will be sent shortly.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to sign agreement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process agreement signing",
        )


@router.get("/status/{booking_id}", response_model=AgreementStatusResponse)
async def get_agreement_status(
    booking_id: UUID,
    agreement_service: AgreementService = Depends(get_agreement_service),
) -> AgreementStatusResponse:
    """
    Check which agreements have been signed for a booking.

    Returns status of liability waiver and allergen disclosure.
    """
    try:
        liability_signed = await agreement_service.has_signed_agreement(
            booking_id=booking_id, agreement_type="liability_waiver"
        )
        allergen_signed = await agreement_service.has_signed_agreement(
            booking_id=booking_id, agreement_type="allergen_disclosure"
        )

        # Get most recent signature time
        signed_at = None
        if liability_signed or allergen_signed:
            agreements = await agreement_service.get_agreements_for_booking(booking_id)
            if agreements:
                # Extract signed_at - agreements are dicts
                signed_at = max(a.get("signed_at") for a in agreements if a.get("signed_at"))

        return AgreementStatusResponse(
            booking_id=booking_id,
            liability_waiver_signed=liability_signed,
            allergen_disclosure_signed=allergen_signed,
            all_required_signed=liability_signed and allergen_signed,
            signed_at=signed_at,
        )

    except Exception as e:
        logger.exception(f"Failed to check agreement status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check agreement status",
        )


@router.post("/send-link")
async def send_signing_link(
    request: SendLinkRequest,
    slot_hold_service: SlotHoldService = Depends(get_slot_hold_service),
):
    """
    Send agreement signing link via SMS or email.

    Used for phone bookings where customer signs later.
    Rate limited to 5 sends per hold (enforced by database).
    """
    try:
        # Validate hold
        hold = await slot_hold_service.validate_hold(request.hold_token)
        if not hold:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired hold token",
            )

        # TODO: Replace with actual frontend URL from settings
        base_url = "https://myhibachichef.com"
        signing_url = f"{base_url}/sign/{request.hold_token}"

        # Determine channel
        channel = request.send_via.lower()

        if channel == "sms":
            if not request.phone_number:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number required for SMS",
                )
            # TODO: Integrate with SMS service (RingCentral)
            # await sms_service.send_signing_link(request.phone_number, signing_url)
            logger.info(f"Would send SMS signing link to {request.phone_number}: {signing_url}")

        elif channel == "email":
            if not request.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email required for email link",
                )
            # TODO: Integrate with email service (Resend)
            # await email_service.send_signing_link(request.email, signing_url)
            logger.info(f"Would send email signing link to {request.email}: {signing_url}")

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="send_via must be 'sms' or 'email'",
            )

        # Record the send in database for tracking
        try:
            link_status = await slot_hold_service.record_signing_link_sent(
                hold_id=hold["id"],
                channel=channel,
            )
            send_count = link_status["send_count"] if link_status else 1
        except ValueError as e:
            # Rate limit exceeded
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e),
            )

        return {
            "message": f"Signing link sent via {request.send_via}",
            "signing_url": signing_url,  # Also return URL for testing
            "send_count": send_count,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to send signing link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send signing link",
        )


@router.get("/holds/{hold_id}/link-status")
async def get_signing_link_status(
    hold_id: UUID,
    slot_hold_service: SlotHoldService = Depends(get_slot_hold_service),
):
    """
    Get the signing link send status for a slot hold.

    Used by admin dashboard to see if/when links were sent.
    """
    try:
        status_info = await slot_hold_service.get_signing_link_status(hold_id)
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot hold not found",
            )

        return status_info

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get link status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get signing link status",
        )
