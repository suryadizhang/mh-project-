"""Verify database state for MenuAgent"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL_SYNC"))
conn = engine.connect()

r1 = conn.execute(text("SELECT COUNT(*) FROM menu_items"))
r2 = conn.execute(text("SELECT COUNT(*) FROM addon_items"))
print("Database status:")
print(f"  menu_items: {r1.scalar()} rows")
print(f"  addon_items: {r2.scalar()} rows")
print()
print("MenuAgent will load:")
r3 = conn.execute(
    text(
        "SELECT name, base_price FROM menu_items WHERE is_available = true ORDER BY display_order LIMIT 5"
    )
)
for row in r3:
    price_str = f"${float(row.base_price):.2f}" if row.base_price else "$0.00"
    print(f"  - {row.name} ({price_str})")

conn.close()
