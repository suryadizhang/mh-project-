"""Social media outbox processor for webhook deliveries."""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import aiohttp
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from api.app.models.events import OutboxEntry
from api.app.models.social import SocialAccount, SocialMessage, SocialThread

logger = logging.getLogger(__name__)


class SocialOutboxProcessor:
    """Processor for social media outbox events."""

    def __init__(self):
        self.rate_limits = {
            "instagram": {"requests_per_hour": 200, "current": 0, "reset_at": None},
            "facebook": {"requests_per_hour": 200, "current": 0, "reset_at": None},
            "google": {"requests_per_hour": 1000, "current": 0, "reset_at": None},
            "yelp": {"requests_per_hour": 5000, "current": 0, "reset_at": None}
        }

        self.handlers = {
            "social_reply_approved": self._handle_reply_approved,
            "social_message_schedule": self._handle_message_schedule,
            "social_followup_due": self._handle_followup_due,
            "webhook_delivery_failed": self._handle_webhook_retry,
            "social_account_sync": self._handle_account_sync
        }

    async def process_event(self, event: OutboxEntry, session: AsyncSession) -> bool:
        """Process a social media outbox event."""
        try:
            handler = self.handlers.get(event.event_type)
            if not handler:
                logger.debug(f"No handler for outbox event type: {event.event_type}")
                return False

            # Check rate limits before processing
            platform = self._extract_platform_from_event(event)
            if platform and not await self._check_rate_limit(platform):
                logger.warning(f"Rate limit exceeded for {platform}, deferring event {event.id}")
                return False

            success = await handler(event, session)

            if success and platform:
                await self._update_rate_limit(platform)

            return success

        except Exception as e:
            logger.error(f"Error processing social outbox event {event.id}: {e}")
            raise

    async def _handle_reply_approved(self, event: OutboxEntry, session: AsyncSession) -> bool:
        """Handle approved social media reply."""
        data = event.event_data
        message_id = data.get("message_id")
        thread_id = data.get("thread_id")

        try:
            # Get message and thread details
            message_stmt = select(SocialMessage).where(SocialMessage.id == message_id)
            message_result = await session.execute(message_stmt)
            message = message_result.scalar_one_or_none()

            if not message:
                logger.error(f"Message {message_id} not found for approved reply")
                return False

            thread_stmt = select(SocialThread).join(SocialAccount).where(
                SocialThread.id == thread_id
            ).options(joinedload(SocialThread.account))
            thread_result = await session.execute(thread_stmt)
            thread = thread_result.scalar_one_or_none()

            if not thread:
                logger.error(f"Thread {thread_id} not found for approved reply")
                return False

            # Send the message via platform API
            platform = thread.account.platform
            success = await self._send_platform_message(
                platform=platform,
                account=thread.account,
                message=message,
                thread=thread,
                session=session
            )

            if success:
                # Mark message as sent
                message.sent_at = datetime.utcnow()
                message.metadata = {
                    **(message.metadata or {}),
                    "sent_via_outbox": True,
                    "approved_at": event.created_at.isoformat()
                }

                logger.info(f"Successfully sent approved reply {message_id}")
                return True
            else:
                logger.error(f"Failed to send approved reply {message_id}")
                return False

        except Exception as e:
            logger.error(f"Error handling approved reply {message_id}: {e}")
            return False

    async def _handle_message_schedule(self, event: OutboxEntry, session: AsyncSession) -> bool:
        """Handle scheduled social media message."""
        data = event.event_data
        message_id = data.get("message_id")
        scheduled_for = data.get("scheduled_for")

        # Check if it's time to send
        if datetime.fromisoformat(scheduled_for.replace('Z', '+00:00')) > datetime.utcnow():
            logger.debug(f"Message {message_id} not yet scheduled to send")
            return False  # Will retry later

        # Process similar to approved reply
        return await self._handle_reply_approved(event, session)

    async def _handle_followup_due(self, event: OutboxEntry, session: AsyncSession) -> bool:
        """Handle social media follow-up due."""
        data = event.event_data
        thread_id = data.get("thread_id")
        follow_up_type = data.get("follow_up_type")
        conditions = data.get("conditions", {})

        try:
            # Check follow-up conditions
            if not await self._check_followup_conditions(thread_id, conditions, session):
                logger.info(f"Follow-up conditions not met for thread {thread_id}")
                return True  # Skip this follow-up

            # Create and send follow-up message
            follow_up_message = await self._create_followup_message(
                thread_id=thread_id,
                follow_up_type=follow_up_type,
                data=data,
                session=session
            )

            if follow_up_message:
                # Process the follow-up as a regular message
                follow_up_event = OutboxEntry(
                    event_type="social_reply_approved",
                    aggregate_type="SocialMessage",
                    aggregate_id=follow_up_message.id,
                    event_data={
                        "message_id": follow_up_message.id,
                        "thread_id": thread_id,
                        "is_followup": True
                    }
                )

                return await self._handle_reply_approved(follow_up_event, session)

            return False

        except Exception as e:
            logger.error(f"Error handling follow-up for thread {thread_id}: {e}")
            return False

    async def _handle_webhook_retry(self, event: OutboxEntry, session: AsyncSession) -> bool:
        """Handle webhook delivery retry."""
        data = event.event_data
        webhook_url = data.get("webhook_url")
        payload = data.get("payload")
        retry_count = data.get("retry_count", 0)

        if retry_count >= 3:
            logger.error(f"Max retries reached for webhook {webhook_url}")
            return False

        try:
            async with aiohttp.ClientSession() as client_session:
                async with client_session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                    headers={
                        "Content-Type": "application/json",
                        "User-Agent": "MyHibachiChef-Webhook/1.0"
                    }
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook retry successful: {webhook_url}")
                        return True
                    else:
                        logger.error(f"Webhook retry failed: {response.status} for {webhook_url}")

                        # Schedule another retry if not max retries
                        if retry_count < 2:
                            retry_event = OutboxEntry(
                                event_type="webhook_delivery_failed",
                                aggregate_type="WebhookDelivery",
                                aggregate_id=UUID(int=0),  # Dummy ID
                                event_data={
                                    **data,
                                    "retry_count": retry_count + 1
                                }
                            )
                            session.add(retry_event)

                        return False

        except Exception as e:
            logger.error(f"Error retrying webhook {webhook_url}: {e}")
            return False

    async def _handle_account_sync(self, event: OutboxEntry, session: AsyncSession) -> bool:
        """Handle social account sync."""
        data = event.event_data
        account_id = data.get("account_id")

        try:
            account_stmt = select(SocialAccount).where(SocialAccount.id == account_id)
            result = await session.execute(account_stmt)
            account = result.scalar_one_or_none()

            if not account:
                logger.error(f"Account {account_id} not found for sync")
                return False

            # Sync account details with platform
            platform_data = await self._fetch_account_details(account)

            if platform_data:
                # Update account with fresh data
                account.page_name = platform_data.get("page_name", account.page_name)
                account.avatar_url = platform_data.get("avatar_url", account.avatar_url)
                account.metadata = {
                    **(account.metadata or {}),
                    "last_sync": datetime.utcnow().isoformat(),
                    "platform_data": platform_data
                }

                logger.info(f"Synced account {account_id} with platform")
                return True
            else:
                logger.warning(f"Could not fetch platform data for account {account_id}")
                return False

        except Exception as e:
            logger.error(f"Error syncing account {account_id}: {e}")
            return False

    async def _send_platform_message(
        self,
        platform: str,
        account: SocialAccount,
        message: SocialMessage,
        thread: SocialThread,
        session: AsyncSession
    ) -> bool:
        """Send message via platform API."""
        try:
            if platform in ["instagram", "facebook"]:
                return await self._send_meta_message(account, message, thread)
            elif platform == "google":
                return await self._send_google_message(account, message, thread)
            elif platform == "yelp":
                # Yelp doesn't support direct messaging via API
                logger.warning("Yelp direct messaging not supported via API")
                return False
            else:
                logger.error(f"Unsupported platform for messaging: {platform}")
                return False

        except Exception as e:
            logger.error(f"Error sending {platform} message: {e}")
            return False

    async def _send_meta_message(self, account: SocialAccount, message: SocialMessage, thread: SocialThread) -> bool:
        """Send message via Meta Graph API (Instagram/Facebook)."""
        if not account.token_ref:
            logger.error("No access token for Meta account")
            return False

        # Get access token (should be encrypted in production)
        access_token = await self._decrypt_token(account.token_ref)

        if message.kind == "dm":
            # Send direct message
            url = f"https://graph.facebook.com/v18.0/{account.page_id}/messages"
            payload = {
                "recipient": {
                    "id": thread.metadata.get("customer_id") or thread.metadata.get("sender_id")
                },
                "message": {
                    "text": message.body
                },
                "access_token": access_token
            }
        elif message.kind == "comment":
            # Reply to comment/post
            url = f"https://graph.facebook.com/v18.0/{thread.metadata.get('post_id')}/comments"
            payload = {
                "message": message.body,
                "access_token": access_token
            }
        else:
            logger.error(f"Unsupported message kind for Meta: {message.kind}")
            return False

        async with aiohttp.ClientSession() as client_session:
            async with client_session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    response_data = await response.json()
                    message.platform_message_id = response_data.get("id")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Meta API error: {response.status} - {error_text}")
                    return False

    async def _send_google_message(self, account: SocialAccount, message: SocialMessage, thread: SocialThread) -> bool:
        """Send message via Google Business Profile API."""
        # Google Business Profile doesn't support direct messaging
        # This would typically be for review responses
        if message.kind == "review_response":
            # Implementation would depend on Google My Business API
            logger.info("Google review response would be sent via GMB API")
            return True
        else:
            logger.warning("Google Business Profile messaging not fully supported")
            return False

    async def _check_rate_limit(self, platform: str) -> bool:
        """Check if platform rate limit allows request."""
        rate_info = self.rate_limits.get(platform)
        if not rate_info:
            return True

        now = datetime.utcnow()

        # Reset counters if hour has passed
        if rate_info["reset_at"] and now >= rate_info["reset_at"]:
            rate_info["current"] = 0
            rate_info["reset_at"] = now + timedelta(hours=1)
        elif not rate_info["reset_at"]:
            rate_info["reset_at"] = now + timedelta(hours=1)

        # Check if under limit
        return rate_info["current"] < rate_info["requests_per_hour"]

    async def _update_rate_limit(self, platform: str):
        """Update rate limit counter after successful request."""
        rate_info = self.rate_limits.get(platform)
        if rate_info:
            rate_info["current"] += 1

    async def _check_followup_conditions(self, thread_id: UUID, conditions: dict[str, Any], session: AsyncSession) -> bool:
        """Check if follow-up conditions are met."""
        if not conditions:
            return True

        # Check if no response by specified time
        no_response_by = conditions.get("if_no_response_by")
        if no_response_by:
            cutoff_time = datetime.fromisoformat(no_response_by.replace('Z', '+00:00'))

            # Check for customer messages after cutoff
            recent_messages_stmt = select(SocialMessage).where(
                and_(
                    SocialMessage.thread_id == thread_id,
                    SocialMessage.direction == "inbound",
                    SocialMessage.created_at > cutoff_time
                )
            )

            result = await session.execute(recent_messages_stmt)
            recent_messages = result.scalars().all()

            if recent_messages:
                return False  # Customer has responded, skip follow-up

        # Check quiet hours
        respect_quiet = conditions.get("respect_quiet_hours", True)
        if respect_quiet:
            current_hour = datetime.utcnow().hour
            if current_hour < 8 or current_hour > 21:  # 8 AM to 9 PM
                return False

        return True

    async def _create_followup_message(
        self,
        thread_id: UUID,
        follow_up_type: str,
        data: dict[str, Any],
        session: AsyncSession
    ) -> Optional[SocialMessage]:
        """Create follow-up message."""
        try:
            message_template = data.get("message_template", "")

            # Create follow-up message
            followup_message = SocialMessage(
                thread_id=thread_id,
                kind=follow_up_type,
                direction="outbound",
                body=message_template,
                sender_handle="myhibachichef",
                sender_name="My Hibachi Chef",
                metadata={
                    "is_followup": True,
                    "followup_type": follow_up_type,
                    "auto_generated": True
                }
            )

            session.add(followup_message)
            await session.flush()

            return followup_message

        except Exception as e:
            logger.error(f"Error creating follow-up message: {e}")
            return None

    async def _decrypt_token(self, token_ref: str) -> str:
        """Decrypt access token (placeholder - implement proper encryption)."""
        # In production, this should decrypt the token reference
        # For now, return placeholder
        return "placeholder_access_token"

    async def _fetch_account_details(self, account: SocialAccount) -> Optional[dict[str, Any]]:
        """Fetch account details from platform API."""
        # Placeholder implementation
        return {
            "page_name": account.page_name,
            "avatar_url": account.avatar_url,
            "last_updated": datetime.utcnow().isoformat()
        }

    def _extract_platform_from_event(self, event: OutboxEntry) -> Optional[str]:
        """Extract platform from event data."""
        data = event.event_data
        return data.get("platform") or data.get("source", "").replace("social_", "")
