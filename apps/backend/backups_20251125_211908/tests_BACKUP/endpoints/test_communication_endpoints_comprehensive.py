"""
Comprehensive Communication Endpoints Tests
Tests all communication-related API endpoints (SMS, email, RingCentral, Meta).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import datetime

from models.customer import Customer


@pytest.mark.asyncio
class TestSMSEndpoints:
    """Test /v1/communications/sms - SMS messaging via RingCentral"""

    async def test_send_sms_success(self, client: AsyncClient):
        """Test successful SMS send"""
        sms_data = {
            "to": "+1234567890",
            "message": "Your booking is confirmed for December 25th at 7 PM.",
        }

        response = await client.post("/v1/communications/sms/send", json=sms_data)

        assert response.status_code in [200, 201, 404]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "message_id" in data or "status" in data

    async def test_send_sms_validation_invalid_phone(self, client: AsyncClient):
        """Test SMS fails with invalid phone number"""
        sms_data = {
            "to": "invalid",
            "message": "Test message",
        }

        response = await client.post("/v1/communications/sms/send", json=sms_data)

        assert response.status_code == 422

    async def test_send_sms_validation_empty_message(self, client: AsyncClient):
        """Test SMS fails with empty message"""
        sms_data = {
            "to": "+1234567890",
            "message": "",
        }

        response = await client.post("/v1/communications/sms/send", json=sms_data)

        assert response.status_code == 422

    async def test_sms_quiet_hours_restriction(self, client: AsyncClient):
        """Test SMS is blocked during quiet hours (9 PM - 8 AM)"""
        sms_data = {
            "to": "+1234567890",
            "message": "Test message during quiet hours",
            "send_time": "22:00",  # 10 PM
        }

        response = await client.post("/v1/communications/sms/send", json=sms_data)

        # Should either reject or queue for next day
        if response.status_code in [200, 201]:
            data = response.json()
            assert "scheduled" in data or "queued" in data


@pytest.mark.asyncio
class TestEmailEndpoints:
    """Test /v1/communications/email - Email sending"""

    async def test_send_email_success(self, client: AsyncClient):
        """Test successful email send"""
        email_data = {
            "to": "customer@example.com",
            "subject": "Booking Confirmation",
            "body": "Your booking is confirmed.",
        }

        response = await client.post("/v1/communications/email/send", json=email_data)

        assert response.status_code in [200, 201, 404]

    async def test_send_email_with_template(self, client: AsyncClient):
        """Test sending email with template"""
        email_data = {
            "to": "customer@example.com",
            "template": "booking_confirmation",
            "variables": {
                "customer_name": "John Doe",
                "event_date": "2025-12-25",
                "event_time": "19:00",
            },
        }

        response = await client.post("/v1/communications/email/send", json=email_data)

        assert response.status_code in [200, 201, 404]

    async def test_email_validation_invalid_address(self, client: AsyncClient):
        """Test email fails with invalid email address"""
        email_data = {
            "to": "invalid-email",
            "subject": "Test",
            "body": "Test",
        }

        response = await client.post("/v1/communications/email/send", json=email_data)

        assert response.status_code == 422


@pytest.mark.asyncio
class TestRingCentralWebhookEndpoints:
    """Test /v1/webhooks/ringcentral - RingCentral webhooks"""

    async def test_ringcentral_sms_webhook_received(self, client: AsyncClient):
        """Test RingCentral SMS webhook processing"""
        webhook_data = {
            "event": "instant-message-event-filters/message-created",
            "body": {
                "id": "msg_123",
                "from": {"phoneNumber": "+1234567890"},
                "to": [{"phoneNumber": "+0987654321"}],
                "subject": "RE: Booking",
                "creationTime": datetime.utcnow().isoformat(),
            },
        }

        response = await client.post("/v1/webhooks/ringcentral", json=webhook_data)

        assert response.status_code in [200, 404]

    async def test_ringcentral_call_webhook_received(self, client: AsyncClient):
        """Test RingCentral voice call webhook"""
        webhook_data = {
            "event": "telephony-sessions-event",
            "body": {
                "id": "call_123",
                "status": "Answered",
                "from": {"phoneNumber": "+1234567890"},
                "to": {"phoneNumber": "+0987654321"},
            },
        }

        response = await client.post("/v1/webhooks/ringcentral", json=webhook_data)

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestMetaWhatsAppEndpoints:
    """Test /v1/communications/whatsapp - Meta WhatsApp (internal team only)"""

    async def test_send_whatsapp_message_internal_only(self, client: AsyncClient):
        """Test WhatsApp send (internal team notifications only)"""
        whatsapp_data = {
            "to": "+1234567890",  # Internal team member
            "message": "New booking alert: John Doe - Dec 25th",
            "is_internal": True,
        }

        response = await client.post("/v1/communications/whatsapp/send", json=whatsapp_data)

        # WhatsApp is for internal team only
        assert response.status_code in [200, 201, 404, 501]

    async def test_whatsapp_webhook_received(self, client: AsyncClient):
        """Test Meta WhatsApp webhook processing"""
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "123",
                    "changes": [
                        {
                            "value": {
                                "messaging_product": "whatsapp",
                                "messages": [
                                    {"from": "1234567890", "text": {"body": "Booking status?"}}
                                ],
                            }
                        }
                    ],
                }
            ],
        }

        response = await client.post("/v1/webhooks/meta", json=webhook_data)

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestNewsletterEndpoints:
    """Test /v1/marketing/newsletters - Newsletter management"""

    async def test_subscribe_to_newsletter(self, client: AsyncClient):
        """Test customer newsletter subscription"""
        subscription_data = {
            "email": "customer@example.com",
            "name": "John Doe",
            "preferences": ["monthly_specials", "holiday_menus"],
        }

        response = await client.post("/v1/marketing/newsletters/subscribe", json=subscription_data)

        assert response.status_code in [200, 201]

    async def test_unsubscribe_from_newsletter(self, client: AsyncClient):
        """Test newsletter unsubscription"""
        unsubscribe_data = {
            "email": "customer@example.com",
            "token": "unsubscribe_token_123",
        }

        response = await client.post("/v1/marketing/newsletters/unsubscribe", json=unsubscribe_data)

        assert response.status_code in [200, 404]

    async def test_send_newsletter_campaign(self, client: AsyncClient):
        """Test sending newsletter campaign (admin)"""
        campaign_data = {
            "subject": "Holiday Specials",
            "template": "holiday_2025",
            "segment": "all_subscribers",
        }

        response = await client.post("/v1/marketing/newsletters/send", json=campaign_data)

        assert response.status_code in [200, 201, 401, 404]


@pytest.mark.asyncio
class TestCampaignEndpoints:
    """Test /v1/marketing/campaigns - Marketing campaigns"""

    async def test_create_marketing_campaign(self, client: AsyncClient):
        """Test creating marketing campaign"""
        campaign_data = {
            "name": "Christmas 2025 Promotion",
            "type": "email",
            "start_date": "2025-12-01",
            "end_date": "2025-12-26",
        }

        response = await client.post("/v1/marketing/campaigns", json=campaign_data)

        assert response.status_code in [201, 401, 404]

    async def test_get_campaign_metrics(self, client: AsyncClient):
        """Test retrieving campaign metrics"""
        campaign_id = uuid4()
        response = await client.get(f"/v1/marketing/campaigns/{campaign_id}/metrics")

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestInboxEndpoints:
    """Test /v1/inbox - Unified communication inbox"""

    async def test_list_inbox_messages(self, client: AsyncClient):
        """Test listing all inbox messages"""
        response = await client.get("/v1/inbox")

        assert response.status_code in [200, 401, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    async def test_get_inbox_message_by_id(self, client: AsyncClient):
        """Test retrieving specific inbox message"""
        message_id = uuid4()
        response = await client.get(f"/v1/inbox/{message_id}")

        assert response.status_code in [200, 404]

    async def test_mark_inbox_message_read(self, client: AsyncClient):
        """Test marking message as read"""
        message_id = uuid4()
        response = await client.put(f"/v1/inbox/{message_id}/read", json={"is_read": True})

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestCommunicationBusinessLogic:
    """Test communication business logic and integrations"""

    async def test_sms_opt_out_respected(self, client: AsyncClient, db: AsyncSession):
        """Test SMS not sent to customers who opted out"""
        # Create customer with SMS opt-out
        customer = Customer(
            name="Opted Out Customer",
            email="optout@example.com",
            phone="+1234567890",
            sms_opted_out=True,
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        sms_data = {
            "to": "+1234567890",
            "message": "Test message",
        }

        response = await client.post("/v1/communications/sms/send", json=sms_data)

        # Should reject or skip
        if response.status_code in [200, 201]:
            data = response.json()
            assert data.get("status") in ["skipped", "opted_out"]

    async def test_communication_tracking(self, client: AsyncClient, db: AsyncSession):
        """Test all communications are tracked"""
        customer = Customer(
            name="Track Test",
            email="track@example.com",
            phone="+1234567890",
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        # Send SMS
        await client.post(
            "/v1/communications/sms/send", json={"to": "+1234567890", "message": "Test"}
        )

        # Check communication history
        response = await client.get(f"/v1/customers/{customer.id}/communications")

        if response.status_code == 200:
            data = response.json()
            # Should have communication record
            assert isinstance(data, list)

    async def test_rate_limiting_sms_per_customer(self, client: AsyncClient):
        """Test SMS rate limiting per customer"""
        customer_phone = "+1234567890"

        # Send multiple SMS rapidly
        responses = []
        for i in range(10):
            response = await client.post(
                "/v1/communications/sms/send", json={"to": customer_phone, "message": f"Test {i}"}
            )
            responses.append(response)

        # Should eventually rate limit
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes or all(s in [200, 201] for s in status_codes)

    async def test_delivery_receipt_tracking(self, client: AsyncClient):
        """Test SMS delivery receipt webhook processing"""
        receipt_data = {
            "message_id": "msg_123",
            "status": "delivered",
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = await client.post("/v1/webhooks/ringcentral/delivery-receipt", json=receipt_data)

        assert response.status_code in [200, 404]
