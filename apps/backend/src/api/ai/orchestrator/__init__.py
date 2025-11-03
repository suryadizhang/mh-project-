"""
AI Orchestrator Module

This module provides the main orchestration layer for AI-powered customer inquiry handling.
It manages tool execution, OpenAI function calling, and response generation.

Module Structure:
- orchestrator/
  ├── ai_orchestrator.py          # Main orchestrator (you are here next)
  ├── tools/                       # Tool definitions
  │   ├── base_tool.py            # Abstract base class
  │   ├── pricing_tool.py         # Party quote calculation
  │   ├── travel_fee_tool.py      # Travel distance/fees
  │   └── protein_tool.py         # Protein upgrade costs
  ├── services/                    # Supporting services
  │   ├── conversation_service.py # Conversation management
  │   └── phase3_services.py      # Phase 3 placeholders
  └── schemas/                     # Request/response models
      └── orchestrator_schemas.py # Pydantic schemas

Integration Points:
- Replaces direct pricing calls in multi_channel_ai_handler.py
- Uses existing pricing_service.py and protein_calculator_service.py
- Integrates with admin email review system
- Compatible with all 6 communication channels

Phase 1 Features (Current):
- Tool calling (pricing, travel, protein)
- OpenAI function calling integration
- Error handling and logging
- Admin review workflow

Phase 3 Ready (Data-Driven):
- Voice AI (IF phone_call_rate >30%)
- RAG knowledge base (IF ai_error_rate >30%)
- Conversation threading (IF follow_up_rate >50%)
- Identity resolution (IF multi_channel_rate >30%)

Author: MyHibachi Development Team
Created: October 31, 2025
Version: 1.0.0 (Phase 1)
"""

from .tools import (
    BaseTool,
    ToolParameter,
    ToolResult,
    ToolRegistry,
    PricingTool,
    TravelFeeTool,
    ProteinTool
)

from .schemas.orchestrator_schemas import (
    OrchestratorRequest,
    OrchestratorResponse,
    OrchestratorConfig,
    ToolCall
)

from .services.conversation_service import (
    ConversationService,
    get_conversation_service
)

from .services.phase3_services import (
    RAGService,
    VoiceAIService,
    IdentityResolver,
    get_rag_service,
    get_voice_service,
    get_identity_resolver
)

from .ai_orchestrator import (
    AIOrchestrator,
    get_ai_orchestrator
)

__version__ = "1.0.0"
__phase__ = "Phase 1"

__all__ = [
    # Main Orchestrator
    "AIOrchestrator",
    "get_ai_orchestrator",
    
    # Tools
    "BaseTool",
    "ToolParameter",
    "ToolResult",
    "ToolRegistry",
    "PricingTool",
    "TravelFeeTool",
    "ProteinTool",
    
    # Schemas
    "OrchestratorRequest",
    "OrchestratorResponse",
    "OrchestratorConfig",
    "ToolCall",
    
    # Services
    "ConversationService",
    "get_conversation_service",
    "RAGService",
    "VoiceAIService",
    "IdentityResolver",
    "get_rag_service",
    "get_voice_service",
    "get_identity_resolver",
    
    # Metadata
    "__version__",
    "__phase__"
]
