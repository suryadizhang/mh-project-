"""
Shadow Learning API Endpoints
Health checks, stats, and manual testing for local model
"""

from api.ai.shadow import (
    get_high_quality_pairs,
    get_local_llm_service,
    get_tutor_pair_stats,
)
from core.database import get_db
from fastapi import APIRouter, Body, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/ai/shadow", tags=["Shadow Learning"])


@router.get("/health")
async def shadow_learning_health():
    """
    Check Shadow Learning system health

    Verifies:
    - Ollama service is running
    - Llama-3 model is installed
    - Service connectivity
    """
    llm_service = get_local_llm_service()
    health_status = await llm_service.health_check()

    if health_status["status"] == "unhealthy":
        return {
            **health_status,
            "recommendation": "Please install Ollama and run 'ollama pull llama3'",
        }

    return health_status


@router.get("/model-info")
async def get_shadow_model_info():
    """
    Get detailed information about the local Llama-3 model
    """
    llm_service = get_local_llm_service()
    model_info = await llm_service.get_model_info()

    if model_info is None:
        raise HTTPException(
            status_code=503, detail="Llama-3 model not available. Run 'ollama pull llama3'"
        )

    return model_info


@router.post("/test-generate")
async def test_local_generation(
    prompt: str = Body(..., embed=True),
    context: str | None = Body(None, embed=True),
    system_prompt: str | None = Body(None, embed=True),
):
    """
    Test local model generation

    Use this endpoint to manually test the Llama-3 model
    without logging to the database.
    """
    llm_service = get_local_llm_service()

    result = await llm_service.generate_response(
        prompt=prompt, context=context, system_prompt=system_prompt
    )

    if not result["success"]:
        raise HTTPException(status_code=503, detail=f"Generation failed: {result['error']}")

    return result


@router.get("/stats")
async def get_shadow_learning_stats(days: int = 7, db: AsyncSession = Depends(get_db)):
    """
    Get Shadow Learning training statistics

    Shows how many teacher-student pairs have been collected,
    average similarity scores, and response time comparisons.
    """
    stats = await get_tutor_pair_stats(db, days=days)

    # Add interpretation
    stats["interpretation"] = {
        "readiness": (
            "not_ready"
            if stats["total_pairs"] < 100
            else ("ready" if stats["average_similarity"] >= 0.85 else "training")
        ),
        "quality_assessment": (
            "excellent"
            if stats["average_similarity"] >= 0.9
            else "good" if stats["average_similarity"] >= 0.85 else "needs_improvement"
        ),
        "recommendation": (
            f"Collect {100 - stats['total_pairs']} more pairs"
            if stats["total_pairs"] < 100
            else (
                "Ready for fine-tuning!"
                if stats["average_similarity"] >= 0.85
                else "Continue collecting high-quality pairs"
            )
        ),
    }

    return stats


@router.get("/training-data")
async def get_training_data_preview(
    min_similarity: float = 0.85, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    """
    Preview high-quality training data pairs

    Shows examples of teacher-student pairs that would be
    used for fine-tuning the local model.
    """
    pairs = await get_high_quality_pairs(db, min_similarity=min_similarity, limit=limit)

    return {
        "count": len(pairs),
        "min_similarity": min_similarity,
        "pairs": [
            {
                "id": pair.id,
                "prompt": pair.prompt[:100] + "..." if len(pair.prompt) > 100 else pair.prompt,
                "teacher_response": (
                    pair.teacher_response[:200] + "..."
                    if len(pair.teacher_response) > 200
                    else pair.teacher_response
                ),
                "student_response": (
                    pair.student_response[:200] + "..."
                    if len(pair.student_response) > 200
                    else pair.student_response
                ),
                "similarity_score": pair.similarity_score,
                "teacher_model": pair.teacher_model,
                "student_model": pair.student_model,
                "created_at": pair.created_at.isoformat(),
            }
            for pair in pairs
        ],
    }


@router.get("/readiness")
async def check_deployment_readiness(db: AsyncSession = Depends(get_db)):
    """
    Check if Shadow Learning system is ready for deployment

    Evaluates:
    - Ollama service health
    - Data collection progress
    - Model performance metrics
    """
    # Check Ollama health
    llm_service = get_local_llm_service()
    health = await llm_service.health_check()

    # Get training stats
    stats = await get_tutor_pair_stats(db, days=30)

    # Determine readiness
    ollama_ready = health["status"] == "healthy" and health.get("llama3_installed", False)
    data_ready = stats["total_pairs"] >= 100
    quality_ready = stats["average_similarity"] >= 0.85

    overall_ready = ollama_ready and data_ready and quality_ready

    return {
        "ready_for_deployment": overall_ready,
        "checklist": {
            "ollama_installed": ollama_ready,
            "sufficient_training_data": data_ready,
            "high_quality_responses": quality_ready,
        },
        "details": {
            "ollama_status": health["status"],
            "llama3_installed": health.get("llama3_installed", False),
            "total_pairs_collected": stats["total_pairs"],
            "minimum_pairs_required": 100,
            "average_similarity": stats["average_similarity"],
            "target_similarity": 0.85,
        },
        "next_steps": (
            ["System is ready for shadow mode deployment!"]
            if overall_ready
            else [
                "Install Ollama and run 'ollama pull llama3'" if not ollama_ready else None,
                (
                    f"Collect {100 - stats['total_pairs']} more training pairs"
                    if not data_ready
                    else None
                ),
                (
                    "Improve response quality (current avg: {:.2f}, target: 0.85)".format(
                        stats["average_similarity"]
                    )
                    if not quality_ready
                    else None
                ),
            ]
        ),
    }
