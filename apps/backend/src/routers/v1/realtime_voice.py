"""
Real-time Voice WebSocket Router
WebSocket endpoints for RingCentral voice AI integration.
"""

import logging
from fastapi import APIRouter, WebSocket, Query
from typing import Optional

from services.realtime_voice.websocket_handler import webrtc_call_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice/realtime", tags=["Voice - Real-time"])


@router.websocket("/ws/call")
async def websocket_call_endpoint(
    websocket: WebSocket,
    call_id: str = Query(..., description="RingCentral call ID"),
    from_number: str = Query(..., description="Caller phone number"),
    to_number: str = Query(..., description="Callee phone number"),
    session_id: Optional[str] = Query(None, description="Optional session ID"),
):
    """
    WebSocket endpoint for real-time voice calls.

    RingCentral media gateway connects here to establish bidirectional audio stream.

    Flow:
    1. RingCentral initiates WebSocket connection
    2. Sends audio packets (RTP payload)
    3. Receives AI-generated audio responses
    4. Streams back to caller

    Parameters:
    - call_id: RingCentral call identifier
    - from_number: Caller's phone number (E.164 format)
    - to_number: Called number (E.164 format)
    - session_id: Optional session ID for tracking

    Example:
    ws://localhost:8000/api/voice/realtime/ws/call?call_id=abc123&from_number=+15555551234&to_number=+15555555678
    """
    logger.info(
        f"🎧 New WebSocket call | call_id={call_id} | " f"from={from_number} | to={to_number}"
    )

    try:
        await webrtc_call_handler.handle_call(
            websocket=websocket,
            call_id=call_id,
            from_number=from_number,
            to_number=to_number,
        )
    except Exception as e:
        logger.exception(f"WebSocket call handler error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


@router.get("/health")
async def realtime_voice_health():
    """
    Health check for real-time voice system.

    Returns status of:
    - Deepgram connectivity
    - Active call sessions
    - System readiness
    """
    from services.speech_service import speech_service
    from services.realtime_voice.call_session import call_session_manager

    # Check Deepgram
    deepgram_status = "healthy" if speech_service.deepgram_enabled else "unavailable"

    # Get active sessions
    stats = call_session_manager.get_stats()

    return {
        "status": "healthy",
        "deepgram": deepgram_status,
        "active_calls": stats["active_sessions"],
        "total_calls": stats["total_calls"],
        "success_rate": stats["success_rate"],
    }
