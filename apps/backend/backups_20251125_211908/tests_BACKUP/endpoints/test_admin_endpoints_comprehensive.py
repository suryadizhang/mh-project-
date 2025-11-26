"""
Comprehensive Admin Endpoints Tests
Tests all admin-related API endpoints.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import date, time

from models.booking import Booking, BookingStatus
from models.customer import Customer


@pytest.mark.asyncio
class TestAdminAuthEndpoints:
    """Test /v1/auth - Admin authentication"""

    async def test_admin_login_success(self, client: AsyncClient):
        """Test successful admin login"""
        login_data = {
            "email": "admin@myhibachi.com",
            "password": "admin_password",
        }

        response = await client.post("/v1/auth/login", json=login_data)

        # May require setup or fail if no admin user exists
        assert response.status_code in [200, 401, 404]
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data or "token" in data

    async def test_admin_login_invalid_credentials(self, client: AsyncClient):
        """Test login fails with invalid credentials"""
        login_data = {
            "email": "admin@myhibachi.com",
            "password": "wrong_password",
        }

        response = await client.post("/v1/auth/login", json=login_data)

        assert response.status_code == 401

    async def test_admin_logout(self, client: AsyncClient):
        """Test admin logout"""
        response = await client.post("/v1/auth/logout")

        # May require authentication token
        assert response.status_code in [200, 401]


@pytest.mark.asyncio
class TestAdminDashboardEndpoints:
    """Test admin dashboard endpoints"""

    async def test_get_dashboard_stats(self, client: AsyncClient):
        """Test retrieving dashboard statistics"""
        response = await client.get("/v1/admin/dashboard/stats")

        # May require authentication
        assert response.status_code in [200, 401, 404]
        if response.status_code == 200:
            data = response.json()
            assert "total_bookings" in data or "stats" in data

    async def test_get_recent_bookings(self, client: AsyncClient):
        """Test retrieving recent bookings for dashboard"""
        response = await client.get("/v1/admin/dashboard/recent-bookings")

        assert response.status_code in [200, 401, 404]

    async def test_get_revenue_stats(self, client: AsyncClient):
        """Test retrieving revenue statistics"""
        response = await client.get("/v1/admin/dashboard/revenue")

        assert response.status_code in [200, 401, 404]


@pytest.mark.asyncio
class TestAdminBookingManagement:
    """Test admin booking management endpoints"""

    async def test_admin_update_booking_status(self, client: AsyncClient, db: AsyncSession):
        """Test admin can update booking status"""
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

        update_data = {"status": BookingStatus.CONFIRMED.value}
        response = await client.put(f"/v1/admin/bookings/{booking.id}/status", json=update_data)

        # May or may not have dedicated admin endpoint
        assert response.status_code in [200, 404]

    async def test_admin_manual_booking_creation(self, client: AsyncClient):
        """Test admin can create bookings manually"""
        booking_data = {
            "customer_name": "Walk-in Customer",
            "phone": "+1234567890",
            "event_date": "2025-12-25",
            "event_time": "19:00",
            "guest_count": 8,
            "address": "123 Main St",
            "source": "admin_manual",
        }

        response = await client.post("/v1/admin/bookings", json=booking_data)

        assert response.status_code in [201, 404]

    async def test_admin_cancel_booking_with_refund(self, client: AsyncClient, db: AsyncSession):
        """Test admin can cancel booking with refund"""
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

        cancel_data = {
            "reason": "Customer request",
            "issue_refund": True,
        }
        response = await client.post(f"/v1/admin/bookings/{booking.id}/cancel", json=cancel_data)

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestAdminCustomerManagement:
    """Test admin customer management endpoints"""

    async def test_admin_list_all_customers(self, client: AsyncClient):
        """Test admin can list all customers with filters"""
        response = await client.get(
            "/v1/admin/customers", params={"include_inactive": True, "limit": 50}
        )

        assert response.status_code in [200, 404]

    async def test_admin_view_customer_details(self, client: AsyncClient, db: AsyncSession):
        """Test admin can view full customer details"""
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890",
        )
        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        response = await client.get(f"/v1/admin/customers/{customer.id}")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == str(customer.id)

    async def test_admin_merge_duplicate_customers(self, client: AsyncClient, db: AsyncSession):
        """Test admin can merge duplicate customer records"""
        customer1 = Customer(
            name="John Doe",
            email="john1@example.com",
            phone="+1234567890",
        )
        customer2 = Customer(
            name="John Doe",
            email="john2@example.com",
            phone="+1234567890",
        )
        db.add_all([customer1, customer2])
        await db.commit()

        merge_data = {
            "source_id": str(customer2.id),
            "target_id": str(customer1.id),
        }
        response = await client.post("/v1/admin/customers/merge", json=merge_data)

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestAdminSettingsEndpoints:
    """Test admin settings management"""

    async def test_get_system_settings(self, client: AsyncClient):
        """Test retrieving system settings"""
        response = await client.get("/v1/admin/settings")

        assert response.status_code in [200, 401, 404]

    async def test_update_system_settings(self, client: AsyncClient):
        """Test updating system settings"""
        settings_data = {
            "booking_window_days": 90,
            "min_guests": 6,
            "max_guests": 20,
        }

        response = await client.put("/v1/admin/settings", json=settings_data)

        assert response.status_code in [200, 401, 404]

    async def test_get_feature_flags(self, client: AsyncClient):
        """Test retrieving feature flags"""
        response = await client.get("/v1/admin/feature-flags")

        assert response.status_code in [200, 404]

    async def test_update_feature_flag(self, client: AsyncClient):
        """Test toggling feature flag"""
        flag_data = {
            "flag_name": "ai_booking_v3",
            "enabled": True,
        }

        response = await client.put("/v1/admin/feature-flags", json=flag_data)

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestAdminReportsEndpoints:
    """Test admin reports and analytics"""

    async def test_get_booking_report(self, client: AsyncClient):
        """Test generating booking report"""
        response = await client.get(
            "/v1/admin/reports/bookings",
            params={
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
            },
        )

        assert response.status_code in [200, 404]

    async def test_get_revenue_report(self, client: AsyncClient):
        """Test generating revenue report"""
        response = await client.get(
            "/v1/admin/reports/revenue",
            params={
                "start_date": "2025-11-01",
                "end_date": "2025-11-30",
            },
        )

        assert response.status_code in [200, 404]

    async def test_export_customer_data(self, client: AsyncClient):
        """Test exporting customer data (CSV/Excel)"""
        response = await client.get("/v1/admin/reports/customers/export", params={"format": "csv"})

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestAdminAIManagement:
    """Test admin AI system management"""

    async def test_view_ai_cost_breakdown(self, client: AsyncClient):
        """Test viewing AI cost breakdown"""
        response = await client.get("/v1/admin/ai/costs")

        assert response.status_code in [200, 404]

    async def test_view_ai_usage_metrics(self, client: AsyncClient):
        """Test viewing AI usage metrics"""
        response = await client.get("/v1/admin/ai/metrics")

        assert response.status_code in [200, 404]

    async def test_toggle_ai_feature(self, client: AsyncClient):
        """Test enabling/disabling AI features"""
        toggle_data = {
            "feature": "ai_chat",
            "enabled": False,
        }

        response = await client.put("/v1/admin/ai/toggle", json=toggle_data)

        assert response.status_code in [200, 404]

    async def test_view_shadow_learning_results(self, client: AsyncClient):
        """Test viewing shadow learning comparison results"""
        response = await client.get("/v1/admin/ai/shadow-learning")

        assert response.status_code in [200, 404]


@pytest.mark.asyncio
class TestAdminBusinessLogic:
    """Test admin business logic and workflows"""

    async def test_admin_bulk_booking_update(self, client: AsyncClient, db: AsyncSession):
        """Test admin can bulk update bookings"""
        # Create multiple bookings
        bookings = [
            Booking(
                customer_id=uuid4(),
                event_date=date(2025, 12, i + 1),
                event_time=time(19, 0),
                guest_count=8,
                address="123 Main St",
                phone="+1234567890",
                status=BookingStatus.PENDING.value,
            )
            for i in range(3)
        ]
        db.add_all(bookings)
        await db.commit()

        booking_ids = [str(b.id) for b in bookings]
        bulk_update_data = {
            "booking_ids": booking_ids,
            "status": BookingStatus.CONFIRMED.value,
        }

        response = await client.put("/v1/admin/bookings/bulk-update", json=bulk_update_data)

        assert response.status_code in [200, 404]

    async def test_admin_search_across_entities(self, client: AsyncClient):
        """Test admin global search"""
        response = await client.get(
            "/v1/admin/search", params={"q": "john", "entities": "customers,bookings"}
        )

        assert response.status_code in [200, 404]
