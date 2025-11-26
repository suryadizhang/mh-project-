from sqlalchemy import create_engine, inspect
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Use sync URL for inspection
db_url = os.getenv('DATABASE_URL_SYNC', 'postgresql+psycopg2://postgres:DkYokZB945vm3itM@db.yuchqvpctookhjovvdwi.supabase.co:5432/postgres')
print(f'Connecting to: {db_url.split("@")[0]}@...') # Hide password
engine = create_engine(db_url)
inspector = inspect(engine)

print('=== IDENTITY SCHEMA ANALYSIS ===\n')

if 'identity' in inspector.get_schema_names():
    print('✅ identity schema exists')

    tables = inspector.get_table_names(schema='identity')
    print(f'\nTables in identity schema: {tables}\n')

    # Check critical tables for User model conflicts
    critical_tables = ['users', 'station_users', 'auth_users', 'user_station_assignments']

    for table in critical_tables:
        if table in tables:
            print(f'{"="*70}')
            print(f'TABLE: identity.{table}')
            print(f'{"="*70}')
            cols = inspector.get_columns(table, schema='identity')
            print(f'Columns ({len(cols)}):')
            for col in cols:
                nullable = "NULL" if col['nullable'] else "NOT NULL"
                print(f"  {col['name']:30} {str(col['type']):20} {nullable}")

            # Check foreign keys
            fks = inspector.get_foreign_keys(table, schema='identity')
            if fks:
                print(f'\nForeign Keys:')
                for fk in fks:
                    print(f"  {fk['constrained_columns']} -> {fk['referred_schema']}.{fk['referred_table']}.{fk['referred_columns']}")
            print()
        else:
            print(f'❌ identity.{table} does NOT exist\n')
else:
    print('❌ identity schema NOT found')

engine.dispose()
