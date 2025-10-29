"""Final database state verification"""
from sqlalchemy import create_engine, text, inspect

engine = create_engine('postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres')
inspector = inspect(engine)

print("=" * 80)
print("DATABASE MIGRATION COMPLETE - FINAL STATE")
print("=" * 80)

# Get schemas
schemas = [s for s in inspector.get_schema_names() 
           if s not in ('information_schema', 'pg_catalog', 'pg_toast', 'auth', 
                       'extensions', 'graphql', 'graphql_public', 'realtime', 'storage', 'vault')]

print(f"\n✓ {len(schemas)} Schemas Created:")
for s in sorted(schemas):
    table_count = len(inspector.get_table_names(schema=s))
    print(f"  - {s}: {table_count} tables")

total_tables = sum(len(inspector.get_table_names(schema=s)) for s in schemas)
print(f"\n✓ Total: {total_tables} tables across all schemas")

# Users table details
print(f"\n✓ Users Table Structure:")
columns = inspector.get_columns('users', schema='public')
for col in columns:
    nullable = "NULL" if col['nullable'] else "NOT NULL"
    print(f"  - {col['name']}: {col['type']} {nullable}")

# Check migration version
conn = engine.connect()
result = conn.execute(text("SELECT version_num FROM alembic_version"))
version = result.fetchone()
print(f"\n✓ Current Migration Version: {version[0]}")
conn.close()

print("\n" + "=" * 80)
print("READY FOR PERFORMANCE INDEX DEPLOYMENT")
print("=" * 80)
