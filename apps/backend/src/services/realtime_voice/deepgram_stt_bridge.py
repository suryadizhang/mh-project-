"""
Deepgram Live STT Bridge
Async->Thread bridge for Deepgram v5 WebSocket STT with production-grade error handling.
"""

import asyncio
import logging
import queue
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from dataclasses import dataclass

from .metrics import VoiceMetrics

logger = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    """Transcript result from Deepgram"""
    text: str
    is_final: bool
    confidence: float
    timestamp: datetime
    speech_final: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "is_final": self.is_final,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
            "speech_final": self.speech_final,
        }


class DeepgramSTTBridge:
    """
    Production-grade bridge between asyncio (RingCentral) and Deepgram v5 sync WebSocket.
    
    Architecture:
    - Main asyncio loop handles RingCentral WebSocket
    - Background thread runs Deepgram v5 listen.v1.connect() context
    - Thread-safe queue for audio frames (asyncio → thread)
    - Callback queue for transcripts (thread → asyncio)
    
    Features:
    - Graceful shutdown
    - Error recovery
    - Backpressure handling
    - Connection monitoring
    """
    
    def __init__(
        self,
        deepgram_client,
        callback: Callable[[TranscriptResult], None],
        model: str = "nova-2",
        language: str = "en",
        sample_rate: int = 16000,
        max_queue_size: int = 100,
    ):
        """
        Initialize STT bridge.
        
        Args:
            deepgram_client: DeepgramClient instance
            callback: Async callback for transcript results
            model: Deepgram model (nova-2, nova, enhanced)
            language: Language code (en, es, etc.)
            sample_rate: Audio sample rate in Hz
            max_queue_size: Max audio frames in queue
        """
        self.deepgram_client = deepgram_client
        self.callback = callback
        self.model = model
        self.language = language
        self.sample_rate = sample_rate
        
        # Thread-safe queues
        self.audio_queue: queue.Queue[Optional[bytes]] = queue.Queue(maxsize=max_queue_size)
        self.transcript_queue: asyncio.Queue[TranscriptResult] = asyncio.Queue()
        
        # State management
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.connection = None
        
        # Metrics
        self.frames_processed = 0
        self.transcripts_received = 0
        self.errors_count = 0
        self.started_at: Optional[datetime] = None
        
        logger.info(
            f"🎙️ DeepgramSTTBridge initialized | "
            f"model={model} | lang={language} | rate={sample_rate}Hz"
        )
    
    def start(self, event_loop: asyncio.AbstractEventLoop):
        """
        Start the STT bridge.
        
        Args:
            event_loop: The asyncio event loop to use for callbacks
        """
        if self.is_running:
            logger.warning("STT bridge already running")
            return
        
        self.loop = event_loop
        self.is_running = True
        self.started_at = datetime.now(timezone.utc)
        
        # Start background thread
        self.thread = threading.Thread(
            target=self._run_deepgram_thread,
            name=f"Deepgram-STT-{id(self)}",
            daemon=True
        )
        self.thread.start()
        
        # Start transcript processor
        asyncio.run_coroutine_threadsafe(
            self._process_transcripts(),
            self.loop
        )
        
        logger.info("✅ STT bridge started")
    
    def stop(self):
        """Stop the STT bridge gracefully"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping STT bridge...")
        self.is_running = False
        
        # Send sentinel to stop thread
        try:
            self.audio_queue.put(None, timeout=1.0)
        except queue.Full:
            logger.warning("Audio queue full on stop, forcing shutdown")
        
        # Wait for thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
            if self.thread.is_alive():
                logger.warning("STT thread did not stop gracefully")
        
        # Log metrics
        duration = (datetime.now(timezone.utc) - self.started_at).total_seconds()
        logger.info(
            f"📊 STT bridge stopped | "
            f"duration={duration:.1f}s | "
            f"frames={self.frames_processed} | "
            f"transcripts={self.transcripts_received} | "
            f"errors={self.errors_count}"
        )
    
    async def send_audio(self, audio_bytes: bytes):
        """
        Send audio frame to Deepgram (async interface).
        
        Args:
            audio_bytes: PCM audio data (16-bit, 16kHz mono recommended)
        """
        if not self.is_running:
            raise RuntimeError("STT bridge not running")
        
        try:
            # Non-blocking put with timeout
            self.audio_queue.put_nowait(audio_bytes)
            self.frames_processed += 1
        except queue.Full:
            logger.warning("Audio queue full, dropping frame (backpressure)")
            # Don't block - drop frame to prevent latency buildup
    
    def _run_deepgram_thread(self):
        """
        Background thread: runs Deepgram WebSocket connection.
        This is where the sync Deepgram SDK lives.
        """
        try:
            logger.info("🔌 Connecting to Deepgram...")
            
            # Deepgram v5 sync WebSocket context manager
            with self.deepgram_client.listen.v1.connect(
                model=self.model,
                language=self.language,
                smart_format=True,
                interim_results=True,
                utterance_end_ms=1000,
                vad_events=True,
                encoding="linear16",
                sample_rate=self.sample_rate,
                channels=1,
            ) as connection:
                
                self.connection = connection
                logger.info("✅ Connected to Deepgram")
                
                # Start receiving thread
                recv_thread = threading.Thread(
                    target=self._receive_transcripts,
                    args=(connection,),
                    daemon=True
                )
                recv_thread.start()
                
                # Send audio loop
                while self.is_running:
                    try:
                        # Block with timeout to allow shutdown
                        audio_chunk = self.audio_queue.get(timeout=0.1)
                        
                        if audio_chunk is None:  # Sentinel value
                            logger.info("Received stop signal")
                            break
                        
                        # Send to Deepgram
                        connection.send(audio_chunk)
                        
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Error sending audio to Deepgram: {e}")
                        self.errors_count += 1
                        VoiceMetrics.record_stt_error("audio_send_error")
                
                logger.info("📤 Audio send loop stopped")
                
                # Wait for receive thread
                recv_thread.join(timeout=2.0)
        
        except Exception as e:
            logger.exception(f"Fatal error in Deepgram thread: {e}")
            self.errors_count += 1
            self.is_running = False
    
    def _receive_transcripts(self, connection):
        """
        Receive transcripts from Deepgram WebSocket.
        Runs in separate thread to not block audio sending.
        """
        try:
            logger.info("📥 Starting transcript receive loop")
            
            for message in connection:
                if not self.is_running:
                    break
                
                try:
                    # Parse Deepgram response
                    if hasattr(message, 'channel'):
                        # This is a transcript message
                        alternatives = message.channel.alternatives
                        if alternatives and len(alternatives) > 0:
                            alt = alternatives[0]
                            transcript_text = alt.transcript
                            
                            if transcript_text.strip():  # Only process non-empty
                                result = TranscriptResult(
                                    text=transcript_text,
                                    is_final=message.is_final,
                                    confidence=alt.confidence if hasattr(alt, 'confidence') else 0.0,
                                    timestamp=datetime.now(timezone.utc),
                                    speech_final=message.speech_final if hasattr(message, 'speech_final') else False,
                                )
                                
                                # Queue for async processing
                                self.transcript_queue.put_nowait(result)
                                self.transcripts_received += 1
                                
                                if result.is_final:
                                    logger.debug(f"📝 Final transcript: '{transcript_text}'")
                
                except Exception as e:
                    logger.error(f"Error processing transcript message: {e}")
                    self.errors_count += 1
                    VoiceMetrics.record_stt_error("transcript_parse_error")
        
        except Exception as e:
            logger.exception(f"Fatal error in transcript receive loop: {e}")
            self.errors_count += 1
            VoiceMetrics.record_stt_error("receive_loop_error")
    
    async def _process_transcripts(self):
        """
        Process transcripts from queue and invoke callback.
        Runs in asyncio event loop.
        """
        logger.info("🔄 Starting transcript processor")
        
        while self.is_running:
            try:
                # Get transcript with timeout
                result = await asyncio.wait_for(
                    self.transcript_queue.get(),
                    timeout=0.1
                )
                
                # Invoke user callback
                if asyncio.iscoroutinefunction(self.callback):
                    await self.callback(result)
                else:
                    self.callback(result)
            
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in transcript processor: {e}")
                self.errors_count += 1
        
        logger.info("🔄 Transcript processor stopped")
    
    def get_stats(self) -> dict[str, Any]:
        """Get bridge statistics"""
        uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds() if self.started_at else 0
        
        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "frames_processed": self.frames_processed,
            "transcripts_received": self.transcripts_received,
            "errors_count": self.errors_count,
            "audio_queue_size": self.audio_queue.qsize(),
            "transcript_queue_size": self.transcript_queue.qsize(),
            "frames_per_second": self.frames_processed / uptime if uptime > 0 else 0,
        }
