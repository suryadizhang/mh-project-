"""
Comprehensive Voice AI Test Suite
Tests for speech service, voice service, and voice assistant
"""

import asyncio
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Import services
from services.speech_service import SpeechService
from services.ringcentral_voice_service import RingCentralVoiceService, CallDirection
from api.ai.voice_assistant import VoiceAssistant
from models.call_recording import CallRecording, CallState


@pytest.fixture
def mock_deepgram():
    """Mock Deepgram client"""
    with patch("services.speech_service.DeepgramClient") as mock:
        client = MagicMock()
        mock.return_value = client
        
        # Mock transcription response
        async def mock_transcribe(*args, **kwargs):
            return {
                "results": {
                    "channels": [
                        {
                            "alternatives": [
                                {
                                    "transcript": "Hello, I'd like to book a party for 10 people",
                                    "confidence": 0.95,
                                    "words": [
                                        {"word": "Hello", "start": 0.0, "end": 0.5},
                                        {"word": "I'd", "start": 0.6, "end": 0.8},
                                        {"word": "like", "start": 0.9, "end": 1.1},
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        
        client.transcription.prerecorded = AsyncMock(side_effect=mock_transcribe)
        yield client


@pytest.fixture
def mock_deepgram_tts():
    """Mock Deepgram TTS"""
    with patch("services.speech_service.DeepgramClient") as mock:
        client = MagicMock()
        
        # Mock TTS response
        def mock_tts(*args, **kwargs):
            # Return audio chunks
            return [b"fake_audio_chunk" for _ in range(3)]
        
        client.speak.v1.audio.generate = MagicMock(return_value=mock_tts())
        
        yield client


@pytest.fixture
def speech_service(mock_deepgram):
    """Speech service with mocked dependencies"""
    service = SpeechService()
    service.deepgram_enabled = True
    return service


@pytest.fixture
def voice_service():
    """Voice service instance"""
    return RingCentralVoiceService()


@pytest.fixture
async def voice_assistant():
    """Voice assistant instance"""
    assistant = VoiceAssistant()
    # Mock orchestrator
    assistant.orchestrator = MagicMock()
    assistant.orchestrator.chat = AsyncMock(return_value={
        "response": "Great! I can help you book a party for 10 people. What date were you thinking?",
        "intent": "booking_inquiry",
        "confidence": 0.95
    })
    return assistant


@pytest.fixture
async def db_session():
    """Mock database session"""
    session = AsyncMock(spec=AsyncSession)
    
    # Mock query results
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_result.scalars.return_value.all.return_value = []
    
    session.execute.return_value = mock_result
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    
    return session


class TestSpeechService:
    """Tests for SpeechService"""
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_file(self, speech_service):
        """Test audio file transcription"""
        # Fake audio data
        audio_bytes = b"fake_audio_wav_data"
        
        result = await speech_service.transcribe_audio_file(audio_bytes)
        
        assert result is not None
        assert "transcript" in result
        assert result["transcript"] == "Hello, I'd like to book a party for 10 people"
        assert result["confidence"] > 0.9
        assert "words" in result
    
    @pytest.mark.asyncio
    async def test_synthesize_speech(self, speech_service):
        """Test text-to-speech synthesis"""
        text = "Welcome to MyHibachi! How can I help you today?"
        
        audio_bytes = await speech_service.synthesize_speech(text)
        
        assert audio_bytes is not None
        assert len(audio_bytes) > 0
    
    @pytest.mark.asyncio
    async def test_synthesize_speech_stream(self, speech_service):
        """Test streaming text-to-speech"""
        text = "This is a streaming test"
        
        chunks = []
        async for chunk in speech_service.synthesize_speech_stream(text):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, bytes) for chunk in chunks)
    
    @pytest.mark.asyncio
    async def test_get_available_voices(self, speech_service):
        """Test fetching available voices"""
        voices = await speech_service.get_available_voices()
        
        assert len(voices) > 0
        assert voices[0]["name"] == "Rachel"
        assert "voice_id" in voices[0]
    
    def test_cost_calculation(self, speech_service):
        """Test cost calculation methods"""
        # Transcription cost
        transcription_cost = speech_service.calculate_transcription_cost(5.0)
        assert transcription_cost == 5.0 * 0.0125  # $0.0625
        
        # TTS cost
        tts_cost = speech_service.calculate_tts_cost(1000)
        # Deepgram TTS: $0.015/1000 chars
        assert tts_cost == 1.0 * 0.015  # $0.015
    
    @pytest.mark.asyncio
    async def test_health_check(self, speech_service):
        """Test service health check"""
        health = await speech_service.health_check()
        
        assert "service" in health
        assert health["service"] == "speech"
        assert "deepgram" in health
        assert health["deepgram"]["enabled"] is True


class TestRingCentralVoiceService:
    """Tests for RingCentralVoiceService"""
    
    @pytest.mark.asyncio
    async def test_handle_inbound_call(self, voice_service, db_session):
        """Test inbound call handling"""
        call_data = {
            "id": "call_123",
            "from": {"phoneNumber": "+19167408768"},
            "to": {"phoneNumber": "+18005551234"},
            "status": "ringing"
        }
        
        result = await voice_service.handle_inbound_call(db_session, call_data)
        
        assert result["success"] is True
        assert result["action"] == "answer"
        assert "call_id" in result
        assert db_session.add.called
        assert db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_handle_call_status(self, voice_service, db_session):
        """Test call status update"""
        # Create mock call recording
        call_recording = CallRecording(
            id=uuid4(),
            rc_call_id="call_123",
            direction=CallDirection.INBOUND.value,
            from_number="+19167408768",
            to_number="+18005551234",
            status="ringing",
            state=CallState.INITIATED
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = call_recording
        db_session.execute.return_value = mock_result
        
        status_data = {
            "id": "call_123",
            "status": "Answered",
            "duration": 180
        }
        
        result = await voice_service.handle_call_status(db_session, status_data)
        
        assert result["success"] is True
        assert call_recording.status == "Answered"
        assert call_recording.state == CallState.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_transcribe_call_recording(self, voice_service, db_session):
        """Test call recording transcription"""
        recording_id = uuid4()
        
        # Mock call recording
        call_recording = CallRecording(
            id=recording_id,
            rc_call_id="call_123",
            direction=CallDirection.INBOUND.value,
            from_number="+19167408768",
            to_number="+18005551234",
            state=CallState.RECORDED
        )
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = call_recording
        db_session.execute.return_value = mock_result
        
        # Mock speech service
        with patch("services.ringcentral_voice_service.speech_service") as mock_speech:
            mock_speech.transcribe_audio_file = AsyncMock(return_value={
                "transcript": "This is a test transcript",
                "confidence": 0.95,
                "words": []
            })
            
            audio_bytes = b"fake_audio_data"
            result = await voice_service.transcribe_call_recording(
                db_session, recording_id, audio_bytes
            )
            
            assert result["success"] is True
            assert call_recording.transcript == "This is a test transcript"
            assert call_recording.state == CallState.TRANSCRIBED
    
    def test_get_active_calls(self, voice_service):
        """Test getting active calls"""
        # Add mock active call
        voice_service.active_calls["call_123"] = {
            "id": "call_123",
            "from": "+19167408768",
            "to": "+18005551234",
            "state": CallState.IN_PROGRESS,
            "started_at": datetime.now(timezone.utc)
        }
        
        active_calls = voice_service.get_active_calls()
        
        assert len(active_calls) == 1
        assert active_calls[0]["id"] == "call_123"
    
    @pytest.mark.asyncio
    async def test_get_call_analytics(self, voice_service, db_session):
        """Test call analytics"""
        # Mock recordings
        recordings = [
            MagicMock(duration_seconds=120, transcript="Test 1"),
            MagicMock(duration_seconds=180, transcript="Test 2"),
            MagicMock(duration_seconds=90, transcript=None)
        ]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = recordings
        db_session.execute.return_value = mock_result
        
        analytics = await voice_service.get_call_analytics(db_session)
        
        assert analytics["total_calls"] == 3
        assert analytics["total_duration_seconds"] == 390
        assert analytics["transcribed_calls"] == 2
        assert analytics["transcription_rate"] == pytest.approx(0.666, 0.01)


class TestVoiceAssistant:
    """Tests for VoiceAssistant"""
    
    @pytest.mark.asyncio
    async def test_handle_call_start(self, voice_assistant, db_session):
        """Test call start handling"""
        call_data = {
            "call_id": "call_123",
            "from_number": "+19167408768",
            "to_number": "+18005551234"
        }
        
        result = await voice_assistant.handle_call_start(db_session, call_data)
        
        assert result["success"] is True
        assert "greeting" in result
        assert "audio" in result
        assert isinstance(result["audio"], bytes)
    
    @pytest.mark.asyncio
    async def test_process_speech_input(self, voice_assistant, db_session):
        """Test processing speech input"""
        call_id = "call_123"
        audio_bytes = b"fake_audio_data"
        
        # Mock speech service
        with patch("api.ai.voice_assistant.speech_service") as mock_speech:
            mock_speech.transcribe_audio_file = AsyncMock(return_value={
                "transcript": "I want to book a party for 15 people",
                "confidence": 0.92
            })
            
            mock_speech.synthesize_speech = AsyncMock(
                return_value=b"fake_response_audio"
            )
            
            result = await voice_assistant.process_speech_input(
                db_session, call_id, audio_bytes
            )
            
            assert result["success"] is True
            assert "transcript" in result
            assert "response_text" in result
            assert "response_audio" in result
    
    @pytest.mark.asyncio
    async def test_handle_call_end(self, voice_assistant, db_session):
        """Test call end handling"""
        call_id = "call_123"
        
        result = await voice_assistant.handle_call_end(db_session, call_id)
        
        assert result["success"] is True
        assert "summary" in result
    
    @pytest.mark.asyncio
    async def test_get_call_summary(self, voice_assistant, db_session):
        """Test call summary generation"""
        call_id = "call_123"
        
        # Add conversation history
        voice_assistant.conversations[call_id] = {
            "call_id": call_id,
            "started_at": datetime.now(timezone.utc),
            "messages": [
                {
                    "role": "user",
                    "content": "I want to book a party",
                    "timestamp": datetime.now(timezone.utc)
                },
                {
                    "role": "assistant",
                    "content": "Great! How many people?",
                    "timestamp": datetime.now(timezone.utc)
                }
            ]
        }
        
        summary = await voice_assistant.get_call_summary(call_id)
        
        assert "call_id" in summary
        assert summary["message_count"] == 2
        assert "conversation" in summary


@pytest.mark.integration
class TestVoiceIntegration:
    """Integration tests for complete voice flow"""
    
    @pytest.mark.asyncio
    async def test_complete_call_flow(
        self, voice_service, voice_assistant, db_session
    ):
        """Test complete call flow from start to end"""
        # 1. Inbound call
        call_data = {
            "id": "call_integration_123",
            "from": {"phoneNumber": "+19167408768"},
            "to": {"phoneNumber": "+18005551234"}
        }
        
        call_result = await voice_service.handle_inbound_call(db_session, call_data)
        assert call_result["success"] is True
        
        # 2. Start voice assistant
        start_result = await voice_assistant.handle_call_start(db_session, call_data)
        assert start_result["success"] is True
        
        # 3. Process speech (mocked)
        with patch("api.ai.voice_assistant.speech_service") as mock_speech:
            mock_speech.transcribe_audio_file = AsyncMock(return_value={
                "transcript": "Book party for 10",
                "confidence": 0.9
            })
            mock_speech.synthesize_speech = AsyncMock(
                return_value=b"response_audio"
            )
            
            process_result = await voice_assistant.process_speech_input(
                db_session, call_data["id"], b"audio"
            )
            assert process_result["success"] is True
        
        # 4. End call
        end_result = await voice_assistant.handle_call_end(
            db_session, call_data["id"]
        )
        assert end_result["success"] is True


@pytest.mark.performance
class TestVoicePerformance:
    """Performance tests for voice AI"""
    
    @pytest.mark.asyncio
    async def test_concurrent_calls(self, voice_assistant, db_session):
        """Test handling multiple concurrent calls"""
        num_calls = 10
        
        async def simulate_call(call_id):
            call_data = {
                "call_id": call_id,
                "from_number": f"+1916740{call_id:04d}",
                "to_number": "+18005551234"
            }
            result = await voice_assistant.handle_call_start(db_session, call_data)
            return result["success"]
        
        # Simulate concurrent calls
        tasks = [simulate_call(i) for i in range(num_calls)]
        results = await asyncio.gather(*tasks)
        
        assert all(results), "All calls should succeed"
    
    @pytest.mark.asyncio
    async def test_response_latency(self, voice_assistant, db_session):
        """Test response time is acceptable"""
        import time
        
        call_data = {
            "call_id": "latency_test",
            "from_number": "+19167408768",
            "to_number": "+18005551234"
        }
        
        start_time = time.time()
        await voice_assistant.handle_call_start(db_session, call_data)
        end_time = time.time()
        
        latency = end_time - start_time
        assert latency < 2.0, f"Response took {latency}s, should be < 2s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
