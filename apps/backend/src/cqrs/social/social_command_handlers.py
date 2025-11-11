"""Social media CQRS command handlers."""

from datetime import datetime, timezone
import logging
from typing import Any

from cqrs.base import CommandHandler  # Phase 2C: Updated from api.app.cqrs.base
from cqrs.social.social_commands import (  # Phase 2C: Updated from api.app.cqrs.social_commands
    AcknowledgeReviewCommand,
    CreateLeadFromSocialCommand,
    CreateSocialAccountCommand,
    LinkSocialIdentityToCustomerCommand,
    SendSocialReplyCommand,
    UpdateThreadStatusCommand,
)
from models.legacy_core import Customer, Lead  # Phase 2C: Updated from api.app.models.core
from models.legacy_events import OutboxEntry  # Phase 2C: Updated from api.app.models.events
from models.legacy_social import (  # Phase 2C: Updated from api.app.models.social
    Review,
    SocialAccount,
    SocialIdentity,
    SocialMessage,
    SocialThread,
)
from services.social.social_service import (
    SocialService,
)  # Phase 2C: Updated from api.app.services.social_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CreateLeadFromSocialHandler(CommandHandler[CreateLeadFromSocialCommand]):
    """Handler for creating leads from social media interactions."""

    async def handle(
        self, command: CreateLeadFromSocialCommand, session: AsyncSession
    ) -> dict[str, Any]:
        try:
            # Check if lead already exists for this handle on this platform
            existing_stmt = (
                select(Lead)
                .join(SocialIdentity, Lead.id == SocialIdentity.customer_id)
                .where(
                    SocialIdentity.handle == command.handle,
                    SocialIdentity.platform == command.source,
                )
            )
            existing_lead = await session.execute(existing_stmt)
            existing_lead = existing_lead.scalar_one_or_none()

            if existing_lead:
                logger.info(f"Lead already exists for {command.handle} on {command.source}")
                return {"lead_id": existing_lead.id, "created": False, "reason": "already_exists"}

            # Create new lead
            lead_data = {
                "source": f"social_{command.source}",
                "phone": None,  # Will be filled if customer provides
                "email": None,  # Will be filled if customer provides
                "first_name": (
                    command.handle.replace("@", "").split(".")[0]
                    if "." in command.handle
                    else command.handle.replace("@", "")
                ),
                "last_name": None,
                "notes": f"Social media lead from {command.source}. Handle: {command.handle}",
                "metadata": {
                    **(command.metadata or {}),
                    "social_source": {
                        "platform": command.source,
                        "handle": command.handle,
                        "post_url": command.post_url,
                        "message_excerpt": command.message_excerpt,
                        "inferred_interest": command.inferred_interest,
                        "consent": {
                            "dm": command.consent_dm,
                            "sms": command.consent_sms,
                            "email": command.consent_email,
                        },
                    },
                },
            }

            lead = Lead(**lead_data)
            session.add(lead)
            await session.flush()

            # Create social identity linked to the lead
            identity_data = {
                "platform": command.source,
                "handle": command.handle,
                "customer_id": lead.id,  # Link to lead as customer
                "profile_data": {
                    "handle": command.handle,
                    "inferred_interest": command.inferred_interest,
                    "consent_status": {
                        "dm": command.consent_dm,
                        "sms": command.consent_sms,
                        "email": command.consent_email,
                    },
                },
            }

            social_identity = SocialIdentity(**identity_data)
            session.add(social_identity)
            await session.flush()

            # Create outbox event for lead creation
            event_data = {
                "event_type": "lead_created_from_social",
                "aggregate_type": "Lead",
                "aggregate_id": lead.id,
                "event_data": {
                    "lead_id": lead.id,
                    "source": command.source,
                    "handle": command.handle,
                    "thread_id": command.thread_id,
                    "consent": {
                        "dm": command.consent_dm,
                        "sms": command.consent_sms,
                        "email": command.consent_email,
                    },
                },
            }

            outbox_event = OutboxEntry(**event_data)
            session.add(outbox_event)

            await session.commit()

            logger.info(
                f"Created lead {lead.id} from social {command.source} handle {command.handle}"
            )
            return {
                "lead_id": lead.id,
                "social_identity_id": social_identity.id,
                "created": True,
                "handle": command.handle,
                "platform": command.source,
            }

        except Exception as e:
            logger.exception(f"Error creating lead from social: {e}")
            await session.rollback()
            raise


class SendSocialReplyHandler(CommandHandler[SendSocialReplyCommand]):
    """Handler for sending social media replies."""

    def __init__(self, social_service: SocialService):
        self.social_service = social_service

    async def handle(
        self, command: SendSocialReplyCommand, session: AsyncSession
    ) -> dict[str, Any]:
        try:
            # Get thread details
            thread_stmt = select(SocialThread).where(SocialThread.id == command.thread_id)
            thread_result = await session.execute(thread_stmt)
            thread = thread_result.scalar_one_or_none()

            if not thread:
                raise ValueError(f"Thread {command.thread_id} not found")

            # Create reply message record
            message_data = {
                "thread_id": command.thread_id,
                "kind": command.reply_kind,
                "direction": "outbound",
                "body": command.body,
                "sender_handle": "myhibachichef",  # Our business handle
                "sender_name": "My Hibachi Chef",
                "metadata": {
                    **(command.metadata or {}),
                    "safety": command.safety,
                    "requires_approval": command.requires_approval,
                    "scheduled_send_at": (
                        command.schedule_send_at.isoformat() if command.schedule_send_at else None
                    ),
                },
                "sent_at": command.schedule_send_at or datetime.now(timezone.utc),
            }

            message = SocialMessage(**message_data)
            session.add(message)
            await session.flush()

            # If not scheduled and approved, send immediately
            if not command.schedule_send_at and not command.requires_approval:
                # Use social service to send the actual message
                send_result = await self.social_service.send_reply(
                    thread=thread, message=message, session=session
                )

                # Update message with send result
                message.platform_message_id = send_result.get("message_id")
                message.metadata = {**message.metadata, "send_result": send_result}

            # Update thread last activity
            thread.updated_at = datetime.now(timezone.utc)
            thread.last_message_at = datetime.now(timezone.utc)

            # Create outbox event for reply sent
            event_data = {
                "event_type": "social_reply_sent",
                "aggregate_type": "SocialThread",
                "aggregate_id": command.thread_id,
                "event_data": {
                    "thread_id": command.thread_id,
                    "message_id": message.id,
                    "reply_kind": command.reply_kind,
                    "body": command.body,
                    "requires_approval": command.requires_approval,
                    "scheduled": command.schedule_send_at is not None,
                },
            }

            outbox_event = OutboxEntry(**event_data)
            session.add(outbox_event)

            await session.commit()

            logger.info(
                f"Social reply created for thread {command.thread_id}, message {message.id}"
            )
            return {
                "message_id": message.id,
                "thread_id": command.thread_id,
                "sent": not command.requires_approval and not command.schedule_send_at,
                "scheduled": command.schedule_send_at is not None,
                "requires_approval": command.requires_approval,
            }

        except Exception as e:
            logger.exception(f"Error sending social reply: {e}")
            await session.rollback()
            raise


class LinkSocialIdentityToCustomerHandler(CommandHandler[LinkSocialIdentityToCustomerCommand]):
    """Handler for linking social identities to customers."""

    async def handle(
        self, command: LinkSocialIdentityToCustomerCommand, session: AsyncSession
    ) -> dict[str, Any]:
        try:
            # Get social identity
            identity_stmt = select(SocialIdentity).where(
                SocialIdentity.id == command.social_identity_id
            )
            identity_result = await session.execute(identity_stmt)
            identity = identity_result.scalar_one_or_none()

            if not identity:
                raise ValueError(f"Social identity {command.social_identity_id} not found")

            # Get customer
            customer_stmt = select(Customer).where(Customer.id == command.customer_id)
            customer_result = await session.execute(customer_stmt)
            customer = customer_result.scalar_one_or_none()

            if not customer:
                raise ValueError(f"Customer {command.customer_id} not found")

            # Update social identity with customer link
            identity.customer_id = command.customer_id
            identity.metadata = {
                **(identity.metadata or {}),
                "customer_link": {
                    "confidence_score": command.confidence_score,
                    "verification_method": command.verification_method,
                    "linked_at": datetime.now(timezone.utc).isoformat(),
                    "notes": command.notes,
                },
            }

            # Create outbox event for identity linking
            event_data = {
                "event_type": "social_identity_linked",
                "aggregate_type": "Customer",
                "aggregate_id": command.customer_id,
                "event_data": {
                    "customer_id": command.customer_id,
                    "social_identity_id": command.social_identity_id,
                    "platform": identity.platform,
                    "handle": identity.handle,
                    "confidence_score": command.confidence_score,
                    "verification_method": command.verification_method,
                },
            }

            outbox_event = OutboxEntry(**event_data)
            session.add(outbox_event)

            await session.commit()

            logger.info(
                f"Linked social identity {command.social_identity_id} to customer {command.customer_id}"
            )
            return {
                "social_identity_id": command.social_identity_id,
                "customer_id": command.customer_id,
                "platform": identity.platform,
                "handle": identity.handle,
                "confidence_score": command.confidence_score,
            }

        except Exception as e:
            logger.exception(f"Error linking social identity: {e}")
            await session.rollback()
            raise


class AcknowledgeReviewHandler(CommandHandler[AcknowledgeReviewCommand]):
    """Handler for acknowledging reviews."""

    async def handle(
        self, command: AcknowledgeReviewCommand, session: AsyncSession
    ) -> dict[str, Any]:
        try:
            # Get review
            review_stmt = select(Review).where(Review.id == command.review_id)
            review_result = await session.execute(review_stmt)
            review = review_result.scalar_one_or_none()

            if not review:
                raise ValueError(f"Review {command.review_id} not found")

            # Update review status
            review.status = "acknowledged"
            review.acknowledged_at = datetime.now(timezone.utc)
            review.acknowledged_by = command.acknowledged_by
            review.assigned_to = command.assigned_to
            review.priority_level = command.priority_level
            review.metadata = {
                **(review.metadata or {}),
                "acknowledgment": {
                    "acknowledged_by": command.acknowledged_by,
                    "acknowledged_at": datetime.now(timezone.utc).isoformat(),
                    "notes": command.notes,
                    "priority_level": command.priority_level,
                    "assigned_to": command.assigned_to,
                },
            }

            # Create outbox event
            event_data = {
                "event_type": "review_acknowledged",
                "aggregate_type": "Review",
                "aggregate_id": command.review_id,
                "event_data": {
                    "review_id": command.review_id,
                    "acknowledged_by": command.acknowledged_by,
                    "priority_level": command.priority_level,
                    "assigned_to": command.assigned_to,
                    "rating": review.rating,
                },
            }

            outbox_event = OutboxEntry(**event_data)
            session.add(outbox_event)

            await session.commit()

            logger.info(f"Acknowledged review {command.review_id}")
            return {
                "review_id": command.review_id,
                "status": "acknowledged",
                "acknowledged_by": command.acknowledged_by,
                "priority_level": command.priority_level,
            }

        except Exception as e:
            logger.exception(f"Error acknowledging review: {e}")
            await session.rollback()
            raise


class UpdateThreadStatusHandler(CommandHandler[UpdateThreadStatusCommand]):
    """Handler for updating thread status."""

    async def handle(
        self, command: UpdateThreadStatusCommand, session: AsyncSession
    ) -> dict[str, Any]:
        try:
            # Get thread
            thread_stmt = select(SocialThread).where(SocialThread.id == command.thread_id)
            thread_result = await session.execute(thread_stmt)
            thread = thread_result.scalar_one_or_none()

            if not thread:
                raise ValueError(f"Thread {command.thread_id} not found")

            old_status = thread.status

            # Update thread
            thread.status = command.status
            thread.assigned_to = command.assigned_to
            thread.updated_at = datetime.now(timezone.utc)

            # Update metadata with status change info
            existing_metadata = thread.metadata or {}
            existing_history = existing_metadata.get("status_history", [])

            thread.metadata = {
                **existing_metadata,
                "status_history": [
                    *existing_history,
                    {
                        "from_status": old_status,
                        "to_status": command.status,
                        "updated_by": command.updated_by,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "reason": command.reason,
                    },
                ],
                "tags": command.tags or existing_metadata.get("tags", []),
            }

            # Create outbox event
            event_data = {
                "event_type": "thread_status_updated",
                "aggregate_type": "SocialThread",
                "aggregate_id": command.thread_id,
                "event_data": {
                    "thread_id": command.thread_id,
                    "old_status": old_status,
                    "new_status": command.status,
                    "updated_by": command.updated_by,
                    "reason": command.reason,
                    "assigned_to": command.assigned_to,
                },
            }

            outbox_event = OutboxEntry(**event_data)
            session.add(outbox_event)

            await session.commit()

            logger.info(
                f"Updated thread {command.thread_id} status from {old_status} to {command.status}"
            )
            return {
                "thread_id": command.thread_id,
                "old_status": old_status,
                "new_status": command.status,
                "assigned_to": command.assigned_to,
            }

        except Exception as e:
            logger.exception(f"Error updating thread status: {e}")
            await session.rollback()
            raise


class CreateSocialAccountHandler(CommandHandler[CreateSocialAccountCommand]):
    """Handler for creating/connecting social media accounts."""

    async def handle(
        self, command: CreateSocialAccountCommand, session: AsyncSession
    ) -> dict[str, Any]:
        try:
            # Check if account already exists
            existing_stmt = select(SocialAccount).where(
                SocialAccount.platform == command.platform, SocialAccount.page_id == command.page_id
            )
            existing_result = await session.execute(existing_stmt)
            existing_account = existing_result.scalar_one_or_none()

            if existing_account:
                logger.info(
                    f"Social account already exists for {command.platform} page {command.page_id}"
                )
                return {
                    "account_id": existing_account.id,
                    "created": False,
                    "reason": "already_exists",
                }

            # Create new social account
            account_data = {
                "platform": command.platform,
                "page_id": command.page_id,
                "page_name": command.page_name,
                "handle": command.handle,
                "profile_url": command.profile_url,
                "avatar_url": command.avatar_url,
                "is_active": True,
                "connected_at": datetime.now(timezone.utc),
                "connected_by": command.connected_by,
                "token_ref": command.token_ref,
                "metadata": command.metadata or {},
            }

            account = SocialAccount(**account_data)
            session.add(account)
            await session.flush()

            # Create outbox event
            event_data = {
                "event_type": "social_account_connected",
                "aggregate_type": "SocialAccount",
                "aggregate_id": account.id,
                "event_data": {
                    "account_id": account.id,
                    "platform": command.platform,
                    "page_id": command.page_id,
                    "page_name": command.page_name,
                    "connected_by": command.connected_by,
                },
            }

            outbox_event = OutboxEntry(**event_data)
            session.add(outbox_event)

            await session.commit()

            logger.info(f"Created social account {account.id} for {command.platform}")
            return {
                "account_id": account.id,
                "created": True,
                "platform": command.platform,
                "page_name": command.page_name,
            }

        except Exception as e:
            logger.exception(f"Error creating social account: {e}")
            await session.rollback()
            raise
