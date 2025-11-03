"""
Multi-Channel Communication API Endpoints
Handles customer inquiries from Email, SMS, Instagram, Facebook, Phone transcripts
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

from api.ai.endpoints.services.customer_booking_ai import (
    get_customer_booking_ai,
)
from api.ai.endpoints.services.multi_channel_ai_handler import (
    get_multi_channel_handler,
)

router = APIRouter()


class MultiChannelInquiry(BaseModel):
    """Customer inquiry from any communication channel."""

    message: str = Field(..., description="The raw customer message/inquiry")
    channel: str = Field(
        ...,
        description="Communication channel: email, sms, instagram, facebook, phone_transcript, web_chat",
    )
    customer_metadata: dict[str, Any] | None = Field(
        default=None, description="Additional customer metadata (if available)"
    )

    @validator("channel")
    def validate_channel(self, v):
        allowed_channels = ["email", "sms", "instagram", "facebook", "phone_transcript", "web_chat"]
        if v.lower() not in allowed_channels:
            raise ValueError(f"Channel must be one of: {', '.join(allowed_channels)}")
        return v.lower()

    class Config:
        schema_extra = {
            "example": {
                "message": "I'm looking into booking a hibachi experience for 9 people in August of 2026, likely in the Sonoma area. Do you have a quote I could take a look at? Looking forward to hearing from you. Malia -- Malia Nakamura (206)-661-8822",
                "channel": "email",
                "customer_metadata": {
                    "source": "contact_form",
                    "timestamp": "2025-10-31T10:30:00Z",
                },
            }
        }


class ChannelResponse(BaseModel):
    """Formatted AI response for specific channel."""

    channel: str
    response_text: str
    metadata: dict[str, Any]
    suggested_actions: list[str]
    response_time_expectation: str
    ai_metadata: dict[str, Any]


@router.post("/inquiries/process", response_model=ChannelResponse, status_code=status.HTTP_200_OK)
async def process_customer_inquiry(
    inquiry: MultiChannelInquiry,
    multi_channel_handler=Depends(get_multi_channel_handler),
    customer_ai=Depends(get_customer_booking_ai),
):
    """
    Process customer inquiry from any communication channel.

    This endpoint:
    1. Extracts structured information from the message
    2. Determines inquiry type, urgency, and sentiment
    3. Builds channel-specific system prompt
    4. Routes through optimized AI pipeline (cache, intelligent model selection)
    5. Formats response according to channel requirements
    6. Returns response with metadata and suggested actions

    **Supported Channels**:
    - `email`: Professional, detailed responses (max 2000 chars)
    - `sms`: Brief, action-oriented responses (max 160 chars)
    - `instagram`: Casual, enthusiastic with emojis (max 1000 chars)
    - `facebook`: Friendly professional (max 1200 chars)
    - `phone_transcript`: Conversational talking points (max 1500 chars)
    - `web_chat`: Real-time chat responses (max 800 chars)

    **Example Use Cases**:
    - Customer emails quote request → Detailed quote with breakdown
    - Instagram DM "How much?" → Quick price + booking link
    - Phone transcript → Structured talking points for staff
    - SMS inquiry → Brief response with CTA
    """
    start_time = time.time()

    try:
        logger.info(f"📬 Received {inquiry.channel} inquiry: {inquiry.message[:100]}...")

        # Process through multi-channel handler
        response = await multi_channel_handler.process_multi_channel_inquiry(
            message=inquiry.message, channel=inquiry.channel, customer_booking_ai=customer_ai
        )

        processing_time = (time.time() - start_time) * 1000
        logger.info(f"✅ {inquiry.channel} inquiry processed in {processing_time:.2f}ms")

        # Add processing time to response
        response["ai_metadata"]["total_processing_time_ms"] = processing_time

        return ChannelResponse(**response)

    except Exception as e:
        logger.exception(f"❌ Error processing {inquiry.channel} inquiry: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process inquiry: {e!s}",
        )


@router.post(
    "/inquiries/batch", response_model=list[ChannelResponse], status_code=status.HTTP_200_OK
)
async def process_batch_inquiries(
    inquiries: list[MultiChannelInquiry],
    multi_channel_handler=Depends(get_multi_channel_handler),
    customer_ai=Depends(get_customer_booking_ai),
):
    """
    Process multiple customer inquiries in batch (up to 10 at a time).

    Useful for:
    - Processing backlog of messages
    - Handling multiple channels simultaneously
    - Bulk email responses

    **Rate Limit**: Max 10 inquiries per batch
    """
    if len(inquiries) > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum 10 inquiries per batch request"
        )

    start_time = time.time()
    logger.info(f"📬 Processing batch of {len(inquiries)} inquiries")

    responses = []
    for inquiry in inquiries:
        try:
            response = await multi_channel_handler.process_multi_channel_inquiry(
                message=inquiry.message, channel=inquiry.channel, customer_booking_ai=customer_ai
            )
            responses.append(ChannelResponse(**response))
        except Exception as e:
            logger.exception(f"❌ Error processing inquiry in batch: {e!s}")
            # Continue with other inquiries
            continue

    total_time = (time.time() - start_time) * 1000
    logger.info(
        f"✅ Batch processed {len(responses)}/{len(inquiries)} inquiries in {total_time:.2f}ms"
    )

    return responses


class ChannelTestRequest(BaseModel):
    """Test request to see how AI would respond across all channels."""

    message: str = Field(..., description="Customer inquiry to test")

    class Config:
        schema_extra = {"example": {"message": "What payment methods do you accept?"}}


@router.post("/inquiries/test-all-channels", status_code=status.HTTP_200_OK)
async def test_all_channels(
    test_request: ChannelTestRequest,
    multi_channel_handler=Depends(get_multi_channel_handler),
    customer_ai=Depends(get_customer_booking_ai),
):
    """
    Test how the same inquiry would be handled across all channels.

    Returns responses formatted for:
    - Email
    - SMS
    - Instagram
    - Facebook
    - Phone transcript
    - Web chat

    **Use Case**: Training, quality assurance, A/B testing different responses
    """
    channels = ["email", "sms", "instagram", "facebook", "phone_transcript", "web_chat"]

    responses = {}
    for channel in channels:
        try:
            response = await multi_channel_handler.process_multi_channel_inquiry(
                message=test_request.message, channel=channel, customer_booking_ai=customer_ai
            )
            responses[channel] = {
                "response": response["response_text"],
                "length": len(response["response_text"]),
                "model_used": response["ai_metadata"].get("model_used"),
                "cached": response["ai_metadata"].get("from_cache", False),
            }
        except Exception as e:
            logger.exception(f"❌ Error testing {channel}: {e!s}")
            responses[channel] = {"error": str(e)}

    return {"original_message": test_request.message, "responses_by_channel": responses}


class InquiryAnalysis(BaseModel):
    """Request to analyze inquiry without generating response."""

    message: str = Field(..., description="Message to analyze")
    channel: str = Field(default="email", description="Channel context")


@router.post("/inquiries/analyze", status_code=status.HTTP_200_OK)
async def analyze_inquiry(
    analysis_request: InquiryAnalysis, multi_channel_handler=Depends(get_multi_channel_handler)
):
    """
    Analyze customer inquiry to extract structured information.

    Returns:
    - Party size, event date, location
    - Customer name, phone, email
    - Inquiry type (quote, booking, complaint, info)
    - Urgency level (low, normal, high, urgent)
    - Sentiment (positive, neutral, negative)
    - Special requests and dietary restrictions

    **Use Case**: Pre-processing, routing, priority assignment
    """
    try:
        details = await multi_channel_handler.extract_inquiry_details(
            message=analysis_request.message, channel=analysis_request.channel
        )

        return {
            "analysis": details,
            "routing_recommendation": {
                "priority": "high" if details["urgency"] in ["high", "urgent"] else "normal",
                "requires_human_review": details["sentiment"] == "negative"
                or details["urgency"] == "urgent",
                "estimated_response_model": (
                    "gpt-4"
                    if details["inquiry_type"] in ["complaint", "quote"]
                    else "gpt-3.5-turbo"
                ),
            },
        }
    except Exception as e:
        logger.exception(f"❌ Error analyzing inquiry: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze inquiry: {e!s}",
        )


# Include router in main API
def include_multi_channel_router(app):
    """Include multi-channel router in main FastAPI app."""
    app.include_router(
        router, prefix="/api/v1/ai/multi-channel", tags=["AI Multi-Channel Communication"]
    )
