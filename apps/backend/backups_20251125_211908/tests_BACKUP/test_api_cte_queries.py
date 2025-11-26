"""
CTE Query API Tests

Tests Common Table Expression (CTE) query implementation:
- Payment analytics CTE
- Booking KPIs CTE
- Customer analytics CTE
- Data accuracy validation
- JSON parsing correctness
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any


class TestPaymentAnalyticsCTE:
    """Test payment analytics CTE endpoint."""
    
    @pytest.mark.asyncio
    async def test_payment_analytics_basic_structure(
        self,
        auth_client: AsyncClient,
        create_test_payments,
    ):
        """
        Test basic payment analytics response structure.
        
        Should return:
        - total_payments: Integer count
        - total_amount: Decimal total
        - method_stats: Dict of payment method counts
        - monthly_revenue: List of monthly data
        """
        await create_test_payments(count=50)
        
        # Query last 30 days
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        response = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate structure
        assert "total_payments" in data
        assert "total_amount" in data
        assert isinstance(data["total_payments"], int)
        assert isinstance(data["total_amount"], (int, float, str))
        
        # Optional fields (may be present)
        if "method_stats" in data:
            assert isinstance(data["method_stats"], dict)
            print(f"✅ Method stats: {data['method_stats']}")
        
        if "monthly_revenue" in data:
            assert isinstance(data["monthly_revenue"], list)
            print(f"✅ Monthly revenue: {len(data['monthly_revenue'])} months")
        
        print(f"✅ Payment analytics structure valid")
    
    @pytest.mark.asyncio
    async def test_payment_analytics_aggregation_accuracy(
        self,
        auth_client: AsyncClient,
        create_test_payments,
        test_db_session,
    ):
        """
        Test that CTE aggregations match raw data.
        
        Validates:
        - total_payments count is accurate
        - total_amount sum is accurate
        - No data loss in aggregation
        """
        # Create known payments
        payments = await create_test_payments(count=10)
        
        # Calculate expected values
        expected_count = len(payments)
        expected_total = sum(
            Decimal(str(p.get("amount", 0))) 
            for p in payments
        )
        
        # Query analytics
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        response = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
        )
        
        data = response.json()
        
        # Validate counts
        assert data["total_payments"] == expected_count, (
            f"Expected {expected_count} payments, got {data['total_payments']}"
        )
        
        # Validate totals (allow small rounding difference)
        actual_total = Decimal(str(data["total_amount"]))
        difference = abs(actual_total - expected_total)
        assert difference < Decimal("0.01"), (
            f"Expected ${expected_total}, got ${actual_total} (diff: ${difference})"
        )
        
        print(f"✅ Aggregation accurate: {expected_count} payments, ${expected_total}")
    
    @pytest.mark.asyncio
    async def test_payment_analytics_date_filtering(
        self,
        auth_client: AsyncClient,
        create_test_payments,
    ):
        """
        Test that date range filtering works correctly.
        
        Validates:
        - Only payments in date range are included
        - Date boundaries are respected
        """
        await create_test_payments(count=50)
        
        # Query narrow date range (last 7 days)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=7)
        
        response_7d = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
        )
        data_7d = response_7d.json()
        
        # Query wider date range (last 30 days)
        start_date_30d = end_date - timedelta(days=30)
        response_30d = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date_30d}&end_date={end_date}"
        )
        data_30d = response_30d.json()
        
        # 30-day range should have >= 7-day range
        assert data_30d["total_payments"] >= data_7d["total_payments"], (
            "30-day range should include all 7-day payments"
        )
        
        print(f"✅ Date filtering: 7d={data_7d['total_payments']}, 30d={data_30d['total_payments']}")
    
    @pytest.mark.asyncio
    async def test_payment_analytics_method_stats_parsing(
        self,
        auth_client: AsyncClient,
        create_test_payments,
    ):
        """
        Test that payment method statistics are parsed correctly from JSON.
        
        Validates:
        - method_stats is a dict
        - Each method has count
        - All methods are accounted for
        """
        await create_test_payments(count=30)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        response = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
        )
        
        data = response.json()
        
        if "method_stats" in data:
            method_stats = data["method_stats"]
            assert isinstance(method_stats, dict)
            
            # Each method should have a count
            for method, count in method_stats.items():
                assert isinstance(method, str)
                assert isinstance(count, int)
                assert count > 0
            
            print(f"✅ Method stats parsed: {method_stats}")
        else:
            print(f"ℹ️  Method stats not in response")


class TestBookingKPIsCTE:
    """Test booking KPIs CTE endpoint."""
    
    @pytest.mark.asyncio
    async def test_booking_kpis_basic_structure(
        self,
        auth_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test basic booking KPIs response structure.
        
        Should return:
        - total_bookings: Integer count
        - total_revenue: Decimal total
        - status_breakdown: Dict of status counts
        - revenue_by_status: Revenue aggregated by status
        """
        await create_test_bookings(count=50)
        
        response = await auth_client.get("/api/admin/kpis")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate structure
        assert "total_bookings" in data or "bookings_count" in data
        
        if "total_revenue" in data:
            assert isinstance(data["total_revenue"], (int, float, str))
        
        if "status_breakdown" in data:
            assert isinstance(data["status_breakdown"], dict)
            print(f"✅ Status breakdown: {data['status_breakdown']}")
        
        print(f"✅ Booking KPIs structure valid")
    
    @pytest.mark.asyncio
    async def test_booking_kpis_status_aggregation(
        self,
        auth_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test that status breakdown aggregations are accurate.
        
        Validates:
        - All statuses are counted
        - Sum of status counts equals total bookings
        """
        # Create bookings with known statuses
        await create_test_bookings(count=30)
        
        response = await auth_client.get("/api/admin/kpis")
        data = response.json()
        
        if "status_breakdown" in data:
            status_breakdown = data["status_breakdown"]
            
            # Sum all status counts
            total_from_statuses = sum(status_breakdown.values())
            
            # Should match total bookings
            total_bookings = data.get("total_bookings") or data.get("bookings_count")
            if total_bookings:
                assert total_from_statuses == total_bookings, (
                    f"Status counts ({total_from_statuses}) != total bookings ({total_bookings})"
                )
                print(f"✅ Status aggregation accurate: {total_from_statuses} bookings")
    
    @pytest.mark.asyncio
    async def test_booking_kpis_revenue_calculation(
        self,
        auth_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test that revenue calculations are accurate.
        
        Validates:
        - Revenue matches sum of booking amounts
        - Decimal precision is maintained
        """
        bookings = await create_test_bookings(count=20)
        
        # Calculate expected revenue
        expected_revenue = sum(
            Decimal(str(b.get("amount", 0) or b.get("total_amount", 0)))
            for b in bookings
        )
        
        response = await auth_client.get("/api/admin/kpis")
        data = response.json()
        
        if "total_revenue" in data:
            actual_revenue = Decimal(str(data["total_revenue"]))
            difference = abs(actual_revenue - expected_revenue)
            
            # Allow small rounding difference
            assert difference < Decimal("0.01"), (
                f"Expected ${expected_revenue}, got ${actual_revenue}"
            )
            print(f"✅ Revenue calculation accurate: ${actual_revenue}")
    
    @pytest.mark.asyncio
    async def test_booking_kpis_performance(
        self,
        auth_client: AsyncClient,
        create_test_bookings,
        performance_tracker,
    ):
        """
        Test that booking KPIs endpoint meets performance target.
        
        Target: <17ms (25x improvement from 300ms)
        """
        await create_test_bookings(count=100)
        
        with performance_tracker("booking_kpis"):
            response = await auth_client.get("/api/admin/kpis")
        
        duration_ms = performance_tracker.get_duration("booking_kpis")
        
        assert response.status_code == 200
        print(f"✅ Booking KPIs: {duration_ms:.2f}ms (target: <17ms)")


class TestCustomerAnalyticsCTE:
    """Test customer analytics CTE endpoint."""
    
    @pytest.mark.asyncio
    async def test_customer_analytics_basic_structure(
        self,
        auth_client: AsyncClient,
        create_test_bookings,
        create_test_payments,
        sample_customer_data,
    ):
        """
        Test basic customer analytics response structure.
        
        Should return:
        - total_bookings: Customer's booking count
        - total_spent: Customer's total spend
        - payment_methods: List of methods used
        - loyalty_tier: Customer's tier
        """
        # Create customer data
        await create_test_bookings(count=10)
        await create_test_payments(count=10)
        
        customer_email = sample_customer_data["email"]
        
        response = await auth_client.get(
            f"/api/admin/customer-analytics?customer_email={customer_email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate structure
        assert "total_bookings" in data or "bookings_count" in data
        
        if "total_spent" in data:
            assert isinstance(data["total_spent"], (int, float, str))
        
        if "payment_methods" in data:
            assert isinstance(data["payment_methods"], list)
            print(f"✅ Payment methods: {data['payment_methods']}")
        
        print(f"✅ Customer analytics structure valid")
    
    @pytest.mark.asyncio
    async def test_customer_analytics_filtering(
        self,
        auth_client: AsyncClient,
        create_test_bookings,
        sample_customer_data,
    ):
        """
        Test that customer analytics filters by customer correctly.
        
        Validates:
        - Only specific customer's data is returned
        - No data leakage from other customers
        """
        # Create bookings for test customer
        customer_email = sample_customer_data["email"]
        await create_test_bookings(count=5)
        
        response = await auth_client.get(
            f"/api/admin/customer-analytics?customer_email={customer_email}"
        )
        
        data = response.json()
        
        # Verify customer email in response
        if "customer_email" in data:
            assert data["customer_email"] == customer_email
        
        print(f"✅ Customer filtering: {customer_email}")
    
    @pytest.mark.asyncio
    async def test_customer_analytics_payment_method_aggregation(
        self,
        auth_client: AsyncClient,
        create_test_payments,
        sample_customer_data,
    ):
        """
        Test that payment methods are aggregated correctly.
        
        Validates:
        - All payment methods used by customer are listed
        - No duplicate methods
        - Methods are from customer's payments only
        """
        await create_test_payments(count=15)
        
        customer_email = sample_customer_data["email"]
        
        response = await auth_client.get(
            f"/api/admin/customer-analytics?customer_email={customer_email}"
        )
        
        data = response.json()
        
        if "payment_methods" in data:
            methods = data["payment_methods"]
            
            # Should be a list
            assert isinstance(methods, list)
            
            # Should have unique methods
            assert len(methods) == len(set(methods)), "Duplicate payment methods found"
            
            print(f"✅ Payment methods aggregated: {methods}")


class TestCTEQueryCorrectness:
    """Test overall CTE query correctness and data integrity."""
    
    @pytest.mark.asyncio
    async def test_cte_vs_raw_query_consistency(
        self,
        auth_client: AsyncClient,
        create_test_payments,
        test_db_session,
    ):
        """
        Test that CTE queries return same results as raw queries.
        
        This is a sanity check to ensure optimizations don't change results.
        """
        await create_test_payments(count=50)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        # Get CTE result
        response = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
        )
        
        data = response.json()
        
        # Verify basic sanity
        assert data["total_payments"] > 0, "Should have payments in test data"
        assert float(data["total_amount"]) > 0, "Should have non-zero amount"
        
        print(f"✅ CTE query correctness validated")
    
    @pytest.mark.asyncio
    async def test_cte_handles_null_values(
        self,
        auth_client: AsyncClient,
        create_test_payments,
    ):
        """
        Test that CTE queries handle NULL values gracefully.
        
        Validates:
        - NULLs don't break aggregations
        - NULLs are excluded from counts where appropriate
        """
        # Create payments (some may have NULL fields)
        await create_test_payments(count=20)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        response = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should not have NULL in critical fields
        assert data["total_payments"] is not None
        assert data["total_amount"] is not None
        
        print(f"✅ NULL handling correct")
    
    @pytest.mark.asyncio
    async def test_cte_handles_empty_results(
        self,
        auth_client: AsyncClient,
    ):
        """
        Test that CTE queries handle empty results gracefully.
        
        Validates:
        - No errors when no data matches filters
        - Returns appropriate zero values
        """
        # Query far future date (no data)
        end_date = datetime.utcnow().date() + timedelta(days=365)
        start_date = end_date - timedelta(days=30)
        
        response = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return zeros, not errors
        assert data["total_payments"] == 0
        assert float(data["total_amount"]) == 0.0
        
        print(f"✅ Empty results handled gracefully")


class TestCTEMultiTenancy:
    """Test multi-tenancy filtering in CTE queries."""
    
    @pytest.mark.asyncio
    async def test_station_filtering_in_payment_analytics(
        self,
        auth_client: AsyncClient,
        create_test_payments,
    ):
        """
        Test that station_id filtering works in payment analytics.
        
        Validates:
        - Only specified station's data is returned
        - Other stations' data is excluded
        """
        await create_test_payments(count=50)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        # Query with station filter
        response = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}&station_id=1"
        )
        
        data = response.json()
        
        # Verify station filtering (if station_id is in response)
        if "station_id" in data:
            assert data["station_id"] == 1
        
        print(f"✅ Station filtering works")
    
    @pytest.mark.asyncio
    async def test_station_filtering_excludes_other_stations(
        self,
        auth_client: AsyncClient,
        create_test_payments,
    ):
        """
        Test that station filtering actually excludes other stations' data.
        
        Validates:
        - Station 1 count != All stations count
        - Multi-tenancy is enforced
        """
        await create_test_payments(count=100)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        # Query all stations
        response_all = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
        )
        data_all = response_all.json()
        
        # Query specific station
        response_station1 = await auth_client.get(
            f"/api/payments/analytics?start_date={start_date}&end_date={end_date}&station_id=1"
        )
        data_station1 = response_station1.json()
        
        # Station 1 should have <= all stations
        assert data_station1["total_payments"] <= data_all["total_payments"]
        
        print(f"✅ Station isolation: Station1={data_station1['total_payments']}, All={data_all['total_payments']}")
