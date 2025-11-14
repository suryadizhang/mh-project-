"""
Call Session Management
Manages active real-time voice calls with lifecycle tracking and cleanup.
"""

import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .metrics import VoiceMetrics

logger = logging.getLogger(__name__)


class CallState(str, Enum):
    """Call state enumeration"""
    INITIALIZING = "initializing"
    RINGING = "ringing"
    CONNECTED = "connected"
    IN_PROGRESS = "in_progress"
    ENDING = "ending"
    ENDED = "ended"
    FAILED = "failed"


@dataclass
class CallSession:
    """
    Active call session with full state tracking.
    """
    # Identifiers
    session_id: UUID = field(default_factory=uuid4)
    call_id: str = ""  # RingCentral call ID
    from_number: str = ""
    to_number: str = ""
    
    # State
    state: CallState = CallState.INITIALIZING
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    connected_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Components
    stt_bridge: Any = None  # DeepgramSTTBridge instance
    audio_processor: Any = None  # AudioProcessor instance
    websocket: Any = None  # WebSocket connection
    
    # Conversation tracking
    turn_count: int = 0
    messages: list[dict[str, Any]] = field(default_factory=list)
    transcripts: list[dict[str, Any]] = field(default_factory=list)
    
    # AI state
    current_intent: str = "unknown"
    should_escalate: bool = False
    booking_data: dict[str, Any] = field(default_factory=dict)
    
    # Metrics
    audio_frames_received: int = 0
    audio_frames_sent: int = 0
    transcripts_count: int = 0
    ai_responses_count: int = 0
    errors_count: int = 0
    
    # Flags
    is_active: bool = True
    has_error: bool = False
    error_message: str = ""
    
    def mark_connected(self):
        """Mark call as connected"""
        self.state = CallState.CONNECTED
        self.connected_at = datetime.now(timezone.utc)
        logger.info(f"📞 Call {self.session_id} connected")
    
    def mark_in_progress(self):
        """Mark call as in progress"""
        self.state = CallState.IN_PROGRESS
        logger.info(f"🗣️ Call {self.session_id} in progress")
    
    def mark_ended(self):
        """Mark call as ended"""
        self.state = CallState.ENDED
        self.ended_at = datetime.now(timezone.utc)
        self.is_active = False
        
        # Record metrics
        duration = self.get_duration()
        VoiceMetrics.record_call_end("completed", duration, self.turn_count, self.transcripts_count)
        
        logger.info(f"📴 Call {self.session_id} ended")
    
    def mark_failed(self, error: str):
        """Mark call as failed"""
        self.state = CallState.FAILED
        self.ended_at = datetime.now(timezone.utc)
        self.is_active = False
        self.has_error = True
        self.error_message = error
        
        # Record metrics
        duration = self.get_duration()
        VoiceMetrics.record_call_end("failed", duration, self.turn_count, self.transcripts_count)
        
        logger.error(f"❌ Call {self.session_id} failed: {error}")
    
    def add_transcript(self, transcript: dict[str, Any]):
        """Add transcript to session"""
        self.transcripts.append(transcript)
        self.transcripts_count += 1
    
    def add_message(self, role: str, content: str, metadata: Optional[dict] = None):
        """Add message to conversation"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        self.messages.append(message)
        
        if role == "assistant":
            self.ai_responses_count += 1
            self.turn_count += 1
    
    def get_duration(self) -> float:
        """Get call duration in seconds"""
        end_time = self.ended_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    def get_talk_duration(self) -> float:
        """Get actual talk time duration"""
        if not self.connected_at:
            return 0.0
        end_time = self.ended_at or datetime.now(timezone.utc)
        return (end_time - self.connected_at).total_seconds()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary"""
        return {
            "session_id": str(self.session_id),
            "call_id": self.call_id,
            "from_number": self.from_number,
            "to_number": self.to_number,
            "state": self.state.value,
            "started_at": self.started_at.isoformat(),
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.get_duration(),
            "talk_duration_seconds": self.get_talk_duration(),
            "turn_count": self.turn_count,
            "transcripts_count": self.transcripts_count,
            "ai_responses_count": self.ai_responses_count,
            "audio_frames_received": self.audio_frames_received,
            "audio_frames_sent": self.audio_frames_sent,
            "errors_count": self.errors_count,
            "current_intent": self.current_intent,
            "should_escalate": self.should_escalate,
            "has_error": self.has_error,
            "error_message": self.error_message,
        }


class CallSessionManager:
    """
    Manages all active call sessions with cleanup and monitoring.
    Thread-safe singleton pattern.
    """
    
    _instance: Optional["CallSessionManager"] = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.sessions: dict[str, CallSession] = {}  # session_id → CallSession
        self.call_id_to_session: dict[str, str] = {}  # call_id → session_id
        
        self.total_calls = 0
        self.completed_calls = 0
        self.failed_calls = 0
        
        self._initialized = True
        logger.info("📋 CallSessionManager initialized")
    
    async def create_session(
        self,
        call_id: str,
        from_number: str,
        to_number: str,
    ) -> CallSession:
        """
        Create new call session.
        
        Args:
            call_id: RingCentral call ID
            from_number: Caller phone number
            to_number: Callee phone number
            
        Returns:
            New CallSession instance
        """
        async with self._lock:
            session = CallSession(
                call_id=call_id,
                from_number=from_number,
                to_number=to_number,
            )
            
            self.sessions[str(session.session_id)] = session
            self.call_id_to_session[call_id] = str(session.session_id)
            self.total_calls += 1
            
            # Record call start metrics
            VoiceMetrics.record_call_start()
            
            logger.info(
                f"🆕 Created session {session.session_id} | "
                f"call={call_id} | from={from_number} | to={to_number}"
            )
            
            return session
    
    async def get_session(self, session_id: str) -> Optional[CallSession]:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    async def get_session_by_call_id(self, call_id: str) -> Optional[CallSession]:
        """Get session by RingCentral call ID"""
        session_id = self.call_id_to_session.get(call_id)
        if session_id:
            return self.sessions.get(session_id)
        return None
    
    async def end_session(self, session_id: str):
        """
        End call session and cleanup resources.
        
        Args:
            session_id: Session ID to end
        """
        async with self._lock:
            session = self.sessions.get(session_id)
            if not session:
                logger.warning(f"Session {session_id} not found")
                return
            
            # Mark as ended
            if session.has_error:
                self.failed_calls += 1
            else:
                self.completed_calls += 1
            
            session.mark_ended()
            
            # Cleanup components
            if session.stt_bridge:
                try:
                    session.stt_bridge.stop()
                except Exception as e:
                    logger.error(f"Error stopping STT bridge: {e}")
            
            if session.websocket:
                try:
                    await session.websocket.close()
                except Exception as e:
                    logger.error(f"Error closing WebSocket: {e}")
            
            # Log final stats
            logger.info(
                f"📊 Session {session_id} ended | "
                f"duration={session.get_duration():.1f}s | "
                f"turns={session.turn_count} | "
                f"transcripts={session.transcripts_count} | "
                f"frames_rx={session.audio_frames_received} | "
                f"frames_tx={session.audio_frames_sent}"
            )
            
            # Remove from call_id mapping
            if session.call_id in self.call_id_to_session:
                del self.call_id_to_session[session.call_id]
            
            # Keep session in memory for history (could move to DB)
            # del self.sessions[session_id]  # Uncomment to free memory immediately
    
    async def cleanup_stale_sessions(self, max_age_seconds: int = 3600):
        """
        Cleanup stale sessions older than max_age.
        
        Args:
            max_age_seconds: Maximum session age in seconds
        """
        async with self._lock:
            now = datetime.now(timezone.utc)
            stale_sessions = []
            
            for session_id, session in self.sessions.items():
                age = (now - session.started_at).total_seconds()
                if age > max_age_seconds and session.is_active:
                    stale_sessions.append(session_id)
            
            for session_id in stale_sessions:
                logger.warning(f"Cleaning up stale session: {session_id}")
                await self.end_session(session_id)
    
    def get_active_sessions(self) -> list[CallSession]:
        """Get all active sessions"""
        return [s for s in self.sessions.values() if s.is_active]
    
    @property
    def active_sessions(self) -> dict[str, CallSession]:
        """Get dictionary of active sessions by session_id"""
        return {sid: s for sid, s in self.sessions.items() if s.is_active}
    
    async def cleanup_all_sessions(self):
        """
        Cleanup all sessions (used during shutdown).
        Gracefully ends all active sessions.
        """
        async with self._lock:
            session_ids = list(self.sessions.keys())
            
            for session_id in session_ids:
                session = self.sessions.get(session_id)
                if session and session.is_active:
                    try:
                        await self.end_session(session_id)
                    except Exception as e:
                        logger.error(f"Error ending session {session_id}: {e}")
            
            logger.info(f"✅ Cleaned up {len(session_ids)} sessions")
    
    def get_stats(self) -> dict[str, Any]:
        """Get manager statistics"""
        active_sessions = self.get_active_sessions()
        
        return {
            "total_calls": self.total_calls,
            "completed_calls": self.completed_calls,
            "failed_calls": self.failed_calls,
            "active_sessions": len(active_sessions),
            "total_sessions_in_memory": len(self.sessions),
            "success_rate": self.completed_calls / self.total_calls if self.total_calls > 0 else 0,
        }


# Global singleton instance
call_session_manager = CallSessionManager()
