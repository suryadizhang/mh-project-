"""Check if identity schema exists."""
import os
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL environment variable is required")
    print("   Set it in your apps/backend/.env file")
    sys.exit(1)

engine = create_engine(DATABASE_URL)
conn = engine.connect()
result = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'identity'"))
schemas = list(result)
print(f"Identity schema exists: {len(schemas) > 0}")
if not schemas:
    print("Creating identity schema...")
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS identity"))
    conn.execute(text("GRANT ALL ON SCHEMA identity TO PUBLIC"))
    conn.commit()
    print("✅ Identity schema created!")
conn.close()
