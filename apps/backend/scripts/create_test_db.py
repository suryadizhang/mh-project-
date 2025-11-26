#!/usr/bin/env python3
"""Create test database for migration testing"""

from sqlalchemy import create_engine, text
from core.config import settings
import os

# Get sync DATABASE_URL
db_url = os.getenv("DATABASE_URL", str(settings.DATABASE_URL))
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

# Extract connection params
from urllib.parse import urlparse
parsed = urlparse(db_url)

# Connect to default 'postgres' database to create test database
admin_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/postgres"

engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

with engine.connect() as conn:
    # Drop existing test database
    conn.execute(text("DROP DATABASE IF EXISTS myhibachi_test_migrations"))
    print("🗑️  Dropped existing test database")

    # Create fresh test database
    conn.execute(text("CREATE DATABASE myhibachi_test_migrations"))
    print("✅ Created test database: myhibachi_test_migrations")

    # Print test DATABASE_URL
    test_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port or 5432}/myhibachi_test_migrations"
    print(f"\n📝 Test DATABASE_URL:\n   {test_url}")
