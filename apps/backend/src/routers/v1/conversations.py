"""
Conversation History API Router

Provides endpoints for accessing customer conversation history,
booking-related calls, and transcript search.

Used by: AI agents, customer service dashboards, analytics
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.deps import get_current_admin_user
from models.user import User
from services.conversation_history_service import ConversationHistoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/customer/{customer_id}")
async def get_customer_conversations(
    customer_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Number of conversations to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    include_no_transcript: bool = Query(
        False, description="Include calls without transcripts"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get conversation history for a specific customer.
    
    Returns all call recordings with transcripts, sorted by most recent.
    Includes AI insights, sentiment analysis, and topics.
    
    **Permissions**: Admin only
    
    **Response**:
    - `customer_id`: Customer UUID
    - `customer_name`: Full name
    - `customer_phone`: Phone number
    - `customer_email`: Email address
    - `total_conversations`: Total count (for pagination)
    - `conversations`: List of conversation objects with:
      - `id`: Recording UUID
      - `call_started_at`: ISO timestamp
      - `duration_seconds`: Call duration
      - `call_direction`: "inbound" or "outbound"
      - `transcript_excerpt`: First 200 chars
      - `transcript_full_length`: Total length
      - `transcript_confidence`: 0-100 confidence score
      - `ai_insights`: Sentiment, topics, intent, action items
    - `pagination`: Limit, offset, has_more flag
    
    **Example**:
    ```
    GET /api/v1/conversations/customer/123e4567-e89b-12d3-a456-426614174000?limit=10
    ```
    """
    try:
        service = ConversationHistoryService(db)
        result = await service.get_customer_history(
            customer_id=customer_id,
            limit=limit,
            offset=offset,
            include_no_transcript=include_no_transcript,
        )

        if result.get("error"):
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_customer_conversations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve customer conversations"
        )


@router.get("/booking/{booking_id}")
async def get_booking_conversations(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get all conversations related to a specific booking.
    
    Groups conversations by timeline:
    - **Pre-booking**: Calls before booking date
    - **Day-of**: Calls on booking date
    - **Post-booking**: Calls after booking date
    
    Useful for understanding customer communication patterns and
    identifying common questions or concerns at each stage.
    
    **Permissions**: Admin only
    
    **Response**:
    - `booking_id`: Booking UUID
    - `booking_datetime`: ISO timestamp
    - `booking_status`: Current status
    - `party_size`: Number of guests
    - `customer_id`: Customer UUID
    - `total_conversations`: Total call count
    - `conversations`: Grouped by timeline:
      - `pre_booking`: List of conversations before booking
      - `day_of`: List of conversations on booking day
      - `post_booking`: List of conversations after booking
    - `key_insights`: 
      - `common_topics`: Most discussed topics
      - `sentiment_summary`: Sentiment distribution
    
    **Example**:
    ```
    GET /api/v1/conversations/booking/123e4567-e89b-12d3-a456-426614174000
    ```
    """
    try:
        service = ConversationHistoryService(db)
        result = await service.get_booking_context(booking_id=booking_id)

        if result.get("error"):
            if "not found" in result["error"].lower():
                raise HTTPException(status_code=404, detail=result["error"])
            else:
                raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_booking_conversations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve booking conversations"
        )


@router.get("/customer/{customer_id}/ai-context")
async def get_customer_ai_context(
    customer_id: UUID,
    max_conversations: int = Query(
        5, ge=1, le=10, description="Maximum conversations to include"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get AI-formatted conversation context for a customer.
    
    Returns a concise text summary of recent interactions that AI agents
    can inject into their prompts for personalized service.
    
    **Permissions**: Admin only
    
    **Response**:
    - `customer_id`: Customer UUID
    - `context`: Formatted context string
    
    **Context Format**:
    ```
    Customer: John Smith (555-0123)
    Recent interactions (last 5 calls):
    - 2024-11-15 10:27: Asked about vegetarian options. Positive sentiment.
    - 2024-11-10 14:20: Booking confirmation. Positive sentiment.
    
    Key topics discussed: catering, dietary requirements, parking
    Active booking: 2024-11-15, 30 guests, confirmed
    ```
    
    **Usage**:
    AI agents should prepend this context to their system prompts when
    handling calls or messages from this customer.
    
    **Example**:
    ```
    GET /api/v1/conversations/customer/123e4567-e89b-12d3-a456-426614174000/ai-context
    ```
    """
    try:
        service = ConversationHistoryService(db)
        context = await service.get_ai_context_for_customer(
            customer_id=customer_id, max_conversations=max_conversations
        )

        return {
            "customer_id": str(customer_id),
            "context": context,
            "max_conversations": max_conversations,
        }

    except Exception as e:
        logger.error(f"Error in get_customer_ai_context: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to generate AI context"
        )


@router.get("/search")
async def search_transcripts(
    q: str = Query(..., min_length=3, description="Search query"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    booking_id: Optional[UUID] = Query(None, description="Filter by booking"),
    date_from: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO format)"),
    sentiment: Optional[str] = Query(
        None, regex="^(positive|neutral|negative)$", description="Filter by sentiment"
    ),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Search across all call transcripts.
    
    Performs full-text search on transcript content with optional filters.
    Returns matching conversations with surrounding context highlighted.
    
    **Permissions**: Admin only
    
    **Query Parameters**:
    - `q`: Search query (minimum 3 characters) - **Required**
    - `customer_id`: Filter by specific customer (optional)
    - `booking_id`: Filter by specific booking (optional)
    - `date_from`: Filter calls after date (ISO 8601 format) (optional)
    - `date_to`: Filter calls before date (ISO 8601 format) (optional)
    - `sentiment`: Filter by sentiment: positive, neutral, negative (optional)
    - `limit`: Results per page (1-100, default 50)
    - `offset`: Pagination offset (default 0)
    
    **Response**:
    - `query`: Original search query
    - `total_results`: Total matching conversations
    - `results`: List of conversation objects with:
      - All standard conversation fields
      - `search_context`: Text excerpt showing query in context (±100 chars)
    - `pagination`: Limit, offset, has_more flag
    
    **Examples**:
    ```
    # Search for "vegetarian"
    GET /api/v1/conversations/search?q=vegetarian
    
    # Search with filters
    GET /api/v1/conversations/search?q=party&sentiment=positive&date_from=2024-11-01
    
    # Search for specific customer
    GET /api/v1/conversations/search?q=refund&customer_id=123e4567-e89b-12d3-a456-426614174000
    ```
    
    **Use Cases**:
    - Find all calls mentioning specific topics ("allergy", "refund", "parking")
    - Identify sentiment patterns ("complaint", "thank you")
    - Audit customer interactions
    - Train AI models on conversation patterns
    """
    try:
        service = ConversationHistoryService(db)
        result = await service.search_transcripts(
            query=q,
            customer_id=customer_id,
            booking_id=booking_id,
            date_from=date_from,
            date_to=date_to,
            sentiment=sentiment,
            limit=limit,
            offset=offset,
        )

        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_transcripts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to search transcripts")


@router.get("/stats/sentiment-overview")
async def get_sentiment_overview(
    date_from: Optional[datetime] = Query(None, description="Start date"),
    date_to: Optional[datetime] = Query(None, description="End date"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """
    Get sentiment distribution across conversations.
    
    Provides aggregate statistics about sentiment in call transcripts.
    Useful for monitoring customer satisfaction trends.
    
    **Permissions**: Admin only
    
    **Query Parameters**:
    - `date_from`: Start date for analysis (optional)
    - `date_to`: End date for analysis (optional)
    - `customer_id`: Analyze specific customer only (optional)
    
    **Response**:
    - `total_conversations`: Total analyzed
    - `sentiment_distribution`:
      - `positive`: Count and percentage
      - `neutral`: Count and percentage
      - `negative`: Count and percentage
      - `unknown`: Count and percentage
    - `filters`: Applied filters
    
    **Example**:
    ```
    GET /api/v1/conversations/stats/sentiment-overview?date_from=2024-11-01&date_to=2024-11-30
    ```
    """
    try:
        # This is a placeholder - implement actual stats logic
        # Could use service method or direct SQL aggregation
        
        return {
            "total_conversations": 0,
            "sentiment_distribution": {
                "positive": {"count": 0, "percentage": 0.0},
                "neutral": {"count": 0, "percentage": 0.0},
                "negative": {"count": 0, "percentage": 0.0},
                "unknown": {"count": 0, "percentage": 0.0},
            },
            "filters": {
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "customer_id": str(customer_id) if customer_id else None,
            },
            "message": "Sentiment analysis coming soon",
        }

    except Exception as e:
        logger.error(f"Error in get_sentiment_overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve sentiment overview"
        )
