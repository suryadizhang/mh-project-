"""
RingCentral Voice Service
Handles voice calls, webhooks, and call state management.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
import logging
from typing import Any, Optional
from uuid import UUID

from models.call_recording import CallRecording, CallState
from services.speech_service import speech_service
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class CallDirection(str, Enum):
    """Call direction"""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class RingCentralVoiceService:
    """Service for handling voice calls via RingCentral"""

    def __init__(self):
        self.active_calls: dict[str, dict[str, Any]] = {}

    async def handle_inbound_call(
        self,
        db: AsyncSession,
        call_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle inbound call webhook.

        Args:
            db: Database session
            call_data: RingCentral call webhook data

        Returns:
            Call handling result
        """
        try:
            call_id = call_data.get("id")
            from_number = call_data.get("from", {}).get("phoneNumber")
            to_number = call_data.get("to", {}).get("phoneNumber")

            logger.info(f"Inbound call: {call_id} from {from_number} to {to_number}")

            # Create call recording entry
            call_recording = CallRecording(
                rc_call_id=call_id,
                direction=CallDirection.INBOUND.value,
                from_number=from_number,
                to_number=to_number,
                status="ringing",
                state=CallState.INITIATED,
                started_at=datetime.now(timezone.utc),
            )

            db.add(call_recording)
            await db.commit()
            await db.refresh(call_recording)

            # Track active call
            self.active_calls[call_id] = {
                "id": call_id,
                "recording_id": call_recording.id,
                "from": from_number,
                "to": to_number,
                "state": CallState.INITIATED,
                "started_at": datetime.now(timezone.utc),
            }

            return {
                "success": True,
                "call_id": call_id,
                "recording_id": str(call_recording.id),
                "action": "answer",  # Auto-answer the call
            }

        except Exception as e:
            logger.exception(f"Error handling inbound call: {e}")
            return {"success": False, "error": str(e)}

    async def handle_call_status(
        self,
        db: AsyncSession,
        status_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle call status update webhook.

        Args:
            db: Database session
            status_data: RingCentral status update data

        Returns:
            Update result
        """
        try:
            call_id = status_data.get("id")
            status = status_data.get("status")
            duration = status_data.get("duration")

            logger.info(f"Call status update: {call_id} -> {status}")

            # Update database
            result = await db.execute(
                select(CallRecording).where(CallRecording.rc_call_id == call_id)
            )
            call_recording = result.scalar_one_or_none()

            if call_recording:
                call_recording.status = status

                # Map status to state
                state_mapping = {
                    "Setup": CallState.INITIATED,
                    "Proceeding": CallState.INITIATED,
                    "Answered": CallState.IN_PROGRESS,
                    "InProgress": CallState.IN_PROGRESS,
                    "Disconnected": CallState.COMPLETED,
                    "Voicemail": CallState.FAILED,
                    "Rejected": CallState.FAILED,
                    "Missed": CallState.FAILED,
                    "Busy": CallState.FAILED,
                }

                call_recording.state = state_mapping.get(status, CallState.IN_PROGRESS)

                if status in ["Disconnected", "Voicemail", "Rejected", "Missed"]:
                    call_recording.ended_at = datetime.now(timezone.utc)

                if duration:
                    call_recording.duration_seconds = duration

                await db.commit()

                # Update active calls tracking
                if call_id in self.active_calls:
                    self.active_calls[call_id]["state"] = call_recording.state
                    self.active_calls[call_id]["status"] = status

                    # Remove from active if ended
                    if status in ["Disconnected", "Voicemail", "Rejected", "Missed"]:
                        del self.active_calls[call_id]

            return {"success": True, "call_id": call_id, "status": status}

        except Exception as e:
            logger.exception(f"Error handling call status: {e}")
            return {"success": False, "error": str(e)}

    async def handle_recording_ready(
        self,
        db: AsyncSession,
        recording_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Handle recording ready webhook.

        Args:
            db: Database session
            recording_data: RingCentral recording data

        Returns:
            Recording handling result
        """
        try:
            call_id = recording_data.get("id")
            recording_uri = recording_data.get("uri")

            logger.info(f"Recording ready for call: {call_id}")

            # Update database
            result = await db.execute(
                select(CallRecording).where(CallRecording.rc_call_id == call_id)
            )
            call_recording = result.scalar_one_or_none()

            if call_recording:
                call_recording.recording_uri = recording_uri
                call_recording.state = CallState.RECORDED
                await db.commit()

                # TODO: Trigger download and transcription
                # Can be done via Celery task
                logger.info(f"Recording URI saved: {recording_uri}")

            return {"success": True, "call_id": call_id, "recording_uri": recording_uri}

        except Exception as e:
            logger.exception(f"Error handling recording: {e}")
            return {"success": False, "error": str(e)}

    async def transcribe_call_recording(
        self,
        db: AsyncSession,
        recording_id: UUID,
        audio_bytes: bytes,
    ) -> dict[str, Any]:
        """
        Transcribe call recording using Deepgram.

        Args:
            db: Database session
            recording_id: Call recording ID
            audio_bytes: Audio file bytes

        Returns:
            Transcription result
        """
        try:
            # Get call recording
            result = await db.execute(
                select(CallRecording).where(CallRecording.id == recording_id)
            )
            call_recording = result.scalar_one_or_none()

            if not call_recording:
                raise ValueError(f"Call recording {recording_id} not found")

            logger.info(f"Transcribing recording: {recording_id}")

            # Transcribe using Deepgram
            transcription_result = await speech_service.transcribe_audio_file(audio_bytes)

            # Extract transcript
            transcript = transcription_result.get("transcript", "")
            confidence = transcription_result.get("confidence", 0.0)
            words = transcription_result.get("words", [])

            # Update database
            call_recording.transcript = transcript
            call_recording.transcript_confidence = confidence
            call_recording.state = CallState.TRANSCRIBED

            # Store word-level timing (optional, for advanced features)
            if words:
                call_recording.metadata = call_recording.metadata or {}
                call_recording.metadata["word_timing"] = words

            await db.commit()

            logger.info(
                f"Transcription complete: {len(transcript)} chars, "
                f"{confidence:.2%} confidence"
            )

            return {
                "success": True,
                "recording_id": str(recording_id),
                "transcript": transcript,
                "confidence": confidence,
                "word_count": len(transcript.split()),
            }

        except Exception as e:
            logger.exception(f"Error transcribing recording: {e}")
            return {"success": False, "error": str(e)}

    async def initiate_outbound_call(
        self,
        db: AsyncSession,
        to_number: str,
        from_number: str,
        ai_greeting: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Initiate outbound call (future feature).

        Args:
            db: Database session
            to_number: Destination phone number
            from_number: Source phone number
            ai_greeting: Optional AI greeting message

        Returns:
            Call initiation result
        """
        try:
            logger.info(f"Initiating outbound call to {to_number}")

            # TODO: Implement RingCentral API call to initiate call
            # This would use RingCentral's telephony API

            return {
                "success": True,
                "message": "Outbound calls not yet implemented",
                "to": to_number,
                "from": from_number,
            }

        except Exception as e:
            logger.exception(f"Error initiating outbound call: {e}")
            return {"success": False, "error": str(e)}

    def get_active_calls(self) -> list[dict[str, Any]]:
        """
        Get list of currently active calls.

        Returns:
            List of active call data
        """
        return list(self.active_calls.values())

    async def get_call_analytics(
        self,
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """
        Get call analytics for a date range.

        Args:
            db: Database session
            start_date: Start date filter
            end_date: End date filter

        Returns:
            Analytics data
        """
        try:
            query = select(CallRecording)

            if start_date:
                query = query.where(CallRecording.started_at >= start_date)
            if end_date:
                query = query.where(CallRecording.started_at <= end_date)

            result = await db.execute(query)
            recordings = result.scalars().all()

            total_calls = len(recordings)
            total_duration = sum(r.duration_seconds or 0 for r in recordings)
            transcribed_calls = sum(1 for r in recordings if r.transcript)

            return {
                "total_calls": total_calls,
                "total_duration_seconds": total_duration,
                "average_duration_seconds": total_duration / total_calls if total_calls > 0 else 0,
                "transcribed_calls": transcribed_calls,
                "transcription_rate": transcribed_calls / total_calls if total_calls > 0 else 0,
                "active_calls": len(self.active_calls),
            }

        except Exception as e:
            logger.exception(f"Error getting call analytics: {e}")
            return {"error": str(e)}


# Global voice service instance
voice_service = RingCentralVoiceService()
