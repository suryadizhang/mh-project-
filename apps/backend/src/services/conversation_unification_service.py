"""
Conversation Unification Service

Links conversations across channels (SMS, WhatsApp, Instagram, Facebook)
to a single customer record using phone number as primary key.

Features:
- Auto-extracts phone numbers from messages
- Links social identities to customers
- Provides unified conversation timeline
- Confidence scoring for matches
"""

import re
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

# MIGRATED: Imports moved from OLD models to NEW db.models system
from db.models.core import (
    Customer,
    SocialIdentity,
    SocialThread,
    SocialMessage,
)
from db.models.lead import Lead

logger = logging.getLogger(__name__)


class ConversationUnificationService:
    """
    Unifies conversations across multiple channels by customer.

    Primary Key: Phone number (E.164 format)
    Secondary Keys: Email, social handles

    Conversation Sources:
    - SMS (RingCentral)
    - WhatsApp (Twilio)
    - Instagram DMs
    - Facebook Messenger
    - Voice calls (transcripts)
    """

    # Phone number patterns (US and international)
    PHONE_PATTERNS = [
        r"\+1[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}",  # +1 (XXX) XXX-XXXX
        r"\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}",  # (XXX) XXX-XXXX
        r"\d{3}[\s-]?\d{3}[\s-]?\d{4}",  # XXX-XXX-XXXX
        r"\+\d{1,3}[\s-]?\d{6,14}",  # International
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    # ========================================================================
    # PHONE NUMBER EXTRACTION & NORMALIZATION
    # ========================================================================

    def extract_phone_numbers(self, text: str) -> List[str]:
        """
        Extract phone numbers from message text.

        Returns normalized E.164 format phone numbers.
        """
        if not text:
            return []

        found_numbers = []
        for pattern in self.PHONE_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                raw_number = match.group(0)
                normalized = self.normalize_phone(raw_number)
                if normalized:
                    found_numbers.append(normalized)

        return list(set(found_numbers))  # Remove duplicates

    def normalize_phone(self, phone: str) -> Optional[str]:
        """
        Normalize phone number to E.164 format (+1XXXXXXXXXX).

        Examples:
        - "(916) 555-1234" → "+19165551234"
        - "916-555-1234" → "+19165551234"
        - "+1 916 555 1234" → "+19165551234"
        """
        # Remove all non-digit characters
        digits = re.sub(r"[^\d+]", "", phone)

        # If starts with +, keep it
        if digits.startswith("+"):
            return digits if len(digits) >= 11 else None

        # US number without country code
        if len(digits) == 10:
            return f"+1{digits}"

        # Already has country code
        if len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"

        # International number
        if len(digits) > 10:
            return f"+{digits}"

        logger.warning(f"Could not normalize phone: {phone}")
        return None

    # ========================================================================
    # CUSTOMER MATCHING & LINKING
    # ========================================================================

    async def find_customer_by_phone(self, phone: str) -> Optional[Customer]:
        """Find customer by phone number (exact match)."""
        normalized = self.normalize_phone(phone)
        if not normalized:
            return None

        stmt = select(Customer).where(Customer.phone == normalized)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_or_create_customer(
        self,
        phone: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        source: str = "social_media",
    ) -> tuple[Customer, bool]:
        """
        Find existing customer or create new one.

        Returns: (customer, created_new)
        """
        customer = await self.find_customer_by_phone(phone)

        if customer:
            # Update name/email if provided and not set
            updated = False
            if name and not customer.name:
                customer.name = name
                updated = True
            if email and not customer.email:
                customer.email = email
                updated = True

            if updated:
                await self.db.commit()
                logger.info(f"Updated customer {customer.id} with new info")

            return (customer, False)

        # Create new customer
        from uuid import uuid4

        customer = Customer(
            id=uuid4(),
            phone=self.normalize_phone(phone),
            name=name or "Unknown",
            email=email,
            source=source,
            created_at=datetime.utcnow(),
        )

        self.db.add(customer)
        await self.db.commit()
        await self.db.refresh(customer)

        logger.info(f"Created new customer {customer.id} from phone {phone}")
        return (customer, True)

    async def link_social_identity_to_customer(
        self, identity_id: UUID, customer_id: UUID, confidence: float = 1.0
    ) -> SocialIdentity:
        """
        Link a social identity to a customer.

        Args:
            identity_id: SocialIdentity UUID
            customer_id: Customer UUID
            confidence: Match confidence (0.0-1.0)
        """
        stmt = select(SocialIdentity).where(SocialIdentity.id == identity_id)
        result = await self.db.execute(stmt)
        identity = result.scalar_one_or_none()

        if not identity:
            raise ValueError(f"SocialIdentity {identity_id} not found")

        identity.customer_id = customer_id
        identity.confidence_score = confidence
        identity.verification_status = "verified" if confidence >= 0.9 else "pending"
        identity.last_active_at = datetime.utcnow()

        await self.db.commit()
        logger.info(
            f"Linked identity {identity.handle} on {identity.platform} "
            f"to customer {customer_id} (confidence: {confidence:.2f})"
        )

        return identity

    async def link_thread_to_customer(self, thread_id: UUID, customer_id: UUID) -> SocialThread:
        """Link a social thread to a customer."""
        stmt = select(SocialThread).where(SocialThread.id == thread_id)
        result = await self.db.execute(stmt)
        thread = result.scalar_one_or_none()

        if not thread:
            raise ValueError(f"SocialThread {thread_id} not found")

        thread.customer_id = customer_id
        await self.db.commit()

        logger.info(f"Linked thread {thread_id} to customer {customer_id}")
        return thread

    # ========================================================================
    # AUTO-LINKING FROM MESSAGES
    # ========================================================================

    async def auto_link_from_message(
        self, message: SocialMessage, thread: SocialThread
    ) -> Optional[Customer]:
        """
        Auto-link social thread to customer by extracting phone from message.

        Returns linked customer if successful.
        """
        # Extract phone numbers from message content
        phone_numbers = self.extract_phone_numbers(message.content)

        if not phone_numbers:
            logger.debug(f"No phone numbers found in message {message.id}")
            return None

        # Try each phone number until we find/create a customer
        for phone in phone_numbers:
            try:
                customer, created = await self.find_or_create_customer(
                    phone=phone,
                    name=message.author_name or message.author_handle,
                    source="social_media",
                )

                # Link thread to customer
                if thread.customer_id != customer.id:
                    thread.customer_id = customer.id

                # Link social identity to customer if available
                if thread.social_identity_id:
                    await self.link_social_identity_to_customer(
                        identity_id=thread.social_identity_id,
                        customer_id=customer.id,
                        confidence=0.95,  # High confidence since they provided phone
                    )

                await self.db.commit()

                logger.info(
                    f"Auto-linked thread {thread.id} to "
                    f"{'new' if created else 'existing'} customer {customer.id} "
                    f"via phone {phone}"
                )

                return customer

            except Exception as e:
                logger.error(f"Failed to link phone {phone}: {e}")
                continue

        return None

    # ========================================================================
    # UNIFIED CONVERSATION VIEW
    # ========================================================================

    async def get_unified_conversations(
        self, customer_id: UUID, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get ALL conversations for a customer across ALL channels.

        Returns unified timeline with:
        - Social media messages (Instagram, Facebook)
        - SMS messages (RingCentral)
        - WhatsApp messages (Twilio)
        - Voice call transcripts
        - Lead interactions

        Sorted by timestamp (most recent first).
        """
        conversations = []

        # 1. Get social media conversations
        social_stmt = (
            select(SocialThread, SocialMessage)
            .join(SocialMessage, SocialThread.id == SocialMessage.thread_id)
            .where(SocialThread.customer_id == customer_id)
            .order_by(desc(SocialMessage.sent_at))
            .limit(limit)
        )

        result = await self.db.execute(social_stmt)
        for thread, message in result:
            conversations.append(
                {
                    "type": "social_media",
                    "platform": thread.platform.value,
                    "timestamp": message.sent_at,
                    "direction": (
                        message.direction.value
                        if hasattr(message, "direction")
                        else ("in" if message.is_from_customer else "out")
                    ),
                    "content": message.content,
                    "sender": message.author_name or message.sender_handle,
                    "thread_id": str(thread.id),
                    "message_id": str(message.id),
                    "metadata": {
                        "sentiment": (
                            message.sentiment_score if hasattr(message, "sentiment_score") else None
                        ),
                        "intent_tags": (
                            message.intent_tags if hasattr(message, "intent_tags") else None
                        ),
                    },
                }
            )

        # 2. TODO: Get SMS conversations from message_threads table
        # 3. TODO: Get WhatsApp conversations
        # 4. TODO: Get voice call transcripts
        # 5. TODO: Get lead interaction timeline

        # Sort all conversations by timestamp
        conversations.sort(key=lambda x: x["timestamp"], reverse=True)

        return conversations[:limit]

    async def get_customer_timeline(self, customer_id: UUID) -> Dict[str, Any]:
        """
        Get complete customer interaction timeline.

        Returns:
        - All conversations (unified)
        - Lead history
        - Booking history
        - Review history
        """
        # Get customer
        customer_stmt = select(Customer).where(Customer.id == customer_id)
        result = await self.db.execute(customer_stmt)
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # Get unified conversations
        conversations = await self.get_unified_conversations(customer_id)

        # Get social identities
        identities_stmt = select(SocialIdentity).where(SocialIdentity.customer_id == customer_id)
        result = await self.db.execute(identities_stmt)
        identities = result.scalars().all()

        # Get leads
        leads_stmt = select(Lead).where(
            or_(Lead.phone == customer.phone, Lead.email == customer.email)
        )
        result = await self.db.execute(leads_stmt)
        leads = result.scalars().all()

        return {
            "customer": {
                "id": str(customer.id),
                "phone": customer.phone,
                "email": customer.email,
                "name": customer.name,
                "created_at": customer.created_at.isoformat(),
            },
            "social_identities": [
                {
                    "platform": identity.platform.value,
                    "handle": f"@{identity.handle}",
                    "confidence": identity.confidence_score,
                    "verified": identity.verification_status == "verified",
                }
                for identity in identities
            ],
            "conversations": conversations,
            "total_conversations": len(conversations),
            "leads": [
                {
                    "id": str(lead.id),
                    "status": lead.status.value if hasattr(lead, "status") else None,
                    "source": lead.source.value if hasattr(lead, "source") else None,
                    "created_at": lead.created_at.isoformat(),
                }
                for lead in leads
            ],
            "stats": {
                "total_messages": len(conversations),
                "platforms_used": len(set(c["platform"] for c in conversations)),
                "linked_identities": len(identities),
                "leads_created": len(leads),
            },
        }

    # ========================================================================
    # BATCH PROCESSING
    # ========================================================================

    async def process_unlinked_threads(self, limit: int = 50) -> int:
        """
        Process threads that have no customer_id and try to auto-link them.

        Returns number of threads linked.
        """
        # Find threads with messages but no customer link
        stmt = select(SocialThread).where(SocialThread.customer_id.is_(None)).limit(limit)

        result = await self.db.execute(stmt)
        unlinked_threads = result.scalars().all()

        linked_count = 0
        for thread in unlinked_threads:
            # Get first few messages from thread
            messages_stmt = (
                select(SocialMessage)
                .where(SocialMessage.thread_id == thread.id)
                .order_by(SocialMessage.sent_at)
                .limit(10)
            )

            messages_result = await self.db.execute(messages_stmt)
            messages = messages_result.scalars().all()

            # Try to extract phone from any message
            for message in messages:
                customer = await self.auto_link_from_message(message, thread)
                if customer:
                    linked_count += 1
                    break

        logger.info(f"Linked {linked_count}/{len(unlinked_threads)} threads to customers")
        return linked_count


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================


async def get_unified_customer_view(db: AsyncSession, customer_id: UUID) -> Dict[str, Any]:
    """
    Convenience function to get unified customer view.

    Usage:
        from services.conversation_unification_service import get_unified_customer_view

        timeline = await get_unified_customer_view(db, customer_id)
        print(timeline["total_conversations"])
    """
    service = ConversationUnificationService(db)
    return await service.get_customer_timeline(customer_id)


async def auto_link_customer_from_phone(
    db: AsyncSession, phone: str, name: Optional[str] = None, email: Optional[str] = None
) -> Customer:
    """
    Find or create customer from phone number.

    Usage:
        customer = await auto_link_customer_from_phone(
            db,
            phone="(916) 555-1234",
            name="John Doe"
        )
    """
    service = ConversationUnificationService(db)
    customer, _ = await service.find_or_create_customer(phone, name, email)
    return customer
