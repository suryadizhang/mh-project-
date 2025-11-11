"""
Speech Processing Service
Uses Deepgram for both speech-to-text AND text-to-speech
Single provider for complete voice AI solution.
"""

import asyncio
from datetime import datetime, timezone
from enum import Enum
import json
import logging
import os
from typing import Any, AsyncGenerator, Optional
import aiohttp

logger = logging.getLogger(__name__)

try:
    from deepgram import DeepgramClient
    from deepgram.options.live import LiveOptions, LiveTranscriptionEvents
    from deepgram.options.prerecorded import PrerecordedOptions
    DEEPGRAM_AVAILABLE = True
except ImportError:
    DEEPGRAM_AVAILABLE = False
    logger.warning("Deepgram SDK not installed. Voice AI features will be disabled.")


class SpeechProvider(str, Enum):
    """Speech service providers"""

    DEEPGRAM = "deepgram"
    AWS_TRANSCRIBE = "aws_transcribe"
    AWS_POLLY = "aws_polly"


class TranscriptionQuality(str, Enum):
    """Transcription quality levels"""

    NOVA_2 = "nova-2"  # Best quality, highest cost
    NOVA = "nova"  # Good quality, medium cost
    ENHANCED = "enhanced"  # Base quality, lowest cost


class VoiceModel(str, Enum):
    """Available Deepgram TTS voice models"""

    AURA_ASTERIA_EN = "aura-asteria-en"  # Natural female voice
    AURA_LUNA_EN = "aura-luna-en"  # Natural female voice
    AURA_STELLA_EN = "aura-stella-en"  # Natural female voice
    AURA_ATHENA_EN = "aura-athena-en"  # Natural female voice
    AURA_HERA_EN = "aura-hera-en"  # Natural female voice
    AURA_ORION_EN = "aura-orion-en"  # Natural male voice
    AURA_ARCAS_EN = "aura-arcas-en"  # Natural male voice
    AURA_PERSEUS_EN = "aura-perseus-en"  # Natural male voice
    AURA_ANGUS_EN = "aura-angus-en"  # Natural male voice
    AURA_ORPHEUS_EN = "aura-orpheus-en"  # Natural male voice


class SpeechService:
    """
    Unified speech processing service with Deepgram (STT + TTS).

    Features:
    - Real-time speech-to-text (streaming)
    - Batch transcription (pre-recorded audio)
    - Text-to-speech synthesis (Deepgram Aura)
    - Latency optimization
    - Cost tracking
    """

    def __init__(self):
        # Deepgram configuration (handles both STT and TTS)
        self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        self.deepgram_enabled = bool(self.deepgram_api_key)

        # Voice AI settings
        self.enable_voice_ai = os.getenv("ENABLE_VOICE_AI", "false").lower() == "true"
        self.default_voice_model = os.getenv(
            "DEEPGRAM_TTS_MODEL", VoiceModel.AURA_ASTERIA_EN.value
        )

        # Quality settings
        self.transcription_model = os.getenv(
            "DEEPGRAM_MODEL", TranscriptionQuality.NOVA_2.value
        )

        # Initialize Deepgram client
        self.deepgram_client = None

        if self.deepgram_enabled:
            self.deepgram_client = DeepgramClient(api_key=self.deepgram_api_key)
            logger.info("✅ Deepgram client initialized (STT + TTS)")

        # Cost tracking (Deepgram pricing)
        self.transcription_cost_per_minute = 0.0125  # Deepgram Nova-2 STT
        self.tts_cost_per_1000_chars = 0.015  # Deepgram Aura TTS

        logger.info(
            f"Speech service initialized (voice_ai={self.enable_voice_ai}, "
            f"deepgram={self.deepgram_enabled})"
        )

    async def transcribe_audio_stream(
        self,
        audio_stream: AsyncGenerator[bytes, None],
        callback: callable,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Real-time speech-to-text streaming.

        Args:
            audio_stream: Async generator yielding audio chunks
            callback: Function called with each transcript segment
            language: Language code (en, es, fr, etc.)

        Returns:
            Dict with transcription metadata and statistics
        """
        if not self.deepgram_enabled:
            raise RuntimeError("Deepgram not configured. Set DEEPGRAM_API_KEY")

        try:
            # Configure live transcription
            options = LiveOptions(
                model=self.transcription_model,
                language=language,
                punctuate=True,
                interim_results=True,
                utterance_end_ms=1000,  # 1 second pause = end of utterance
                vad_events=True,  # Voice activity detection
                smart_format=True,  # Automatic formatting
            )

            # Create connection
            connection = self.deepgram_client.listen.live.v("1")

            # Track statistics
            stats = {
                "start_time": datetime.now(timezone.utc),
                "segments": 0,
                "characters": 0,
                "words": 0,
                "confidence_scores": [],
            }

            # Event handlers
            def on_message(self, result, **kwargs):
                """Handle transcription results"""
                sentence = result.channel.alternatives[0].transcript

                if len(sentence) == 0:
                    return

                # Update statistics
                stats["segments"] += 1
                stats["characters"] += len(sentence)
                stats["words"] += len(sentence.split())
                stats["confidence_scores"].append(result.channel.alternatives[0].confidence)

                # Call user callback
                is_final = result.is_final
                callback(
                    {
                        "text": sentence,
                        "is_final": is_final,
                        "confidence": result.channel.alternatives[0].confidence,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )

            def on_error(self, error, **kwargs):
                """Handle errors"""
                logger.error(f"Deepgram error: {error}")

            # Register event handlers
            connection.on(LiveTranscriptionEvents.Transcript, on_message)
            connection.on(LiveTranscriptionEvents.Error, on_error)

            # Start connection
            if connection.start(options) is False:
                raise RuntimeError("Failed to start Deepgram connection")

            # Stream audio
            async for audio_chunk in audio_stream:
                connection.send(audio_chunk)

            # Finish
            connection.finish()

            # Calculate statistics
            stats["end_time"] = datetime.now(timezone.utc)
            duration = (stats["end_time"] - stats["start_time"]).total_seconds()
            stats["duration_seconds"] = duration
            stats["duration_minutes"] = duration / 60
            stats["cost_usd"] = stats["duration_minutes"] * self.transcription_cost_per_minute
            stats["avg_confidence"] = (
                sum(stats["confidence_scores"]) / len(stats["confidence_scores"])
                if stats["confidence_scores"]
                else 0
            )

            logger.info(
                f"Transcription complete: {stats['duration_minutes']:.2f} min, "
                f"{stats['words']} words, ${stats['cost_usd']:.4f}"
            )

            return stats

        except Exception as e:
            logger.exception(f"Transcription error: {e}")
            raise

    async def transcribe_audio_file(
        self, audio_data: bytes, language: str = "en"
    ) -> dict[str, Any]:
        """
        Transcribe pre-recorded audio file.

        Args:
            audio_data: Audio file bytes (WAV, MP3, etc.)
            language: Language code

        Returns:
            Dict with transcription and metadata
        """
        if not self.deepgram_enabled:
            raise RuntimeError("Deepgram not configured. Set DEEPGRAM_API_KEY")

        try:
            options = PrerecordedOptions(
                model=self.transcription_model,
                language=language,
                punctuate=True,
                smart_format=True,
                utterances=True,
                diarize=True,  # Speaker detection
            )

            # Send request
            response = await self.deepgram_client.listen.asyncrest.v("1").transcribe_file(
                {"buffer": audio_data}, options
            )

            # Extract transcription
            transcript = response.results.channels[0].alternatives[0].transcript
            confidence = response.results.channels[0].alternatives[0].confidence
            words = response.results.channels[0].alternatives[0].words

            # Calculate cost
            duration_seconds = response.metadata.duration
            duration_minutes = duration_seconds / 60
            cost = duration_minutes * self.transcription_cost_per_minute

            result = {
                "transcript": transcript,
                "confidence": confidence,
                "words": len(words),
                "duration_seconds": duration_seconds,
                "duration_minutes": duration_minutes,
                "cost_usd": cost,
                "language": language,
                "model": self.transcription_model,
            }

            logger.info(
                f"File transcribed: {duration_minutes:.2f} min, "
                f"{len(words)} words, ${cost:.4f}"
            )

            return result

        except Exception as e:
            logger.exception(f"File transcription error: {e}")
            raise

    async def synthesize_speech_stream(
        self,
        text: str,
        voice_model: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Convert text to speech with streaming (low latency) using Deepgram Aura.

        Args:
            text: Text to synthesize
            voice_model: Deepgram voice model (default: aura-asteria-en)

        Yields:
            Audio bytes chunks (streaming)
        """
        if not self.deepgram_enabled:
            raise RuntimeError("Deepgram not configured. Set DEEPGRAM_API_KEY")

        try:
            voice_model = voice_model or self.default_voice_model

            # Calculate cost
            char_count = len(text)
            cost = (char_count / 1000) * self.tts_cost_per_1000_chars

            logger.info(f"Synthesizing speech (streaming): {char_count} chars, ${cost:.4f}")

            # Stream audio chunks using Deepgram Aura
            audio_stream = self.deepgram_client.speak.v1.audio.generate(
                text=text,
                model=voice_model
            )

            for chunk in audio_stream:
                yield chunk

        except Exception as e:
            logger.exception(f"Speech synthesis streaming error: {e}")
            raise

    async def synthesize_speech(
        self,
        text: str,
        voice_model: Optional[str] = None,
    ) -> bytes:
        """
        Convert text to speech (full audio) using Deepgram Aura.

        Args:
            text: Text to synthesize
            voice_model: Deepgram voice model (default: aura-asteria-en)

        Returns:
            Complete audio bytes (MP3 format)
        """
        if not self.deepgram_enabled:
            raise RuntimeError("Deepgram not configured. Set DEEPGRAM_API_KEY")

        try:
            voice_model = voice_model or self.default_voice_model

            # Calculate cost
            char_count = len(text)
            cost = (char_count / 1000) * self.tts_cost_per_1000_chars

            logger.info(f"Synthesizing speech (full): {char_count} chars, ${cost:.4f}")

            # Generate full audio using Deepgram Aura
            audio_stream = self.deepgram_client.speak.v1.audio.generate(
                text=text,
                model=voice_model
            )

            # Collect all chunks
            audio_bytes = b""
            for chunk in audio_stream:
                audio_bytes += chunk

            return audio_bytes

        except Exception as e:
            logger.exception(f"Speech synthesis error: {e}")
            raise

    async def get_available_voices(self) -> list[dict[str, Any]]:
        """
        Get list of available Deepgram Aura voices.

        Returns:
            List of voice info dicts
        """
        if not self.deepgram_enabled:
            raise RuntimeError("Deepgram not configured")

        try:
            # Return Deepgram Aura voice models
            voice_list = [
                {
                    "voice_model": VoiceModel.AURA_ASTERIA_EN.value,
                    "name": "Asteria",
                    "gender": "female",
                    "language": "English",
                    "description": "Natural female voice"
                },
                {
                    "voice_model": VoiceModel.AURA_LUNA_EN.value,
                    "name": "Luna",
                    "gender": "female",
                    "language": "English",
                    "description": "Natural female voice"
                },
                {
                    "voice_model": VoiceModel.AURA_STELLA_EN.value,
                    "name": "Stella",
                    "gender": "female",
                    "language": "English",
                    "description": "Natural female voice"
                },
                {
                    "voice_model": VoiceModel.AURA_ATHENA_EN.value,
                    "name": "Athena",
                    "gender": "female",
                    "language": "English",
                    "description": "Natural female voice"
                },
                {
                    "voice_model": VoiceModel.AURA_HERA_EN.value,
                    "name": "Hera",
                    "gender": "female",
                    "language": "English",
                    "description": "Natural female voice"
                },
                {
                    "voice_model": VoiceModel.AURA_ORION_EN.value,
                    "name": "Orion",
                    "gender": "male",
                    "language": "English",
                    "description": "Natural male voice"
                },
                {
                    "voice_model": VoiceModel.AURA_ARCAS_EN.value,
                    "name": "Arcas",
                    "gender": "male",
                    "language": "English",
                    "description": "Natural male voice"
                },
                {
                    "voice_model": VoiceModel.AURA_PERSEUS_EN.value,
                    "name": "Perseus",
                    "gender": "male",
                    "language": "English",
                    "description": "Natural male voice"
                },
                {
                    "voice_model": VoiceModel.AURA_ANGUS_EN.value,
                    "name": "Angus",
                    "gender": "male",
                    "language": "English",
                    "description": "Natural male voice"
                },
                {
                    "voice_model": VoiceModel.AURA_ORPHEUS_EN.value,
                    "name": "Orpheus",
                    "gender": "male",
                    "language": "English",
                    "description": "Natural male voice"
                }
            ]

            logger.info(f"Retrieved {len(voice_list)} Deepgram Aura voices")
            return voice_list

        except Exception as e:
            logger.exception(f"Error fetching voices: {e}")
            raise

    def calculate_transcription_cost(self, duration_minutes: float) -> float:
        """Calculate transcription cost"""
        return duration_minutes * self.transcription_cost_per_minute

    def calculate_tts_cost(self, character_count: int) -> float:
        """Calculate text-to-speech cost"""
        return (character_count / 1000) * self.tts_cost_per_1000_chars

    async def health_check(self) -> dict[str, Any]:
        """
        Check service health and connectivity.

        Returns:
            Health status dict
        """
        health = {
            "service": "speech",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "deepgram": {
                "enabled": self.deepgram_enabled,
                "stt_model": self.transcription_model,
                "tts_model": self.default_voice_model,
                "stt_cost_per_minute": self.transcription_cost_per_minute,
                "tts_cost_per_1000_chars": self.tts_cost_per_1000_chars,
            },
            "voice_ai_enabled": self.enable_voice_ai,
        }

        # Test Deepgram connectivity (STT + TTS)
        if self.deepgram_enabled:
            try:
                # Quick test: transcribe silent audio
                test_audio = b"\x00" * 16000  # 1 second of silence at 16kHz
                await self.transcribe_audio_file(test_audio)
                health["deepgram"]["stt_status"] = "healthy"
            except Exception as e:
                health["deepgram"]["stt_status"] = "error"
                health["deepgram"]["stt_error"] = str(e)

            try:
                # Quick test: get voices
                await self.get_available_voices()
                health["deepgram"]["tts_status"] = "healthy"
            except Exception as e:
                health["deepgram"]["tts_status"] = "error"
                health["deepgram"]["tts_error"] = str(e)

        return health


# Global speech service instance
speech_service = SpeechService()
