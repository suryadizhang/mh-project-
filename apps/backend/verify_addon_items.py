"""Quick verification script for addon_items table"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL_SYNC"))
conn = engine.connect()

print("📊 addon_items table contents:\n")
result = conn.execute(text("SELECT name, category, price FROM addon_items ORDER BY display_order"))
for row in result:
    print(f"  {row.name:30s} | {row.category:20s} | ${row.price:6.2f}")

print()
result2 = conn.execute(text("SELECT COUNT(*) FROM menu_items"))
print(f"menu_items count: {result2.scalar()}")

conn.close()
