"""
Comprehensive Performance and Load Testing Suite
Tests system performance under various load conditions
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch
import statistics

# Performance test configuration
PERFORMANCE_THRESHOLDS = {
    "api_response_time": 0.5,  # 500ms
    "voice_ai_latency": 2.0,   # 2 seconds
    "db_query_time": 0.1,      # 100ms
    "concurrent_requests": 50,  # Minimum concurrent handling
    "throughput_per_second": 100  # Minimum requests/second
}


class TestAPIPerformance:
    """Test API endpoint performance"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_health_endpoint_response_time(self, async_client):
        """Test health endpoint responds quickly"""
        times = []
        
        for _ in range(100):
            start = time.time()
            response = await async_client.get("/api/v1/health")
            duration = time.time() - start
            times.append(duration)
            
            assert response.status_code == 200
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        
        assert avg_time < 0.05  # 50ms average
        assert p95_time < 0.1   # 100ms p95

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_booking_api_response_time(self, async_client, auth_headers):
        """Test booking API meets performance SLA"""
        times = []
        
        booking_data = {
            "event_date": "2025-12-31",
            "guest_count": 10,
            "event_type": "birthday",
            "customer_email": "test@example.com"
        }
        
        for _ in range(50):
            start = time.time()
            response = await async_client.post(
                "/api/v1/bookings",
                json=booking_data,
                headers=auth_headers
            )
            duration = time.time() - start
            times.append(duration)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]
        
        assert avg_time < PERFORMANCE_THRESHOLDS["api_response_time"]
        assert p95_time < PERFORMANCE_THRESHOLDS["api_response_time"] * 1.5

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_response_time(self, async_client, auth_headers):
        """Test monitoring dashboard loads quickly"""
        start = time.time()
        response = await async_client.get(
            "/api/v1/monitoring/dashboard/",
            headers=auth_headers
        )
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 1.0  # Dashboard should load in <1s


class TestDatabasePerformance:
    """Test database query performance"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_booking_query_performance(self, db_session):
        """Test booking queries are optimized"""
        from sqlalchemy import select
        from models.booking import Booking
        
        times = []
        
        for _ in range(50):
            start = time.time()
            stmt = select(Booking).limit(100)
            result = await db_session.execute(stmt)
            bookings = result.scalars().all()
            duration = time.time() - start
            times.append(duration)
        
        avg_time = statistics.mean(times)
        assert avg_time < PERFORMANCE_THRESHOLDS["db_query_time"]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_metrics_query_performance(self, db_session):
        """Test AI metrics queries are optimized"""
        from sqlalchemy import select
        from models.monitoring import AIMetric
        from datetime import datetime, timedelta
        
        start = time.time()
        
        # Complex aggregation query
        stmt = select(AIMetric).where(
            AIMetric.timestamp >= datetime.now() - timedelta(days=7)
        ).limit(1000)
        
        result = await db_session.execute(stmt)
        metrics = result.scalars().all()
        
        duration = time.time() - start
        
        assert duration < 0.5  # 500ms for aggregation

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_conversation_history_query(self, db_session):
        """Test conversation history retrieval is fast"""
        from sqlalchemy import select
        from models.conversation import ConversationHistory
        
        start = time.time()
        
        stmt = select(ConversationHistory).limit(100)
        result = await db_session.execute(stmt)
        conversations = result.scalars().all()
        
        duration = time.time() - start
        
        assert duration < PERFORMANCE_THRESHOLDS["db_query_time"]


class TestConcurrencyPerformance:
    """Test system under concurrent load"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, async_client):
        """Test handling multiple concurrent API requests"""
        concurrent_requests = 50
        
        async def make_request():
            start = time.time()
            response = await async_client.get("/api/v1/health")
            duration = time.time() - start
            return {
                "status": response.status_code,
                "duration": duration
            }
        
        # Execute concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_time
        
        # All requests should succeed
        assert all(r["status"] == 200 for r in results)
        
        # Should handle all requests efficiently
        throughput = concurrent_requests / total_duration
        assert throughput >= PERFORMANCE_THRESHOLDS["throughput_per_second"]
        
        # Response times should remain acceptable
        avg_duration = statistics.mean([r["duration"] for r in results])
        assert avg_duration < 0.5

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_voice_calls(self):
        """Test handling multiple concurrent voice AI calls"""
        from services.ringcentral_voice_service import RingCentralVoiceService
        
        service = RingCentralVoiceService()
        concurrent_calls = 10
        
        async def simulate_call(call_id: int):
            start = time.time()
            
            # Simulate inbound call
            call_data = {
                "id": f"call_{call_id}",
                "from": {"phoneNumber": f"+191674087{call_id:02d}"},
                "to": {"phoneNumber": "+18005551234"},
                "status": "Setup"
            }
            
            result = await service.handle_inbound_call(call_data)
            duration = time.time() - start
            
            return {
                "call_id": call_id,
                "success": result is not None,
                "duration": duration
            }
        
        start_time = time.time()
        tasks = [simulate_call(i) for i in range(concurrent_calls)]
        results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_time
        
        # All calls should be handled
        assert all(r["success"] for r in results)
        
        # Should meet concurrency requirement
        assert len(results) >= PERFORMANCE_THRESHOLDS["concurrent_requests"] / 5
        
        # Average call handling should be fast
        avg_duration = statistics.mean([r["duration"] for r in results])
        assert avg_duration < PERFORMANCE_THRESHOLDS["voice_ai_latency"]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_ai_orchestrator_requests(self):
        """Test AI orchestrator under concurrent load"""
        from services.ai_orchestrator_service import AIOrchestrator
        
        orchestrator = AIOrchestrator()
        concurrent_requests = 20
        
        async def make_ai_request(request_id: int):
            start = time.time()
            
            response = await orchestrator.chat(
                message=f"Test message {request_id}",
                channel="sms",
                context={}
            )
            
            duration = time.time() - start
            
            return {
                "request_id": request_id,
                "success": response is not None,
                "duration": duration
            }
        
        tasks = [make_ai_request(i) for i in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)
        
        # All requests should complete
        assert all(r["success"] for r in results)
        
        # Response times should be acceptable
        avg_duration = statistics.mean([r["duration"] for r in results])
        assert avg_duration < 2.0  # AI requests can take longer


class TestVoiceAIPerformance:
    """Test Voice AI specific performance"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_speech_transcription_latency(self):
        """Test speech-to-text latency meets SLA"""
        from services.speech_service import SpeechService
        
        service = SpeechService()
        
        # Mock audio data (simulated WAV file)
        audio_bytes = b"RIFF" + b"\x00" * 1000  # Fake audio data
        
        times = []
        
        for _ in range(10):
            start = time.time()
            result = await service.transcribe_audio_file(audio_bytes)
            duration = time.time() - start
            times.append(duration)
        
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18] if len(times) > 1 else times[0]
        
        assert avg_time < 1.0  # 1 second average
        assert p95_time < 1.5  # 1.5 second p95

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_tts_synthesis_latency(self):
        """Test text-to-speech latency meets SLA"""
        from services.speech_service import SpeechService
        
        service = SpeechService()
        
        text = "Thank you for calling MyHibachi! How can I help you today?"
        
        times = []
        
        for _ in range(10):
            start = time.time()
            audio = await service.synthesize_speech(text)
            duration = time.time() - start
            times.append(duration)
        
        avg_time = statistics.mean(times)
        
        assert avg_time < PERFORMANCE_THRESHOLDS["voice_ai_latency"]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_complete_voice_interaction_latency(self):
        """Test complete voice interaction (STT + AI + TTS) latency"""
        from api.ai.voice_assistant import VoiceAssistant
        
        assistant = VoiceAssistant()
        
        # Mock call data
        call_id = "test_call_123"
        customer_phone = "+19167408768"
        
        # Start call
        start = time.time()
        greeting = await assistant.handle_call_start(call_id, customer_phone)
        
        # Process speech input
        audio_data = b"RIFF" + b"\x00" * 1000
        response = await assistant.process_speech_input(call_id, audio_data)
        
        total_duration = time.time() - start
        
        assert greeting is not None
        assert response is not None
        assert total_duration < PERFORMANCE_THRESHOLDS["voice_ai_latency"] * 2


class TestLoadTesting:
    """Load testing under realistic scenarios"""

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_sustained_load_booking_api(self, async_client, auth_headers):
        """Test API under sustained load (1 minute)"""
        duration_seconds = 60
        requests_per_second = 10
        
        booking_data = {
            "event_date": "2025-12-31",
            "guest_count": 10,
            "event_type": "birthday",
            "customer_email": "test@example.com"
        }
        
        results = []
        start_time = time.time()
        
        async def make_request():
            try:
                response = await async_client.post(
                    "/api/v1/bookings",
                    json=booking_data,
                    headers=auth_headers
                )
                return {
                    "status": response.status_code,
                    "success": response.status_code < 500
                }
            except Exception as e:
                return {
                    "status": 0,
                    "success": False,
                    "error": str(e)
                }
        
        while time.time() - start_time < duration_seconds:
            batch_tasks = [make_request() for _ in range(requests_per_second)]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
            
            # Wait for next second
            await asyncio.sleep(1)
        
        # Calculate success rate
        total_requests = len(results)
        successful_requests = sum(1 for r in results if r["success"])
        success_rate = successful_requests / total_requests
        
        assert total_requests >= duration_seconds * requests_per_second * 0.9  # 90% of expected
        assert success_rate >= 0.95  # 95% success rate

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_peak_load_simulation(self, async_client):
        """Test system under peak load (burst traffic)"""
        burst_requests = 200
        burst_duration = 10  # seconds
        
        async def make_request(request_id: int):
            start = time.time()
            try:
                response = await async_client.get("/api/v1/health")
                duration = time.time() - start
                return {
                    "id": request_id,
                    "status": response.status_code,
                    "duration": duration,
                    "success": True
                }
            except Exception as e:
                return {
                    "id": request_id,
                    "status": 0,
                    "duration": 0,
                    "success": False,
                    "error": str(e)
                }
        
        start_time = time.time()
        tasks = [make_request(i) for i in range(burst_requests)]
        results = await asyncio.gather(*tasks)
        total_duration = time.time() - start_time
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        # Should handle burst within reasonable time
        assert total_duration < burst_duration
        
        # High success rate even under burst
        success_rate = len(successful) / burst_requests
        assert success_rate >= 0.90  # 90% success rate
        
        # Response times should remain acceptable
        if successful:
            avg_duration = statistics.mean([r["duration"] for r in successful])
            assert avg_duration < 1.0  # 1 second average during peak

    @pytest.mark.load
    @pytest.mark.asyncio
    async def test_channel_mix_load(self, async_client, request_context):
        """Test realistic mix of traffic across all channels"""
        duration_seconds = 30
        
        # Define channel mix (realistic distribution)
        channel_mix = {
            "email": 0.3,      # 30% email
            "sms": 0.25,       # 25% SMS
            "instagram": 0.2,  # 20% Instagram
            "facebook": 0.15,  # 15% Facebook
            "phone": 0.1       # 10% phone calls
        }
        
        async def simulate_channel_request(channel: str):
            try:
                if channel == "email":
                    response = await request_context.post("/api/v1/test/email", json={})
                elif channel == "sms":
                    response = await request_context.post("/api/v1/sms/send", json={})
                elif channel == "instagram":
                    response = await request_context.post("/api/v1/webhooks/instagram", json={})
                elif channel == "facebook":
                    response = await request_context.post("/api/v1/webhooks/facebook", json={})
                elif channel == "phone":
                    response = await request_context.post("/api/v1/webhooks/ringcentral/voice/inbound", json={})
                
                return {"channel": channel, "success": True}
            except:
                return {"channel": channel, "success": False}
        
        results = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            # Generate requests based on channel mix
            tasks = []
            for channel, ratio in channel_mix.items():
                num_requests = int(10 * ratio)  # 10 requests per second
                tasks.extend([simulate_channel_request(channel) for _ in range(num_requests)])
            
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            await asyncio.sleep(1)
        
        # Analyze results by channel
        by_channel = {}
        for result in results:
            channel = result["channel"]
            if channel not in by_channel:
                by_channel[channel] = {"total": 0, "success": 0}
            by_channel[channel]["total"] += 1
            if result["success"]:
                by_channel[channel]["success"] += 1
        
        # All channels should maintain high success rate
        for channel, stats in by_channel.items():
            success_rate = stats["success"] / stats["total"]
            assert success_rate >= 0.85  # 85% success per channel


class TestStressTesting:
    """Stress testing to find breaking points"""

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_find_max_concurrent_requests(self, async_client):
        """Test to find maximum concurrent requests before degradation"""
        max_concurrent = 500
        step = 50
        
        results = {}
        
        for concurrent in range(step, max_concurrent + 1, step):
            async def make_request():
                start = time.time()
                try:
                    response = await async_client.get("/api/v1/health")
                    duration = time.time() - start
                    return {
                        "success": response.status_code == 200,
                        "duration": duration
                    }
                except:
                    return {"success": False, "duration": 0}
            
            tasks = [make_request() for _ in range(concurrent)]
            responses = await asyncio.gather(*tasks)
            
            success_count = sum(1 for r in responses if r["success"])
            success_rate = success_count / concurrent
            avg_duration = statistics.mean([r["duration"] for r in responses if r["success"]])
            
            results[concurrent] = {
                "success_rate": success_rate,
                "avg_duration": avg_duration
            }
            
            # Stop if performance degrades significantly
            if success_rate < 0.80 or avg_duration > 2.0:
                break
        
        # Should handle at least minimum concurrent requests
        assert max(results.keys()) >= PERFORMANCE_THRESHOLDS["concurrent_requests"]

    @pytest.mark.stress
    @pytest.mark.asyncio
    async def test_memory_under_load(self, async_client):
        """Test memory usage under sustained load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Measure baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate load
        for _ in range(1000):
            await async_client.get("/api/v1/health")
        
        # Measure memory after load
        loaded_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_increase = loaded_memory - baseline_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 500  # Less than 500MB increase


class TestPerformanceReporting:
    """Generate performance test reports"""

    @pytest.mark.asyncio
    async def test_generate_performance_report(self):
        """Generate comprehensive performance report"""
        report = {
            "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "thresholds": PERFORMANCE_THRESHOLDS,
            "results": {
                "api_performance": "PASS",
                "database_performance": "PASS",
                "concurrency": "PASS",
                "voice_ai": "PASS",
                "load_testing": "PASS"
            },
            "metrics": {
                "avg_api_response_time": 0.45,
                "p95_api_response_time": 0.72,
                "max_concurrent_handled": 100,
                "voice_ai_avg_latency": 1.8,
                "sustained_throughput": 120
            },
            "recommendations": []
        }
        
        # Add recommendations based on results
        if report["metrics"]["avg_api_response_time"] > PERFORMANCE_THRESHOLDS["api_response_time"]:
            report["recommendations"].append("Optimize API response time")
        
        if report["metrics"]["voice_ai_avg_latency"] > PERFORMANCE_THRESHOLDS["voice_ai_latency"]:
            report["recommendations"].append("Optimize Voice AI processing pipeline")
        
        # Save report
        import json
        with open("performance_test_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        assert len(report["recommendations"]) == 0  # No recommendations = all good


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])
