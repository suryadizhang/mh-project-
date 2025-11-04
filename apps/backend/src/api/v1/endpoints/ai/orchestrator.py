"""
AI Orchestrator Endpoint

This endpoint provides access to the AI orchestrator for customer inquiry processing.
It integrates with OpenAI function calling and tool execution.

Author: MyHibachi Development Team
Created: October 31, 2025
Version: 1.0.0 (Phase 1)
Updated: Phase 3 (DI Container integration)
"""

import logging

# Phase 3: Using DI Container pattern
from api.ai.container import get_container
from api.ai.orchestrator import (
    AIOrchestrator,
    OrchestratorRequest,
    OrchestratorResponse,
)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def get_orchestrator() -> AIOrchestrator:
    """
    Dependency to get orchestrator singleton via DI Container.

    Returns:
        AIOrchestrator instance
    """
    try:
        container = get_container()
        return container.get_orchestrator()
    except Exception as e:
        logger.exception(f"Failed to get orchestrator: {e!s}")
        raise HTTPException(status_code=500, detail="Failed to initialize AI orchestrator")


@router.post("/process", response_model=OrchestratorResponse)
async def process_inquiry(
    request: OrchestratorRequest, orchestrator: AIOrchestrator = Depends(get_orchestrator)
):
    """
    Process customer inquiry with AI orchestrator.

    This endpoint:
    1. Receives customer inquiry from any channel
    2. Uses OpenAI function calling to determine tool usage
    3. Executes tools (pricing, travel fees, protein costs)
    4. Generates AI response with tool results
    5. Returns response for admin review

    **Example Request:**
    ```json
    {
        "message": "I need a hibachi chef for 10 adults with filet mignon in Sacramento 95630",
        "channel": "email",
        "customer_context": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "(916) 555-0123",
            "zipcode": "95630"
        }
    }
    ```

    **Example Response:**
    ```json
    {
        "success": true,
        "response": "I'd be happy to help you with a quote! For 10 adults...",
        "tools_used": [
            {
                "tool_name": "calculate_party_quote",
                "parameters": {...},
                "result": {...},
                "execution_time_ms": 150.5,
                "success": true
            }
        ],
        "requires_admin_review": true,
        "conversation_id": "conv_20251031_123456"
    }
    ```

    Args:
        request: Customer inquiry request
        orchestrator: AI orchestrator instance

    Returns:
        AI-generated response with tool execution details

    Raises:
        HTTPException: If inquiry processing fails
    """
    try:
        logger.info(
            "Processing inquiry via orchestrator",
            extra={
                "channel": request.channel,
                "has_customer_id": request.customer_id is not None,
                "has_conversation_id": request.conversation_id is not None,
            },
        )

        # Process inquiry through orchestrator
        response = await orchestrator.process_inquiry(request)

        # Log success
        logger.info(
            "Inquiry processed successfully",
            extra={
                "conversation_id": response.conversation_id,
                "tools_used": len(response.tools_used),
                "success": response.success,
                "requires_admin_review": response.requires_admin_review,
            },
        )

        return response

    except Exception as e:
        logger.error(
            f"Failed to process inquiry: {e!s}",
            exc_info=True,
            extra={
                "channel": request.channel,
                "message_preview": request.message[:100] if request.message else None,
            },
        )

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to process inquiry",
                "message": str(e),
                "fallback": "Please call us at (916) 740-8768 for immediate assistance",
            },
        )


@router.post("/batch-process")
async def batch_process_inquiries(
    requests: list[OrchestratorRequest],
    background_tasks: BackgroundTasks,
    orchestrator: AIOrchestrator = Depends(get_orchestrator),
):
    """
    Process multiple inquiries in batch.

    This endpoint is useful for:
    - Processing multiple customer inquiries at once
    - Bulk email responses
    - Admin review queue processing

    **Example Request:**
    ```json
    [
        {
            "message": "Quote for 10 adults...",
            "channel": "email",
            "customer_context": {...}
        },
        {
            "message": "Quote for 15 adults...",
            "channel": "email",
            "customer_context": {...}
        }
    ]
    ```

    Args:
        requests: List of customer inquiry requests
        background_tasks: FastAPI background tasks
        orchestrator: AI orchestrator instance

    Returns:
        List of AI-generated responses
    """
    if len(requests) > 50:
        raise HTTPException(status_code=400, detail="Maximum 50 inquiries per batch")

    try:
        responses = []
        for request in requests:
            response = await orchestrator.process_inquiry(request)
            responses.append(response)

        logger.info(
            "Batch processing completed",
            extra={
                "count": len(responses),
                "successful": sum(1 for r in responses if r.success),
                "failed": sum(1 for r in responses if not r.success),
            },
        )

        return {"success": True, "count": len(responses), "responses": responses}

    except Exception as e:
        logger.error(f"Batch processing failed: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {e!s}")


@router.get("/config")
async def get_orchestrator_config(orchestrator: AIOrchestrator = Depends(get_orchestrator)):
    """
    Get current orchestrator configuration.

    Returns:
        Current orchestrator configuration including Phase 3 feature flags
    """
    return {
        "config": orchestrator.config.dict(),
        "version": "1.0.0",
        "phase": "Phase 1",
        "tools_available": orchestrator.tool_registry.list_tools(),
        "phase3_features": {
            "rag": {
                "enabled": orchestrator.config.enable_rag,
                "status": "Phase 3 - Data Collection",
                "criteria": "Build IF ai_error_rate >30%",
            },
            "voice": {
                "enabled": orchestrator.config.enable_voice,
                "status": "Phase 3 - Data Collection",
                "criteria": "Build IF phone_call_rate >30%",
            },
            "threading": {
                "enabled": orchestrator.config.enable_threading,
                "status": "Phase 3 - Data Collection",
                "criteria": "Build IF follow_up_rate >50%",
            },
            "identity": {
                "enabled": orchestrator.config.enable_identity,
                "status": "Phase 3 - Data Collection",
                "criteria": "Build IF multi_channel_rate >30%",
            },
        },
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint for orchestrator.

    Returns:
        Health status of orchestrator service
    """
    try:
        # Check if orchestrator can be initialized (via DI Container)
        container = get_container()
        orchestrator = container.get_orchestrator()

        return {
            "status": "healthy",
            "version": "1.0.0",
            "phase": "Phase 3 (DI Container)",
            "tools_count": (
                len(orchestrator.tool_registry.list_tools())
                if hasattr(orchestrator, "tool_registry")
                else "N/A (multi-agent mode)"
            ),
            "openai_configured": (
                bool(orchestrator.client.api_key) if hasattr(orchestrator, "client") else True
            ),
            "using_container": True,
        }
    except Exception as e:
        logger.exception(f"Health check failed: {e!s}")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})


@router.get("/tools")
async def list_tools(orchestrator: AIOrchestrator = Depends(get_orchestrator)):
    """
    List all available tools.

    Returns:
        List of tools with their schemas
    """
    tools = orchestrator.tool_registry.to_openai_functions()

    return {
        "count": len(tools),
        "tools": [
            {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "parameters": tool["function"]["parameters"],
            }
            for tool in tools
        ],
    }
