"""Audit all database tables and their schemas"""
import sys
sys.path.insert(0, "src")

from sqlalchemy import create_engine, inspect
from core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL_SYNC)
inspector = inspect(engine)

# Get all schemas
schemas = inspector.get_schema_names()
print(f"\n{'='*80}")
print(f"DATABASE SCHEMAS: {', '.join(schemas)}")
print(f"{'='*80}")

# For each schema, list tables
for schema in ['core', 'identity', 'public']:
    try:
        tables = inspector.get_table_names(schema=schema)
        if tables:
            print(f"\n{schema.upper()} SCHEMA ({len(tables)} tables):")
            print("-" * 80)
            for table in sorted(tables):
                cols = inspector.get_columns(table, schema=schema)
                print(f"\n  {schema}.{table} ({len(cols)} columns):")
                for col in cols[:5]:  # First 5 columns only
                    print(f"    - {col['name']}: {col['type']}")
                if len(cols) > 5:
                    print(f"    ... and {len(cols) - 5} more columns")
    except Exception as e:
        print(f"\n{schema.upper()} SCHEMA: Error - {e}")

print(f"\n{'='*80}")
print("AUDIT COMPLETE")
print(f"{'='*80}\n")
