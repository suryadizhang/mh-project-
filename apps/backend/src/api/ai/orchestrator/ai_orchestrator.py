"""
AI Orchestrator - Main Orchestration Engine

This is the central orchestrator that manages tool execution, OpenAI function calling,
and response generation. It integrates with existing services while maintaining
modularity and scalability.

Architecture:
- Uses Intent Router for intelligent agent selection (Phase 1A)
- Specialized agents (Lead Nurturing, Customer Care, Operations, Knowledge)
- Provider-agnostic design (OpenAI/Llama/Hybrid via ModelProvider)
- Integrates with multi_channel_ai_handler.py for channel-specific formatting
- Supports admin review workflow via email_review.py
- ChatGPT-ready design with Phase 3 extension points

Author: MyHibachi Development Team
Created: October 31, 2025
Version: 2.0.0 (Phase 1A - Multi-Agent Foundation)
"""

from datetime import datetime
import json
import logging
import os
from typing import Any
from uuid import uuid4

from openai import OpenAI

from .schemas import (
    OrchestratorConfig,
    OrchestratorRequest,
    OrchestratorResponse,
    ToolCall,
)
from .services import (
    get_conversation_service,
    get_identity_resolver,
    get_rag_service,
    get_voice_service,
)
from .tools import (
    PricingTool,
    ProteinTool,
    ToolRegistry,
    TravelFeeTool,
)

# Initialize logger first
logger = logging.getLogger(__name__)

# Phase 1A: Import router and provider
try:
    from ..routers import get_intent_router

    ROUTER_ENABLED = True
    logger.info("✅ Intent Router imported successfully - multi-agent system available")
except ImportError as e:
    ROUTER_ENABLED = False
    logger.warning(f"Intent router not available - using legacy mode: {e}")

try:
    from .providers import get_provider

    PROVIDER_ENABLED = True
    logger.info("✅ Model Provider imported successfully")
except ImportError as e:
    PROVIDER_ENABLED = False
    logger.warning(f"Model provider not available - using OpenAI client directly: {e}")

# Phase 3: Import adaptive reasoning layers
try:
    from ..reasoning import (
        ComplexityRouter,
        ReActAgent,
        ComplexityLevel,
        MultiAgentSystem,
        MultiAgentConfig,
        HumanEscalationService,
        EscalationReason,
        EscalationContext,
    )
    REASONING_ENABLED = True
    logger.info("✅ Adaptive Reasoning imported successfully - Layers 3-5 (ReAct + Multi-Agent + Human Escalation) available")
except ImportError as e:
    REASONING_ENABLED = False
    logger.warning(f"Adaptive reasoning not available - using direct routing: {e}")


class AIOrchestrator:
    """
    Main orchestrator for AI-powered customer inquiry handling.

    This orchestrator:
    1. Receives customer inquiries via OrchestratorRequest
    2. Routes to specialized agents via Intent Router (Phase 1A)
    3. Agents execute tools as needed (pricing, booking, support, knowledge)
    4. Returns formatted response via OrchestratorResponse

    Phase 1A Features (NEW):
    - Intent Router: Semantic routing to 4 specialized agents
    - Model Provider: Provider-agnostic (OpenAI/Llama/Hybrid)
    - Specialized Agents:
      * Lead Nurturing: Sales psychology, upselling, conversion
      * Customer Care: Empathy, de-escalation, CSAT optimization
      * Operations: Logistics, scheduling, booking management
      * Knowledge: RAG integration, policy lookup, FAQs
    - Tool calling: 16 tools across all agents
    - Conversation history management

    Phase 1 Features (Legacy, still supported):
    - Direct OpenAI integration (fallback if router disabled)
    - Tool calling (pricing, travel, protein)
    - Error handling and retry logic
    - Admin review workflow

    Phase 3 Ready:
    - Voice AI (placeholder service ready)
    - RAG knowledge base (placeholder service ready)
    - Conversation threading (placeholder service ready)
    - Identity resolution (placeholder service ready)

    Example Usage:
        ```python
        orchestrator = AIOrchestrator()

        request = OrchestratorRequest(
            message="I need a chef for 10 adults with filet in 95630",
            channel="email",
            customer_context={"email": "customer@example.com"}
        )

        response = await orchestrator.process_inquiry(request)
        print(response.response)  # AI-generated quote
        print(response.tools_used)  # [PricingTool, ...]
        print(response.metadata["agent_type"])  # "lead_nurturing"
        ```
    """

    def __init__(
        self,
        config: OrchestratorConfig | None = None,
        use_router: bool = True,
        router=None,
        provider=None,
        enable_reasoning: bool = True,
    ):
        """
        Initialize the AI orchestrator.

        Args:
            config: Optional configuration (uses defaults if not provided)
            use_router: Whether to use Intent Router (default: True)
            router: Optional IntentRouter instance (for DI, None = lazy load from container)
            provider: Optional ModelProvider instance (for DI, None = lazy load from container)
            enable_reasoning: Whether to use adaptive reasoning layers (default: True)
        """
        self.config = config or OrchestratorConfig()
        self.logger = logging.getLogger(__name__)
        self.use_router = use_router and ROUTER_ENABLED
        self.enable_reasoning = enable_reasoning and REASONING_ENABLED

        # Phase 2: Dependency Injection support (backward compatible)
        self.router = router
        self.provider = provider

        # Initialize router (Phase 1A) - with DI fallback
        if self.use_router:
            if self.router is None:
                # Backward compatibility: lazy load from container
                try:
                    from ..container import get_container

                    self.router = get_container().get_intent_router()
                except ImportError:
                    # Fallback to old way if container not available
                    self.router = get_intent_router()
            self.logger.info("Intent router enabled - using multi-agent system")
        else:
            self.router = None
            self.logger.info("Intent router disabled - using legacy OpenAI client")

            # Initialize OpenAI client (legacy mode)
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")

            self.client = OpenAI(api_key=api_key)

            # Initialize tool registry (legacy mode)
            self.tool_registry = ToolRegistry()
            self._register_tools()

        # Initialize provider (Phase 1A) - with DI fallback
        if PROVIDER_ENABLED:
            if self.provider is None:
                # Backward compatibility: lazy load from container
                try:
                    from ..container import get_container

                    self.provider = get_container().get_model_provider()
                except ImportError:
                    # Fallback to old way if container not available
                    self.provider = get_provider()
            self.logger.info(f"Model provider initialized: {self.provider.__class__.__name__}")
        else:
            self.provider = None

        # Phase 3: Initialize adaptive reasoning layers (Layer 3 + Layer 4 + Layer 5)
        if self.enable_reasoning:
            try:
                self.complexity_router = ComplexityRouter()
                self.react_agent = None  # Lazy init when needed (requires provider + tools)
                self.multi_agent_system = None  # Lazy init when needed (requires provider + tools)
                self.human_escalation_service = None  # Lazy init when needed (requires provider)
                self.logger.info("✅ Adaptive reasoning enabled - ComplexityRouter initialized")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to initialize reasoning layers: {e}")
                self.complexity_router = None
                self.react_agent = None
                self.multi_agent_system = None
                self.human_escalation_service = None
        else:
            self.complexity_router = None
            self.react_agent = None
            self.multi_agent_system = None
            self.human_escalation_service = None

        # Initialize services
        self.conversation_service = get_conversation_service(
            enable_threading=self.config.enable_threading
        )
        self.rag_service = get_rag_service(enable_rag=self.config.enable_rag)
        self.voice_service = get_voice_service(enable_voice=self.config.enable_voice)
        self.identity_resolver = get_identity_resolver(enable_identity=self.config.enable_identity)

        # Phase 1B: Initialize memory backend and emotion service (deferred to start())
        self.memory_backend = None
        self.emotion_service = None
        self.scheduler = None

        # Conversation history cache (in-memory for now, will be database in Phase 1B)
        self._conversation_history: dict[str, list[dict[str, str]]] = {}

        self.logger.info(
            "AIOrchestrator initialized",
            extra={
                "model": self.config.model,
                "phase": "Phase 1A" if self.use_router else "Phase 1 (Legacy)",
                "router_enabled": self.use_router,
                "provider_enabled": PROVIDER_ENABLED,
                "reasoning_enabled": self.enable_reasoning,
                "tools_registered": (
                    len(self.tool_registry.list_tools())
                    if not self.use_router
                    else "N/A (agents have tools)"
                ),
                "phase3_features_enabled": {
                    "rag": self.config.enable_rag,
                    "voice": self.config.enable_voice,
                    "threading": self.config.enable_threading,
                    "identity": self.config.enable_identity,
                    "adaptive_reasoning": self.enable_reasoning,
                },
            },
        )

    async def start(self) -> None:
        """
        Start the orchestrator and all its services.

        Phase 1B: Initializes memory backend, emotion service, and starts the follow-up scheduler.
        """
        # Phase 1B: Initialize memory backend and emotion service
        if not self.memory_backend or not self.emotion_service:
            try:
                from ..memory import get_memory_backend
                from ..services import get_emotion_service

                self.memory_backend = await get_memory_backend()
                self.emotion_service = get_emotion_service()
                self.logger.info("✅ Memory backend and emotion service initialized")
            except ImportError as e:
                self.logger.warning(f"⚠️ Memory backend or emotion service not available: {e}")
                self.memory_backend = None
                self.emotion_service = None
            except Exception as e:
                self.logger.exception(f"❌ Failed to initialize memory backend: {e}")
                self.memory_backend = None
                self.emotion_service = None

        # Phase 1B: Initialize Follow-Up Scheduler
        if not self.scheduler and self.memory_backend and self.emotion_service:
            try:
                import os

                from ..scheduler import FollowUpScheduler

                timezone = os.getenv("SCHEDULER_TIMEZONE", "UTC")
                self.scheduler = FollowUpScheduler(
                    memory=self.memory_backend,
                    emotion_service=self.emotion_service,
                    timezone=timezone,
                    orchestrator_callback=self._send_followup_message,
                )
                self.logger.info(f"✅ Follow-up scheduler initialized (timezone: {timezone})")
            except ImportError as e:
                self.logger.warning(f"⚠️ Follow-up scheduler not available: {e}")
                self.scheduler = None
            except Exception as e:
                self.logger.exception(f"❌ Failed to initialize scheduler: {e}")
                self.scheduler = None

        # Start scheduler
        if self.scheduler:
            try:
                await self.scheduler.start()
                self.logger.info("✅ Follow-up scheduler started")

                # Schedule daily inactive user detection (runs at 9 AM daily)
                from ..scheduler.inactive_user_detection import (
                    run_daily_reengagement_check,
                )

                self.scheduler.scheduler.add_job(
                    run_daily_reengagement_check,
                    "cron",
                    args=[self.scheduler],
                    hour=9,
                    minute=0,
                    id="daily_reengagement_check",
                    replace_existing=True,
                )
                self.logger.info("✅ Daily inactive user re-engagement check scheduled (9 AM)")
            except Exception as e:
                self.logger.exception(f"❌ Failed to start scheduler: {e}")

    async def stop(self) -> None:
        """
        Stop the orchestrator and gracefully shutdown all services.

        Phase 1B: Stops the follow-up scheduler if running.
        """
        if self.scheduler:
            try:
                await self.scheduler.stop()
                self.logger.info("✅ Follow-up scheduler stopped")
            except Exception as e:
                self.logger.exception(f"❌ Failed to stop scheduler: {e}")

    async def schedule_post_event_followup(
        self,
        conversation_id: str,
        user_id: str,
        event_date: datetime,
        booking_id: str | None = None,
    ) -> str | None:
        """
        Schedule a post-event follow-up for a booking.

        Args:
            conversation_id: Conversation ID
            user_id: User ID
            event_date: Date of the event
            booking_id: Optional booking ID

        Returns:
            Job ID if scheduled, None if not scheduled (e.g., duplicate or scheduler disabled)
        """
        if not self.scheduler:
            self.logger.warning("Scheduler not available - cannot schedule follow-up")
            return None

        try:
            from datetime import timedelta

            job_id = await self.scheduler.schedule_post_event_followup(
                conversation_id=conversation_id,
                user_id=user_id,
                event_date=event_date,
                booking_id=booking_id,
                followup_delay=timedelta(hours=24),
            )
            if job_id:
                self.logger.info(f"Scheduled post-event follow-up: {job_id}")
            else:
                self.logger.debug(f"Follow-up not scheduled (duplicate): {user_id}")
            return job_id
        except Exception as e:
            self.logger.exception(f"Failed to schedule post-event follow-up: {e}")
            return None

    async def schedule_reengagement(self, user_id: str, last_activity: datetime) -> str | None:
        """
        Schedule a re-engagement campaign for an inactive user.

        Args:
            user_id: User ID
            last_activity: Last activity timestamp

        Returns:
            Job ID if scheduled, None if not scheduled
        """
        if not self.scheduler:
            self.logger.warning("Scheduler not available - cannot schedule re-engagement")
            return None

        try:
            from datetime import timedelta

            job_id = await self.scheduler.schedule_reengagement(
                user_id=user_id, last_activity=last_activity, inactive_threshold=timedelta(days=30)
            )
            if job_id:
                self.logger.info(f"Scheduled re-engagement: {job_id}")
            else:
                self.logger.debug(f"Re-engagement not scheduled (duplicate): {user_id}")
            return job_id
        except Exception as e:
            self.logger.exception(f"Failed to schedule re-engagement: {e}")
            return None

    async def _send_followup_message(
        self, user_id: str, conversation_id: str, content: str, metadata: dict[str, Any]
    ) -> None:
        """
        Send a follow-up message to the user.

        This is the callback used by the scheduler to send automated messages.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            content: Message content
            metadata: Additional metadata (followup_id, trigger_type, etc.)
        """
        try:
            # Store the follow-up message in memory
            if self.memory_backend:
                from ..memory.memory_backend import MessageRole

                await self.memory_backend.store_message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=content,
                    user_id=user_id,
                    metadata=metadata,
                )

            # TODO: Actually send the message via appropriate channel
            # This would involve:
            # 1. Looking up user's preferred channel (email, SMS, etc.)
            # 2. Formatting message for that channel
            # 3. Sending via the appropriate service
            # For now, we just log it
            self.logger.info(
                f"Follow-up message queued for user {user_id}",
                extra={
                    "conversation_id": conversation_id,
                    "followup_id": metadata.get("followup_id"),
                    "trigger_type": metadata.get("trigger_type"),
                    "content_preview": content[:100] + "..." if len(content) > 100 else content,
                },
            )

        except Exception as e:
            self.logger.exception(f"Failed to send follow-up message: {e}")
            raise

    def _register_tools(self) -> None:
        """
        Register all available tools with the registry.

        Phase 1: Pricing, Travel, Protein tools
        Phase 3: Voice, RAG tools (when enabled)
        """
        # Phase 1 tools (always registered)
        self.tool_registry.register(PricingTool())
        self.tool_registry.register(TravelFeeTool())
        self.tool_registry.register(ProteinTool())

        # Phase 3 tools (register when enabled)
        # These will be implemented in Phase 3 based on data validation

        self.logger.info(
            f"Registered {len(self.tool_registry.list_tools())} tools",
            extra={"tools": self.tool_registry.list_tools()},
        )

    def _build_system_prompt(self, channel: str) -> str:
        """
        Build system prompt for the AI.

        This prompt defines the AI's role, capabilities, and constraints.
        Integrates with existing multi_channel_ai_handler tone/format.

        WHITE-LABEL READY: Uses dynamic brand context from settings.

        Args:
            channel: Communication channel (email, sms, instagram, etc.)

        Returns:
            System prompt string
        """
        # Get brand context from settings (white-label ready)
        from ....core.config import get_settings

        settings = get_settings()
        brand = settings.get_brand_context()

        # Channel-specific tone adjustments
        channel_tones = {
            "email": "professional and detailed",
            "sms": "brief and friendly",
            "instagram": "casual and enthusiastic",
            "facebook": "warm and conversational",
            "phone": "clear and direct",
            "tiktok": "energetic and engaging",
        }

        tone = channel_tones.get(channel, "professional and helpful")

        return f"""You are an AI assistant for {brand['brand_name']}, a premier {brand['cuisine_type'].lower()} catering service in {brand['city']}, {brand['state']}.

**YOUR ROLE**:
- Help customers get accurate quotes for hibachi parties
- Answer questions about our services, pricing, and availability
- Be {tone} in your communication style

**PRICING & SERVICES**:
- Base Pricing: $55/adult (13+), $30/child (6-12), FREE under 5
- Party Minimum: $550 total
- Each guest gets 2 FREE proteins (Chicken, NY Strip Steak, Shrimp, Tofu, Vegetables)
- Premium Upgrades: Filet Mignon/Salmon/Scallops (+$5 each), Lobster Tail (+$15 each)
- 3rd Protein Rule: +$10 per extra protein beyond 2 per guest
- Travel: FREE within 30 miles, $2/mile after
- Addons: Premium Sake Service (+$25), Extended Performance (+$50), Custom Menu (+$35)

**IMPORTANT TOOLS**:
You have access to tools for EXACT calculations. ALWAYS use tools for pricing - NEVER estimate or guess.

Available tools:
1. calculate_party_quote - Complete quote with proteins, travel, addons
2. calculate_travel_fee - Distance-based travel fees
3. calculate_protein_costs - Protein upgrade costs

**RESPONSE GUIDELINES**:
1. Use tools for any pricing question (even "roughly" or "ballpark")
2. Break down costs clearly (base + proteins + travel = total)
3. Mention gratuity is not included (20-35% suggested)
4. Include contact info for booking: {brand['phone_formatted']} or {brand['email']}
5. Be transparent about what's included vs. upgrades
6. If customer says "filet" they mean "filet mignon"
7. If customer says "steak" clarify if they mean NY Strip (FREE) or Filet (+$5)

**CHANNEL: {channel}**
Adjust your tone and length for this channel accordingly.

Generate accurate, helpful responses that make customers excited to book!"""

    async def process_inquiry(self, request: OrchestratorRequest) -> OrchestratorResponse:
        """
        Process customer inquiry with AI orchestration.

        Phase 1A Mode (Router Enabled):
        1. Resolves customer identity (Phase 3)
        2. Retrieves conversation history from cache
        3. Routes to appropriate agent via Intent Router
        4. Agent executes tools as needed
        5. Returns response with routing metadata

        Legacy Mode (Router Disabled):
        1. Resolves customer identity (Phase 3)
        2. Gets RAG knowledge context (Phase 3)
        3. Calls OpenAI with function calling
        4. Executes requested tools
        5. Generates final response

        Args:
            request: Customer inquiry request

        Returns:
            Orchestrator response with AI-generated reply and tool usage
        """
        start_time = datetime.now()

        try:
            # Step 1: Resolve customer identity (Phase 3 - currently no-op)
            customer_id = (
                await self.identity_resolver.resolve_identity(
                    email=request.customer_context.get("email"),
                    phone=request.customer_context.get("phone"),
                    name=request.customer_context.get("name"),
                )
                or request.customer_id
            )

            # Step 2: Create/retrieve conversation
            if not request.conversation_id:
                request.conversation_id = await self.conversation_service.create_conversation(
                    customer_id=customer_id, channel=request.channel, message=request.message
                )

            # Step 3: Get conversation history
            conversation_history = self._conversation_history.get(request.conversation_id, [])

            # Phase 3: Adaptive complexity routing (if enabled)
            complexity_level = None
            if self.enable_reasoning and self.complexity_router:
                try:
                    # Build context for complexity assessment
                    routing_context = {
                        "conversation_id": request.conversation_id,
                        "customer_id": customer_id,
                        "channel": request.channel,
                        "escalation_count": len(
                            [m for m in conversation_history if "escalate" in m.get("content", "").lower()]
                        ),
                        "avg_complexity": 1.0,  # TODO: Track historical complexity
                        **request.customer_context,
                    }

                    # Classify query complexity
                    complexity_level = await self.complexity_router.classify(
                        request.message, routing_context
                    )

                    self.logger.debug(
                        f"Complexity classified as {complexity_level.name}",
                        extra={
                            "query": request.message[:100],
                            "level": complexity_level.value,
                            "context": routing_context,
                        },
                    )

                    # Handle different complexity levels
                    if complexity_level == ComplexityLevel.REACT:
                        # Use ReAct agent for medium complexity
                        response = await self._process_with_react(
                            request, customer_id, conversation_history, start_time, routing_context
                        )
                    elif complexity_level == ComplexityLevel.MULTI_AGENT:
                        # Route to multi-agent system (Layer 4)
                        self.logger.info("Routing to multi-agent system for complex reasoning")
                        response = await self._process_with_multi_agent(
                            request, customer_id, conversation_history, start_time, routing_context
                        )
                    elif complexity_level == ComplexityLevel.HUMAN:
                        # Route to human escalation (Layer 5)
                        self.logger.warning("Routing to human escalation with AI context preparation")
                        response = await self._process_with_human_escalation(
                            request, customer_id, conversation_history, start_time, routing_context
                        )
                    else:  # ComplexityLevel.CACHE or fallback
                        # Use standard routing for simple queries
                        response = await self._process_with_router_or_legacy(
                            request, customer_id, conversation_history, start_time
                        )

                except Exception as e:
                    self.logger.warning(
                        f"Complexity routing failed: {e}, falling back to standard routing",
                        exc_info=True,
                    )
                    response = await self._process_with_router_or_legacy(
                        request, customer_id, conversation_history, start_time
                    )
            else:
                # Standard routing (no adaptive reasoning)
                response = await self._process_with_router_or_legacy(
                    request, customer_id, conversation_history, start_time
                )

            # Add complexity metadata if available
            if complexity_level:
                response.metadata["complexity_level"] = complexity_level.name
                response.metadata["complexity_value"] = complexity_level.value

            # Update conversation history
            self._conversation_history[request.conversation_id] = [
                *conversation_history,
                {"role": "user", "content": request.message},
                {"role": "assistant", "content": response.response},
            ]

            # Add to conversation service (Phase 3)
            await self.conversation_service.add_message(
                conversation_id=request.conversation_id, role="user", content=request.message
            )
            await self.conversation_service.add_message(
                conversation_id=request.conversation_id, role="assistant", content=response.response
            )

            return response

        except Exception as e:
            self.logger.error(
                f"Inquiry processing failed: {e!s}",
                exc_info=True,
                extra={"request": request.dict() if hasattr(request, "dict") else str(request)},
            )

            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            return OrchestratorResponse(
                success=False,
                response="I apologize, but I'm having trouble processing your inquiry right now. Please call us at (916) 740-8768 and we'll help you immediately!",
                error=str(e),
                requires_admin_review=True,
                metadata={
                    "execution_time_ms": round(execution_time_ms, 2),
                    "error_type": type(e).__name__,
                },
            )

    async def _process_with_router(
        self,
        request: OrchestratorRequest,
        customer_id: str,
        conversation_history: list[dict[str, str]],
        start_time: datetime,
    ) -> OrchestratorResponse:
        """
        Process inquiry using Intent Router and specialized agents.

        This is the Phase 1A multi-agent flow.
        """
        # Build context for router
        context = {
            "conversation_id": request.conversation_id,
            "customer_id": customer_id,
            "channel": request.channel,
            **request.customer_context,
        }

        # Route to appropriate agent
        agent_response = await self.router.route(
            message=request.message, context=context, conversation_history=conversation_history
        )

        # Convert agent tool calls to orchestrator format
        tools_used = []
        if agent_response.get("tool_calls"):
            for tool_call in agent_response["tool_calls"]:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                # Find matching tool result
                tool_result = next(
                    (
                        tr
                        for tr in agent_response.get("tool_results", [])
                        if tr.get("tool_call_id") == tool_call["id"]
                    ),
                    None,
                )

                tools_used.append(
                    ToolCall(
                        tool_name=function_name,
                        parameters=function_args,
                        result=tool_result.get("result", {}) if tool_result else {},
                        execution_time_ms=(
                            tool_result.get("execution_time_ms", 0) if tool_result else 0
                        ),
                        success=tool_result.get("success", False) if tool_result else False,
                    )
                )

        # Calculate metadata
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        routing_metadata = agent_response.get("routing", {})

        # Determine if admin review needed
        requires_admin_review = self.config.auto_admin_review

        # Build response
        return OrchestratorResponse(
            success=True,
            response=agent_response["content"],
            tools_used=tools_used,
            conversation_id=request.conversation_id,
            requires_admin_review=requires_admin_review,
            metadata={
                "model": self.config.model,
                "execution_time_ms": round(execution_time_ms, 2),
                "customer_id": customer_id,
                "channel": request.channel,
                "tools_count": len(tools_used),
                "phase": "Phase 1A",
                "router_enabled": True,
                "agent_type": routing_metadata.get("agent_type"),
                "routing_confidence": routing_metadata.get("confidence"),
                "classification_latency_ms": routing_metadata.get("classification_latency_ms"),
                "agent_latency_ms": routing_metadata.get("agent_latency_ms"),
                "intent_transition": routing_metadata.get("intent_transition"),
                "usage": agent_response.get("usage", {}),
                "finish_reason": agent_response.get("finish_reason"),
                "phase3_features_used": {
                    "rag": False,  # Phase 3
                    "threading": len(conversation_history) > 0,
                    "identity": customer_id != request.customer_id,
                },
            },
        )

    async def _process_with_router_or_legacy(
        self,
        request: OrchestratorRequest,
        customer_id: str,
        conversation_history: list[dict[str, str]],
        start_time: datetime,
    ) -> OrchestratorResponse:
        """
        Route to either Intent Router (Phase 1A) or Legacy mode based on configuration.

        This is a helper to avoid code duplication in complexity routing.
        """
        if self.use_router:
            return await self._process_with_router(
                request, customer_id, conversation_history, start_time
            )
        else:
            return await self._process_with_legacy(
                request, customer_id, conversation_history, start_time
            )

    async def _process_with_react(
        self,
        request: OrchestratorRequest,
        customer_id: str,
        conversation_history: list[dict[str, str]],
        start_time: datetime,
        routing_context: dict,
    ) -> OrchestratorResponse:
        """
        Process inquiry using ReAct Agent (Layer 3: Reason + Act pattern).

        This is used for medium complexity queries that benefit from
        iterative reasoning and tool execution.
        """
        # Lazy initialize ReAct agent if not already done
        if not self.react_agent:
            try:
                # Get tools from router or tool registry
                if self.use_router and self.router:
                    # Extract tools from one of the agents (they share the same registry)
                    tool_registry = self.router.agents.get("lead_nurturing").tool_registry
                elif hasattr(self, "tool_registry"):
                    tool_registry = self.tool_registry
                else:
                    raise ValueError("No tool registry available for ReAct agent")

                self.react_agent = ReActAgent(
                    model_provider=self.provider or self.client,
                    tool_registry=tool_registry,
                )
                self.logger.info("✅ ReAct agent initialized on-demand")
            except Exception as e:
                self.logger.error(f"Failed to initialize ReAct agent: {e}", exc_info=True)
                # Fall back to standard routing
                return await self._process_with_router_or_legacy(
                    request, customer_id, conversation_history, start_time
                )

        # Build context for ReAct agent
        react_context = {
            "conversation_history": conversation_history,
            "customer_id": customer_id,
            "channel": request.channel,
            **routing_context,
        }

        try:
            # Process with ReAct agent
            react_result = await self.react_agent.process(request.message, react_context)

            # Convert ReAct result to OrchestratorResponse
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Convert tools used
            tools_used = []
            for tool_name in react_result.tools_used:
                # Find the tool execution in the steps
                for step in react_result.steps:
                    if step.action == tool_name and step.action_input:
                        tools_used.append(
                            ToolCall(
                                tool_name=tool_name,
                                parameters=step.action_input,
                                result={"observation": step.observation},
                                execution_time_ms=0,  # Not tracked per-tool in ReAct
                                success=True,
                            )
                        )
                        break

            return OrchestratorResponse(
                success=react_result.success,
                response=react_result.response,
                tools_used=tools_used,
                conversation_id=request.conversation_id,
                requires_admin_review=not react_result.success or self.config.auto_admin_review,
                metadata={
                    "model": self.config.model,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "customer_id": customer_id,
                    "channel": request.channel,
                    "tools_count": len(tools_used),
                    "phase": "Phase 3 (ReAct Agent)",
                    "reasoning_iterations": react_result.iterations,
                    "reasoning_cost_usd": react_result.cost_usd,
                    "reasoning_duration_ms": react_result.duration_ms,
                    "reasoning_steps": len(react_result.steps),
                },
            )

        except Exception as e:
            self.logger.error(f"ReAct agent processing failed: {e}", exc_info=True)
            # Fall back to standard routing
            return await self._process_with_router_or_legacy(
                request, customer_id, conversation_history, start_time
            )

    async def _process_with_multi_agent(
        self,
        request: OrchestratorRequest,
        customer_id: str,
        conversation_history: list[dict[str, str]],
        start_time: datetime,
        routing_context: dict,
    ) -> OrchestratorResponse:
        """
        Process inquiry using Multi-Agent System (Layer 4).

        This is used for complex queries that require coordinated reasoning
        across multiple specialized agents (Analyzer, Planner, Executor, Critic).

        Target: 97% accuracy for complex multi-constraint problems.
        """
        # Lazy initialize Multi-Agent System if not already done
        if not self.multi_agent_system:
            try:
                # Get tools from router or tool registry
                if self.use_router and self.router:
                    # Extract tools from one of the agents (they share the same registry)
                    tool_registry = self.router.agents.get("lead_nurturing").tool_registry
                elif hasattr(self, "tool_registry"):
                    tool_registry = self.tool_registry
                else:
                    raise ValueError("No tool registry available for multi-agent system")

                # Configure multi-agent system
                config = MultiAgentConfig(
                    max_iterations=3,
                    max_critique_cycles=2,
                    critique_quality_threshold=0.85,
                    timeout_seconds=15.0,
                )

                self.multi_agent_system = MultiAgentSystem(
                    model_provider=self.provider or self.client,
                    tool_registry=tool_registry,
                    config=config,
                )
                self.logger.info("✅ Multi-Agent System initialized on-demand")
            except Exception as e:
                self.logger.error(f"Failed to initialize Multi-Agent System: {e}", exc_info=True)
                # Fall back to standard routing
                return await self._process_with_router_or_legacy(
                    request, customer_id, conversation_history, start_time
                )

        # Build context for Multi-Agent System
        multi_agent_context = {
            "conversation_history": conversation_history,
            "customer_id": customer_id,
            "channel": request.channel,
            **routing_context,
            **request.customer_context,
        }

        try:
            # Process with Multi-Agent System
            multi_agent_result = await self.multi_agent_system.process(
                request.message, multi_agent_context
            )

            # Convert Multi-Agent result to OrchestratorResponse
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Convert tools used
            tools_used = []
            for step in multi_agent_result.plan.steps:
                if step.tool_name and step.completed:
                    tools_used.append(
                        ToolCall(
                            tool_name=step.tool_name,
                            parameters=step.tool_parameters or {},
                            result=step.result or {},
                            execution_time_ms=0,  # Not tracked per-tool
                            success=step.completed,
                        )
                    )

            return OrchestratorResponse(
                success=multi_agent_result.success,
                response=multi_agent_result.response,
                tools_used=tools_used,
                conversation_id=request.conversation_id,
                requires_admin_review=(
                    not multi_agent_result.success
                    or multi_agent_result.critique.quality_score < 0.85
                    or self.config.auto_admin_review
                ),
                metadata={
                    "model": self.config.model,
                    "execution_time_ms": round(execution_time_ms, 2),
                    "customer_id": customer_id,
                    "channel": request.channel,
                    "tools_count": len(tools_used),
                    "phase": "Phase 3 (Multi-Agent System)",
                    # Multi-agent specific metadata
                    "multi_agent_iterations": multi_agent_result.iterations,
                    "multi_agent_critique_cycles": multi_agent_result.critique_cycles,
                    "multi_agent_quality_score": multi_agent_result.critique.quality_score,
                    "multi_agent_verdict": multi_agent_result.critique.final_verdict,
                    "multi_agent_cost_usd": multi_agent_result.cost_usd,
                    "multi_agent_duration_ms": multi_agent_result.duration_ms,
                    "multi_agent_agents_used": [
                        msg.from_agent.value for msg in multi_agent_result.messages
                    ],
                },
            )

        except Exception as e:
            self.logger.error(f"Multi-Agent System processing failed: {e}", exc_info=True)
            # Fall back to standard routing
            return await self._process_with_router_or_legacy(
                request, customer_id, conversation_history, start_time
            )

    async def _process_with_human_escalation(
        self,
        request: OrchestratorRequest,
        customer_id: str,
        conversation_history: list[dict[str, str]],
        start_time: datetime,
        routing_context: dict,
    ) -> OrchestratorResponse:
        """
        Process inquiry requiring human intervention with AI context preparation (Layer 5).

        This is the highest complexity level - prepares comprehensive context for human agents.
        
        Steps:
        1. Lazy initialize HumanEscalationService
        2. Determine escalation reason from routing context
        3. Prepare AI attempt metadata
        4. Call escalation service to prepare context
        5. Create escalation record in database
        6. Build response directing customer to human
        7. Add rich metadata for admin dashboard
        
        Args:
            request: Orchestrator request
            customer_id: Customer identifier
            conversation_history: Full conversation history
            start_time: Processing start time
            routing_context: Context from complexity classification
            
        Returns:
            OrchestratorResponse with escalation details
        """
        try:
            # Lazy initialize HumanEscalationService if needed
            if self.human_escalation_service is None:
                self.logger.info("Initializing HumanEscalationService (Layer 5)...")
                self.human_escalation_service = HumanEscalationService(
                    model_provider=self.model_provider,
                    escalation_service=None,  # Will use direct DB access instead
                )
                self.logger.info("✅ HumanEscalationService initialized successfully")

            # Determine escalation reason from routing context
            escalation_reason = self._determine_escalation_reason(routing_context)
            
            self.logger.info(
                "Preparing human escalation context",
                extra={
                    "customer_id": customer_id,
                    "reason": escalation_reason.value,
                    "query_preview": request.message[:100],
                },
            )

            # Prepare AI attempt metadata
            ai_attempt = {
                "layer": "HUMAN",
                "complexity_level": "HUMAN",
                "routing_context": routing_context,
                "confidence": routing_context.get("confidence", 0.5),
                "quality_score": routing_context.get("quality_score", 0.5),
                "tools_available": routing_context.get("tools_available", []),
                "attempt_timestamp": start_time.isoformat(),
            }

            # Prepare customer context
            customer_context = {
                "name": request.customer_context.get("name", "Unknown"),
                "email": request.customer_context.get("email"),
                "phone": request.customer_context.get("phone"),
                "zipcode": request.customer_context.get("zipcode"),
                "lifetime_value": request.customer_context.get("lifetime_value", 0.0),
                "booking_count": request.customer_context.get("booking_count", 0),
                "vip_status": request.customer_context.get("vip_status", False),
                "previous_escalations": request.customer_context.get("previous_escalations", 0),
            }

            # Call HumanEscalationService to prepare complete context
            escalation_result = await self.human_escalation_service.prepare_escalation(
                query=request.message,
                customer_id=customer_id,
                customer_context=customer_context,
                conversation_history=conversation_history,
                ai_attempt=ai_attempt,
                escalation_reason=escalation_reason,
                channel=request.channel,
            )

            if not escalation_result.success:
                self.logger.error(
                    f"Failed to prepare escalation context: {escalation_result.error}"
                )
                # Fall back to standard routing
                return await self._process_with_router_or_legacy(
                    request, customer_id, conversation_history, start_time
                )

            escalation_context = escalation_result.context
            
            # Create escalation record in database
            escalation_id = None
            if request.customer_context.get("phone"):
                try:
                    from services.escalation_service import EscalationService
                    from database import get_db
                    
                    db = next(get_db())
                    escalation_svc = EscalationService(db)
                    
                    # Map urgency to priority
                    priority_map = {
                        "LOW": "low",
                        "MEDIUM": "medium",
                        "HIGH": "high",
                        "CRITICAL": "urgent",
                    }
                    
                    escalation_record = await escalation_svc.create_escalation(
                        conversation_id=request.conversation_id or str(uuid4()),
                        phone=request.customer_context.get("phone"),
                        reason=escalation_context.why_ai_failed,
                        preferred_method="sms",
                        priority=priority_map.get(
                            escalation_context.urgency_level.name, "medium"
                        ),
                        email=request.customer_context.get("email"),
                        customer_id=customer_id,
                        customer_consent=True,
                        metadata={
                            "escalation_context_id": escalation_context.escalation_id,
                            "sentiment": escalation_context.current_sentiment.value,
                            "urgency": escalation_context.urgency_level.value,
                            "reason": escalation_context.escalation_reason.value,
                            "ai_attempt": escalation_context.ai_attempt.__dict__,
                            "priority_flags": escalation_context.priority_flags,
                        },
                    )
                    
                    escalation_id = str(escalation_record.id)
                    self.logger.info(f"✅ Escalation record created: {escalation_id}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to create escalation record: {e}")
                    # Continue without database record

            # Build response message for customer
            response_message = self._build_escalation_response_message(escalation_context)

            # Calculate processing time
            end_time = datetime.now()
            processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

            # Create orchestrator response
            return OrchestratorResponse(
                message=response_message,
                success=True,
                response_time_ms=processing_time_ms,
                model_used=self.model_provider.model_name,
                confidence_score=0.99,  # High confidence (human will handle)
                tools_used=["human_escalation"],
                conversation_id=request.conversation_id,
                metadata={
                    "timestamp": end_time.isoformat(),
                    "channel": request.channel,
                    "phase": "Phase 3 (Human Escalation - Layer 5)",
                    # Human escalation specific metadata
                    "escalation_id": escalation_context.escalation_id,
                    "escalation_db_id": escalation_id,
                    "escalation_reason": escalation_context.escalation_reason.value,
                    "urgency_level": escalation_context.urgency_level.name,
                    "sentiment": escalation_context.current_sentiment.value,
                    "sentiment_explanation": escalation_context.sentiment_explanation,
                    "priority_flags": escalation_context.priority_flags,
                    "customer_lifetime_value": escalation_context.customer_context.lifetime_value,
                    "customer_vip_status": escalation_context.customer_context.vip_status,
                    "recommended_action": escalation_context.recommended_actions.primary_action,
                    "escalation_cost_usd": 0.030,  # Approximate cost
                    "escalation_duration_ms": escalation_result.duration_ms,
                    "admin_notes": escalation_context.admin_notes,
                },
            )

        except Exception as e:
            self.logger.error(f"Human Escalation processing failed: {e}", exc_info=True)
            # Fall back to standard routing
            return await self._process_with_router_or_legacy(
                request, customer_id, conversation_history, start_time
            )

    def _determine_escalation_reason(self, routing_context: dict) -> EscalationReason:
        """
        Determine escalation reason from routing context.
        
        Maps routing signals to EscalationReason enum.
        """
        # Check for explicit signals in routing context
        if routing_context.get("explicit_human_request"):
            return EscalationReason.EXPLICIT_REQUEST
        
        if routing_context.get("contains_crisis_keywords"):
            return EscalationReason.CRISIS
        
        if routing_context.get("contains_sensitive_topics"):
            return EscalationReason.SENSITIVE
        
        if routing_context.get("high_value_query"):
            return EscalationReason.HIGH_VALUE
        
        confidence = routing_context.get("confidence", 1.0)
        if confidence < 0.85:
            return EscalationReason.LOW_CONFIDENCE
        
        # Default to complex unsolved
        return EscalationReason.COMPLEX_UNSOLVED

    def _build_escalation_response_message(self, escalation_context: EscalationContext) -> str:
        """
        Build customer-facing response message for human escalation.
        
        Message is empathetic and explains what will happen next.
        """
        # Get customer name if available
        customer_name = escalation_context.customer_context.name
        greeting = f"Hi {customer_name}! " if customer_name != "Unknown" else "Hi! "
        
        # Base message
        message = (
            f"{greeting}I understand you need assistance with this. "
            f"I'm connecting you with one of our team members who can help. "
        )
        
        # Add urgency-specific messaging
        if escalation_context.urgency_level.name == "CRITICAL":
            message += (
                "Your request is marked as urgent and we'll respond as soon as possible. "
            )
        elif escalation_context.urgency_level.name == "HIGH":
            message += "We'll get back to you shortly. "
        else:
            message += "We'll respond within our normal business hours. "
        
        # Add sentiment-specific messaging
        if escalation_context.current_sentiment.value <= -1:
            message += (
                "I apologize for any frustration. "
                "Our team will make sure you get the help you need. "
            )
        
        # Add VIP messaging
        if escalation_context.customer_context.vip_status:
            message += "As a valued VIP customer, you're a priority for us. "
        
        # Add contact method
        if escalation_context.customer_context.phone:
            message += f"We'll contact you at {escalation_context.customer_context.phone}. "
        
        # Closing
        message += f"Reference ID: {escalation_context.escalation_id}"
        
        return message

    async def _process_with_legacy(
        self,
        request: OrchestratorRequest,
        customer_id: str,
        conversation_history: list[dict[str, str]],
        start_time: datetime,
    ) -> OrchestratorResponse:
        """
        Process inquiry using legacy OpenAI direct integration.

        This maintains backward compatibility with Phase 1.
        """
        # Get RAG knowledge (Phase 3 - currently None)
        rag_knowledge = await self.rag_service.retrieve_knowledge(request.message)

        # Build messages for OpenAI
        messages = self._build_messages(
            request.message,
            request.channel,
            request.customer_context,
            conversation_history,
            rag_knowledge,
        )

        # Call OpenAI with function calling
        tools_used = []
        response_text = await self._call_openai_with_tools(messages, tools_used)

        # Calculate metadata
        execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        # Determine if admin review needed
        requires_admin_review = self.config.auto_admin_review

        # Build response
        return OrchestratorResponse(
            success=True,
            response=response_text,
            tools_used=tools_used,
            conversation_id=request.conversation_id,
            requires_admin_review=requires_admin_review,
            metadata={
                "model": self.config.model,
                "execution_time_ms": round(execution_time_ms, 2),
                "customer_id": customer_id,
                "channel": request.channel,
                "tools_count": len(tools_used),
                "phase": "Phase 1 (Legacy)",
                "router_enabled": False,
                "phase3_features_used": {
                    "rag": rag_knowledge is not None,
                    "threading": len(conversation_history) > 0,
                    "identity": customer_id != request.customer_id,
                },
            },
        )

    def _build_messages(
        self,
        message: str,
        channel: str,
        customer_context: dict[str, Any],
        history: list[dict[str, Any]],
        rag_knowledge: list[dict[str, Any]] | None,
    ) -> list[dict[str, str]]:
        """
        Build message list for OpenAI.

        Args:
            message: Customer inquiry
            channel: Communication channel
            customer_context: Customer information
            history: Conversation history (Phase 3)
            rag_knowledge: RAG knowledge (Phase 3)

        Returns:
            List of messages for OpenAI
        """
        messages = [{"role": "system", "content": self._build_system_prompt(channel)}]

        # Add conversation history (Phase 3)
        for msg in history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

        # Add RAG knowledge context (Phase 3)
        if rag_knowledge:
            knowledge_text = "\n\n".join(
                [f"**Knowledge**: {doc.get('content', '')}" for doc in rag_knowledge]
            )
            messages.append(
                {"role": "system", "content": f"**Additional Context**:\n{knowledge_text}"}
            )

        # Add customer context if available
        if customer_context:
            context_parts = []
            if customer_context.get("name"):
                context_parts.append(f"Customer: {customer_context['name']}")
            if customer_context.get("email"):
                context_parts.append(f"Email: {customer_context['email']}")
            if customer_context.get("phone"):
                context_parts.append(f"Phone: {customer_context['phone']}")
            if customer_context.get("address") or customer_context.get("zipcode"):
                location = customer_context.get("address") or customer_context.get("zipcode")
                context_parts.append(f"Location: {location}")

            if context_parts:
                messages.append(
                    {
                        "role": "system",
                        "content": f"**Customer Context**: {', '.join(context_parts)}",
                    }
                )

        # Add current user message
        messages.append({"role": "user", "content": message})

        return messages

    async def _call_openai_with_tools(
        self, messages: list[dict[str, str]], tools_used: list[ToolCall]
    ) -> str:
        """
        Call OpenAI with function calling and tool execution.

        This method:
        1. Gets tool schemas from registry
        2. Calls OpenAI with tools parameter
        3. Executes any requested tools
        4. Feeds results back to OpenAI
        5. Returns final response

        Args:
            messages: Message history for OpenAI
            tools_used: List to append tool execution records

        Returns:
            Final AI response text
        """
        # Get tool schemas
        tool_schemas = self.tool_registry.to_openai_functions()

        self.logger.debug(
            f"Calling OpenAI with {len(tool_schemas)} tools available",
            extra={"tools": [t["function"]["name"] for t in tool_schemas]},
        )

        # Initial OpenAI call with tools
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto",  # Let AI decide when to use tools
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        message = response.choices[0].message

        # Check if AI wants to use tools
        if message.tool_calls:
            self.logger.info(
                f"AI requested {len(message.tool_calls)} tool calls",
                extra={"tools": [tc.function.name for tc in message.tool_calls]},
            )

            # Add assistant message to history
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                }
            )

            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                self.logger.info(f"Executing tool: {tool_name}", extra={"arguments": tool_args})

                # Get tool from registry
                tool = self.tool_registry.get(tool_name)
                if not tool:
                    self.logger.error(f"Tool not found: {tool_name}")
                    continue

                # Execute tool with logging
                tool_start = datetime.now()
                tool_result = await tool.execute_with_logging(**tool_args)
                tool_time_ms = (datetime.now() - tool_start).total_seconds() * 1000

                # Record tool usage
                tools_used.append(
                    ToolCall(
                        tool_name=tool_name,
                        parameters=tool_args,
                        result=tool_result.data or {},
                        execution_time_ms=round(tool_time_ms, 2),
                        success=tool_result.success,
                    )
                )

                # Add tool result to messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": json.dumps(tool_result.dict()),
                    }
                )

            # Call OpenAI again with tool results
            final_response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            return final_response.choices[0].message.content

        else:
            # No tools used, return direct response
            return message.content

    def get_conversation_history(self, conversation_id: str) -> list[dict[str, str]]:
        """
        Get conversation history for a given conversation ID.

        Args:
            conversation_id: Conversation ID to retrieve

        Returns:
            List of messages (role + content)
        """
        return self._conversation_history.get(conversation_id, [])

    def clear_conversation_history(self, conversation_id: str) -> None:
        """
        Clear conversation history for a given conversation ID.

        Useful when a conversation ends or for testing.

        Args:
            conversation_id: Conversation ID to clear
        """
        if conversation_id in self._conversation_history:
            del self._conversation_history[conversation_id]
            self.logger.info(f"Cleared conversation history: {conversation_id}")

    def get_statistics(self) -> dict[str, Any]:
        """
        Get orchestrator statistics.

        Returns:
            Statistics about orchestrator usage
        """
        stats = {
            "mode": "router" if self.use_router else "legacy",
            "total_conversations": len(self._conversation_history),
            "phase": "Phase 1A" if self.use_router else "Phase 1 (Legacy)",
        }

        # Add router statistics if enabled
        if self.use_router and self.router:
            router_stats = self.router.get_statistics()
            stats["router"] = router_stats

        # Add legacy statistics if applicable
        if not self.use_router:
            stats["tools_registered"] = len(self.tool_registry.list_tools())

        return stats


# Singleton instance
_orchestrator: AIOrchestrator | None = None


def get_ai_orchestrator(config: OrchestratorConfig | None = None) -> AIOrchestrator:
    """
    Get AI orchestrator singleton.

    Args:
        config: Optional configuration (only used on first call)

    Returns:
        AIOrchestrator instance
    """
    global _orchestrator

    if _orchestrator is None:
        _orchestrator = AIOrchestrator(config=config)

    return _orchestrator
