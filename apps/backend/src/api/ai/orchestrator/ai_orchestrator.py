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

# Phase 1A: Import router and provider
try:
    from ..routers import get_intent_router

    ROUTER_ENABLED = True
except ImportError:
    ROUTER_ENABLED = False
    logger = logging.getLogger(__name__)
    logger.warning("Intent router not available - using legacy mode")

try:
    from .providers import get_provider

    PROVIDER_ENABLED = True
except ImportError:
    PROVIDER_ENABLED = False
    logger = logging.getLogger(__name__)
    logger.warning("Model provider not available - using OpenAI client directly")

logger = logging.getLogger(__name__)


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

    def __init__(self, config: OrchestratorConfig | None = None, use_router: bool = True):
        """
        Initialize the AI orchestrator.

        Args:
            config: Optional configuration (uses defaults if not provided)
            use_router: Whether to use Intent Router (default: True)
        """
        self.config = config or OrchestratorConfig()
        self.logger = logging.getLogger(__name__)
        self.use_router = use_router and ROUTER_ENABLED

        # Initialize router (Phase 1A)
        if self.use_router:
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

        # Initialize provider (Phase 1A)
        if PROVIDER_ENABLED:
            self.provider = get_provider()
            self.logger.info(f"Model provider initialized: {self.provider.__class__.__name__}")
        else:
            self.provider = None

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

        Args:
            channel: Communication channel (email, sms, instagram, etc.)

        Returns:
            System prompt string
        """
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

        return f"""You are an AI assistant for My Hibachi Chef, a premier hibachi catering service in Sacramento, CA.

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
4. Include contact info for booking: (916) 740-8768 or email
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

            # Phase 1A: Route to specialized agent
            if self.use_router:
                response = await self._process_with_router(
                    request, customer_id, conversation_history, start_time
                )
            else:
                # Legacy: Direct OpenAI call
                response = await self._process_with_legacy(
                    request, customer_id, conversation_history, start_time
                )

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
