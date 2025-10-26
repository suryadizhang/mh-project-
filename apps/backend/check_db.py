import psycopg2

conn = psycopg2.connect('postgresql://user:password@localhost:5432/myhibachi_crm')
cursor = conn.cursor()

# Get all schemas
cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('pg_catalog', 'information_schema')")
schemas = [r[0] for r in cursor.fetchall()]
print('Schemas:', schemas)

# Check for all custom enums
cursor.execute("""
    SELECT n.nspname as schema, t.typname as enum_name
    FROM pg_type t 
    JOIN pg_namespace n ON t.typnamespace = n.oid
    WHERE t.typtype = 'e'
    AND n.nspname IN ('feedback', 'marketing', 'public')
    ORDER BY n.nspname, t.typname
""")
enums = cursor.fetchall()
print('\nCustom enums:')
for enum in enums:
    print(f'  {enum[0]}.{enum[1]}')

# Check core tables
cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'core'")
core_tables = [r[0] for r in cursor.fetchall()]
print('\nCore tables:', core_tables)

# Check if feedback schema exists
cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'feedback')")
feedback_exists = cursor.fetchone()[0]
print('\nFeedback schema exists:', feedback_exists)

if feedback_exists:
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'feedback'")
    feedback_tables = [r[0] for r in cursor.fetchall()]
    print('Feedback tables:', feedback_tables)

# Check if marketing schema exists
cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = 'marketing')")
marketing_exists = cursor.fetchone()[0]
print('\nMarketing schema exists:', marketing_exists)

if marketing_exists:
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'marketing'")
    marketing_tables = [r[0] for r in cursor.fetchall()]
    print('Marketing tables:', marketing_tables)

# Check alembic version
cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'alembic_version')")
alembic_exists = cursor.fetchone()[0]
print('\nAlembic version table exists:', alembic_exists)

if alembic_exists:
    cursor.execute("SELECT version_num FROM alembic_version")
    versions = [r[0] for r in cursor.fetchall()]
    print('Applied migrations:', versions)

conn.close()
