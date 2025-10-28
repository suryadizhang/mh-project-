"""Yelp integration handler for reviews (polling-based due to limited webhook support)."""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings

settings = get_settings()
from api.app.database import get_async_session
from api.app.services.social_service import SocialService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/yelp", tags=["social", "yelp"])


class YelpAPIClient:
    """Client for Yelp Fusion API."""

    BASE_URL = "https://api.yelp.com/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def get_business_reviews(self, business_id: str, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        """Get reviews for a business."""
        url = f"{self.BASE_URL}/businesses/{business_id}/reviews"
        params = {
            "limit": min(limit, 50),  # Yelp max is 50
            "offset": offset,
            "sort_by": "date_desc"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Yelp API error: {error_data}"
                    )

    async def get_business_details(self, business_id: str) -> dict[str, Any]:
        """Get business details."""
        url = f"{self.BASE_URL}/businesses/{business_id}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_data = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Yelp API error: {error_data}"
                    )


@router.post("/setup-polling")
async def setup_yelp_polling(
    account_data: dict[str, Any],
    db: AsyncSession = Depends(get_async_session)
):
    """Set up Yelp review polling for a business."""
    try:
        business_id = account_data.get("business_id")
        api_key = account_data.get("api_key", settings.yelp_api_key)

        if not business_id:
            raise HTTPException(status_code=400, detail="business_id is required")

        if not api_key:
            raise HTTPException(status_code=400, detail="Yelp API key not configured")

        # Verify business exists and get details
        client = YelpAPIClient(api_key)
        business_details = await client.get_business_details(business_id)

        social_service = SocialService(db)
        result = await social_service.setup_yelp_account(business_details, api_key)

        return {"status": "polling_configured", "details": result}

    except Exception as e:
        logger.error(f"Yelp polling setup error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Polling setup failed: {str(e)}")


@router.post("/poll-reviews/{account_id}")
async def poll_yelp_reviews(
    account_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session),
    force_full: bool = False
):
    """Poll Yelp reviews for a business account."""
    try:
        social_service = SocialService(db)

        # Add to background tasks for async processing
        background_tasks.add_task(
            _poll_yelp_reviews_task,
            db,
            account_id,
            force_full
        )

        return {"status": "polling_started", "account_id": account_id}

    except Exception as e:
        logger.error(f"Yelp review polling error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Polling failed: {str(e)}")


async def _poll_yelp_reviews_task(db: AsyncSession, account_id: str, force_full: bool = False):
    """Background task to poll Yelp reviews."""
    try:
        social_service = SocialService(db)

        # Get account details
        account = await social_service.get_social_account(account_id)
        if not account or account.platform != "yelp":
            logger.error(f"Yelp account not found: {account_id}")
            return

        # Get API key from account metadata
        api_key = account.metadata.get("api_key") if account.metadata else None
        if not api_key:
            api_key = settings.yelp_api_key

        if not api_key:
            logger.error(f"No Yelp API key configured for account {account_id}")
            return

        client = YelpAPIClient(api_key)
        business_id = account.page_id  # Yelp business ID

        # Get last sync timestamp to only fetch new reviews
        last_sync = account.last_sync_at
        if not last_sync and not force_full:
            # First sync - get reviews from last 30 days
            last_sync = datetime.utcnow() - timedelta(days=30)

        # Poll reviews
        new_reviews = 0
        updated_reviews = 0
        offset = 0
        limit = 50

        while True:
            try:
                reviews_data = await client.get_business_reviews(
                    business_id,
                    limit=limit,
                    offset=offset
                )

                reviews = reviews_data.get("reviews", [])
                if not reviews:
                    break

                for review_data in reviews:
                    # Convert Yelp review data to our format
                    review_date = datetime.fromisoformat(
                        review_data.get("time_created", "").replace('Z', '+00:00')
                    )

                    # Skip old reviews if not doing full sync
                    if not force_full and last_sync and review_date < last_sync:
                        continue

                    # Create idempotency signature
                    signature = hashlib.sha256(
                        f"yelp_review_{business_id}_{review_data.get('id', '')}"
                        .encode()
                    ).hexdigest()

                    # Check if already processed
                    existing = await db.execute(
                        select(1).select_from("integra.social_inbox")
                        .where("signature = :sig")
                        .params(sig=signature)
                    )

                    if existing.first():
                        updated_reviews += 1
                        continue

                    # Insert into inbox for idempotency
                    await db.execute(
                        insert("integra.social_inbox").values({
                            "signature": signature,
                            "platform": "yelp",
                            "webhook_type": "review",
                            "account_id": account.id,
                            "payload_hash": hashlib.sha256(
                                json.dumps(review_data, sort_keys=True).encode('utf-8')
                            ).hexdigest(),
                            "received_at": datetime.utcnow()
                        })
                    )

                    # Process the review
                    await social_service.process_yelp_review(account, review_data)
                    new_reviews += 1

                    # Mark as processed
                    await db.execute(
                        "UPDATE integra.social_inbox SET processed = TRUE, processed_at = :now "
                        "WHERE signature = :sig"
                        .params(now=datetime.utcnow(), sig=signature)
                    )

                # Check if we have more reviews to fetch
                total_reviews = reviews_data.get("total", 0)
                if offset + limit >= total_reviews:
                    break

                offset += limit

            except Exception as e:
                logger.error(f"Error polling Yelp reviews at offset {offset}: {e}")
                break

        # Update last sync timestamp
        await db.execute(
            "UPDATE core.social_accounts SET last_sync_at = :now "
            "WHERE id = :account_id"
            .params(now=datetime.utcnow(), account_id=account.id)
        )

        await db.commit()

        logger.info(
            f"Yelp review polling complete for {account_id}: "
            f"{new_reviews} new, {updated_reviews} updated"
        )

    except Exception as e:
        logger.error(f"Yelp review polling task error: {e}", exc_info=True)
        await db.rollback()


@router.post("/reply-to-review")
async def reply_to_yelp_review(
    review_id: str,
    reply_data: dict[str, Any],
    db: AsyncSession = Depends(get_async_session)
):
    """
    Handle Yelp review reply (manual process).

    Since Yelp doesn't support direct API replies to reviews,
    this endpoint stores the reply draft and provides a deep link
    for manual posting via Yelp Business account.
    """
    try:
        social_service = SocialService(db)

        # Store reply draft and generate deep link
        result = await social_service.create_yelp_reply_draft(review_id, reply_data)

        return {
            "status": "reply_draft_created",
            "draft_id": result.get("draft_id"),
            "deep_link": result.get("deep_link"),
            "instructions": "Please use the provided deep link to manually post this reply via your Yelp Business account."
        }

    except Exception as e:
        logger.error(f"Yelp reply creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Reply creation failed: {str(e)}")


@router.get("/review-deep-link/{review_id}")
async def get_yelp_review_deep_link(
    review_id: str,
    business_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Generate deep link to Yelp Business account for manual review response."""
    try:
        # Generate Yelp Business deep link
        # This would be the URL format for Yelp Business account
        deep_link = f"https://biz.yelp.com/manage_account/reviews?review_id={review_id}&business_id={business_id}"

        return {
            "deep_link": deep_link,
            "instructions": "Click this link to respond to the review in your Yelp Business account"
        }

    except Exception as e:
        logger.error(f"Yelp deep link generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Deep link generation failed: {str(e)}")


@router.delete("/polling/{account_id}")
async def remove_yelp_polling(
    account_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Remove Yelp polling configuration for an account."""
    try:
        social_service = SocialService(db)
        await social_service.remove_yelp_account(account_id)

        return {"status": "polling_removed"}

    except Exception as e:
        logger.error(f"Yelp polling removal error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Polling removal failed: {str(e)}")
