"""Rate-limited social platform API clients."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import logging
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """Rate limit information for a platform."""

    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    current_minute: int = 0
    current_hour: int = 0
    current_day: int = 0
    minute_reset_at: datetime | None = None
    hour_reset_at: datetime | None = None
    day_reset_at: datetime | None = None


class RateLimitedClient:
    """Base class for rate-limited API clients."""

    def __init__(self, platform: str, rate_limits: RateLimitInfo):
        self.platform = platform
        self.rate_limits = rate_limits
        self._lock = asyncio.Lock()

    async def can_make_request(self) -> bool:
        """Check if we can make a request within rate limits."""
        async with self._lock:
            now = datetime.now(timezone.utc)

            # Reset minute counter
            if not self.rate_limits.minute_reset_at or now >= self.rate_limits.minute_reset_at:
                self.rate_limits.current_minute = 0
                self.rate_limits.minute_reset_at = now + timedelta(minutes=1)

            # Reset hour counter
            if not self.rate_limits.hour_reset_at or now >= self.rate_limits.hour_reset_at:
                self.rate_limits.current_hour = 0
                self.rate_limits.hour_reset_at = now + timedelta(hours=1)

            # Reset day counter
            if not self.rate_limits.day_reset_at or now >= self.rate_limits.day_reset_at:
                self.rate_limits.current_day = 0
                self.rate_limits.day_reset_at = now + timedelta(days=1)

            # Check all limits
            return (
                self.rate_limits.current_minute < self.rate_limits.requests_per_minute
                and self.rate_limits.current_hour < self.rate_limits.requests_per_hour
                and self.rate_limits.current_day < self.rate_limits.requests_per_day
            )

    async def track_request(self):
        """Track a successful request."""
        async with self._lock:
            self.rate_limits.current_minute += 1
            self.rate_limits.current_hour += 1
            self.rate_limits.current_day += 1

    async def wait_for_rate_limit_reset(self) -> float:
        """Calculate seconds to wait for next available request."""
        now = datetime.now(timezone.utc)

        wait_times = []

        if self.rate_limits.current_minute >= self.rate_limits.requests_per_minute:
            if self.rate_limits.minute_reset_at:
                wait_times.append((self.rate_limits.minute_reset_at - now).total_seconds())

        if self.rate_limits.current_hour >= self.rate_limits.requests_per_hour:
            if self.rate_limits.hour_reset_at:
                wait_times.append((self.rate_limits.hour_reset_at - now).total_seconds())

        if self.rate_limits.current_day >= self.rate_limits.requests_per_day:
            if self.rate_limits.day_reset_at:
                wait_times.append((self.rate_limits.day_reset_at - now).total_seconds())

        return min(wait_times) if wait_times else 0


class InstagramClient(RateLimitedClient):
    """Instagram/Meta Graph API client with rate limiting."""

    def __init__(self, access_token: str):
        super().__init__(
            platform="instagram",
            rate_limits=RateLimitInfo(
                requests_per_minute=60, requests_per_hour=200, requests_per_day=200000
            ),
        )
        self.access_token = access_token
        self.base_url = "https://graph.facebook.com/v18.0"

    async def send_direct_message(self, recipient_id: str, message: str) -> dict[str, Any]:
        """Send a direct message via Instagram API."""
        if not await self.can_make_request():
            wait_time = await self.wait_for_rate_limit_reset()
            logger.info(f"Instagram rate limit hit, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/me/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message},
            "access_token": self.access_token,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        await self.track_request()
                        result = await response.json()
                        logger.info(f"Instagram DM sent successfully: {result.get('id')}")
                        return {"success": True, "message_id": result.get("id")}
                    else:
                        error_text = await response.text()
                        logger.error(f"Instagram API error: {response.status} - {error_text}")
                        return {"success": False, "error": error_text}

        except Exception as e:
            logger.exception(f"Instagram API request failed: {e}")
            return {"success": False, "error": str(e)}

    async def reply_to_comment(self, comment_id: str, message: str) -> dict[str, Any]:
        """Reply to a comment via Instagram API."""
        if not await self.can_make_request():
            wait_time = await self.wait_for_rate_limit_reset()
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/{comment_id}/replies"
        payload = {"message": message, "access_token": self.access_token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        await self.track_request()
                        result = await response.json()
                        return {"success": True, "reply_id": result.get("id")}
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Instagram comment reply error: {response.status} - {error_text}"
                        )
                        return {"success": False, "error": error_text}

        except Exception as e:
            logger.exception(f"Instagram comment reply failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_media_comments(self, media_id: str) -> list[dict[str, Any]]:
        """Get comments for a media item."""
        if not await self.can_make_request():
            wait_time = await self.wait_for_rate_limit_reset()
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/{media_id}/comments"
        params = {"fields": "id,text,username,timestamp,replies", "access_token": self.access_token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        await self.track_request()
                        result = await response.json()
                        return result.get("data", [])
                    else:
                        logger.error(f"Instagram comments fetch error: {response.status}")
                        return []

        except Exception as e:
            logger.exception(f"Instagram comments fetch failed: {e}")
            return []


class FacebookClient(RateLimitedClient):
    """Facebook Graph API client with rate limiting."""

    def __init__(self, access_token: str, page_id: str):
        super().__init__(
            platform="facebook",
            rate_limits=RateLimitInfo(
                requests_per_minute=60, requests_per_hour=200, requests_per_day=200000
            ),
        )
        self.access_token = access_token
        self.page_id = page_id
        self.base_url = "https://graph.facebook.com/v18.0"

    async def send_message(self, recipient_id: str, message: str) -> dict[str, Any]:
        """Send a message via Facebook Messenger."""
        if not await self.can_make_request():
            wait_time = await self.wait_for_rate_limit_reset()
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/{self.page_id}/messages"
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": message},
            "access_token": self.access_token,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        await self.track_request()
                        result = await response.json()
                        return {"success": True, "message_id": result.get("message_id")}
                    else:
                        error_text = await response.text()
                        logger.error(f"Facebook Messenger error: {response.status} - {error_text}")
                        return {"success": False, "error": error_text}

        except Exception as e:
            logger.exception(f"Facebook Messenger request failed: {e}")
            return {"success": False, "error": str(e)}

    async def reply_to_post_comment(self, comment_id: str, message: str) -> dict[str, Any]:
        """Reply to a post comment."""
        if not await self.can_make_request():
            wait_time = await self.wait_for_rate_limit_reset()
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/{comment_id}/comments"
        payload = {"message": message, "access_token": self.access_token}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        await self.track_request()
                        result = await response.json()
                        return {"success": True, "comment_id": result.get("id")}
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"Facebook comment reply error: {response.status} - {error_text}"
                        )
                        return {"success": False, "error": error_text}

        except Exception as e:
            logger.exception(f"Facebook comment reply failed: {e}")
            return {"success": False, "error": str(e)}


class GoogleBusinessClient(RateLimitedClient):
    """Google Business Profile API client with rate limiting."""

    def __init__(self, access_token: str, location_id: str):
        super().__init__(
            platform="google",
            rate_limits=RateLimitInfo(
                requests_per_minute=100, requests_per_hour=1000, requests_per_day=25000
            ),
        )
        self.access_token = access_token
        self.location_id = location_id
        self.base_url = "https://mybusinessbusinessinformation.googleapis.com/v1"

    async def reply_to_review(self, review_name: str, reply_text: str) -> dict[str, Any]:
        """Reply to a Google Business review."""
        if not await self.can_make_request():
            wait_time = await self.wait_for_rate_limit_reset()
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/{review_name}/reply"
        payload = {"comment": reply_text}
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        await self.track_request()
                        result = await response.json()
                        return {"success": True, "reply": result}
                    else:
                        error_text = await response.text()
                        logger.error(f"Google review reply error: {response.status} - {error_text}")
                        return {"success": False, "error": error_text}

        except Exception as e:
            logger.exception(f"Google review reply failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_reviews(self) -> list[dict[str, Any]]:
        """Get reviews for the business location."""
        if not await self.can_make_request():
            wait_time = await self.wait_for_rate_limit_reset()
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/accounts/*/locations/{self.location_id}/reviews"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        await self.track_request()
                        result = await response.json()
                        return result.get("reviews", [])
                    else:
                        logger.error(f"Google reviews fetch error: {response.status}")
                        return []

        except Exception as e:
            logger.exception(f"Google reviews fetch failed: {e}")
            return []


class YelpClient(RateLimitedClient):
    """Yelp Fusion API client with rate limiting."""

    def __init__(self, api_key: str, business_id: str):
        super().__init__(
            platform="yelp",
            rate_limits=RateLimitInfo(
                requests_per_minute=100, requests_per_hour=5000, requests_per_day=25000
            ),
        )
        self.api_key = api_key
        self.business_id = business_id
        self.base_url = "https://api.yelp.com/v3"

    async def get_reviews(self, offset: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        """Get reviews for the business."""
        if not await self.can_make_request():
            wait_time = await self.wait_for_rate_limit_reset()
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/businesses/{self.business_id}/reviews"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"offset": offset, "limit": min(limit, 50)}  # Yelp max limit

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        await self.track_request()
                        result = await response.json()
                        return result.get("reviews", [])
                    else:
                        logger.error(f"Yelp reviews fetch error: {response.status}")
                        return []

        except Exception as e:
            logger.exception(f"Yelp reviews fetch failed: {e}")
            return []

    async def get_business_info(self) -> dict[str, Any] | None:
        """Get business information."""
        if not await self.can_make_request():
            wait_time = await self.wait_for_rate_limit_reset()
            await asyncio.sleep(wait_time)

        url = f"{self.base_url}/businesses/{self.business_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        await self.track_request()
                        result = await response.json()
                        return result
                    else:
                        logger.error(f"Yelp business info fetch error: {response.status}")
                        return None

        except Exception as e:
            logger.exception(f"Yelp business info fetch failed: {e}")
            return None


class SocialClientManager:
    """Manager for social media API clients."""

    def __init__(self):
        self.clients: dict[str, RateLimitedClient] = {}

    def add_instagram_client(self, account_id: str, access_token: str):
        """Add Instagram client for account."""
        self.clients[f"instagram_{account_id}"] = InstagramClient(access_token)

    def add_facebook_client(self, account_id: str, access_token: str, page_id: str):
        """Add Facebook client for account."""
        self.clients[f"facebook_{account_id}"] = FacebookClient(access_token, page_id)

    def add_google_client(self, account_id: str, access_token: str, location_id: str):
        """Add Google Business client for account."""
        self.clients[f"google_{account_id}"] = GoogleBusinessClient(access_token, location_id)

    def add_yelp_client(self, account_id: str, api_key: str, business_id: str):
        """Add Yelp client for account."""
        self.clients[f"yelp_{account_id}"] = YelpClient(api_key, business_id)

    def get_client(self, platform: str, account_id: str) -> RateLimitedClient | None:
        """Get client for platform and account."""
        return self.clients.get(f"{platform}_{account_id}")

    def remove_client(self, platform: str, account_id: str):
        """Remove client for account."""
        key = f"{platform}_{account_id}"
        if key in self.clients:
            del self.clients[key]

    async def get_rate_limit_status(self) -> dict[str, dict[str, Any]]:
        """Get rate limit status for all clients."""
        status = {}

        for key, client in self.clients.items():
            platform, account_id = key.split("_", 1)
            status[key] = {
                "platform": platform,
                "account_id": account_id,
                "rate_limits": {
                    "minute": f"{client.rate_limits.current_minute}/{client.rate_limits.requests_per_minute}",
                    "hour": f"{client.rate_limits.current_hour}/{client.rate_limits.requests_per_hour}",
                    "day": f"{client.rate_limits.current_day}/{client.rate_limits.requests_per_day}",
                },
                "can_make_request": await client.can_make_request(),
            }

        return status


# Global client manager instance
social_client_manager = SocialClientManager()
