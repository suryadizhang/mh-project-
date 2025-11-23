#!/usr/bin/env python3
"""Check for duplicate migration files"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import get_settings
import psycopg2

settings = get_settings()

# Convert async URL to sync
db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Check what revision is actually in the database
cur.execute("SELECT version_num FROM alembic_version")
current = cur.fetchone()[0]

print(f"Database is at: {current}")

# List all migration files
versions_dir = Path(__file__).parent.parent / "src" / "db" / "migrations" / "alembic" / "versions"

files = {}
for f in versions_dir.glob("*.py"):
    if f.name == "__init__.py":
        continue

    # Read revision ID from file
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
        for line in content.split('\n'):
            if line.startswith("revision = "):
                rev = line.split("=")[1].strip().strip("'\"")
                if rev not in files:
                    files[rev] = []
                files[rev].append(f.name)
                break

# Find duplicates
duplicates = {k: v for k, v in files.items() if len(v) > 1}

if duplicates:
    print("\n❌ DUPLICATE REVISION IDs FOUND:\n")
    for rev, filenames in duplicates.items():
        print(f"Revision {rev}:")
        for fname in filenames:
            print(f"  - {fname}")
        print()
else:
    print("\n✅ No duplicate revision IDs found")

conn.close()
