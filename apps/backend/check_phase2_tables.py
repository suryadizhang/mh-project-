"""Check if Phase 2A tables exist in ops schema"""

from sqlalchemy import create_engine, text
import sys

sys.path.insert(0, r"c:\Users\surya\projects\MH webapps\apps\backend\src")
from core.config import settings

# Convert async URL to sync URL for this check
sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
engine = create_engine(sync_url)

with engine.connect() as conn:
    result = conn.execute(
        text(
            "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'ops' ORDER BY tablename"
        )
    )
    tables = [row[0] for row in result]

    print(f"\n✓ ops schema tables ({len(tables)} total):")
    for table in tables:
        print(f"  - {table}")

    print("\n✓ Phase 2A Model Status:")
    print(
        f"  {'✅' if 'travel_zones' in tables else '❌'} TravelZone (travel_zones): {'EXISTS' if 'travel_zones' in tables else 'MISSING'}"
    )
    print(
        f"  {'✅' if 'menu_items' in tables else '❌'} MenuItem (menu_items): {'EXISTS' if 'menu_items' in tables else 'MISSING'}"
    )
    print(
        f"  {'✅' if 'pricing_rules' in tables else '❌'} PricingRule (pricing_rules): {'EXISTS' if 'pricing_rules' in tables else 'MISSING'}"
    )

    if all(t in tables for t in ["travel_zones", "menu_items", "pricing_rules"]):
        print("\n🎉 SUCCESS! All 3 Phase 2A tables exist!")
    else:
        print("\n❌ MISSING TABLES!")
