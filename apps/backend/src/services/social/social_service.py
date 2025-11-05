"""Social media integration service."""

from datetime import datetime
import logging
from typing import Any
from uuid import UUID

from cqrs.registry import get_command_bus  # Phase 2C: Updated from api.app.cqrs.registry
from models.legacy_social import (  # Phase 2C: Updated from api.app.models.social
    MessageDirection,
    MessageKind,
    SocialAccount,
    SocialIdentity,
    SocialMessage,
    SocialPlatform,
    SocialThread,
)
from schemas.social import SocialMessageCreate  # Phase 2C: Updated from api.app.schemas.social

# Newsletter opt-out service
from services.newsletter_service import (
    NewsletterService,
)  # Phase 2C: Updated from api.app.services.newsletter_service
from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class SocialService:
    """Service for social media integrations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.command_bus = get_command_bus()

    async def process_instagram_webhook(self, payload: dict[str, Any]) -> None:
        """Process Instagram webhook payload."""
        try:
            for entry in payload.get("entry", []):
                await self._process_instagram_entry(entry)
        except Exception as e:
            logger.error(f"Instagram webhook processing error: {e}", exc_info=True)
            raise

    async def process_facebook_webhook(self, payload: dict[str, Any]) -> None:
        """Process Facebook webhook payload."""
        try:
            for entry in payload.get("entry", []):
                await self._process_facebook_entry(entry)
        except Exception as e:
            logger.error(f"Facebook webhook processing error: {e}", exc_info=True)
            raise

    async def _process_instagram_entry(self, entry: dict[str, Any]) -> None:
        """Process a single Instagram webhook entry."""
        page_id = entry.get("id")

        # Get the associated account
        account_result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.platform == SocialPlatform.INSTAGRAM,
                SocialAccount.page_id == page_id,
                SocialAccount.is_active,
                SocialAccount.deleted_at.is_(None),
            )
        )
        account = account_result.scalar_one_or_none()

        if not account:
            logger.warning(f"No active Instagram account found for page_id: {page_id}")
            return

        # Process messaging events
        for messaging in entry.get("messaging", []):
            await self._process_instagram_message(account, messaging)

        # Process feed changes (comments, mentions, etc.)
        for change in entry.get("changes", []):
            await self._process_instagram_change(account, change)

    async def _process_instagram_message(
        self, account: SocialAccount, messaging: dict[str, Any]
    ) -> None:
        """Process Instagram direct message."""
        sender = messaging.get("sender", {})
        recipient = messaging.get("recipient", {})
        message_data = messaging.get("message", {})

        # Determine if this is incoming or outgoing
        is_incoming = sender.get("id") != account.page_id
        direction = MessageDirection.IN if is_incoming else MessageDirection.OUT

        if is_incoming:
            other_party_id = sender.get("id")
            other_party_handle = sender.get("username", other_party_id)
        else:
            other_party_id = recipient.get("id")
            other_party_handle = recipient.get("username", other_party_id)

        # Check for STOP/START commands in incoming messages (newsletter opt-out)
        if is_incoming and message_data.get("text"):
            message_text = message_data.get("text", "").strip()
            newsletter_service = NewsletterService(self.db)

            if newsletter_service.is_stop_command(message_text):
                # Get Instagram handle as identifier
                instagram_handle = sender.get("username") or sender.get("id")

                success, response_msg = await newsletter_service.process_stop_command(
                    phone=None,  # Instagram doesn't have phone
                    email=None,  # Use handle as identifier
                    channel="instagram",
                    instagram_handle=instagram_handle,
                )

                # Send confirmation via Instagram DM
                thread_ref = f"ig_{sender.get('id')}_{recipient.get('id')}"

                # Find or create thread for response
                social_identity = await self._get_or_create_social_identity(
                    platform=SocialPlatform.INSTAGRAM,
                    handle=other_party_handle,
                    profile_data=sender,
                )

                thread = await self._get_or_create_thread(
                    platform=SocialPlatform.INSTAGRAM,
                    thread_ref=thread_ref,
                    account=account,
                    social_identity=social_identity,
                )

                await self.send_instagram_message(
                    thread.id, response_msg, {"is_system_message": True}
                )

                logger.info(f"Processed STOP command from Instagram @{instagram_handle}: {success}")
                return  # Don't process with AI

            if newsletter_service.is_start_command(message_text):
                instagram_handle = sender.get("username") or sender.get("id")
                display_name = sender.get("name")

                success, response_msg = await newsletter_service.process_start_command(
                    phone=None,
                    name=display_name,
                    channel="instagram",
                    instagram_handle=instagram_handle,
                )

                # Send confirmation via Instagram DM
                thread_ref = f"ig_{sender.get('id')}_{recipient.get('id')}"

                social_identity = await self._get_or_create_social_identity(
                    platform=SocialPlatform.INSTAGRAM,
                    handle=other_party_handle,
                    profile_data=sender,
                )

                thread = await self._get_or_create_thread(
                    platform=SocialPlatform.INSTAGRAM,
                    thread_ref=thread_ref,
                    account=account,
                    social_identity=social_identity,
                )

                await self.send_instagram_message(
                    thread.id, response_msg, {"is_system_message": True}
                )

                logger.info(
                    f"Processed START command from Instagram @{instagram_handle}: {success}"
                )
                return  # Don't process with AI

        # Normal message processing - get or create social identity
        social_identity = await self._get_or_create_social_identity(
            platform=SocialPlatform.INSTAGRAM,
            handle=other_party_handle,
            profile_data=sender if is_incoming else recipient,
        )

        # Get or create thread
        thread_ref = f"ig_{sender.get('id')}_{recipient.get('id')}"
        thread = await self._get_or_create_thread(
            platform=SocialPlatform.INSTAGRAM,
            thread_ref=thread_ref,
            account=account,
            social_identity=social_identity,
        )

        # Create message
        message_create = SocialMessageCreate(
            thread_id=thread.id,
            message_ref=messaging.get("id"),
            direction=direction,
            kind=MessageKind.DM,
            author_handle=sender.get("username") if is_incoming else None,
            author_name=sender.get("name") if is_incoming else account.page_name,
            body=message_data.get("text"),
            media=self._extract_media(message_data),
            is_public=False,
            metadata={"platform_data": messaging, "timestamp": messaging.get("timestamp")},
        )

        await self._create_message(message_create)

        # If incoming message, trigger AI processing
        if is_incoming and direction == MessageDirection.IN:
            await self._trigger_ai_response(thread.id, message_create)

    async def _process_instagram_change(
        self, account: SocialAccount, change: dict[str, Any]
    ) -> None:
        """Process Instagram feed changes (comments, mentions)."""
        field = change.get("field")
        value = change.get("value", {})

        if field == "comments":
            await self._process_instagram_comment(account, value)
        elif field == "mentions":
            await self._process_instagram_mention(account, value)

    async def _process_facebook_entry(self, entry: dict[str, Any]) -> None:
        """Process a single Facebook webhook entry."""
        page_id = entry.get("id")

        # Get the associated account
        account_result = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.platform == SocialPlatform.FACEBOOK,
                SocialAccount.page_id == page_id,
                SocialAccount.is_active,
                SocialAccount.deleted_at.is_(None),
            )
        )
        account = account_result.scalar_one_or_none()

        if not account:
            logger.warning(f"No active Facebook account found for page_id: {page_id}")
            return

        # Process messaging events
        for messaging in entry.get("messaging", []):
            await self._process_facebook_message(account, messaging)

        # Process feed changes (comments, mentions, etc.)
        for change in entry.get("changes", []):
            await self._process_facebook_change(account, change)

    async def _process_facebook_message(
        self, account: SocialAccount, messaging: dict[str, Any]
    ) -> None:
        """Process Facebook Messenger message."""
        sender = messaging.get("sender", {})
        recipient = messaging.get("recipient", {})
        message_data = messaging.get("message", {})

        # Determine if this is incoming or outgoing
        is_incoming = sender.get("id") != account.page_id
        direction = MessageDirection.IN if is_incoming else MessageDirection.OUT

        if is_incoming:
            other_party_id = sender.get("id")
        else:
            other_party_id = recipient.get("id")

        # Check for STOP/START commands in incoming messages (newsletter opt-out)
        if is_incoming and message_data.get("text"):
            message_text = message_data.get("text", "").strip()
            newsletter_service = NewsletterService(self.db)

            if newsletter_service.is_stop_command(message_text):
                # Use Facebook ID as identifier
                fb_id = sender.get("id")

                success, response_msg = await newsletter_service.process_stop_command(
                    phone=None, email=None, channel="facebook", facebook_id=fb_id
                )

                # Send confirmation via Facebook Messenger
                thread_ref = f"fb_{sender.get('id')}_{recipient.get('id')}"

                # Find or create thread for response
                social_identity = await self._get_or_create_social_identity(
                    platform=SocialPlatform.FACEBOOK, handle=fb_id, profile_data=sender
                )

                thread = await self._get_or_create_thread(
                    platform=SocialPlatform.FACEBOOK,
                    thread_ref=thread_ref,
                    account=account,
                    social_identity=social_identity,
                )

                await self.send_facebook_message(
                    thread.id, response_msg, {"is_system_message": True}
                )

                logger.info(f"Processed STOP command from Facebook ID {fb_id}: {success}")
                return  # Don't process with AI

            if newsletter_service.is_start_command(message_text):
                fb_id = sender.get("id")

                success, response_msg = await newsletter_service.process_start_command(
                    phone=None,
                    name=None,  # Can be fetched from Facebook profile if needed
                    channel="facebook",
                    facebook_id=fb_id,
                )

                # Send confirmation via Facebook Messenger
                thread_ref = f"fb_{sender.get('id')}_{recipient.get('id')}"

                social_identity = await self._get_or_create_social_identity(
                    platform=SocialPlatform.FACEBOOK, handle=fb_id, profile_data=sender
                )

                thread = await self._get_or_create_thread(
                    platform=SocialPlatform.FACEBOOK,
                    thread_ref=thread_ref,
                    account=account,
                    social_identity=social_identity,
                )

                await self.send_facebook_message(
                    thread.id, response_msg, {"is_system_message": True}
                )

                logger.info(f"Processed START command from Facebook ID {fb_id}: {success}")
                return  # Don't process with AI

        # Normal message processing - get or create social identity
        social_identity = await self._get_or_create_social_identity(
            platform=SocialPlatform.FACEBOOK,
            handle=other_party_id,
            profile_data=sender if is_incoming else recipient,
        )

        # Get or create thread
        thread_ref = f"fb_{sender.get('id')}_{recipient.get('id')}"
        thread = await self._get_or_create_thread(
            platform=SocialPlatform.FACEBOOK,
            thread_ref=thread_ref,
            account=account,
            social_identity=social_identity,
        )

        # Create message
        message_create = SocialMessageCreate(
            thread_id=thread.id,
            message_ref=messaging.get("mid") or messaging.get("id"),
            direction=direction,
            kind=MessageKind.DM,
            author_handle=other_party_id if is_incoming else None,
            author_name=sender.get("name") if is_incoming else account.page_name,
            body=message_data.get("text"),
            media=self._extract_media(message_data),
            is_public=False,
            metadata={"platform_data": messaging, "timestamp": messaging.get("timestamp")},
        )

        await self._create_message(message_create)

        # If incoming message, trigger AI processing
        if is_incoming and direction == MessageDirection.IN:
            await self._trigger_ai_response(thread.id, message_create)

    async def _process_facebook_change(
        self, account: SocialAccount, change: dict[str, Any]
    ) -> None:
        """Process Facebook feed changes (comments, posts)."""
        field = change.get("field")
        value = change.get("value", {})

        if field == "comments":
            await self._process_facebook_comment(account, value)

    async def _process_facebook_comment(
        self, account: SocialAccount, comment_data: dict[str, Any]
    ) -> None:
        """Process Facebook comment."""
        post_id = comment_data.get("post_id") or comment_data.get("parent_id")
        comment_id = comment_data.get("comment_id") or comment_data.get("id")

        if not comment_id:
            return

        # Get commenter info
        commenter = comment_data.get("from", {})
        commenter_id = commenter.get("id", "unknown")

        # Get or create social identity
        social_identity = await self._get_or_create_social_identity(
            platform=SocialPlatform.FACEBOOK, handle=commenter_id, profile_data=commenter
        )

        # Get or create thread (using post as thread reference)
        thread_ref = f"fb_post_{post_id}"
        thread = await self._get_or_create_thread(
            platform=SocialPlatform.FACEBOOK,
            thread_ref=thread_ref,
            account=account,
            social_identity=social_identity,
            context_url=f"https://www.facebook.com/{post_id}",
        )

        # Create message
        message_create = SocialMessageCreate(
            thread_id=thread.id,
            message_ref=comment_id,
            direction=MessageDirection.IN,
            kind=MessageKind.COMMENT,
            author_handle=commenter_id,
            author_name=commenter.get("name", commenter_id),
            body=comment_data.get("message"),
            is_public=True,
            requires_approval=True,  # Public comments need approval
            metadata={"platform_data": comment_data, "post_id": post_id},
        )

        await self._create_message(message_create)

        # Trigger AI processing for comment response
        await self._trigger_ai_response(thread.id, message_create)

    async def _process_instagram_comment(
        self, account: SocialAccount, comment_data: dict[str, Any]
    ) -> None:
        """Process Instagram comment."""
        post_id = comment_data.get("media_id") or comment_data.get("parent_id")
        comment_id = comment_data.get("id")

        if not comment_id:
            return

        # Get commenter info
        commenter = comment_data.get("from", {})
        commenter_handle = commenter.get("username", commenter.get("id", "unknown"))

        # Get or create social identity
        social_identity = await self._get_or_create_social_identity(
            platform=SocialPlatform.INSTAGRAM, handle=commenter_handle, profile_data=commenter
        )

        # Get or create thread (using post as thread reference)
        thread_ref = f"ig_post_{post_id}"
        thread = await self._get_or_create_thread(
            platform=SocialPlatform.INSTAGRAM,
            thread_ref=thread_ref,
            account=account,
            social_identity=social_identity,
            context_url=f"https://www.instagram.com/p/{post_id}/",
        )

        # Create message
        message_create = SocialMessageCreate(
            thread_id=thread.id,
            message_ref=comment_id,
            direction=MessageDirection.IN,
            kind=MessageKind.COMMENT,
            author_handle=commenter_handle,
            author_name=commenter.get("name", commenter_handle),
            body=comment_data.get("text"),
            is_public=True,
            requires_approval=True,  # Public comments need approval
            metadata={"platform_data": comment_data, "post_id": post_id},
        )

        await self._create_message(message_create)

        # Trigger AI processing for comment response
        await self._trigger_ai_response(thread.id, message_create)

    async def _get_or_create_social_identity(
        self, platform: SocialPlatform, handle: str, profile_data: dict[str, Any] | None = None
    ) -> SocialIdentity:
        """Get or create a social identity."""
        # Try to find existing identity
        result = await self.db.execute(
            select(SocialIdentity).where(
                SocialIdentity.platform == platform, SocialIdentity.handle == handle
            )
        )
        identity = result.scalar_one_or_none()

        if identity:
            # Update last active timestamp
            await self.db.execute(
                update(SocialIdentity)
                .where(SocialIdentity.id == identity.id)
                .values(last_active_at=datetime.utcnow())
            )
            return identity

        # Create new identity
        identity_data = {
            "platform": platform,
            "handle": handle,
            "display_name": profile_data.get("name") if profile_data else None,
            "avatar_url": profile_data.get("profile_pic") if profile_data else None,
            "last_active_at": datetime.utcnow(),
        }

        result = await self.db.execute(
            insert(SocialIdentity).values(**identity_data).returning(SocialIdentity)
        )

        return result.scalar_one()

    async def _get_or_create_thread(
        self,
        platform: SocialPlatform,
        thread_ref: str,
        account: SocialAccount,
        social_identity: SocialIdentity,
        context_url: str | None = None,
    ) -> SocialThread:
        """Get or create a social thread."""
        # Try to find existing thread
        result = await self.db.execute(
            select(SocialThread).where(
                SocialThread.account_id == account.id, SocialThread.thread_ref == thread_ref
            )
        )
        thread = result.scalar_one_or_none()

        if thread:
            # Update last message timestamp
            await self.db.execute(
                update(SocialThread)
                .where(SocialThread.id == thread.id)
                .values(last_message_at=datetime.utcnow())
            )
            return thread

        # Create new thread
        thread_data = {
            "platform": platform,
            "thread_ref": thread_ref,
            "account_id": account.id,
            "social_identity_id": social_identity.id,
            "context_url": context_url,
            "last_message_at": datetime.utcnow(),
        }

        result = await self.db.execute(
            insert(SocialThread).values(**thread_data).returning(SocialThread)
        )

        return result.scalar_one()

    async def _create_message(self, message_create: SocialMessageCreate) -> SocialMessage:
        """Create a social message."""
        result = await self.db.execute(
            insert(SocialMessage)
            .values(**message_create.model_dump(exclude_unset=True))
            .returning(SocialMessage)
        )

        message = result.scalar_one()

        # Update thread counters
        await self.db.execute(
            update(SocialThread)
            .where(SocialThread.id == message_create.thread_id)
            .values(
                message_count=SocialThread.message_count + 1,
                unread_count=SocialThread.unread_count
                + (1 if message_create.direction == MessageDirection.IN else 0),
                last_message_at=datetime.utcnow(),
            )
        )

        return message

    def _extract_media(self, message_data: dict[str, Any]) -> dict[str, Any] | None:
        """Extract media attachments from message data."""
        media = []

        # Extract attachments
        for attachment in message_data.get("attachments", []):
            attachment_type = attachment.get("type")
            payload = attachment.get("payload", {})

            if attachment_type == "image":
                media.append(
                    {
                        "type": "image",
                        "url": payload.get("url"),
                        "sticker_id": payload.get("sticker_id"),
                    }
                )
            elif attachment_type == "video":
                media.append({"type": "video", "url": payload.get("url")})
            elif attachment_type == "audio":
                media.append({"type": "audio", "url": payload.get("url")})

        return {"attachments": media} if media else None

    async def _trigger_ai_response(self, thread_id: UUID, message: SocialMessageCreate) -> None:
        """Trigger AI processing for message response."""
        # This would integrate with your AI API
        # For now, we'll just log the trigger
        logger.info(f"Triggering AI response for thread {thread_id}, message kind: {message.kind}")

        # TODO: Implement AI API integration
        # - Send message context to AI API
        # - AI generates appropriate response
        # - Response gets queued for approval if needed
        # - Approved responses get sent via platform API

    async def setup_instagram_webhooks(self, account_data: dict[str, Any]) -> dict[str, Any]:
        """Set up Instagram webhook subscriptions."""
        # This would use Instagram Graph API to set up webhooks
        # Implementation depends on your Instagram app configuration

        logger.info(f"Setting up Instagram webhooks for account: {account_data.get('page_id')}")

        # TODO: Implement actual Instagram Graph API webhook setup
        # - Subscribe to messaging, comments, mentions events
        # - Verify webhook endpoint
        # - Store webhook configuration

        return {"status": "configured", "subscriptions": ["messaging", "comments", "mentions"]}

    async def remove_instagram_webhooks(self, account_id: str) -> None:
        """Remove Instagram webhook subscriptions."""
        logger.info(f"Removing Instagram webhooks for account: {account_id}")

        # TODO: Implement actual Instagram Graph API webhook removal
        # - Unsubscribe from all events
        # - Clean up stored configurations

    async def send_instagram_message(
        self, thread_id: UUID, message_body: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Send a message via Instagram API."""
        try:
            # Get thread and account info
            result = await self.db.execute(
                select(SocialThread)
                .options(selectinload(SocialThread.account))
                .where(SocialThread.id == thread_id)
            )
            thread = result.scalar_one_or_none()

            if not thread:
                raise ValueError(f"Thread not found: {thread_id}")

            # TODO: Implement actual Instagram Graph API message sending
            # - Use stored access token
            # - Send message via Graph API
            # - Handle rate limiting and errors

            # Create outgoing message record
            message_create = SocialMessageCreate(
                thread_id=thread_id,
                direction=MessageDirection.OUT,
                kind=MessageKind.DM,
                body=message_body,
                ai_generated=metadata.get("ai_generated", False) if metadata else False,
                metadata=metadata,
            )

            await self._create_message(message_create)

            logger.info(f"Instagram message sent for thread {thread_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Instagram message: {e}", exc_info=True)
            return False

    async def send_facebook_message(
        self, thread_id: UUID, message_body: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Send a message via Facebook Messenger API."""
        try:
            # Get thread and account info
            result = await self.db.execute(
                select(SocialThread)
                .options(selectinload(SocialThread.account))
                .where(SocialThread.id == thread_id)
            )
            thread = result.scalar_one_or_none()

            if not thread:
                raise ValueError(f"Thread not found: {thread_id}")

            # TODO: Implement actual Facebook Graph API message sending
            # - Use stored access token
            # - Send message via Graph API
            # - Handle rate limiting and errors

            # Create outgoing message record
            message_create = SocialMessageCreate(
                thread_id=thread_id,
                direction=MessageDirection.OUT,
                kind=MessageKind.DM,
                body=message_body,
                ai_generated=metadata.get("ai_generated", False) if metadata else False,
                metadata=metadata,
            )

            await self._create_message(message_create)

            logger.info(f"Facebook message sent for thread {thread_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Facebook message: {e}", exc_info=True)
            return False

    async def setup_facebook_webhooks(self, account_data: dict[str, Any]) -> dict[str, Any]:
        """Set up Facebook webhook subscriptions."""
        logger.info(f"Setting up Facebook webhooks for account: {account_data.get('page_id')}")

        # TODO: Implement actual Facebook Graph API webhook setup
        # - Subscribe to messaging, feed, comments events
        # - Verify webhook endpoint
        # - Store webhook configuration

        return {"status": "configured", "subscriptions": ["messaging", "feed", "comments"]}

    async def remove_facebook_webhooks(self, account_id: str) -> None:
        """Remove Facebook webhook subscriptions."""
        logger.info(f"Removing Facebook webhooks for account: {account_id}")

        # TODO: Implement actual Facebook Graph API webhook removal
        # - Unsubscribe from all events
        # - Clean up stored configurations
