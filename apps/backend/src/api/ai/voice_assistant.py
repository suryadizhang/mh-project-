"""
Voice AI Assistant
Real-time conversational AI for phone calls.
Integrates speech recognition, AI orchestrator, and speech synthesis.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
import json
import logging
from typing import Any, AsyncGenerator, Optional
from uuid import uuid4

from services.speech_service import speech_service
from api.ai.orchestrator.ai_orchestrator import AIOrchestrator
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Voice conversation states"""

    GREETING = "greeting"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    CLARIFYING = "clarifying"
    BOOKING = "booking"
    TRANSFERRING = "transferring"
    ENDING = "ending"


class VoiceAssistant:
    """
    Real-time voice AI assistant for phone conversations.

    Features:
    - Natural conversation flow
    - Context retention across turns
    - Emotion detection from voice
    - Interruption handling
    - Booking capture
    - Human escalation
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.speech_service = speech_service
        self.orchestrator = AIOrchestrator(db=db)

        # Conversation settings
        self.max_silence_seconds = 3  # Max silence before prompting
        self.max_clarification_attempts = 2
        self.confidence_threshold = 0.7  # Minimum confidence for action

    async def handle_conversation(
        self,
        call_id: str,
        caller_phone: str,
        audio_stream: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Handle complete voice conversation.

        Args:
            call_id: Unique call identifier
            caller_phone: Caller's phone number
            audio_stream: Incoming audio stream

        Yields:
            Dict with conversation events and responses
        """
        try:
            # Initialize conversation state
            conversation_state = {
                "call_id": call_id,
                "caller_phone": caller_phone,
                "state": ConversationState.GREETING,
                "started_at": datetime.now(timezone.utc),
                "messages": [],
                "context": {},
                "clarification_count": 0,
            }

            # Send initial greeting
            yield await self._generate_greeting(conversation_state)

            # Main conversation loop
            transcript_buffer = []
            silence_timer = 0

            async def on_transcript(transcript_data: dict[str, Any]):
                """Handle transcription results"""
                text = transcript_data["text"]
                is_final = transcript_data["is_final"]
                confidence = transcript_data["confidence"]

                logger.info(
                    f"Transcript: '{text}' (final={is_final}, confidence={confidence:.2f})"
                )

                if is_final:
                    # Process complete utterance
                    transcript_buffer.append(text)
                    silence_timer = 0

                    # Generate AI response
                    if len(transcript_buffer) >= 1:
                        full_text = " ".join(transcript_buffer)
                        transcript_buffer.clear()

                        # Update conversation
                        conversation_state["messages"].append(
                            {"role": "user", "content": full_text, "timestamp": datetime.now()}
                        )

                        # Generate response
                        response = await self._generate_response(conversation_state, full_text)

                        yield response

            # Start transcription
            await self.speech_service.transcribe_audio_stream(
                audio_stream=audio_stream, callback=on_transcript, language="en"
            )

            # End conversation
            yield await self._end_conversation(conversation_state)

        except Exception as e:
            logger.exception(f"Voice conversation error: {e}")
            yield {
                "event": "error",
                "error": str(e),
                "action": "transfer_human",
            }

    async def _generate_greeting(self, state: dict[str, Any]) -> dict[str, Any]:
        """Generate personalized greeting"""
        # Check if returning customer
        caller_phone = state["caller_phone"]
        customer_history = await self._get_customer_history(caller_phone)

        if customer_history:
            name = customer_history.get("name", "")
            greeting = (
                f"Hi {name}! Welcome back to MyHibachi. "
                f"How can I help you today?"
            )
        else:
            greeting = (
                "Hi! Thank you for calling MyHibachi. "
                "I'm your AI assistant. How can I help you today?"
            )

        # Convert to speech
        audio = await self.speech_service.synthesize_speech(greeting, streaming=False)

        state["state"] = ConversationState.LISTENING

        return {
            "event": "greeting",
            "text": greeting,
            "audio": audio,
            "state": state["state"],
        }

    async def _generate_response(
        self, state: dict[str, Any], user_message: str
    ) -> dict[str, Any]:
        """
        Generate AI response to user message.

        Args:
            state: Conversation state
            user_message: User's transcribed message

        Returns:
            Response dict with text, audio, and next action
        """
        try:
            state["state"] = ConversationState.THINKING

            # Build context for orchestrator
            context = {
                "channel": "phone",
                "caller_phone": state["caller_phone"],
                "conversation_history": state["messages"],
                "call_id": state["call_id"],
            }

            # Get AI response
            ai_response = await self.orchestrator.chat(
                message=user_message,
                session_id=state["call_id"],
                customer_id=None,  # TODO: Link to customer if known
                channel="phone",
                metadata=context,
            )

            response_text = ai_response.get("response", "")
            confidence = ai_response.get("confidence", 0.0)
            intent = ai_response.get("intent", "")

            # Check if booking info captured
            booking_info = ai_response.get("booking_info", {})
            if booking_info:
                state["context"]["booking_info"] = booking_info

            # Determine next action
            next_action = self._determine_next_action(
                state, response_text, confidence, intent, booking_info
            )

            # Convert to speech
            state["state"] = ConversationState.SPEAKING
            audio = await self.speech_service.synthesize_speech(response_text, streaming=False)

            # Update conversation
            state["messages"].append(
                {"role": "assistant", "content": response_text, "timestamp": datetime.now()}
            )

            # Transition state
            if next_action == "transfer":
                state["state"] = ConversationState.TRANSFERRING
            elif next_action == "end":
                state["state"] = ConversationState.ENDING
            else:
                state["state"] = ConversationState.LISTENING

            return {
                "event": "response",
                "text": response_text,
                "audio": audio,
                "state": state["state"],
                "action": next_action,
                "confidence": confidence,
                "intent": intent,
                "booking_info": booking_info,
            }

        except Exception as e:
            logger.exception(f"Error generating response: {e}")

            # Fallback response
            fallback_text = "I'm having trouble understanding. Let me transfer you to someone who can help."
            audio = await self.speech_service.synthesize_speech(fallback_text, streaming=False)

            return {
                "event": "error",
                "text": fallback_text,
                "audio": audio,
                "action": "transfer",
            }

    def _determine_next_action(
        self,
        state: dict[str, Any],
        response_text: str,
        confidence: float,
        intent: str,
        booking_info: dict[str, Any],
    ) -> str:
        """
        Determine next conversation action.

        Returns:
            Action: "continue", "transfer", "end", "clarify"
        """
        # Low confidence → clarify or transfer
        if confidence < self.confidence_threshold:
            if state["clarification_count"] >= self.max_clarification_attempts:
                logger.info("Max clarifications reached, transferring to human")
                return "transfer"
            else:
                state["clarification_count"] += 1
                return "clarify"

        # Complete booking captured → confirm and end
        if booking_info and self._is_booking_complete(booking_info):
            logger.info("Booking complete, ending call")
            return "end"

        # Complaint or complex issue → transfer
        if intent in ["complaint", "cancellation", "custom_request"]:
            logger.info(f"Complex intent detected: {intent}, transferring")
            return "transfer"

        # Default: continue conversation
        return "continue"

    def _is_booking_complete(self, booking_info: dict[str, Any]) -> bool:
        """Check if all required booking info is captured"""
        required_fields = ["party_size", "event_date", "location", "contact_info"]
        return all(booking_info.get(field) for field in required_fields)

    async def _get_customer_history(self, phone_number: str) -> Optional[dict[str, Any]]:
        """Get customer history from database"""
        # TODO: Query database for customer info
        return None

    async def _end_conversation(self, state: dict[str, Any]) -> dict[str, Any]:
        """End conversation gracefully"""
        duration = (datetime.now(timezone.utc) - state["started_at"]).total_seconds()

        summary = {
            "call_id": state["call_id"],
            "duration_seconds": duration,
            "message_count": len(state["messages"]),
            "booking_info": state["context"].get("booking_info"),
            "ended_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"Conversation ended: {json.dumps(summary)}")

        return {
            "event": "end",
            "summary": summary,
        }

    async def analyze_call_quality(
        self, call_id: str, transcripts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Analyze call quality and conversation effectiveness.

        Args:
            call_id: Call identifier
            transcripts: List of transcription segments

        Returns:
            Analysis with quality metrics
        """
        try:
            # Calculate metrics
            total_words = sum(len(t["text"].split()) for t in transcripts)
            avg_confidence = (
                sum(t.get("confidence", 0) for t in transcripts) / len(transcripts)
                if transcripts
                else 0
            )

            # Sentiment analysis (using orchestrator)
            full_transcript = " ".join(t["text"] for t in transcripts)
            sentiment = await self._analyze_sentiment(full_transcript)

            # Detect key moments
            booking_mentioned = any(
                keyword in t["text"].lower()
                for t in transcripts
                for keyword in ["book", "reservation", "party", "event"]
            )
            complaint_detected = any(
                keyword in t["text"].lower()
                for t in transcripts
                for keyword in ["complaint", "problem", "issue", "unhappy", "disappointed"]
            )

            analysis = {
                "call_id": call_id,
                "total_words": total_words,
                "avg_confidence": avg_confidence,
                "sentiment": sentiment,
                "booking_mentioned": booking_mentioned,
                "complaint_detected": complaint_detected,
                "quality_score": self._calculate_quality_score(
                    avg_confidence, sentiment, booking_mentioned, complaint_detected
                ),
            }

            logger.info(f"Call analysis complete: {json.dumps(analysis)}")
            return analysis

        except Exception as e:
            logger.exception(f"Error analyzing call: {e}")
            return {"error": str(e)}

    async def _analyze_sentiment(self, text: str) -> str:
        """Analyze sentiment of conversation"""
        # TODO: Use emotion service or orchestrator
        # For now, simple keyword detection
        negative_keywords = ["complaint", "problem", "unhappy", "bad", "terrible"]
        positive_keywords = ["great", "excellent", "love", "perfect", "amazing"]

        text_lower = text.lower()

        if any(word in text_lower for word in negative_keywords):
            return "negative"
        elif any(word in text_lower for word in positive_keywords):
            return "positive"
        else:
            return "neutral"

    def _calculate_quality_score(
        self,
        confidence: float,
        sentiment: str,
        booking_mentioned: bool,
        complaint_detected: bool,
    ) -> float:
        """Calculate overall call quality score (0-100)"""
        score = 50.0  # Base score

        # Confidence factor (max +30)
        score += confidence * 30

        # Sentiment factor (max +20)
        if sentiment == "positive":
            score += 20
        elif sentiment == "neutral":
            score += 10
        elif sentiment == "negative":
            score -= 10

        # Booking mentioned (+10)
        if booking_mentioned:
            score += 10

        # Complaint detected (-20)
        if complaint_detected:
            score -= 20

        # Clamp to 0-100
        return max(0, min(100, score))
