"""
AI Memory Backend Module
========================

Provider-agnostic memory system for conversation history and context management.
Supports multiple backends (PostgreSQL, Neo4j) with zero-code swapping.

Architecture:
- MemoryBackend: Abstract interface (like ModelProvider)
- PostgreSQLMemory: Production implementation with JSONB storage
- Neo4jMemory: Graph-based memory (Option 2 stub)
- memory_factory: Zero-code backend swapping

Usage:
    from api.ai.memory import create_memory_backend

    # Automatically selects backend from environment
    memory = await create_memory_backend()

    # Store conversation
    await memory.store_message(
        conversation_id="conv_123",
        message="How much for 50 people?",
        role="user",
        metadata={"channel": "web"}
    )

    # Retrieve history
    history = await memory.get_conversation_history(
        conversation_id="conv_123",
        limit=10
    )

    # Cross-channel retrieval
    all_history = await memory.get_user_history(
        user_id="user_456",
        channels=["web", "email", "sms"]
    )
"""

from api.ai.memory.memory_backend import (
    ConversationChannel,
    ConversationMessage,
    ConversationMetadata,
    MemoryBackend,
    MemoryBackendError,
    MemoryConnectionError,
    MemoryNotFoundError,
    MemorySearchResult,
    MessageRole,
)
from api.ai.memory.memory_factory import (
    MemoryBackendType,
    create_memory_backend,
    get_memory_backend,
)
from api.ai.memory.neo4j_memory import Neo4jMemory
from api.ai.memory.postgresql_memory import PostgreSQLMemory

__all__ = [
    "ConversationChannel",
    "ConversationMessage",
    "ConversationMetadata",
    # Abstract interface
    "MemoryBackend",
    # Exceptions
    "MemoryBackendError",
    "MemoryBackendType",
    "MemoryConnectionError",
    "MemoryNotFoundError",
    "MemorySearchResult",
    "MessageRole",
    "Neo4jMemory",
    # Implementations
    "PostgreSQLMemory",
    # Factory
    "create_memory_backend",
    "get_memory_backend",
]
