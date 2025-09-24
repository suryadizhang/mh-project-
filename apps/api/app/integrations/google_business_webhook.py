"""Google Business Profile webhook handler for reviews and messages."""

import base64
import hashlib
import json
import logging
from datetime import datetime
from typing import Any

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_async_session
from app.services.social_service import SocialService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/google-business", tags=["social", "google"])


def verify_google_webhook_token(token: str) -> bool:
    """Verify Google webhook JWT token."""
    try:
        # Google sends Pub/Sub messages with JWT tokens
        # This is a simplified version - in production, you'd validate the full JWT
        decoded = jwt.decode(
            token,
            options={"verify_signature": False},  # For demo - in production, verify signature
            algorithms=["RS256"]
        )

        # Verify the token is from Google and for your project
        issuer = decoded.get("iss")
        audience = decoded.get("aud")

        return issuer == "accounts.google.com" and audience == settings.google_project_id

    except Exception as e:
        logger.error(f"Google webhook token verification failed: {e}")
        return False


@router.post("/webhook")
async def google_business_webhook_handler(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    authorization: str = Header(None),
):
    """Handle Google Business Profile webhook events (via Cloud Pub/Sub)."""
    try:
        # Get raw payload
        payload_body = await request.body()

        # Google sends Pub/Sub messages, verify JWT if present
        if authorization and authorization.startswith('Bearer '):
            token = authorization[7:]
            if not verify_google_webhook_token(token):
                logger.warning("Google webhook token verification failed")
                raise HTTPException(status_code=403, detail="Invalid token")

        # Parse Pub/Sub message
        payload_data = json.loads(payload_body)

        # Pub/Sub messages have a specific structure
        message = payload_data.get("message", {})
        if not message:
            logger.warning("No message in Google webhook payload")
            return {"status": "no_message"}

        # Decode the base64 data
        data = message.get("data", "")
        if data:
            decoded_data = json.loads(base64.b64decode(data).decode('utf-8'))
        else:
            decoded_data = {}

        # Create idempotency signature
        message_id = message.get("messageId", "")
        signature = hashlib.sha256(f"google_{message_id}".encode()).hexdigest()

        # Check for duplicate processing
        existing = await db.execute(
            select(1).select_from("integra.social_inbox")
            .where("signature = :sig")
            .params(sig=signature)
        )

        if existing.first():
            logger.info(f"Google webhook already processed: {signature}")
            return {"status": "already_processed"}

        # Insert into inbox for idempotency
        await db.execute(
            insert("integra.social_inbox").values({
                "signature": signature,
                "platform": "google_business",
                "webhook_type": decoded_data.get("eventType", "unknown"),
                "payload_hash": hashlib.sha256(payload_body).hexdigest(),
                "received_at": datetime.utcnow()
            })
        )

        # Process the webhook
        social_service = SocialService(db)
        await social_service.process_google_business_webhook(decoded_data)

        # Mark as processed
        await db.execute(
            "UPDATE integra.social_inbox SET processed = TRUE, processed_at = :now WHERE signature = :sig"
            .params(now=datetime.utcnow(), sig=signature)
        )

        await db.commit()

        logger.info(f"Google Business webhook processed successfully: {signature}")
        return {"status": "processed"}

    except Exception as e:
        logger.error(f"Google Business webhook processing error: {e}", exc_info=True)
        await db.rollback()

        # Update error in inbox
        try:
            await db.execute(
                "UPDATE integra.social_inbox SET processing_attempts = processing_attempts + 1, "
                "last_error = :error WHERE signature = :sig"
                .params(error=str(e), sig=signature)
            )
            await db.commit()
        except:
            pass

        raise HTTPException(status_code=500, detail="Webhook processing failed")


@router.post("/setup-notifications")
async def setup_google_business_notifications(
    account_data: dict[str, Any],
    db: AsyncSession = Depends(get_async_session)
):
    """Set up Google Business Profile notifications."""
    try:
        social_service = SocialService(db)
        result = await social_service.setup_google_business_notifications(account_data)

        return {"status": "notifications_configured", "details": result}

    except Exception as e:
        logger.error(f"Google Business notification setup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Notification setup failed: {str(e)}")


@router.delete("/notifications/{account_id}")
async def remove_google_business_notifications(
    account_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Remove Google Business Profile notifications for a location."""
    try:
        social_service = SocialService(db)
        await social_service.remove_google_business_notifications(account_id)

        return {"status": "notifications_removed"}

    except Exception as e:
        logger.error(f"Google Business notification removal error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Notification removal failed: {str(e)}")


@router.get("/locations")
async def list_google_business_locations(
    access_token: str,
    db: AsyncSession = Depends(get_async_session)
):
    """List Google Business Profile locations for account setup."""
    try:
        social_service = SocialService(db)
        locations = await social_service.list_google_business_locations(access_token)

        return {"locations": locations}

    except Exception as e:
        logger.error(f"Failed to list Google Business locations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list locations: {str(e)}")


@router.post("/poll-reviews")
async def poll_google_business_reviews(
    account_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Manually trigger polling of Google Business reviews (fallback when webhooks aren't available)."""
    try:
        social_service = SocialService(db)
        results = await social_service.poll_google_business_reviews(account_id)

        return {
            "status": "polling_complete",
            "new_reviews": results.get("new_reviews", 0),
            "updated_reviews": results.get("updated_reviews", 0)
        }

    except Exception as e:
        logger.error(f"Google Business review polling error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Review polling failed: {str(e)}")
