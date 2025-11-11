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

print('=== Database Schema Check ===\n')
print('Available schemas:', inspector.get_schema_names())
print()

if 'newsletter' in inspector.get_schema_names():
    print('✅ newsletter schema exists')
    
    tables = inspector.get_table_names(schema='newsletter')
    print(f'Tables in newsletter schema: {tables}')
    print()
    
    if 'subscribers' in tables:
        print('✅ newsletter.subscribers table exists')
        print('\nColumns in newsletter.subscribers:')
        cols = inspector.get_columns('subscribers', schema='newsletter')
        for col in cols:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            print(f"  - {col['name']:30} {str(col['type']):20} {nullable}")
        
        col_names = [c['name'] for c in cols]
        print(f'\n🔍 Has updated_at column: {"✅ YES" if "updated_at" in col_names else "❌ NO"}')
        print(f'🔍 Has deleted_at column: {"✅ YES" if "deleted_at" in col_names else "❌ NO"}')
        print(f'🔍 Has created_at column: {"✅ YES" if "created_at" in col_names else "❌ NO"}')
    else:
        print('❌ newsletter.subscribers table NOT found')
else:
    print('❌ newsletter schema NOT found')

engine.dispose()
