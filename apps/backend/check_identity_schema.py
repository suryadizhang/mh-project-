"""Check if identity schema exists."""
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://user:password@localhost:5432/myhibachi_crm"

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
