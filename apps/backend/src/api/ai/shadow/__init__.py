"""
Shadow Learning Module
Local model training through teacher-student parallel inference
"""

from api.ai.shadow.confidence_predictor import (
    ConfidencePredictor,
    get_confidence_predictor,
)
from api.ai.shadow.local_model import LocalLLMService, get_local_llm_service
from api.ai.shadow.model_router import ModelRouter, get_model_router
from db.models.ai.shadow_learning import AIExportJob, AIRLHFScore, AITutorPair
from api.ai.shadow.quality_monitor import QualityMonitor, get_quality_monitor
from api.ai.shadow.readiness_service import (
    AIReadinessService,
    get_readiness_service,
)
from api.ai.shadow.similarity_evaluator import (
    calculate_similarity,
    evaluate_response_quality,
)
from api.ai.shadow.tutor_logger import (
    get_high_quality_pairs,
    get_tutor_pair_stats,
    log_tutor_pair,
)

__all__ = [
    "AIExportJob",
    "AIRLHFScore",
    # Readiness & Monitoring (Option B+C)
    "AIReadinessService",
    # Database Models
    "AITutorPair",
    "ConfidencePredictor",
    # Core Shadow Learning
    "LocalLLMService",
    "ModelRouter",
    "QualityMonitor",
    "calculate_similarity",
    "evaluate_response_quality",
    "get_confidence_predictor",
    "get_high_quality_pairs",
    "get_local_llm_service",
    "get_model_router",
    "get_quality_monitor",
    "get_readiness_service",
    "get_tutor_pair_stats",
    "log_tutor_pair",
]
