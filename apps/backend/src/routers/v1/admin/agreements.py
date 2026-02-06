"""
Admin Agreements Router
=======================

Admin endpoints for managing legal agreements:
- View all signed agreements
- Get agreement details
- View active slot holds
- Generate signing links for copy-paste
- Send signing links via SMS/email

Roles: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT
"""

import logging
from datetime import date, datetime
from datetime import time as time_type
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.agreements import (
    SlotHoldService,
    get_slot_hold_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/agreements", tags=["Admin - Agreements"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class SignedAgreementSummary(BaseModel):
    """Summary of a signed agreement for list view."""

    id: UUID
    booking_id: Optional[UUID]
    customer_id: UUID
    agreement_type: str
    agreement_version: str
    signed_at: datetime
    signer_name: str
    signer_email: str
    signing_method: str
    confirmation_pdf_url: Optional[str]


class SignedAgreementDetail(BaseModel):
    """Full signed agreement details."""

    id: UUID
    booking_id: Optional[UUID]
    customer_id: UUID
    agreement_type: str
    agreement_version: str
    agreement_text: str
    signed_at: datetime
    signer_name: str
    signer_email: str
    signer_ip_address: Optional[str]
    signing_method: str
    confirmation_pdf_url: Optional[str]
    retention_expires_at: Optional[datetime]


class SignedAgreementsListResponse(BaseModel):
    """Paginated list of signed agreements."""

    agreements: list[SignedAgreementSummary]
    total: int
    page: int
    limit: int
    has_more: bool


class SlotHoldSummary(BaseModel):
    """Summary of an active slot hold."""

    id: UUID
    signing_token: str
    station_id: UUID
    station_name: Optional[str]
    event_date: date
    slot_time: time_type
    customer_email: str
    customer_name: Optional[str]
    status: str
    created_at: datetime
    expires_at: datetime
    agreement_signed_at: Optional[datetime]
    deposit_paid_at: Optional[datetime]
    signing_link_sent_at: Optional[datetime]
    signing_link: str


class SlotHoldsListResponse(BaseModel):
    """List of active slot holds."""

    holds: list[SlotHoldSummary]
    total: int


class GenerateLinkRequest(BaseModel):
    """Request to generate a signing link for a customer."""

    station_id: UUID = Field(..., description="Station for the booking")
    event_date: date = Field(..., description="Event date")
    slot_time: time_type = Field(..., description="Slot time (e.g., 18:00)")
    customer_email: EmailStr = Field(..., description="Customer email")
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_phone: Optional[str] = Field(None, description="Customer phone")
    guest_count: int = Field(10, description="Number of guests")


class GenerateLinkResponse(BaseModel):
    """Response with generated signing link."""

    hold_id: UUID
    signing_token: str
    signing_url: str
    expires_at: datetime
    message: str


class SendLinkRequest(BaseModel):
    """Request to send signing link to customer."""

    hold_id: UUID = Field(..., description="Slot hold ID")
    send_via: str = Field("sms", description="Send method: 'sms' or 'email'")
    phone_number: Optional[str] = Field(None, description="Phone for SMS")
    email: Optional[EmailStr] = Field(None, description="Email address")


class SendLinkResponse(BaseModel):
    """Response after sending link."""

    success: bool
    message: str
    send_count: int
    channel: str


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/signed", response_model=SignedAgreementsListResponse)
async def list_signed_agreements(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    agreement_type: Optional[str] = Query(
        None, description="Filter by type: liability_waiver, allergen_disclosure"
    ),
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    booking_id: Optional[UUID] = Query(None, description="Filter by booking ID"),
    date_from: Optional[date] = Query(None, description="Signed after this date"),
    date_to: Optional[date] = Query(None, description="Signed before this date"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all signed agreements with pagination and filters.

    Roles: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT
    """
    try:
        offset = (page - 1) * limit

        # Build query with filters
        where_clauses = []
        params: Dict[str, Any] = {"limit": limit, "offset": offset}

        if agreement_type:
            where_clauses.append("agreement_type = :agreement_type")
            params["agreement_type"] = agreement_type

        if customer_email:
            where_clauses.append("signer_email ILIKE :customer_email")
            params["customer_email"] = f"%{customer_email}%"

        if booking_id:
            where_clauses.append("booking_id = :booking_id")
            params["booking_id"] = str(booking_id)

        if date_from:
            where_clauses.append("signed_at >= :date_from")
            params["date_from"] = datetime.combine(date_from, time_type.min)

        if date_to:
            where_clauses.append("signed_at <= :date_to")
            params["date_to"] = datetime.combine(date_to, time_type.max)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Get total count
        count_result = await db.execute(
            text(f"SELECT COUNT(*) FROM core.signed_agreements WHERE {where_sql}"),
            params,
        )
        total = count_result.scalar() or 0

        # Get paginated results
        result = await db.execute(
            text(
                f"""
                SELECT id, booking_id, customer_id, agreement_type, agreement_version,
                       signed_at, signer_name, signer_email, signing_method,
                       confirmation_pdf_url
                FROM core.signed_agreements
                WHERE {where_sql}
                ORDER BY signed_at DESC
                LIMIT :limit OFFSET :offset
            """
            ),
            params,
        )

        agreements = [
            SignedAgreementSummary(
                id=row.id,
                booking_id=row.booking_id,
                customer_id=row.customer_id,
                agreement_type=row.agreement_type,
                agreement_version=row.agreement_version,
                signed_at=row.signed_at,
                signer_name=row.signer_name,
                signer_email=row.signer_email,
                signing_method=row.signing_method,
                confirmation_pdf_url=row.confirmation_pdf_url,
            )
            for row in result.fetchall()
        ]

        return SignedAgreementsListResponse(
            agreements=agreements,
            total=int(total),
            page=page,
            limit=limit,
            has_more=(page * limit) < int(total),
        )

    except Exception as e:
        logger.exception(f"Failed to list signed agreements: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list signed agreements",
        )


@router.get("/signed/{agreement_id}", response_model=SignedAgreementDetail)
async def get_signed_agreement(
    agreement_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get full details of a signed agreement.

    Roles: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT
    """
    try:
        result = await db.execute(
            text(
                """
                SELECT id, booking_id, customer_id, agreement_type, agreement_version,
                       agreement_text, signed_at, signer_name, signer_email,
                       signer_ip_address, signing_method, confirmation_pdf_url,
                       retention_expires_at
                FROM core.signed_agreements
                WHERE id = :agreement_id
            """
            ),
            {"agreement_id": str(agreement_id)},
        )

        row = result.fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agreement not found",
            )

        return SignedAgreementDetail(
            id=row.id,
            booking_id=row.booking_id,
            customer_id=row.customer_id,
            agreement_type=row.agreement_type,
            agreement_version=row.agreement_version,
            agreement_text=row.agreement_text,
            signed_at=row.signed_at,
            signer_name=row.signer_name,
            signer_email=row.signer_email,
            signer_ip_address=row.signer_ip_address,
            signing_method=row.signing_method,
            confirmation_pdf_url=row.confirmation_pdf_url,
            retention_expires_at=row.retention_expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get agreement: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agreement",
        )


@router.get("/holds", response_model=SlotHoldsListResponse)
async def list_slot_holds(
    status_filter: Optional[str] = Query(
        None, description="Filter by status: pending, converted, expired, cancelled"
    ),
    include_expired: bool = Query(False, description="Include expired holds"),
    db: AsyncSession = Depends(get_db),
):
    """
    List all slot holds with signing links.

    Roles: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT

    Returns signing links that can be copied and sent to customers.
    """
    try:
        where_clauses = []
        params = {}

        if status_filter:
            where_clauses.append("sh.status = :status_filter")
            params["status_filter"] = status_filter

        if not include_expired:
            where_clauses.append("sh.expires_at > NOW()")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        result = await db.execute(
            text(
                f"""
                SELECT sh.id, sh.signing_token, sh.station_id, s.name as station_name,
                       sh.event_date, sh.slot_time, sh.customer_email, sh.customer_name,
                       sh.status, sh.created_at, sh.expires_at,
                       sh.agreement_signed_at, sh.deposit_paid_at, sh.signing_link_sent_at
                FROM core.slot_holds sh
                LEFT JOIN identity.stations s ON s.id = sh.station_id
                WHERE {where_sql}
                ORDER BY sh.created_at DESC
                LIMIT 100
            """
            ),
            params,
        )

        base_url = "https://myhibachichef.com"
        holds = [
            SlotHoldSummary(
                id=row.id,
                signing_token=str(row.signing_token),
                station_id=row.station_id,
                station_name=row.station_name,
                event_date=row.event_date,
                slot_time=row.slot_time,
                customer_email=row.customer_email,
                customer_name=row.customer_name,
                status=row.status,
                created_at=row.created_at,
                expires_at=row.expires_at,
                agreement_signed_at=row.agreement_signed_at,
                deposit_paid_at=row.deposit_paid_at,
                signing_link_sent_at=row.signing_link_sent_at,
                signing_link=f"{base_url}/sign/{row.signing_token}",
            )
            for row in result.fetchall()
        ]

        return SlotHoldsListResponse(
            holds=holds,
            total=len(holds),
        )

    except Exception as e:
        logger.exception(f"Failed to list slot holds: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list slot holds",
        )


@router.post("/generate-link", response_model=GenerateLinkResponse)
async def generate_signing_link(
    request: GenerateLinkRequest,
    slot_hold_service: SlotHoldService = Depends(get_slot_hold_service),
):
    """
    Generate a signing link for admin to copy and share with customer.

    Use this when:
    - Taking a booking over the phone
    - Customer can't complete online booking
    - Need to manually create a hold for a customer

    The link can be:
    - Copied and pasted to customer via text/WhatsApp
    - Sent via email manually
    - Read over the phone

    Roles: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT
    """
    try:
        logger.info(
            f"Admin generating signing link: station={request.station_id}, "
            f"date={request.event_date}, time={request.slot_time}, "
            f"email={request.customer_email}"
        )

        # Create the slot hold
        hold_result = await slot_hold_service.create_hold(
            station_id=request.station_id,
            event_date=request.event_date,
            slot_time=request.slot_time,
            customer_email=request.customer_email,
            customer_name=request.customer_name,
            guest_count=request.guest_count,
        )

        # Generate signing URL
        base_url = "https://myhibachichef.com"
        signing_url = f"{base_url}/sign/{hold_result['signing_token']}"

        logger.info(f"Generated signing link: hold_id={hold_result['id']}")

        return GenerateLinkResponse(
            hold_id=hold_result["id"],
            signing_token=hold_result["signing_token"],
            signing_url=signing_url,
            expires_at=hold_result["expires_at"],
            message="Signing link generated. Copy and share with customer. Valid for 2 hours.",
        )

    except ValueError as e:
        # Slot unavailable
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Failed to generate signing link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate signing link",
        )


@router.post("/send-link", response_model=SendLinkResponse)
async def send_signing_link_to_customer(
    request: SendLinkRequest,
    db: AsyncSession = Depends(get_db),
    slot_hold_service: SlotHoldService = Depends(get_slot_hold_service),
):
    """
    Send signing link to customer via SMS or email.

    This actually sends the message (when SMS/email services are configured).

    Roles: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT
    """
    try:
        # Get hold details
        result = await db.execute(
            text(
                """
                SELECT id, signing_token, customer_email, customer_name,
                       event_date, slot_time, expires_at, status
                FROM core.slot_holds
                WHERE id = :hold_id
            """
            ),
            {"hold_id": str(request.hold_id)},
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot hold not found",
            )

        if row.status not in ("pending",):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot send link for hold with status: {row.status}",
            )

        # Generate signing URL
        base_url = "https://myhibachichef.com"
        signing_url = f"{base_url}/sign/{row.signing_token}"

        channel = request.send_via.lower()
        send_success = False

        if channel == "sms":
            phone = request.phone_number
            if not phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone number required for SMS",
                )

            # Actually send SMS
            from services.sms_service import send_sms_sync

            message = (
                f"Hi{' ' + row.customer_name if row.customer_name else ''}! "
                f"Please sign your My Hibachi service agreement here: {signing_url} "
                f"(Link expires in 2 hours)"
            )

            send_success = send_sms_sync(to_phone=phone, message=message)

            if send_success:
                logger.info(f"SMS sent to {phone[:4]}*** with signing link")
            else:
                logger.warning(f"SMS failed to send to {phone[:4]}***")

        elif channel == "email":
            email = request.email or row.customer_email
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email required",
                )

            # Actually send email
            from services.email_service import EmailService

            email_service = EmailService()
            customer_name = row.customer_name or "there"

            subject = "Sign Your My Hibachi Service Agreement"
            html_body = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>Hi {customer_name}!</h2>
                <p>Thank you for choosing My Hibachi for your event!</p>
                <p>Please sign your service agreement to confirm your booking:</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{signing_url}"
                       style="background-color: #2563eb; color: white; padding: 15px 30px;
                              text-decoration: none; border-radius: 8px; font-size: 16px;">
                        Sign Agreement Now
                    </a>
                </p>
                <p><strong>Important:</strong> This link expires in 2 hours.</p>
                <p>Event Details:</p>
                <ul>
                    <li>Date: {row.event_date.strftime('%B %d, %Y')}</li>
                    <li>Time: {row.slot_time.strftime('%I:%M %p')}</li>
                </ul>
                <p>Questions? Reply to this email or text us at (916) 740-8768.</p>
                <p>- My Hibachi Team</p>
            </div>
            """
            text_body = (
                f"Hi {customer_name}!\n\n"
                f"Please sign your My Hibachi service agreement: {signing_url}\n\n"
                f"This link expires in 2 hours.\n\n"
                f"- My Hibachi Team"
            )

            send_success = email_service._send_email(
                to_email=email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            if send_success:
                logger.info(f"Email sent to {email} with signing link")
            else:
                logger.warning(f"Email failed to send to {email}")

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="send_via must be 'sms' or 'email'",
            )

        # Record the send
        try:
            link_status = await slot_hold_service.record_signing_link_sent(
                hold_id=row.id,
                channel=channel,
            )
            send_count = link_status["send_count"] if link_status else 1
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=str(e),
            )

        return SendLinkResponse(
            success=send_success,
            message=(f"Signing link {'sent' if send_success else 'attempted'} via {channel}"),
            send_count=send_count,
            channel=channel,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to send signing link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send signing link",
        )


@router.get("/holds/{hold_id}/signing-url")
async def get_hold_signing_url(
    hold_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the signing URL for a specific hold.

    Quick endpoint for admins to get just the URL to copy.

    Roles: SUPER_ADMIN, ADMIN, CUSTOMER_SUPPORT
    """
    try:
        result = await db.execute(
            text(
                """
                SELECT signing_token, status, expires_at
                FROM core.slot_holds
                WHERE id = :hold_id
            """
            ),
            {"hold_id": str(hold_id)},
        )
        row = result.fetchone()

        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hold not found",
            )

        base_url = "https://myhibachichef.com"
        signing_url = f"{base_url}/sign/{row.signing_token}"

        return {
            "signing_url": signing_url,
            "status": row.status,
            "expires_at": row.expires_at.isoformat() if row.expires_at else None,
            "is_valid": row.status == "pending" and row.expires_at > datetime.utcnow(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get signing URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get signing URL",
        )
