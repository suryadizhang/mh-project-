import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add src directory to path (go up from alembic/versions to src)
backend_src = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if backend_src not in sys.path:
    sys.path.insert(0, backend_src)

# Import after path manipulation to avoid import errors
from core.config import get_settings  # noqa: E402

settings = get_settings()

# Import Base without importing async engine
# Use models.base instead of api.app.database to avoid async engine creation
from models.base import Base  # noqa: E402

# Import all models for Alembic discovery
# Import models so Alembic can detect tables
from models import (  # noqa: E402, F401
    # Core models
    Booking,
    Customer,
    Review,
    Lead,
    Campaign,
    # Social media & communications
    SocialAccount,
    SocialIdentity,
    SocialThread,
    SocialMessage,
    # RingCentral communications (call recordings, SMS)
    CallRecording,
    # Event sourcing
    DomainEvent,
    OutboxEntry,
    # Business & multi-tenancy
    Business,
    # Customer support
    Escalation,
    # Payment processing
    PaymentNotification,
    # RBAC
    Role,
    Permission,
    # System events & audit
    SystemEvent,
    # Terms & conditions
    TermsAcknowledgment,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override the database URL from settings
# Use environment variable or settings
# Convert async database URL to sync for Alembic
database_url = os.getenv("DATABASE_URL_SYNC", settings.database_url_sync)
if not database_url:
    # If no sync URL provided, convert async URL to sync
    database_url = os.getenv("DATABASE_URL", settings.database_url)
    if database_url and "postgresql+asyncpg://" in database_url:
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
