"""
Test suite for query optimizer CTE queries.

This module tests:
- CTE query generation
- Parameter handling
- Query structure validation
- Performance expectations

Tests validate logic without requiring database connection.
"""
import sys
from pathlib import Path

# Add src directory to path for imports
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))

from datetime import datetime, timedelta
from typing import Dict, Any


def test_payment_analytics_cte_generation():
    """Test payment analytics CTE query generation."""
    from utils.query_optimizer import QueryOptimizer
    
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 1, 31)
    station_id = "station-123"
    
    # Generate CTE query
    query, params = QueryOptimizer.build_payment_analytics_cte(
        start_date=start_date,
        end_date=end_date,
        station_id=station_id,
    )
    
    # Validate query structure
    assert "WITH payment_base AS MATERIALIZED" in query
    assert "method_aggregates AS" in query
    assert "overall_stats AS" in query
    assert "monthly_breakdown AS" in query
    
    # Validate filtering
    assert "WHERE p.created_at >=" in query
    assert "AND p.created_at <=" in query
    assert "AND p.status = 'succeeded'" in query
    assert "AND p.station_id = :station_id" in query
    
    # Validate parameters
    assert params["start_date"] == start_date
    assert params["end_date"] == end_date
    assert params["station_id"] == station_id
    
    # Validate aggregations
    assert "COUNT(*)" in query
    assert "SUM(amount)" in query
    assert "AVG(amount)" in query
    assert "GROUP BY method" in query
    
    # Validate JSON output
    assert "json_agg" in query
    assert "json_build_object" in query
    
    print("✅ Payment analytics CTE generation PASSED")
    return True


def test_payment_analytics_cte_without_station():
    """Test payment analytics CTE without station filter."""
    from utils.query_optimizer import QueryOptimizer
    
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 1, 31)
    
    # Generate CTE query without station_id
    query, params = QueryOptimizer.build_payment_analytics_cte(
        start_date=start_date,
        end_date=end_date,
        station_id=None,
    )
    
    # Validate no station filter
    assert "AND p.station_id" not in query
    assert "station_id" not in params
    
    # Validate other parameters still present
    assert params["start_date"] == start_date
    assert params["end_date"] == end_date
    
    print("✅ Payment analytics CTE without station PASSED")
    return True


def test_booking_kpi_cte_generation():
    """Test booking KPI CTE query generation."""
    from utils.query_optimizer import QueryOptimizer
    
    station_id = "station-456"
    
    # Generate CTE query
    query, params = QueryOptimizer.build_booking_kpi_cte(
        station_id=station_id,
    )
    
    # Validate query structure
    assert "WITH booking_base AS MATERIALIZED" in query
    assert "time_based_counts AS" in query
    assert "revenue_stats AS" in query
    assert "upcoming_bookings AS" in query
    
    # Validate filtering
    assert "WHERE 1=1" in query
    assert "AND b.station_id = :station_id" in query
    
    # Validate parameters
    assert "week_start" in params
    assert "month_start" in params
    assert "now" in params
    assert params["station_id"] == station_id
    
    # Validate date calculations
    assert isinstance(params["week_start"], datetime)
    assert isinstance(params["month_start"], datetime)
    
    # Validate FILTER clauses (PostgreSQL aggregation)
    assert "COUNT(*) FILTER" in query
    assert "WHERE created_at >= :week_start" in query
    assert "WHERE created_at >= :month_start" in query
    
    # Validate revenue calculations
    assert "SUM(total_amount)" in query
    assert "SUM(balance_due)" in query
    assert "AVG(total_amount)" in query
    assert "COALESCE" in query
    
    # Validate status filtering
    assert "status = 'confirmed'" in query
    assert "status = 'cancelled'" in query
    assert "status = 'pending'" in query
    
    print("✅ Booking KPI CTE generation PASSED")
    return True


def test_customer_analytics_cte_generation():
    """Test customer analytics CTE query generation."""
    from utils.query_optimizer import QueryOptimizer
    
    customer_email = "customer@example.com"
    station_id = "station-789"
    
    # Generate CTE query
    query, params = QueryOptimizer.build_customer_analytics_cte(
        customer_email=customer_email,
        station_id=station_id,
    )
    
    # Validate query structure
    assert "WITH customer_bookings AS MATERIALIZED" in query
    assert "booking_stats AS" in query
    assert "payment_methods AS" in query
    
    # Validate filtering
    assert "WHERE b.customer_email = :customer_email" in query
    assert "AND b.station_id = :station_id" in query
    
    # Validate parameters
    assert params["customer_email"] == customer_email
    assert params["station_id"] == station_id
    
    # Validate aggregations
    assert "COUNT(*)" in query
    assert "COUNT(*) FILTER (WHERE status = 'completed')" in query
    assert "COUNT(*) FILTER (WHERE status = 'cancelled')" in query
    assert "SUM(total_amount)" in query
    assert "AVG(total_amount)" in query
    assert "MAX(created_at)" in query
    assert "MIN(created_at)" in query
    
    # Validate JOIN for payment methods
    assert "JOIN payments p ON p.booking_id = cb.id" in query
    assert "WHERE p.status = 'succeeded'" in query
    assert "GROUP BY p.method" in query
    
    # Validate customer lifetime calculation
    assert "EXTRACT(EPOCH FROM" in query
    assert "/ 86400" in query  # Convert seconds to days
    
    print("✅ Customer analytics CTE generation PASSED")
    return True


def test_query_parameter_sanitization():
    """Test that parameters are properly sanitized."""
    from utils.query_optimizer import QueryOptimizer
    
    # Test with potentially dangerous input
    malicious_email = "'; DROP TABLE bookings; --"
    
    query, params = QueryOptimizer.build_customer_analytics_cte(
        customer_email=malicious_email,
        station_id="station-123",
    )
    
    # Validate parameterized query (not string interpolation)
    # Parameters should be in params dict, not in query string
    assert malicious_email not in query
    assert params["customer_email"] == malicious_email
    
    # Validate all filters use parameterized queries
    assert ":customer_email" in query
    assert ":station_id" in query
    
    print("✅ Query parameter sanitization PASSED (SQL injection protected)")
    return True


def test_cte_materialization_hints():
    """Test that CTEs use MATERIALIZED hint for PostgreSQL."""
    from utils.query_optimizer import QueryOptimizer
    
    # Test payment analytics
    query1, _ = QueryOptimizer.build_payment_analytics_cte(
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 1, 31),
    )
    assert "AS MATERIALIZED" in query1
    
    # Test booking KPIs
    query2, _ = QueryOptimizer.build_booking_kpi_cte()
    assert "AS MATERIALIZED" in query2
    
    # Test customer analytics
    query3, _ = QueryOptimizer.build_customer_analytics_cte(
        customer_email="test@example.com"
    )
    assert "AS MATERIALIZED" in query3
    
    print("✅ CTE materialization hints PASSED (PostgreSQL optimization)")
    return True


def test_date_boundary_calculations():
    """Test date boundary calculations for week/month."""
    from utils.query_optimizer import QueryOptimizer
    
    # Generate KPI query
    _, params = QueryOptimizer.build_booking_kpi_cte()
    
    # Validate week_start is Monday
    week_start = params["week_start"]
    assert week_start.weekday() == 0, f"Week start should be Monday, got {week_start.weekday()}"
    
    # Validate month_start is first day of month
    month_start = params["month_start"]
    assert month_start.day == 1, f"Month start should be day 1, got {month_start.day}"
    assert month_start.hour == 0
    assert month_start.minute == 0
    assert month_start.second == 0
    
    print("✅ Date boundary calculations PASSED")
    return True


def test_join_order_optimization():
    """Test join order optimization suggestion."""
    from utils.query_optimizer import QueryOptimizer
    
    base_table = "bookings"
    join_tables = ["customers", "payments", "stations"]
    estimated_rows = {
        "bookings": 10000,
        "customers": 5000,
        "payments": 15000,
        "stations": 10,  # Smallest
    }
    
    # Get optimized join order
    optimal_order = QueryOptimizer.optimize_join_order(
        base_table=base_table,
        join_tables=join_tables,
        estimated_rows=estimated_rows,
    )
    
    # Validate base table is first
    assert optimal_order[0] == "bookings"
    
    # Validate smallest table (stations) is joined first
    assert optimal_order[1] == "stations"
    
    # Validate tables are sorted by size
    assert optimal_order == ["bookings", "stations", "customers", "payments"]
    
    print("✅ Join order optimization PASSED")
    return True


def run_all_tests():
    """Run all CTE query tests."""
    print("\n" + "="*60)
    print("RUNNING CTE QUERY OPTIMIZER TESTS")
    print("="*60 + "\n")
    
    tests = [
        test_payment_analytics_cte_generation,
        test_payment_analytics_cte_without_station,
        test_booking_kpi_cte_generation,
        test_customer_analytics_cte_generation,
        test_query_parameter_sanitization,
        test_cte_materialization_hints,
        test_date_boundary_calculations,
        test_join_order_optimization,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! Query optimizer CTEs are correct.\n")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Review implementation.\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
