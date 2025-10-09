"""Social media projectors for read model updates."""

import json
import logging
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.events import OutboxEntry
from app.models.read import CustomerSummary, LeadSummary

logger = logging.getLogger(__name__)


class SocialProjector:
    """Projector for social media events to read models."""

    def __init__(self):
        self.handlers = {
            "social_thread_created": self._handle_thread_created,
            "social_message_received": self._handle_message_received,
            "social_reply_sent": self._handle_reply_sent,
            "lead_created_from_social": self._handle_lead_created,
            "social_identity_linked": self._handle_identity_linked,
            "review_received": self._handle_review_received,
            "review_acknowledged": self._handle_review_acknowledged,
            "review_escalated": self._handle_review_escalated,
            "thread_status_updated": self._handle_thread_status_updated,
            "social_account_connected": self._handle_account_connected
        }

    async def process_event(self, event: OutboxEntry, session: AsyncSession) -> bool:
        """Process a social media event and update read models."""
        try:
            handler = self.handlers.get(event.event_type)
            if not handler:
                logger.debug(f"No handler for event type: {event.event_type}")
                return False

            await handler(event, session)
            logger.info(f"Processed {event.event_type} event {event.id}")
            return True

        except Exception as e:
            logger.error(f"Error processing social event {event.id}: {e}")
            raise

    async def _handle_thread_created(self, event: OutboxEntry, session: AsyncSession):
        """Handle social thread creation event."""
        data = event.event_data
        thread_id = data.get("thread_id")
        platform = data.get("platform")
        customer_handle = data.get("customer_handle")

        # Update social inbox entry
        await self._upsert_social_inbox_entry(
            session=session,
            thread_id=thread_id,
            platform=platform,
            last_activity="thread_created",
            metadata={
                "customer_handle": customer_handle,
                "created_at": event.created_at.isoformat()
            }
        )

        # If customer is linked, update customer summary
        if data.get("customer_id"):
            await self._update_customer_social_activity(
                session=session,
                customer_id=data["customer_id"],
                platform=platform,
                activity_type="thread_created"
            )

    async def _handle_message_received(self, event: OutboxEntry, session: AsyncSession):
        """Handle incoming social message event."""
        data = event.event_data
        thread_id = data.get("thread_id")
        message_id = data.get("message_id")
        platform = data.get("platform")
        customer_handle = data.get("customer_handle")
        message_kind = data.get("message_kind")

        # Update social inbox with latest message
        await self._upsert_social_inbox_entry(
            session=session,
            thread_id=thread_id,
            platform=platform,
            last_activity="message_received",
            metadata={
                "latest_message_id": message_id,
                "customer_handle": customer_handle,
                "message_kind": message_kind,
                "received_at": event.created_at.isoformat()
            }
        )

        # Update thread unread count
        await session.execute(
            text("""
                UPDATE social.social_threads
                SET unread_count = unread_count + 1,
                    last_message_at = :timestamp
                WHERE id = :thread_id
            """),
            {"thread_id": thread_id, "timestamp": event.created_at}
        )

        # Update customer engagement if linked
        if data.get("customer_id"):
            await self._update_customer_social_activity(
                session=session,
                customer_id=data["customer_id"],
                platform=platform,
                activity_type="message_received"
            )

    async def _handle_reply_sent(self, event: OutboxEntry, session: AsyncSession):
        """Handle outgoing social reply event."""
        data = event.event_data
        thread_id = data.get("thread_id")
        message_id = data.get("message_id")

        # Update social inbox
        await self._upsert_social_inbox_entry(
            session=session,
            thread_id=thread_id,
            platform=None,  # Will be fetched from thread
            last_activity="reply_sent",
            metadata={
                "latest_reply_id": message_id,
                "reply_sent_at": event.created_at.isoformat(),
                "requires_approval": data.get("requires_approval", False)
            }
        )

        # Update thread last message time
        await session.execute(
            text("""
                UPDATE social.social_threads
                SET last_message_at = :timestamp
                WHERE id = :thread_id
            """),
            {"thread_id": thread_id, "timestamp": event.created_at}
        )

    async def _handle_lead_created(self, event: OutboxEntry, session: AsyncSession):
        """Handle lead creation from social event."""
        data = event.event_data
        lead_id = data.get("lead_id")
        platform = data.get("source", "").replace("social_", "")
        handle = data.get("handle")

        # Update lead summary with social context
        lead_stmt = select(LeadSummary).where(LeadSummary.id == lead_id)
        result = await session.execute(lead_stmt)
        lead_summary = result.scalar_one_or_none()

        if lead_summary:
            # Update existing summary
            social_context = lead_summary.metadata.get("social_context", {}) if lead_summary.metadata else {}
            social_context[platform] = {
                "handle": handle,
                "thread_id": data.get("thread_id"),
                "consent": data.get("consent", {}),
                "created_at": event.created_at.isoformat()
            }

            lead_summary.metadata = {
                **(lead_summary.metadata or {}),
                "social_context": social_context
            }
        else:
            # Create new lead summary
            lead_summary = LeadSummary(
                id=lead_id,
                source=f"social_{platform}",
                status="new",
                metadata={
                    "social_context": {
                        platform: {
                            "handle": handle,
                            "thread_id": data.get("thread_id"),
                            "consent": data.get("consent", {}),
                            "created_at": event.created_at.isoformat()
                        }
                    }
                }
            )
            session.add(lead_summary)

    async def _handle_identity_linked(self, event: OutboxEntry, session: AsyncSession):
        """Handle social identity linked to customer event."""
        data = event.event_data
        customer_id = data.get("customer_id")
        platform = data.get("platform")
        handle = data.get("handle")

        # Update customer summary with social identity
        customer_stmt = select(CustomerSummary).where(CustomerSummary.id == customer_id)
        result = await session.execute(customer_stmt)
        customer_summary = result.scalar_one_or_none()

        if customer_summary:
            social_profiles = customer_summary.metadata.get("social_profiles", {}) if customer_summary.metadata else {}
            social_profiles[platform] = {
                "handle": handle,
                "linked_at": event.created_at.isoformat(),
                "confidence_score": data.get("confidence_score", 1.0),
                "verification_method": data.get("verification_method", "manual")
            }

            customer_summary.metadata = {
                **(customer_summary.metadata or {}),
                "social_profiles": social_profiles
            }

        # Update social inbox entries for this customer
        await session.execute(
            text("""
                UPDATE integra.social_inbox
                SET metadata = jsonb_set(
                    COALESCE(metadata, '{}'),
                    '{customer_linked}',
                    'true'
                )
                FROM social.social_threads st
                JOIN social.social_identities si ON st.customer_identity_id = si.id
                WHERE social_inbox.thread_id = st.id
                AND si.customer_id = :customer_id
            """),
            {"customer_id": customer_id}
        )

    async def _handle_review_received(self, event: OutboxEntry, session: AsyncSession):
        """Handle review received event."""
        data = event.event_data
        review_id = data.get("review_id")
        platform = data.get("platform")
        rating = data.get("rating")

        # Update social inbox with review alert
        await self._upsert_social_inbox_entry(
            session=session,
            thread_id=None,  # Reviews might not have threads
            platform=platform,
            last_activity="review_received",
            metadata={
                "review_id": review_id,
                "rating": rating,
                "requires_response": rating <= 3,  # Low ratings need attention
                "received_at": event.created_at.isoformat()
            }
        )

        # Update customer review history if linked
        if data.get("customer_id"):
            await self._update_customer_review_history(
                session=session,
                customer_id=data["customer_id"],
                platform=platform,
                rating=rating,
                review_id=review_id
            )

    async def _handle_review_acknowledged(self, event: OutboxEntry, session: AsyncSession):
        """Handle review acknowledgment event."""
        data = event.event_data
        review_id = data.get("review_id")

        # Update social inbox to mark as handled
        await session.execute(
            text("""
                UPDATE integra.social_inbox
                SET metadata = jsonb_set(
                    COALESCE(metadata, '{}'),
                    '{acknowledged}',
                    'true'
                )
                WHERE metadata->>'review_id' = :review_id
            """),
            {"review_id": str(review_id)}
        )

    async def _handle_thread_status_updated(self, event: OutboxEntry, session: AsyncSession):
        """Handle thread status update event."""
        data = event.event_data
        thread_id = data.get("thread_id")
        new_status = data.get("new_status")

        # Update social inbox entry
        await session.execute(
            text("""
                UPDATE integra.social_inbox
                SET metadata = jsonb_set(
                    COALESCE(metadata, '{}'),
                    '{thread_status}',
                    :status
                ),
                last_updated = :timestamp
                WHERE thread_id = :thread_id
            """),
            {
                "thread_id": thread_id,
                "status": json.dumps(new_status),
                "timestamp": event.created_at
            }
        )

        # If status is resolved/closed, mark as read
        if new_status in ["resolved", "closed"]:
            await session.execute(
                text("""
                    UPDATE social.social_threads
                    SET unread_count = 0
                    WHERE id = :thread_id
                """),
                {"thread_id": thread_id}
            )

    async def _handle_account_connected(self, event: OutboxEntry, session: AsyncSession):
        """Handle social account connection event."""
        data = event.event_data
        account_id = data.get("account_id")
        platform = data.get("platform")
        page_name = data.get("page_name")

        # Update social inbox with account info
        await self._upsert_social_inbox_entry(
            session=session,
            thread_id=None,
            platform=platform,
            last_activity="account_connected",
            metadata={
                "account_id": account_id,
                "page_name": page_name,
                "connected_at": event.created_at.isoformat()
            }
        )

    async def _upsert_social_inbox_entry(
        self,
        session: AsyncSession,
        thread_id: Optional[UUID],
        platform: Optional[str],
        last_activity: str,
        metadata: dict[str, Any]
    ):
        """Upsert social inbox entry."""
        if thread_id:
            # Update existing thread entry
            await session.execute(
                text("""
                    INSERT INTO integra.social_inbox (
                        thread_id, platform, last_activity, metadata, last_updated, created_at
                    )
                    VALUES (:thread_id, :platform, :activity, :metadata, :timestamp, :timestamp)
                    ON CONFLICT (thread_id) DO UPDATE SET
                        last_activity = EXCLUDED.last_activity,
                        metadata = integra.social_inbox.metadata || EXCLUDED.metadata,
                        last_updated = EXCLUDED.last_updated
                """),
                {
                    "thread_id": thread_id,
                    "platform": platform,
                    "activity": last_activity,
                    "metadata": json.dumps(metadata),
                    "timestamp": datetime.utcnow()
                }
            )
        else:
            # Create general platform entry
            entry_id = f"{platform}_{last_activity}_{datetime.utcnow().timestamp()}"
            await session.execute(
                text("""
                    INSERT INTO integra.social_inbox (
                        id, platform, last_activity, metadata, last_updated, created_at
                    )
                    VALUES (:id, :platform, :activity, :metadata, :timestamp, :timestamp)
                    ON CONFLICT (id) DO UPDATE SET
                        last_activity = EXCLUDED.last_activity,
                        metadata = integra.social_inbox.metadata || EXCLUDED.metadata,
                        last_updated = EXCLUDED.last_updated
                """),
                {
                    "id": entry_id,
                    "platform": platform,
                    "activity": last_activity,
                    "metadata": json.dumps(metadata),
                    "timestamp": datetime.utcnow()
                }
            )

    async def _update_customer_social_activity(
        self,
        session: AsyncSession,
        customer_id: UUID,
        platform: str,
        activity_type: str
    ):
        """Update customer summary with social activity."""
        await session.execute(
            text("""
                UPDATE read.customer_summary
                SET metadata = jsonb_set(
                    jsonb_set(
                        COALESCE(metadata, '{}'),
                        '{social_activity}',
                        COALESCE(metadata->'social_activity', '{}')
                    ),
                    array['social_activity', :platform, 'last_activity'],
                    :activity
                ),
                updated_at = :timestamp
                WHERE id = :customer_id
            """),
            {
                "customer_id": customer_id,
                "platform": platform,
                "activity": json.dumps({
                    "type": activity_type,
                    "timestamp": datetime.utcnow().isoformat()
                }),
                "timestamp": datetime.utcnow()
            }
        )

    async def _update_customer_review_history(
        self,
        session: AsyncSession,
        customer_id: UUID,
        platform: str,
        rating: int,
        review_id: UUID
    ):
        """Update customer review history."""
        await session.execute(
            text("""
                UPDATE read.customer_summary
                SET metadata = jsonb_set(
                    jsonb_set(
                        COALESCE(metadata, '{}'),
                        '{review_history}',
                        COALESCE(metadata->'review_history', '[]')
                    ),
                    array['review_history', '999'],
                    :review_data
                )
                WHERE id = :customer_id
            """),
            {
                "customer_id": customer_id,
                "review_data": json.dumps({
                    "review_id": str(review_id),
                    "platform": platform,
                    "rating": rating,
                    "created_at": datetime.utcnow().isoformat()
                })
            }
        )
