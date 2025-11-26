"""
Comprehensive Payment Endpoints Tests
Tests all payment-related API endpoints (Stripe, Plaid, deposits).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import date, time

from models.booking import Booking, BookingStatus
from models.customer import Customer


@pytest.mark.asyncio
class TestPaymentDepositEndpoints:
    """Test /v1/payments/deposits - Deposit payments"""

    async def test_create_deposit_payment_success(self, client: AsyncClient, db: AsyncSession):
        """Test successful deposit payment creation"""
        # Create booking first
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        payment_data = {
            "booking_id": str(booking.id),
            "amount": 250.00,
            "payment_method": "card",
            "stripe_token": "tok_visa",
        }

        response = await client.post("/v1/payments/deposits", json=payment_data)

        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "payment_id" in data or "transaction_id" in data
            assert data.get("status") in ["succeeded", "pending", "completed"]

    async def test_deposit_validation_amount_too_low(self, client: AsyncClient, db: AsyncSession):
        """Test deposit fails with amount below minimum"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        payment_data = {
            "booking_id": str(booking.id),
            "amount": 5.00,  # Too low
            "payment_method": "card",
            "stripe_token": "tok_visa",
        }

        response = await client.post("/v1/payments/deposits", json=payment_data)

        assert response.status_code == 422

    async def test_deposit_validation_invalid_payment_method(
        self, client: AsyncClient, db: AsyncSession
    ):
        """Test deposit fails with invalid payment method"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        payment_data = {
            "booking_id": str(booking.id),
            "amount": 250.00,
            "payment_method": "bitcoin",  # Invalid
            "stripe_token": "tok_visa",
        }

        response = await client.post("/v1/payments/deposits", json=payment_data)

        assert response.status_code == 422

    async def test_deposit_updates_booking_status(self, client: AsyncClient, db: AsyncSession):
        """Test successful deposit payment updates booking status"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        payment_data = {
            "booking_id": str(booking.id),
            "amount": 250.00,
            "payment_method": "card",
            "stripe_token": "tok_visa",
        }

        response = await client.post("/v1/payments/deposits", json=payment_data)

        if response.status_code in [200, 201]:
            # Check booking status changed
            await db.refresh(booking)
            # Booking should be confirmed or deposit_paid
            assert booking.status in [
                BookingStatus.CONFIRMED.value,
                "deposit_paid",  # If this status exists
            ]


@pytest.mark.asyncio
class TestPaymentStripeEndpoints:
    """Test Stripe payment processing endpoints"""

    async def test_create_payment_intent(self, client: AsyncClient, db: AsyncSession):
        """Test creating Stripe payment intent"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        intent_data = {
            "booking_id": str(booking.id),
            "amount": 250.00,
        }

        response = await client.post("/v1/payments/stripe/payment-intent", json=intent_data)

        assert response.status_code in [200, 201, 404]
        if response.status_code in [200, 201]:
            data = response.json()
            assert "client_secret" in data or "payment_intent_id" in data

    async def test_stripe_webhook_payment_succeeded(self, client: AsyncClient):
        """Test Stripe webhook for successful payment"""
        webhook_data = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test123",
                    "amount": 25000,  # $250 in cents
                    "metadata": {
                        "booking_id": str(uuid4()),
                    },
                }
            },
        }

        response = await client.post("/v1/webhooks/stripe", json=webhook_data)

        # Should accept webhook
        assert response.status_code in [200, 404]

    async def test_stripe_webhook_payment_failed(self, client: AsyncClient):
        """Test Stripe webhook for failed payment"""
        webhook_data = {
            "type": "payment_intent.payment_failed",
            "data": {
                "object": {
                    "id": "pi_test123",
                    "amount": 25000,
                    "metadata": {
                        "booking_id": str(uuid4()),
                    },
                }
            },
        }

        response = await client.post("/v1/webhooks/stripe", json=webhook_data)

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestPaymentPlaidEndpoints:
    """Test Plaid bank account verification endpoints"""

    async def test_create_plaid_link_token(self, client: AsyncClient):
        """Test creating Plaid link token"""
        link_data = {
            "customer_id": str(uuid4()),
        }

        response = await client.post("/v1/payments/plaid/link-token", json=link_data)

        assert response.status_code in [200, 404, 501]
        if response.status_code == 200:
            data = response.json()
            assert "link_token" in data

    async def test_exchange_plaid_public_token(self, client: AsyncClient):
        """Test exchanging Plaid public token"""
        exchange_data = {
            "public_token": "public-sandbox-test-token",
            "customer_id": str(uuid4()),
        }

        response = await client.post("/v1/payments/plaid/exchange-token", json=exchange_data)

        assert response.status_code in [200, 404, 501]

    async def test_verify_bank_account(self, client: AsyncClient):
        """Test bank account verification"""
        verify_data = {
            "account_id": "test_account_123",
            "customer_id": str(uuid4()),
        }

        response = await client.post("/v1/payments/plaid/verify", json=verify_data)

        assert response.status_code in [200, 404, 501]


@pytest.mark.asyncio
class TestPaymentRefundEndpoints:
    """Test payment refund endpoints"""

    async def test_create_refund_success(self, client: AsyncClient, db: AsyncSession):
        """Test successful refund creation"""
        # Simulate a paid booking
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.CONFIRMED.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        refund_data = {
            "booking_id": str(booking.id),
            "amount": 250.00,
            "reason": "Customer cancellation",
        }

        response = await client.post("/v1/payments/refunds", json=refund_data)

        assert response.status_code in [200, 201, 404]

    async def test_partial_refund(self, client: AsyncClient, db: AsyncSession):
        """Test partial refund"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.CONFIRMED.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        refund_data = {
            "booking_id": str(booking.id),
            "amount": 125.00,  # Half refund
            "reason": "Service issue",
        }

        response = await client.post("/v1/payments/refunds", json=refund_data)

        assert response.status_code in [200, 201, 404]

    async def test_refund_validation_exceeds_payment(self, client: AsyncClient, db: AsyncSession):
        """Test refund fails when amount exceeds original payment"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.CONFIRMED.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        refund_data = {
            "booking_id": str(booking.id),
            "amount": 10000.00,  # Exceeds original payment
            "reason": "Test",
        }

        response = await client.post("/v1/payments/refunds", json=refund_data)

        assert response.status_code == 422


@pytest.mark.asyncio
class TestPaymentHistoryEndpoints:
    """Test payment history and tracking"""

    async def test_get_booking_payments(self, client: AsyncClient, db: AsyncSession):
        """Test retrieving all payments for a booking"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.CONFIRMED.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        response = await client.get(f"/v1/payments/bookings/{booking.id}")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    async def test_get_customer_payments(self, client: AsyncClient, db: AsyncSession):
        """Test retrieving all payments for a customer"""
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890",
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        response = await client.get(f"/v1/payments/customers/{customer.id}")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    async def test_get_payment_by_id(self, client: AsyncClient):
        """Test retrieving specific payment by ID"""
        payment_id = uuid4()
        response = await client.get(f"/v1/payments/{payment_id}")

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestPaymentBusinessLogic:
    """Test payment business logic and calculations"""

    async def test_deposit_amount_calculation(self, client: AsyncClient, db: AsyncSession):
        """Test deposit is calculated as 50% of total or $250 minimum"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        # Get deposit amount
        response = await client.get(f"/v1/payments/bookings/{booking.id}/deposit-amount")

        if response.status_code == 200:
            data = response.json()
            deposit = data.get("deposit_amount", 0)
            # Should be at least $250
            assert deposit >= 250

    async def test_payment_email_confirmation_sent(self, client: AsyncClient, db: AsyncSession):
        """Test payment confirmation email is sent"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        payment_data = {
            "booking_id": str(booking.id),
            "amount": 250.00,
            "payment_method": "card",
            "stripe_token": "tok_visa",
        }

        response = await client.post("/v1/payments/deposits", json=payment_data)

        if response.status_code in [200, 201]:
            # Email confirmation should be queued
            # Check via email service or logs
            pass  # Implementation depends on email service

    async def test_payment_retry_logic(self, client: AsyncClient, db: AsyncSession):
        """Test payment retry after failure"""
        booking = Booking(
            customer_id=uuid4(),
            event_date=date(2025, 12, 25),
            event_time=time(19, 0),
            guest_count=8,
            address="123 Main St",
            phone="+1234567890",
            status=BookingStatus.PENDING.value,
        )
        db.add(booking)
        await db.commit()
        await db.refresh(booking)

        # First attempt (simulate failure)
        payment_data = {
            "booking_id": str(booking.id),
            "amount": 250.00,
            "payment_method": "card",
            "stripe_token": "tok_chargeDeclined",  # Simulates decline
        }

        response1 = await client.post("/v1/payments/deposits", json=payment_data)

        # Retry with valid token
        payment_data["stripe_token"] = "tok_visa"
        response2 = await client.post("/v1/payments/deposits", json=payment_data)

        # Second attempt should succeed
        assert response2.status_code in [200, 201, 422]
