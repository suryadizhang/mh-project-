"""
Meta (Facebook/Instagram) webhook router - REFACTORED VERSION

This router is now a thin layer that delegates all business logic to MetaWebhookHandler.
Reduced from 337 lines to ~80 lines by extracting logic to webhook_service.py.

Benefits:
- Route handler is just routing (as it should be)
- Business logic in testable service layer
- Easy to mock webhook_service in tests
- Consistent with DI architecture
"""

import json
import logging
from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
)

from core.config import get_settings
from core.dependencies import get_db, get_lead_service, get_event_service
from services.webhook_service import MetaWebhookHandler
from services.lead_service import LeadService
from services.event_service import EventService
from sqlalchemy.ext.asyncio import AsyncSession


settings = get_settings()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/meta", tags=["webhooks", "social"])


async def get_meta_webhook_handler(
    db: AsyncSession = Depends(get_db),
    lead_service: LeadService = Depends(get_lead_service),
    event_service: EventService = Depends(get_event_service),
) -> MetaWebhookHandler:
    """
    Dependency injection provider for MetaWebhookHandler.

    Returns:
        MetaWebhookHandler with all dependencies injected
    """
    return MetaWebhookHandler(
        db=db,
        lead_service=lead_service,
        event_service=event_service,
    )


@router.get("")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    """
    Verify Meta webhook during setup.

    Meta sends a GET request with these parameters during webhook registration.
    We must return the challenge value if the verify token matches.

    IMPORTANT: Meta sends verification to the SAME URL as webhook posts.
    This must be at the root of the router prefix (e.g., /api/v1/webhooks/meta)

    Args:
        hub_mode: Should be 'subscribe'
        hub_verify_token: Token to verify against our configured token
        hub_challenge: Challenge string to echo back

    Returns:
        Challenge as plain text (Meta expects this format)

    Raises:
        HTTPException: If verification fails
    """
    logger.info(f"Meta webhook verification request: mode={hub_mode}")

    # Get verify token from settings (supports GSM)
    expected_token = settings.META_VERIFY_TOKEN

    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("✅ Meta webhook verification successful")
        # Meta expects the challenge as plain text response
        from fastapi.responses import PlainTextResponse

        return PlainTextResponse(content=hub_challenge)
    else:
        logger.warning(
            f"❌ Meta webhook verification failed: mode={hub_mode}, token_match={hub_verify_token == expected_token}"
        )
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def meta_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    webhook_handler: MetaWebhookHandler = Depends(get_meta_webhook_handler),
    x_hub_signature_256: Optional[str] = Header(None),
):
    """
    Handle Meta (Facebook/Instagram) webhooks.

    Processes:
    - Instagram direct messages
    - Facebook Messenger messages
    - Lead generation ad submissions
    - Page messaging events

    All business logic is in MetaWebhookHandler for testability.

    Args:
        request: FastAPI request object (for raw body)
        background_tasks: FastAPI background tasks (for async processing)
        webhook_handler: Injected MetaWebhookHandler
        x_hub_signature_256: Meta webhook signature header

    Returns:
        Processing result from webhook handler

    Raises:
        HTTPException: If signature is invalid or processing fails
    """
    try:
        # Get raw body for signature verification
        payload = await request.body()

        # Parse webhook data
        webhook_data = json.loads(payload.decode())

        # Delegate all processing to service layer
        result = await webhook_handler.handle_webhook(
            payload=payload,
            signature=x_hub_signature_256 or "",
            secret=settings.META_APP_SECRET,
            data=webhook_data,
        )

        logger.info(
            f"Processed Meta webhook: {result.get('event_type')} "
            f"({result.get('processed', 0)} events)"
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions (signature failures, etc.)
        raise
    except Exception as e:
        # Log and return 500 for unexpected errors
        logger.error(f"Unexpected error in Meta webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error processing webhook")


# Optional: Health check endpoint
@router.get("/health")
async def webhook_health():
    """
    Health check endpoint for Meta webhooks.

    Returns:
        Simple status dict
    """
    return {
        "status": "healthy",
        "service": "meta_webhooks",
        "version": "2.0",  # Version 2.0 with service layer architecture
    }


# Test endpoint for sending WhatsApp messages (admin only)
@router.post("/test/send")
async def test_send_whatsapp(
    to: str = Query(..., description="Phone number in format 1XXXXXXXXXX"),
    message: str = Query(default=None, description="Message to send (only works in 24hr window)"),
    use_template: bool = Query(default=True, description="Use template instead of freeform text"),
    template_name: str = Query(
        default="hello_world", description="Template name (default: hello_world)"
    ),
):
    """
    Test endpoint to send WhatsApp message.

    IMPORTANT:
    - Freeform text only works within 24-hour window after user messages first
    - For proactive outreach, use templates (use_template=true)
    - The 'hello_world' template is pre-approved by Meta

    Args:
        to: Phone number (format: 1XXXXXXXXXX, no + sign)
        message: Message text (ignored if use_template=true)
        use_template: Use approved template instead of freeform text (default: true)
        template_name: Template name to use (default: hello_world)

    Returns:
        API response from Meta
    """
    from services.whatsapp_notification_service import get_whatsapp_service

    service = get_whatsapp_service()

    if not service.client:
        raise HTTPException(
            status_code=503,
            detail="WhatsApp service not configured (missing credentials)",
        )

    try:
        if use_template:
            # Use template message (works for proactive outreach)
            result = await service.send_template_message(
                to=to, template_name=template_name, language_code="en_US"
            )
        else:
            # Use freeform text (only works in 24hr window)
            if not message:
                raise HTTPException(
                    status_code=400, detail="message parameter required when use_template=false"
                )
            result = await service._send_whatsapp(to, message)

        return {
            "success": result.get("success", False),
            "message_id": result.get("message_id"),
            "template_used": template_name if use_template else None,
            "details": result,
        }
    except Exception as e:
        logger.error(f"Failed to send test WhatsApp: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Test endpoint for booking confirmation template
@router.post("/test/booking-confirmation")
async def test_booking_confirmation(
    to: str = Query(..., description="Phone number in format 1XXXXXXXXXX"),
    name: str = Query(default="John", description="Customer name"),
    date: str = Query(default="Saturday, January 15, 2025", description="Event date"),
    time: str = Query(default="6:00 PM", description="Event time"),
    guests: int = Query(default=12, description="Number of guests"),
    address: str = Query(default="123 Main St, Sacramento, CA 95814", description="Venue address"),
    total: float = Query(default=850.00, description="Total amount"),
    deposit: float = Query(default=100.00, description="Deposit paid"),
    balance: float = Query(default=750.00, description="Balance due"),
):
    """
    Test the booking_confirmation WhatsApp template.

    NOTE: Template must be approved by Meta before this works.
    Check template status at: https://business.facebook.com/wa/manage/message-templates/

    Args:
        to: Phone number (format: 1XXXXXXXXXX, no + sign)
        name: Customer first name
        date: Event date string
        time: Event time string
        guests: Number of guests
        address: Venue address
        total: Total booking amount
        deposit: Deposit paid
        balance: Balance due

    Returns:
        API response from Meta
    """
    from services.whatsapp_notification_service import get_whatsapp_service

    service = get_whatsapp_service()

    if not service.client:
        raise HTTPException(
            status_code=503,
            detail="WhatsApp service not configured (missing credentials)",
        )

    try:
        result = await service.send_booking_confirmation(
            phone_number=to,
            customer_name=name,
            event_date=date,
            event_time=time,
            guest_count=guests,
            venue_address=address,
            total_amount=total,
            deposit_paid=deposit,
            balance_due=balance,
        )

        return {
            "success": result.get("success", False),
            "message_id": result.get("message_id"),
            "template": "booking_confirmation",
            "details": result,
        }
    except Exception as e:
        logger.error(f"Failed to send booking confirmation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Debug endpoint to test webhook reception (bypasses signature for testing)
@router.post("/test/receive")
async def test_receive_webhook(
    request: Request,
    webhook_handler: MetaWebhookHandler = Depends(get_meta_webhook_handler),
):
    """
    Test endpoint that bypasses signature verification.

    USE ONLY FOR DEBUGGING. Does not verify Meta signature.

    Returns:
        Webhook processing result
    """
    try:
        payload = await request.body()
        webhook_data = json.loads(payload.decode())

        # Skip signature verification - process directly
        result = await webhook_handler.process_event(
            event_type=webhook_data.get("object", "unknown"),
            data=webhook_data,
        )

        logger.info(f"Test webhook processed: {result}")
        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Test webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
