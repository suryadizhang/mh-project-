"""
Real-Time Voice AI Metrics
Prometheus metrics for voice call monitoring and performance tracking.
"""

import logging
import time
from contextlib import contextmanager
from typing import Optional

from prometheus_client import Counter, Gauge, Histogram

from core.metrics import registry

logger = logging.getLogger(__name__)

# Call metrics
voice_calls_total = Counter(
    "voice_calls_total",
    "Total voice calls handled",
    ["status"],  # status: completed, failed, timeout
    registry=registry,
)

voice_calls_active = Gauge(
    "voice_calls_active",
    "Number of active voice calls",
    [],
    registry=registry,
)

voice_call_duration_seconds = Histogram(
    "voice_call_duration_seconds",
    "Voice call duration in seconds",
    ["status"],
    registry=registry,
    buckets=(5, 10, 30, 60, 120, 300, 600, 1800, 3600),  # 5s to 1 hour
)

# Audio processing metrics
voice_audio_frames_received = Counter(
    "voice_audio_frames_received_total",
    "Total audio frames received from RingCentral",
    [],
    registry=registry,
)

voice_audio_frames_sent = Counter(
    "voice_audio_frames_sent_total",
    "Total audio frames sent to RingCentral",
    [],
    registry=registry,
)

voice_audio_processing_duration_seconds = Histogram(
    "voice_audio_processing_duration_seconds",
    "Audio processing latency",
    ["operation"],  # operation: resample, decode_mulaw, decode_alaw, silence_detect
    registry=registry,
    buckets=(0.001, 0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500),  # 1ms to 500ms
)

# STT metrics
voice_stt_transcripts_total = Counter(
    "voice_stt_transcripts_total",
    "Total STT transcripts received",
    ["is_final"],  # is_final: true, false
    registry=registry,
)

voice_stt_latency_seconds = Histogram(
    "voice_stt_latency_seconds",
    "STT processing latency (frame sent → transcript received)",
    [],
    registry=registry,
    buckets=(0.050, 0.100, 0.150, 0.200, 0.300, 0.500, 1.0, 2.0),  # 50ms to 2s
)

voice_stt_errors_total = Counter(
    "voice_stt_errors_total",
    "Total STT errors",
    ["error_type"],
    registry=registry,
)

voice_stt_confidence = Histogram(
    "voice_stt_confidence",
    "STT transcript confidence scores",
    [],
    registry=registry,
    buckets=(0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.98, 1.0),
)

# TTS metrics
voice_tts_requests_total = Counter(
    "voice_tts_requests_total",
    "Total TTS requests",
    ["status"],  # status: success, error
    registry=registry,
)

voice_tts_latency_seconds = Histogram(
    "voice_tts_latency_seconds",
    "TTS processing latency (text → audio)",
    [],
    registry=registry,
    buckets=(0.050, 0.100, 0.150, 0.200, 0.300, 0.500, 1.0, 2.0),  # 50ms to 2s
)

voice_tts_audio_size_bytes = Histogram(
    "voice_tts_audio_size_bytes",
    "TTS audio output size in bytes",
    [],
    registry=registry,
    buckets=(1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000),  # 1KB to 500KB
)

# AI Pipeline metrics
voice_ai_responses_total = Counter(
    "voice_ai_responses_total",
    "Total AI responses generated",
    ["intent"],  # intent: booking, inquiry, complaint, unknown
    registry=registry,
)

voice_ai_latency_seconds = Histogram(
    "voice_ai_latency_seconds",
    "AI pipeline latency (user message → AI response)",
    [],
    registry=registry,
    buckets=(0.100, 0.200, 0.300, 0.500, 1.0, 2.0, 3.0, 5.0),  # 100ms to 5s
)

voice_ai_escalations_total = Counter(
    "voice_ai_escalations_total",
    "Total escalations to human agents",
    ["reason"],  # reason: low_confidence, complaint, explicit_request, error
    registry=registry,
)

# Conversation metrics
voice_conversation_turns = Histogram(
    "voice_conversation_turns",
    "Number of conversation turns per call",
    [],
    registry=registry,
    buckets=(1, 2, 3, 5, 10, 15, 20, 30, 50),
)

voice_conversation_transcripts = Histogram(
    "voice_conversation_transcripts",
    "Number of transcripts per call",
    [],
    registry=registry,
    buckets=(1, 3, 5, 10, 20, 30, 50, 100),
)

# Error metrics
voice_errors_total = Counter(
    "voice_errors_total",
    "Total voice system errors",
    ["component", "error_type"],  # component: websocket, stt, tts, ai, audio
    registry=registry,
)

voice_websocket_disconnects_total = Counter(
    "voice_websocket_disconnects_total",
    "Total WebSocket disconnections",
    ["reason"],  # reason: normal, error, timeout
    registry=registry,
)

# Session metrics
voice_sessions_created_total = Counter(
    "voice_sessions_created_total",
    "Total call sessions created",
    [],
    registry=registry,
)

voice_sessions_ended_total = Counter(
    "voice_sessions_ended_total",
    "Total call sessions ended",
    ["final_state"],  # final_state: ended, failed
    registry=registry,
)


class VoiceMetrics:
    """Helper class for recording voice AI metrics"""
    
    @staticmethod
    def record_call_start():
        """Record a new call starting"""
        voice_calls_active.inc()
        voice_sessions_created_total.inc()
    
    @staticmethod
    def record_call_end(status: str, duration: float, turns: int, transcripts: int):
        """
        Record call completion
        
        Args:
            status: "completed", "failed", or "timeout"
            duration: Call duration in seconds
            turns: Number of conversation turns
            transcripts: Number of transcripts
        """
        voice_calls_active.dec()
        voice_calls_total.labels(status=status).inc()
        voice_call_duration_seconds.labels(status=status).observe(duration)
        voice_conversation_turns.observe(turns)
        voice_conversation_transcripts.observe(transcripts)
        voice_sessions_ended_total.labels(final_state=status).inc()
    
    @staticmethod
    def record_audio_frame_received():
        """Record audio frame received from RingCentral"""
        voice_audio_frames_received.inc()
    
    @staticmethod
    def record_audio_frame_sent():
        """Record audio frame sent to RingCentral"""
        voice_audio_frames_sent.inc()
    
    @staticmethod
    @contextmanager
    def track_audio_processing(operation: str):
        """
        Context manager to track audio processing time
        
        Usage:
            with VoiceMetrics.track_audio_processing("resample"):
                audio = processor.resample(data, 8000, 16000)
        """
        start = time.time()
        try:
            yield
        finally:
            duration = time.time() - start
            voice_audio_processing_duration_seconds.labels(operation=operation).observe(duration)
    
    @staticmethod
    def record_transcript(is_final: bool, confidence: float, latency: Optional[float] = None):
        """
        Record STT transcript received
        
        Args:
            is_final: Whether transcript is final
            confidence: Transcript confidence (0.0-1.0)
            latency: Optional STT latency in seconds
        """
        voice_stt_transcripts_total.labels(is_final=str(is_final).lower()).inc()
        voice_stt_confidence.observe(confidence)
        
        if latency is not None:
            voice_stt_latency_seconds.observe(latency)
    
    @staticmethod
    def record_stt_error(error_type: str):
        """Record STT error"""
        voice_stt_errors_total.labels(error_type=error_type).inc()
    
    @staticmethod
    def record_tts_request(status: str, latency: float, audio_size: int):
        """
        Record TTS request
        
        Args:
            status: "success" or "error"
            latency: TTS latency in seconds
            audio_size: Audio output size in bytes
        """
        voice_tts_requests_total.labels(status=status).inc()
        voice_tts_latency_seconds.observe(latency)
        voice_tts_audio_size_bytes.observe(audio_size)
    
    @staticmethod
    def record_ai_response(intent: str, latency: float):
        """
        Record AI response generated
        
        Args:
            intent: Detected intent
            latency: AI pipeline latency in seconds
        """
        voice_ai_responses_total.labels(intent=intent).inc()
        voice_ai_latency_seconds.observe(latency)
    
    @staticmethod
    def record_escalation(reason: str):
        """
        Record escalation to human agent
        
        Args:
            reason: Escalation reason (low_confidence, complaint, explicit_request, error)
        """
        voice_ai_escalations_total.labels(reason=reason).inc()
    
    @staticmethod
    def record_error(component: str, error_type: str):
        """
        Record system error
        
        Args:
            component: Component where error occurred (websocket, stt, tts, ai, audio)
            error_type: Type of error
        """
        voice_errors_total.labels(component=component, error_type=error_type).inc()
    
    @staticmethod
    def record_websocket_disconnect(reason: str):
        """
        Record WebSocket disconnection
        
        Args:
            reason: Disconnect reason (normal, error, timeout)
        """
        voice_websocket_disconnects_total.labels(reason=reason).inc()


# Export for convenience
__all__ = ["VoiceMetrics"]
