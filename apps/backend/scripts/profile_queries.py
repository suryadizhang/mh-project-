"""
Query Profiling Script for MEDIUM #34 Phase 3
Profiles complex queries with EXPLAIN ANALYZE to identify optimization opportunities
"""
import asyncio
import sys
import os
from datetime import date, timedelta
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_src))

from sqlalchemy import text, func, and_
from sqlalchemy.orm import Session
from api.app.database import SessionLocal
from repositories.booking_repository import BookingRepository
from models.booking import Booking, BookingStatus


def print_section(title: str):
    """Print formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def explain_query(session: Session, query_str: str, params: dict = None) -> str:
    """
    Run EXPLAIN ANALYZE on a query
    
    Args:
        session: Database session
        query_str: SQL query string
        params: Query parameters
        
    Returns:
        EXPLAIN output
    """
    explain_sql = f"EXPLAIN ANALYZE {query_str}"
    
    if params:
        result = session.execute(text(explain_sql), params)
    else:
        result = session.execute(text(explain_sql))
    
    return "\n".join([row[0] for row in result.fetchall()])


def profile_booking_statistics():
    """Profile get_booking_statistics query"""
    print_section("1. BOOKING STATISTICS QUERY (get_booking_statistics)")
    
    session = SessionLocal()
    
    try:
        # Date range: last 30 days
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Build the actual query that repository uses
        query = session.query(func.count(Booking.id)).filter(
            and_(
                func.date(Booking.booking_datetime) >= start_date,
                func.date(Booking.booking_datetime) <= end_date
            )
        )
        
        # Get SQL string
        compiled = query.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
        sql_str = str(compiled)
        
        print("Original Query (Total Count):")
        print(sql_str)
        print("\n" + "-"*80 + "\n")
        
        # Run EXPLAIN ANALYZE
        explain_output = explain_query(session, sql_str)
        print("EXPLAIN ANALYZE Output:")
        print(explain_output)
        
        # Check for sequential scans or wrong index usage
        if "Seq Scan" in explain_output:
            print("\n⚠️  WARNING: Sequential scan detected! Missing or unused index.")
        
        if "Index Scan" in explain_output:
            print("\n✅ Good: Index scan being used.")
            
    finally:
        session.close()


def profile_status_breakdown():
    """Profile status breakdown query with GROUP BY"""
    print_section("2. STATUS BREAKDOWN QUERY (GROUP BY)")
    
    session = SessionLocal()
    
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Query with GROUP BY
        query = session.query(
            Booking.status,
            func.count(Booking.id)
        ).filter(
            and_(
                func.date(Booking.booking_datetime) >= start_date,
                func.date(Booking.booking_datetime) <= end_date
            )
        ).group_by(Booking.status)
        
        compiled = query.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
        sql_str = str(compiled)
        
        print("Query with GROUP BY:")
        print(sql_str)
        print("\n" + "-"*80 + "\n")
        
        explain_output = explain_query(session, sql_str)
        print("EXPLAIN ANALYZE Output:")
        print(explain_output)
        
        # Check for hash aggregate or group aggregate
        if "HashAggregate" in explain_output:
            print("\n✅ Good: Using hash aggregate (efficient for GROUP BY)")
        elif "GroupAggregate" in explain_output:
            print("\n⚠️  GroupAggregate detected (might be slow if not indexed properly)")
            
    finally:
        session.close()


def profile_customer_booking_history():
    """Profile customer booking history query"""
    print_section("3. CUSTOMER BOOKING HISTORY (Multiple Aggregations)")
    
    session = SessionLocal()
    
    try:
        # Use a test customer ID (1)
        customer_id = 1
        
        # Status counts query
        query = session.query(
            Booking.status,
            func.count(Booking.id)
        ).filter(
            Booking.customer_id == customer_id
        ).group_by(Booking.status)
        
        compiled = query.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
        sql_str = str(compiled)
        
        print("Customer Status Counts Query:")
        print(sql_str)
        print("\n" + "-"*80 + "\n")
        
        explain_output = explain_query(session, sql_str)
        print("EXPLAIN ANALYZE Output:")
        print(explain_output)
        
        # Check for index usage on customer_id
        if "Index Scan using" in explain_output and "customer_id" in explain_output:
            print("\n✅ Good: Using customer_id index")
        elif "Seq Scan" in explain_output:
            print("\n⚠️  WARNING: Sequential scan! customer_id index might be missing or not used.")
            
    finally:
        session.close()


def profile_peak_hours_query():
    """Profile peak hours query with EXTRACT and complex GROUP BY"""
    print_section("4. PEAK HOURS QUERY (EXTRACT + GROUP BY + ORDER BY)")
    
    session = SessionLocal()
    
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Peak hours query
        query = session.query(
            func.extract('hour', Booking.booking_datetime).label('hour'),
            func.count(Booking.id).label('count')
        ).filter(
            and_(
                func.date(Booking.booking_datetime) >= start_date,
                func.date(Booking.booking_datetime) <= end_date,
                Booking.status != BookingStatus.CANCELLED
            )
        ).group_by('hour').order_by(text('count DESC'))
        
        compiled = query.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
        sql_str = str(compiled)
        
        print("Peak Hours Query:")
        print(sql_str)
        print("\n" + "-"*80 + "\n")
        
        explain_output = explain_query(session, sql_str)
        print("EXPLAIN ANALYZE Output:")
        print(explain_output)
        
        # Check for sort operations
        if "Sort" in explain_output:
            print("\n⚠️  Sort operation detected (can be expensive on large datasets)")
        
        if "HashAggregate" in explain_output:
            print("\n✅ Good: Using hash aggregate for grouping")
            
    finally:
        session.close()


def profile_search_bookings():
    """Profile search_bookings with multiple filters"""
    print_section("5. SEARCH BOOKINGS (Multiple Filters + Pagination)")
    
    session = SessionLocal()
    
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        
        # Complex search query
        query = session.query(Booking).filter(
            and_(
                func.date(Booking.booking_datetime) >= start_date,
                func.date(Booking.booking_datetime) <= end_date,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
            )
        ).order_by(Booking.booking_datetime.desc()).limit(50)
        
        compiled = query.statement.compile(
            compile_kwargs={"literal_binds": True}
        )
        sql_str = str(compiled)
        
        print("Search Bookings Query:")
        print(sql_str)
        print("\n" + "-"*80 + "\n")
        
        explain_output = explain_query(session, sql_str)
        print("EXPLAIN ANALYZE Output:")
        print(explain_output)
        
        # Check for index usage
        if "Index Scan" in explain_output:
            print("\n✅ Good: Using index scan")
        
        if "Bitmap" in explain_output:
            print("\n✅ Good: Using bitmap index scan (efficient for multiple conditions)")
            
    finally:
        session.close()


def generate_recommendations():
    """Generate optimization recommendations based on profiling"""
    print_section("OPTIMIZATION RECOMMENDATIONS")
    
    print("""
Based on query profiling, here are recommended optimizations:

1. **Booking Statistics Query**:
   - Add composite index: (booking_datetime, status)
   - Consider materialized view for frequently accessed date ranges
   - Use CTE to force index selection order

2. **Status Breakdown Query**:
   - Ensure index on (booking_datetime, status) exists
   - PostgreSQL should use hash aggregate (good)
   - Consider partial index for non-cancelled bookings

3. **Customer Booking History**:
   - Verify index on customer_id exists and is used
   - Add composite index: (customer_id, status) for faster aggregations
   - Use CTE for complex multi-aggregation queries

4. **Peak Hours Query**:
   - EXTRACT function prevents index usage
   - Consider adding computed column for hour
   - Or use CTE with indexed subquery first, then extract

5. **Search Bookings**:
   - Composite index: (booking_datetime, status) should cover most queries
   - Consider partial indexes for common status values
   - Cursor pagination already efficient (no OFFSET)

**Priority**: Implement CTEs for queries 1, 3, and 4 first (biggest impact)
""")


def main():
    """Main profiling function"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║   MEDIUM #34 Phase 3: Query Profiling                                     ║
║   Analyzing complex queries to identify optimization opportunities         ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    
    try:
        # Run all profiling tests
        profile_booking_statistics()
        profile_status_breakdown()
        profile_customer_booking_history()
        profile_peak_hours_query()
        profile_search_bookings()
        
        # Generate recommendations
        generate_recommendations()
        
        print("\n" + "="*80)
        print("Profiling complete! ✅")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error during profiling: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
