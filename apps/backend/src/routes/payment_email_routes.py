"""
Payment Email Notification API Endpoints

Endpoints for managing automatic payment notification email processing:
- Check for new payment emails
- View recent notifications
- Manually process/match payments
- View unmatched notifications
"""

from datetime import datetime, timedelta
import logging

from core.config import get_settings
from core.database import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from services.payment_email_monitor import PaymentEmailMonitor
from sqlalchemy.orm import Session

settings = get_settings()
from middleware.auth import require_roles
from models.user import UserRole
from services.email_service import EmailService
from services.notification_service import NotificationService
from services.payment_matcher_service import PaymentEmailService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/payments/email-notifications", tags=["Payment Email Notifications"]
)


# Pydantic models
class EmailNotificationResponse(BaseModel):
    """Payment email notification details"""

    email_id: str
    provider: str
    amount: float
    status: str
    subject: str
    from_email: str = Field(alias="from")
    received_at: str
    transaction_id: str | None = None
    sender_username: str | None = None
    sender_name: str | None = None
    payment_type: str | None = None
    parsed_at: str

    class Config:
        populate_by_name = True


class ProcessEmailsRequest(BaseModel):
    """Request to process payment emails"""

    since_hours: int = Field(
        default=24, ge=1, le=168, description="Process emails from last N hours"
    )
    auto_confirm: bool = Field(default=True, description="Automatically confirm matched payments")
    mark_as_read: bool = Field(default=True, description="Mark processed emails as read")


class ProcessEmailsResponse(BaseModel):
    """Results of email processing"""

    success: bool
    emails_found: int
    emails_parsed: int
    payments_matched: int
    payments_confirmed: int
    errors: list[dict]
    processed_at: str


class ManualMatchRequest(BaseModel):
    """Manually match email notification to payment"""

    email_id: str = Field(description="Email ID from notification")
    payment_id: str = Field(description="Payment ID to match")
    confirm_payment: bool = Field(default=True, description="Confirm payment after matching")


class ManualMatchResponse(BaseModel):
    """Manual match result"""

    success: bool
    payment_id: str
    booking_id: str | None
    message: str


# Dependency: Get email monitor
def get_email_monitor() -> PaymentEmailMonitor:
    """Get configured email monitor instance"""
    try:
        monitor = PaymentEmailMonitor(
            email_address=settings.GMAIL_USER,
            app_password=settings.GMAIL_APP_PASSWORD,
        )
        return monitor
    except Exception as e:
        logger.exception(f"Failed to initialize email monitor: {e}")
        raise HTTPException(status_code=500, detail="Email monitoring not configured")


# Dependency: Get payment email service
def get_payment_email_service(
    db: Session = Depends(get_db),
    email_monitor: PaymentEmailMonitor = Depends(get_email_monitor),
) -> PaymentEmailService:
    """Get payment email service instance"""
    email_service = EmailService()
    notify_service = NotificationService()

    return PaymentEmailService(
        db=db,
        email_monitor=email_monitor,
        email_service=email_service,
        notify_service=notify_service,
    )


@router.post("/process", response_model=ProcessEmailsResponse)
async def process_payment_emails(
    request: ProcessEmailsRequest,
    background_tasks: BackgroundTasks,
    service: PaymentEmailService = Depends(get_payment_email_service),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Process unread payment notification emails

    **Admin only** - Checks Gmail inbox for payment notifications from Stripe, Venmo, Zelle, BofA.
    Automatically matches notifications to pending payments and confirms them.

    **Processing steps:**
    1. Fetch unread emails from payment providers
    2. Parse payment details (amount, transaction ID, etc.)
    3. Match to pending payments in database
    4. Auto-confirm matched payments (if enabled)
    5. Send confirmation emails and admin notifications
    6. Mark processed emails as read (if enabled)

    **Returns:**
    - Number of emails found/processed
    - Number of payments matched/confirmed
    - List of any errors encountered
    """
    try:
        since_date = datetime.utcnow() - timedelta(hours=request.since_hours)

        results = service.process_payment_emails(
            since_date=since_date,
            auto_confirm=request.auto_confirm,
            mark_as_read=request.mark_as_read,
        )

        return ProcessEmailsResponse(
            success=len(results["errors"]) == 0,
            emails_found=results["emails_found"],
            emails_parsed=results["emails_parsed"],
            payments_matched=results["payments_matched"],
            payments_confirmed=results["payments_confirmed"],
            errors=results["errors"],
            processed_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.exception(f"Error processing payment emails: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent", response_model=list[EmailNotificationResponse])
async def get_recent_notifications(
    since_hours: int = 24,
    limit: int = 50,
    email_monitor: PaymentEmailMonitor = Depends(get_email_monitor),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Get recent payment notification emails (read or unread)

    **Admin only** - View payment notification emails from the last N hours.
    Useful for monitoring incoming payments and troubleshooting matching issues.

    **Query parameters:**
    - `since_hours`: Get emails from last N hours (default: 24, max: 168)
    - `limit`: Maximum number of emails to return (default: 50, max: 100)

    **Returns:**
    List of parsed payment notifications with details:
    - Provider (Stripe, Venmo, Zelle, BofA)
    - Amount received
    - Transaction ID (if available)
    - Sender information
    - Email metadata (subject, from, received date)
    """
    try:
        since_date = datetime.utcnow() - timedelta(hours=min(since_hours, 168))

        notifications = email_monitor.get_unread_payment_emails(
            since_date=since_date,
            limit=min(limit, 100),
        )

        return [EmailNotificationResponse(**notif) for notif in notifications]

    except Exception as e:
        logger.exception(f"Error fetching notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unmatched", response_model=list[EmailNotificationResponse])
async def get_unmatched_notifications(
    since_hours: int = 48,
    service: PaymentEmailService = Depends(get_payment_email_service),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Get payment notifications that couldn't be auto-matched

    **Admin only** - View payment emails that were received but couldn't be automatically
    matched to any pending payment in the system. These require manual review.

    **Common reasons for unmatched notifications:**
    - Customer paid without creating a booking first
    - Amount doesn't match any pending payment (within $1 tolerance)
    - Payment received outside 24-hour time window
    - Wrong payment method used (e.g., Venmo instead of Stripe)

    **Query parameters:**
    - `since_hours`: Check emails from last N hours (default: 48, max: 168)

    **Returns:**
    List of unmatched payment notifications that need manual processing
    """
    try:
        since_date = datetime.utcnow() - timedelta(hours=min(since_hours, 168))

        unmatched = service.get_unmatched_notifications(since_date=since_date)

        return [EmailNotificationResponse(**notif) for notif in unmatched]

    except Exception as e:
        logger.exception(f"Error fetching unmatched notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/manual-match", response_model=ManualMatchResponse)
async def manual_match_payment(
    request: ManualMatchRequest,
    service: PaymentEmailService = Depends(get_payment_email_service),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Manually match an email notification to a payment

    **Admin only** - For cases where automatic matching failed, manually link
    a payment notification email to a specific payment record.

    **Use cases:**
    - Customer paid with different amount than expected
    - Payment received outside normal time window
    - Multiple pending payments with similar amounts
    - Need to override automatic matching logic

    **Request body:**
    - `email_id`: Email ID from notification (get from `/recent` or `/unmatched`)
    - `payment_id`: Payment record ID to match
    - `confirm_payment`: Automatically confirm payment after matching (default: true)

    **Returns:**
    - Success status
    - Payment ID and Booking ID
    - Confirmation message
    """
    try:
        from models.booking import Payment
        from services.payment_matcher_service import PaymentMatcher

        # Get payment
        payment = service.db.query(Payment).filter(Payment.id == request.payment_id).first()

        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        # Get email notification (to extract metadata)
        notifications = service.email_monitor.get_unread_payment_emails(limit=100)
        notification = next((n for n in notifications if n["email_id"] == request.email_id), None)

        if not notification:
            raise HTTPException(status_code=404, detail="Email notification not found")

        # Confirm payment
        if request.confirm_payment:
            success = PaymentMatcher.confirm_payment(
                db=service.db,
                payment=payment,
                notification_data=notification,
                email_service=service.email_service,
                notify_service=service.notify_service,
            )

            if not success:
                raise HTTPException(status_code=500, detail="Failed to confirm payment")

            # Mark email as read
            service.email_monitor.mark_as_read(request.email_id)

            return ManualMatchResponse(
                success=True,
                payment_id=payment.id,
                booking_id=payment.booking_id if payment.booking else None,
                message="Payment confirmed and matched to email notification",
            )
        else:
            return ManualMatchResponse(
                success=True,
                payment_id=payment.id,
                booking_id=payment.booking_id if payment.booking else None,
                message="Payment matched but not confirmed (confirm_payment=false)",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in manual match: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_email_monitoring_status(
    email_monitor: PaymentEmailMonitor = Depends(get_email_monitor),
    current_user=Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
):
    """
    Check email monitoring service status

    **Admin only** - Verify that email monitoring is properly configured
    and can connect to Gmail IMAP.

    **Returns:**
    - Connection status (connected/disconnected)
    - Email address being monitored
    - Configuration details
    - Last check time
    """
    try:
        # Test connection
        connected = email_monitor.connect()

        if connected:
            email_monitor.disconnect()

        return {
            "status": "connected" if connected else "disconnected",
            "email_address": email_monitor.email_address,
            "imap_server": email_monitor.imap_server,
            "configured": bool(email_monitor.app_password),
            "last_checked": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.exception(f"Error checking status: {e}")
        return {
            "status": "error",
            "email_address": email_monitor.email_address,
            "error": str(e),
            "last_checked": datetime.utcnow().isoformat(),
        }


# Include router in main app
def include_router(app):
    """Include email notification router in FastAPI app"""
    app.include_router(router)
    logger.info("✅ Payment Email Notification endpoints included")
