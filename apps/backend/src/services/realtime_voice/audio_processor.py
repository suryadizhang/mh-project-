"""
Audio Processing Pipeline
Handles PCM conversion, resampling, buffering, and audio format transformations.
"""

import logging
import struct
import numpy as np
from typing import Optional
from dataclasses import dataclass

from .metrics import VoiceMetrics

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Audio configuration"""
    sample_rate: int = 16000  # Deepgram requires 16kHz
    channels: int = 1  # Mono
    sample_width: int = 2  # 16-bit
    frame_size_ms: int = 20  # 20ms frames (standard for VoIP)
    
    @property
    def frame_size_bytes(self) -> int:
        """Calculate frame size in bytes"""
        return int(self.sample_rate * self.sample_width * self.channels * self.frame_size_ms / 1000)
    
    @property
    def samples_per_frame(self) -> int:
        """Samples per frame"""
        return int(self.sample_rate * self.frame_size_ms / 1000)


class AudioProcessor:
    """
    Production-grade audio processor for real-time voice streaming.
    
    Features:
    - Resampling (8kHz → 16kHz, or any rate → 16kHz)
    - Channel conversion (stereo → mono)
    - Buffering and frame alignment
    - Format conversion (mulaw, alaw → linear PCM)
    - Silence detection
    """
    
    def __init__(
        self,
        target_config: Optional[AudioConfig] = None,
        enable_silence_detection: bool = True,
        silence_threshold: int = 500,  # Amplitude threshold for silence
    ):
        """
        Initialize audio processor.
        
        Args:
            target_config: Target audio configuration (default: 16kHz mono 16-bit)
            enable_silence_detection: Enable silence detection
            silence_threshold: RMS threshold below which audio is considered silence
        """
        self.target_config = target_config or AudioConfig()
        self.enable_silence_detection = enable_silence_detection
        self.silence_threshold = silence_threshold
        
        # Buffer for incomplete frames
        self.buffer = b""
        
        # Metrics
        self.frames_processed = 0
        self.bytes_processed = 0
        self.silent_frames = 0
        
        logger.info(
            f"🎵 AudioProcessor initialized | "
            f"rate={self.target_config.sample_rate}Hz | "
            f"channels={self.target_config.channels} | "
            f"width={self.target_config.sample_width*8}bit"
        )
    
    def resample(
        self,
        audio_data: bytes,
        source_rate: int,
        source_width: int = 2,
        source_channels: int = 1,
    ) -> bytes:
        """
        Resample audio to target configuration using numpy.
        
        Args:
            audio_data: Source audio data
            source_rate: Source sample rate
            source_width: Source sample width (bytes)
            source_channels: Source channels
            
        Returns:
            Resampled audio data
        """
        # Convert bytes to numpy array
        if source_width == 1:
            dtype = np.int8
        elif source_width == 2:
            dtype = np.int16
        else:
            dtype = np.int32
        
        samples = np.frombuffer(audio_data, dtype=dtype)
        
        # Convert stereo → mono if needed
        if source_channels == 2 and self.target_config.channels == 1:
            samples = samples.reshape(-1, 2).mean(axis=1).astype(dtype)
            logger.debug("Converted stereo → mono")
        
        # Resample if rates differ
        if source_rate != self.target_config.sample_rate:
            # Simple linear interpolation resampling
            duration = len(samples) / source_rate
            target_length = int(duration * self.target_config.sample_rate)
            indices = np.linspace(0, len(samples) - 1, target_length)
            samples = np.interp(indices, np.arange(len(samples)), samples).astype(dtype)
            logger.debug(f"Resampled {source_rate}Hz → {self.target_config.sample_rate}Hz")
        
        # Convert to target width if needed
        if source_width != self.target_config.sample_width:
            if self.target_config.sample_width == 2:
                samples = samples.astype(np.int16)
            elif self.target_config.sample_width == 1:
                samples = samples.astype(np.int8)
        
        return samples.tobytes()
    
    def decode_mulaw(self, mulaw_data: bytes) -> bytes:
        """
        Decode μ-law encoded audio to linear PCM using numpy.
        
        Args:
            mulaw_data: μ-law encoded audio
            
        Returns:
            Linear PCM audio (16-bit)
        """
        # μ-law decompression table
        mulaw_array = np.frombuffer(mulaw_data, dtype=np.uint8)
        
        # μ-law decode algorithm
        mulaw_array = ~mulaw_array
        sign = (mulaw_array & 0x80) >> 7
        exponent = (mulaw_array & 0x70) >> 4
        mantissa = mulaw_array & 0x0F
        
        sample = ((mantissa << 3) + 0x84) << exponent
        sample = np.where(sign == 0, sample, -sample)
        
        return sample.astype(np.int16).tobytes()
    
    def decode_alaw(self, alaw_data: bytes) -> bytes:
        """
        Decode A-law encoded audio to linear PCM using numpy.
        
        Args:
            alaw_data: A-law encoded audio
            
        Returns:
            Linear PCM audio (16-bit)
        """
        # A-law decompression
        alaw_array = np.frombuffer(alaw_data, dtype=np.uint8)
        
        # A-law decode algorithm
        alaw_array = alaw_array ^ 0x55
        sign = (alaw_array & 0x80) >> 7
        exponent = (alaw_array & 0x70) >> 4
        mantissa = alaw_array & 0x0F
        
        # Fixed: use np.where for numpy array conditional
        sample = ((mantissa << 4) + 8) << np.where(exponent > 0, exponent, 1)
        sample = np.where(sign == 0, sample, -sample)
        
        return sample.astype(np.int16).tobytes()
    
    def is_silence(self, audio_data: bytes) -> bool:
        """
        Detect if audio frame is silence using RMS calculation.
        
        Args:
            audio_data: Audio data to check
            
        Returns:
            True if silence detected
        """
        if not self.enable_silence_detection:
            return False
        
        try:
            # Convert to numpy and calculate RMS
            if self.target_config.sample_width == 2:
                samples = np.frombuffer(audio_data, dtype=np.int16)
            else:
                samples = np.frombuffer(audio_data, dtype=np.int8)
            
            rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))
            return rms < self.silence_threshold
        except Exception as e:
            logger.warning(f"Error detecting silence: {e}")
            return False
    
    def process_frame(
        self,
        audio_data: bytes,
        source_rate: int = 8000,
        source_encoding: str = "linear16",
    ) -> list[bytes]:
        """
        Process incoming audio frame.
        
        Args:
            audio_data: Raw audio data
            source_rate: Source sample rate
            source_encoding: Source encoding (linear16, mulaw, alaw)
            
        Returns:
            List of processed frames ready for Deepgram (may be empty or multiple)
        """
        try:
            # Track audio processing time
            with VoiceMetrics.track_audio_processing():
                # Decode if needed
                if source_encoding == "mulaw":
                    audio_data = self.decode_mulaw(audio_data)
                elif source_encoding == "alaw":
                    audio_data = self.decode_alaw(audio_data)
                
                # Resample to target rate
                if source_rate != self.target_config.sample_rate:
                    audio_data = self.resample(audio_data, source_rate)
                
                # Add to buffer
                self.buffer += audio_data
                
                # Extract complete frames
                frames = []
                frame_size = self.target_config.frame_size_bytes
                
                while len(self.buffer) >= frame_size:
                    frame = self.buffer[:frame_size]
                    self.buffer = self.buffer[frame_size:]
                    
                    # Check silence
                    is_silent = self.is_silence(frame)
                    if is_silent:
                        self.silent_frames += 1
                        # Still send silent frames (VAD will handle)
                    
                    frames.append(frame)
                    self.frames_processed += 1
                
                self.bytes_processed += len(audio_data)
                
                return frames
        
        except Exception as e:
            logger.error(f"Error processing audio frame: {e}")
            return []
    
    def flush(self) -> Optional[bytes]:
        """
        Flush remaining buffered audio.
        
        Returns:
            Buffered audio or None
        """
        if self.buffer:
            frame = self.buffer
            self.buffer = b""
            return frame
        return None
    
    def reset(self):
        """Reset processor state"""
        self.buffer = b""
        self.frames_processed = 0
        self.bytes_processed = 0
        self.silent_frames = 0
        logger.debug("Audio processor reset")
    
    def get_stats(self) -> dict:
        """Get processor statistics"""
        return {
            "frames_processed": self.frames_processed,
            "bytes_processed": self.bytes_processed,
            "silent_frames": self.silent_frames,
            "silence_ratio": self.silent_frames / self.frames_processed if self.frames_processed > 0 else 0,
            "buffer_size": len(self.buffer),
        }
