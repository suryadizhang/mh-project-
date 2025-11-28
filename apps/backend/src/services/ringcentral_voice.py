"""
RingCentral Voice Service
Handles inbound/outbound phone calls with AI voice assistant integration.
"""

from datetime import datetime, timezone
from enum import Enum
import logging
import os
from typing import Any
from uuid import uuid4

from services.speech_service import speech_service
from services.ringcentral_service import RingCentralService

# MIGRATED: from models.call_recording → db.models.call_recording
from db.models.call_recording import CallRecording, CallStatus, CallDirection
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

logger = logging.getLogger(__name__)


class CallEvent(str, Enum):
    """RingCentral call events"""

    RINGING = "ringing"
    ANSWERED = "answered"
    RECORDING_STARTED = "recording-started"
    RECORDING_STOPPED = "recording-stopped"
    HOLD = "hold"
    UNHOLD = "unhold"
    MUTE = "mute"
    UNMUTE = "unmute"
    TRANSFER = "transfer"
    HANGUP = "hangup"
    MISSED = "missed"


class VoiceAIMode(str, Enum):
    """Voice AI operating modes"""

    FULL_AUTO = "full_auto"  # AI handles entire call
    ASSISTED = "assisted"  # AI assists human agent
    HUMAN_ONLY = "human_only"  # Transfer to human immediately
    TRIAGE = "triage"  # AI qualifies, then transfers


class RingCentralVoiceService:
    """
    Voice call handling with AI assistant.

    Features:
    - Inbound call answering
    - Real-time speech-to-text
    - AI response generation
    - Text-to-speech output
    - Call recording
    - Human escalation
    - Call routing
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rc_service = RingCentralService()
        self.speech_service = speech_service

        # Voice AI configuration
        self.voice_ai_enabled = os.getenv("ENABLE_VOICE_AI", "false").lower() == "true"
        self.default_mode = VoiceAIMode(os.getenv("VOICE_AI_MODE", VoiceAIMode.TRIAGE.value))
        self.max_call_duration = int(os.getenv("MAX_CALL_DURATION_SECONDS", "1800"))  # 30 min

        # Call routing
        self.business_hours_start = int(os.getenv("BUSINESS_HOURS_START", "9"))  # 9 AM
        self.business_hours_end = int(os.getenv("BUSINESS_HOURS_END", "17"))  # 5 PM

        logger.info(
            f"Voice service initialized (ai_enabled={self.voice_ai_enabled}, "
            f"mode={self.default_mode})"
        )

    async def handle_inbound_call(self, call_data: dict[str, Any]) -> dict[str, Any]:
        """
        Handle incoming phone call.

        Args:
            call_data: RingCentral call webhook data

        Returns:
            Dict with call handling instructions
        """
        try:
            session_id = call_data.get("sessionId")
            from_number = call_data.get("from", {}).get("phoneNumber")
            to_number = call_data.get("to", {}).get("phoneNumber")

            logger.info(f"📞 Inbound call: {from_number} → {to_number} (session: {session_id})")

            # Create call record
            call_record = await self._create_call_record(
                session_id=session_id,
                from_number=from_number,
                to_number=to_number,
                direction=CallDirection.INBOUND,
            )

            # Determine routing strategy
            routing = await self._determine_call_routing(call_data)

            if routing["action"] == "ai_handle":
                # AI handles the call
                return await self._handle_with_ai(call_record, call_data)

            elif routing["action"] == "transfer_human":
                # Transfer to human immediately
                return await self._transfer_to_human(call_record, routing["agent_number"])

            elif routing["action"] == "voicemail":
                # Send to voicemail (after hours)
                return await self._send_to_voicemail(call_record)

            else:
                # Default: AI triage then transfer
                return await self._ai_triage_then_transfer(call_record, call_data)

        except Exception as e:
            logger.exception(f"Error handling inbound call: {e}")
            # Fallback: transfer to human
            return {
                "action": "transfer",
                "number": os.getenv("FALLBACK_PHONE_NUMBER", "+19167408768"),
            }

    async def handle_call_status(self, status_data: dict[str, Any]) -> None:
        """
        Handle call status updates (answered, recording started, hangup, etc.)

        Args:
            status_data: RingCentral status webhook data
        """
        try:
            session_id = status_data.get("sessionId")
            event = status_data.get("event")

            logger.info(f"Call status update: {session_id} - {event}")

            # Find call record
            result = await self.db.execute(
                select(CallRecording).where(CallRecording.rc_call_id == session_id)
            )
            call_record = result.scalar_one_or_none()

            if not call_record:
                logger.warning(f"Call record not found: {session_id}")
                return

            # Update based on event
            if event == CallEvent.ANSWERED:
                await self._handle_call_answered(call_record, status_data)

            elif event == CallEvent.RECORDING_STARTED:
                await self._handle_recording_started(call_record, status_data)

            elif event == CallEvent.HANGUP:
                await self._handle_call_hangup(call_record, status_data)

            elif event == CallEvent.TRANSFER:
                await self._handle_call_transfer(call_record, status_data)

            await self.db.commit()

        except Exception as e:
            logger.exception(f"Error handling call status: {e}")
            await self.db.rollback()

    async def _handle_with_ai(
        self, call_record: CallRecording, call_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Handle call with full AI assistant.

        Returns:
            Instructions for RingCentral
        """
        logger.info(f"🤖 AI handling call: {call_record.rc_call_id}")

        # Answer the call
        await self._answer_call(call_record)

        # Start recording
        await self._start_recording(call_record)

        # Initial greeting
        greeting = await self._generate_ai_greeting(call_data)

        # Convert to speech
        audio_stream = self.speech_service.synthesize_speech(greeting, streaming=True)

        return {
            "action": "answer",
            "play_audio": audio_stream,
            "start_recording": True,
            "enable_transcription": True,
        }

    async def _ai_triage_then_transfer(
        self, call_record: CallRecording, call_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        AI qualifies the call, then transfers to appropriate agent.

        Returns:
            Instructions for RingCentral
        """
        logger.info(f"🔍 AI triage mode: {call_record.rc_call_id}")

        # Answer and greet
        await self._answer_call(call_record)

        greeting = (
            "Hi! This is MyHibachi. Thanks for calling. "
            "I'm your AI assistant. How can I help you today?"
        )

        # Start conversation
        # (Actual implementation would stream audio and transcribe responses)

        return {
            "action": "answer",
            "message": greeting,
            "start_recording": True,
            "enable_transcription": True,
            "triage_mode": True,
        }

    async def _transfer_to_human(
        self, call_record: CallRecording, agent_number: str
    ) -> dict[str, Any]:
        """Transfer call to human agent"""
        logger.info(f"👤 Transferring to human: {agent_number}")

        call_record.status = CallStatus.TRANSFERRED
        call_record.transferred_at = datetime.now(timezone.utc)
        await self.db.commit()

        return {
            "action": "transfer",
            "number": agent_number,
            "announcement": "Transferring you to a team member now.",
        }

    async def _send_to_voicemail(self, call_record: CallRecording) -> dict[str, Any]:
        """Send call to voicemail"""
        logger.info(f"📧 Sending to voicemail: {call_record.rc_call_id}")

        call_record.status = CallStatus.VOICEMAIL
        await self.db.commit()

        message = (
            "Thank you for calling MyHibachi. We're currently closed. "
            "Please leave a message and we'll get back to you soon."
        )

        return {
            "action": "voicemail",
            "message": message,
            "start_recording": True,
        }

    async def _determine_call_routing(self, call_data: dict[str, Any]) -> dict[str, Any]:
        """
        Determine how to route the call based on time, caller, etc.

        Returns:
            Dict with routing decision
        """
        # Check business hours
        now = datetime.now(timezone.utc)
        hour = now.hour

        if hour < self.business_hours_start or hour >= self.business_hours_end:
            return {"action": "voicemail", "reason": "after_hours"}

        # Check if caller is VIP (has previous bookings)
        from_number = call_data.get("from", {}).get("phoneNumber")
        is_vip = await self._check_vip_status(from_number)

        if is_vip:
            # VIP customers go to human immediately
            return {
                "action": "transfer_human",
                "agent_number": os.getenv("VIP_AGENT_NUMBER", "+19167408768"),
                "reason": "vip_customer",
            }

        # Default: AI triage
        if self.voice_ai_enabled and self.default_mode == VoiceAIMode.FULL_AUTO:
            return {"action": "ai_handle", "reason": "auto_mode"}
        else:
            return {"action": "ai_triage", "reason": "triage_mode"}

    async def _check_vip_status(self, phone_number: str) -> bool:
        """Check if caller is a VIP customer"""
        # TODO: Check database for previous bookings
        # For now, return False
        return False

    async def _create_call_record(
        self, session_id: str, from_number: str, to_number: str, direction: CallDirection
    ) -> CallRecording:
        """Create call record in database"""
        call_record = CallRecording(
            id=uuid4(),
            rc_call_id=session_id,
            caller_phone=from_number,
            recipient_phone=to_number,
            direction=direction,
            status=CallStatus.RINGING,
            started_at=datetime.now(timezone.utc),
        )

        self.db.add(call_record)
        await self.db.commit()
        await self.db.refresh(call_record)

        logger.info(f"✅ Call record created: {call_record.id}")
        return call_record

    async def _answer_call(self, call_record: CallRecording) -> None:
        """Mark call as answered"""
        call_record.status = CallStatus.IN_PROGRESS
        call_record.answered_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def _start_recording(self, call_record: CallRecording) -> None:
        """Start call recording"""
        # RingCentral automatically starts recording if configured
        call_record.recording_started_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.info(f"🔴 Recording started: {call_record.rc_call_id}")

    async def _generate_ai_greeting(self, call_data: dict[str, Any]) -> str:
        """Generate personalized AI greeting"""
        from_number = call_data.get("from", {}).get("phoneNumber")

        # Check if returning customer
        # TODO: Personalize based on customer history

        return (
            "Hi! Thank you for calling MyHibachi. "
            "I'm your AI assistant. How can I help you today?"
        )

    async def _handle_call_answered(
        self, call_record: CallRecording, status_data: dict[str, Any]
    ) -> None:
        """Handle call answered event"""
        call_record.status = CallStatus.IN_PROGRESS
        call_record.answered_at = datetime.now(timezone.utc)
        logger.info(f"✅ Call answered: {call_record.rc_call_id}")

    async def _handle_recording_started(
        self, call_record: CallRecording, status_data: dict[str, Any]
    ) -> None:
        """Handle recording started event"""
        call_record.recording_started_at = datetime.now(timezone.utc)
        logger.info(f"🔴 Recording started: {call_record.rc_call_id}")

    async def _handle_call_hangup(
        self, call_record: CallRecording, status_data: dict[str, Any]
    ) -> None:
        """Handle call hangup event"""
        call_record.status = CallStatus.COMPLETED
        call_record.ended_at = datetime.now(timezone.utc)

        # Calculate duration
        if call_record.answered_at:
            duration = (call_record.ended_at - call_record.answered_at).total_seconds()
            call_record.duration_seconds = int(duration)

        logger.info(
            f"📵 Call ended: {call_record.rc_call_id} "
            f"(duration: {call_record.duration_seconds}s)"
        )

    async def _handle_call_transfer(
        self, call_record: CallRecording, status_data: dict[str, Any]
    ) -> None:
        """Handle call transfer event"""
        call_record.status = CallStatus.TRANSFERRED
        call_record.transferred_at = datetime.now(timezone.utc)
        logger.info(f"➡️ Call transferred: {call_record.rc_call_id}")

    async def get_call_statistics(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        """
        Get call statistics for a date range.

        Returns:
            Dict with statistics
        """
        result = await self.db.execute(
            select(CallRecording).where(
                CallRecording.started_at >= start_date, CallRecording.started_at <= end_date
            )
        )
        calls = result.scalars().all()

        total_calls = len(calls)
        answered_calls = len([c for c in calls if c.answered_at is not None])
        transferred_calls = len([c for c in calls if c.status == CallStatus.TRANSFERRED])
        voicemails = len([c for c in calls if c.status == CallStatus.VOICEMAIL])

        total_duration = sum((c.duration_seconds or 0) for c in calls)
        avg_duration = total_duration / answered_calls if answered_calls > 0 else 0

        return {
            "total_calls": total_calls,
            "answered_calls": answered_calls,
            "missed_calls": total_calls - answered_calls,
            "transferred_calls": transferred_calls,
            "voicemails": voicemails,
            "answer_rate": (answered_calls / total_calls * 100) if total_calls > 0 else 0,
            "total_duration_seconds": total_duration,
            "avg_duration_seconds": avg_duration,
            "ai_handled": answered_calls - transferred_calls,
            "ai_success_rate": (
                ((answered_calls - transferred_calls) / answered_calls * 100)
                if answered_calls > 0
                else 0
            ),
        }
