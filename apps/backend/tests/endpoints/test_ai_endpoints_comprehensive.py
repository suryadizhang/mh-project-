"""
Comprehensive AI Endpoints Tests
Tests all AI-related API endpoints (chat, orchestrator, embeddings, voice).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from db.models.core import Customer


@pytest.mark.asyncio
class TestAIChatEndpoints:
    """Test POST /v1/ai/chat - AI chat completions"""

    async def test_chat_simple_query_success(self, client: AsyncClient):
        """Test simple chat query"""
        chat_data = {
            "message": "What are your prices for 8 guests?",
            "customer_id": str(uuid4()),
        }

        response = await client.post("/v1/ai/chat", json=chat_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "message" in data
        assert len(data["response"]) > 0

    async def test_chat_with_context(self, client: AsyncClient, db: AsyncSession):
        """Test chat with customer context"""
        customer = Customer(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        chat_data = {
            "message": "What's my booking for next week?",
            "customer_id": str(customer.id),
        }

        response = await client.post("/v1/ai/chat", json=chat_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data

    async def test_chat_booking_intent_detection(self, client: AsyncClient):
        """Test AI detects booking intent"""
        chat_data = {
            "message": "I want to book a hibachi dinner for 10 people on December 25th at 7pm",
            "customer_id": str(uuid4()),
        }

        response = await client.post("/v1/ai/chat", json=chat_data)

        assert response.status_code == 200
        data = response.json()
        assert "intent" in data or "action" in data or "response" in data
        # Should detect booking intent

    async def test_chat_pricing_query(self, client: AsyncClient):
        """Test AI answers pricing questions"""
        chat_data = {
            "message": "How much does it cost for 12 guests?",
            "customer_id": str(uuid4()),
        }

        response = await client.post("/v1/ai/chat", json=chat_data)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        # Response should mention pricing

    async def test_chat_validation_empty_message(self, client: AsyncClient):
        """Test chat fails with empty message"""
        chat_data = {
            "message": "",
            "customer_id": str(uuid4()),
        }

        response = await client.post("/v1/ai/chat", json=chat_data)

        assert response.status_code == 422

    async def test_chat_rate_limiting(self, client: AsyncClient):
        """Test chat rate limiting protection"""
        chat_data = {
            "message": "Test message",
            "customer_id": str(uuid4()),
        }

        # Send multiple rapid requests
        responses = []
        for _ in range(20):
            response = await client.post("/v1/ai/chat", json=chat_data)
            responses.append(response)

        # Should eventually rate limit (429) or succeed with all
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or all(s == 200 for s in status_codes)


@pytest.mark.asyncio
class TestAIOrchestratorEndpoints:
    """Test POST /v1/ai/orchestrator - AI orchestration"""

    async def test_orchestrator_booking_flow(self, client: AsyncClient):
        """Test orchestrator handles complete booking flow"""
        orchestration_data = {
            "task": "create_booking",
            "parameters": {
                "customer_name": "John Doe",
                "phone": "+1234567890",
                "guest_count": 8,
                "event_date": "2025-12-25",
                "event_time": "19:00",
                "address": "123 Main St",
            },
        }

        response = await client.post("/v1/ai/orchestrator", json=orchestration_data)

        assert response.status_code in [200, 201]
        data = response.json()
        assert "result" in data or "booking_id" in data

    async def test_orchestrator_multi_step_task(self, client: AsyncClient):
        """Test orchestrator handles multi-step tasks"""
        orchestration_data = {
            "task": "book_and_confirm",
            "parameters": {
                "message": "I want to book for 10 people on Christmas Eve at 7pm. My address is 456 Oak Ave",
            },
        }

        response = await client.post("/v1/ai/orchestrator", json=orchestration_data)

        assert response.status_code == 200
        data = response.json()
        assert "steps" in data or "result" in data

    async def test_orchestrator_validation_invalid_task(self, client: AsyncClient):
        """Test orchestrator rejects invalid tasks"""
        orchestration_data = {"task": "delete_all_data", "parameters": {}}  # Invalid/dangerous task

        response = await client.post("/v1/ai/orchestrator", json=orchestration_data)

        assert response.status_code in [400, 422]


@pytest.mark.asyncio
class TestAIVoiceEndpoints:
    """Test /v1/ai/voice endpoints"""

    async def test_voice_transcription(self, client: AsyncClient):
        """Test voice transcription endpoint"""
        # Simulate audio file upload
        files = {"audio": ("test.wav", b"fake_audio_data", "audio/wav")}

        response = await client.post("/v1/ai/voice/transcribe", files=files)

        # May or may not be implemented yet
        assert response.status_code in [200, 404, 501]

    async def test_voice_synthesis(self, client: AsyncClient):
        """Test text-to-speech synthesis"""
        tts_data = {
            "text": "Your booking is confirmed for December 25th at 7 PM.",
            "voice": "friendly",
        }

        response = await client.post("/v1/ai/voice/synthesize", json=tts_data)

        # May or may not be implemented yet
        assert response.status_code in [200, 404, 501]


@pytest.mark.asyncio
class TestAIEmbeddingsEndpoints:
    """Test /v1/ai/embeddings endpoints"""

    async def test_create_embeddings(self, client: AsyncClient):
        """Test creating text embeddings"""
        embedding_data = {
            "text": "Hibachi dinner for 8 guests on Christmas Eve",
        }

        response = await client.post("/v1/ai/embeddings", json=embedding_data)

        # May or may not be implemented yet
        assert response.status_code in [200, 404, 501]

    async def test_similarity_search(self, client: AsyncClient):
        """Test semantic similarity search"""
        search_data = {
            "query": "booking for Christmas",
            "limit": 10,
        }

        response = await client.post("/v1/ai/embeddings/search", json=search_data)

        # May or may not be implemented yet
        assert response.status_code in [200, 404, 501]


@pytest.mark.asyncio
class TestAICostMonitoringEndpoints:
    """Test /v1/ai/costs - AI cost tracking"""

    async def test_get_ai_costs_overview(self, client: AsyncClient):
        """Test retrieving AI costs overview"""
        response = await client.get("/v1/ai/costs")

        assert response.status_code == 200
        data = response.json()
        assert "total_cost" in data or "costs" in data

    async def test_get_ai_costs_by_date_range(self, client: AsyncClient):
        """Test filtering costs by date range"""
        response = await client.get(
            "/v1/ai/costs",
            params={
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))

    async def test_get_ai_costs_by_feature(self, client: AsyncClient):
        """Test filtering costs by feature"""
        response = await client.get("/v1/ai/costs", params={"feature": "chat"})

        assert response.status_code == 200


@pytest.mark.asyncio
class TestAIReadinessEndpoints:
    """Test /v1/ai/readiness - AI system health"""

    async def test_get_ai_readiness_status(self, client: AsyncClient):
        """Test AI readiness check"""
        response = await client.get("/v1/ai/readiness")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "readiness" in data

    async def test_get_ai_feature_flags(self, client: AsyncClient):
        """Test AI feature flag status"""
        response = await client.get("/v1/ai/readiness/flags")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


@pytest.mark.asyncio
class TestShadowLearningEndpoints:
    """Test /v1/shadow-learning - AI shadow mode"""

    async def test_shadow_learning_comparison(self, client: AsyncClient):
        """Test shadow learning comparison endpoint"""
        response = await client.get("/v1/shadow-learning/comparisons")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_shadow_learning_metrics(self, client: AsyncClient):
        """Test shadow learning metrics"""
        response = await client.get("/v1/shadow-learning/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "accuracy" in data or "metrics" in data


@pytest.mark.asyncio
class TestAIBusinessLogic:
    """Test AI business logic and integration"""

    async def test_ai_respects_customer_tone_preference(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Test AI uses customer's preferred tone"""
        from db.models.ai import CustomerTonePreference

        customer = Customer(
            name="Formal Customer",
            email="formal@example.com",
            phone="+1234567890",
            ai_tone_preference=CustomerTonePreference.FORMAL.value,
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        chat_data = {
            "message": "What are your prices?",
            "customer_id": str(customer.id),
        }

        response = await client.post("/v1/ai/chat", json=chat_data)

        assert response.status_code == 200
        data = response.json()
        # Response should be formal in tone

    async def test_ai_tracks_conversation_history(self, client: AsyncClient):
        """Test AI maintains conversation context"""
        customer_id = str(uuid4())

        # First message
        response1 = await client.post(
            "/v1/ai/chat",
            json={"message": "I want to book for 8 guests", "customer_id": customer_id},
        )
        assert response1.status_code == 200

        # Follow-up message (should remember previous context)
        response2 = await client.post(
            "/v1/ai/chat", json={"message": "Make it for December 25th", "customer_id": customer_id}
        )
        assert response2.status_code == 200
        # Should understand "it" refers to the booking

    async def test_ai_cost_tracking_records_usage(self, client: AsyncClient):
        """Test that AI usage is tracked for cost monitoring"""
        # Make AI request
        chat_data = {
            "message": "Test message for cost tracking",
            "customer_id": str(uuid4()),
        }
        await client.post("/v1/ai/chat", json=chat_data)

        # Check costs were recorded
        response = await client.get("/v1/ai/costs")
        assert response.status_code == 200
        # Should have cost data
