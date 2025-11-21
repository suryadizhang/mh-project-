"""
Health check endpoints for configuration and GSM status
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import asyncio

from core.config import get_settings_async, get_config_status, reload_config
from core.auth import verify_admin_user

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/config")
async def config_health() -> Dict[str, Any]:
    """
    Get configuration health status (public endpoint for basic checks)

    Returns basic configuration status without sensitive information
    """
    try:
        settings = await get_settings_async()
        config_status = get_config_status()

        return {
            "status": "healthy",
            "gsm_available": config_status["gsm_available"],
            "config_loaded": config_status["config_loaded"],
            "secrets_count": config_status["secrets_count"],
            "environment": settings.ENVIRONMENT,
            "app_name": settings.APP_NAME,
            "api_version": settings.API_VERSION,
            "timestamp": asyncio.get_event_loop().time(),
        }

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Configuration health check failed: {str(e)}")


@router.get("/config/detailed")
async def detailed_config_health(current_user=Depends(verify_admin_user)) -> Dict[str, Any]:
    """
    Get detailed configuration status (admin only)

    Includes sensitive configuration checks for debugging
    """
    try:
        settings = await get_settings_async()
        config_status = get_config_status()

        # Check critical configuration (without revealing values)
        critical_checks = {
            "JWT_SECRET": bool(settings.JWT_SECRET),
            "SECRET_KEY": bool(settings.SECRET_KEY),
            "ENCRYPTION_KEY": bool(settings.ENCRYPTION_KEY),
            "DATABASE_URL": bool(settings.DATABASE_URL),
            "REDIS_URL": bool(settings.REDIS_URL),
            "OPENAI_API_KEY": bool(settings.OPENAI_API_KEY),
            "STRIPE_SECRET_KEY": bool(settings.STRIPE_SECRET_KEY),
            "RC_CLIENT_ID": bool(settings.RC_CLIENT_ID),
            "RC_CLIENT_SECRET": bool(settings.RC_CLIENT_SECRET),
        }

        # Count enabled feature flags
        enabled_features = settings.get_enabled_features()

        return {
            "status": "healthy",
            "gsm_integration": {
                "available": config_status["gsm_available"],
                "config_loaded": config_status["config_loaded"],
                "secrets_count": config_status["secrets_count"],
            },
            "critical_config": critical_checks,
            "feature_flags": {
                "enabled_count": len(enabled_features),
                "enabled_flags": enabled_features,
            },
            "environment_details": {
                "environment": settings.ENVIRONMENT,
                "debug": settings.DEBUG,
                "app_name": settings.APP_NAME,
                "api_version": settings.API_VERSION,
                "host": settings.HOST,
                "port": settings.PORT,
            },
            "timestamp": asyncio.get_event_loop().time(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Detailed configuration health check failed: {str(e)}"
        )


@router.post("/config/reload")
async def reload_configuration(current_user=Depends(verify_admin_user)) -> Dict[str, Any]:
    """
    Reload configuration from GSM (admin only)

    Useful for updating secrets without restarting the server
    """
    try:
        settings = await reload_config()
        config_status = get_config_status()

        return {
            "status": "reloaded",
            "message": "Configuration successfully reloaded from GSM",
            "secrets_count": config_status["secrets_count"],
            "timestamp": asyncio.get_event_loop().time(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Configuration reload failed: {str(e)}")


@router.get("/dependencies")
async def dependencies_health() -> Dict[str, Any]:
    """
    Check health of external dependencies
    """
    results = {}

    try:
        settings = await get_settings_async()

        # Check database connection
        try:
            # This would be replaced with actual database health check
            results["database"] = {
                "status": "healthy",
                "url_configured": bool(settings.DATABASE_URL),
            }
        except Exception as e:
            results["database"] = {"status": "unhealthy", "error": str(e)}

        # Check Redis connection
        try:
            # This would be replaced with actual Redis health check
            results["redis"] = {"status": "healthy", "url_configured": bool(settings.REDIS_URL)}
        except Exception as e:
            results["redis"] = {"status": "unhealthy", "error": str(e)}

        # Check external APIs
        results["external_apis"] = {
            "openai": {"configured": bool(settings.OPENAI_API_KEY)},
            "stripe": {"configured": bool(settings.STRIPE_SECRET_KEY)},
            "ringcentral": {
                "configured": bool(settings.RC_CLIENT_ID and settings.RC_CLIENT_SECRET)
            },
        }

        return {
            "status": "checked",
            "dependencies": results,
            "timestamp": asyncio.get_event_loop().time(),
        }

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Dependencies health check failed: {str(e)}")
