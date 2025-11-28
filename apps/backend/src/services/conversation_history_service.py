"""
Conversation History Service - Retrieves customer conversation context for AI.

This service provides:
1. Customer conversation history (all calls with transcripts)
2. Booking-related conversations (calls linked to specific bookings)
3. AI-formatted context strings for prompts
4. Search across transcripts

Used by: AI agents, customer service dashboards, conversation API
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.core import Booking, BookingStatus, Customer

# MIGRATED: from models.call_recording → db.models.call_recording
from db.models.call_recording import CallRecording

logger = logging.getLogger(__name__)


class ConversationHistoryService:
    """Service for retrieving and formatting conversation history"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_customer_history(
        self,
        customer_id: UUID,
        limit: int = 20,
        offset: int = 0,
        include_no_transcript: bool = False,
    ) -> dict:
        """
        Get conversation history for a customer.

        Returns all call recordings with transcripts, sorted by most recent.
        Includes AI insights, sentiment, and topics.

        Args:
            customer_id: Customer UUID
            limit: Maximum number of conversations to return (default 20)
            offset: Pagination offset (default 0)
            include_no_transcript: Include calls without transcripts (default False)

        Returns:
            dict with customer info and conversations list
        """
        try:
            # Get customer
            stmt = select(Customer).where(Customer.id == customer_id)
            result = await self.db.execute(stmt)
            customer = result.scalar_one_or_none()

            if not customer:
                logger.warning(f"Customer {customer_id} not found")
                return {
                    "customer_id": customer_id,
                    "error": "Customer not found",
                    "conversations": [],
                }

            # Build query for recordings
            query_filters = [CallRecording.customer_id == customer_id]

            if not include_no_transcript:
                # Only include recordings with transcripts
                query_filters.append(CallRecording.rc_transcript.isnot(None))
                query_filters.append(CallRecording.rc_transcript != "")

            # Count total conversations
            count_stmt = select(func.count()).select_from(CallRecording).where(and_(*query_filters))
            count_result = await self.db.execute(count_stmt)
            total_count = count_result.scalar()

            # Get recordings
            stmt = (
                select(CallRecording)
                .where(and_(*query_filters))
                .order_by(desc(CallRecording.call_started_at))
                .limit(limit)
                .offset(offset)
            )

            result = await self.db.execute(stmt)
            recordings = result.scalars().all()

            # Format conversations
            conversations = []
            for recording in recordings:
                conversation = await self._format_conversation(recording)
                conversations.append(conversation)

            logger.info(
                f"Retrieved {len(conversations)} conversations for customer {customer_id} "
                f"(total: {total_count})"
            )

            return {
                "customer_id": customer_id,
                "customer_name": f"{customer.first_name} {customer.last_name}".strip(),
                "customer_phone": customer.phone,
                "customer_email": customer.email,
                "total_conversations": total_count,
                "conversations": conversations,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + len(conversations)) < total_count,
                },
            }

        except Exception as e:
            logger.error(
                f"Error getting customer history for {customer_id}: {e}",
                exc_info=True,
            )
            return {
                "customer_id": customer_id,
                "error": str(e),
                "conversations": [],
            }

    async def _format_conversation(self, recording: CallRecording) -> dict:
        """Format a CallRecording into conversation dict"""
        # Extract AI insights
        insights = recording.rc_ai_insights or {}
        sentiment = insights.get("sentiment", "unknown")
        topics = insights.get("topics", [])
        intent = insights.get("intent", "unknown")

        # Create transcript excerpt (first 200 chars)
        transcript_excerpt = ""
        if recording.rc_transcript:
            transcript_excerpt = recording.rc_transcript[:200]
            if len(recording.rc_transcript) > 200:
                transcript_excerpt += "..."

        # Determine call direction
        call_direction = "unknown"
        if recording.from_phone and recording.to_phone:
            # If from_phone is customer's phone, it's inbound
            # This is a simplification - in real code we'd check against business phone
            call_direction = "inbound" if recording.customer_id else "outbound"

        return {
            "id": str(recording.id),
            "call_started_at": (
                recording.call_started_at.isoformat() if recording.call_started_at else None
            ),
            "duration_seconds": recording.duration_seconds,
            "call_direction": call_direction,
            "from_phone": recording.from_phone,
            "to_phone": recording.to_phone,
            "booking_id": str(recording.booking_id) if recording.booking_id else None,
            "transcript_excerpt": transcript_excerpt,
            "transcript_full_length": (
                len(recording.rc_transcript) if recording.rc_transcript else 0
            ),
            "transcript_confidence": recording.rc_transcript_confidence,
            "ai_insights": {
                "sentiment": sentiment,
                "topics": topics,
                "intent": intent,
                "action_items": insights.get("action_items", []),
            },
            "has_recording": bool(recording.s3_uri),
        }

    async def get_booking_context(self, booking_id: UUID) -> dict:
        """
        Get all conversations related to a booking.

        Groups conversations into timeline:
        - Pre-booking (before booking date)
        - Day-of (same day as booking)
        - Post-booking (after booking date)

        Args:
            booking_id: Booking UUID

        Returns:
            dict with booking info and grouped conversations
        """
        try:
            # Get booking
            stmt = select(Booking).where(Booking.id == booking_id)
            result = await self.db.execute(stmt)
            booking = result.scalar_one_or_none()

            if not booking:
                logger.warning(f"Booking {booking_id} not found")
                return {
                    "booking_id": booking_id,
                    "error": "Booking not found",
                    "conversations": [],
                }

            # Get all recordings linked to this booking
            stmt = (
                select(CallRecording)
                .where(CallRecording.booking_id == booking_id)
                .order_by(CallRecording.call_started_at)
            )

            result = await self.db.execute(stmt)
            recordings = result.scalars().all()

            # Group by timeline
            pre_booking = []
            day_of = []
            post_booking = []

            booking_date = booking.booking_datetime.date()

            for recording in recordings:
                conversation = await self._format_conversation(recording)
                call_date = recording.call_started_at.date() if recording.call_started_at else None

                if call_date:
                    if call_date < booking_date:
                        pre_booking.append(conversation)
                    elif call_date == booking_date:
                        day_of.append(conversation)
                    else:
                        post_booking.append(conversation)

            # Extract key insights from all conversations
            all_insights = [r.rc_ai_insights for r in recordings if r.rc_ai_insights]
            key_topics = self._extract_common_topics(all_insights)
            sentiment_summary = self._summarize_sentiment(all_insights)

            logger.info(f"Retrieved {len(recordings)} conversations for booking {booking_id}")

            return {
                "booking_id": str(booking_id),
                "booking_datetime": booking.booking_datetime.isoformat(),
                "booking_status": booking.status.value,
                "party_size": booking.party_size,
                "customer_id": str(booking.customer_id) if booking.customer_id else None,
                "total_conversations": len(recordings),
                "conversations": {
                    "pre_booking": pre_booking,
                    "day_of": day_of,
                    "post_booking": post_booking,
                },
                "key_insights": {
                    "common_topics": key_topics,
                    "sentiment_summary": sentiment_summary,
                },
            }

        except Exception as e:
            logger.error(f"Error getting booking context for {booking_id}: {e}", exc_info=True)
            return {
                "booking_id": booking_id,
                "error": str(e),
                "conversations": {},
            }

    def _extract_common_topics(self, insights_list: list[dict]) -> list[str]:
        """Extract most common topics from AI insights"""
        topic_counts = {}
        for insights in insights_list:
            topics = insights.get("topics", [])
            for topic in topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        # Sort by frequency, return top 5
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [topic for topic, count in sorted_topics[:5]]

    def _summarize_sentiment(self, insights_list: list[dict]) -> dict:
        """Summarize sentiment across conversations"""
        sentiments = {"positive": 0, "neutral": 0, "negative": 0, "unknown": 0}
        for insights in insights_list:
            sentiment = insights.get("sentiment", "unknown")
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

        total = len(insights_list)
        if total == 0:
            return sentiments

        # Calculate percentages
        return {
            sentiment: {
                "count": count,
                "percentage": round((count / total) * 100, 1),
            }
            for sentiment, count in sentiments.items()
        }

    async def get_ai_context_for_customer(
        self, customer_id: UUID, max_conversations: int = 5
    ) -> str:
        """
        Format recent conversation history as context string for AI prompts.

        Creates a concise summary of recent interactions that AI agents can
        use to provide personalized, context-aware service.

        Args:
            customer_id: Customer UUID
            max_conversations: Maximum conversations to include (default 5)

        Returns:
            Formatted context string for AI prompt

        Example output:
            Customer: John Smith (555-0123)
            Recent interactions (last 5 calls):
            - 2024-11-15 10:27: Asked about vegetarian options for Nov 15 event. Positive.
            - 2024-11-10 14:20: Booking confirmation. Asked about parking. Positive.
            - 2024-11-08 09:15: Initial inquiry about catering prices. Neutral.

            Key preferences: Vegetarian options, parking concerns
            Active booking: 2024-11-15, 30 guests, confirmed
        """
        try:
            # Get recent conversations
            history = await self.get_customer_history(
                customer_id, limit=max_conversations, include_no_transcript=False
            )

            if history.get("error") or not history.get("conversations"):
                return f"No conversation history available for customer {customer_id}"

            # Build context string
            lines = []
            lines.append(f"Customer: {history['customer_name']} ({history['customer_phone']})")
            lines.append(f"Recent interactions (last {len(history['conversations'])} calls):")

            for conv in history["conversations"]:
                # Format: Date Time: Brief summary. Sentiment.
                date_str = ""
                if conv["call_started_at"]:
                    dt = datetime.fromisoformat(conv["call_started_at"])
                    date_str = dt.strftime("%Y-%m-%d %H:%M")

                # Extract brief summary from transcript or AI insights
                summary = self._create_brief_summary(conv)

                sentiment = conv["ai_insights"]["sentiment"].capitalize()

                lines.append(f"- {date_str}: {summary} {sentiment} sentiment.")

            # Add key topics across all conversations
            all_topics = []
            for conv in history["conversations"]:
                all_topics.extend(conv["ai_insights"]["topics"])

            if all_topics:
                # Get unique topics
                unique_topics = list(set(all_topics))[:5]
                lines.append(f"\nKey topics discussed: {', '.join(unique_topics)}")

            # Check for active booking
            active_booking = await self._get_active_booking_for_customer(customer_id)
            if active_booking:
                lines.append(
                    f"Active booking: {active_booking['date']}, "
                    f"{active_booking['party_size']} guests, "
                    f"{active_booking['status']}"
                )

            context = "\n".join(lines)
            logger.debug(f"Generated AI context for customer {customer_id}")
            return context

        except Exception as e:
            logger.error(
                f"Error generating AI context for customer {customer_id}: {e}",
                exc_info=True,
            )
            return f"Error retrieving conversation history: {str(e)}"

    def _create_brief_summary(self, conversation: dict) -> str:
        """Create a brief summary from conversation data"""
        # Try to use intent first
        intent = conversation["ai_insights"]["intent"]
        if intent and intent != "unknown":
            return intent.replace("_", " ").capitalize()

        # Fall back to topics
        topics = conversation["ai_insights"]["topics"]
        if topics:
            return f"Discussed {', '.join(topics[:2])}"

        # Last resort: use transcript excerpt
        excerpt = conversation["transcript_excerpt"]
        if excerpt:
            # Take first sentence
            first_sentence = excerpt.split(".")[0]
            if len(first_sentence) > 60:
                return first_sentence[:60] + "..."
            return first_sentence

        return "Call recorded"

    async def _get_active_booking_for_customer(self, customer_id: UUID) -> Optional[dict]:
        """Get active booking for a customer (if any)"""
        try:
            # Find next upcoming booking or recent booking
            stmt = (
                select(Booking)
                .where(
                    and_(
                        Booking.customer_id == customer_id,
                        Booking.status.in_(
                            [
                                BookingStatus.PENDING,
                                BookingStatus.CONFIRMED,
                                BookingStatus.SEATED,
                            ]
                        ),
                        Booking.booking_datetime >= datetime.now(timezone.utc) - timedelta(hours=4),
                    )
                )
                .order_by(Booking.booking_datetime)
                .limit(1)
            )

            result = await self.db.execute(stmt)
            booking = result.scalar_one_or_none()

            if booking:
                return {
                    "date": booking.booking_datetime.strftime("%Y-%m-%d %H:%M"),
                    "party_size": booking.party_size,
                    "status": booking.status.value,
                }

            return None

        except Exception as e:
            logger.error(f"Error getting active booking: {e}")
            return None

    async def search_transcripts(
        self,
        query: str,
        customer_id: Optional[UUID] = None,
        booking_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sentiment: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """
        Search across all call transcripts.

        Supports full-text search on transcript content with filters.

        Args:
            query: Search query (searched in transcript text)
            customer_id: Filter by customer (optional)
            booking_id: Filter by booking (optional)
            date_from: Filter by start date (optional)
            date_to: Filter by end date (optional)
            sentiment: Filter by sentiment: positive, neutral, negative (optional)
            limit: Maximum results (default 50)
            offset: Pagination offset (default 0)

        Returns:
            dict with search results and metadata
        """
        try:
            # Build query filters
            filters = [
                CallRecording.rc_transcript.isnot(None),
                CallRecording.rc_transcript != "",
            ]

            # Full-text search on transcript
            if query:
                # Use PostgreSQL full-text search or LIKE for simplicity
                filters.append(CallRecording.rc_transcript.ilike(f"%{query}%"))

            if customer_id:
                filters.append(CallRecording.customer_id == customer_id)

            if booking_id:
                filters.append(CallRecording.booking_id == booking_id)

            if date_from:
                filters.append(CallRecording.call_started_at >= date_from)

            if date_to:
                filters.append(CallRecording.call_started_at <= date_to)

            if sentiment:
                # Note: This requires JSONB query
                filters.append(CallRecording.rc_ai_insights["sentiment"].astext == sentiment)

            # Count total results
            count_stmt = select(func.count()).select_from(CallRecording).where(and_(*filters))
            count_result = await self.db.execute(count_stmt)
            total_count = count_result.scalar()

            # Get results
            stmt = (
                select(CallRecording)
                .where(and_(*filters))
                .order_by(desc(CallRecording.call_started_at))
                .limit(limit)
                .offset(offset)
            )

            result = await self.db.execute(stmt)
            recordings = result.scalars().all()

            # Format results
            results = []
            for recording in recordings:
                conversation = await self._format_conversation(recording)

                # Add search context (surrounding text)
                if query and recording.rc_transcript:
                    context = self._extract_search_context(recording.rc_transcript, query)
                    conversation["search_context"] = context

                results.append(conversation)

            logger.info(
                f"Transcript search '{query}' returned {len(results)} results "
                f"(total: {total_count})"
            )

            return {
                "query": query,
                "total_results": total_count,
                "results": results,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + len(results)) < total_count,
                },
            }

        except Exception as e:
            logger.error(f"Error searching transcripts: {e}", exc_info=True)
            return {
                "query": query,
                "error": str(e),
                "results": [],
            }

    def _extract_search_context(self, transcript: str, query: str, context_chars: int = 100) -> str:
        """Extract text around search query match"""
        query_lower = query.lower()
        transcript_lower = transcript.lower()

        index = transcript_lower.find(query_lower)
        if index == -1:
            return transcript[:context_chars] + "..."

        # Get surrounding context
        start = max(0, index - context_chars)
        end = min(len(transcript), index + len(query) + context_chars)

        context = transcript[start:end]
        if start > 0:
            context = "..." + context
        if end < len(transcript):
            context = context + "..."

        return context
