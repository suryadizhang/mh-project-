"""
AI Orchestrator - Main Orchestration Engine

This is the central orchestrator that manages tool execution, OpenAI function calling,
and response generation. It integrates with existing services while maintaining
modularity and scalability.

Architecture:
- Uses existing pricing_service.py and protein_calculator_service.py
- Integrates with multi_channel_ai_handler.py for channel-specific formatting
- Supports admin review workflow via email_review.py
- ChatGPT-ready design with Phase 3 extension points

Author: MyHibachi Development Team
Created: October 31, 2025
Version: 1.0.0 (Phase 1)
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

import openai
from openai import OpenAI

from .tools import (
    BaseTool,
    ToolRegistry,
    PricingTool,
    TravelFeeTool,
    ProteinTool
)
from .schemas import (
    OrchestratorRequest,
    OrchestratorResponse,
    OrchestratorConfig,
    ToolCall
)
from .services import (
    get_conversation_service,
    get_rag_service,
    get_voice_service,
    get_identity_resolver
)

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Main orchestrator for AI-powered customer inquiry handling.
    
    This orchestrator:
    1. Receives customer inquiries via OrchestratorRequest
    2. Determines which tools to use via OpenAI function calling
    3. Executes tools (pricing, travel fees, protein costs)
    4. Feeds results back to OpenAI for final response
    5. Returns formatted response via OrchestratorResponse
    
    Phase 1 Features:
    - Tool calling (pricing, travel, protein)
    - OpenAI GPT-4 Turbo integration
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
        ```
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """
        Initialize the AI orchestrator.
        
        Args:
            config: Optional configuration (uses defaults if not provided)
        """
        self.config = config or OrchestratorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=api_key)
        
        # Initialize tool registry
        self.tool_registry = ToolRegistry()
        self._register_tools()
        
        # Initialize services
        self.conversation_service = get_conversation_service(
            enable_threading=self.config.enable_threading
        )
        self.rag_service = get_rag_service(
            enable_rag=self.config.enable_rag
        )
        self.voice_service = get_voice_service(
            enable_voice=self.config.enable_voice
        )
        self.identity_resolver = get_identity_resolver(
            enable_identity=self.config.enable_identity
        )
        
        self.logger.info(
            f"AIOrchestrator initialized",
            extra={
                "model": self.config.model,
                "phase": "Phase 1",
                "tools_registered": len(self.tool_registry.list_tools()),
                "phase3_features_enabled": {
                    "rag": self.config.enable_rag,
                    "voice": self.config.enable_voice,
                    "threading": self.config.enable_threading,
                    "identity": self.config.enable_identity
                }
            }
        )
    
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
            extra={"tools": self.tool_registry.list_tools()}
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
            "tiktok": "energetic and engaging"
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
    
    async def process_inquiry(
        self,
        request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """
        Process customer inquiry with AI orchestration.
        
        This is the main entry point that:
        1. Resolves customer identity (Phase 3)
        2. Retrieves conversation history (Phase 3)
        3. Gets RAG knowledge context (Phase 3)
        4. Calls OpenAI with function calling
        5. Executes requested tools
        6. Generates final response
        
        Args:
            request: Customer inquiry request
        
        Returns:
            Orchestrator response with AI-generated reply and tool usage
        """
        start_time = datetime.now()
        
        try:
            # Step 1: Resolve customer identity (Phase 3 - currently no-op)
            customer_id = await self.identity_resolver.resolve_identity(
                email=request.customer_context.get("email"),
                phone=request.customer_context.get("phone"),
                name=request.customer_context.get("name")
            ) or request.customer_id
            
            # Step 2: Create/retrieve conversation
            if not request.conversation_id:
                request.conversation_id = await self.conversation_service.create_conversation(
                    customer_id=customer_id,
                    channel=request.channel,
                    message=request.message
                )
            
            # Step 3: Get conversation history (Phase 3 - currently empty)
            history = await self.conversation_service.get_conversation_history(
                request.conversation_id
            )
            
            # Step 4: Retrieve RAG knowledge (Phase 3 - currently None)
            rag_knowledge = await self.rag_service.retrieve_knowledge(
                request.message
            )
            
            # Step 5: Build messages for OpenAI
            messages = self._build_messages(
                request.message,
                request.channel,
                request.customer_context,
                history,
                rag_knowledge
            )
            
            # Step 6: Call OpenAI with function calling
            tools_used = []
            response_text = await self._call_openai_with_tools(
                messages,
                tools_used
            )
            
            # Step 7: Add message to conversation (Phase 3 - currently no-op)
            await self.conversation_service.add_message(
                conversation_id=request.conversation_id,
                role="user",
                content=request.message
            )
            await self.conversation_service.add_message(
                conversation_id=request.conversation_id,
                role="assistant",
                content=response_text
            )
            
            # Step 8: Calculate metadata
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Step 9: Determine if admin review needed
            requires_admin_review = self.config.auto_admin_review
            
            # Step 10: Build response
            response = OrchestratorResponse(
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
                    "phase": "Phase 1",
                    "phase3_features_used": {
                        "rag": rag_knowledge is not None,
                        "threading": len(history) > 0,
                        "identity": customer_id != request.customer_id
                    }
                }
            )
            
            self.logger.info(
                f"Inquiry processed successfully",
                extra={
                    "conversation_id": request.conversation_id,
                    "tools_used": [t.tool_name for t in tools_used],
                    "execution_time_ms": execution_time_ms
                }
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                f"Inquiry processing failed: {str(e)}",
                exc_info=True,
                extra={"request": request.dict()}
            )
            
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            return OrchestratorResponse(
                success=False,
                response="I apologize, but I'm having trouble processing your inquiry right now. Please call us at (916) 740-8768 and we'll help you immediately!",
                error=str(e),
                requires_admin_review=True,
                metadata={
                    "execution_time_ms": round(execution_time_ms, 2),
                    "error_type": type(e).__name__
                }
            )
    
    def _build_messages(
        self,
        message: str,
        channel: str,
        customer_context: Dict[str, Any],
        history: List[Dict[str, Any]],
        rag_knowledge: Optional[List[Dict[str, Any]]]
    ) -> List[Dict[str, str]]:
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
        messages = [
            {
                "role": "system",
                "content": self._build_system_prompt(channel)
            }
        ]
        
        # Add conversation history (Phase 3)
        for msg in history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        # Add RAG knowledge context (Phase 3)
        if rag_knowledge:
            knowledge_text = "\n\n".join([
                f"**Knowledge**: {doc.get('content', '')}"
                for doc in rag_knowledge
            ])
            messages.append({
                "role": "system",
                "content": f"**Additional Context**:\n{knowledge_text}"
            })
        
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
                messages.append({
                    "role": "system",
                    "content": f"**Customer Context**: {', '.join(context_parts)}"
                })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": message
        })
        
        return messages
    
    async def _call_openai_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools_used: List[ToolCall]
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
            extra={"tools": [t["function"]["name"] for t in tool_schemas]}
        )
        
        # Initial OpenAI call with tools
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto",  # Let AI decide when to use tools
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        message = response.choices[0].message
        
        # Check if AI wants to use tools
        if message.tool_calls:
            self.logger.info(
                f"AI requested {len(message.tool_calls)} tool calls",
                extra={"tools": [tc.function.name for tc in message.tool_calls]}
            )
            
            # Add assistant message to history
            messages.append({
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })
            
            # Execute each tool call
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                self.logger.info(
                    f"Executing tool: {tool_name}",
                    extra={"arguments": tool_args}
                )
                
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
                tools_used.append(ToolCall(
                    tool_name=tool_name,
                    parameters=tool_args,
                    result=tool_result.data or {},
                    execution_time_ms=round(tool_time_ms, 2),
                    success=tool_result.success
                ))
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(tool_result.dict())
                })
            
            # Call OpenAI again with tool results
            final_response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            return final_response.choices[0].message.content
        
        else:
            # No tools used, return direct response
            return message.content


# Singleton instance
_orchestrator: Optional[AIOrchestrator] = None


def get_ai_orchestrator(config: Optional[OrchestratorConfig] = None) -> AIOrchestrator:
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
