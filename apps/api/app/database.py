import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models with consistent naming convention."""

    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )


# Import all models for metadata discovery
# This must be done after Base is defined but before engine creation

# Async engine for async operations
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
)

# Sync engine for Alembic migrations
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Sync session maker for migrations
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for consistency with auth module expectations
get_db_session = get_db


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session as context manager.
    This version can be used in non-FastAPI contexts like workers.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_sync_db():
    """Sync database session for migrations and scripts."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_database():
    """Initialize database connection on startup."""
    try:
        # Test database connection
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")

        logger.info(f"Database connected successfully: {settings.database_url}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def close_database():
    """Close database connections on shutdown."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Database configuration instance for direct access
class DatabaseConfig:
    """Database configuration helper class."""

    @property
    def async_engine(self) -> AsyncEngine:
        return engine

    @property
    def sync_engine(self):
        return sync_engine

    @property
    def async_session_factory(self):
        return AsyncSessionLocal

    @property
    def sync_session_factory(self):
        return SessionLocal


db_config = DatabaseConfig()
