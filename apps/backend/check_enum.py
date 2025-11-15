"""Check database enum values"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL_SYNC"))

with engine.connect() as conn:
    # Check leadsource enum
    result = conn.execute(
        text(
            """
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'leadsource')
        ORDER BY enumsortorder
    """
        )
    )

    print("=== Database 'leadsource' enum values ===")
    for row in result:
        print(f"  - {row[0]}")

    # Check lead_source enum (alternative name)
    result2 = conn.execute(
        text(
            """
        SELECT enumlabel 
        FROM pg_enum 
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'lead_source')
        ORDER BY enumsortorder
    """
        )
    )

    print("\n=== Database 'lead_source' enum values ===")
    for row in result2:
        print(f"  - {row[0]}")
