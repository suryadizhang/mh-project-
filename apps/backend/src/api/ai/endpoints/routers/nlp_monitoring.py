"""
NLP Service Monitoring Endpoints
Provides performance metrics and health checks for Enhanced NLP Service
"""

from fastapi import APIRouter, status
from typing import Dict, Any
import structlog

from src.services.enhanced_nlp_service import get_nlp_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/nlp", tags=["nlp-monitoring"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def nlp_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for NLP service
    
    Returns comprehensive health status including:
    - Model availability
    - Performance metrics
    - Error rates
    - System status
    """
    try:
        nlp_service = get_nlp_service()
        health = nlp_service.health_check()
        
        # Map status to HTTP status code
        http_status = {
            'healthy': status.HTTP_200_OK,
            'degraded': status.HTTP_200_OK,  # Still operational
            'unhealthy': status.HTTP_503_SERVICE_UNAVAILABLE
        }.get(health['status'], status.HTTP_200_OK)
        
        return {
            "success": True,
            "service": "Enhanced NLP Service",
            "health": health,
            "timestamp": health.get('last_called')
        }
        
    except Exception as e:
        logger.exception(f"NLP health check failed: {e}")
        return {
            "success": False,
            "service": "Enhanced NLP Service",
            "status": "unhealthy",
            "error": str(e),
            "http_status": status.HTTP_503_SERVICE_UNAVAILABLE
        }


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def nlp_metrics(method: str = None) -> Dict[str, Any]:
    """
    Get performance metrics for NLP operations
    
    Query Parameters:
    - method: Optional - specific method to get metrics for
              (extract_entities, detect_tone_enhanced, etc.)
    
    Returns detailed performance metrics including:
    - Call counts
    - Average/min/max execution times
    - Error rates
    - Per-method breakdown
    """
    try:
        nlp_service = get_nlp_service()
        metrics = nlp_service.get_performance_metrics(method)
        
        return {
            "success": True,
            "service": "Enhanced NLP Service",
            "metrics": metrics,
            "method_filter": method
        }
        
    except Exception as e:
        logger.exception(f"Failed to get NLP metrics: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/metrics/reset", status_code=status.HTTP_200_OK)
async def reset_nlp_metrics() -> Dict[str, Any]:
    """
    Reset all performance metrics
    
    Use this endpoint to clear metrics and start fresh tracking.
    Useful for testing or after system maintenance.
    """
    try:
        nlp_service = get_nlp_service()
        nlp_service.reset_metrics()
        
        return {
            "success": True,
            "message": "NLP performance metrics reset successfully",
            "service": "Enhanced NLP Service"
        }
        
    except Exception as e:
        logger.exception(f"Failed to reset NLP metrics: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/status", status_code=status.HTTP_200_OK)
async def nlp_status() -> Dict[str, Any]:
    """
    Get detailed status information about NLP service
    
    Returns:
    - Initialization status
    - Model availability (spaCy, sentence-transformers)
    - Supported features
    - Version information
    """
    try:
        nlp_service = get_nlp_service()
        
        return {
            "success": True,
            "service": "Enhanced NLP Service",
            "status": {
                "initialized": nlp_service._initialized,
                "models": {
                    "spacy": {
                        "loaded": nlp_service.nlp is not None,
                        "model": "en_core_web_sm" if nlp_service.nlp else None
                    },
                    "semantic_search": {
                        "loaded": nlp_service.semantic_model is not None,
                        "model": "all-MiniLM-L6-v2" if nlp_service.semantic_model else None
                    }
                },
                "features": {
                    "entity_extraction": True,
                    "tone_detection": True,
                    "semantic_faq_search": True,
                    "booking_detail_extraction": True,
                    "text_normalization": True,
                    "performance_monitoring": True
                },
                "fallback_available": True,
                "performance_target": "<50ms per request"
            }
        }
        
    except Exception as e:
        logger.exception(f"Failed to get NLP status: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/test", status_code=status.HTTP_200_OK)
async def nlp_test() -> Dict[str, Any]:
    """
    Quick test endpoint to verify NLP functionality
    
    Runs a simple test on all major NLP features and returns results.
    Useful for smoke testing after deployment.
    """
    try:
        nlp_service = get_nlp_service()
        
        test_text = "I need hibachi for 50 people on Friday at 6pm with chicken and steak"
        
        # Test entity extraction
        entities = nlp_service.extract_entities(test_text)
        
        # Test tone detection
        tone, confidence = nlp_service.detect_tone_enhanced(test_text)
        
        # Test booking extraction
        booking_details = nlp_service.extract_booking_details(test_text)
        
        return {
            "success": True,
            "service": "Enhanced NLP Service",
            "test_input": test_text,
            "results": {
                "entities": entities,
                "tone": {
                    "detected": tone,
                    "confidence": confidence
                },
                "booking_details": booking_details
            },
            "all_features_working": True
        }
        
    except Exception as e:
        logger.exception(f"NLP test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "all_features_working": False
        }
