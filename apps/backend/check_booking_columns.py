"""Check actual database schema for bookings table"""
from sqlalchemy import inspect, create_engine
import sys
sys.path.insert(0, "src")
from core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
inspector = inspect(engine)

print("=== BOOKINGS TABLE COLUMNS (core.bookings) ===\n")
columns = inspector.get_columns('bookings', schema='core')
for col in columns:
    nullable = "NULL" if col['nullable'] else "NOT NULL"
    print(f"{col['name']}: {col['type']} {nullable}")

print("\n=== CHECK CONSTRAINTS ===\n")
constraints = inspector.get_check_constraints('bookings', schema='core')
for constraint in constraints:
    print(f"{constraint['name']}: {constraint['sqltext']}")

print("\n=== INDEXES ===\n")
indexes = inspector.get_indexes('bookings', schema='core')
for idx in indexes:
    print(f"{idx['name']}: {idx['column_names']}")
