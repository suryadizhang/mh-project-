"""
RingCentral Voice Webhooks
API endpoints for handling voice call events.
"""

import logging
from typing import Any
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from services.ringcentral_voice import RingCentralVoiceService

logger = logging.getLogger(__name__)

router = APIRouter()


class CallWebhookData(BaseModel):
    """RingCentral call webhook payload"""

    event: str
    sessionId: str
    timestamp: str
    subscriptionId: str | None = None
    body: dict[str, Any] | None = None


@router.post("/voice/inbound")
async def handle_inbound_call_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle inbound voice call webhook from RingCentral.

    Called when:
    - New inbound call arrives
    - Call needs to be answered/routed

    Returns instructions for RingCentral on how to handle the call.
    """
    try:
        payload = await request.json()
        logger.info(f"📞 Inbound call webhook: {payload.get('event')}")

        voice_service = RingCentralVoiceService(db)

        # Process call in background
        call_data = payload.get("body", {})
        response = await voice_service.handle_inbound_call(call_data)

        return response

    except Exception as e:
        logger.exception(f"Error handling inbound call webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process inbound call: {str(e)}",
        )


@router.post("/voice/status")
async def handle_call_status_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle call status update webhooks from RingCentral.

    Events:
    - call.answered
    - call.recording.started
    - call.recording.stopped
    - call.hold
    - call.unhold
    - call.transfer
    - call.hangup
    """
    try:
        payload = await request.json()
        event = payload.get("event")

        logger.info(f"Call status update: {event}")

        voice_service = RingCentralVoiceService(db)

        # Process status update
        status_data = payload.get("body", {})
        background_tasks.add_task(voice_service.handle_call_status, status_data)

        return {"status": "received", "event": event}

    except Exception as e:
        logger.exception(f"Error handling call status webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process call status: {str(e)}",
        )


@router.post("/voice/recording-complete")
async def handle_recording_complete_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle call recording completion webhook.

    Called when:
    - Call recording is complete and ready for download
    - Recording has been processed and stored
    """
    try:
        payload = await request.json()
        logger.info("🔴 Recording complete webhook received")

        recording_data = payload.get("body", {})
        session_id = recording_data.get("sessionId")
        recording_url = recording_data.get("recordingUrl")

        logger.info(f"Recording ready: {session_id} - {recording_url}")

        # TODO: Download and store recording
        # TODO: Transcribe recording for quality analysis
        # TODO: Update call record with recording URL

        return {"status": "received", "session_id": session_id}

    except Exception as e:
        logger.exception(f"Error handling recording complete webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process recording: {str(e)}",
        )


@router.post("/voice/transcription")
async def handle_transcription_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle real-time transcription webhook from RingCentral.

    Receives:
    - Partial transcripts (interim results)
    - Final transcripts (complete utterances)

    Used for:
    - Real-time AI response generation
    - Live call monitoring
    - Conversation logging
    """
    try:
        payload = await request.json()
        transcript_data = payload.get("body", {})

        text = transcript_data.get("text", "")
        is_final = transcript_data.get("is_final", False)
        confidence = transcript_data.get("confidence", 0.0)
        session_id = transcript_data.get("sessionId")

        logger.info(
            f"Transcript: '{text}' (final={is_final}, confidence={confidence:.2f})"
        )

        if is_final:
            # Process final transcript
            # TODO: Generate AI response
            # TODO: Convert to speech
            # TODO: Send audio to call
            pass

        return {"status": "received", "session_id": session_id}

    except Exception as e:
        logger.exception(f"Error handling transcription webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process transcription: {str(e)}",
        )


@router.get("/voice/calls/stats")
async def get_call_statistics(
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get voice call statistics.

    Query params:
    - start_date: ISO format start date
    - end_date: ISO format end date

    Returns:
    - Total calls
    - Answer rate
    - Average duration
    - AI success rate
    - Transfer rate
    """
    try:
        from datetime import datetime, timezone, timedelta

        # Default to last 7 days
        if not start_date:
            start = datetime.now(timezone.utc) - timedelta(days=7)
        else:
            start = datetime.fromisoformat(start_date)

        if not end_date:
            end = datetime.now(timezone.utc)
        else:
            end = datetime.fromisoformat(end_date)

        voice_service = RingCentralVoiceService(db)
        stats = await voice_service.get_call_statistics(start, end)

        return stats

    except Exception as e:
        logger.exception(f"Error fetching call stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch stats: {str(e)}",
        )


@router.post("/voice/test")
async def test_voice_ai(
    text: str,
    voice_model: str | None = None,
):
    """
    Test voice AI system.

    Args:
    - text: Text to convert to speech
    - voice_model: Optional Deepgram Aura voice model

    Returns audio file.
    """
    try:
        from services.speech_service import speech_service
        from fastapi.responses import Response

        # Generate speech
        audio = await speech_service.synthesize_speech(
            text=text, voice_model=voice_model, streaming=False
        )

        return Response(content=audio, media_type="audio/mpeg")

    except Exception as e:
        logger.exception(f"Error testing voice AI: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate speech: {str(e)}",
        )


@router.get("/voice/health")
async def voice_ai_health_check():
    """
    Check voice AI system health.

    Returns:
    - Deepgram STT status
    - Deepgram TTS status
    - Configuration
    """
    try:
        from services.speech_service import speech_service

        health = await speech_service.health_check()
        return health

    except Exception as e:
        logger.exception(f"Error checking voice AI health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        )
