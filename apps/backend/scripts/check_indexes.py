"""
Database Index Checker for MEDIUM #34 Phase 3
Checks existing indexes and recommends new ones for query optimization
"""
import sys
from pathlib import Path

# Add backend src to path
backend_src = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(backend_src))

from sqlalchemy import text, inspect
from api.app.database import SessionLocal


def check_existing_indexes():
    """Check what indexes currently exist on bookings table"""
    session = SessionLocal()
    
    try:
        # Query PostgreSQL system catalogs for indexes
        query = text("""
            SELECT
                i.relname AS index_name,
                a.attname AS column_name,
                ix.indisunique AS is_unique,
                ix.indisprimary AS is_primary
            FROM
                pg_class t,
                pg_class i,
                pg_index ix,
                pg_attribute a
            WHERE
                t.oid = ix.indrelid
                AND i.oid = ix.indexrelid
                AND a.attrelid = t.oid
                AND a.attnum = ANY(ix.indkey)
                AND t.relkind = 'r'
                AND t.relname = 'bookings'
            ORDER BY
                i.relname,
                a.attnum;
        """)
        
        result = session.execute(query)
        
        print("="*80)
        print("EXISTING INDEXES ON BOOKINGS TABLE")
        print("="*80 + "\n")
        
        current_index = None
        columns = []
        
        for row in result:
            index_name, column_name, is_unique, is_primary = row
            
            if index_name != current_index:
                if current_index:
                    print(f"  Columns: {', '.join(columns)}")
                    columns = []
                
                print(f"\n{index_name}")
                print(f"  Type: {'PRIMARY KEY' if is_primary else 'UNIQUE' if is_unique else 'INDEX'}")
                current_index = index_name
            
            columns.append(column_name)
        
        if columns:
            print(f"  Columns: {', '.join(columns)}")
        
        print("\n" + "="*80)
        print("RECOMMENDED INDEXES FOR OPTIMIZATION")
        print("="*80 + "\n")
        
        recommendations = [
            {
                "name": "idx_bookings_datetime_status",
                "columns": ["booking_datetime", "status"],
                "reason": "Speeds up date range queries with status filtering (dashboard stats, search)",
                "sql": "CREATE INDEX idx_bookings_datetime_status ON bookings(booking_datetime, status);"
            },
            {
                "name": "idx_bookings_customer_status",
                "columns": ["customer_id", "status"],
                "reason": "Speeds up customer history queries with status aggregations",
                "sql": "CREATE INDEX idx_bookings_customer_status ON bookings(customer_id, status);"
            },
            {
                "name": "idx_bookings_status_datetime",
                "columns": ["status", "booking_datetime"],
                "reason": "Speeds up status-first queries (e.g., find all confirmed bookings in date range)",
                "sql": "CREATE INDEX idx_bookings_status_datetime ON bookings(status, booking_datetime);"
            },
            {
                "name": "idx_bookings_datetime_partial_active",
                "columns": ["booking_datetime"],
                "reason": "Partial index for active bookings (smaller, faster)",
                "sql": "CREATE INDEX idx_bookings_datetime_partial_active ON bookings(booking_datetime) WHERE status IN ('confirmed', 'pending', 'seated');"
            }
        ]
        
        for rec in recommendations:
            print(f"\n{rec['name']}")
            print(f"  Columns: {', '.join(rec['columns'])}")
            print(f"  Reason: {rec['reason']}")
            print(f"  SQL: {rec['sql']}")
        
        print("\n" + "="*80 + "\n")
        
    finally:
        session.close()


if __name__ == "__main__":
    check_existing_indexes()
