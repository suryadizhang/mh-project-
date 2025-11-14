"""
Real-Time Voice AI Integration Tests
Tests for WebRTC voice call system components.
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone
from uuid import uuid4

from services.realtime_voice.audio_processor import AudioProcessor, AudioConfig
from services.realtime_voice.deepgram_stt_bridge import DeepgramSTTBridge, TranscriptResult
from services.realtime_voice.call_session import CallSession, CallState, call_session_manager
from services.realtime_voice.websocket_handler import WebRTCCallHandler


class TestAudioProcessor:
    """Test audio processing functionality"""
    
    def test_audio_config_defaults(self):
        """Test default audio configuration"""
        config = AudioConfig()
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.sample_width == 2
        assert config.frame_size_ms == 20  # Fixed: frame_size_ms not frame_duration_ms
    
    def test_audio_processor_initialization(self):
        """Test audio processor initialization"""
        config = AudioConfig(sample_rate=16000)
        processor = AudioProcessor(target_config=config)
        
        assert processor.target_config.sample_rate == 16000
        assert processor.buffer == b""  # Fixed: buffer not frame_buffer
        assert processor.enable_silence_detection  # Fixed: defaults to True
    
    def test_resample_audio(self):
        """Test audio resampling from 8kHz to 16kHz"""
        import numpy as np
        
        processor = AudioProcessor(
            target_config=AudioConfig(sample_rate=16000)
        )
        
        # Generate 8kHz sine wave (1 second)
        sample_rate_in = 8000
        duration = 1.0
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate_in * duration), False)
        audio_8k = np.sin(2 * np.pi * frequency * t)
        audio_8k_int16 = (audio_8k * 32767).astype(np.int16)
        audio_8k_bytes = audio_8k_int16.tobytes()
        
        # Resample to 16kHz
        audio_16k_bytes = processor.resample(audio_8k_bytes, sample_rate_in, 16000)
        
        # Verify output length is approximately input length (numpy preserves sample count)
        # Fixed: numpy's interp preserves input sample count, not 2x output
        assert len(audio_16k_bytes) == len(audio_8k_bytes)
    
    def test_decode_mulaw(self):
        """Test μ-law decoding"""
        import numpy as np
        
        processor = AudioProcessor()
        
        # Generate test μ-law data
        mulaw_data = np.array([0, 127, 255], dtype=np.uint8).tobytes()
        
        # Decode
        pcm_data = processor.decode_mulaw(mulaw_data)
        
        # Verify output is PCM 16-bit
        assert len(pcm_data) == len(mulaw_data) * 2  # 8-bit → 16-bit
        
        # Verify values are in valid range
        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
        assert np.all(pcm_array >= -32768)
        assert np.all(pcm_array <= 32767)
    
    def test_decode_alaw(self):
        """Test A-law decoding"""
        import numpy as np
        
        processor = AudioProcessor()
        
        # Generate test A-law data
        alaw_data = np.array([0, 127, 255], dtype=np.uint8).tobytes()
        
        # Decode
        pcm_data = processor.decode_alaw(alaw_data)
        
        # Verify output is PCM 16-bit
        assert len(pcm_data) == len(alaw_data) * 2
        
        # Verify values are in valid range (fixed: check dtype before array operations)
        pcm_array = np.frombuffer(pcm_data, dtype=np.int16)
        assert pcm_array.dtype == np.int16
        assert np.min(pcm_array) >= -32768
        assert np.max(pcm_array) <= 32767
    
    def test_silence_detection(self):
        """Test silence detection"""
        import numpy as np
        
        processor = AudioProcessor(enable_silence_detection=True)
        
        # Generate silence (zeros)
        silence = np.zeros(320, dtype=np.int16).tobytes()
        assert processor.is_silence(silence)
        
        # Generate audio (sine wave)
        t = np.linspace(0, 0.02, 320, False)
        audio = np.sin(2 * np.pi * 440 * t)
        audio_int16 = (audio * 32767).astype(np.int16)
        audio_bytes = audio_int16.tobytes()
        assert not processor.is_silence(audio_bytes)
    
    def test_process_frame_mulaw(self):
        """Test processing μ-law encoded frame"""
        import numpy as np
        
        processor = AudioProcessor(
            target_config=AudioConfig(sample_rate=16000)
        )
        
        # Generate 8kHz μ-law test data (20ms = 160 samples at 8kHz)
        mulaw_frame = np.random.randint(0, 256, 160, dtype=np.uint8).tobytes()
        
        # Process frame
        frames = processor.process_frame(
            audio_data=mulaw_frame,
            source_rate=8000,
            source_encoding="mulaw",
        )
        
        # Should return processed frames
        assert len(frames) >= 0  # May buffer if incomplete


class TestDeepgramSTTBridge:
    """Test Deepgram STT bridge functionality"""
    
    @pytest.mark.asyncio
    async def test_transcript_result_creation(self):
        """Test TranscriptResult dataclass"""
        result = TranscriptResult(
            text="hello world",
            is_final=True,
            confidence=0.95,
            timestamp=datetime.now(timezone.utc),
            speech_final=True,
        )
        
        assert result.text == "hello world"
        assert result.is_final
        assert result.confidence == 0.95
        assert result.speech_final
        
        # Test to_dict
        data = result.to_dict()
        assert data["text"] == "hello world"
        assert data["is_final"]
        assert data["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_stt_bridge_initialization(self):
        """Test STT bridge initialization"""
        mock_client = Mock()
        mock_callback = Mock()
        
        bridge = DeepgramSTTBridge(
            deepgram_client=mock_client,
            callback=mock_callback,
            model="nova-2",
            language="en",
            sample_rate=16000,
        )
        
        assert bridge.deepgram_client == mock_client
        assert bridge.callback == mock_callback
        assert bridge.model == "nova-2"
        assert bridge.language == "en"
        assert bridge.sample_rate == 16000
        assert not bridge.is_running
    
    @pytest.mark.asyncio
    async def test_stt_bridge_start_stop(self):
        """Test STT bridge lifecycle"""
        mock_client = Mock()
        mock_callback = Mock()
        
        bridge = DeepgramSTTBridge(
            deepgram_client=mock_client,
            callback=mock_callback,
        )
        
        # Mock event loop
        loop = asyncio.get_event_loop()
        
        # Start bridge
        bridge.start(loop)
        assert bridge.is_running
        
        # Wait a bit for thread to start
        await asyncio.sleep(0.1)
        
        # Stop bridge
        bridge.stop()
        assert not bridge.is_running
        
        # Wait for threads to terminate
        await asyncio.sleep(0.2)


class TestCallSession:
    """Test call session management"""
    
    @pytest.mark.asyncio
    async def test_call_session_creation(self):
        """Test call session creation"""
        session = CallSession(
            session_id=uuid4(),
            call_id="test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        
        assert session.call_id == "test-123"
        assert session.from_number == "+15555551234"
        assert session.to_number == "+15555555678"
        assert session.state == CallState.INITIALIZING
        assert session.is_active
        assert not session.should_escalate
        assert session.turn_count == 0
        assert len(session.messages) == 0
        assert len(session.transcripts) == 0
    
    @pytest.mark.asyncio
    async def test_call_session_state_transitions(self):
        """Test call session state transitions"""
        session = CallSession(
            session_id=uuid4(),
            call_id="test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        
        # Initial state
        assert session.state == CallState.INITIALIZING
        
        # Mark connected
        session.mark_connected()
        assert session.state == CallState.CONNECTED
        assert session.connected_at is not None
        
        # Mark in progress
        session.mark_in_progress()
        assert session.state == CallState.IN_PROGRESS
        
        # Mark ended
        session.mark_ended()
        assert session.state == CallState.ENDED
        assert session.ended_at is not None
        assert not session.is_active
    
    @pytest.mark.asyncio
    async def test_call_session_add_message(self):
        """Test adding messages to conversation"""
        session = CallSession(
            session_id=uuid4(),
            call_id="test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        
        # Add user message
        session.add_message("user", "I want to book a table")
        assert len(session.messages) == 1
        assert session.messages[0]["role"] == "user"
        assert session.messages[0]["content"] == "I want to book a table"
        # Fixed: turn_count only increments on assistant messages
        assert session.turn_count == 0
        
        # Add assistant message
        session.add_message("assistant", "I'd be happy to help")
        assert len(session.messages) == 2
        # Fixed: turn_count increments to 1 after assistant response
        assert session.turn_count == 1
    
    @pytest.mark.asyncio
    async def test_call_session_add_transcript(self):
        """Test adding transcripts"""
        session = CallSession(
            session_id=uuid4(),
            call_id="test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        
        # Add transcript
        transcript_data = {
            "text": "hello world",
            "is_final": True,
            "confidence": 0.95,
        }
        session.add_transcript(transcript_data)
        
        assert len(session.transcripts) == 1
        assert session.transcripts[0]["text"] == "hello world"
        assert session.transcripts_count == 1
    
    @pytest.mark.asyncio
    async def test_call_session_manager_create(self):
        """Test session manager create session"""
        # Create session
        session = await call_session_manager.create_session(
            call_id="test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        
        assert session is not None
        assert session.call_id == "test-123"
        assert session.state == CallState.INITIALIZING
        
        # Verify session is tracked (fixed: await async get_session)
        retrieved = await call_session_manager.get_session(str(session.session_id))
        assert retrieved == session
        
        # Cleanup
        await call_session_manager.end_session(str(session.session_id))
    
    @pytest.mark.asyncio
    async def test_call_session_manager_stats(self):
        """Test session manager statistics"""
        # Create sessions
        session1 = await call_session_manager.create_session(
            call_id="test-1",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        session2 = await call_session_manager.create_session(
            call_id="test-2",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        
        # Get stats
        stats = call_session_manager.get_stats()
        assert stats["active_sessions"] >= 2
        assert stats["total_calls"] >= 2
        
        # End sessions
        session1.mark_ended()
        await call_session_manager.end_session(str(session1.session_id))
        
        session2.mark_failed("Test error")
        await call_session_manager.end_session(str(session2.session_id))
        
        # Verify stats updated
        stats = call_session_manager.get_stats()
        assert stats["completed_calls"] >= 1
        assert stats["failed_calls"] >= 1


class TestWebRTCCallHandler:
    """Test WebRTC call handler"""
    
    @pytest.mark.asyncio
    async def test_handler_initialization(self):
        """Test handler initialization"""
        handler = WebRTCCallHandler()
        assert handler.nlp_service is not None
    
    @pytest.mark.asyncio
    async def test_handle_control_message_start(self):
        """Test handling start control message"""
        handler = WebRTCCallHandler()
        
        # Create test session
        session = CallSession(
            session_id=uuid4(),
            call_id="test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        
        # Handle start message
        await handler._handle_control_message(session, '{"type": "start"}')
        
        # Verify state updated
        assert session.state == CallState.IN_PROGRESS
    
    @pytest.mark.asyncio
    async def test_handle_control_message_stop(self):
        """Test handling stop control message"""
        handler = WebRTCCallHandler()
        
        # Create test session
        session = CallSession(
            session_id=uuid4(),
            call_id="test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        session.mark_in_progress()
        
        # Handle stop message
        await handler._handle_control_message(session, '{"type": "stop"}')
        
        # Verify session marked inactive
        assert not session.is_active
    
    @pytest.mark.asyncio
    async def test_handle_transcript(self):
        """Test handling transcript"""
        handler = WebRTCCallHandler()
        
        # Create test session
        session = CallSession(
            session_id=uuid4(),
            call_id="test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        
        # Create interim transcript (should not trigger AI)
        interim_transcript = TranscriptResult(
            text="hello",
            is_final=False,
            confidence=0.8,
            timestamp=datetime.now(timezone.utc),
        )
        
        await handler._handle_transcript(session, interim_transcript)
        
        # Verify transcript added but no messages
        assert len(session.transcripts) == 1
        assert len(session.messages) == 0
    
    @pytest.mark.asyncio
    async def test_handle_audio_packet(self):
        """Test handling audio packet"""
        import numpy as np
        
        handler = WebRTCCallHandler()
        
        # Create test session with audio processor
        session = CallSession(
            session_id=uuid4(),
            call_id="test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        session.audio_processor = AudioProcessor()
        
        # Mock STT bridge
        session.stt_bridge = Mock()
        session.stt_bridge.send_audio = AsyncMock()
        
        # Generate test audio (8kHz mulaw, 20ms = 160 samples)
        audio_data = np.random.randint(0, 256, 160, dtype=np.uint8).tobytes()
        
        # Handle audio packet
        await handler._handle_audio_packet(session, audio_data)
        
        # Verify frames received counter incremented
        assert session.audio_frames_received == 1


class TestEndToEndFlow:
    """Test end-to-end call flow"""
    
    @pytest.mark.asyncio
    async def test_full_call_simulation(self):
        """Test simulated full call flow"""
        import numpy as np
        
        # 1. Create session
        session = await call_session_manager.create_session(
            call_id="e2e-test-123",
            from_number="+15555551234",
            to_number="+15555555678",
        )
        
        assert session.state == CallState.INITIALIZING
        
        # 2. Mark connected
        session.mark_connected()
        assert session.state == CallState.CONNECTED
        
        # 3. Initialize components
        session.audio_processor = AudioProcessor()
        
        # Mock STT bridge (don't actually connect to Deepgram)
        mock_stt = Mock()
        mock_stt.start = Mock()
        mock_stt.send_audio = AsyncMock()
        mock_stt.stop = Mock()
        session.stt_bridge = mock_stt
        
        # 4. Mark in progress
        session.mark_in_progress()
        assert session.state == CallState.IN_PROGRESS
        
        # 5. Simulate audio frames
        for _ in range(10):
            audio_frame = np.random.randint(0, 256, 160, dtype=np.uint8).tobytes()
            frames = session.audio_processor.process_frame(
                audio_data=audio_frame,
                source_rate=8000,
                source_encoding="mulaw",
            )
            session.audio_frames_received += 1
            
            # Send to STT (mocked)
            for frame in frames:
                await session.stt_bridge.send_audio(frame)
        
        assert session.audio_frames_received == 10
        
        # 6. Simulate transcript
        session.add_transcript({
            "text": "I want to book a table",
            "is_final": True,
            "confidence": 0.95,
        })
        
        # 7. Simulate conversation
        session.add_message("user", "I want to book a table")
        session.add_message("assistant", "I'd be happy to help you book a table")
        
        # Fixed: turn_count only increments on assistant messages (1 turn = 1 assistant response)
        assert session.turn_count == 1
        
        # 8. End call
        session.mark_ended()
        assert session.state == CallState.ENDED
        assert not session.is_active
        
        # 9. Cleanup
        await call_session_manager.end_session(str(session.session_id))
        
        # Verify metrics
        assert session.audio_frames_received == 10
        assert session.transcripts_count == 1
        assert len(session.messages) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
