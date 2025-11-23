#!/usr/bin/env python3
"""List all tables per schema for model generation"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_settings
import psycopg2

settings = get_settings()
db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Get tables per schema
schemas = ['core', 'identity', 'lead', 'newsletter', 'feedback', 'events', 'integra', 'marketing', 'support', 'communications']

print("="*80)
print("DATABASE TABLES BY SCHEMA")
print("="*80)

total = 0
for schema in schemas:
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """, (schema,))

    tables = [row[0] for row in cur.fetchall()]
    total += len(tables)

    print(f"\n{schema.upper()} schema: {len(tables)} tables")
    for table in tables:
        print(f"  - {table}")

print(f"\n{'='*80}")
print(f"TOTAL: {total} tables across {len(schemas)} schemas")
print("="*80)

conn.close()
