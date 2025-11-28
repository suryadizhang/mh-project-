"""Create Phase 2A tables via SQL"""

from sqlalchemy import create_engine, text
import sys

sys.path.insert(0, r"c:\Users\surya\projects\MH webapps\apps\backend\src")
from core.config import settings

# Read SQL file
with open(r"c:\Users\surya\projects\MH webapps\apps\backend\create_phase2_tables.sql", "r") as f:
    sql_script = f.read()

# Convert async URL to sync
sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
engine = create_engine(sync_url)

print("🔧 Creating Phase 2A tables...")
print("=" * 60)

try:
    with engine.connect() as conn:
        # Execute the entire SQL script
        print("\n📝 Executing SQL script...")
        conn.execute(text(sql_script))
        conn.commit()
        print("✅ SQL script executed successfully!")

        # Verify tables exist
        print("\n🔍 Verifying table creation...")
        result = conn.execute(
            text(
                """
            SELECT 'ops.travel_zones' AS table_name, COUNT(*) AS row_count FROM ops.travel_zones
            UNION ALL
            SELECT 'ops.menu_items', COUNT(*) FROM ops.menu_items
            UNION ALL
            SELECT 'ops.pricing_rules', COUNT(*) FROM ops.pricing_rules
        """
            )
        )

        print("\n✓ Table Status:")
        for row in result:
            print(f"  - {row[0]}: {row[1]} rows")

    print("\n" + "=" * 60)
    print("🎉 Phase 2A tables created successfully!")

except Exception as e:
    print(f"\n❌ Failed: {e}")
    raise
