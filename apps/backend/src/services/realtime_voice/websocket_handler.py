"""
WebRTC Call Handler
WebSocket endpoint for real-time bidirectional audio streaming with RingCentral.
"""

import asyncio
import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from .audio_processor import AudioConfig, AudioProcessor
from .call_session import CallSession, call_session_manager

# Lazy imports - services loaded on first use, not at module import
# This prevents heavy initialization (spaCy, transformers, etc.) at startup
from .deepgram_stt_bridge import DeepgramSTTBridge, TranscriptResult
from .metrics import VoiceMetrics

logger = logging.getLogger(__name__)


class WebRTCCallHandler:
    """
    Production-grade real-time voice AI handler.

    Flow:
    1. RingCentral connects via WebSocket (media gateway)
    2. Receives RTP/audio packets
    3. Processes audio → Deepgram STT
    4. STT transcript → AI pipeline
    5. AI response → Deepgram TTS
    6. TTS audio → RingCentral via WebSocket

    Features:
    - Real-time bidirectional audio (<100ms latency)
    - Automatic audio format handling
    - Error recovery and graceful degradation
    - Call state management
    - Comprehensive metrics

    Design:
    - Lazy service loading: Heavy services (NLP, AI, TTS) loaded on first use
    - This prevents 2+ second startup penalty from spaCy/transformers
    - Services are cached after first load
    """

    def __init__(self):
        # Lazy-loaded services (initialized on first use)
        self._nlp_service = None
        self._speech_service = None
        self._ai_pipeline = None
        logger.info("🎧 WebRTCCallHandler initialized (services lazy-loaded)")

    @property
    def nlp_service(self):
        """Lazy load NLP service (spaCy + transformers)"""
        if self._nlp_service is None:
            from services.enhanced_nlp_service import get_nlp_service

            self._nlp_service = get_nlp_service()
            logger.info("✅ NLP service loaded")
        return self._nlp_service

    @property
    def speech_service(self):
        """Lazy load speech service (Deepgram TTS)"""
        if self._speech_service is None:
            from services.speech_service import speech_service

            self._speech_service = speech_service
            logger.info("✅ Speech service loaded")
        return self._speech_service

    @property
    def ai_pipeline(self):
        """Lazy load AI pipeline"""
        if self._ai_pipeline is None:
            from api.ai.endpoints.services.ai_pipeline import ai_pipeline

            self._ai_pipeline = ai_pipeline
            logger.info("✅ AI pipeline loaded")
        return self._ai_pipeline

    async def handle_call(
        self,
        websocket: WebSocket,
        call_id: str,
        from_number: str,
        to_number: str,
    ):
        """
        Handle real-time voice call via WebSocket.

        Args:
            websocket: WebSocket connection to RingCentral
            call_id: RingCentral call ID
            from_number: Caller number
            to_number: Callee number
        """
        session: Optional[CallSession] = None

        try:
            # Accept WebSocket connection
            await websocket.accept()
            logger.info(f"🔌 WebSocket connected | call={call_id}")

            # Create call session
            session = await call_session_manager.create_session(
                call_id=call_id,
                from_number=from_number,
                to_number=to_number,
            )
            session.websocket = websocket
            session.mark_connected()

            # Initialize audio processor
            audio_processor = AudioProcessor(
                target_config=AudioConfig(
                    sample_rate=16000,  # Deepgram requires 16kHz
                    channels=1,  # Mono
                    sample_width=2,  # 16-bit
                ),
                enable_silence_detection=True,
            )
            session.audio_processor = audio_processor

            # Initialize Deepgram STT bridge
            if not self.speech_service.deepgram_enabled:
                raise RuntimeError("Deepgram not configured")

            stt_bridge = DeepgramSTTBridge(
                deepgram_client=self.speech_service.deepgram_client,
                callback=lambda transcript: asyncio.create_task(
                    self._handle_transcript(session, transcript)
                ),
                model="nova-2",
                language="en",
                sample_rate=16000,
            )
            session.stt_bridge = stt_bridge

            # Start STT bridge
            stt_bridge.start(asyncio.get_event_loop())
            session.mark_in_progress()

            # Send greeting
            await self._send_greeting(session)

            # Main loop: receive audio from RingCentral
            while session.is_active:
                try:
                    # Receive message from WebSocket
                    message = await asyncio.wait_for(
                        websocket.receive(), timeout=30.0  # 30s timeout
                    )

                    if message["type"] == "websocket.disconnect":
                        logger.info(f"WebSocket disconnected | call={call_id}")
                        break

                    # Handle different message types
                    if "text" in message:
                        await self._handle_control_message(session, message["text"])
                    elif "bytes" in message:
                        await self._handle_audio_packet(session, message["bytes"])

                except asyncio.TimeoutError:
                    # Send keepalive
                    await websocket.send_json({"type": "keepalive"})
                    continue
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected | call={call_id}")
                    VoiceMetrics.record_websocket_disconnect("client_disconnect")
                    break
                except Exception as e:
                    logger.error(f"Error in call loop: {e}")
                    session.errors_count += 1
                    VoiceMetrics.record_error("websocket", "loop_error")

                    # Don't break on single errors, try to recover
                    if session.errors_count > 10:
                        logger.error(f"Too many errors, ending call")
                        VoiceMetrics.record_error("websocket", "too_many_errors")
                        break

        except Exception as e:
            logger.exception(f"Fatal error handling call {call_id}: {e}")
            if session:
                session.mark_failed(str(e))

        finally:
            # Cleanup
            if session:
                await call_session_manager.end_session(str(session.session_id))

            try:
                await websocket.close()
            except Exception as e:
                logger.debug(f"Error closing websocket: {e}")

    async def _handle_control_message(self, session: CallSession, message_text: str):
        """
        Handle control/signaling messages from RingCentral.

        Args:
            session: Active call session
            message_text: JSON message from RingCentral
        """
        try:
            data = json.loads(message_text)
            msg_type = data.get("type")

            if msg_type == "start":
                logger.info(f"📞 Call start signal | session={session.session_id}")
                session.mark_in_progress()

            elif msg_type == "stop":
                logger.info(f"📴 Call stop signal | session={session.session_id}")
                session.is_active = False

            elif msg_type == "media_config":
                # RingCentral sends media configuration
                media_format = data.get("mediaFormat", {})
                logger.info(
                    f"🎵 Media config | "
                    f"encoding={media_format.get('encoding')} | "
                    f"rate={media_format.get('sampleRate')}Hz | "
                    f"channels={media_format.get('channels')}"
                )

            elif msg_type == "error":
                error_msg = data.get("message", "Unknown error")
                logger.error(f"❌ RingCentral error: {error_msg}")
                session.errors_count += 1

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON control message: {message_text[:100]}")
        except Exception as e:
            logger.error(f"Error handling control message: {e}")

    async def _handle_audio_packet(self, session: CallSession, audio_data: bytes):
        """
        Handle incoming audio packet from RingCentral.

        Args:
            session: Active call session
            audio_data: Raw audio data (typically RTP payload)
        """
        try:
            session.audio_frames_received += 1
            VoiceMetrics.record_audio_frame_received()

            # Process audio (resample, format conversion)
            # Assume 8kHz mulaw (typical for RingCentral/SIP)
            frames = session.audio_processor.process_frame(
                audio_data,
                source_rate=8000,
                source_encoding="mulaw",
            )

            # Send each frame to Deepgram STT
            for frame in frames:
                await session.stt_bridge.send_audio(frame)

        except Exception as e:
            logger.error(f"Error processing audio packet: {e}")
            session.errors_count += 1
            VoiceMetrics.record_error("audio_processor", "processing_error")

    async def _handle_transcript(
        self, session: CallSession, transcript: TranscriptResult
    ):
        """
        Handle transcript from Deepgram STT.

        Args:
            session: Active call session
            transcript: Transcript result
        """
        try:
            # Add to session
            session.add_transcript(transcript.to_dict())

            # Record metrics
            VoiceMetrics.record_transcript(
                is_final=transcript.is_final, confidence=transcript.confidence
            )

            # Only process final transcripts
            if not transcript.is_final:
                logger.debug(f"Interim: {transcript.text}")
                return

            # Log final transcript
            logger.info(
                f"📝 Final transcript: '{transcript.text}' (conf={transcript.confidence:.2f})"
            )

            # Add to conversation
            session.add_message("user", transcript.text)

            # Generate AI response
            await self._generate_and_send_response(session, transcript.text)

        except Exception as e:
            logger.exception(f"Error handling transcript: {e}")
            session.errors_count += 1
            VoiceMetrics.record_stt_error("transcript_processing_error")

    async def _generate_and_send_response(
        self, session: CallSession, user_message: str
    ):
        """
        Generate AI response and send as audio.

        Args:
            session: Active call session
            user_message: User's message text
        """
        try:
            # Start timing AI response
            start_time = asyncio.get_event_loop().time()

            # 1. Enhanced NLP analysis
            nlp_result = await asyncio.to_thread(
                self.nlp_service.extract_booking_details, user_message
            )

            intent = nlp_result.get("intent", "unknown")
            confidence = nlp_result.get("confidence", 0.0)

            # 2. Detect tone
            tone_result = await asyncio.to_thread(
                self.nlp_service.detect_tone_enhanced, user_message
            )
            detected_tone = tone_result.get("tone", "neutral")

            logger.info(
                f"🧠 NLP | intent={intent} | "
                f"conf={confidence:.2f} | tone={detected_tone}"
            )

            # 3. Generate AI response
            ai_context = {
                "channel": "voice",
                "call_id": session.call_id,
                "from_number": session.from_number,
                "intent": intent,
                "tone": detected_tone,
                "turn_count": session.turn_count,
            }

            response = await self.ai_pipeline.generate_response(
                user_message=user_message, context=ai_context
            )

            # Update session state
            session.current_intent = intent
            session.add_message("assistant", response)

            # Record AI response metrics
            ai_latency = asyncio.get_event_loop().time() - start_time
            VoiceMetrics.record_ai_response(intent=intent, latency=ai_latency)

            # Check for escalation
            if intent in ["complaint", "escalation", "manager"] or confidence < 0.4:
                session.should_escalate = True
                VoiceMetrics.record_escalation(reason=intent)
                logger.warning(
                    f"⚠️ Escalation triggered | intent={intent} | conf={confidence:.2f}"
                )

            logger.info(f"🤖 AI response: '{response[:100]}...'")

            # 4. Convert to speech (TTS)
            tts_start_time = asyncio.get_event_loop().time()
            audio_bytes = await self.speech_service.synthesize_speech(
                text=response,
                voice_model="aura-asteria-en",
            )
            tts_latency = asyncio.get_event_loop().time() - tts_start_time

            # Record TTS metrics
            VoiceMetrics.record_tts_request(
                latency=tts_latency, audio_size=len(audio_bytes)
            )

            # 5. Send audio to RingCentral
            await self._send_audio(session, audio_bytes)

        except Exception as e:
            logger.exception(f"Error generating response: {e}")
            session.errors_count += 1
            VoiceMetrics.record_error("ai_pipeline", "response_generation_error")

            # Send fallback message
            fallback = "I apologize, I'm having trouble processing that. Let me connect you with someone who can help."
            try:
                audio_bytes = await self.speech_service.synthesize_speech(fallback)
                await self._send_audio(session, audio_bytes)
                session.should_escalate = True
                VoiceMetrics.record_escalation(reason="error")
            except Exception as e:
                logger.warning(f"Failed to send fallback audio: {e}")

    async def _send_greeting(self, session: CallSession):
        """
        Send greeting message at call start.

        Args:
            session: Active call session
        """
        try:
            greeting = "Hello! Thank you for calling My Hibachi Chef. How can I help you today?"

            logger.info(f"👋 Sending greeting | session={session.session_id}")

            # Add to conversation
            session.add_message("assistant", greeting)

            # Synthesize and send
            audio_bytes = await self.speech_service.synthesize_speech(
                text=greeting,
                voice_model="aura-asteria-en",
            )

            await self._send_audio(session, audio_bytes)

        except Exception as e:
            logger.error(f"Error sending greeting: {e}")
            session.errors_count += 1

    async def _send_audio(self, session: CallSession, audio_bytes: bytes):
        """
        Send audio to RingCentral via WebSocket.

        Args:
            session: Active call session
            audio_bytes: Audio data to send (PCM 16kHz mono 16-bit)
        """
        try:
            if not session.websocket:
                logger.warning("No WebSocket connection")
                return

            # RingCentral expects audio in specific format
            # May need conversion depending on their media gateway requirements

            # Send as binary WebSocket message
            # For text-based protocol, base64 encode:
            # audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            # await session.websocket.send_json({"type": "audio", "data": audio_b64})

            # For binary protocol:
            await session.websocket.send_bytes(audio_bytes)

            session.audio_frames_sent += 1
            VoiceMetrics.record_audio_frame_sent()

            logger.debug(f"📤 Sent audio | size={len(audio_bytes)} bytes")

        except Exception as e:
            logger.error(f"Error sending audio: {e}")
            session.errors_count += 1
            VoiceMetrics.record_error("websocket", "audio_send_error")


# Global handler instance
webrtc_call_handler = WebRTCCallHandler()
