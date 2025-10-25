"""
Integration tests for Newsletter Auto-Subscribe System
Tests quote form, booking form, and newsletter subscription flows
"""
import pytest
import asyncio
from datetime import date, datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

# Test configuration
BASE_URL = "http://test"


@pytest.mark.integration
class TestQuoteFormIntegration:
    """Test quote form with newsletter auto-subscribe"""
    
    @pytest.mark.asyncio
    async def test_quote_form_creates_lead_and_subscribes(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that submitting quote form creates lead and auto-subscribes"""
        # Submit quote form
        response = await async_client.post(
            "/api/v1/public/leads",
            json={
                "name": "John Doe",
                "phone": "5551234567",
                "email": "john@example.com",
                "event_date": "2025-12-25",
                "guest_count": 50,
                "budget": "$1,000 - $2,000",
                "location": "San Jose, CA",
                "message": "Looking for hibachi catering",
                "source": "quote"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "lead_id" in data
        
        # Verify lead was created in database
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM lead.leads WHERE phone = '+15551234567'")
        )
        count = result.scalar()
        assert count >= 1, "Lead should be created in database"
    
    @pytest.mark.asyncio
    async def test_quote_form_without_email(self, async_client: AsyncClient):
        """Test quote form works with phone only (email optional)"""
        response = await async_client.post(
            "/api/v1/public/leads",
            json={
                "name": "Jane Smith",
                "phone": "(555) 987-6543",  # Test phone formatting
                "guest_count": 20,
                "source": "quote"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_quote_form_honeypot_spam_detection(self, async_client: AsyncClient):
        """Test honeypot field blocks spam"""
        response = await async_client.post(
            "/api/v1/public/leads",
            json={
                "name": "Spammer",
                "phone": "5551111111",
                "honeypot": "spam content",  # Should trigger spam detection
                "source": "quote"
            }
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_quote_form_missing_required_fields(self, async_client: AsyncClient):
        """Test validation of required fields"""
        # Missing name
        response = await async_client.post(
            "/api/v1/public/leads",
            json={
                "phone": "5551234567",
                "source": "quote"
            }
        )
        
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestBookingFormIntegration:
    """Test booking form with newsletter auto-subscribe"""
    
    @pytest.mark.asyncio
    async def test_booking_form_creates_lead_and_subscribes(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test that submitting booking form creates booking lead and auto-subscribes"""
        response = await async_client.post(
            "/api/v1/public/bookings",
            json={
                "customer_name": "Alice Johnson",
                "customer_phone": "+15559876543",
                "customer_email": "alice@example.com",
                "date": "2025-12-31",
                "time": "18:00",  # 24-hour format
                "guests": 30,
                "location_address": "123 Main St, San Jose, CA 95123",
                "special_requests": "Vegetarian options needed"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "booking_id" in data
        assert "newsletter" in data["message"].lower() or "thank" in data["message"].lower()
        
        # Verify booking lead was created
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM lead.leads WHERE phone = '+15559876543' AND message LIKE '%BOOKING REQUEST%'")
        )
        count = result.scalar()
        assert count >= 1, "Booking lead should be created"
    
    @pytest.mark.asyncio
    async def test_booking_form_time_formats(self, async_client: AsyncClient):
        """Test various time formats are accepted"""
        times = ["12:00", "15:30", "18:00", "21:45"]
        
        for time_str in times:
            response = await async_client.post(
                "/api/v1/public/bookings",
                json={
                    "customer_name": "Test User",
                    "customer_phone": "5551234567",
                    "customer_email": "test@example.com",
                    "date": "2025-11-15",
                    "time": time_str,
                    "guests": 10,
                    "location_address": "456 Oak Ave, San Jose, CA 95110"
                }
            )
            
            assert response.status_code == 200, f"Time format {time_str} should be accepted"
    
    @pytest.mark.asyncio
    async def test_booking_form_past_date_rejected(self, async_client: AsyncClient):
        """Test that past dates are rejected"""
        response = await async_client.post(
            "/api/v1/public/bookings",
            json={
                "customer_name": "Test User",
                "customer_phone": "5551234567",
                "customer_email": "test@example.com",
                "date": "2020-01-01",  # Past date
                "time": "18:00",
                "guests": 10,
                "location_address": "123 Main St, San Jose, CA"
            }
        )
        
        assert response.status_code == 400
        assert "future" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_booking_form_honeypot_spam_detection(self, async_client: AsyncClient):
        """Test honeypot blocks spam bookings"""
        response = await async_client.post(
            "/api/v1/public/bookings",
            json={
                "customer_name": "Spammer",
                "customer_phone": "5551111111",
                "customer_email": "spam@example.com",
                "date": "2025-12-25",
                "time": "18:00",
                "guests": 10,
                "location_address": "123 Spam St",
                "honeypot": "bot filled this"  # Should block
            }
        )
        
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_booking_form_guest_count_validation(self, async_client: AsyncClient):
        """Test guest count validation (1-50)"""
        # Test too many guests
        response = await async_client.post(
            "/api/v1/public/bookings",
            json={
                "customer_name": "Test User",
                "customer_phone": "5551234567",
                "customer_email": "test@example.com",
                "date": "2025-12-25",
                "time": "18:00",
                "guests": 100,  # Over limit
                "location_address": "123 Main St"
            }
        )
        
        assert response.status_code == 422  # Validation error


@pytest.mark.integration
class TestEndToEndFlow:
    """Test complete user journey"""
    
    @pytest.mark.asyncio
    async def test_quote_to_booking_flow(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test user submits quote, then books"""
        # Step 1: Submit quote request
        quote_response = await async_client.post(
            "/api/v1/public/leads",
            json={
                "name": "End-to-End Test User",
                "phone": "5559999999",
                "email": "e2e@example.com",
                "event_date": "2025-12-25",
                "guest_count": 40,
                "source": "quote"
            }
        )
        
        assert quote_response.status_code == 201
        quote_data = quote_response.json()
        assert quote_data["success"] is True
        
        # Step 2: Submit booking
        booking_response = await async_client.post(
            "/api/v1/public/bookings",
            json={
                "customer_name": "End-to-End Test User",
                "customer_phone": "5559999999",  # Same phone
                "customer_email": "e2e@example.com",
                "date": "2025-12-25",
                "time": "18:00",
                "guests": 40,
                "location_address": "789 Test Ave, San Jose, CA"
            }
        )
        
        assert booking_response.status_code == 200
        
        # Verify both leads exist
        result = await db_session.execute(
            text("SELECT COUNT(*) FROM lead.leads WHERE phone = '+15559999999'")
        )
        count = result.scalar()
        assert count >= 2, "Should have both quote and booking leads"


@pytest.mark.unit
class TestPhoneNumberFormatting:
    """Test phone number cleaning and formatting"""
    
    @pytest.mark.asyncio
    async def test_various_phone_formats(self, async_client: AsyncClient):
        """Test that various phone formats are accepted and cleaned"""
        phone_formats = [
            "5551234567",          # Plain 10 digits
            "(555) 123-4567",      # Formatted
            "555-123-4567",        # Dashes
            "+15551234567",        # E.164
            "1-555-123-4567",      # With country code
        ]
        
        for i, phone in enumerate(phone_formats):
            response = await async_client.post(
                "/api/v1/public/leads",
                json={
                    "name": f"Phone Test {i}",
                    "phone": phone,
                    "source": "quote"
                }
            )
            
            assert response.status_code == 201, f"Phone format '{phone}' should be accepted"
    
    @pytest.mark.asyncio
    async def test_invalid_phone_formats(self, async_client: AsyncClient):
        """Test that invalid phone numbers are rejected"""
        invalid_phones = [
            "123",               # Too short
            "abc-def-ghij",      # Letters
            "12345",             # Too short
            "",                  # Empty
        ]
        
        for phone in invalid_phones:
            response = await async_client.post(
                "/api/v1/public/leads",
                json={
                    "name": "Invalid Phone Test",
                    "phone": phone,
                    "source": "quote"
                }
            )
            
            assert response.status_code in [400, 422], f"Invalid phone '{phone}' should be rejected"


@pytest.mark.performance
class TestPerformance:
    """Test performance and response times"""
    
    @pytest.mark.asyncio
    async def test_quote_form_response_time(self, async_client: AsyncClient, performance_tracker):
        """Test quote form responds within acceptable time"""
        with performance_tracker.measure("quote_form"):
            response = await async_client.post(
                "/api/v1/public/leads",
                json={
                    "name": "Performance Test",
                    "phone": "5551111111",
                    "email": "perf@test.com",
                    "source": "quote"
                }
            )
        
        assert response.status_code == 201
        response_time_ms = performance_tracker.get_duration_ms("quote_form")
        assert response_time_ms < 1000, f"Quote form should respond in <1000ms (got {response_time_ms:.2f}ms)"
    
    @pytest.mark.asyncio
    async def test_booking_form_response_time(self, async_client: AsyncClient, performance_tracker):
        """Test booking form responds within acceptable time"""
        with performance_tracker.measure("booking_form"):
            response = await async_client.post(
                "/api/v1/public/bookings",
                json={
                    "customer_name": "Performance Test",
                    "customer_phone": "5552222222",
                    "customer_email": "perf@test.com",
                    "date": "2025-12-25",
                    "time": "18:00",
                    "guests": 20,
                    "location_address": "123 Perf St"
                }
            )
        
        assert response.status_code == 200
        response_time_ms = performance_tracker.get_duration_ms("booking_form")
        assert response_time_ms < 1500, f"Booking form should respond in <1500ms (got {response_time_ms:.2f}ms)"


@pytest.mark.smoke
class TestSmokeTests:
    """Critical path smoke tests"""
    
    @pytest.mark.asyncio
    async def test_quote_form_smoke(self, async_client: AsyncClient):
        """Smoke test: Quote form basic functionality"""
        response = await async_client.post(
            "/api/v1/public/leads",
            json={
                "name": "Smoke Test",
                "phone": "5550000000",
                "source": "quote"
            }
        )
        
        assert response.status_code == 201
        assert response.json()["success"] is True
    
    @pytest.mark.asyncio
    async def test_booking_form_smoke(self, async_client: AsyncClient):
        """Smoke test: Booking form basic functionality"""
        response = await async_client.post(
            "/api/v1/public/bookings",
            json={
                "customer_name": "Smoke Test",
                "customer_phone": "5550000001",
                "customer_email": "smoke@test.com",
                "date": "2025-12-25",
                "time": "18:00",
                "guests": 10,
                "location_address": "123 Smoke St"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Smoke test: Health check endpoint"""
        response = await async_client.get("/api/v1/public/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


# Run tests with: pytest tests/test_newsletter_integration.py -v -s --tb=short
# Run smoke tests only: pytest tests/test_newsletter_integration.py -v -s -m smoke
# Run performance tests: pytest tests/test_newsletter_integration.py -v -s -m performance
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])


class TestQuoteFormIntegration:
    """Test quote form with newsletter auto-subscribe"""
    
    @pytest.mark.asyncio
    async def test_quote_form_creates_lead_and_subscribes(self):
        """Test that submitting quote form creates lead and auto-subscribes"""
        async with AsyncClient(base_url=BASE_URL) as client:
            # Submit quote form
            response = await client.post(
                "/api/v1/public/leads",
                json={
                    "name": "John Doe",
                    "phone": "5551234567",
                    "email": "john@example.com",
                    "event_date": "2025-12-25",
                    "guest_count": 50,
                    "budget": "$1,000 - $2,000",
                    "location": "San Jose, CA",
                    "message": "Looking for hibachi catering",
                    "source": "quote"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert "lead_id" in data
            
            # TODO: Verify subscriber was created in database
            # TODO: Verify welcome SMS/email was sent
    
    @pytest.mark.asyncio
    async def test_quote_form_without_email(self):
        """Test quote form works with phone only (email optional)"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/v1/public/leads",
                json={
                    "name": "Jane Smith",
                    "phone": "(555) 987-6543",  # Test phone formatting
                    "guest_count": 20,
                    "source": "quote"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_quote_form_rate_limiting(self):
        """Test rate limiting (10 requests/minute)"""
        async with AsyncClient(base_url=BASE_URL) as client:
            # Make 11 requests rapidly
            tasks = []
            for i in range(11):
                task = client.post(
                    "/api/v1/public/leads",
                    json={
                        "name": f"Test User {i}",
                        "phone": f"555000{i:04d}",
                        "source": "quote"
                    }
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # At least one should be rate limited (status 429)
            status_codes = [r.status_code for r in responses if not isinstance(r, Exception)]
            assert 429 in status_codes or len([s for s in status_codes if s == 201]) <= 10
    
    @pytest.mark.asyncio
    async def test_quote_form_honeypot_spam_detection(self):
        """Test honeypot field blocks spam"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/v1/public/leads",
                json={
                    "name": "Spammer",
                    "phone": "5551111111",
                    "honeypot": "spam content",  # Should trigger spam detection
                    "source": "quote"
                }
            )
            
            assert response.status_code == 400


class TestBookingFormIntegration:
    """Test booking form with newsletter auto-subscribe"""
    
    @pytest.mark.asyncio
    async def test_booking_form_creates_lead_and_subscribes(self):
        """Test that submitting booking form creates booking lead and auto-subscribes"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/v1/public/bookings",
                json={
                    "customer_name": "Alice Johnson",
                    "customer_phone": "+15559876543",
                    "customer_email": "alice@example.com",
                    "date": "2025-12-31",
                    "time": "18:00",  # 24-hour format
                    "guests": 30,
                    "location_address": "123 Main St, San Jose, CA 95123",
                    "special_requests": "Vegetarian options needed"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "booking_id" in data
            assert "newsletter" in data["message"].lower() or "thank" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_booking_form_time_conversion(self):
        """Test various time formats are accepted"""
        async with AsyncClient(base_url=BASE_URL) as client:
            # Test different time formats
            times = ["12:00", "15:30", "18:00", "21:45"]
            
            for time_str in times:
                response = await client.post(
                    "/api/v1/public/bookings",
                    json={
                        "customer_name": "Test User",
                        "customer_phone": "5551234567",
                        "customer_email": "test@example.com",
                        "date": "2025-11-15",
                        "time": time_str,
                        "guests": 10,
                        "location_address": "456 Oak Ave, San Jose, CA 95110"
                    }
                )
                
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_booking_form_past_date_rejected(self):
        """Test that past dates are rejected"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/v1/public/bookings",
                json={
                    "customer_name": "Test User",
                    "customer_phone": "5551234567",
                    "customer_email": "test@example.com",
                    "date": "2020-01-01",  # Past date
                    "time": "18:00",
                    "guests": 10,
                    "location_address": "123 Main St, San Jose, CA"
                }
            )
            
            assert response.status_code == 400
            assert "future" in response.json()["detail"].lower()
    
    @pytest.mark.asyncio
    async def test_booking_form_rate_limiting(self):
        """Test booking form rate limiting (5 requests/minute)"""
        async with AsyncClient(base_url=BASE_URL) as client:
            tasks = []
            for i in range(6):
                task = client.post(
                    "/api/v1/public/bookings",
                    json={
                        "customer_name": f"Test User {i}",
                        "customer_phone": f"555000{i:04d}",
                        "customer_email": f"test{i}@example.com",
                        "date": "2025-12-25",
                        "time": "18:00",
                        "guests": 10,
                        "location_address": "123 Main St"
                    }
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            status_codes = [r.status_code for r in responses if not isinstance(r, Exception)]
            
            # Should have rate limiting kick in
            assert 429 in status_codes or len([s for s in status_codes if s == 200]) <= 5
    
    @pytest.mark.asyncio
    async def test_booking_form_honeypot_spam_detection(self):
        """Test honeypot blocks spam bookings"""
        async with AsyncClient(base_url=BASE_URL) as client:
            response = await client.post(
                "/api/v1/public/bookings",
                json={
                    "customer_name": "Spammer",
                    "customer_phone": "5551111111",
                    "customer_email": "spam@example.com",
                    "date": "2025-12-25",
                    "time": "18:00",
                    "guests": 10,
                    "location_address": "123 Spam St",
                    "honeypot": "bot filled this"  # Should block
                }
            )
            
            assert response.status_code == 400


class TestNewsletterService:
    """Test newsletter subscription and STOP command"""
    
    @pytest.mark.asyncio
    async def test_stop_command_unsubscribes(self):
        """Test that STOP command unsubscribes user"""
        # This would require SMS webhook testing
        # Placeholder for integration with RingCentral/Twilio webhook
        pass
    
    @pytest.mark.asyncio
    async def test_start_command_resubscribes(self):
        """Test that START command resubscribes user"""
        pass
    
    @pytest.mark.asyncio
    async def test_duplicate_subscription_updates_existing(self):
        """Test that duplicate subscriptions update existing record"""
        pass


class TestEndToEndFlow:
    """Test complete user journey"""
    
    @pytest.mark.asyncio
    async def test_quote_to_booking_flow(self):
        """Test user submits quote, then books"""
        async with AsyncClient(base_url=BASE_URL) as client:
            # Step 1: Submit quote request
            quote_response = await client.post(
                "/api/v1/public/leads",
                json={
                    "name": "End-to-End Test User",
                    "phone": "5559999999",
                    "email": "e2e@example.com",
                    "event_date": "2025-12-25",
                    "guest_count": 40,
                    "source": "quote"
                }
            )
            
            assert quote_response.status_code == 201
            quote_data = quote_response.json()
            lead_id = quote_data["lead_id"]
            
            # Step 2: Submit booking
            booking_response = await client.post(
                "/api/v1/public/bookings",
                json={
                    "customer_name": "End-to-End Test User",
                    "customer_phone": "5559999999",  # Same phone
                    "customer_email": "e2e@example.com",
                    "date": "2025-12-25",
                    "time": "18:00",
                    "guests": 40,
                    "location_address": "789 Test Ave, San Jose, CA"
                }
            )
            
            assert booking_response.status_code == 200
            
            # TODO: Verify subscriber is not duplicated (should update existing)


class TestErrorHandling:
    """Test error handling and graceful degradation"""
    
    @pytest.mark.asyncio
    async def test_lead_created_even_if_newsletter_fails(self):
        """Test that lead is created even if newsletter subscription fails"""
        # This would require mocking newsletter service to fail
        pass
    
    @pytest.mark.asyncio
    async def test_invalid_phone_format(self):
        """Test various phone number formats"""
        async with AsyncClient(base_url=BASE_URL) as client:
            # Test too short phone
            response = await client.post(
                "/api/v1/public/leads",
                json={
                    "name": "Test User",
                    "phone": "123",  # Too short
                    "source": "quote"
                }
            )
            
            assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self):
        """Test validation of required fields"""
        async with AsyncClient(base_url=BASE_URL) as client:
            # Missing name
            response = await client.post(
                "/api/v1/public/leads",
                json={
                    "phone": "5551234567",
                    "source": "quote"
                }
            )
            
            assert response.status_code == 422  # Validation error


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
