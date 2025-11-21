"""
Migration Example: Using Dependency Injection Container

This file demonstrates how to migrate from direct imports to container-based DI
without breaking existing code. Use this as a reference for gradual migration.

Author: MH Backend Team
Date: 2025-11-03
"""

# ═══════════════════════════════════════════════════════════════════════════
# ❌ OLD WAY (Circular Import Risk)
# ═══════════════════════════════════════════════════════════════════════════

"""
# orchestrator/ai_orchestrator.py (OLD)
from ..routers import get_intent_router  # ← Module-level import
from ..agents import LeadNurturingAgent  # ← Module-level import

class AIOrchestrator:
    def __init__(self):
        self.router = get_intent_router()  # ← Direct dependency
        self.agent = LeadNurturingAgent()  # ← Direct dependency

# PROBLEM: If IntentRouter or LeadNurturingAgent imports AIOrchestrator → CIRCULAR!
"""

# ═══════════════════════════════════════════════════════════════════════════
# ✅ NEW WAY (Container-Based - Zero Circular Imports)
# ═══════════════════════════════════════════════════════════════════════════

# Example 1: Updating AIOrchestrator
# ───────────────────────────────────────────────────────────────────────────

"""
# orchestrator/ai_orchestrator.py (NEW)
class AIOrchestrator:
    def __init__(self, router=None, provider=None):
        # Accept dependencies via constructor (Dependency Injection)
        self.router = router
        self.provider = provider
        
        # Backward compatibility: If not provided, use container
        if self.router is None:
            from ..container import get_container
            self.router = get_container().get_intent_router()
        
        if self.provider is None:
            from ..container import get_container
            self.provider = get_container().get_model_provider()

# ✅ NO CIRCULAR IMPORTS: Dependencies come from outside or container
"""

# Example 2: Updating IntentRouter
# ───────────────────────────────────────────────────────────────────────────

"""
# routers/intent_router.py (NEW)
class IntentRouter:
    def __init__(self, provider=None):
        # Accept dependencies via constructor
        self.provider = provider
        
        # Backward compatibility
        if self.provider is None:
            from ..container import get_container
            self.provider = get_container().get_model_provider()
    
    def route_message(self, message: str):
        # Use injected provider
        agent_type = self._classify_intent(message)
        
        # Get agent from container (lazy)
        from ..container import get_container
        agent = get_container().get_agent(agent_type)
        
        return agent.process(message)

# ✅ NO CIRCULAR IMPORTS: Provider injected, agents loaded lazily from container
"""

# Example 3: Updating BaseAgent
# ───────────────────────────────────────────────────────────────────────────

"""
# agents/base_agent.py (NEW)
class BaseAgent(ABC):
    def __init__(self, agent_type: str, provider=None):
        self.agent_type = agent_type
        
        # Accept provider via constructor
        self.provider = provider
        
        # Backward compatibility
        if self.provider is None:
            from ..container import get_container
            self.provider = get_container().get_model_provider()

# ✅ NO CIRCULAR IMPORTS: Provider injected or loaded from container
"""

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 USAGE EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════

# Usage Example 1: In API Endpoints (Simple)
# ───────────────────────────────────────────────────────────────────────────

"""
# api/ai/endpoints/main.py
from api.ai.container import get_container

@app.post("/api/v1/ai/chat")
async def chat_endpoint(message: str):
    # Get orchestrator from container
    orchestrator = get_container().get_orchestrator()
    
    # Process message
    response = await orchestrator.process(message)
    
    return {"response": response}

# ✅ Clean, simple, no imports needed
"""

# Usage Example 2: With Custom Configuration
# ───────────────────────────────────────────────────────────────────────────

"""
# For advanced use cases with custom config
from api.ai.container import AIContainer
from api.ai.orchestrator import AIOrchestrator

# Create custom container
container = AIContainer()

# Get orchestrator with custom settings
orchestrator = container.get_orchestrator()
orchestrator.config.temperature = 0.9  # Customize

# Use it
response = await orchestrator.process("Hello")
"""

# Usage Example 3: Testing with Mocks
# ───────────────────────────────────────────────────────────────────────────

"""
# tests/test_orchestrator.py
import pytest
from api.ai.container import AIContainer

def test_orchestrator_with_mock_provider():
    # Create fresh container for test
    container = AIContainer()
    
    # Inject mock provider
    mock_provider = MockModelProvider()
    container._model_provider = mock_provider
    
    # Get orchestrator (will use mock provider)
    orchestrator = container.get_orchestrator()
    
    # Test
    response = await orchestrator.process("test message")
    assert mock_provider.called
    
    # Clean up
    container.reset()

# ✅ Easy testing with dependency injection
"""

# Usage Example 4: Gradual Migration (Backward Compatible)
# ───────────────────────────────────────────────────────────────────────────

"""
# Existing code still works!
from api.ai.orchestrator import get_ai_orchestrator

# Old way still functional
orchestrator = get_ai_orchestrator()
response = await orchestrator.process("message")

# New way (preferred)
from api.ai.container import get_container
orchestrator = get_container().get_orchestrator()
response = await orchestrator.process("message")

# Both work! Migrate gradually.
"""

# ═══════════════════════════════════════════════════════════════════════════
# 📋 MIGRATION CHECKLIST
# ═══════════════════════════════════════════════════════════════════════════

MIGRATION_CHECKLIST = """
✅ Phase 1: Setup (DONE)
   - [x] Created container.py
   - [x] Created migration guide
   - [x] Documented patterns

⏳ Phase 2: Update Core Classes (NEXT)
   - [ ] Update AIOrchestrator.__init__ to accept dependencies
   - [ ] Update IntentRouter.__init__ to accept dependencies
   - [ ] Update BaseAgent.__init__ to accept dependencies
   - [ ] Add backward compatibility (if provider is None, use container)

⏳ Phase 3: Update Endpoints
   - [ ] Replace get_ai_orchestrator() with get_container().get_orchestrator()
   - [ ] Update main.py
   - [ ] Update chat endpoints
   - [ ] Update admin endpoints

⏳ Phase 4: Testing
   - [ ] Run existing tests (should still pass)
   - [ ] Add container-based tests
   - [ ] Test with mocks
   - [ ] Load testing

⏳ Phase 5: Cleanup
   - [ ] Remove old singleton patterns (optional)
   - [ ] Update documentation
   - [ ] Team training
   - [ ] Deploy to production
"""

# ═══════════════════════════════════════════════════════════════════════════
# 🎓 KEY PRINCIPLES
# ═══════════════════════════════════════════════════════════════════════════

KEY_PRINCIPLES = """
1. **Lazy Loading**: Import inside methods, not at module level
   ✅ def get_router(self): from .routers import...
   ❌ from .routers import IntentRouter  # At top of file

2. **Dependency Injection**: Pass dependencies via constructor
   ✅ def __init__(self, router, provider): ...
   ❌ def __init__(self): self.router = IntentRouter()

3. **Single Responsibility**: Container manages creation, classes use dependencies
   ✅ Container creates, classes receive
   ❌ Classes create their own dependencies

4. **Backward Compatibility**: Support both old and new patterns during migration
   ✅ provider = provider or get_container().get_model_provider()
   ❌ Break existing code immediately

5. **Testing First**: Make testing easier with dependency injection
   ✅ Inject mocks via constructor
   ❌ Hard-coded dependencies that can't be mocked
"""

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 QUICK START
# ═══════════════════════════════════════════════════════════════════════════

QUICK_START = """
# In your API endpoint, replace:

# OLD:
from api.ai.orchestrator import get_ai_orchestrator
orchestrator = get_ai_orchestrator()

# NEW:
from api.ai.container import get_container
orchestrator = get_container().get_orchestrator()

# That's it! Zero circular imports, production-ready!
"""

print(__doc__)
print("\n" + "=" * 80)
print("MIGRATION CHECKLIST")
print("=" * 80)
print(MIGRATION_CHECKLIST)
print("\n" + "=" * 80)
print("KEY PRINCIPLES")
print("=" * 80)
print(KEY_PRINCIPLES)
print("\n" + "=" * 80)
print("QUICK START")
print("=" * 80)
print(QUICK_START)
