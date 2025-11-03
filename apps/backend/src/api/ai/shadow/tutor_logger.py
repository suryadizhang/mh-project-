"""
Tutor Logger Service - Shadow Learning
Records teacher-student response pairs for training
"""

from datetime import datetime
import logging
from typing import Any

from api.ai.shadow.models import AITutorPair
from api.ai.shadow.similarity_evaluator import calculate_similarity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def log_tutor_pair(
    db: AsyncSession,
    prompt: str,
    teacher_response: str,
    student_response: str,
    teacher_model: str = "gpt-4",
    student_model: str = "llama3",
    context: str | None = None,
    agent_type: str | None = None,
    teacher_tokens: int | None = None,
    student_tokens: int | None = None,
    teacher_cost_usd: float | None = None,
    teacher_response_time_ms: int | None = None,
    student_response_time_ms: int | None = None,
    calculate_similarity_score: bool = True,
) -> AITutorPair:
    """
    Log a teacher-student response pair for Shadow Learning

    This records both the teacher (OpenAI) and student (Llama-3) responses
    to the same prompt, along with similarity metrics.

    Args:
        db: Database session
        prompt: User's original prompt
        teacher_response: Response from teacher model (OpenAI)
        student_response: Response from student model (Llama-3)
        teacher_model: Name of teacher model
        student_model: Name of student model
        context: Conversation context/history
        agent_type: Which AI agent type handled this
        teacher_tokens: Token count for teacher response
        student_tokens: Token count for student response
        teacher_cost_usd: Cost of teacher API call
        teacher_response_time_ms: Response time for teacher
        student_response_time_ms: Response time for student
        calculate_similarity_score: Whether to calculate similarity

    Returns:
        AITutorPair: Created database record
    """

    # Calculate similarity if enabled
    similarity_score = None
    if calculate_similarity_score and teacher_response and student_response:
        try:
            similarity_score = await calculate_similarity(teacher_response, student_response)
            logger.info(f"Similarity score: {similarity_score:.3f}")
        except Exception as e:
            logger.warning(f"Failed to calculate similarity: {e}")

    # Create tutor pair record
    tutor_pair = AITutorPair(
        prompt=prompt,
        context=context,
        agent_type=agent_type,
        teacher_model=teacher_model,
        teacher_response=teacher_response,
        teacher_tokens=teacher_tokens,
        teacher_cost_usd=teacher_cost_usd,
        teacher_response_time_ms=teacher_response_time_ms,
        student_model=student_model,
        student_response=student_response,
        student_tokens=student_tokens,
        student_response_time_ms=student_response_time_ms,
        similarity_score=similarity_score,
        quality_score=None,  # To be set by human review or automated eval
        used_in_production=False,  # Always false in shadow mode
        customer_feedback=None,
        created_at=datetime.utcnow(),
    )

    db.add(tutor_pair)
    await db.commit()
    await db.refresh(tutor_pair)

    logger.info(
        f"Logged tutor pair {tutor_pair.id}: "
        f"similarity={similarity_score:.3f if similarity_score else 'N/A'}, "
        f"teacher_time={teacher_response_time_ms}ms, "
        f"student_time={student_response_time_ms}ms"
    )

    return tutor_pair


async def get_high_quality_pairs(
    db: AsyncSession,
    min_similarity: float = 0.85,
    limit: int = 100,
    agent_type: str | None = None,
) -> list[AITutorPair]:
    """
    Get high-quality tutor pairs for training data export

    Args:
        db: Database session
        min_similarity: Minimum similarity threshold
        limit: Maximum number of pairs to return
        agent_type: Filter by specific agent type

    Returns:
        List of high-quality AITutorPair records
    """

    query = select(AITutorPair).where(AITutorPair.similarity_score >= min_similarity)

    if agent_type:
        query = query.where(AITutorPair.agent_type == agent_type)

    query = query.order_by(AITutorPair.similarity_score.desc()).limit(limit)

    result = await db.execute(query)
    pairs = result.scalars().all()

    logger.info(f"Retrieved {len(pairs)} high-quality pairs " f"(min_similarity={min_similarity})")

    return list(pairs)


async def get_tutor_pair_stats(db: AsyncSession, days: int = 7) -> dict[str, Any]:
    """
    Get statistics about tutor pair collection

    Args:
        db: Database session
        days: Number of days to analyze

    Returns:
        dict: Statistics about collected pairs
    """
    from datetime import timedelta

    from sqlalchemy import func

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Total pairs
    total_query = select(func.count(AITutorPair.id))
    total_result = await db.execute(total_query)
    total_pairs = total_result.scalar() or 0

    # Recent pairs
    recent_query = select(func.count(AITutorPair.id)).where(AITutorPair.created_at >= cutoff_date)
    recent_result = await db.execute(recent_query)
    recent_pairs = recent_result.scalar() or 0

    # Average similarity
    avg_similarity_query = select(func.avg(AITutorPair.similarity_score)).where(
        AITutorPair.similarity_score.isnot(None)
    )
    avg_result = await db.execute(avg_similarity_query)
    avg_similarity = avg_result.scalar() or 0.0

    # High quality count (>= 0.85 similarity)
    high_quality_query = select(func.count(AITutorPair.id)).where(
        AITutorPair.similarity_score >= 0.85
    )
    high_quality_result = await db.execute(high_quality_query)
    high_quality_count = high_quality_result.scalar() or 0

    # Response time comparison
    avg_teacher_time_query = select(func.avg(AITutorPair.teacher_response_time_ms)).where(
        AITutorPair.teacher_response_time_ms.isnot(None)
    )
    teacher_time_result = await db.execute(avg_teacher_time_query)
    avg_teacher_time = teacher_time_result.scalar() or 0

    avg_student_time_query = select(func.avg(AITutorPair.student_response_time_ms)).where(
        AITutorPair.student_response_time_ms.isnot(None)
    )
    student_time_result = await db.execute(avg_student_time_query)
    avg_student_time = student_time_result.scalar() or 0

    return {
        "total_pairs": total_pairs,
        "recent_pairs_last_n_days": recent_pairs,
        "days_analyzed": days,
        "average_similarity": round(float(avg_similarity), 3),
        "high_quality_pairs": high_quality_count,
        "high_quality_percentage": (
            round((high_quality_count / total_pairs) * 100, 1) if total_pairs > 0 else 0.0
        ),
        "avg_teacher_response_ms": round(avg_teacher_time, 0),
        "avg_student_response_ms": round(avg_student_time, 0),
        "student_speedup": (
            round(avg_teacher_time / avg_student_time, 2) if avg_student_time > 0 else 0.0
        ),
    }
