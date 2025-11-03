"""
AI Readiness & Monitoring API Endpoints
Complete dashboard for Shadow Learning monitoring and activation
"""

import logging

from api.ai.shadow.confidence_predictor import get_confidence_predictor
from api.ai.shadow.model_router import get_model_router
from api.ai.shadow.quality_monitor import get_quality_monitor
from api.ai.shadow.readiness_service import get_readiness_service
from core.config import get_settings
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/ai/readiness", tags=["AI Readiness & Monitoring"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class TrafficSplitUpdate(BaseModel):
    """Request to update traffic split"""

    intent: str = Field(..., description="Intent category (faq/quote/booking)")
    percentage: int = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of traffic to local model (0-100)",
    )


class ActivationRequest(BaseModel):
    """Request to activate local AI mode"""

    mode: str = Field(..., description="Activation mode: 'shadow' or 'active'")
    reason: str | None = Field(None, description="Reason for activation")


class ConfidenceTestRequest(BaseModel):
    """Request to test confidence prediction"""

    message: str = Field(..., description="Test message")
    intent: str = Field(..., description="Intent category")


# ============================================================================
# READINESS ENDPOINTS
# ============================================================================


@router.get("/dashboard")
async def get_readiness_dashboard(db: AsyncSession = Depends(get_db)):
    """
    🎯 **MAIN DASHBOARD** - Complete AI readiness overview

    Shows:
    - Overall readiness score
    - Per-intent breakdown
    - Quality metrics
    - Actionable recommendations

    **Use this endpoint to decide when to activate Ollama!**
    """
    readiness_service = get_readiness_service()

    try:
        dashboard = await readiness_service.get_overall_readiness(db)

        # Add routing stats
        router_service = get_model_router()
        dashboard["routing_stats"] = router_service.get_routing_stats()

        # Add recent alerts
        quality_monitor = get_quality_monitor()
        dashboard["recent_alerts"] = quality_monitor.get_alerts(limit=5)

        return dashboard

    except Exception as e:
        logger.exception(f"Error getting readiness dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intent/{intent}")
async def get_intent_readiness(intent: str, db: AsyncSession = Depends(get_db)):
    """
    Get detailed readiness for specific intent

    **Intent categories:**
    - `faq`: FAQ and general info
    - `quote`: Price quotes and estimates
    - `booking`: Booking and scheduling
    """
    readiness_service = get_readiness_service()

    try:
        readiness = await readiness_service.get_intent_readiness(db, intent)
        return readiness.to_dict()

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Error getting intent readiness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overall")
async def get_overall_status(db: AsyncSession = Depends(get_db)):
    """
    Quick overall readiness check

    Returns simplified status (green/yellow/red)
    """
    readiness_service = get_readiness_service()

    try:
        full_dashboard = await readiness_service.get_overall_readiness(db)
        return full_dashboard["overall_readiness"]

    except Exception as e:
        logger.exception(f"Error getting overall status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROUTING & ACTIVATION ENDPOINTS
# ============================================================================


@router.get("/routing/stats")
async def get_routing_stats():
    """
    Get routing statistics

    Shows how traffic is split between OpenAI and Ollama
    """
    router_service = get_model_router()
    return router_service.get_routing_stats()


@router.post("/routing/update-split")
async def update_traffic_split(request: TrafficSplitUpdate):
    """
    🎚️ **GRADUAL ROLLOUT CONTROL** - Update traffic split

    Example: Set FAQ to 10% local traffic
    ```json
    {
      "intent": "faq",
      "percentage": 10
    }
    ```

    **Recommended rollout:**
    - Week 1: 10%
    - Week 2: 25%
    - Week 3: 50%
    - Week 4+: 75-100%
    """
    router_service = get_model_router()

    try:
        router_service.update_traffic_split(request.intent, request.percentage)
        return {
            "success": True,
            "intent": request.intent,
            "new_percentage": request.percentage,
            "message": f"Traffic split updated: {request.intent} = {request.percentage}%",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/activation/enable")
async def enable_local_ai(request: ActivationRequest):
    """
    🚀 **ONE-CLICK ACTIVATION** - Enable local AI mode

    **Modes:**
    - `shadow`: Learning only (no customer impact)
    - `active`: Production use (based on traffic splits)

    **⚠️ WARNING:** Only enable 'active' mode when readiness >= 85%

    Example:
    ```json
    {
      "mode": "active",
      "reason": "FAQ intent at 92% readiness, starting 10% rollout"
    }
    ```
    """
    if request.mode not in ["shadow", "active"]:
        raise HTTPException(status_code=400, detail="Mode must be 'shadow' or 'active'")

    # Update config (in-memory for now)
    # TODO: Persist to database or config file
    settings.LOCAL_AI_MODE = request.mode

    logger.info(
        f"LOCAL_AI_MODE changed to '{request.mode}'. " f"Reason: {request.reason or 'Not provided'}"
    )

    return {
        "success": True,
        "previous_mode": "shadow",
        "new_mode": request.mode,
        "timestamp": "2025-11-02T...",
        "message": f"Local AI mode set to '{request.mode}'",
    }


@router.post("/activation/disable")
async def disable_local_ai():
    """
    🛑 **EMERGENCY STOP** - Disable local AI immediately

    Switches back to shadow mode (OpenAI only for customers)
    """
    previous_mode = settings.LOCAL_AI_MODE
    settings.LOCAL_AI_MODE = "shadow"

    # Also reset all traffic splits
    router_service = get_model_router()
    for intent in ["faq", "quote", "booking"]:
        router_service.update_traffic_split(intent, 0)

    logger.warning("LOCAL_AI_MODE disabled via API. Switched to shadow mode.")

    return {
        "success": True,
        "previous_mode": previous_mode,
        "new_mode": "shadow",
        "message": "Local AI disabled. All traffic routed to OpenAI.",
        "traffic_splits_reset": True,
    }


# ============================================================================
# QUALITY MONITORING ENDPOINTS
# ============================================================================


@router.get("/quality/alerts")
async def get_quality_alerts(
    severity: str | None = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Get quality alerts

    **Severity levels:**
    - `info`: Informational
    - `warning`: Needs attention
    - `critical`: Auto-rollback triggered

    Example: `GET /quality/alerts?severity=critical&limit=5`
    """
    quality_monitor = get_quality_monitor()

    # Run quality check first
    await quality_monitor.check_quality(db)

    # Get alerts
    alerts = quality_monitor.get_alerts(severity=severity, limit=limit)

    return {
        "alerts": alerts,
        "total_count": len(alerts),
        "auto_rollback_enabled": settings.AUTO_ROLLBACK_ENABLED,
    }


@router.get("/quality/comparison")
async def get_quality_comparison(
    intent: str | None = None,
    days: int = 7,
    db: AsyncSession = Depends(get_db),
):
    """
    Teacher vs Student quality comparison

    Shows side-by-side metrics:
    - Similarity scores
    - Response times
    - Cost analysis

    Example: `GET /quality/comparison?intent=faq&days=7`
    """
    quality_monitor = get_quality_monitor()

    try:
        comparison = await quality_monitor.get_quality_comparison(db, intent=intent, days=days)
        return comparison

    except Exception as e:
        logger.exception(f"Error getting quality comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality/rollback/{intent}")
async def manual_rollback(intent: str):
    """
    🔄 **MANUAL ROLLBACK** - Disable local model for specific intent

    Useful if you notice quality issues
    """
    if intent not in ["faq", "quote", "booking"]:
        raise HTTPException(status_code=400, detail=f"Invalid intent: {intent}")

    router_service = get_model_router()
    router_service.update_traffic_split(intent, 0)

    logger.warning(f"Manual rollback triggered for {intent}")

    return {
        "success": True,
        "intent": intent,
        "action": "rollback",
        "message": f"{intent} traffic disabled. Using OpenAI only.",
    }


@router.get("/quality/rollback-history")
async def get_rollback_history():
    """
    Get history of automatic rollbacks

    Shows when and why rollbacks occurred
    """
    quality_monitor = get_quality_monitor()
    history = quality_monitor.get_rollback_history()

    return {"rollback_count": len(history), "history": history}


# ============================================================================
# ML PREDICTOR ENDPOINTS
# ============================================================================


@router.get("/ml/predictor-stats")
async def get_predictor_stats():
    """
    Get ML confidence predictor statistics

    Shows training status and performance
    """
    predictor = get_confidence_predictor()
    return predictor.get_stats()


@router.post("/ml/test-confidence")
async def test_confidence_prediction(
    request: ConfidenceTestRequest, db: AsyncSession = Depends(get_db)
):
    """
    🧪 **TEST CONFIDENCE** - Predict quality for a test message

    Example:
    ```json
    {
      "message": "What are your business hours?",
      "intent": "faq"
    }
    ```

    Returns predicted confidence (0-1)
    """
    predictor = get_confidence_predictor()

    try:
        confidence = await predictor.predict_confidence(
            db, message=request.message, intent=request.intent
        )

        return {
            "message": request.message,
            "intent": request.intent,
            "predicted_confidence": round(confidence, 3),
            "would_use_local": confidence >= settings.LOCAL_AI_MIN_CONFIDENCE,
            "threshold": settings.LOCAL_AI_MIN_CONFIDENCE,
        }

    except Exception as e:
        logger.exception(f"Error predicting confidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ml/retrain")
async def retrain_predictor(db: AsyncSession = Depends(get_db)):
    """
    🔄 **RETRAIN PREDICTOR** - Force ML model retraining

    Normally runs automatically every 24 hours
    """
    predictor = get_confidence_predictor()

    try:
        await predictor.train(db)
        stats = predictor.get_stats()

        return {
            "success": True,
            "message": "ML predictor retrained successfully",
            "stats": stats,
        }

    except Exception as e:
        logger.exception(f"Error retraining predictor: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================


@router.get("/config")
async def get_readiness_config():
    """
    Get current readiness configuration

    Shows all thresholds and settings
    """
    return {
        "shadow_learning_enabled": settings.SHADOW_LEARNING_ENABLED,
        "local_ai_mode": settings.LOCAL_AI_MODE,
        "sample_rate": settings.SHADOW_LEARNING_SAMPLE_RATE,
        "min_confidence": settings.LOCAL_AI_MIN_CONFIDENCE,
        "thresholds": {
            "faq": {
                "min_pairs": settings.READINESS_FAQ_MIN_PAIRS,
                "min_similarity": settings.READINESS_FAQ_MIN_SIMILARITY,
            },
            "quote": {
                "min_pairs": settings.READINESS_QUOTE_MIN_PAIRS,
                "min_similarity": settings.READINESS_QUOTE_MIN_SIMILARITY,
            },
            "booking": {
                "min_pairs": settings.READINESS_BOOKING_MIN_PAIRS,
                "min_similarity": settings.READINESS_BOOKING_MIN_SIMILARITY,
            },
        },
        "quality_monitoring": {
            "enabled": settings.QUALITY_MONITOR_ENABLED,
            "degradation_threshold": settings.QUALITY_DEGRADATION_THRESHOLD,
            "auto_rollback_enabled": settings.AUTO_ROLLBACK_ENABLED,
        },
        "ml_predictor": {
            "enabled": settings.ML_PREDICTOR_ENABLED,
            "min_training_samples": settings.ML_PREDICTOR_MIN_TRAINING_SAMPLES,
            "retrain_interval_hours": settings.ML_PREDICTOR_RETRAIN_INTERVAL_HOURS,
        },
    }


@router.post("/reset-stats")
async def reset_all_stats():
    """
    🔄 **RESET STATS** - Clear all statistics and alerts

    Useful for fresh start after testing
    """
    router_service = get_model_router()
    router_service.reset_stats()

    quality_monitor = get_quality_monitor()
    quality_monitor.clear_alerts()

    return {"success": True, "message": "All statistics and alerts cleared"}
