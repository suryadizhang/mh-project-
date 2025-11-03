"""
Memory Backend Factory
=====================

Zero-code backend swapping for conversation memory.
Inspired by model_factory for consistent provider management.

Usage:
    # Automatic backend selection from environment
    memory = await create_memory_backend()

    # Explicit backend selection
    memory = await create_memory_backend(MemoryBackendType.POSTGRESQL)

    # Use in AI Orchestrator
    from api.ai.memory import create_memory_backend

    class AIOrchestrator:
        async def initialize(self):
            self.memory = await create_memory_backend()
            await self.memory.initialize()

Environment Configuration:
    MEMORY_BACKEND=postgresql  # or neo4j

    # PostgreSQL (default - uses existing DATABASE_URL)
    DATABASE_URL=postgresql+asyncpg://...

    # Neo4j (Option 2)
    NEO4J_URI=neo4j://localhost:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=password
"""

from enum import Enum
import logging
import os

from api.ai.memory.memory_backend import MemoryBackend, MemoryBackendError
from api.ai.memory.neo4j_memory import Neo4jMemory
from api.ai.memory.postgresql_memory import PostgreSQLMemory

logger = logging.getLogger(__name__)


# =============================================================================
# BACKEND TYPES
# =============================================================================


class MemoryBackendType(str, Enum):
    """Available memory backend types"""

    POSTGRESQL = "postgresql"
    NEO4J = "neo4j"


# Default backend
DEFAULT_BACKEND = MemoryBackendType.POSTGRESQL


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


async def create_memory_backend(
    backend_type: MemoryBackendType | None = None, **kwargs
) -> MemoryBackend:
    """
    Create and initialize memory backend.

    Args:
        backend_type: Explicit backend type (None = use environment)
        **kwargs: Backend-specific configuration

    Returns:
        Initialized MemoryBackend instance

    Raises:
        MemoryBackendError: If backend creation or initialization fails

    Example:
        # Use environment config
        memory = await create_memory_backend()

        # Explicit backend
        memory = await create_memory_backend(MemoryBackendType.POSTGRESQL)

        # Neo4j with custom URI
        memory = await create_memory_backend(
            MemoryBackendType.NEO4J,
            neo4j_uri="neo4j://prod-server:7687"
        )
    """

    # Determine backend from environment or parameter
    if backend_type is None:
        backend_str = os.getenv("MEMORY_BACKEND", DEFAULT_BACKEND.value).lower()
        try:
            backend_type = MemoryBackendType(backend_str)
        except ValueError:
            logger.exception(
                f"Invalid MEMORY_BACKEND: {backend_str}, using default: {DEFAULT_BACKEND.value}"
            )
            backend_type = DEFAULT_BACKEND

    logger.info(f"Creating memory backend: {backend_type.value}")

    try:
        # Create backend instance
        if backend_type == MemoryBackendType.POSTGRESQL:
            memory = PostgreSQLMemory(**kwargs)

        elif backend_type == MemoryBackendType.NEO4J:
            # Get Neo4j configuration from environment
            neo4j_uri = kwargs.get("neo4j_uri") or os.getenv("NEO4J_URI")
            neo4j_user = kwargs.get("neo4j_user") or os.getenv("NEO4J_USER", "neo4j")
            neo4j_password = kwargs.get("neo4j_password") or os.getenv("NEO4J_PASSWORD")

            if not neo4j_uri:
                raise MemoryBackendError("NEO4J_URI not configured")

            logger.warning("Neo4j memory backend is a STUB - not yet implemented")
            memory = Neo4jMemory(
                neo4j_uri=neo4j_uri, neo4j_user=neo4j_user, neo4j_password=neo4j_password, **kwargs
            )

        else:
            raise MemoryBackendError(f"Unsupported backend type: {backend_type}")

        # Initialize backend
        await memory.initialize()

        logger.info(f"✅ {backend_type.value.upper()} memory backend initialized successfully")

        return memory

    except Exception as e:
        logger.exception(f"Failed to create memory backend: {e}")
        raise MemoryBackendError(f"Memory backend creation failed: {e}")


# =============================================================================
# SINGLETON INSTANCE (Optional - for global access)
# =============================================================================

_global_memory_backend: MemoryBackend | None = None


async def get_memory_backend() -> MemoryBackend:
    """
    Get global memory backend instance (singleton pattern).
    Creates backend on first call.

    Usage:
        from api.ai.memory import get_memory_backend

        memory = await get_memory_backend()
        await memory.store_message(...)

    Returns:
        Global MemoryBackend instance
    """
    global _global_memory_backend

    if _global_memory_backend is None:
        logger.info("Creating global memory backend instance")
        _global_memory_backend = await create_memory_backend()

    return _global_memory_backend


async def close_memory_backend() -> None:
    """
    Close global memory backend.
    Call this on application shutdown.

    Usage:
        # In FastAPI lifespan
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            yield
            await close_memory_backend()
    """
    global _global_memory_backend

    if _global_memory_backend is not None:
        logger.info("Closing global memory backend")
        await _global_memory_backend.close()
        _global_memory_backend = None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def get_configured_backend() -> MemoryBackendType:
    """
    Get memory backend configured in environment.

    Returns:
        Configured MemoryBackendType
    """
    backend_str = os.getenv("MEMORY_BACKEND", DEFAULT_BACKEND.value).lower()
    try:
        return MemoryBackendType(backend_str)
    except ValueError:
        logger.warning(f"Invalid MEMORY_BACKEND: {backend_str}, returning default")
        return DEFAULT_BACKEND


async def test_memory_backend(backend_type: MemoryBackendType | None = None) -> bool:
    """
    Test memory backend connection and basic operations.

    Args:
        backend_type: Backend to test (None = use environment)

    Returns:
        True if all tests pass, False otherwise
    """
    try:
        logger.info("Testing memory backend...")

        # Create backend
        memory = await create_memory_backend(backend_type)

        # Health check
        health = await memory.health_check()
        logger.info(f"Health check: {health}")

        if health["status"] == "unhealthy":
            logger.error("Memory backend health check failed")
            return False

        # Test store and retrieve (if not stub)
        if health["status"] != "stub":
            from api.ai.memory.memory_backend import (
                ConversationChannel,
                MessageRole,
            )

            test_conv_id = "test_conversation_123"

            # Store test message
            msg = await memory.store_message(
                conversation_id=test_conv_id,
                role=MessageRole.USER,
                content="Test message",
                channel=ConversationChannel.WEB,
                user_id="test_user",
            )
            logger.info(f"Stored test message: {msg.id}")

            # Retrieve history
            history = await memory.get_conversation_history(test_conv_id)
            logger.info(f"Retrieved {len(history)} messages")

            if len(history) == 0:
                logger.error("Failed to retrieve stored message")
                return False

            # Get statistics
            stats = await memory.get_statistics()
            logger.info(f"Statistics: {stats}")

        # Close backend
        await memory.close()

        logger.info("✅ Memory backend test passed")
        return True

    except Exception as e:
        logger.exception(f"Memory backend test failed: {e}")
        return False
