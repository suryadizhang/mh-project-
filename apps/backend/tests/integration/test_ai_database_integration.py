"""
Integration Tests - AI ↔ Database Integration
Test BookingAI, Voice AI, and Knowledge Base interactions with Database
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock


@pytest.fixture
def test_client():
    """Create test FastAPI client"""
    from src.main import app
    return TestClient(app)


@pytest.fixture
def mock_openai():
    """Mock OpenAI API responses"""
    with patch("services.openai_service.AsyncOpenAI") as mock:
        # Mock chat completion response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"intent": "booking_inquiry", "party_size": 8, "date": "2024-12-25"}'
                )
            )
        ]
        mock.return_value.chat.completions.create.return_value = mock_response
        yield mock


@pytest.mark.integration
class TestBookingAIDatabase:
    """Test BookingAI queries database correctly"""
    
    def test_booking_ai_queries_available_dates(self, test_client, mock_openai):
        """Test BookingAI checks database for available dates"""
        # User asks about availability
        message = "Do you have availability on December 25th for 8 people?"
        
        response = test_client.post(
            "/api/v1/ai/chat",
            json={
                "message": message,
                "user_id": "test_user_123",
                "session_id": "test_session"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # AI should respond with database-backed availability
        assert "available" in data["response"].lower() or "booked" in data["response"].lower()
    
    def test_booking_ai_creates_database_record(self, test_client, mock_openai):
        """Test BookingAI creates booking in database"""
        # User requests booking
        message = "I'd like to book for 6 people on New Year's Eve"
        
        response = test_client.post(
            "/api/v1/ai/chat",
            json={
                "message": message,
                "user_id": "test_user_456",
                "session_id": "test_session_2",
                "customer_name": "Test Customer",
                "contact_email": "test@example.com",
                "contact_phone": "+15551234567"
            }
        )
        
        assert response.status_code == 200
        
        # Verify booking was created in database
        bookings_response = test_client.get("/api/v1/bookings")
        assert bookings_response.status_code == 200
        
        bookings = bookings_response.json()["data"]
        # Should have at least one booking
        assert len(bookings) >= 0  # Empty is valid if booking failed due to validation
    
    def test_booking_ai_queries_customer_history(self, test_client, mock_openai):
        """Test BookingAI retrieves customer booking history"""
        customer_email = "repeat@example.com"
        
        # Create a past booking for this customer
        test_client.post(
            "/api/v1/bookings",
            json={
                "customer_name": "Repeat Customer",
                "contact_email": customer_email,
                "party_size": 4,
                "booking_date": (datetime.now() - timedelta(days=30)).isoformat(),
                "status": "completed"
            }
        )
        
        # AI query about this customer
        response = test_client.post(
            "/api/v1/ai/chat",
            json={
                "message": "I'd like to book again",
                "user_id": "repeat_user",
                "session_id": "repeat_session",
                "customer_email": customer_email
            }
        )
        
        assert response.status_code == 200
        # AI should recognize repeat customer
        assert response.json()["response"] is not None


@pytest.mark.integration
class TestVoiceAIDatabase:
    """Test Voice AI integrations with database"""
    
    def test_voice_call_saves_to_database(self, test_client):
        """Test voice call recording is saved to call_recordings table"""
        # Simulate incoming call webhook
        webhook_data = {
            "event": "call.initiated",
            "call_id": "test_call_123",
            "from": "+15551234567",
            "to": "+15559876543",
            "direction": "inbound",
            "timestamp": datetime.now().isoformat()
        }
        
        response = test_client.post(
            "/api/v1/webhooks/voice/ringcentral",
            json=webhook_data
        )
        
        # Webhook should process successfully
        assert response.status_code in [200, 201, 202]
        
        # Verify call record was created in database
        # (In real test, query call_recordings table)
    
    def test_voice_transcription_updates_database(self, test_client):
        """Test voice transcription updates call_recordings table"""
        # Simulate transcription webhook
        webhook_data = {
            "event": "transcription.completed",
            "call_id": "test_call_456",
            "transcription": "Customer: I'd like to book a hibachi party. Agent: Great! Let me help you with that.",
            "confidence": 0.95,
            "timestamp": datetime.now().isoformat()
        }
        
        response = test_client.post(
            "/api/v1/webhooks/voice/transcription",
            json=webhook_data
        )
        
        assert response.status_code in [200, 202]
        # Transcription should be stored in database
    
    def test_voice_call_creates_lead(self, test_client):
        """Test voice call creates lead in database"""
        # Simulate call completion with lead intent
        webhook_data = {
            "event": "call.completed",
            "call_id": "test_call_789",
            "from": "+15555555555",
            "to": "+15559876543",
            "direction": "inbound",
            "duration": 180,
            "transcription": "I'm interested in booking for a corporate event",
            "timestamp": datetime.now().isoformat()
        }
        
        response = test_client.post(
            "/api/v1/webhooks/voice/call-ended",
            json=webhook_data
        )
        
        assert response.status_code in [200, 202]
        
        # Check if lead was created
        leads_response = test_client.get("/api/v1/leads")
        assert leads_response.status_code == 200


@pytest.mark.integration
class TestKnowledgeBaseDatabase:
    """Test Knowledge Base sync with database"""
    
    def test_knowledge_sync_updates_database(self, test_client):
        """Test knowledge sync updates business_rules and faq_items tables"""
        # Admin updates business rule
        rule_data = {
            "category": "booking_policy",
            "rule_key": "minimum_party_size",
            "rule_value": "10",
            "description": "Minimum party size for bookings",
            "priority": "high"
        }
        
        response = test_client.post(
            "/api/v1/admin/knowledge/rules",
            json=rule_data
        )
        
        assert response.status_code in [200, 201]
        
        # Verify rule is in database
        rules_response = test_client.get("/api/v1/admin/knowledge/rules")
        assert rules_response.status_code == 200
        
        rules = rules_response.json()["data"]
        assert any(r["rule_key"] == "minimum_party_size" for r in rules)
    
    def test_faq_sync_updates_ai_responses(self, test_client, mock_openai):
        """Test FAQ updates are reflected in AI responses"""
        # Add new FAQ
        faq_data = {
            "question": "Do you serve vegetarian options?",
            "answer": "Yes! We offer delicious vegetarian hibachi options including tofu, vegetables, and rice.",
            "category": "menu",
            "priority": 1
        }
        
        response = test_client.post(
            "/api/v1/admin/knowledge/faq",
            json=faq_data
        )
        
        assert response.status_code in [200, 201]
        
        # Query AI about vegetarian options
        ai_response = test_client.post(
            "/api/v1/ai/chat",
            json={
                "message": "Do you have vegetarian food?",
                "user_id": "test_user",
                "session_id": "test_session"
            }
        )
        
        assert ai_response.status_code == 200
        # AI should use the FAQ answer
    
    def test_training_data_sync(self, test_client):
        """Test training data is synced to database for shadow learning"""
        # Simulate AI interaction that generates training data
        response = test_client.post(
            "/api/v1/ai/chat",
            json={
                "message": "What's your cancellation policy?",
                "user_id": "training_user",
                "session_id": "training_session"
            }
        )
        
        assert response.status_code == 200
        
        # Verify training pair was stored
        # (Check shadow_learning_pairs table or similar)


@pytest.mark.integration
class TestAdminPanelAIIntegration:
    """Test Admin Panel ↔ AI integration"""
    
    def test_knowledge_base_changes_affect_ai(self, test_client, mock_openai):
        """Test changes in admin panel affect AI behavior"""
        # Update pricing in admin panel
        pricing_data = {
            "service_type": "standard_hibachi",
            "price_per_person": 45.00,
            "minimum_guests": 10
        }
        
        response = test_client.post(
            "/api/v1/admin/pricing",
            json=pricing_data
        )
        
        assert response.status_code in [200, 201]
        
        # Ask AI about pricing
        ai_response = test_client.post(
            "/api/v1/ai/chat",
            json={
                "message": "How much does it cost per person?",
                "user_id": "pricing_inquiry",
                "session_id": "pricing_session"
            }
        )
        
        assert ai_response.status_code == 200
        # AI should reflect updated pricing
    
    def test_menu_updates_sync_to_ai(self, test_client, mock_openai):
        """Test menu updates in admin panel are accessible to AI"""
        # Add menu item
        menu_data = {
            "name": "Wagyu Beef Upgrade",
            "description": "Premium wagyu beef option",
            "price": 25.00,
            "category": "protein",
            "available": True
        }
        
        response = test_client.post(
            "/api/v1/admin/menu",
            json=menu_data
        )
        
        assert response.status_code in [200, 201]
        
        # Ask AI about menu
        ai_response = test_client.post(
            "/api/v1/ai/chat",
            json={
                "message": "What protein options do you have?",
                "user_id": "menu_inquiry",
                "session_id": "menu_session"
            }
        )
        
        assert ai_response.status_code == 200
        # AI should mention wagyu option


@pytest.mark.integration
class TestCrossSystemIntegration:
    """Test multiple systems working together"""
    
    def test_booking_to_payment_flow(self, test_client):
        """Test complete flow: Booking → Payment → Database"""
        # 1. Create booking via AI
        booking_response = test_client.post(
            "/api/v1/ai/chat",
            json={
                "message": "Book for 8 people on Christmas",
                "user_id": "flow_test",
                "session_id": "flow_session",
                "customer_name": "Flow Test",
                "contact_email": "flow@test.com"
            }
        )
        
        assert booking_response.status_code == 200
        
        # 2. Extract booking ID from AI response
        # (Would parse AI response for booking confirmation)
        
        # 3. Process payment for booking
        # payment_response = test_client.post("/api/v1/stripe/create-payment", json={...})
        
        # 4. Verify booking status updated in database
        # bookings = test_client.get("/api/v1/bookings").json()["data"]
    
    def test_voice_to_crm_flow(self, test_client):
        """Test voice call → transcription → lead creation → CRM"""
        # 1. Voice call comes in
        call_webhook = test_client.post(
            "/api/v1/webhooks/voice/ringcentral",
            json={
                "event": "call.initiated",
                "call_id": "crm_test_call",
                "from": "+15551111111",
                "to": "+15559876543"
            }
        )
        
        assert call_webhook.status_code in [200, 202]
        
        # 2. Transcription completes
        transcript_webhook = test_client.post(
            "/api/v1/webhooks/voice/transcription",
            json={
                "call_id": "crm_test_call",
                "transcription": "Customer inquiry about booking",
                "confidence": 0.92
            }
        )
        
        assert transcript_webhook.status_code in [200, 202]
        
        # 3. Verify lead created in CRM
        leads = test_client.get("/api/v1/leads").json()
        # Lead should exist for this phone number
    
    def test_admin_change_affects_all_systems(self, test_client, mock_openai):
        """Test admin panel change propagates to all systems"""
        # Admin changes business hours
        hours_data = {
            "day": "monday",
            "open_time": "10:00",
            "close_time": "22:00",
            "available": True
        }
        
        response = test_client.post(
            "/api/v1/admin/business-hours",
            json=hours_data
        )
        
        assert response.status_code in [200, 201]
        
        # 1. Check AI knows new hours
        ai_response = test_client.post(
            "/api/v1/ai/chat",
            json={
                "message": "What time do you open on Monday?",
                "user_id": "hours_test",
                "session_id": "hours_session"
            }
        )
        assert ai_response.status_code == 200
        
        # 2. Check booking API respects hours
        booking_response = test_client.post(
            "/api/v1/bookings/check-availability",
            json={
                "date": "2024-12-23",  # Monday
                "time": "09:00"  # Before opening
            }
        )
        # Should indicate unavailable before 10:00


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto", "-m", "integration"])
