"""Manually merge Alembic heads"""
from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres')
conn = engine.connect()

# Check current versions
print("Current versions in alembic_version:")
result = conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
for row in result:
    print(f"  - {row[0]}")

# Delete the three branch heads
print("\nDeleting branch heads...")
conn.execute(text("DELETE FROM alembic_version WHERE version_num IN ('004_station_rbac', '008_add_user_roles', 'ea9069521d16')"))

# Insert the merge head
print("Inserting merge head...")
conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('06fc7e9891b1')"))

conn.commit()

# Verify
print("\nNew version in alembic_version:")
result = conn.execute(text("SELECT version_num FROM alembic_version ORDER BY version_num"))
for row in result:
    print(f"  - {row[0]}")

print("\n✓ Successfully merged heads to 06fc7e9891b1")
conn.close()
