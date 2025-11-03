"""Instagram webhook handler for DMs, comments, and mentions."""

from datetime import datetime
import hashlib
import hmac
import json
import logging
from typing import Any

from core.config import get_settings
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

settings = get_settings()
from api.app.database import get_async_session
from api.app.services.social_service import SocialService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/instagram", tags=["social", "instagram"])


def verify_instagram_signature(payload_body: bytes, signature: str, app_secret: str) -> bool:
    """Verify Instagram webhook signature."""
    try:
        # Instagram sends signature as sha256=<hash>
        if not signature.startswith("sha256="):
            return False

        expected_signature = signature[7:]  # Remove 'sha256=' prefix
        mac = hmac.new(app_secret.encode("utf-8"), payload_body, hashlib.sha256)
        computed_signature = mac.hexdigest()

        return hmac.compare_digest(expected_signature, computed_signature)
    except Exception as e:
        logger.exception(f"Instagram signature verification failed: {e}")
        return False


@router.get("/webhook")
async def verify_instagram_webhook(
    hub_mode: str | None = None,
    hub_challenge: str | None = None,
    hub_verify_token: str | None = None,
):
    """Verify Instagram webhook subscription."""
    if hub_mode == "subscribe" and hub_verify_token == settings.instagram_verify_token:
        logger.info("Instagram webhook verified successfully")
        return hub_challenge

    logger.warning(
        f"Instagram webhook verification failed: mode={hub_mode}, token={hub_verify_token}"
    )
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def instagram_webhook_handler(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
):
    """Handle Instagram webhook events."""
    try:
        # Get raw payload for signature verification
        payload_body = await request.body()

        # Verify signature
        if not verify_instagram_signature(
            payload_body, x_hub_signature_256 or "", settings.instagram_app_secret
        ):
            logger.warning("Instagram webhook signature verification failed")
            raise HTTPException(status_code=403, detail="Invalid signature")

        # Parse payload
        payload_data = json.loads(payload_body)

        # Create idempotency signature
        signature = hashlib.sha256(
            f"instagram_{x_hub_signature_256}_{payload_data.get('object', '')}".encode()
        ).hexdigest()

        # Check for duplicate processing
        existing = await db.execute(
            select(1)
            .select_from("integra.social_inbox")
            .where("signature = :sig")
            .params(sig=signature)
        )

        if existing.first():
            logger.info(f"Instagram webhook already processed: {signature}")
            return {"status": "already_processed"}

        # Insert into inbox for idempotency
        await db.execute(
            insert("integra.social_inbox").values(
                {
                    "signature": signature,
                    "platform": "instagram",
                    "webhook_type": payload_data.get("object", "unknown"),
                    "payload_hash": hashlib.sha256(payload_body).hexdigest(),
                    "received_at": datetime.utcnow(),
                }
            )
        )

        # Process the webhook
        social_service = SocialService(db)
        await social_service.process_instagram_webhook(payload_data)

        # Mark as processed
        await db.execute(
            "UPDATE integra.social_inbox SET processed = TRUE, processed_at = :now WHERE signature = :sig".params(
                now=datetime.utcnow(), sig=signature
            )
        )

        await db.commit()

        logger.info(f"Instagram webhook processed successfully: {signature}")
        return {"status": "processed"}

    except Exception as e:
        logger.error(f"Instagram webhook processing error: {e}", exc_info=True)
        await db.rollback()

        # Update error in inbox
        try:
            await db.execute(
                "UPDATE integra.social_inbox SET processing_attempts = processing_attempts + 1, "
                "last_error = :error WHERE signature = :sig".params(error=str(e), sig=signature)
            )
            await db.commit()
        except Exception as db_error:
            logger.exception(f"Failed to update error record in database: {db_error}")

        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/setup-webhooks")
async def setup_instagram_webhooks(
    account_data: dict[str, Any], db: AsyncSession = Depends(get_async_session)
):
    """Set up Instagram webhook subscriptions for an account."""
    try:
        # This would integrate with Instagram Graph API to set up webhooks
        # Implementation depends on specific Instagram Business Account setup

        social_service = SocialService(db)
        result = await social_service.setup_instagram_webhooks(account_data)

        return {"status": "webhooks_configured", "details": result}

    except Exception as e:
        logger.error(f"Instagram webhook setup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Webhook setup failed: {e!s}")


@router.delete("/webhooks/{account_id}")
async def remove_instagram_webhooks(account_id: str, db: AsyncSession = Depends(get_async_session)):
    """Remove Instagram webhook subscriptions for an account."""
    try:
        social_service = SocialService(db)
        await social_service.remove_instagram_webhooks(account_id)

        return {"status": "webhooks_removed"}

    except Exception as e:
        logger.error(f"Instagram webhook removal error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Webhook removal failed: {e!s}")
