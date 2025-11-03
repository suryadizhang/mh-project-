"""
Shadow Learning Module
Local model training through teacher-student parallel inference
"""

from api.ai.shadow.local_model import LocalLLMService, get_local_llm_service
from api.ai.shadow.tutor_logger import log_tutor_pair, get_high_quality_pairs, get_tutor_pair_stats
from api.ai.shadow.similarity_evaluator import calculate_similarity, evaluate_response_quality
from api.ai.shadow.models import AITutorPair, AIRLHFScore, AIExportJob

__all__ = [
    "LocalLLMService",
    "get_local_llm_service",
    "log_tutor_pair",
    "get_high_quality_pairs",
    "get_tutor_pair_stats",
    "calculate_similarity",
    "evaluate_response_quality",
    "AITutorPair",
    "AIRLHFScore",
    "AIExportJob",
]
