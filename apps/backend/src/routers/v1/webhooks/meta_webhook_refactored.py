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
