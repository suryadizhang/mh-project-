"""
Database configuration and session management for MyHibachi AI Backend
"""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base

# Database URL from environment
DATABASE_URL = os.getenv("SYNC_DATABASE_URL", "sqlite:///./ai_chat.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def close_db():
    """Close database connections"""
    engine.dispose()
