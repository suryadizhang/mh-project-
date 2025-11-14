"""
RingCentral Voice AI Service
Bridges RingCentral voice webhooks to AI orchestration system.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CallDirection(str, Enum):
    """Call direction"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class VoiceCallEvent(BaseModel):
    """Voice call event from RingCentral webhook"""
    call_id: str
    direction: str
    from_number: str
    to_number: str
    status: str
    timestamp: datetime


class AIReply(BaseModel):
    """AI-generated reply"""
    reply: str
    intent: str
    confidence: float
    should_escalate: bool
    booking_data: Optional[dict[str, Any]] = None
    tone: str = "warm"


class RingCentralVoiceAI:
    """
    Voice AI Integration Service
    
    Handles:
    - Inbound call routing to AI
    - Real-time STT → AI → TTS pipeline
    - Intent detection and booking extraction
    - Escalation to human agents
    """
    
    def __init__(self):
        self.active_conversations: dict[str, dict[str, Any]] = {}
        
        # Lazy-loaded services (heavy ML models)
        self._nlp_service = None
        self._speech_service = None
        self._ai_pipeline = None
        self._customer_booking_ai = None
        
        # AI configuration
        self.greeting_message = "Hello! Thank you for calling My Hibachi Chef. How can I help you today?"
        self.default_voice = "aura-asteria-en"
        self.max_conversation_turns = 20
        self.escalation_threshold = 0.4  # Confidence below this triggers escalation
        
        logger.info("RingCentral Voice AI service initialized")
    
    @property
    def nlp_service(self):
        """Lazy load NLP service (spaCy + transformers: ~2.3s, 550MB)"""
        if self._nlp_service is None:
            logger.info("Loading NLP service...")
            from services.enhanced_nlp_service import get_nlp_service
            self._nlp_service = get_nlp_service()
        return self._nlp_service
    
    @property
    def speech_service(self):
        """Lazy load speech service (Deepgram SDK)"""
        if self._speech_service is None:
            logger.info("Loading speech service...")
            from services.speech_service import speech_service
            self._speech_service = speech_service
        return self._speech_service
    
    @property
    def ai_pipeline(self):
        """Lazy load AI pipeline (OpenAI/Claude + knowledge base)"""
        if self._ai_pipeline is None:
            logger.info("Loading AI pipeline...")
            from api.ai.endpoints.services.ai_pipeline import ai_pipeline
            self._ai_pipeline = ai_pipeline
        return self._ai_pipeline
    
    @property
    def customer_booking_ai(self):
        """Lazy load customer booking AI"""
        if self._customer_booking_ai is None:
            logger.info("Loading customer booking AI...")
            from api.ai.endpoints.services.customer_booking_ai import customer_booking_ai
            self._customer_booking_ai = customer_booking_ai
        return self._customer_booking_ai
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        pass
    
    async def handle_inbound_call(self, call_event: VoiceCallEvent) -> dict[str, Any]:
        """
        Handle inbound call - auto-answer and start AI conversation.
        
        Args:
            call_event: Call event from RingCentral webhook
            
        Returns:
            Call handling result
        """
        try:
            call_id = call_event.call_id
            from_number = call_event.from_number
            
            logger.info(f"🤖 AI handling inbound call: {call_id} from {from_number}")
            
            # Initialize conversation context
            self.active_conversations[call_id] = {
                "call_id": call_id,
                "from_number": from_number,
                "to_number": call_event.to_number,
                "started_at": call_event.timestamp,
                "turn_count": 0,
                "messages": [],
                "booking_data": {},
                "intent": "unknown",
                "should_escalate": False,
            }
            
            # Generate greeting audio
            greeting_audio = await self._synthesize_greeting()
            
            return {
                "success": True,
                "call_id": call_id,
                "action": "answer",
                "greeting_audio": greeting_audio,
                "ai_enabled": True,
            }
            
        except Exception as e:
            logger.exception(f"Error handling inbound call: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "reject",  # Reject call if AI fails
            }
    
    async def generate_ai_reply(
        self,
        message: str,
        context: dict[str, Any],
    ) -> AIReply:
        """
        Generate AI reply for SMS or voice transcript.
        
        Args:
            message: User message text
            context: Conversation context
            
        Returns:
            AI reply with intent and escalation info
        """
        try:
            channel = context.get("channel", "voice")
            from_number = context.get("from_number", "")
            
            logger.info(f"🤖 Generating AI reply | Channel: {channel} | Message: {message[:50]}...")
            
            # 1. Enhanced NLP Analysis
            nlp_result = await asyncio.to_thread(
                self.nlp_service.extract_booking_details,
                message
            )
            
            intent = nlp_result.get("intent", "unknown")
            confidence = nlp_result.get("confidence", 0.0)
            
            # 2. Detect tone for response matching
            tone_result = await asyncio.to_thread(
                self.nlp_service.detect_tone_enhanced,
                message
            )
            detected_tone = tone_result.get("tone", "neutral")
            
            logger.info(
                f"📊 NLP Analysis | Intent: {intent} | "
                f"Confidence: {confidence:.2f} | Tone: {detected_tone}"
            )
            
            # 3. Extract booking details
            booking_data = {}
            if intent in ["booking", "reservation", "inquiry"]:
                booking_extraction = await self.customer_booking_ai._extract_booking_details(message)
                booking_data = {
                    "guest_count": booking_extraction.get("guest_count"),
                    "date": booking_extraction.get("date"),
                    "time": booking_extraction.get("time"),
                    "proteins": booking_extraction.get("proteins", []),
                    "dietary_restrictions": booking_extraction.get("dietary_restrictions", []),
                    "special_requests": booking_extraction.get("special_requests"),
                }
            
            # 4. Generate AI response using pipeline
            ai_context = {
                "channel": channel,
                "from_number": from_number,
                "intent": intent,
                "tone": detected_tone,
                "booking_data": booking_data,
            }
            
            response = await self.ai_pipeline.generate_response(
                user_message=message,
                context=ai_context
            )
            
            # 5. Determine escalation
            should_escalate = (
                confidence < self.escalation_threshold or
                intent in ["complaint", "escalation", "manager"] or
                "speak to manager" in message.lower() or
                "human" in message.lower()
            )
            
            # 6. Adjust response tone
            reply_tone = self._match_response_tone(detected_tone)
            
            return AIReply(
                reply=response,
                intent=intent,
                confidence=confidence,
                should_escalate=should_escalate,
                booking_data=booking_data if booking_data else None,
                tone=reply_tone,
            )
            
        except Exception as e:
            logger.exception(f"Error generating AI reply: {e}")
            
            # Fallback response
            return AIReply(
                reply="I apologize, but I'm having trouble understanding. Let me connect you with a team member who can help.",
                intent="error",
                confidence=0.0,
                should_escalate=True,
                tone="apologetic",
            )
    
    async def transcribe_and_respond(
        self,
        call_id: str,
        audio_url: str,
    ) -> dict[str, Any]:
        """
        Transcribe audio from call and generate AI response.
        
        Args:
            call_id: Call identifier
            audio_url: URL to audio file
            
        Returns:
            Transcription and response result
        """
        try:
            logger.info(f"🎙️ Transcribing audio for call: {call_id}")
            
            # Download audio
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(audio_url) as resp:
                    audio_bytes = await resp.read()
            
            # Transcribe with Deepgram
            transcript_result = await self.speech_service.transcribe_audio_file(
                audio_bytes,
                language="en"
            )
            
            transcript = transcript_result["transcript"]
            confidence = transcript_result["confidence"]
            
            logger.info(f"📝 Transcript: '{transcript}' (confidence: {confidence:.2%})")
            
            # Generate AI reply
            context = {
                "channel": "voice",
                "call_id": call_id,
                "from_number": self.active_conversations.get(call_id, {}).get("from_number", ""),
            }
            
            ai_reply = await self.generate_ai_reply(transcript, context)
            
            # Synthesize response audio
            response_audio = await self.speech_service.synthesize_speech(
                ai_reply.reply,
                voice_model=self.default_voice
            )
            
            # Update conversation
            if call_id in self.active_conversations:
                self.active_conversations[call_id]["messages"].append({
                    "role": "user",
                    "content": transcript,
                    "timestamp": datetime.now(timezone.utc),
                })
                self.active_conversations[call_id]["messages"].append({
                    "role": "assistant",
                    "content": ai_reply.reply,
                    "timestamp": datetime.now(timezone.utc),
                })
                self.active_conversations[call_id]["turn_count"] += 1
                self.active_conversations[call_id]["intent"] = ai_reply.intent
                self.active_conversations[call_id]["should_escalate"] = ai_reply.should_escalate
            
            return {
                "success": True,
                "call_id": call_id,
                "transcript": transcript,
                "transcript_confidence": confidence,
                "ai_reply": ai_reply.reply,
                "ai_intent": ai_reply.intent,
                "ai_confidence": ai_reply.confidence,
                "should_escalate": ai_reply.should_escalate,
                "response_audio": response_audio,
                "booking_data": ai_reply.booking_data,
            }
            
        except Exception as e:
            logger.exception(f"Error transcribing and responding: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def finalize_call(
        self,
        call_id: str,
    ) -> dict[str, Any]:
        """
        Finalize call - save transcript and cleanup.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Finalization result
        """
        try:
            if call_id not in self.active_conversations:
                logger.warning(f"No active conversation found for call: {call_id}")
                return {"success": False, "error": "Conversation not found"}
            
            conversation = self.active_conversations[call_id]
            
            logger.info(
                f"📴 Finalizing call: {call_id} | "
                f"Turns: {conversation['turn_count']} | "
                f"Intent: {conversation['intent']} | "
                f"Escalated: {conversation['should_escalate']}"
            )
            
            # Prepare summary
            summary = {
                "call_id": call_id,
                "from_number": conversation["from_number"],
                "to_number": conversation["to_number"],
                "duration": (datetime.now(timezone.utc) - conversation["started_at"]).total_seconds(),
                "turn_count": conversation["turn_count"],
                "intent": conversation["intent"],
                "escalated": conversation["should_escalate"],
                "messages": conversation["messages"],
                "booking_data": conversation.get("booking_data", {}),
            }
            
            # Remove from active conversations
            del self.active_conversations[call_id]
            
            return {
                "success": True,
                "call_id": call_id,
                "summary": summary,
            }
            
        except Exception as e:
            logger.exception(f"Error finalizing call: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def _synthesize_greeting(self) -> bytes:
        """Generate greeting audio"""
        try:
            audio = await self.speech_service.synthesize_speech(
                self.greeting_message,
                voice_model=self.default_voice
            )
            return audio
        except Exception as e:
            logger.exception(f"Error synthesizing greeting: {e}")
            return b""
    
    def _match_response_tone(self, detected_tone: str) -> str:
        """Match response tone to user's tone"""
        tone_mapping = {
            "anxious": "reassuring",
            "formal": "professional",
            "casual": "friendly",
            "warm": "warm",
            "direct": "concise",
        }
        return tone_mapping.get(detected_tone, "warm")


# Singleton instance
ringcentral_voice_ai = RingCentralVoiceAI()
