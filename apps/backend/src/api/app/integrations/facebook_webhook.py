"""Facebook webhook handler for messages, comments, and posts."""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings

settings = get_settings()
from api.app.database import get_async_session
from api.app.services.social_service import SocialService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/facebook", tags=["social", "facebook"])


def verify_facebook_signature(payload_body: bytes, signature: str, app_secret: str) -> bool:
    """Verify Facebook webhook signature."""
    try:
        # Facebook sends signature as sha256=<hash>
        if not signature.startswith('sha256='):
            return False

        expected_signature = signature[7:]  # Remove 'sha256=' prefix
        mac = hmac.new(
            app_secret.encode('utf-8'),
            payload_body,
            hashlib.sha256
        )
        computed_signature = mac.hexdigest()

        return hmac.compare_digest(expected_signature, computed_signature)
    except Exception as e:
        logger.error(f"Facebook signature verification failed: {e}")
        return False


@router.get("/webhook")
async def verify_facebook_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    """Verify Facebook webhook subscription."""
    if (
        hub_mode == "subscribe"
        and hub_verify_token == settings.facebook_verify_token
    ):
        logger.info("Facebook webhook verified successfully")
        return hub_challenge

    logger.warning(f"Facebook webhook verification failed: mode={hub_mode}, token={hub_verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def facebook_webhook_handler(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
):
    """Handle Facebook webhook events."""
    try:
        # Get raw payload for signature verification
        payload_body = await request.body()

        # Verify signature
        if not verify_facebook_signature(
            payload_body,
            x_hub_signature_256 or "",
            settings.facebook_app_secret
        ):
            logger.warning("Facebook webhook signature verification failed")
            raise HTTPException(status_code=403, detail="Invalid signature")

        # Parse payload
        payload_data = json.loads(payload_body)

        # Create idempotency signature
        signature = hashlib.sha256(
            f"facebook_{x_hub_signature_256}_{payload_data.get('object', '')}"
            .encode()
        ).hexdigest()

        # Check for duplicate processing
        existing = await db.execute(
            select(1).select_from("integra.social_inbox")
            .where("signature = :sig")
            .params(sig=signature)
        )

        if existing.first():
            logger.info(f"Facebook webhook already processed: {signature}")
            return {"status": "already_processed"}

        # Insert into inbox for idempotency
        await db.execute(
            insert("integra.social_inbox").values({
                "signature": signature,
                "platform": "facebook",
                "webhook_type": payload_data.get("object", "unknown"),
                "payload_hash": hashlib.sha256(payload_body).hexdigest(),
                "received_at": datetime.utcnow()
            })
        )

        # Process the webhook
        social_service = SocialService(db)
        await social_service.process_facebook_webhook(payload_data)

        # Mark as processed
        await db.execute(
            "UPDATE integra.social_inbox SET processed = TRUE, processed_at = :now WHERE signature = :sig"
            .params(now=datetime.utcnow(), sig=signature)
        )

        await db.commit()

        logger.info(f"Facebook webhook processed successfully: {signature}")
        return {"status": "processed"}

    except Exception as e:
        logger.error(f"Facebook webhook processing error: {e}", exc_info=True)
        await db.rollback()

        # Update error in inbox
        try:
            await db.execute(
                "UPDATE integra.social_inbox SET processing_attempts = processing_attempts + 1, "
                "last_error = :error WHERE signature = :sig"
                .params(error=str(e), sig=signature)
            )
            await db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update error record in database: {db_error}")
            pass

        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/setup-webhooks")
async def setup_facebook_webhooks(
    account_data: dict[str, Any],
    db: AsyncSession = Depends(get_async_session)
):
    """Set up Facebook webhook subscriptions for a page."""
    try:
        social_service = SocialService(db)
        result = await social_service.setup_facebook_webhooks(account_data)

        return {"status": "webhooks_configured", "details": result}

    except Exception as e:
        logger.error(f"Facebook webhook setup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Webhook setup failed: {str(e)}")


@router.delete("/webhooks/{account_id}")
async def remove_facebook_webhooks(
    account_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Remove Facebook webhook subscriptions for a page."""
    try:
        social_service = SocialService(db)
        await social_service.remove_facebook_webhooks(account_id)

        return {"status": "webhooks_removed"}

    except Exception as e:
        logger.error(f"Facebook webhook removal error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Webhook removal failed: {str(e)}")
