import sys
sys.path.insert(0, 'src')

from sqlalchemy import create_engine, text
from core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text('SELECT current_user'))
    print(f'Current DB user: {result.scalar()}')
