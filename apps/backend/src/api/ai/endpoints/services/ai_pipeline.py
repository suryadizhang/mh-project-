"""
AI Pipeline service that orchestrates the complete conversation flow
Handles intent classification, knowledge retrieval, GPT fallback, and escalation
"""

import re
import time
from typing import Any
from uuid import UUID

from api.ai.endpoints.models import Message, MessageRole
from api.ai.endpoints.schemas import ChatReplyResponse
from api.ai.endpoints.services.knowledge_base_simple import kb_service
from api.ai.endpoints.services.openai_service import openai_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class AIPipeline:
    """Main AI pipeline for processing customer messages"""

    def __init__(self):
        self.confidence_thresholds = {
            "high": 0.80,  # Use our KB directly
            "medium": 0.50,  # Use GPT with KB context
            "low": 0.30,  # Use GPT-4 or escalate
        }

        # Intent classification keywords
        self.intent_keywords = {
            "booking": [
                "book",
                "reserve",
                "schedule",
                "appointment",
                "date",
                "availability",
            ],
            "pricing": [
                "price",
                "cost",
                "how much",
                "fee",
                "deposit",
                "charge",
                "payment",
                "pay",
            ],
            "menu": [
                "food",
                "protein",
                "chicken",
                "beef",
                "shrimp",
                "salmon",
                "vegetarian",
            ],
            "service_area": [
                "serve",
                "area",
                "location",
                "travel",
                "distance",
                "sacramento",
                "bay area",
            ],
            "policy": [
                "cancel",
                "refund",
                "policy",
                "terms",
                "conditions",
                "agreement",
            ],
            "service_details": [
                "include",
                "provide",
                "cleanup",
                "tables",
                "chairs",
                "equipment",
            ],
            "complaint": [
                "bad",
                "terrible",
                "awful",
                "disappointed",
                "wrong",
                "problem",
            ],
        }

    def classify_intent(self, message: str) -> tuple[str, float]:
        """Classify the intent of a user message"""
        message_lower = message.lower()
        intent_scores = {}

        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                intent_scores[intent] = score / len(keywords)

        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = min(intent_scores[best_intent] * 2, 1.0)  # Scale up confidence
            return best_intent, confidence

        return "general", 0.3

    def extract_entities(self, message: str) -> dict[str, Any]:
        """Extract entities like dates, locations, numbers from message"""
        entities = {}

        # Extract potential dates
        date_patterns = [
            r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # MM/DD/YYYY
            r"\b\d{1,2}-\d{1,2}-\d{2,4}\b",  # MM-DD-YYYY
            r"\b(today|tomorrow|next week|this weekend)\b",
        ]

        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, message, re.IGNORECASE))
        if dates:
            entities["dates"] = dates

        # Extract locations
        ca_cities = [
            "sacramento",
            "san francisco",
            "san jose",
            "oakland",
            "palo alto",
            "mountain view",
            "santa clara",
            "sunnyvale",
            "fremont",
            "roseville",
            "folsom",
            "davis",
            "berkeley",
            "hayward",
            "milpitas",
        ]

        locations = [city for city in ca_cities if city in message.lower()]
        if locations:
            entities["locations"] = locations

        # Extract numbers (for guest count, etc.)
        numbers = re.findall(r"\b\d+\b", message)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers if int(n) < 1000]

        return entities

    async def process_message(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        message: str,
        user_role: str = MessageRole.USER.value,
    ) -> ChatReplyResponse:
        """Process a single message through the AI pipeline"""
        start_time = time.time()

        try:
            # Step 1: Classify intent
            intent, intent_confidence = self.classify_intent(message)

            # Step 2: Search knowledge base
            from api.ai.endpoints.schemas import KBSearchRequest

            kb_request = KBSearchRequest(query=message, limit=3, min_score=0.3)
            kb_results, _ = await kb_service.search_chunks(db, kb_request)

            # Step 3: Determine response strategy
            kb_confidence = max([chunk["score"] for chunk in kb_results], default=0.0)
            combined_confidence = (intent_confidence + kb_confidence) / 2

            # Step 4: Generate response based on confidence
            if combined_confidence >= self.confidence_thresholds["high"] and kb_results:
                # High confidence: Use KB directly
                response_text = self._format_kb_response(kb_results[0], message)
                source = "our-ai"
                confidence = combined_confidence
                tokens_in, tokens_out, cost_usd = 0, 0, 0.0

            elif combined_confidence >= self.confidence_thresholds["medium"]:
                # Medium confidence: Use GPT with KB context
                context = self._build_kb_context(kb_results)
                (
                    response_text,
                    confidence,
                    model_used,
                    tokens_in,
                    tokens_out,
                    cost_usd,
                ) = await openai_service.generate_response(message, context)
                source = f"gpt-{model_used.split('-')[-1]}"

            else:
                # Low confidence: Use GPT-4 or escalate
                (
                    should_escalate,
                    escalation_reason,
                ) = openai_service.should_escalate(message)
                if should_escalate:
                    response_text = "I understand this is important to you. Let me connect you with one of our team members who can provide personalized assistance."
                    source = "escalation"
                    confidence = 0.95
                    tokens_in, tokens_out, cost_usd = 0, 0, 0.0
                else:
                    context = self._build_kb_context(kb_results)
                    (
                        response_text,
                        confidence,
                        model_used,
                        tokens_in,
                        tokens_out,
                        cost_usd,
                    ) = await openai_service.generate_response(
                        message, context, force_model="gpt-4-1-mini"
                    )
                    source = "gpt-4-mini"

            # Step 5: Save message to database
            user_message = Message(
                conversation_id=conversation_id,
                role=user_role,
                text=message,
                intent_classification=intent,
                confidence=intent_confidence,
                kb_sources_used=[chunk["id"] for chunk in kb_results[:2]],
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

            ai_message = Message(
                conversation_id=conversation_id,
                role=(MessageRole.AI.value if "gpt" not in source else MessageRole.GPT.value),
                text=response_text,
                confidence=confidence,
                model_used=source,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=cost_usd,
                intent_classification=intent,
                kb_sources_used=[chunk["id"] for chunk in kb_results[:2]],
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

            db.add(user_message)
            db.add(ai_message)
            await db.commit()

            # Step 6: Return response
            return ChatReplyResponse(
                reply=response_text,
                confidence=confidence,
                source=source,
                kb_sources=kb_results[:2],
                tokens_used=tokens_in + tokens_out,
                cost_usd=cost_usd,
            )

        except Exception:
            return ChatReplyResponse(
                reply="I'm experiencing technical difficulties. Please contact our team directly for immediate assistance.",
                confidence=0.1,
                source="error",
                kb_sources=[],
                tokens_used=0,
                cost_usd=0.0,
            )

    def _format_kb_response(self, kb_chunk: dict[str, Any], original_message: str) -> str:
        """Format a knowledge base response to feel natural"""
        # Simple formatting for now - can be enhanced with templates
        base_response = kb_chunk["text"]

        # Add natural introduction if the response is very direct
        if not base_response.startswith(("Hi", "Hello", "Thanks", "Great")):
            if "price" in original_message.lower() or "cost" in original_message.lower():
                base_response = f"Great question! {base_response}"
            elif "?" in original_message:
                base_response = f"Here's what I can tell you: {base_response}"

        # Add helpful closing for booking-related queries
        if any(word in original_message.lower() for word in ["book", "reserve", "schedule"]):
            base_response += "\n\nWould you like me to help you start the booking process?"

        return base_response

    def _build_kb_context(self, kb_results: list[dict[str, Any]]) -> str:
        """Build context string from knowledge base results"""
        if not kb_results:
            return ""

        context_parts = []
        for i, chunk in enumerate(kb_results[:3]):
            context_parts.append(f"{i+1}. {chunk['title']}: {chunk['text'][:200]}...")

        return "Relevant information from our knowledge base:\n" + "\n".join(context_parts)

    async def get_conversation_history(
        self, db: AsyncSession, conversation_id: UUID, limit: int = 10
    ) -> list[dict[str, str]]:
        """Get recent conversation history for context"""
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )

        result = await db.execute(query)
        messages = result.scalars().all()

        history = []
        for msg in reversed(messages):  # Reverse to get chronological order
            role = "user" if msg.role == MessageRole.USER.value else "assistant"
            history.append({"role": role, "content": msg.text})

        return history

    async def should_escalate_conversation(
        self, db: AsyncSession, conversation_id: UUID
    ) -> tuple[bool, str]:
        """Determine if conversation should be escalated based on history"""
        # Get recent messages
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(5)
        )

        result = await db.execute(query)
        messages = result.scalars().all()

        # Check for escalation indicators
        low_confidence_count = sum(1 for msg in messages if msg.confidence and msg.confidence < 0.4)
        user_messages = [msg for msg in messages if msg.role == MessageRole.USER.value]

        # Too many low confidence responses
        if low_confidence_count >= 3:
            return True, "Multiple low-confidence responses"

        # User repeating similar questions
        if len(user_messages) >= 3:
            recent_texts = [msg.text.lower() for msg in user_messages[:3]]
            if any(
                text in other for text in recent_texts for other in recent_texts if text != other
            ):
                return (
                    True,
                    "User repeating questions - possible dissatisfaction",
                )

        # Check for escalation keywords in recent messages
        for msg in user_messages[:2]:
            should_escalate, reason = openai_service.should_escalate(msg.text)
            if should_escalate:
                return True, reason

        return False, ""


# Global instance
ai_pipeline = AIPipeline()
