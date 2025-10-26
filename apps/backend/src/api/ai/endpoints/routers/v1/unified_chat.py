"""
Unified Agent-Aware Chat API
Single endpoint with X-Agent header routing for all AI interactions.
Implements proper agent scoping, tool permissions, and prompt isolation.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from api.ai.endpoints.database import get_db
from api.ai.endpoints.services.agent_gateway import StationAwareAgentGatewayService
from api.ai.endpoints.services.prompt_registry import PromptRegistryService
from api.ai.endpoints.services.tool_registry import ToolRegistryService
from api.ai.endpoints.services.model_ladder import ModelLadderService
from api.ai.endpoints.services.monitoring import MonitoringService

# Station-aware dependencies
from api.ai.endpoints.auth import get_station_context_optional, has_agent_access, StationContext

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["v1-unified-chat"])

# Pydantic models for unified chat API
class UnifiedChatRequest(BaseModel):
    """Unified chat request supporting all agent types."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message": "I want to book a hibachi chef for my party",
            "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
            "user_id": "customer_123",
            "context": {
                "location": "San Francisco",
                "party_size": 12
            },
            "stream": False
        }
    })
    
    message: str = Field(..., min_length=1, max_length=4000, description="The user's message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for continuity")
    user_id: Optional[str] = Field(None, description="User identifier for personalization")
    context: Optional[Dict[str, Any]] = None
    stream: bool = Field(default=False, description="Enable streaming response")
    model_override: Optional[str] = Field(None, description="Force specific model selection")


class UnifiedChatResponse(BaseModel):
    """Unified chat response with agent-aware metadata."""
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "message_id": "msg_123456",
            "conversation_id": "conv_789012",
            "agent": "customer",
            "content": "I'd be happy to help you book a hibachi chef! Let me gather some details...",
            "timestamp": "2024-12-19T10:30:00Z",
            "confidence": 0.92,
            "model_used": "gpt-4-mini",
            "intent": "booking_inquiry",
            "suggestions": ["Tell me about pricing", "What's included?", "Check availability"],
            "agent_capabilities": {
                "can_book": True,
                "can_manage_users": False,
                "can_view_analytics": False
            },
            "tools_used": ["booking_search"],
            "cost": {"input_tokens": 0.001, "output_tokens": 0.002},
            "station_context": {
                "station_id": 1,
                "station_name": "Main Location",
                "role": "customer_support"
            },
            "permission_level": "station_scoped"
        }
    })
    
    message_id: str = Field(..., description="Unique message identifier")
    conversation_id: str = Field(..., description="Conversation identifier")
    agent: str = Field(..., description="Agent that processed the request")
    content: str = Field(..., description="AI response content")
    timestamp: datetime = Field(..., description="Response timestamp")
    confidence: float = Field(..., description="AI confidence score (0-1)")
    model_used: str = Field(..., description="Model that generated the response")
    intent: Optional[str] = Field(None, description="Detected user intent")
    suggestions: Optional[List[str]] = Field(None, description="Suggested follow-up questions")
    actions: Optional[List[Dict[str, Any]]] = Field(None, description="Available actions")
    escalation: Optional[Dict[str, Any]] = Field(None, description="Escalation information if needed")
    
    # Agent-aware metadata
    agent_capabilities: Dict[str, bool] = Field(..., description="Current agent capabilities")
    tools_used: List[str] = []
    cost: Optional[Dict[str, float]] = Field(None, description="Request cost breakdown")
    
    # Station-aware metadata
    station_context: Optional[Dict[str, Any]] = Field(None, description="Station context information")
    permission_level: str = Field(..., description="Permission level used for request")


class StreamChatResponse(BaseModel):
    """Streaming chat response chunk."""
    chunk_id: str = Field(..., description="Chunk identifier")
    message_id: str = Field(..., description="Parent message identifier")
    content: str = Field(..., description="Content chunk")
    is_final: bool = Field(default=False, description="Whether this is the final chunk")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata")


# Agent detection and validation
def detect_agent_from_request(
    x_agent: Optional[str] = Header(None, description="Agent identifier"),
    user_agent: Optional[str] = Header(None),
    request: Request = None,
    station_context: Optional[StationContext] = Depends(get_station_context_optional)
) -> str:
    """
    Detect agent type from request headers and context.
    Validates agent access based on station permissions.
    
    Priority:
    1. Explicit X-Agent header (if permitted by station context)
    2. User-Agent analysis
    3. Request path analysis
    4. Station role-based default
    5. Default to 'customer'
    """
    # Explicit agent header
    if x_agent:
        valid_agents = ["customer", "admin", "staff", "support", "analytics"]
        if x_agent.lower() in valid_agents:
            requested_agent = x_agent.lower()
            # Check if station context allows this agent
            if has_agent_access(station_context, requested_agent):
                return requested_agent
            else:
                logger.warning(f"Station context denied access to agent: {requested_agent}")
        else:
            logger.warning(f"Invalid X-Agent header: {x_agent}")
    
    # Analyze User-Agent for admin interfaces
    if user_agent:
        if "admin" in user_agent.lower() or "backstage" in user_agent.lower():
            if has_agent_access(station_context, "admin"):
                return "admin"
    
    # Analyze request path
    if request:
        path = str(request.url.path)
        if "/admin/" in path and has_agent_access(station_context, "admin"):
            return "admin"
        elif "/staff/" in path and has_agent_access(station_context, "staff"):
            return "staff"
    
    # Station role-based defaults
    if station_context:
        if station_context.role in ["super_admin", "admin"]:
            return "admin"
        elif station_context.role == "station_admin":
            return "staff"
        elif station_context.role == "customer_support":
            return "support"
    
    # Default to customer agent (always available)
    return "customer"


@router.post("/chat", response_model=UnifiedChatResponse)
async def unified_chat(
    request: UnifiedChatRequest,
    agent: str = Depends(detect_agent_from_request),
    station_context: Optional[StationContext] = Depends(get_station_context_optional),
    db: Session = Depends(get_db)
) -> UnifiedChatResponse:
    """
    Unified chat endpoint with agent-aware routing and station-scoped permissions.
    
    This endpoint handles all AI chat interactions through agent-specific routing:
    - Customer agent: Booking and general inquiries (public access)
    - Admin agent: Full management capabilities (admin/super_admin roles)
    - Staff agent: Operational guidance and limited management (station_admin+ roles)
    - Support agent: Customer service and escalation handling (customer_support+ roles)
    - Analytics agent: Data queries and reporting (admin+ roles)
    
    Headers:
    - X-Agent: Explicitly specify agent type (customer, admin, staff, support, analytics)
    - Authorization: Bearer token with station context for enhanced permissions
    
    Station Context:
    - Requests without station context default to customer agent with public access
    - Station-scoped tokens enable access to additional agents based on role
    - Multi-tenant data isolation enforced through station context
    - Permissions validated against station-specific RBAC rules
    """
    start_time = datetime.utcnow()
    message_id = str(uuid4())
    conversation_id = request.conversation_id or str(uuid4())
    
    try:
        # Initialize services
        gateway = StationAwareAgentGatewayService()
        monitoring = MonitoringService()
        
        # Log request
        await monitoring.log_request(
            message_id=message_id,
            agent=agent,
            user_id=request.user_id,
            message=request.message,
            context=request.context
        )
        
        # Validate agent and get capabilities
        agent_info = await gateway.validate_agent(agent)
        if not agent_info["valid"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent: {agent}. {agent_info.get('error', '')}"
            )
        
        # Process request through agent gateway with station context
        response_data = await gateway.process_request(
            agent=agent,
            message=request.message,
            conversation_id=conversation_id,
            user_id=request.user_id,
            context=request.context,
            model_override=request.model_override,
            station_context=station_context
        )
        
        # Build response with station context
        station_info = None
        permission_level = "public"
        
        if station_context:
            station_info = {
                "station_id": station_context.station_id,
                "station_name": station_context.station_name,
                "role": station_context.role,
                "permissions_count": len(station_context.permissions)
            }
            permission_level = "station_scoped" if not station_context.is_super_admin else "super_admin"
        
        response = UnifiedChatResponse(
            message_id=message_id,
            conversation_id=conversation_id,
            agent=agent,
            content=response_data["content"],
            timestamp=datetime.utcnow(),
            confidence=response_data["confidence"],
            model_used=response_data["model_used"],
            intent=response_data.get("intent"),
            suggestions=response_data.get("suggestions", []),
            actions=response_data.get("actions", []),
            escalation=response_data.get("escalation"),
            agent_capabilities=agent_info["capabilities"],
            tools_used=response_data.get("tools_used", []),
            cost=response_data.get("cost"),
            station_context=station_info,
            permission_level=permission_level
        )
        
        # Log response
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        await monitoring.log_response(
            message_id=message_id,
            agent=agent,
            response=response,
            processing_time=processing_time
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified chat error: {e}")
        await monitoring.log_error(
            message_id=message_id,
            agent=agent,
            error=str(e),
            context=request.context
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to process chat request"
        )


@router.post("/chat/stream")
async def unified_chat_stream(
    request: UnifiedChatRequest,
    agent: str = Depends(detect_agent_from_request),
    station_context: Optional[StationContext] = Depends(get_station_context_optional),
    db: Session = Depends(get_db)
):
    """
    Streaming version of unified chat endpoint.
    
    Returns Server-Sent Events (SSE) stream for real-time response generation.
    """
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate_stream():
        message_id = str(uuid4())
        conversation_id = request.conversation_id or str(uuid4())
        
        try:
            gateway = StationAwareAgentGatewayService()
            
            # Validate agent
            agent_info = await gateway.validate_agent(agent)
            if not agent_info["valid"]:
                error_chunk = StreamChatResponse(
                    chunk_id=str(uuid4()),
                    message_id=message_id,
                    content=f"Error: Invalid agent {agent}",
                    is_final=True,
                    metadata={"error": True}
                )
                yield f"data: {error_chunk.json()}\n\n"
                return
            
            # Stream response with station context
            async for chunk in gateway.stream_response(
                agent=agent,
                message=request.message,
                conversation_id=conversation_id,
                user_id=request.user_id,
                context=request.context,
                station_context=station_context
            ):
                stream_chunk = StreamChatResponse(
                    chunk_id=str(uuid4()),
                    message_id=message_id,
                    content=chunk["content"],
                    is_final=chunk.get("is_final", False),
                    metadata=chunk.get("metadata")
                )
                yield f"data: {stream_chunk.json()}\n\n"
                
                if chunk.get("is_final"):
                    break
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_chunk = StreamChatResponse(
                chunk_id=str(uuid4()),
                message_id=message_id,
                content=f"Error: {str(e)}",
                is_final=True,
                metadata={"error": True}
            )
            yield f"data: {error_chunk.json()}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/agents")
async def list_agents():
    """
    List available agents and their capabilities.
    
    Returns information about all available agents, their capabilities,
    and current status.
    """
    try:
        gateway = StationAwareAgentGatewayService()
        agents = await gateway.list_agents()
        
        return {
            "agents": agents,
            "total": len(agents),
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve agent information"
        )


@router.get("/agents/{agent_name}")
async def get_agent_info(agent_name: str):
    """
    Get detailed information about a specific agent.
    
    Returns capabilities, tools, permissions, and current status.
    """
    try:
        gateway = StationAwareAgentGatewayService()
        agent_info = await gateway.get_agent_details(agent_name)
        
        if not agent_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent '{agent_name}' not found"
            )
        
        return agent_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve agent information"
        )


@router.get("/health")
async def unified_api_health():
    """
    Health check for unified API system.
    
    Returns status of all agent-aware components.
    """
    try:
        gateway = StationAwareAgentGatewayService()
        prompt_registry = PromptRegistryService()
        tool_registry = ToolRegistryService()
        model_ladder = ModelLadderService()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "components": {
                "agent_gateway": await gateway.health_check(),
                "prompt_registry": await prompt_registry.health_check(),
                "tool_registry": await tool_registry.health_check(),
                "model_ladder": await model_ladder.health_check()
            },
            "features": {
                "station_aware": True,
                "rbac_enabled": True,
                "multi_tenant": True
            }
        }
        
        # Check if any component is unhealthy
        if any(not comp["healthy"] for comp in health_status["components"].values()):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }


# Export router
__all__ = ["router"]