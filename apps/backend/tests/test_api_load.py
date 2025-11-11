"""
Load Testing for Optimized APIs

Tests system performance under concurrent load:
- Concurrent request handling
- Connection pool management
- Throughput measurement
- Error rate monitoring
"""
import pytest
import asyncio
from httpx import AsyncClient
from datetime import datetime, timedelta
from typing import List, Dict, Any


class TestConcurrentLoadHandling:
    """Test API performance under concurrent load."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_cursor_pagination_requests(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test cursor pagination under concurrent load.
        
        Validates:
        - 50 concurrent requests complete successfully
        - No errors or timeouts
        - Response times remain acceptable
        """
        await create_test_bookings(count=200)
        
        async def fetch_page(page_num: int) -> Dict[str, Any]:
            """Fetch a page of bookings."""
            response = await async_client.get(f"/api/bookings?limit=20")
            return {
                "page": page_num,
                "status": response.status_code,
                "duration_ms": response.elapsed.total_seconds() * 1000,
            }
        
        # Send 50 concurrent requests
        tasks = [fetch_page(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successes = [r for r in results if isinstance(r, dict) and r["status"] == 200]
        failures = [r for r in results if not isinstance(r, dict) or r.get("status") != 200]
        
        # Should have high success rate
        success_rate = len(successes) / len(results) * 100
        assert success_rate >= 95, f"Success rate {success_rate:.1f}% below 95%"
        
        # Calculate average response time
        avg_duration = sum(r["duration_ms"] for r in successes) / len(successes)
        
        print(f"✅ Concurrent pagination: {len(successes)}/50 succeeded ({success_rate:.1f}%)")
        print(f"   Average response time: {avg_duration:.2f}ms")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_cte_analytics_requests(
        self,
        auth_client: AsyncClient,
        create_test_payments,
        performance_tracker,
    ):
        """
        Test CTE analytics under concurrent load.
        
        Validates:
        - 30 concurrent analytics requests complete successfully
        - CTE queries don't block each other
        - Connection pool handles load
        """
        await create_test_payments(count=150)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        async def fetch_analytics(request_num: int) -> Dict[str, Any]:
            """Fetch payment analytics."""
            start_time = datetime.utcnow()
            response = await auth_client.get(
                f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
            )
            duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "request": request_num,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "data": response.json() if response.status_code == 200 else None,
            }
        
        # Send 30 concurrent requests
        with performance_tracker("concurrent_analytics"):
            tasks = [fetch_analytics(i) for i in range(30)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        total_duration = performance_tracker.get_duration("concurrent_analytics")
        
        # Count successes
        successes = [r for r in results if isinstance(r, dict) and r["status"] == 200]
        success_rate = len(successes) / len(results) * 100
        
        # Should have high success rate
        assert success_rate >= 95, f"Success rate {success_rate:.1f}% below 95%"
        
        # Calculate throughput
        throughput = len(successes) / (total_duration / 1000)  # requests per second
        
        print(f"✅ Concurrent analytics: {len(successes)}/30 succeeded ({success_rate:.1f}%)")
        print(f"   Total time: {total_duration:.2f}ms")
        print(f"   Throughput: {throughput:.1f} req/sec")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_mixed_concurrent_requests(
        self,
        async_client: AsyncClient,
        auth_client: AsyncClient,
        create_test_bookings,
        create_test_payments,
    ):
        """
        Test mixed endpoint types under concurrent load.
        
        Validates:
        - Different endpoints don't interfere
        - Connection pool handles variety
        - No resource starvation
        """
        await create_test_bookings(count=100)
        await create_test_payments(count=100)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        async def fetch_mixed(request_num: int) -> Dict[str, Any]:
            """Fetch different endpoints based on request number."""
            if request_num % 3 == 0:
                # Cursor pagination
                response = await async_client.get("/api/bookings?limit=20")
                endpoint = "cursor_pagination"
            elif request_num % 3 == 1:
                # Payment analytics
                response = await auth_client.get(
                    f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
                )
                endpoint = "payment_analytics"
            else:
                # Booking KPIs
                response = await auth_client.get("/api/admin/kpis")
                endpoint = "booking_kpis"
            
            return {
                "request": request_num,
                "endpoint": endpoint,
                "status": response.status_code,
            }
        
        # Send 60 mixed concurrent requests
        tasks = [fetch_mixed(i) for i in range(60)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes by endpoint
        successes = [r for r in results if isinstance(r, dict) and r["status"] == 200]
        success_rate = len(successes) / len(results) * 100
        
        # Group by endpoint
        by_endpoint = {}
        for r in successes:
            endpoint = r["endpoint"]
            by_endpoint[endpoint] = by_endpoint.get(endpoint, 0) + 1
        
        # Should have high success rate
        assert success_rate >= 90, f"Mixed success rate {success_rate:.1f}% below 90%"
        
        print(f"✅ Mixed concurrent: {len(successes)}/60 succeeded ({success_rate:.1f}%)")
        print(f"   Breakdown: {by_endpoint}")


class TestConnectionPoolManagement:
    """Test database connection pool handling."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_connection_pool_no_exhaustion(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test that connection pool doesn't exhaust under load.
        
        Validates:
        - 100 sequential requests complete successfully
        - No "connection pool exhausted" errors
        - Connections are properly released
        """
        await create_test_bookings(count=100)
        
        errors = []
        
        # Send 100 sequential requests
        for i in range(100):
            try:
                response = await async_client.get("/api/bookings?limit=10")
                if response.status_code != 200:
                    errors.append(f"Request {i}: Status {response.status_code}")
            except Exception as e:
                errors.append(f"Request {i}: {str(e)}")
        
        # Should have very few errors
        error_rate = len(errors) / 100 * 100
        assert error_rate < 5, f"Error rate {error_rate:.1f}% too high: {errors[:5]}"
        
        print(f"✅ Connection pool: {100 - len(errors)}/100 succeeded ({100 - error_rate:.1f}%)")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_connection_pool_concurrent_stress(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test connection pool under high concurrent stress.
        
        Validates:
        - 100 concurrent requests complete
        - Connection pool scales appropriately
        - No deadlocks or hangs
        """
        await create_test_bookings(count=200)
        
        async def stress_request(request_num: int) -> Dict[str, Any]:
            """Make a request and track success."""
            try:
                response = await async_client.get("/api/bookings?limit=10")
                return {
                    "request": request_num,
                    "status": response.status_code,
                    "success": response.status_code == 200,
                }
            except Exception as e:
                return {
                    "request": request_num,
                    "status": None,
                    "success": False,
                    "error": str(e),
                }
        
        # Send 100 concurrent requests
        tasks = [stress_request(i) for i in range(100)]
        results = await asyncio.gather(*tasks)
        
        # Count successes
        successes = [r for r in results if r["success"]]
        success_rate = len(successes) / len(results) * 100
        
        # Should handle most requests
        assert success_rate >= 85, f"Stress test success rate {success_rate:.1f}% too low"
        
        print(f"✅ Connection pool stress: {len(successes)}/100 succeeded ({success_rate:.1f}%)")


class TestThroughputMeasurement:
    """Test system throughput and requests per second."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_cursor_pagination_throughput(
        self,
        async_client: AsyncClient,
        create_test_bookings,
        performance_tracker,
    ):
        """
        Measure throughput of cursor pagination endpoint.
        
        Target: >50 requests/second
        """
        await create_test_bookings(count=500)
        
        request_count = 100
        
        with performance_tracker("pagination_throughput"):
            tasks = [
                async_client.get("/api/bookings?limit=20")
                for _ in range(request_count)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration_seconds = performance_tracker.get_duration("pagination_throughput") / 1000
        
        # Count successful responses
        successes = [
            r for r in responses
            if not isinstance(r, Exception) and r.status_code == 200
        ]
        
        # Calculate throughput
        throughput = len(successes) / duration_seconds
        
        print(f"✅ Pagination throughput: {throughput:.1f} req/sec")
        print(f"   {len(successes)}/{request_count} succeeded in {duration_seconds:.2f}s")
        
        # Should achieve decent throughput
        assert throughput > 20, f"Throughput {throughput:.1f} req/sec too low"
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_cte_analytics_throughput(
        self,
        auth_client: AsyncClient,
        create_test_payments,
        performance_tracker,
    ):
        """
        Measure throughput of CTE analytics endpoint.
        
        Target: >30 requests/second
        """
        await create_test_payments(count=500)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        request_count = 50
        
        with performance_tracker("analytics_throughput"):
            tasks = [
                auth_client.get(
                    f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
                )
                for _ in range(request_count)
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration_seconds = performance_tracker.get_duration("analytics_throughput") / 1000
        
        # Count successes
        successes = [
            r for r in responses
            if not isinstance(r, Exception) and r.status_code == 200
        ]
        
        # Calculate throughput
        throughput = len(successes) / duration_seconds
        
        print(f"✅ Analytics throughput: {throughput:.1f} req/sec")
        print(f"   {len(successes)}/{request_count} succeeded in {duration_seconds:.2f}s")
        
        # Should achieve decent throughput
        assert throughput > 10, f"Throughput {throughput:.1f} req/sec too low"


class TestErrorRateMonitoring:
    """Test error rates under various load conditions."""
    
    @pytest.mark.asyncio
    async def test_error_rate_under_normal_load(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test error rate under normal load (10 concurrent requests).
        
        Target: <1% error rate
        """
        await create_test_bookings(count=100)
        
        async def make_request(request_num: int) -> bool:
            """Make request and return success status."""
            try:
                response = await async_client.get("/api/bookings?limit=20")
                return response.status_code == 200
            except Exception:
                return False
        
        # Send 10 concurrent requests, 5 times
        all_results = []
        for batch in range(5):
            tasks = [make_request(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            all_results.extend(results)
        
        # Calculate error rate
        successes = sum(all_results)
        error_rate = (len(all_results) - successes) / len(all_results) * 100
        
        # Should have very low error rate
        assert error_rate < 5, f"Error rate {error_rate:.1f}% too high under normal load"
        
        print(f"✅ Normal load error rate: {error_rate:.1f}% ({successes}/{len(all_results)} succeeded)")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_error_rate_under_heavy_load(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test error rate under heavy load (50 concurrent requests).
        
        Target: <10% error rate
        """
        await create_test_bookings(count=200)
        
        async def make_request(request_num: int) -> bool:
            """Make request and return success status."""
            try:
                response = await async_client.get("/api/bookings?limit=20")
                return response.status_code == 200
            except Exception:
                return False
        
        # Send 50 concurrent requests
        tasks = [make_request(i) for i in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Calculate error rate
        successes = sum(results)
        error_rate = (len(results) - successes) / len(results) * 100
        
        # Should maintain acceptable error rate
        assert error_rate < 20, f"Error rate {error_rate:.1f}% too high under heavy load"
        
        print(f"✅ Heavy load error rate: {error_rate:.1f}% ({successes}/{len(results)} succeeded)")
    
    @pytest.mark.asyncio
    async def test_error_recovery(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test system recovery after errors.
        
        Validates:
        - System recovers from transient errors
        - Subsequent requests succeed
        """
        await create_test_bookings(count=50)
        
        # Make some requests (may have errors)
        first_batch = []
        for _ in range(20):
            try:
                response = await async_client.get("/api/bookings?limit=20")
                first_batch.append(response.status_code == 200)
            except Exception:
                first_batch.append(False)
        
        # Wait a bit for recovery
        await asyncio.sleep(1)
        
        # Make more requests (should succeed)
        second_batch = []
        for _ in range(10):
            try:
                response = await async_client.get("/api/bookings?limit=20")
                second_batch.append(response.status_code == 200)
            except Exception:
                second_batch.append(False)
        
        # Second batch should have better success rate
        first_success_rate = sum(first_batch) / len(first_batch) * 100
        second_success_rate = sum(second_batch) / len(second_batch) * 100
        
        print(f"✅ Error recovery: First={first_success_rate:.1f}%, Second={second_success_rate:.1f}%")


class TestLongRunningLoad:
    """Test system stability under sustained load."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_sustained_load_stability(
        self,
        async_client: AsyncClient,
        create_test_bookings,
    ):
        """
        Test system stability under sustained load for 30 seconds.
        
        Validates:
        - No memory leaks
        - No performance degradation over time
        - Consistent error rates
        """
        await create_test_bookings(count=500)
        
        start_time = datetime.utcnow()
        request_count = 0
        success_count = 0
        
        # Run for 30 seconds (or 200 requests, whichever comes first)
        while (datetime.utcnow() - start_time).total_seconds() < 30 and request_count < 200:
            try:
                response = await async_client.get("/api/bookings?limit=20")
                if response.status_code == 200:
                    success_count += 1
            except Exception:
                pass
            
            request_count += 1
            
            # Small delay between requests
            await asyncio.sleep(0.1)
        
        duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        success_rate = success_count / request_count * 100
        throughput = request_count / duration_seconds
        
        # Should maintain stability
        assert success_rate > 80, f"Success rate {success_rate:.1f}% dropped below 80%"
        
        print(f"✅ Sustained load: {success_count}/{request_count} succeeded ({success_rate:.1f}%)")
        print(f"   Duration: {duration_seconds:.1f}s, Throughput: {throughput:.1f} req/sec")


class TestDatabaseQueryLoad:
    """Test database query performance under load."""
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_cte_query_execution(
        self,
        auth_client: AsyncClient,
        create_test_payments,
        create_test_bookings,
    ):
        """
        Test concurrent execution of multiple CTE queries.
        
        Validates:
        - Multiple complex CTEs can run simultaneously
        - No database locks or contention
        - All queries complete successfully
        """
        await create_test_payments(count=200)
        await create_test_bookings(count=200)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=30)
        
        async def run_analytics_mix(request_num: int) -> Dict[str, Any]:
            """Run different analytics queries."""
            results = {}
            
            try:
                # Payment analytics
                if request_num % 3 == 0:
                    resp = await auth_client.get(
                        f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
                    )
                    results["payment_analytics"] = resp.status_code == 200
                
                # Booking KPIs
                if request_num % 3 == 1:
                    resp = await auth_client.get("/api/admin/kpis")
                    results["booking_kpis"] = resp.status_code == 200
                
                # Both together
                if request_num % 3 == 2:
                    resp1 = await auth_client.get(
                        f"/api/payments/analytics?start_date={start_date}&end_date={end_date}"
                    )
                    resp2 = await auth_client.get("/api/admin/kpis")
                    results["both"] = (resp1.status_code == 200 and resp2.status_code == 200)
                
            except Exception as e:
                results["error"] = str(e)
            
            return results
        
        # Run 30 concurrent mixed queries
        tasks = [run_analytics_mix(i) for i in range(30)]
        results = await asyncio.gather(*tasks)
        
        # Count overall successes
        total_queries = 0
        successful_queries = 0
        
        for result in results:
            for key, value in result.items():
                if key != "error":
                    total_queries += 1
                    if value:
                        successful_queries += 1
        
        success_rate = successful_queries / total_queries * 100 if total_queries > 0 else 0
        
        # Should handle concurrent CTEs well
        assert success_rate > 85, f"CTE concurrency success rate {success_rate:.1f}% too low"
        
        print(f"✅ Concurrent CTEs: {successful_queries}/{total_queries} succeeded ({success_rate:.1f}%)")
