#!/usr/bin/env python3
"""Check database state vs Alembic migrations"""

from sqlalchemy import create_engine, inspect, text
from core.config import settings
import os

# Get sync DATABASE_URL (Alembic uses psycopg2)
db_url = os.getenv("DATABASE_URL", str(settings.DATABASE_URL))
# Convert async URL to sync if needed
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

engine = create_engine(db_url)

with engine.connect() as conn:
    # Get all tables
    tables = inspect(engine).get_table_names()

    # Check KB tables
    kb_tables = [
        'business_rules', 'faq_items', 'training_data',
        'upsell_rules', 'seasonal_offers', 'availability_calendar',
        'customer_tone_preferences'
    ]

    existing_kb = [t for t in kb_tables if t in tables]

    print("\nKnowledge Base Tables Status:")
    print("=" * 50)
    for table in kb_tables:
        status = "✅ EXISTS" if table in tables else "❌ MISSING"
        print(f"{table:30} {status}")

    # Check Alembic version
    result = conn.execute(text('SELECT version_num FROM alembic_version'))
    version = result.scalar()

    print(f"\n\nAlembic Version: {version}")
    print("\nDiagnosis:")
    if existing_kb:
        print(f"⚠️  Found {len(existing_kb)} KB tables already in database")
        print(f"   Tables exist: {', '.join(existing_kb)}")
        print(f"   This means:")
        print(f"   1. Tables were created manually (not via Alembic), OR")
        print(f"   2. Migration was partially applied, OR")
        print(f"   3. Alembic version table is out of sync")
        print(f"\n   SOLUTION: Mark migration bd8856cf6aa0 as applied WITHOUT running it")
    else:
        print("✅ No KB tables found - safe to run migration")
