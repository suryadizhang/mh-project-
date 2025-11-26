"""Check actual columns in core.customers table"""
from sqlalchemy import create_engine, inspect
import sys
sys.path.insert(0, "src")
from core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL_SYNC)
inspector = inspect(engine)

cols = inspector.get_columns('customers', schema='core')
print('\ncore.customers columns:')
for col in cols:
    print(f"  {col['name']}: {col['type']}")
