from sqlalchemy import create_engine, inspect
from src.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL_SYNC)
inspector = inspect(engine)

cols = inspector.get_columns('bookings', schema='core')
print('\ncore.bookings columns:')
for col in cols:
    print(f"  {col['name']}: {col['type']}")
