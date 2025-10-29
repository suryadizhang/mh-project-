"""
Database Module - Consolidated
Unified database configuration, session management, and connection pooling
Single source of truth for all database operations across MyHibachi backend

Consolidated from:
- api/app/database.py (main async database with SQLAlchemy)
- api/ai/endpoints/database.py (simple sync database for AI)

Provides both async and sync database sessions for different use cases:
- Async sessions for FastAPI endpoints (recommended)
- Sync sessions for scripts, migrations, and workers
"""
import logging
import os
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager

from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# =============================================================================
# BASE MODEL
# =============================================================================

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


# =============================================================================
# ASYNC DATABASE (Primary - for FastAPI endpoints)
# =============================================================================

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

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.
    
    Usage in FastAPI:
    ```python
    @router.get("/items")
    async def get_items(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Item))
        return result.scalars().all()
    ```
    """
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
    
    Usage in workers/scripts:
    ```python
    async with get_db_context() as db:
        result = await db.execute(select(Item))
        items = result.scalars().all()
    ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_async_session() -> AsyncSession:
    """
    Get async session directly (not as generator).
    Remember to close the session manually!
    
    Usage:
    ```python
    session = await get_async_session()
    try:
        result = await session.execute(select(Item))
        await session.commit()
    finally:
        await session.close()
    ```
    """
    return AsyncSessionLocal()


# =============================================================================
# SYNC DATABASE (for migrations, scripts, and legacy code)
# =============================================================================

# Sync engine for Alembic migrations and scripts
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
)

# Sync session maker for migrations
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine
)


def get_sync_db() -> Generator[Session, None, None]:
    """
    Sync database session for migrations and scripts.
    
    Usage in scripts:
    ```python
    for db in get_sync_db():
        result = db.execute(text("SELECT * FROM items"))
        items = result.fetchall()
    ```
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_sync_session() -> Session:
    """
    Get sync session directly.
    Remember to close the session manually!
    
    Usage:
    ```python
    session = get_sync_session()
    try:
        result = session.execute(text("SELECT * FROM items"))
        session.commit()
    finally:
        session.close()
    ```
    """
    return SessionLocal()


# =============================================================================
# DATABASE LIFECYCLE MANAGEMENT
# =============================================================================

async def init_database():
    """
    Initialize database connection on startup.
    Tests the connection and logs status.
    
    Usage in FastAPI lifespan:
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_database()
        yield
        await close_database()
    ```
    """
    try:
        # Test database connection
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        
        logger.info(f"✅ Async database connected: {settings.database_url}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to async database: {e}")
        raise


async def close_database():
    """
    Close database connections on shutdown.
    Disposes of the connection pool.
    """
    try:
        await engine.dispose()
        logger.info("✅ Async database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing async database connections: {e}")


def init_db():
    """
    Initialize database tables (sync version).
    Creates all tables defined in Base.metadata.
    
    ⚠️ WARNING: Only use for development/testing!
    Use Alembic migrations for production.
    
    Usage:
    ```python
    init_db()  # Creates all tables
    ```
    """
    try:
        Base.metadata.create_all(bind=sync_engine)
        logger.info("✅ Database tables created (sync)")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


def close_db():
    """
    Close sync database connections.
    Disposes of the sync connection pool.
    """
    try:
        sync_engine.dispose()
        logger.info("✅ Sync database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing sync database connections: {e}")


# =============================================================================
# DATABASE CONFIGURATION HELPER
# =============================================================================

class DatabaseConfig:
    """
    Database configuration helper class.
    Provides easy access to engines and session factories.
    
    Usage:
    ```python
    from core.database import db_config
    
    # Get async engine
    engine = db_config.async_engine
    
    # Get session factory
    SessionFactory = db_config.async_session_factory
    ```
    """

    @property
    def async_engine(self) -> AsyncEngine:
        """Get async SQLAlchemy engine"""
        return engine

    @property
    def sync_engine(self):
        """Get sync SQLAlchemy engine"""
        return sync_engine

    @property
    def async_session_factory(self):
        """Get async session factory"""
        return AsyncSessionLocal

    @property
    def sync_session_factory(self):
        """Get sync session factory"""
        return SessionLocal
    
    def get_database_url(self, async_url: bool = True) -> str:
        """Get database URL (async or sync)"""
        return settings.database_url if async_url else settings.database_url_sync
    
    def get_pool_stats(self) -> dict:
        """Get connection pool statistics"""
        return {
            "async_pool_size": engine.pool.size(),
            "async_checked_out": engine.pool.checkedout(),
            "sync_pool_size": sync_engine.pool.size(),
            "sync_checked_out": sync_engine.pool.checkedout(),
        }


# Global database config instance
db_config = DatabaseConfig()


# =============================================================================
# HEALTH CHECK
# =============================================================================

async def check_database_health() -> dict:
    """
    Check database health and return status.
    
    Returns:
        dict: Health status with connection details
        
    Usage:
    ```python
    status = await check_database_health()
    if status["healthy"]:
        print("Database is healthy!")
    ```
    """
    try:
        async with AsyncSessionLocal() as session:
            start_time = __import__('time').time()
            await session.execute(text("SELECT 1"))
            response_time = __import__('time').time() - start_time
            
        pool_stats = db_config.get_pool_stats()
        
        return {
            "healthy": True,
            "database": "postgresql",
            "response_time_ms": round(response_time * 1000, 2),
            "pool_size": pool_stats["async_pool_size"],
            "connections_in_use": pool_stats["async_checked_out"],
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "healthy": False,
            "error": str(e)
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Base
    "Base",
    
    # Async database (primary)
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "get_db_session",
    "get_db_context",
    "get_async_session",
    
    # Sync database (migrations/scripts)
    "sync_engine",
    "SessionLocal",
    "get_sync_db",
    "get_sync_session",
    
    # Lifecycle
    "init_database",
    "close_database",
    "init_db",
    "close_db",
    
    # Configuration
    "db_config",
    "DatabaseConfig",
    
    # Health
    "check_database_health",
]
