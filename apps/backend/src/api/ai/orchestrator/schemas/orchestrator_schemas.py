"""
Request/Response Schemas for AI Orchestrator

These Pydantic models define the input and output formats for the orchestrator.
Used for API endpoints and validation.

Author: MyHibachi Development Team
Created: October 31, 2025
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class OrchestratorRequest(BaseModel):
    """
    Request to the AI orchestrator.
    
    Attributes:
        message: Customer inquiry message
        channel: Communication channel (email, phone, instagram, etc.)
        customer_id: Optional customer identifier
        customer_context: Optional additional context (email, phone, name, etc.)
        conversation_id: Optional existing conversation ID
        metadata: Additional request metadata
    """
    message: str = Field(..., description="Customer inquiry message", min_length=1)
    channel: str = Field(
        default="email",
        description="Communication channel (email, phone, instagram, facebook, tiktok, sms)"
    )
    customer_id: Optional[str] = Field(None, description="Customer identifier if known")
    customer_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Customer context (email, phone, name, address, etc.)"
    )
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional request metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "I need a hibachi chef for 10 adults with filet mignon in 95630",
                "channel": "email",
                "customer_context": {
                    "email": "customer@example.com",
                    "name": "John Doe",
                    "zipcode": "95630"
                }
            }
        }


class ToolCall(BaseModel):
    """
    Record of a tool execution.
    
    Attributes:
        tool_name: Name of the tool executed
        parameters: Parameters passed to the tool
        result: Tool execution result
        execution_time_ms: Execution time in milliseconds
        success: Whether execution succeeded
    """
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    execution_time_ms: float
    success: bool


class OrchestratorResponse(BaseModel):
    """
    Response from the AI orchestrator.
    
    Attributes:
        success: Whether request was processed successfully
        response: AI-generated response text
        tools_used: List of tools that were executed
        metadata: Response metadata (costs, timing, etc.)
        error: Error message if request failed
        requires_admin_review: Whether response needs admin approval
        conversation_id: Conversation identifier
    """
    success: bool
    response: str
    tools_used: List[ToolCall] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    requires_admin_review: bool = False
    conversation_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "Great! For 10 adults with filet mignon in 95630, your total is $575.00...",
                "tools_used": [
                    {
                        "tool_name": "calculate_party_quote",
                        "parameters": {"adults": 10, "protein_selections": {"filet_mignon": 10}},
                        "result": {"total": 575.00},
                        "execution_time_ms": 45.2,
                        "success": True
                    }
                ],
                "metadata": {
                    "model": "gpt-4-turbo-preview",
                    "total_tokens": 850,
                    "total_time_ms": 1250
                },
                "requires_admin_review": False,
                "conversation_id": "conv_20251031_143022"
            }
        }


class OrchestratorConfig(BaseModel):
    """
    Configuration for the AI orchestrator.
    
    Attributes:
        model: OpenAI model to use
        temperature: Sampling temperature (0.0-1.0)
        max_tokens: Maximum tokens in response
        enable_rag: Enable RAG knowledge retrieval (Phase 3)
        enable_voice: Enable voice AI features (Phase 3)
        enable_threading: Enable conversation threading (Phase 3)
        enable_identity: Enable identity resolution (Phase 3)
        auto_admin_review: Automatically send to admin review
    """
    model: str = Field(
        default="gpt-4-turbo-preview",
        description="OpenAI model name"
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sampling temperature (lower = more focused)"
    )
    max_tokens: int = Field(
        default=1500,
        ge=100,
        le=4000,
        description="Maximum tokens in response"
    )
    enable_rag: bool = Field(
        default=False,
        description="Enable RAG knowledge base (Phase 3)"
    )
    enable_voice: bool = Field(
        default=False,
        description="Enable voice AI (Phase 3)"
    )
    enable_threading: bool = Field(
        default=False,
        description="Enable conversation threading (Phase 3)"
    )
    enable_identity: bool = Field(
        default=False,
        description="Enable identity resolution (Phase 3)"
    )
    auto_admin_review: bool = Field(
        default=True,
        description="Automatically send responses to admin review"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4-turbo-preview",
                "temperature": 0.3,
                "max_tokens": 1500,
                "enable_rag": False,
                "enable_voice": False,
                "enable_threading": False,
                "enable_identity": False,
                "auto_admin_review": True
            }
        }
