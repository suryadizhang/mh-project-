"""
Shadow Learning Integration for Chat Service
Automatically logs teacher-student pairs during conversations
"""

import logging
import time
from typing import Any

from api.ai.shadow import (
    get_confidence_predictor,
    get_local_llm_service,
    get_model_router,
    log_tutor_pair,
)
from core.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()


async def process_with_shadow_learning(
    db: AsyncSession,
    message: str,
    intent: str,
    context: dict[str, Any] | None,
    teacher_generate_func,
    **teacher_kwargs,
) -> tuple[str, dict[str, Any]]:
    """
    Process message with automatic shadow learning

    This function:
    1. Predicts confidence for student model
    2. Routes to appropriate model (teacher vs student)
    3. Generates both responses in shadow mode
    4. Logs training pair
    5. Returns appropriate response to customer

    Args:
        db: Database session
        message: User message
        intent: Intent category (faq/quote/booking)
        context: Conversation context
        teacher_generate_func: Function to generate teacher response
        **teacher_kwargs: Args for teacher function

    Returns:
        Tuple of (response_text, metadata)
    """

    if not settings.SHADOW_LEARNING_ENABLED:
        # Shadow learning disabled - use teacher only
        response = await teacher_generate_func(**teacher_kwargs)
        return response, {"model": "openai", "shadow_learning": False}

    # Step 1: Predict confidence
    predictor = get_confidence_predictor()
    confidence = await predictor.predict_confidence(db, message, intent, context)

    # Step 2: Decide routing
    router = get_model_router()
    model_choice = await router.route_message(db, intent, message, confidence, context)

    # Step 3: Generate responses
    teacher_start = time.time()
    teacher_response = await teacher_generate_func(**teacher_kwargs)
    teacher_time_ms = int((time.time() - teacher_start) * 1000)

    # Generate student response (if Ollama available)
    student_response = None
    student_time_ms = None

    try:
        local_llm = get_local_llm_service()
        student_start = time.time()

        student_result = await local_llm.generate_response(
            prompt=message,
            context=str(context) if context else None,
            system_prompt=teacher_kwargs.get("system_prompt"),
        )

        student_time_ms = int((time.time() - student_start) * 1000)
        student_response = student_result.get("response")

    except Exception as e:
        logger.warning(f"Student model generation failed: {e}")
        # Continue with teacher response

    # Step 4: Log training pair (if student generated response)
    if student_response:
        try:
            await log_tutor_pair(
                db=db,
                prompt=message,
                teacher_response=teacher_response,
                student_response=student_response,
                teacher_model="gpt-4",
                student_model="llama3",
                context=str(context) if context else None,
                agent_type=intent,
                teacher_response_time_ms=teacher_time_ms,
                student_response_time_ms=student_time_ms,
                calculate_similarity_score=True,
            )
            await db.commit()

        except Exception as e:
            logger.exception(f"Failed to log tutor pair: {e}")
            # Don't block customer response

    # Step 5: Return appropriate response
    if model_choice == "ollama_local" and student_response:
        # Use student response (active mode)
        logger.info(f"Using LOCAL model for {intent} (confidence: {confidence:.2f})")
        return student_response, {
            "model": "ollama_local",
            "confidence": confidence,
            "shadow_learning": True,
            "response_time_ms": student_time_ms,
        }
    else:
        # Use teacher response (shadow mode or fallback)
        return teacher_response, {
            "model": "openai",
            "confidence": confidence,
            "shadow_learning": bool(student_response),
            "response_time_ms": teacher_time_ms,
        }


async def classify_intent(message: str) -> str:
    """
    Simple intent classification

    Returns: "faq", "quote", or "booking"
    """
    message_lower = message.lower()

    # Booking keywords
    booking_keywords = [
        "book",
        "reserve",
        "schedule",
        "appointment",
        "date",
        "time",
    ]
    if any(keyword in message_lower for keyword in booking_keywords):
        return "booking"

    # Quote keywords
    quote_keywords = ["price", "cost", "quote", "how much", "fee", "charge"]
    if any(keyword in message_lower for keyword in quote_keywords):
        return "quote"

    # Default to FAQ
    return "faq"
